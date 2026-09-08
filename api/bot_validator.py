"""
Technische validatie van ingeleverde pokerbot-code.

Draait de code van de student NOOIT in het eigen proces van de API (dat zou
elke fout of oneindige loop van een student meteen de server laten crashen).
In plaats daarvan: wegschrijven naar een tijdelijk bestand en uitvoeren in
een apart subprocess met een timeout en zonder netwerktoegang.
"""
import ast
import json
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
TOEGESTANE_STRATEGIEEN = {"tight", "loose", "balanced", "aggressive"}
BLUF_KANS_MIN, BLUF_KANS_MAX = 0.0, 1.0

# Testhanden en -stacks waarmee we de bot ECHT even laten spelen (niet met
# één vaste invoer, maar met een klein setje representatieve situaties). Zo
# vinden we bugs die alleen bij een zwakke hand of een lage stack optreden.
_TEST_HANDEN = [["A", "K"], ["7", "2"], ["Q", "Q"]]
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
    1: {"functienaam": "kies_actie", "heeft_stack": False, "heeft_strategie": False, "heeft_bluf_kans": False},
    3: {"functienaam": "kies_actie", "heeft_stack": True, "heeft_strategie": False, "heeft_bluf_kans": False},
    5: {"functienaam": "kies_actie", "heeft_stack": True, "heeft_strategie": True, "heeft_bluf_kans": True},
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
    if config["heeft_strategie"]:
        if strategie is None:
            return (
                "Deze week hoort er een 'strategie' bij je inzending, maar die ontbreekt. "
                f"Kies uit: {', '.join(sorted(TOEGESTANE_STRATEGIEEN))}."
            )
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


_RONDE_PARAMETERS = {"ronde", "pot", "inzet_om_te_callen", "tegenstander_acties_deze_hand"}
# Representatieve situaties op elke straat, om te checken dat een bot die
# ronde/pot/inzet_om_te_callen/tegenstander_acties_deze_hand gebruikt, in elke
# fase van de hand een herkenbare actie teruggeeft (niet alleen preflop, waar
# de meeste bots het eerst getest worden) -- inclusief een variatie in wat
# tegenstanders deze hand al gedaan hebben, want dat is precies waar een bot
# die daarop reageert onderuit kan gaan (bv. een lege lijst niet aankunnen).
_TEST_RONDE_SCENARIOS = [
    {"ronde": "preflop", "pot": 30, "inzet_om_te_callen": 10, "tegenstander_acties_deze_hand": []},
    {"ronde": "flop", "pot": 120, "inzet_om_te_callen": 0, "tegenstander_acties_deze_hand": [
        {"bot_naam": "TestBot", "actie": "call", "bedrag": 20},
    ]},
    {"ronde": "river", "pot": 400, "inzet_om_te_callen": 200, "tegenstander_acties_deze_hand": [
        {"bot_naam": "TestBot", "actie": "raise", "bedrag": 200},
    ]},
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
            if config["heeft_strategie"]:
                basis["strategie"] = strategie
            if config["heeft_bluf_kans"]:
                basis["bluf_kans"] = bluf_kans
            if parameternamen & _RONDE_PARAMETERS:
                for scenario in _TEST_RONDE_SCENARIOS:
                    args = dict(basis)
                    args.update({k: v for k, v in scenario.items() if k in parameternamen})
                    gevallen.append(args)
            else:
                gevallen.append(basis)
    return gevallen


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
        return {"geldig": False, "foutmelding": f"Onbekende week: {week}", "actie_resultaten": None, "constante_bot": False}

    config = VERWACHTE_FUNCTIES[week]

    strategie_fout = _valideer_strategie_en_bluf_kans(config, strategie, bluf_kans)
    if strategie_fout:
        return {"geldig": False, "foutmelding": strategie_fout, "actie_resultaten": None, "constante_bot": False}

    verboden_reden = _bevat_verboden_imports(code)
    if verboden_reden:
        return {"geldig": False, "foutmelding": verboden_reden, "actie_resultaten": None, "constante_bot": False}

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
    testgevallen_json = json.dumps(testgevallen)
    footer = textwrap.dedent(f"""
        testgevallen = json.loads('''{testgevallen_json}''')
        resultaten = []
        for testgeval in testgevallen:
            resultaten.append({functienaam}(**testgeval))
        print("{MARKER}" + json.dumps({{"acties": resultaten}}))
    """)
    runner_script = "import json\n\n" + code + "\n\n" + footer

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(runner_script)
        tijdelijk_pad = f.name

    try:
        proces = subprocess.run(
            [sys.executable, "-I", tijdelijk_pad],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "geldig": False,
            "foutmelding": f"Je bot-code draaide langer dan {TIMEOUT_SECONDS} seconden (oneindige loop?).",
            "actie_resultaten": None,
            "constante_bot": False,
        }
    finally:
        os.remove(tijdelijk_pad)

    if proces.returncode != 0 or MARKER not in proces.stdout:
        foutregel = proces.stderr.strip().splitlines()[-1] if proces.stderr.strip() else "Onbekende fout."
        return {"geldig": False, "foutmelding": f"Je bot-code crasht: {foutregel}", "actie_resultaten": None, "constante_bot": False}

    try:
        resultaat_json = proces.stdout.split(MARKER, 1)[1].strip().splitlines()[0]
        acties = json.loads(resultaat_json)["acties"]
    except (IndexError, json.JSONDecodeError, KeyError):
        return {
            "geldig": False,
            "foutmelding": "Kon het resultaat van je functie niet uitlezen.",
            "actie_resultaten": None,
            "constante_bot": False,
        }

    toegestane_acties = TOEGESTANE_ACTIES_MET_STACK if config["heeft_stack"] else TOEGESTANE_ACTIES
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
                "constante_bot": False,
            }

    return {
        "geldig": True,
        "foutmelding": None,
        "actie_resultaten": acties,
        "constante_bot": _is_constante_bot(acties),
    }
