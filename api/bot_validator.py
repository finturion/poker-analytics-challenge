"""
Technische validatie van ingeleverde pokerbot-code.

Draait de code van de student NOOIT in het eigen proces van de API (dat zou
elke fout of oneindige loop van een student meteen de server laten crashen).
In plaats daarvan: wegschrijven naar een tijdelijk bestand en uitvoeren in
een apart subprocess met een timeout en zonder netwerktoegang.
"""
import ast
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import os

TIMEOUT_SECONDS = 8
MARKER = "###POKERBOT_RESULTAAT###"

TOEGESTANE_ACTIES = {"call", "raise", "fold", "check"}
# "all_in" mag pas zodra een bot zijn eigen stack kent (config["heeft_stack"],
# vanaf Week 3): pas dan kan hij bewust afwegen of hij alles inzet. Zie ook
# _ondersteunt_all_in_regels in poker_adapter.py, dat aan de speel-kant op
# exact hetzelfde signaal ("stack" in de signatuur) gate't.
TOEGESTANE_ACTIES_MET_STACK = TOEGESTANE_ACTIES | {"all_in"}
# "grote_raise" mag vanaf Week 3, op hetzelfde signaal als all_in: de bot kent
# zijn stack. Vanaf die week heeft hij ook pot odds en een winkans, en dat is wat
# je nodig hebt om te bepalen hóeveel je inzet. Zie _ondersteunt_grote_raise in
# poker_adapter.py, dat op hetzelfde signaal gate't.
TOEGESTANE_ACTIES_MET_SIZING = TOEGESTANE_ACTIES_MET_STACK | {"grote_raise"}
TOEGESTANE_STRATEGIEEN = {"tight", "loose", "balanced", "aggressive"}
BLUF_KANS_MIN, BLUF_KANS_MAX = 0.0, 1.0

# Testhanden en -stacks waarmee we de bot ECHT even laten spelen (niet met
# één vaste invoer, maar met een klein setje representatieve situaties). Zo
# vinden we bugs die alleen bij een zwakke hand of een lage stack optreden.
_TEST_HANDEN = [["A", "K"], ["7", "2"], ["Q", "Q"]]
# Dezelfde handen mét kleur, voor bots die `hand_met_kleur` en `bord` gebruiken.
# Bewust geen enkele kaart die ook in _TEST_RONDE_SCENARIOS op het bord ligt:
# een kaart die twee keer bestaat laat schat_winkans terecht struikelen, en dan
# zou de validator een bot afkeuren om een fout die de validator zelf maakte.
_MET_KLEUR = {
    ("A", "K"): ["SA", "HK"],
    ("7", "2"): ["S7", "H2"],
    ("Q", "Q"): ["SQ", "HQ"],
}
_TEST_STACKS = [1000, 50]

# Per week ligt vast welke functienaam de bot moet aanbieden, en welke extra
# gegevens hij verwacht. Dit groeit mee met de cursus:
#   Week 1: kies_actie(hand)
#   Week 3: kies_actie(hand, stack)            -- plus optioneel ronde/pot/etc.
#   Week 5: kies_actie(hand, stack, strategie, bluf_kans)
#
# `strategie` zit bewust pas vanaf Week 5: in Week 3 heeft een tight/loose-label
# nog te weinig om zich in te uiten (de bot kan dan alleen op hand en stack
# reageren). Vanaf Week 5, mét bluf_kans en tegenstander-info erbij, gaat een
# strategie zich pas echt anders gedragen per moment.
VERWACHTE_FUNCTIES = {
    1: {"functienaam": "kies_actie", "heeft_stack": False, "heeft_strategie": False,
        "heeft_bluf_kans": False, "heeft_sizing": False},
    3: {"functienaam": "kies_actie", "heeft_stack": True, "heeft_strategie": False,
        "heeft_bluf_kans": False, "heeft_sizing": True},
    # `strategie` is er in september 2026 uit gehaald. De student koos zijn eigen
    # label en kreeg het daarna zelf weer terug; niets anders las het. Het stond
    # niet in het hand-log, niet in de eindstand, niet in /export en niet in de
    # hub, dus je kon er ook geen vraag mee beantwoorden -- "verslaat tight de
    # aggressives" was niet te berekenen. Wie een drempel per stijl wil, zet die
    # constante in zijn eigen bestand; dat doet precies hetzelfde zonder omweg.
    #
    # Meegeven mág nog wel: een bot die `strategie` in zijn handtekening heeft
    # krijgt hem nog steeds (zie poker_adapter). Zo breekt er niets van wie zijn
    # bot al had geschreven.
    5: {"functienaam": "kies_actie", "heeft_stack": True, "heeft_strategie": False,
        "heeft_bluf_kans": True, "heeft_sizing": True},
}


def _bevat_verboden_imports(code: str) -> str | None:
    """Blokkeert overduidelijk gevaarlijke of oneigenlijke imports (os, sys, socket, subprocess)."""
    verboden = {"os", "sys", "socket", "subprocess", "shutil", "requests", "urllib"}
    try:
        boom = ast.parse(code)
    except SyntaxError as e:
        return f"Syntaxfout, code kon niet eens geparsed worden: {e}"

    for node in ast.walk(boom):
        if isinstance(node, ast.Import):
            for naam in node.names:
                if naam.name.split(".")[0] in verboden:
                    return f"Import van '{naam.name}' is niet toegestaan in de pokerbot."
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in verboden:
                return f"Import van '{node.module}' is niet toegestaan in de pokerbot."
    return None


def _bevat_functie(code: str, functienaam: str) -> bool:
    try:
        boom = ast.parse(code)
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.FunctionDef) and node.name == functienaam
        for node in ast.walk(boom)
    )


def _functie_parameternamen(code: str, functienaam: str) -> set[str]:
    """
    Haalt de parameternamen van de opgegeven functie op via AST-parsing --
    voert de code NIET uit (zie moduledocstring). Retourneert een lege set
    als de functie niet gevonden kan worden; _bevat_functie meldt dat al
    apart als een eigen foutmelding.
    """
    try:
        boom = ast.parse(code)
    except SyntaxError:
        return set()
    for node in ast.walk(boom):
        if isinstance(node, ast.FunctionDef) and node.name == functienaam:
            return {arg.arg for arg in node.args.args}
    return set()


def _valideer_strategie_en_bluf_kans(config: dict, strategie, bluf_kans) -> str | None:
    """
    Checkt of de student een geldige strategie/bluf_kans heeft opgegeven bij
    zijn inzending, VOORDAT we zijn code uitvoeren. Retourneert een nette
    Nederlandstalige foutmelding, of None als alles klopt.
    """
    # Geen enkele week eist nog een strategie. Geeft iemand er tóch een mee, dan
    # controleren we hem wel: een typfout stil doorlaten is erger dan afkeuren.
    if config["heeft_strategie"]:
        if strategie is None:
            return (
                "Deze week hoort er een 'strategie' bij je inzending, maar die ontbreekt. "
                f"Kies uit: {', '.join(sorted(TOEGESTANE_STRATEGIEEN))}."
            )
    if strategie is not None:
        if strategie not in TOEGESTANE_STRATEGIEEN:
            return (
                f"'{strategie}' is geen geldige strategie. "
                f"Kies uit: {', '.join(sorted(TOEGESTANE_STRATEGIEEN))}."
            )

    if config["heeft_bluf_kans"]:
        if bluf_kans is None:
            return "Deze week hoort er een 'bluf_kans' bij je inzending (een kans tussen 0 en 1), maar die ontbreekt."
        if not isinstance(bluf_kans, (int, float)) or isinstance(bluf_kans, bool):
            return f"'bluf_kans' moet een getal zijn, geen {type(bluf_kans).__name__}."
        if not (BLUF_KANS_MIN <= bluf_kans <= BLUF_KANS_MAX):
            return f"'bluf_kans' moet tussen {BLUF_KANS_MIN} en {BLUF_KANS_MAX} liggen, jij gaf {bluf_kans}."

    return None


# De broncode van winkans.py, om in het testproces in te plakken. Eén keer
# inlezen bij het opstarten: hij verandert niet tijdens het draaien.
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "winkans.py"),
          encoding="utf-8") as _bestand:
    _WINKANS_BRON = _bestand.read()


_RONDE_PARAMETERS = {"ronde", "pot", "inzet_om_te_callen", "tegenstander_acties_deze_hand",
                     "bord", "hand_met_kleur"}
# Representatieve situaties op elke straat, om te checken dat een bot die
# ronde/pot/inzet_om_te_callen/tegenstander_acties_deze_hand gebruikt, in elke
# fase van de hand een herkenbare actie teruggeeft (niet alleen preflop, waar
# de meeste bots het eerst getest worden) -- inclusief een variatie in wat
# tegenstanders deze hand al gedaan hebben, want dat is precies waar een bot
# die daarop reageert onderuit kan gaan (bv. een lege lijst niet aankunnen).
#
# `bord` staat er sinds Week 5 bij, en het PREFLOP-scenario met een lege lijst
# is het belangrijkste van de drie. Een bot die schat_winkans met een bord
# aanroept, moet zelf afvangen dat er preflop nog geen bord is -- doet hij dat
# niet, dan crasht hij op elke eerste beslissing van elke hand, en een crash is
# een fold. Zonder dit scenario zou zo'n bot de validatie halen en daarna elke
# hand weggooien.
_TEST_RONDE_SCENARIOS = [
    {"ronde": "preflop", "pot": 30, "inzet_om_te_callen": 10, "tegenstander_acties_deze_hand": [],
     "bord": []},
    # LET OP het veld `ronde` in elke actie. Het toernooi zet dat er altijd bij
    # (poker_adapter.receive_game_update_message), en Werkcollege 7 leert
    # studenten juist om daarop te filteren -- de lijst loopt over de hele hand,
    # dus zonder filter zie je op de river nog de raise van preflop. Toen het
    # hier ontbrak, crashte precies de bot die het goed deed: KeyError 'ronde',
    # en een crash is een afgekeurde inzending. De river-actie staat bewust op
    # "flop", zodat een bot die NIET filtert een ander antwoord geeft dan een
    # bot die dat wel doet.
    {"ronde": "flop", "pot": 120, "inzet_om_te_callen": 0, "tegenstander_acties_deze_hand": [
        {"bot_naam": "TestBot", "actie": "call", "bedrag": 20, "ronde": "flop"},
    ], "bord": ["D4", "C9", "HT"]},
    {"ronde": "river", "pot": 400, "inzet_om_te_callen": 200, "tegenstander_acties_deze_hand": [
        {"bot_naam": "TestBot", "actie": "raise", "bedrag": 200, "ronde": "flop"},
    ], "bord": ["D4", "C9", "HT", "S3", "C6"]},
]


def _bouw_testgevallen(config: dict, strategie, bluf_kans, parameternamen: set[str]) -> list[dict]:
    """
    Bouwt een klein setje realistische aanroepen van kies_actie(), met
    wisselende hand, (vanaf Week 3) stack en (vanaf Week 5) strategie/bluf_kans.
    We testen dus niet met 1 hand, maar meteen met een sterke hand, een zwakke
    hand en een pocket pair, op een normale én een lage stack.

    Neemt de student alleen mee als hij `ronde`/`pot`/`inzet_om_te_callen`/
    `tegenstander_acties_deze_hand` ZELF in zijn functie-signatuur heeft
    opgenomen (parameternamen komt uit _functie_parameternamen) -- anders
    krijgt hij ze niet aangeboden, precies zoals StudentBotSpeler.declare_action
    ook alleen doorgeeft wat de functie zelf accepteert. Zo blijft een bot
    zonder die parameters exact even vaak getest als voorheen.
    """
    gevallen = []
    for hand in _TEST_HANDEN:
        if not config["heeft_stack"]:
            gevallen.append({"hand": hand})
            continue
        for stack in _TEST_STACKS:
            basis = {"hand": hand, "stack": stack}
            # Alleen meegeven als de student hem zelf in zijn signatuur heeft
            # gezet -- net als ronde/pot/bord. Stond dit er onvoorwaardelijk,
            # dan kreeg ELKE bestaande bot een TypeError op een argument dat hij
            # nooit gevraagd heeft.
            if "hand_met_kleur" in parameternamen:
                basis["hand_met_kleur"] = _MET_KLEUR[tuple(hand)]
            # Op de handtekening, niet op de week. Sinds strategie niet meer
            # verplicht is, zou "alleen meegeven als de week erom vraagt"
            # betekenen dat elke bestaande week-5-bot -- die hem positioneel in
            # zijn handtekening heeft -- een TypeError krijgt en wordt afgekeurd.
            # Zo krijgt hij hem gewoon, precies zoals bord en hand_met_kleur.
            if "strategie" in parameternamen:
                basis["strategie"] = strategie
            if config["heeft_bluf_kans"] or "bluf_kans" in parameternamen:
                basis["bluf_kans"] = bluf_kans
            if parameternamen & _RONDE_PARAMETERS:
                for scenario in _TEST_RONDE_SCENARIOS:
                    args = dict(basis)
                    args.update({k: v for k, v in scenario.items() if k in parameternamen})
                    gevallen.append(args)
            else:
                gevallen.append(basis)
    return gevallen


def _draai_in_apart_proces(code: str, functienaam: str, testgevallen: list[dict]):
    """
    Draait de studentcode op deze testgevallen in een apart, geïsoleerd proces.

    Retourneert (acties, foutmelding). Bij een fout is acties None en bevat
    foutmelding iets dat een student kan lezen.

    Apart proces met `python -I`: geen site-packages van ons, geen omgeving die
    doorlekt, en een harde timeout. Zo kan een oneindige loop of een crash in
    studentcode de API niet meesleuren.
    """
    testgevallen_json = json.dumps(testgevallen)
    footer = textwrap.dedent(f"""
        testgevallen = json.loads('''{testgevallen_json}''')
        resultaten = []
        for testgeval in testgevallen:
            resultaten.append({functienaam}(**testgeval))
        print("{MARKER}" + json.dumps({{"acties": resultaten}}))
    """)
    # Let op: het studentbestand (`code`) heeft zijn eigen, willekeurige inspringing.
    # Die mag NIET door textwrap.dedent worden aangeraakt -- daarom blijft `code`
    # ongewijzigd op kolom 0 staan, los van de rest.
    # schat_winkans staat klaar vóór de studentcode, precies zoals
    # toernooi_runner._laad_kies_actie hem in de naamruimte zet. Zonder dit zou
    # een bot die hem gebruikt hier stukgaan en in het toernooi werken -- of
    # andersom, en dat is erger: dan keurt de validatie iets goed dat het niet doet.
    #
    # De bron wordt INGEPLAKT en niet geimporteerd. `python -I` haalt de map van
    # het script zelf uit sys.path, dus winkans.py ernaast zetten werkt niet, en
    # sys.path aanpassen zou `sys` in de naamruimte van de student leggen --
    # precies wat de verbodenlijst tegenhoudt. Inplakken houdt de isolatie heel.
    runner_script = ("import json\n\n" + _WINKANS_BRON + "\n\n"
                     + code + "\n\n" + footer)

    werkmap = tempfile.mkdtemp(prefix="botcheck_")
    tijdelijk_pad = os.path.join(werkmap, "bot_runner.py")
    with open(tijdelijk_pad, "w") as f:
        f.write(runner_script)

    try:
        proces = subprocess.run(
            [sys.executable, "-I", tijdelijk_pad],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, f"Je bot-code draaide langer dan {TIMEOUT_SECONDS} seconden (oneindige loop?)."
    finally:
        shutil.rmtree(werkmap, ignore_errors=True)

    if proces.returncode != 0 or MARKER not in proces.stdout:
        foutregel = proces.stderr.strip().splitlines()[-1] if proces.stderr.strip() else "Onbekende fout."
        return None, f"Je bot-code crasht: {foutregel}"

    try:
        resultaat_json = proces.stdout.split(MARKER, 1)[1].strip().splitlines()[0]
        return json.loads(resultaat_json)["acties"], None
    except (IndexError, json.JSONDecodeError, KeyError):
        return None, "Kon het resultaat van je functie niet uitlezen."


# Welke velden uit een testgeval de student te zien krijgt, en in welke volgorde.
# Niet alles: strategie en bluf_kans zijn zijn eigen invoer, die hoeft hij niet
# terug te lezen, en hand_met_kleur zegt naast hand weinig extra's.
_TOON_VELDEN = ("hand", "stack", "ronde", "pot", "inzet_om_te_callen", "bord")


def _testuitslag(testgevallen: list, acties: list) -> list:
    """
    De testgevallen mét het antwoord van de bot erbij.

    actie_resultaten is een platte lijst acties zonder context: achttien keer
    "fold" zegt een student niets. Met de situatie ernaast wordt het een tabel
    waarin je in één blik ziet dat je bot op elke hand hetzelfde doet -- en dat
    is precies waar het in week 3 misging: een groot deel van de klas leverde de
    voorbeeldbot in, technisch goedgekeurd, en niemand die het zag.
    """
    uitslag = []
    for geval, actie in zip(testgevallen, acties):
        rij = {veld: geval[veld] for veld in _TOON_VELDEN if veld in geval}
        rij["actie"] = actie
        uitslag.append(rij)
    return uitslag


def _is_constante_bot(acties: list) -> bool:
    """
    True als de bot op ALLE testgevallen precies dezelfde actie teruggeeft.

    Dat is technisch prima code -- `return "fold"` draait zonder fouten -- maar
    het is geen pokerbot: hij kijkt niet naar zijn kaarten, zijn stack of de
    ronde. Dit is geen reden om af te keuren (een bot mag nou eenmaal heel
    tight zijn), maar het is wél iets wat de docent wil zien, en wat de student
    als hint terugkrijgt bij het inleveren.
    """
    if len(acties) < 2:
        return False
    return len({str(a).lower() for a in acties}) == 1


def valideer_bot_code(code: str, week: int, strategie: str | None = None, bluf_kans: float | None = None) -> dict:
    """
    Retourneert {"geldig": bool, "foutmelding": str | None, "actie_resultaten": list | None}.

    "geldig" betekent: geen verboden imports, functie met de juiste naam
    bestaat, strategie/bluf_kans zijn (indien van toepassing) geldig, en de
    bot draait zonder crash op een setje representatieve testhanden/stacks,
    en geeft daarbij steeds een herkenbare actie terug.
    """
    if week not in VERWACHTE_FUNCTIES:
        return {"geldig": False, "foutmelding": f"Onbekende week: {week}", "actie_resultaten": None, "testuitslag": None, "constante_bot": False}

    config = VERWACHTE_FUNCTIES[week]

    strategie_fout = _valideer_strategie_en_bluf_kans(config, strategie, bluf_kans)
    if strategie_fout:
        return {"geldig": False, "foutmelding": strategie_fout, "actie_resultaten": None, "testuitslag": None, "constante_bot": False}

    verboden_reden = _bevat_verboden_imports(code)
    if verboden_reden:
        return {"geldig": False, "foutmelding": verboden_reden, "actie_resultaten": None, "testuitslag": None, "constante_bot": False}

    functienaam = config["functienaam"]
    if not _bevat_functie(code, functienaam):
        return {
            "geldig": False,
            "foutmelding": f"Ik kan geen functie met de naam '{functienaam}()' vinden in je bestand.",
            "actie_resultaten": None,
            "constante_bot": False,
        }

    parameternamen = _functie_parameternamen(code, functienaam)
    testgevallen = _bouw_testgevallen(config, strategie, bluf_kans, parameternamen)

    # Let op: het studentbestand (`code`) heeft zijn eigen, willekeurige inspringing.
    # Die mag NIET door textwrap.dedent worden aangeraakt (dedent kijkt naar de
    # gezamenlijke inspringing van alle regels en zou de inhoud van `code` dan
    # kunnen verschuiven t.o.v. zijn eigen functie-body -> valse IndentationError).
    # Daarom blijft `code` ongewijzigd op kolom 0 staan, los van de rest.
    acties, draaifout = _draai_in_apart_proces(code, functienaam, testgevallen)
    if draaifout:
        return {"geldig": False, "foutmelding": draaifout, "actie_resultaten": None, "testuitslag": None, "constante_bot": False}

    if config["heeft_sizing"]:
        toegestane_acties = TOEGESTANE_ACTIES_MET_SIZING
    elif config["heeft_stack"]:
        toegestane_acties = TOEGESTANE_ACTIES_MET_STACK
    else:
        toegestane_acties = TOEGESTANE_ACTIES
    for testgeval, actie in zip(testgevallen, acties):
        if not isinstance(actie, str) or actie.lower() not in toegestane_acties:
            context = [f"hand {testgeval['hand']}"]
            if "stack" in testgeval:
                context.append(f"stack {testgeval['stack']}")
            if "ronde" in testgeval:
                context.append(f"ronde {testgeval['ronde']!r}")
            return {
                "geldig": False,
                "foutmelding": (
                    f"Bij {', '.join(context)}"
                    f" gaf je functie '{actie}' terug — verwacht een van {sorted(toegestane_acties)}."
                ),
                "actie_resultaten": acties,
                "testuitslag": _testuitslag(testgevallen, acties),
                "constante_bot": False,
            }

    return {
        "geldig": True,
        "foutmelding": None,
        "actie_resultaten": acties,
        "testuitslag": _testuitslag(testgevallen, acties),
        "constante_bot": _is_constante_bot(acties),
    }


# Hoeveel testgevallen je in één keer aan iemand anders zijn bot mag stellen.
# Bewust laag: dit is bedoeld om te zien HOE een klasgenoot speelt op een paar
# situaties die jij interessant vindt, niet om zijn hele strategietabel uit te
# lezen. Elke aanroep start ook een apart proces, dus het kost rekentijd.
MAX_TESTGEVALLEN_PEER = 20


def speel_testgevallen(code: str, week: int, testgevallen: list[dict],
                       strategie=None, bluf_kans=None) -> dict:
    """
    Draait een bot op testgevallen die de aanvrager zelf opgeeft.

    Voor "test tegen een klasgenoot": je stuurt een setje situaties in en krijgt
    terug wat die bot daarop doet. De code zelf gaat nergens naartoe -- je ziet
    gedrag, geen broncode. Dat is bewust: er hangt een bonuspunt aan het
    toernooi, en een endpoint dat andermans bot uitdeelt maakt dat kopieerbaar.

    Retourneert {"acties": [...], "foutmelding": None} of andersom. Ontbrekende
    parameters worden weggelaten: net als in het echte spel krijgt een bot
    alleen wat hij zelf in zijn signatuur heeft gezet.
    """
    if week not in VERWACHTE_FUNCTIES:
        return {"acties": None, "foutmelding": f"Onbekende week: {week}"}
    if not testgevallen:
        return {"acties": None, "foutmelding": "Geef minstens één testgeval mee."}
    if len(testgevallen) > MAX_TESTGEVALLEN_PEER:
        return {"acties": None,
                "foutmelding": f"Maximaal {MAX_TESTGEVALLEN_PEER} testgevallen per aanvraag."}

    config = VERWACHTE_FUNCTIES[week]
    functienaam = config["functienaam"]

    verboden_reden = _bevat_verboden_imports(code)
    if verboden_reden:
        return {"acties": None, "foutmelding": verboden_reden}
    if not _bevat_functie(code, functienaam):
        return {"acties": None, "foutmelding": f"Deze bot heeft geen functie '{functienaam}()'."}

    # Alleen doorgeven wat de bot zelf accepteert, en strategie/bluf_kans van de
    # inzending gebruiken in plaats van wat de aanvrager verzint -- anders test je
    # de bot van je klasgenoot met een instelling die hij nooit gekozen heeft.
    toegestaan = _functie_parameternamen(code, functienaam)
    vast = {"strategie": strategie, "bluf_kans": bluf_kans}
    opgeschoond = []
    for testgeval in testgevallen:
        if "hand" not in testgeval:
            return {"acties": None, "foutmelding": "Elk testgeval heeft minstens een 'hand' nodig."}
        samen = {**testgeval, **{k: v for k, v in vast.items() if v is not None}}
        opgeschoond.append({k: v for k, v in samen.items() if k in toegestaan})

    acties, fout = _draai_in_apart_proces(code, functienaam, opgeschoond)
    if fout:
        return {"acties": None, "foutmelding": fout}
    return {"acties": acties, "foutmelding": None, "gebruikte_parameters": sorted(toegestaan)}
