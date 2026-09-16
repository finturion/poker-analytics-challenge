"""
Genereert de Brightspace-pagina's voor de Pokerbot Analytics Challenge in het
HvA-format (Bootstrap 3 + main.min.css uit de HTML-Template-Library 2019).

WAAROM EEN PAGINA PER WEEK
--------------------------
Brightspace kan een *topic* verbergen of op een datum vrijgeven -- niet een stuk
binnen een topic. Er is geen manier om in EEN HTML-bestand week 1 te laten zien
en week 5 te verbergen: release conditions en availability dates hangen aan het
onderdeel in Content, niet aan een <div>. Wil je dus per week vrijgeven, dan
moet elke week een eigen topic zijn. Daarom schrijft dit script zeven bestanden:
zes weekpagina's plus een overzicht dat altijd zichtbaar mag blijven.

Verberg je met CSS of JavaScript, dan is dat alleen cosmetisch: de tekst staat
in de paginabron en is met "view source" te lezen. Voor "niet afleiden" is dat
prima, voor iets wat echt niet gelezen mag worden niet.

En let op: het verbergen van een topic haalt de link uit Content weg, maar het
bestand onder /content/enforced/<cursus>/ houdt zijn eigen URL. Wie die URL uit
een eerdere week nog heeft, kan hem mogelijk blijven openen -- test dat met een
studentaccount voordat je erop vertrouwt.

GEBRUIK
-------
    python3 scripts/genereer_brightspace_paginas.py

Schrijft naar brightspace/. Daarna elk bestand als los HTML-topic in Content
zetten en de availability date op de maandag van die week.
"""

import html
import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, "api")
import datacamp_rooster

CURSUS = "764257-FT-6100DASC23-T--ALG-2627"
BASISPAD = f"/content/enforced/{CURSUS}"
# Inleveren gebeurt in het notebook met lever_in(); er is geen aparte
# inleverpagina. Deze URL is dezelfde die de notebooks als API_URL gebruiken.
API = "https://poker-analytics-api.onrender.com"
UITVOER = "brightspace"

# Maandag van week 1. De DataCamp-deadlines in api/datacamp_rooster.py hangen
# hieraan vast (week 1 heeft rooster_deadline 2026-09-04, de vrijdag), dus als
# deze datum verschuift, klopt daar iets niet meer.
WEEK1_MAANDAG = date(2026, 8, 31)

DAGEN = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag"]
MAANDEN = ["", "januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]


def datum_nl(d: date) -> str:
    return f"{d.day} {MAANDEN[d.month]}"


def weekdatums(week: int) -> tuple[date, date]:
    ma = WEEK1_MAANDAG + timedelta(weeks=week - 1)
    return ma, ma + timedelta(days=4)


# ---------------------------------------------------------------------------
# De inhoud. Eén dict per week; alles wat op de pagina komt staat hier.
# ---------------------------------------------------------------------------

WEKEN = [
    {
        "week": 1,
        "titel": "De eerste deal",
        "lead": "Je bouwt je eerste pokerbot, kijkt hoe hij het tegen de klas doet, "
                "en levert donderdag een verbeterde versie in.",
        "werkcolleges": [
            ("Week1_Werkcollege1.ipynb", "Werkcollege 1 — De eerste deal",
             "Begin hier. Zet dit notebook in een lege map."),
            ("Week1_Werkcollege2.ipynb", "Werkcollege 2 — Testen, toernooi-overzicht en peer review",
             "Zet dit bestand in dezelfde map als Werkcollege 1."),
        ],
        "hulpbestanden": [
            ("_hulpfuncties.py", "Hulpfuncties week 1",
             "Downloaden en in dezelfde map als je notebook zetten, anders werkt de eerste cel niet."),
        ],
        "powerpoints": [
            # De naam op Brightspace, niet de bestandsnaam in de repo -- zie
            # ANDERE_NAAM_OP_BRIGHTSPACE.
            ("Uitleg%20Powerpoint%20Week%201%20-%20Werkcollege%201.pptx",
             "Powerpoint bij Werkcollege 1"),
        ],
        "deadlines": [
            ("woensdag 09:00", "Bot v1 ingeleverd — anders speel je niet mee in het toernooi van woensdag"),
            ("donderdag 18:00", "verbeterde Bot v1, op basis van wat je in het toernooi zag"),
        ],
        "let_op": "De bonuspunten worden in week 5 verdiend, niet nu. Week 1 en 3 zijn "
                  "de weken waarin je leert hoe je een bot bouwt en verbetert.",
    },
    {
        "week": 2,
        "titel": "Visual Maandag: ruis, focal points en ordening",
        "lead": "Deze week geen nieuwe botversie. Je leert grafieken lezen en maken met "
                "de data die je bot heeft opgeleverd.",
        "werkcolleges": [
            ("Week2_Werkcollege3.ipynb", "Werkcollege 3 — Visual Maandag",
             None),
        ],
        "hulpbestanden": [
            ("pokerdata_voorbeeld.csv", "Voorbeelddata bij Werkcollege 3",
             "In dezelfde map als het notebook."),
        ],
        "powerpoints": [],
        "deadlines": [],
        "let_op": None,
    },
    {
        "week": 3,
        "titel": "Bot v2: functies, dictionaries, pandas en Plotly",
        "lead": "Je bot krijgt er informatie bij: zijn stack, de ronde en de echte "
                "spelregels. Twee deadlines deze week.",
        "werkcolleges": [
            ("Week3_Werkcollege4.ipynb", "Werkcollege 4 — Functies, dictionaries, pandas en Plotly",
             "Het hoofdwerk van deze week zit in het huiswerk: reken op 4 tot 8 uur."),
            ("Week3_Werkcollege5.ipynb", "Werkcollege 5 — Resultaten, de spelregels in je eigen data, Case 2 en Streamlit",
             None),
        ],
        "hulpbestanden": [
            ("_hulpfuncties_week3.py", "Hulpfuncties week 3",
             "Hier zit schat_winkans() in. Let op de parameter tegenstanders: standaard 1, "
             "maar aan een tafel van zes moet je 5 meegeven."),
        ],
        "powerpoints": [],
        "deadlines": [
            ("woensdag 09:00", "een werkende Bot v2"),
            ("donderdag 18:00", "verbeterde Bot v2, plus: je groep heeft het onderwerp van Case 2 vastgelegd"),
        ],
        "let_op": "In het toernooi speelt <code>Testbot_CalltAlles</code> mee: een bot die "
                  "altijd callt, nooit naar zijn kaarten kijkt en geen bonuspunten kan pakken. "
                  "Hij staat er als ondergrens. Verlies je van hem, dan ligt dat niet aan de "
                  "kaarten maar aan je drempels.",
    },
    {
        "week": 4,
        "titel": "Visual Maandag: spaghetti-grafieken, kleurcontrast en storytelling",
        "lead": "Toetsweek en de afronding van Case 2. Geen nieuwe botversie.",
        "werkcolleges": [
            ("Week4_Werkcollege6.ipynb", "Werkcollege 6 — Visual Maandag", None),
        ],
        "hulpbestanden": [],
        "powerpoints": [],
        "deadlines": [],
        "let_op": None,
    },
    {
        "week": 5,
        "titel": "Bot v3, en de week waarin de bonuspunten vallen",
        "lead": "Drie dagen, twee toernooien die meetellen en een oefenronde ertussen. "
                "Hier is de volle 1,0 bonuspunt te verdienen.",
        "werkcolleges": [
            ("Week5_Werkcollege7.ipynb", "Werkcollege 7 — Bot v3: strategie, bluffen en tegenstanders",
             "Kort werkcollege, veel eigen werk: reken op 4 tot 8 uur."),
            ("Week5_Werkcollege8.ipynb", "Werkcollege 8 — Resultaten, verfijnen en de aftrap van de laatste case",
             None),
        ],
        "hulpbestanden": [
            ("_hulpfuncties.py", "Hulpfuncties",
             "Hetzelfde bestand als in week 1. Werkcollege 7 importeert het, dus zet je "
             "notebook in dezelfde map als je werk van week 1 en 3, of kopieer dit bestand "
             "erheen. Je eigen <code>mijn_bot_week3.py</code> heb je er ook bij nodig: "
             "daar begin je Bot v3 mee."),
        ],
        "powerpoints": [],
        "deadlines": [
            ("woensdag 09:00", "Bot v3 — <strong>dit toernooi telt mee</strong>: 1e 0,5 · 2e 0,4 · 3e 0,3 · 4e 0,2 · 5e 0,1"),
            ("donderdag 09:00", "oefenronde. Telt niet mee, maar laat zien wat je aanpassing doet"),
            ("vrijdag 18:00", "definitieve bot — <strong>het tweede toernooi dat meetelt</strong>, "
                              "dezelfde punten. Twee keer 0,5 is samen het maximum van 1,0"),
        ],
        "let_op": "De deadline handhaaft zichzelf: een toernooi speelt met de bots die er op dat "
                  "moment zijn. Lever je je woensdagbot woensdagmiddag in, dan doe je niet mee aan "
                  "het woensdagtoernooi en haal je daar dus geen punten.",
    },
    {
        "week": 6,
        "titel": "Visual Maandag: Information Architecture & Progressive Disclosure",
        "lead": "De afsluiting van de pokerlijn: de eindstand op de kaart van Nederland, "
                "en hoe je een dashboard opbouwt dat iemand anders kan lezen.",
        "werkcolleges": [
            ("Week6_Werkcollege9.ipynb", "Werkcollege 9 — Information Architecture & Progressive Disclosure",
             None),
        ],
        "hulpbestanden": [
            ("oefenbots.csv", "Oefenbots met gemeente",
             "In de map data/ naast je notebook."),
            ("gemeenten_nl_fallback.geojson", "Gemeentegrenzen (reservebestand)",
             "Ook in de map <code>data/</code>. Alleen nodig als de PDOK-API niet reageert; "
             "het notebook haalt de grenzen normaal zelf via de API op, en dat ophalen is "
             "onderdeel van de opdracht."),
        ],
        "powerpoints": [],
        "deadlines": [],
        "let_op": "Dit notebook heeft <code>geopandas</code> nodig, en dat is de enige "
                  "package van het hele blok die soms niet in één keer installeert. Doe dat "
                  "vóór het werkcollege: <code>pip install geopandas folium</code>. Lukt het "
                  "niet, meld het dan vooraf — tijdens het werkcollege een installatie "
                  "uitzoeken kost je de hele les. De kaart gebruikt de uitslag van het "
                  "toernooi van vrijdag in week 5, dus de eindstand van de hele reeks.",
    },
]

# ---------------------------------------------------------------------------
# HTML-bouwstenen. Bootstrap 3-klassen die het HvA-template ondersteunt.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# HTML. Bewust kaal: koppen, alinea's, links en lijsten -- dezelfde vorm als de
# bestaande Brightspace-pagina, met de HvA-shell eromheen. Geen panels,
# jumbotrons, tabellen of glyphicons: die maken de pagina drukker zonder dat de
# student er iets aan heeft, en ze zijn met de hand niet te onderhouden.
# ---------------------------------------------------------------------------

KOP = """<!DOCTYPE html>
<html lang="nl"><head>
\t<meta charset="utf-8">
\t<meta http-equiv="x-ua-compatible" content="ie=edge">
\t<title>{titel}</title>
\t<meta name="description" content="{omschrijving}">
\t<meta name="viewport" content="width=device-width, initial-scale=1.0">
\t<!-- Bootstrap CDN CSS -->
\t<link rel="stylesheet" href="/shared/HTML-Template-Library/HTML-Template-HvA-2019/HvA_Template/hva_templates_2019/../assets/thirdpartylib/bootstrap-3.3.6/css/bootstrap.min.css">
\t<!-- Course Styles -->
\t<link rel="stylesheet" href="/shared/HTML-Template-Library/HTML-Template-HvA-2019/HvA_Template/hva_templates_2019/../assets/css/main.min.css">
</head><body class="content layout-2" role="document"><div class="container-fluid"><main>
<div class="row">
<div class="col-sm-12">
<div class="decoration"></div>
</div>
<div class="col-xs-12 col-sm-offset-1 col-sm-10">
"""

VOET = """</div>
</div>
</main></div></body></html>
"""


# Bestanden die op Brightspace anders heten dan in deze repo. De controle
# onderaan kijkt of het bronbestand bestaat; zonder deze tabel zou hij op zo'n
# bestand vals alarm slaan. Verandert de naam op Brightspace, dan hier ook.
ANDERE_NAAM_OP_BRIGHTSPACE = {
    "Uitleg Powerpoint Week 1 - Werkcollege 1.pptx": "powerpoints/Pokerbot_Upgrade_Week1.pptx",
}


def bestandslink(pad: str, label: str) -> str:
    return (f'<p><a rel="noopener" href="{BASISPAD}/{pad}" target="_blank">'
            f'{html.escape(label)}</a></p>')


def bestandenblok(items) -> str:
    """Link, en daaronder als losse alinea waar het bestand moet staan."""
    regels = []
    for pad, label, toelichting in items:
        regels.append(bestandslink(pad, label))
        if toelichting:
            regels.append(f"<p>{toelichting}</p>")
    return "\n".join(regels)


def weekpagina(w: dict) -> str:
    ma, vr = weekdatums(w["week"])
    titel = f'Week {w["week"]} — {w["titel"]}'
    delen = [KOP.format(
        titel=html.escape(f'{titel} | Pokerbot Analytics Challenge'),
        omschrijving=html.escape(w["lead"]),
    )]

    delen.append(f'<h1>{html.escape(titel)}</h1>')
    delen.append(f'<p>{html.escape(w["lead"])}</p>')
    delen.append(f'<p>Pokerbot Analytics Challenge · {datum_nl(ma)} t/m {datum_nl(vr)} 2026</p>')

    if w["deadlines"]:
        regels = "\n".join(f'<li><strong>{wanneer}</strong> — {wat}</li>'
                           for wanneer, wat in w["deadlines"])
        delen.append(f'<h2>Deadlines</h2>\n<ul>\n{regels}\n</ul>')
    else:
        delen.append('<h2>Deadlines</h2>\n'
                     '<p>Deze week lever je geen nieuwe botversie in.</p>')

    delen.append('<h2>Notebooks</h2>\n' + bestandenblok(w["werkcolleges"]))

    if w["hulpbestanden"]:
        delen.append('<h2>Hulpbestanden</h2>\n' + bestandenblok(w["hulpbestanden"]))

    if w["powerpoints"]:
        delen.append('<h2>Slides</h2>\n'
                     + bestandenblok([(p, l, None) for p, l in w["powerpoints"]]))

    dc = datacamp_van_week(w["week"])
    if dc:
        regels = "\n".join(
            f'<li>{c["code"]} — {html.escape(c["titel"])}, '
            f'vóór {datum_nl(date.fromisoformat(c["deadline"]))}</li>'
            for c in dc
        )
        delen.append(f'<h2>DataCamp deze week</h2>\n<ul>\n{regels}\n</ul>')

    if w["let_op"]:
        delen.append(f'<h2>Let op</h2>\n<p>{w["let_op"]}</p>')

    # Alleen in een week waarin er iets in te leveren valt. In week 2, 4 en 6
    # staat er geen botdeadline, en dan is een uitleg over lever_in() een
    # instructie voor iets wat deze week niet gebeurt.
    if w["deadlines"]:
        delen.append(
            '<h2>Inleveren</h2>\n'
            '<p>Inleveren doe je in het notebook zelf, met <code>lever_in()</code>. Je mag zo '
            'vaak opnieuw inleveren als je wilt; het systeem gebruikt altijd je laatste '
            'inzending. Je studentnummer en token staan bovenaan je notebook.</p>'
        )

    delen.append(
        f'<p><a rel="noopener" href="{API}/docs" target="_blank">API-documentatie</a> — '
        'voor wie de resultaten zelf uit de API wil ophalen.</p>'
    )

    delen.append(VOET)
    return "\n".join(delen)


def datacamp_van_week(week: int) -> list[dict]:
    return [c for c in datacamp_rooster.ROOSTER if c["week"] == week]


def overzichtspagina() -> str:
    delen = [KOP.format(
        titel="Pokerbot Analytics Challenge | Introduction to Data Science",
        omschrijving="Weekoverzicht van de Pokerbot Analytics Challenge: "
                     "wat je per week bouwt, inlevert en wanneer.",
    )]

    delen.append('<h1>Pokerbot Analytics Challenge</h1>')
    delen.append('<p>Zes weken, drie botversies, maximaal 1,0 bonuspunt.</p>')

    delen.append(
        '<h2>Hoe je het bonuspunt verdient</h2>\n'
        '<p>Alleen in <strong>week 5</strong>. Daar draaien twee toernooien die meetellen: '
        'woensdagochtend met je woensdagbot en na de slotdeadline van vrijdag met je '
        'definitieve bot. In elk toernooi levert je plek punten op — eerste 0,5, tweede 0,4, '
        'derde 0,3, vierde 0,2, vijfde 0,1, daarna niets. Twee keer 0,5 is samen het '
        'maximum van 1,0.</p>\n'
        '<p>Week 1 en 3 leveren geen punten op. Dat zijn de weken waarin je leert hoe je een '
        'bot bouwt en verbetert — met echte toernooien en echte uitslagen, maar zonder '
        'punten.</p>'
    )

    regels = []
    for w in WEKEN:
        ma, vr = weekdatums(w["week"])
        wat = "nieuwe botversie" if w["deadlines"] else "geen botdeadline"
        if w["week"] == 5:
            wat = "nieuwe botversie, en hier vallen de bonuspunten"
        regels.append(
            f'<li><strong>Week {w["week"]}</strong> ({datum_nl(ma)}–{datum_nl(vr)}) — '
            f'{html.escape(w["titel"])}. {wat.capitalize()}.</li>'
        )
    delen.append('<h2>De zes weken</h2>\n<ul>\n' + "\n".join(regels) + '\n</ul>')

    delen.append(
        '<h2>Elke week hetzelfde ritme</h2>\n<ul>\n'
        '<li><strong>woensdag 09:00</strong> — je bot moet binnen zijn, want het toernooi '
        'speelt met de bots die er op dat moment zijn.</li>\n'
        '<li><strong>woensdag in het werkcollege</strong> — je ziet de uitslag en analyseert '
        'hoe je bot speelde.</li>\n'
        '<li><strong>donderdag 18:00</strong> — een verbeterde versie inleveren. In week 5 is '
        'dat vrijdag 18:00, want dat is de slotdeadline van de hele challenge.</li>\n'
        '</ul>'
    )

    delen.append(
        '<h2>Inleveren</h2>\n'
        '<p>Alles gaat via het notebook van die week: <code>lever_in()</code> stuurt je bot in, '
        'en de cellen eronder halen de uitslag op. Zo vaak opnieuw inleveren als je wilt — het '
        'systeem gebruikt altijd je laatste inzending. Je studentnummer en token krijg je in '
        'week 1 en die blijven het hele blok geldig.</p>\n'
        f'<p><a rel="noopener" href="{API}/docs" target="_blank">API-documentatie</a> — '
        'voor wie de resultaten zelf uit de API wil ophalen.</p>'
    )

    delen.append(VOET)
    return "\n".join(delen)


def controleer(paden: list[str]) -> None:
    """Wat er misgaat als je met de hand in deze HTML knipt."""
    fouten = []
    for pad in paden:
        with open(pad, encoding="utf-8") as f:
            s = f.read()
        naam = os.path.basename(pad)
        for tag in ("div", "main", "ul", "table", "tbody", "li", "tr", "td", "p"):
            open_n = len(re.findall(rf"<{tag}[\s>]", s))
            dicht_n = s.count(f"</{tag}>")
            if open_n != dicht_n:
                fouten.append(f"{naam}: <{tag}> {open_n}x open, {dicht_n}x dicht")
        if s.count("<body") != 1 or s.count("</body>") != 1:
            fouten.append(f"{naam}: body niet precies 1x")
        # Elke link naar een cursusbestand moet naar een bestand wijzen dat bestaat.
        for pad_in_link in re.findall(rf'{re.escape(BASISPAD)}/([^"]+)', s):
            bestand = pad_in_link.replace("%20", " ")
            kandidaten = [f"notebooks/{bestand}", f"notebooks/data/{bestand}",
                          f"powerpoints/{bestand}"]
            if bestand in ANDERE_NAAM_OP_BRIGHTSPACE:
                kandidaten.append(ANDERE_NAAM_OP_BRIGHTSPACE[bestand])
            if not any(os.path.exists(k) for k in kandidaten):
                fouten.append(f"{naam}: link naar {bestand}, maar dat bestand bestaat hier niet")
    if fouten:
        print("\nCONTROLE MISLUKT:")
        for f in fouten:
            print("  -", f)
        sys.exit(1)
    print(f"\nControle OK ({len(paden)} bestanden): tags in balans, alle links bestaan.")


def main() -> None:
    os.makedirs(UITVOER, exist_ok=True)
    geschreven = []

    pad = os.path.join(UITVOER, "00_overzicht.html")
    with open(pad, "w", encoding="utf-8") as f:
        f.write(overzichtspagina())
    geschreven.append(pad)
    print(f"{pad}")

    for w in WEKEN:
        pad = os.path.join(UITVOER, f'week{w["week"]}.html')
        with open(pad, "w", encoding="utf-8") as f:
            f.write(weekpagina(w))
        geschreven.append(pad)
        ma, _ = weekdatums(w["week"])
        print(f'{pad}  ->  availability date: maandag {datum_nl(ma)} 2026')

    controleer(geschreven)


if __name__ == "__main__":
    main()
