#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maakt de notebooks voor semester 2: dezelfde stof, maar de API pas in week 3.

    python3 scripts/maak_sem2_notebooks.py

Leest notebooks/ en schrijft notebooks_sem2/. Afgeleid en niet met de hand
bijgehouden, zodat een verbetering in het origineel vanzelf meekomt.

WAAROM
------
De API zat vanaf werkcollege 1 in de stof: inleveren in WC1, en in WC2 een deel
over wat een API is (20 min), het toernooi ophalen (15) en peer review (10).
Dat is 45 van de 85 minuten van WC2, in dezelfde week waarin tien
programmeerconcepten binnenkomen -- en het bracht een categorie fouten mee die
niets met programmeren te maken heeft: tokens, 401's, netwerk.

Week 1 en 2 werken nu uit data/voorbeeldtoernooi.json: een toernooi dat
werkelijk gespeeld is, met namen in plaats van studentnummers. De API komt in
week 3, als er een bot is die het waard is om in te leveren.

HOE EEN WIJZIGING WORDT AANGEWEZEN
----------------------------------
Niet op celnummer -- dat schuift zodra er iets bij komt -- maar op een stuk tekst
dat in precies één cel moet voorkomen. Klopt dat niet meer, dan stopt het script.
Dan is het bronnotebook veranderd en moet deze bewerking mee.
"""
import argparse
import json
import os
import sys

import nbformat

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
BRON = os.path.join(WORTEL, "notebooks")
# De uitvoer hoort bij het semester, niet bij de repo: de notebooks staan in
# HvA_voorbereidingen/IDS_2026_2027_SEM2/Werkcolleges/. De generator en de
# bronnotebooks blijven hier, want dat is code.
DOEL = '/Users/jerome/Library/Mobile Documents/com~apple~CloudDocs/Full_Stack_dev/HvA_voorbereidingen/IDS_2026_2027_SEM2/Werkcolleges'

LAAD_TOERNOOI = '''import json

# Dit toernooi is echt gespeeld, door een eerdere lichting. De namen zijn
# verzonnen, de getallen niet: dezelfde stacks, hetzelfde foldgedrag, dezelfde
# uitschieters. Vanaf week 3 haal je je eigen toernooi op bij de API; tot die
# tijd werk je hiermee, zodat je je op het programmeren kunt richten.
with open("data/voorbeeldtoernooi.json") as f:
    toernooi_resultaat = json.load(f)

# In deze uitslag staat jouw bot nog niet -- vanaf week 3 wel. Kies er zolang
# eentje om te volgen; alles hieronder rekent met deze naam. Ravi staat net onder
# het midden, en dat is een eerlijker startpunt dan de nummer 1: de vraag onderaan
# is of je boven of onder de helft zit.
mijn_bot = "Ravi"

print("deelnemers:", len(toernooi_resultaat["namen_deelnemers"]))
print("logregels: ", len(toernooi_resultaat["hand_log"]))
print("je volgt:  ", mijn_bot)'''


def zoek_cel(nb, stuk, soort="code"):
    """De enige cel die `stuk` bevat. Meer of minder dan één is een fout."""
    treffers = [i for i, c in enumerate(nb["cells"])
                if c["cell_type"] == soort and stuk in "".join(c["source"])]
    if len(treffers) != 1:
        raise SystemExit(f"{stuk!r} komt in {len(treffers)} {soort}-cellen voor, verwacht 1.\n"
                         f"Het bronnotebook is veranderd; werk dit script bij.")
    return treffers[0]


def zet_bron(cel, tekst):
    regels = tekst.rstrip("\n").split("\n")
    cel["source"] = [r + "\n" for r in regels[:-1]] + [regels[-1]]
    cel["outputs"] = []
    cel["execution_count"] = None


def knip(nb, van_stuk, tot_stuk, van_soort="markdown", tot_soort="markdown"):
    """Haalt de cellen weg van `van_stuk` tot en met de cel vóór `tot_stuk`."""
    van = zoek_cel(nb, van_stuk, van_soort)
    tot = zoek_cel(nb, tot_stuk, tot_soort)
    if tot <= van:
        raise SystemExit(f"{tot_stuk!r} staat vóór {van_stuk!r}; knippen zou de verkeerde kant op gaan.")
    weg = tot - van
    del nb["cells"][van:tot]
    return weg


def werkcollege1(nb):
    """Inleveren eruit: de bot blijft deze week op je eigen machine."""
    weg = knip(nb, "### Stap B: de benodigde imports", "## Reflectievragen")
    i = zoek_cel(nb, "### Stap A: maak `mijn_bot_week1.py`", "markdown")
    nb["cells"][i]["source"] = [
        "### Stap A: zet je bot in een los bestand\n", "\n",
        "Je bot staat nu in een cel van dit notebook. Zet hem daarnaast in een eigen "
        "bestand, want vanaf week 3 lever je dat bestand in — en in week 2 laat je "
        "hem ermee tegen een klasgenoot spelen.\n", "\n",
        "De regel `%%writefile` bovenaan een cel schrijft de rest van die cel naar "
        "een bestand in plaats van hem uit te voeren.\n"]
    # de uitleg ná de writefile-cel mag niet meer naar het inleveren verwijzen
    j = zoek_cel(nb, "Writing mijn_bot_week1.py", "markdown")
    nb["cells"][j]["source"] = [
        "Draai je de cel hierboven, dan zie je `Writing mijn_bot_week1.py` verschijnen "
        "en staat het bestand naast je notebook.\n", "\n",
        "**Deze week lever je nog niets in.** Bewaar `mijn_bot_week1.py` op een plek "
        "die je terugvindt: in week 2 heb je hem nodig, en in week 3 gaat hij naar de "
        "server.\n"]
    return weg, 2


def werkcollege2(nb):
    """De API-les eruit, het toernooi uit een bestand, peer review eruit."""
    weg = knip(nb, "## Deel 2 — Hoe werkt een API", "## Deel 3 — Het toernooi bekijken")
    weg += knip(nb, "## Deel 5 — Peer review via de API", "## Reflectievragen")
    i = zoek_cel(nb, 'f"{API_URL}/toernooi/1"')
    zet_bron(nb["cells"][i], LAAD_TOERNOOI)
    k = zoek_cel(nb, "mijn_bot = next(naam for naam in eindstand")
    zet_bron(nb["cells"][k], """eindstand = toernooi_resultaat["eindstand_per_bot"]

op_volgorde = sorted(eindstand, key=eindstand.get, reverse=True)

print("de top 5:")
for naam in op_volgorde[:5]:
    print("   ", naam, eindstand[naam])

print()
print(mijn_bot, "staat op:", eindstand[mijn_bot])
print("plek:", op_volgorde.index(mijn_bot) + 1, "van de", len(op_volgorde))""")

    j = zoek_cel(nb, "De eerste keer dat iemand in de klas dit ophaalt", "markdown")
    nb["cells"][j]["source"] = [
        "Geen internet nodig: het bestand staat naast je notebook in de map `data/`. "
        "Vanaf week 3 haal je hier je eigen toernooi op bij de API, en dan zie je je "
        "eigen bot in deze uitslag staan.\n"]
    return weg, 3


def werkcollege3(nb):
    """Allebei de toernooi-ophalers uit een bestand."""
    aangepast = 0
    for cel in nb["cells"]:
        if cel["cell_type"] != "code":
            continue
        bron = "".join(cel["source"])
        if 'f"{API_URL}/toernooi/1"' not in bron:
            continue
        staart = bron.split("toernooi_resultaat = response.json()", 1)[1]
        zet_bron(cel, LAAD_TOERNOOI.rsplit("\nprint(", 1)[0].rstrip() + "\n" + staart.lstrip("\n"))
        aangepast += 1
    if aangepast != 2:
        raise SystemExit(f"{aangepast} toernooi-ophalers gevonden in WC3, verwacht 2.")
    return 0, aangepast



API_LES = """---

## Deel 1a — Wat gebeurde er toen je inleverde? (20 min)

Maandag draaide je één regel: `lever_in(...)`. Daar ging een bericht over het
internet, en er kwam een antwoord terug. Nu je bot in een toernooi heeft gespeeld,
is het de moeite waard om te kijken wat daar precies gebeurde.

**Client en server.** Jouw notebook is de *client*: die stelt een vraag. Ergens
anders draait de *server*: die geeft antwoord. Elk bericht heeft een adres,
eventueel een sleutel, en een antwoord met een getal erbij.

**Dat getal is de statuscode:**

| code | betekent |
|---|---|
| `200` | gelukt |
| `401` | wie ben jij? — je token ontbreekt of klopt niet |
| `404` | dat adres bestaat niet — vaak een typefout |
| `422` | je vraag mist iets, bijvoorbeeld je `student_id` |

Hieronder stel je dezelfde vraag drie keer: zonder sleutel, met sleutel, en met een
typefout in het adres. **Voorspel eerst welke code je bij elk verwacht.**"""

API_CODE = "\n".join([
    "import requests",
    "",
    'API_URL = "https://poker-analytics-api.onrender.com"',
    "",
    "# 1 - zonder token",
    'zonder = requests.get(f"{API_URL}/status/{STUDENT_ID}/3")',
    'print("zonder token:  ", zonder.status_code)',
    "",
    "# 2 - met token. De sleutel gaat mee in een 'header': extra informatie naast",
    "#     het adres, die niet in de url zelf staat.",
    "met = requests.get(",
    '    f"{API_URL}/status/{STUDENT_ID}/3",',
    '    headers={"Authorization": f"Bearer {TOKEN}"},',
    ")",
    'print("met token:     ", met.status_code)',
    "",
    "# 3 - met een typefout in het adres",
    "fout = requests.get(",
    '    f"{API_URL}/statuz/{STUDENT_ID}/3",',
    '    headers={"Authorization": f"Bearer {TOKEN}"},',
    ")",
    'print("verkeerd adres:", fout.status_code)',
    "",
    "print()",
    'print("wat de server terugstuurt als het lukt:")',
    "met.json()",
])

API_NA = """🤔 Klopten je voorspellingen? Let vooral op het verschil tussen `401` en `404`:
de eerste zegt *ik weet niet wie je bent*, de tweede *dat bestaat hier niet*. Als je
straks een foutmelding krijgt, scheelt dat een hoop zoeken.

`.json()` zet het antwoord om in een Python-dictionary. Dat is het enige wat je van
een API hoeft te onthouden: je stelt een vraag aan een adres, en je krijgt een
dictionary terug — en met dictionaries werk je sinds week 1."""


def werkcollege5(nb):
    """De API-les erbij, nu met hun eigen toernooi ernaast. Peer review eruit."""
    import nbformat
    weg = knip(nb, "## Deel 4 — Peer review via de API", "## Deel 5 — Aftrap Groepscase 2")
    # Niet hernummeren: er staan kruisverwijzingen in de tekst ("in Deel 6 ga je
    # zien...") en die breken dan stilletjes. Het gat krijgt een regel uitleg.
    j = zoek_cel(nb, "## Deel 5 — Aftrap Groepscase 2", "markdown")
    nb["cells"].insert(j, nbformat.v4.new_markdown_cell(
        "> **Deel 4 staat niet in dit notebook.** Het beoordelen van elkaars "
        "grafieken doe je in de Streamlit-hub, waar je ze gewoon ziet staan in "
        "plaats van ze uit een API te moeten peuteren. De deelnummers hieronder "
        "lopen door zoals ze waren."))
    # Zonder deze drie blijft WC5 op 130 minuten staan in een vak van 100.
    naar_huiswerk(nb, "## Deel 3 — De spelregels terugvinden in je eigen data (20 min)",
                  "## Deel 3 — De spelregels terugvinden in je eigen data (huiswerk, ± 20 min)")
    naar_huiswerk(nb, "## Deel 7 — Van notebook naar script: de opstap naar Streamlit (10 min)",
                  "## Deel 7 — Van notebook naar script: de opstap naar Streamlit (huiswerk, ± 10 min)")
    naar_huiswerk(nb, "## Deel 5 — Aftrap Groepscase 2 (15 min)",
                  "## Deel 5 — Aftrap Groepscase 2 (in het hoorcollege, 15 min)")

    i = zoek_cel(nb, "## Deel 2 — Resultaten: v2 vs v1", "markdown")
    nb["cells"][i:i] = [
        nbformat.v4.new_markdown_cell(API_LES),
        nbformat.v4.new_code_cell(API_CODE),
        nbformat.v4.new_markdown_cell(API_NA),
    ]
    return weg, 6



def naar_huiswerk(nb, kop, nieuwe_kop):
    """Een deel blijft staan maar wordt huiswerk in plaats van klassikaal."""
    i = zoek_cel(nb, kop, "markdown")
    bron = "".join(nb["cells"][i]["source"])
    nb["cells"][i]["source"] = bron.replace(kop, nieuwe_kop, 1)


def werkcollege4b(nb):
    """Pot odds eruit, de spelregels naar voorwerk."""
    weg = knip(nb, "## Deel 6 — Pot odds", "## Deel 7 — Bot v2 afmaken")
    naar_huiswerk(nb,
        "## Deel 2 — Pokerbot Upgrade Week 3: hoe het spel écht werkt (± 16 min)",
        "## Deel 2 — De regels van het spel (voorwerk, ± 16 min)")
    i = zoek_cel(nb, "## Deel 2 — De regels van het spel", "markdown")
    bron = "".join(nb["cells"][i]["source"])
    nb["cells"][i]["source"] = bron.rstrip() + (
        "\n\n> **Doe dit vóór het werkcollege.** Je hoeft er niemand bij te hebben: "
        "het zijn de spelregels, geen programmeerstof. Wie ze al kent kan doorbladeren.\n")
    return weg, 2


def werkcollege6(nb):
    """Het volste werkcollege van het blok: 159 minuten in een vak van 100."""
    weg = knip(nb, "## Deel 9 — De winkans-ranglijst in beeld", "## Deel 10 — Peer-vergelijking")
    weg += knip(nb, "## Deel 10 — Peer-vergelijking", "## Deel 11 — Van grafiek naar Streamlit-app")
    naar_huiswerk(nb, "## Deel 8 — Multi-week: laat je eigen vooruitgang zien (15 min)",
                  "## Deel 8 — Multi-week: laat je eigen vooruitgang zien (huiswerk, ± 15 min)")
    naar_huiswerk(nb, "## Deel 11 — Van grafiek naar Streamlit-app (15 min)",
                  "## Deel 11 — Van grafiek naar Streamlit-app (huiswerk, ± 15 min)")
    naar_huiswerk(nb, "## Deel 3 — Eigen bot uitlichten (22 min)",
                  "## Deel 3 — Eigen bot uitlichten (15 min)")
    i = zoek_cel(nb, "## Deel 11 — Van grafiek naar Streamlit-app", "markdown")
    nb["cells"].insert(i, nbformat.v4.new_markdown_cell(
        "> **Deel 9 en 10 staan niet in dit notebook.** De winkans-ranglijst was de "
        "enige pokerinhoud op een middag die verder over visualisatie gaat, en het "
        "vergelijken met klasgenoten doe je in de Streamlit-hub. De deelnummers "
        "hieronder lopen door zoals ze waren."))
    return weg, 4


def werkcollege8(nb):
    """De kaart hoort bij werkcollege 9, waar hij het onderwerp is."""
    weg = knip(nb, "## Deel 6 — De kaart van de klas", "## Reflectievragen")
    naar_huiswerk(nb, "### 3.6 — De uitgebreide log: één regel per beslissing (extra)",
                  "### 3.6 — De uitgebreide log: één regel per beslissing (huiswerk, ± 8 min)")
    i = zoek_cel(nb, "## Reflectievragen", "markdown")
    nb["cells"].insert(i, nbformat.v4.new_markdown_cell(
        "> **De kaart van de klas staat niet meer in dit notebook.** Werkcollege 9 "
        "gaat er een hele middag over, met echte gemeentegrenzen en een popup per "
        "gemeente; een kwartier hier voegde daar niets aan toe."))
    return weg, 2


def werkcollege9(nb):
    """Peer-vergelijking naar de hub; de detail-popup iets korter."""
    weg = knip(nb, "## Deel 6 — Peer-vergelijking: de 3-seconden-test", "## Reflectievragen")
    naar_huiswerk(nb, "## Deel 4 — Level 2: de detail-popup (25 min)",
                  "## Deel 4 — Level 2: de detail-popup (18 min)")
    # Er staat al 40 minuten voorwerk met geopandas; data ophalen hoort daarbij.
    naar_huiswerk(nb, "## Deel 2 — Data verzamelen (15 min)",
                  "## Deel 2 — Data verzamelen (voorwerk, ± 15 min)")
    i = zoek_cel(nb, "## Reflectievragen", "markdown")
    nb["cells"].insert(i, nbformat.v4.new_markdown_cell(
        "> **De 3-seconden-test doe je in de Streamlit-hub.** Daar staan de kaarten "
        "van je klasgenoten naast elkaar, en dat werkt beter dan ze hier een voor een "
        "op te halen."))
    return weg, 4


BEWERKINGEN = {
    "Week1_Werkcollege1.ipynb": werkcollege1,
    "Week1_Werkcollege2.ipynb": werkcollege2,
    "Week2_Werkcollege3.ipynb": werkcollege3,
    "Week3_Werkcollege4.ipynb": werkcollege4b,
    "Week3_Werkcollege5.ipynb": werkcollege5,
    "Week4_Werkcollege6.ipynb": werkcollege6,
    "Week5_Werkcollege8.ipynb": werkcollege8,
    "Week6_Werkcollege9.ipynb": werkcollege9,
}


def main():
    p = argparse.ArgumentParser()
    p.parse_args()

    os.makedirs(DOEL, exist_ok=True)
    for naam, bewerk in BEWERKINGEN.items():
        nb = nbformat.read(os.path.join(BRON, naam), as_version=4)
        voor = len(nb["cells"])
        weg, aangepast = bewerk(nb)
        nbformat.validator.normalize(nb)
        nbformat.validate(nb)
        doel = os.path.join(DOEL, naam)
        with open(doel, "w") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"   {naam:<28s} {voor} -> {len(nb['cells'])} cellen "
              f"({weg} weg, {aangepast} aangepast)")

    # Controle: er mag geen netwerkaanroep meer in staan.
    import re
    # Alleen week 1 en 2 moeten schoon zijn. Vanaf week 3 hoort er juist wél
    # netwerk in te zitten -- dat is het punt van de verhuizing.
    for naam in [n for n in BEWERKINGEN if n.startswith(("Week1", "Week2"))]:
        nb = nbformat.read(os.path.join(DOEL, naam), as_version=4)
        code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
        resten = re.findall(r"requests\.(get|post)|lever_in\(|onrender\.com", code)
        vlag = "geen netwerk" if not resten else f"LET OP: nog {len(resten)}x {set(resten)}"
        print(f"   {naam:<28s} {vlag}")
    print(f"\n-> {DOEL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
