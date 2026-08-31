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
TOEGESTANE_STRATEGIEEN = {"tight", "loose", "balanced", "aggressive"}
BLUF_KANS_MIN, BLUF_KANS_MAX = 0.0, 1.0

# Testhanden en -stacks waarmee we de bot ECHT even laten spelen (niet met
# één vaste invoer, maar met een klein setje representatieve situaties). Zo
# vinden we bugs die alleen bij een zwakke hand of een lage stack optreden.
_TEST_HANDEN = [["A", "K"], ["7", "2"], ["Q", "Q"]]
_TEST_STACKS = [1000, 50]

# Per week ligt vast welke functienaam de bot moet aanbieden, en of hij een
# strategie / bluf_kans verwacht. Dit groeit mee met de cursus.
VERWACHTE_FUNCTIES = {
    1: {"functienaam": "kies_actie", "heeft_strategie": False, "heeft_bluf_kans": False},
    3: {"functienaam": "kies_actie", "heeft_strategie": True, "heeft_bluf_kans": False},
    5: {"functienaam": "kies_actie", "heeft_strategie": True, "heeft_bluf_kans": True},
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


def _bouw_testgevallen(config: dict, strategie, bluf_kans) -> list[dict]:
    """
    Bouwt een klein setje realistische aanroepen van kies_actie(), met
    wisselende hand en (vanaf Week 3) stack. We testen dus niet met 1 hand,
    maar meteen met een sterke hand, een zwakke hand en een pocket pair, op
    een normale én een lage stack.
    """
    gevallen = []
    for hand in _TEST_HANDEN:
        if not config["heeft_strategie"]:
            gevallen.append({"hand": hand})
            continue
        for stack in _TEST_STACKS:
            args = {"hand": hand, "stack": stack, "strategie": strategie}
            if config["heeft_bluf_kans"]:
                args["bluf_kans"] = bluf_kans
            gevallen.append(args)
    return gevallen


def valideer_bot_code(code: str, week: int, strategie: str | None = None, bluf_kans: float | None = None) -> dict:
    """
    Retourneert {"geldig": bool, "foutmelding": str | None, "actie_resultaten": list | None}.

    "geldig" betekent: geen verboden imports, functie met de juiste naam
    bestaat, strategie/bluf_kans zijn (indien van toepassing) geldig, en de
    bot draait zonder crash op een setje representatieve testhanden/stacks,
    en geeft daarbij steeds een herkenbare actie terug.
    """
    if week not in VERWACHTE_FUNCTIES:
        return {"geldig": False, "foutmelding": f"Onbekende week: {week}", "actie_resultaten": None}

    config = VERWACHTE_FUNCTIES[week]

    strategie_fout = _valideer_strategie_en_bluf_kans(config, strategie, bluf_kans)
    if strategie_fout:
        return {"geldig": False, "foutmelding": strategie_fout, "actie_resultaten": None}

    verboden_reden = _bevat_verboden_imports(code)
    if verboden_reden:
        return {"geldig": False, "foutmelding": verboden_reden, "actie_resultaten": None}

    functienaam = config["functienaam"]
    if not _bevat_functie(code, functienaam):
        return {
            "geldig": False,
            "foutmelding": f"Ik kan geen functie met de naam '{functienaam}()' vinden in je bestand.",
            "actie_resultaten": None,
        }

    testgevallen = _bouw_testgevallen(config, strategie, bluf_kans)

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
        }
    finally:
        os.remove(tijdelijk_pad)

    if proces.returncode != 0 or MARKER not in proces.stdout:
        foutregel = proces.stderr.strip().splitlines()[-1] if proces.stderr.strip() else "Onbekende fout."
        return {"geldig": False, "foutmelding": f"Je bot-code crasht: {foutregel}", "actie_resultaten": None}

    try:
        resultaat_json = proces.stdout.split(MARKER, 1)[1].strip().splitlines()[0]
        acties = json.loads(resultaat_json)["acties"]
    except (IndexError, json.JSONDecodeError, KeyError):
        return {
            "geldig": False,
            "foutmelding": "Kon het resultaat van je functie niet uitlezen.",
            "actie_resultaten": None,
        }

    for testgeval, actie in zip(testgevallen, acties):
        if not isinstance(actie, str) or actie.lower() not in TOEGESTANE_ACTIES:
            return {
                "geldig": False,
                "foutmelding": (
                    f"Bij hand {testgeval['hand']}"
                    + (f" en stack {testgeval['stack']}" if "stack" in testgeval else "")
                    + f" gaf je functie '{actie}' terug — verwacht een van {sorted(TOEGESTANE_ACTIES)}."
                ),
                "actie_resultaten": acties,
            }

    return {"geldig": True, "foutmelding": None, "actie_resultaten": acties}
