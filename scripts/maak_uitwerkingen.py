#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maakt uitwerkingen van de studentnotebooks.

    python3 scripts/maak_uitwerkingen.py
    python3 scripts/maak_uitwerkingen.py --week 1

De uitwerking is het studentnotebook met de open plekken ingevuld, zodat hij van
boven tot onder draait. Dat is niet alleen handig als modelantwoord: het is de
enige manier om te testen of de API het doet, want een notebook vol `___` komt
nooit tot de eerste request.

WAAR DE API STAAT
-----------------
De uitwerking haalt het adres uit de omgeving in plaats van het hard in te
typen. Zo draai je dezelfde notebooks tegen een andere server -- een datalab,
een lokale uvicorn -- zonder één cel aan te raken:

    export POKER_API_URL=https://jouw-datalab-adres
    export POKER_STUDENT_ID=500123456
    export POKER_TOKEN=...

Zonder die variabelen valt hij terug op de productie-API, en dan gedraagt de
uitwerking zich als het notebook van een student.

HOE DE UITWERKINGEN WORDEN BEWAARD
----------------------------------
Niet als losse notebooks -- dan lopen ze weg van het origineel zodra je een cel
in het studentnotebook verplaatst. In plaats daarvan staat per week een bestand
in scripts/uitwerkingen/ met de ingevulde cellen, elk met een stuk tekst dat in
precies één cel van het origineel voorkomt. Komt dat stuk er niet meer in voor,
of juist twee keer, dan stopt dit script. Dan is het notebook veranderd en moet
de uitwerking mee -- en dat merk je nu, niet een week later voor de klas.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
NOTEBOOKMAP = os.path.join(WORTEL, "notebooks")
UITVOERMAP = os.path.join(WORTEL, "uitwerkingen")
BRONMAP = os.path.join(HIER, "uitwerkingen")

API = "https://poker-analytics-api.onrender.com"

# Deze cel komt boven elke uitwerking te staan.
OPZET = f'''# ---------------------------------------------------------------------------
# Alleen in de uitwerking: waar praat dit notebook mee?
#
# Het studentnotebook heeft deze drie hard ingetypt. Hier komen ze uit de
# omgeving, zodat je dezelfde uitwerking tegen een andere server kunt draaien:
#
#     export POKER_API_URL=https://jouw-datalab-adres
#     export POKER_STUDENT_ID=500123456
#     export POKER_TOKEN=...
#
# Zonder die variabelen gaat het naar de productie-API.
#
# Daarnaast: de notebooks doen sys.path.append("..") om _hulpfuncties.py te
# vinden. Dat klopt voor een student, die zijn notebook naast dat bestand heeft
# staan. Vanuit deze map wijst ".." naar de repo-wortel en staan de hulpfuncties
# er niet, dus die map wordt hier toegevoegd -- dan is er één kopie in plaats van
# een tweede die stilletjes achterloopt.
# ---------------------------------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(os.getcwd())),
                                "notebooks"))

API_URL = os.environ.get("POKER_API_URL", "{API}")
STUDENT_ID = os.environ.get("POKER_STUDENT_ID", "vul_hier_je_student_id_in")
TOKEN = os.environ.get("POKER_TOKEN", "vul_hier_je_token_in")

print("API:       ", API_URL)
print("student_id:", STUDENT_ID)
'''

# Wat er in een CODEcel niet meer mag staan als de uitwerking af is.
OPEN_PLEKKEN = [
    ("___", r"___"),
    ("vul_hier", r"vul_hier"),
    ("vul hier", r"vul hier"),
    ("kale pass", r"^\s*pass\s*$"),
    ("jouw ... hier", r"#\s*jouw .* hier"),
    ("TODO", r"#\s*TODO"),
    ("kopieer hier", r"#\s*kopieer hier"),
]


def laad_bron(pad):
    naam = os.path.basename(pad)[:-3]
    spec = importlib.util.spec_from_file_location(f"uitwerking_{naam}", pad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.NOTEBOOKS


def pas_toe(nb, regels, notebooknaam):
    """Vervangt hele cellen. Elke `zoek` moet in precies één cel voorkomen."""
    for regel in regels:
        zoek, vervang = regel["zoek"], regel["vervang"]
        # Alleen in codecellen zoeken. De markdown eromheen beschrijft dezelfde
        # opdracht en bevat dus vaak letterlijk dezelfde regel; dat is geen
        # dubbele treffer maar de uitleg erboven.
        treffers = [i for i, c in enumerate(nb["cells"])
                    if c["cell_type"] == "code" and zoek in "".join(c["source"])]
        if len(treffers) != 1:
            raise SystemExit(
                f"{notebooknaam}: {zoek!r} komt in {len(treffers)} codecel(len) voor, "
                f"verwacht 1.\nHet notebook is veranderd; werk "
                f"scripts/uitwerkingen/ bij."
            )
        cel = nb["cells"][treffers[0]]
        cel["source"] = vervang.rstrip("\n").split("\n")
        cel["source"] = [r + "\n" for r in cel["source"][:-1]] + [cel["source"][-1]]
        cel["outputs"] = []
        cel["execution_count"] = None


def zet_opzet_bovenaan(nb):
    """De opzetcel vlak na de titel, zodat alles eronder hem al heeft."""
    import nbformat
    cel = nbformat.v4.new_code_cell(OPZET.rstrip("\n"))
    na = 1 if nb["cells"] and nb["cells"][0]["cell_type"] == "markdown" else 0
    nb["cells"].insert(na, cel)


def haal_harde_adressen_weg(nb):
    """
    De regels die API_URL, STUDENT_ID of TOKEN opnieuw zetten moeten eruit.

    Anders overschrijft cel 16 de omgevingsvariabele uit de opzetcel, en draai je
    alsnog tegen productie terwijl je denkt dat je het datalab test. Dat is het
    soort fout dat je pas merkt als je de verkeerde database vol hebt staan.
    """
    patronen = [
        re.compile(r'^API_URL\s*=\s*["\']https?://'),
        re.compile(r'^STUDENT_ID\s*=\s*["\']vul_hier'),
        re.compile(r'^TOKEN\s*=\s*["\']vul_hier'),
    ]
    weg = 0
    for cel in nb["cells"]:
        if cel["cell_type"] != "code":
            continue
        regels, nieuw = "".join(cel["source"]).split("\n"), []
        for r in regels:
            if any(p.match(r) for p in patronen):
                nieuw.append(f"# {r}    <- staat nu in de opzetcel bovenaan")
                weg += 1
            else:
                nieuw.append(r)
        cel["source"] = [x + "\n" for x in nieuw[:-1]] + [nieuw[-1]]
    return weg



def stuur_hulpfuncties_mee(nb):
    """
    lever_in() krijgt api_url=API_URL mee.

    Zonder dit gaat het inleveren naar het adres dat in _hulpfuncties.py staat --
    productie -- ook als POKER_API_URL ergens anders heen wijst. Dat merk je niet
    aan een foutmelding maar aan een inzending in de verkeerde database, en dat is
    precies het soort stille fout waarvoor je geen tweede kans krijgt. Gemeten op
    8 oktober 2026: de uitwerking van Werkcollege 1 postte naar onrender.com
    terwijl hij tegen een lokale server draaide.
    """
    aangepast = 0
    for cel in nb["cells"]:
        if cel["cell_type"] != "code":
            continue
        bron = "".join(cel["source"])
        if "lever_in(" not in bron or "api_url=" in bron:
            continue
        # De aanroep eindigt op de eerste ) die de haakjes sluit; in dit notebook
        # staat hij altijd op één regel.
        nieuw = re.sub(r"lever_in\((.*?)\)(?=\s*$|\s*\n)",
                       r"lever_in(\1, api_url=API_URL)", bron, flags=re.M)
        if nieuw != bron:
            cel["source"] = [r + "\n" for r in nieuw.split("\n")[:-1]] + [nieuw.split("\n")[-1]]
            aangepast += 1
    return aangepast


def controleer(nb, naam):
    """Wat er nog open staat. Geeft een lijst (cel, wat) terug."""
    open_nog = []
    for i, cel in enumerate(nb["cells"]):
        if cel["cell_type"] != "code":
            continue
        bron = "".join(cel["source"])
        if bron.lstrip().startswith("# ---"):      # de opzetcel zelf
            continue
        # Regels die dit script zelf heeft uitgezet tellen niet als open plek:
        # daar staat de oude waarde nog in, maar als commentaar.
        bron = "\n".join(r for r in bron.split("\n")
                          if not r.rstrip().endswith("<- staat nu in de opzetcel bovenaan"))
        for wat, patroon in OPEN_PLEKKEN:
            if re.search(patroon, bron, re.M):
                open_nog.append((i, wat))
    return open_nog


def main():
    import nbformat
    p = argparse.ArgumentParser()
    p.add_argument("--week", type=int, help="alleen deze week")
    args = p.parse_args()

    bronnen = sorted(f for f in os.listdir(BRONMAP)
                     if f.startswith("week") and f.endswith(".py"))
    if args.week:
        bronnen = [f for f in bronnen if f == f"week{args.week}.py"]
        if not bronnen:
            raise SystemExit(f"Geen scripts/uitwerkingen/week{args.week}.py gevonden.")

    os.makedirs(UITVOERMAP, exist_ok=True)
    totaal_open = 0
    for bronbestand in bronnen:
        for notebooknaam, regels in laad_bron(os.path.join(BRONMAP, bronbestand)).items():
            bron = os.path.join(NOTEBOOKMAP, notebooknaam)
            if not os.path.exists(bron):
                raise SystemExit(f"Notebook niet gevonden: {bron}")
            nb = nbformat.read(bron, as_version=4)

            pas_toe(nb, regels, notebooknaam)
            zet_opzet_bovenaan(nb)
            weg = haal_harde_adressen_weg(nb)
            meegestuurd = stuur_hulpfuncties_mee(nb)
            open_nog = controleer(nb, notebooknaam)
            totaal_open += len(open_nog)

            nbformat.validator.normalize(nb)
            nbformat.validate(nb)
            doel = os.path.join(UITVOERMAP, notebooknaam.replace(".ipynb", "_uitwerking.ipynb"))
            with open(doel, "w") as f:
                json.dump(nb, f, indent=1, ensure_ascii=False)
                f.write("\n")

            melding = f"   {os.path.basename(doel):<42s} {len(regels)} cellen ingevuld"
            if weg:
                melding += f", {weg} hard adres uitgezet"
            if meegestuurd:
                melding += f", {meegestuurd}x api_url meegegeven"
            print(melding)
            for i, wat in open_nog:
                print(f"      LET OP: cel {i} heeft nog {wat}")

    print(f"\n-> {UITVOERMAP}")
    if totaal_open:
        print(f"{totaal_open} open plek(ken) over. Die horen in scripts/uitwerkingen/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
