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
    """Inleveren eruit, en extra oefening met if/else en functies erbij."""
    """Inleveren eruit: de bot blijft deze week op je eigen machine."""
    weg = knip(nb, "### Stap B: de benodigde imports", "## Reflectievragen")
    # De kop van Deel 4 stond vóór Stap A en overleefde het knippen, maar hij
    # belooft iets wat er niet meer in staat.
    naar_huiswerk(nb, "## Deel 4 — Inleveren via de API (huiswerk, ± 15 min)",
                  "## Deel 4 — Je bot in een eigen bestand (huiswerk, ± 5 min)")
    k = zoek_cel(nb, "## Deel 4 — Je bot in een eigen bestand", "markdown")
    nb["cells"][k]["source"] = (
        "---\n\n## Deel 4 — Je bot in een eigen bestand (huiswerk, ± 5 min)\n\n"
        "Je bot staat nu in een cel. Zet hem daarnaast in een los bestand: in "
        "werkcollege 2 laat je hem daarmee tegen een klasgenoot spelen, en vanaf "
        "week 3 is het het bestand dat je inlevert.\n")

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
    # Het deck telde 13 losse waarden, en dan is een paar met random.sample
    # onmogelijk: de call-tak van de voorbeeldbot vuurde nooit. De tekst eronder
    # belooft 5% call en vraagt zelfs waarom die tak zo weinig vuurt -- met vier
    # kaarten van elke waarde klopt dat weer, en blijft een hand ["A", "K"] zodat
    # hand[0] == hand[1] een paar herkent.
    d = zoek_cel(nb, "deck = kaartwaarden  # uit Deel 1")
    bron = "".join(nb["cells"][d]["source"])
    nb["cells"][d]["source"] = bron.replace(
        "deck = kaartwaarden  # uit Deel 1",
        "# Vier kaarten van elke waarde: 52 stuks, net als een echt deck. Zonder die\n"
        "# maal vier kun je nooit een paar trekken.\ndeck = kaartwaarden * 4")

    _, erbij = oefening_wc1(nb)
    return weg, 3 + erbij


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

    # Deel 2 was de API-les en is weg; de nummers schuiven bewust niet op.
    g = zoek_cel(nb, "## Deel 3 — Het toernooi bekijken", "markdown")
    nb["cells"].insert(g, nbformat.v4.new_markdown_cell(
        "> **Deel 2 staat niet in dit notebook.** Dat ging over hoe een API werkt, "
        "en dat komt in week 3 — op het moment dat je er zelf een nodig hebt om je "
        "bot in te leveren. De deelnummers hieronder lopen door zoals ze waren."))
    _, erbij = oefening_wc2(nb)
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



# ---------------------------------------------------------------------------
# Extra oefening in week 1 en 2: if/else, functies, tracing en flowcharts.
#
# Er is ruimte: werkcollege 1 gebruikt 40 van zijn 100 minuten en werkcollege 2
# na de verhuizing 55. Dat is precies de week waarin tien programmeerconcepten
# binnenkomen, dus die ruimte gaat naar oefenen met de twee die alles dragen --
# if/elif/else en functies -- in de vormen waarvan het onderzoek zegt dat ze
# werken: eerst voorspellen, dan natrekken, dan pas zelf schrijven.
# ---------------------------------------------------------------------------

TRACE_KOP = """---

## Deel 1b — Regel voor regel meekijken (10 min)

Je hebt nu `if`, `else` en een `for`-loop gezien. De vraag is niet of je ze kunt
*lezen* maar of je kunt voorspellen wat ze **doen** — en dat is iets anders.

Hieronder staat een stukje code. Draai het nog niet. Vul eerst de tabel in: wat
staat er in elke variabele, na elke doorloop van de loop?

```python
kaarten = ["A", "7", "K", "3"]
hoog = 0
laag = 0

for kaart in kaarten:
    if kaart in ["A", "K", "Q", "J"]:
        hoog = hoog + 1
    else:
        laag = laag + 1
```

| na kaart | `kaart` | `hoog` | `laag` |
|---|---|---|---|
| 1e | `"A"` | | |
| 2e | | | |
| 3e | | | |
| 4e | | | |

Vul hem met de hand in — op papier of in de cel hieronder als tekst. Daarna pas
draaien."""

TRACE_CODE = "\n".join([
    "kaarten = [\"A\", \"7\", \"K\", \"3\"]",
    "hoog = 0",
    "laag = 0",
    "",
    "for kaart in kaarten:",
    "    if kaart in [\"A\", \"K\", \"Q\", \"J\"]:",
    "        hoog = hoog + 1",
    "    else:",
    "        laag = laag + 1",
    "    print(kaart, \"-> hoog:\", hoog, \"laag:\", laag)",
    "",
    "print()",
    "print(\"eind:\", hoog, \"hoog en\", laag, \"laag\")",
])

TRACE_NA = """🤔 Klopte je tabel? De twee plekken waar het meestal misgaat:

- **`hoog = hoog + 1`** is geen bewering maar een opdracht: *neem wat er in `hoog`
  staat, tel er 1 bij op, en zet dat terug*. Een variabele houdt één waarde vast,
  niet een reeks.
- **De `else` hoort bij de `if` erboven**, en wordt alleen uitgevoerd als die `if`
  onwaar was. Hij draait niet "ook even".

💡 Deze tabel invullen heet *tracen*. Het klinkt als iets voor beginners, maar uit
onderzoek blijkt het de beste voorspeller van of je straks zelf code kunt
schrijven. Doe het bij elk stuk code dat je niet meteen snapt."""

SCHEMA_KOP = """---

## Deel 1c — Van schema naar code, en terug (10 min)

Een `if/elif/else` is een schema met vertakkingen. Hieronder staat er een
getekend. **Schrijf hem om naar code** — en let op de volgorde: wie als eerste
past, wint.

```mermaid
flowchart TD
    A["hand"] --> B{"is het een paar?"}
    B -- ja --> C["raise"]
    B -- nee --> D{"zit er een A of K in?"}
    D -- ja --> E["call"]
    D -- nee --> F["fold"]
```

Noem de functie `kies_actie_schema(hand)` en laat hem `"raise"`, `"call"` of
`"fold"` teruggeven."""

SCHEMA_CODE = "\n".join([
    "def kies_actie_schema(hand):",
    "    # TODO: schrijf het schema hierboven om naar if/elif/else.",
    "    #   Let op de volgorde: een paar azen is én een paar én een hand met",
    "    #   een A erin. Welke tak hoort dan te winnen?",
    "    ___",
    "",
    "",
    "for hand in [[\"A\", \"A\"], [\"A\", \"7\"], [\"8\", \"3\"], [\"K\", \"K\"]]:",
    "    print(hand, \"->\", kies_actie_schema(hand))",
])

SCHEMA_NA = """Verwachte uitvoer: `raise`, `call`, `fold`, `raise`.

**En nu andersom.** Hieronder staat code zonder schema. Teken het schema erbij —
op papier is prima — en kijk daarna of je het eens bent met de volgorde.

```python
def kies_actie_anders(hand):
    if "A" in hand:
        return "raise"
    elif hand[0] == hand[1]:
        return "call"
    else:
        return "fold"
```

🤔 Wat doet deze functie met `["K", "K"]`? En met `["A", "A"]`? Vergelijk met het
schema hierboven: dezelfde drie uitkomsten, een andere volgorde — en dus een ander
antwoord op twee van de vier handen."""

FUNCTIE_KOP = """---

## Deel 1d — `return` of `print`? (8 min)

Dit is de fout die in week 3 de meeste tijd kost, dus we halen hem nu naar voren.

```python
def dubbel_print(getal):
    print(getal * 2)

def dubbel_return(getal):
    return getal * 2
```

Allebei lijken ze te werken: je draait ze en je ziet een getal. Maar probeer
hieronder wat er gebeurt als je ze **gebruikt** in plaats van bekijkt."""

FUNCTIE_CODE = "\n".join([
    "def dubbel_print(getal):",
    "    print(getal * 2)",
    "",
    "def dubbel_return(getal):",
    "    return getal * 2",
    "",
    "# allebei aanroepen: ze zien er hetzelfde uit",
    "dubbel_print(5)",
    "dubbel_return(5)",
    "",
    "# maar nu ermee doorrekenen:",
    "a = dubbel_print(5)",
    "b = dubbel_return(5)",
    "",
    "print(\"a is\", a)",
    "print(\"b is\", b)",
])

FUNCTIE_NA = """🤔 `a` is `None`. Waarom?

`print` laat iets zíén; `return` geeft iets térug. Een functie zonder `return`
geeft `None` terug — en met `None` kun je niet verder rekenen.

**Waarom dit er nu toe doet:** je bot heet `kies_actie(hand)` en moet een actie
*teruggeven*, want de server roept hem aan en doet er iets mee. Print je in plaats
van returnt, dan zie je in je notebook keurig `"raise"` staan en krijgt de server
`None` — en dan wordt je bot afgekeurd met een foutmelding die hier niets over zegt.

💡 Vuistregel: `print` is voor jou, `return` is voor de code die jouw functie
aanroept."""

EENREGEL_KOP = """---

## Deel 2b — Drie bots van één regel (15 min)

Voordat je je eigen bot gaat verbeteren: waar meet je hem tegen af?

Schrijf drie bots die elk precies één ding doen. Ze zijn er niet om te winnen,
maar om een ondergrens te hebben. Wat jouw bot daarboven uitkomt, is wat je idee
waard is.

1. `altijd_callen(hand)` — geeft altijd `"call"` terug
2. `altijd_verhogen(hand)` — geeft altijd `"raise"` terug
3. `het_muntje(hand)` — kiest willekeurig uit de drie acties

Tel daarna van alle drie, plus van je eigen `kies_actie`, wat ze doen over
`alle_handen`."""

EENREGEL_CODE = "\n".join([
    "# TODO: schrijf de drie bots. Elk is één of twee regels.",
    "",
    "",
    "def tel_acties(bot, handen):",
    "    \"\"\"Hoe vaak kiest deze bot elke actie? Geeft percentages terug.\"\"\"",
    "    aantallen = {\"raise\": 0, \"call\": 0, \"fold\": 0}",
    "    for hand in handen:",
    "        aantallen[bot(hand)] += 1",
    "    return {a: n / len(handen) * 100 for a, n in aantallen.items()}",
    "",
    "",
    "# TODO: zet de vier bots in deze dict en draai de vergelijking",
    "bots = {",
    "    \"jouw bot\": kies_actie,",
    "    # ...",
    "}",
    "",
    "for naam, bot in bots.items():",
    "    verdeling = tel_acties(bot, alle_handen)",
    "    print(f\"{naam:<16s}\", \"  \".join(f\"{a} {p:.0f}%\" for a, p in verdeling.items()))",
])

EENREGEL_NA = """🤔 Het muntje kiest alle drie de acties even vaak. Is dat beter of slechter dan
jouw bot? Je kunt die vraag nu nog niet beantwoorden — daar heb je een toernooi
voor nodig, en dat komt in week 3.

💡 Wel alvast dit: in het echte toernooi van een eerdere lichting werd een bot die
**altijd callde eerste van de 27**, tien chips voor nummer twee. Niet omdat callen
slim is, maar omdat de rest zo voorzichtig speelde dat er niemand overbleef om de
pot van af te pakken. Twee weken later, toen iedereen echt speelde, werd diezelfde
bot laatste met nul chips.

Dezelfde ene regel. Dat is waarom je een ondergrens nodig hebt om iets over je
eigen bot te kunnen zeggen."""

PARSONS_KOP = """---

## Deel 4b — Zet de regels op volgorde (10 min)

Hieronder staan de regels van een werkende bot, maar door elkaar. Zet ze in de
juiste volgorde.

Dat klinkt makkelijker dan het is: bij `if/elif/else` wint de eerste tak die past,
dus de volgorde ís de strategie. Zet je de ruimste regel bovenaan, dan komen de
scherpere er nooit aan te pas.

```
    return "fold"
    if hand[0] == hand[1]:
def kies_actie_puzzel(hand):
        return "raise"
    if "A" in hand or "K" in hand:
        return "call"
```

Deze bot hoort te doen: een paar is altijd een `raise`, een hoge kaart zonder paar
een `call`, en de rest `fold`."""

PARSONS_CODE = "\n".join([
    "# TODO: zet de zes regels hierboven in de juiste volgorde.",
    "",
    "",
    "for hand in [[\"8\", \"8\"], [\"A\", \"7\"], [\"9\", \"4\"], [\"A\", \"A\"]]:",
    "    print(hand, \"->\", kies_actie_puzzel(hand))",
])

PARSONS_NA = """Verwachte uitvoer: `raise`, `call`, `fold`, `raise`.

🤔 Zet de `"A" in hand`-regel nu eens bovenaan, vóór de paar-regel. Welke van de
vier handen verandert van antwoord? En welke van de twee volgordes vind je beter —
en waarom?

💡 Dit is dezelfde bug als in Deel 0C, maar nu van de andere kant: daar zocht je
hem, hier bouw je hem per ongeluk zelf als je niet oplet."""


def oefening_wc1(nb):
    """Tracing, een flowchart, return-vs-print en de drie bots van één regel."""
    i = zoek_cel(nb, "## Deel 2 — Pokerbot Upgrade Week 1", "markdown")
    nb["cells"][i:i] = [
        nbformat.v4.new_markdown_cell(TRACE_KOP),
        nbformat.v4.new_code_cell(TRACE_CODE),
        nbformat.v4.new_markdown_cell(TRACE_NA),
        nbformat.v4.new_markdown_cell(SCHEMA_KOP),
        nbformat.v4.new_code_cell(SCHEMA_CODE),
        nbformat.v4.new_markdown_cell(SCHEMA_NA),
        nbformat.v4.new_markdown_cell(FUNCTIE_KOP),
        nbformat.v4.new_code_cell(FUNCTIE_CODE),
        nbformat.v4.new_markdown_cell(FUNCTIE_NA),
    ]
    j = zoek_cel(nb, "## Deel 3 — Je eerste visualisatie", "markdown")
    nb["cells"][j:j] = [
        nbformat.v4.new_markdown_cell(EENREGEL_KOP),
        nbformat.v4.new_code_cell(EENREGEL_CODE),
        nbformat.v4.new_markdown_cell(EENREGEL_NA),
    ]
    return 0, 12


def oefening_wc2(nb):
    """Een Parsons-opdracht op de botregels."""
    i = zoek_cel(nb, "## Reflectievragen", "markdown")
    nb["cells"][i:i] = [
        nbformat.v4.new_markdown_cell(PARSONS_KOP),
        nbformat.v4.new_code_cell(PARSONS_CODE),
        nbformat.v4.new_markdown_cell(PARSONS_NA),
    ]
    return 0, 3


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
