"""
Het deck bij Werkcollege 6 (Week 4): Visual Maandag.

    python3 powerpoints/wc6plaatjes.py [uitslag.json]   # eerst de platen
    python3 powerpoints/maak_presentatie_week6.py       # dan het deck

Schrijft powerpoints/Visual_Maandag_Werkcollege6.pptx.

Dit werkcollege gaat over kijken, dus dit deck laat zien in plaats van te
vertellen. Zeven van de vijftien dia's zijn een plaat met één regel eronder; de
platen komen uit wc6plaatjes.py en staan in dezelfde volgorde als het notebook.
Draai dat script opnieuw met de echte uitslag erbij en het deck klopt weer.

DE INHOUD KOMT UIT HET NOTEBOOK
-------------------------------
Titels en minuten zijn overgenomen uit notebooks/Week4_Werkcollege6.ipynb. Er is
niets dat die twee synchroon houdt, dus de controle onderaan vergelijkt ze en
klaagt als er iets is verschoven.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dekstijl import (ACCENT, BG, GEDEMPT, KAART, LIJN, MONO, PRIMAIR,
                      WAARSCHUWING, kaart, kop, nieuwe_dia, tekstblok)
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
NOTEBOOK = os.path.join(WORTEL, "notebooks", "Week4_Werkcollege6.ipynb")
PLOTMAP = os.path.join(HIER, "plots_week4")
# Werkcollege 6 valt in WEEK 4. Het bestand heette eerst Visual_Maandag_Week6,
# en dat leest als "week 6" -- op Brightspace ziet een student alleen de
# bestandsnaam, en die stond dan in de verkeerde week te suggereren.
UITVOER = os.path.join(HIER, "Visual_Maandag_Werkcollege6.pptx")

# (categorie, titel, plaatnaam of None, [regels], onderschrift)
# Een regel is (tekst, grootte, vet, kleur, ruimte_ervoor).
def r(tekst, grootte=13, vet=False, kleur=PRIMAIR, ruimte=6, lettertype=None):
    return (tekst, grootte, vet, kleur, ruimte, lettertype)


DIAS = [
    ("VANDAAG", "Twee dingen die Werkcollege 3 nog niet deed", None, [
        r("1 · Pre-attentieve attributen", 16, True, ACCENT, 0),
        r("Verschillen die je brein ziet vóórdat je bewust kijkt — binnen 200 milliseconden,", 13),
        r("zonder te zoeken. Kleur is er één van, maar niet de enige.", 13, False, PRIMAIR, 2),
        r("2 · Kleurcontrast en toegankelijkheid", 16, True, ACCENT, 16),
        r("Ongeveer 1 op de 12 mannen heeft een vorm van kleurenblindheid, meestal rood-groen.", 13),
        r("Een grafiek die alléén op kleur leunt, valt voor die lezer uit elkaar.", 13, False, PRIMAIR, 2),
        r("Geen nieuwe inleveropdracht vandaag. Je herontwerpt de data die je al hebt.",
          13, True, GEDEMPT, 18),
    ], None),

    ("HET GEREEDSCHAP", "Vier kanalen, en kleur is er maar één van", "0_kanalen", [], 
     "Dezelfde acht lijnen, vier keer. Hoe verder naar rechts, hoe minder moeite het kost "
     "om de lijn te vinden die ertoe doet — zonder dat er één kleur bij komt."),

    ("HET GEREEDSCHAP", "Wat elk kanaal doet", None, [
        r("Kleur", 14, True, ACCENT, 0),
        r("trekt het sterkst, maar werkt maar voor een handjevol categorieën · 1 tot 4 dingen uitlichten", 12),
        r("Lijndikte", 14, True, ACCENT, 12),
        r("duwt iets naar voren zonder een kleur op te maken · één lijn belangrijker maken", 12),
        r("Opacity", 14, True, ACCENT, 12),
        r("duwt de rest naar áchteren in plaats van iets naar voren · veel achtergrondlijnen dempen", 12),
        r("Positie", 14, True, ACCENT, 12),
        r("het sterkste kanaal van allemaal, maar bepaald door je data · sorteren (Werkcollege 3)", 12),
        r("Heb je 8 lijnen en moet er één opvallen, dan is \"8 kleuren\" het verkeerde antwoord.",
          14, True, WAARSCHUWING, 18),
    ], None),

    ("DEEL 1 · 10 MIN", "Spaghetti identificeren", "1_spaghetti", [],
     "Alle bots, alle zittingen, ongefilterd. Technisch klopt deze grafiek. "
     "Vraag aan de zaal: wie wint? En hoelang deed je erover?"),

    ("DEEL 2 · 12 MIN", "Eerste reductie is geen design maar filteren", "2_gefilterd", [],
     "Eén tafel, één zitting. Van 120 lijnen naar 6. Leesbaar — en nog steeds "
     "geen verhaal: elke lijn schreeuwt even hard."),

    ("DEEL 3 · 22 MIN", "Eén bot naar voren, de rest naar achteren", "3_uitgelicht", [],
     "Kleur + dikte + volle dekking voor je eigen bot. Grijs + dun + halftransparant "
     "voor de rest. De tegenstanders zijn niet onbelangrijk, ze zijn context."),

    ("DEEL 3 · DE CODE", "Drie kanalen, drie argumenten", None, [
        r("# de context", 13, True, GEDEMPT, 0),
        r("ax.plot(x, y, color=\"#9AA3AA\", linewidth=1.0, alpha=0.45, zorder=1)", 13, False, PRIMAIR, 2, lettertype=MONO),
        r("# de hoofdrol", 13, True, ACCENT, 16),
        r("ax.plot(x, y, color=ACCENT,     linewidth=3.0, alpha=1.0,  zorder=3)", 13, False, PRIMAIR, 2, lettertype=MONO),
        r("zorder bepaalt wat er bovenop ligt. Zonder dat verdwijnt je hoofdlijn "
          "onder de grijze massa zodra ze elkaar kruisen.", 13, False, GEDEMPT, 18),
    ], None),

    ("DEEL 4 · 12 MIN", "Meer dan één lijn uitlichten", None, [
        r("Kleur werkt tot ongeveer vier categorieën. Daarna ben je aan het zoeken "
          "in plaats van aan het zien.", 14, False, PRIMAIR, 0),
        r("Kies twee of drie tegenstanders die iets anders doen dan jij — niet de "
          "willekeurige eersten in de lijst.", 13, False, PRIMAIR, 12),
        r("De vraag die je met de grafiek beantwoordt, bepaalt wie er kleur krijgt.",
          14, True, ACCENT, 16),
    ], None),

    ("DEEL 5 · 18 MIN", "Een titel is een bewering, geen label", "4_kantelpunt", [],
     "\"Chipverloop tafel 0\" zegt niets. Schrijf op wát er gebeurde, en zet de "
     "annotatie op het moment waarop het gebeurde."),

    ("DEEL 5 · DE VALKUIL", "Twee Series aftrekken gaat stil mis", None, [
        r("verschil = mijn_stack - zijn_stack", 14, False, PRIMAIR, 0, lettertype=MONO),
        r("Pandas lijnt die twee uit op hun index — hand_nummer. Bust de een eerder "
          "dan de ander, dan krijg je NaN voor elke hand die maar bij één van de twee "
          "voorkomt. Zonder foutmelding.", 13, False, PRIMAIR, 14),
        r("idxmax() slaat die NaN's stilletjes over. Je zoekt je kantelpunt dan alleen "
          "in de overlap, en dat is precies het stuk waar niets bijzonders gebeurde.",
          13, False, PRIMAIR, 10),
        r("Tel ze eerst:  verschil.isna().sum()", 14, True, WAARSCHUWING, 16, lettertype=MONO),
    ], None),

    ("DEEL 6 · 12 MIN", "De eerlijkste kleurtest: haal de kleur weg", "6_kleurloos", [],
     "Blijft je bot herkenbaar? Dan deed je het werk met dikte en opacity. "
     "Valt de grafiek uit elkaar, dan leunde alles op kleur — en dat is wat "
     "1 op de 12 lezers ziet."),

    ("DEEL 7 · 18 MIN", "De stand of wat er gebeurde", "5_niveau_vs_verloop", [],
     "Links de stack: waar sta je. Rechts diff(): wat leverde deze hand op. "
     "Dezelfde bot, dezelfde handen — en pas rechts zie je wannéér het misging."),

    ("DEEL 7 · WAAROM DIT", "diff, cumsum en shift staan in de rubric", None, [
        r("df.groupby(\"bot_naam\")[\"stack\"].diff()", 13, False, PRIMAIR, 0, lettertype=MONO),
        r("het verschil met de hand ervoor — groepeer, anders trek je de eerste hand "
          "van de ene bot af van de laatste van de andere", 12, False, GEDEMPT, 2),
        r("df[\"winst\"].cumsum()", 13, False, PRIMAIR, 12, lettertype=MONO),
        r("het opgetelde verloop: hoeveel heb je tot hier verdiend", 12, False, GEDEMPT, 2),
        r("df[\"stack\"].shift(1)", 13, False, PRIMAIR, 12, lettertype=MONO),
        r("de waarde van de hand ervoor, naast die van nu", 12, False, GEDEMPT, 2),
        r("Case 2, criterium Vergelijken en annoteren, vraagt letterlijk om deze drie.",
          14, True, ACCENT, 18),
    ], None),

    ("DEEL 8 TOT 10 · 40 MIN", "Je eigen vooruitgang, de ranglijst, en een tweede paar ogen", None, [
        r("Deel 8 · Multi-week (15 min)", 14, True, ACCENT, 0),
        r("v1 naast v3 in één grafiek. Dit is de grafiek waarmee je laat zien dat je iets hebt geleerd.", 12),
        r("Deel 9 · De winkans-ranglijst (15 min)", 14, True, ACCENT, 12),
        r("De equity-tabel uit Werkcollege 5 als beeld. Sorteren is hier het hele ontwerp.", 12),
        r("Deel 10 · Peer-vergelijking (10 min)", 14, True, ACCENT, 12),
        r("Laat je grafiek zien zonder iets te zeggen. Wat leest de ander eruit? "
          "Dat is je echte test, niet je eigen oordeel.", 12),
    ], None),

    ("DEEL 11 · 15 MIN", "Van grafiek naar Streamlit-app", None, [
        r("Je grafiek wordt een pagina met een widget. Dat is het skelet van je Case 2-dashboard.",
          14, False, PRIMAIR, 0),
        r("Eerst je data wegschrijven naar CSV — een script kent je notebook-variabelen niet "
          "en heeft je token niet.", 13, False, PRIMAIR, 14),
        r("Dan st.multiselect erbij, en één regel die meldt hoeveel rijen er geselecteerd zijn. "
          "Daarmee zie je het rerun-model: bij elke klik draait het hele script opnieuw.",
          13, False, PRIMAIR, 10),
        r("Case 2 vraagt een slider, een checkbox én een dropdown. Hier bouw je de eerste.",
          14, True, ACCENT, 16),
    ], None),
]

SLOT = {
    "titel": "Wat je meeneemt",
    "regels": [
        "Filteren is de goedkoopste reductie — doe dat eerst, en pas daarna design.",
        "Eén ding uitlichten doe je met drie kanalen tegelijk, niet met acht kleuren.",
        "Een titel is een bewering. Kun je hem niet opschrijven, dan heb je je verhaal nog niet.",
        "Haal de kleur weg. Werkt je grafiek nog, dan werkt hij voor iedereen.",
        "diff, cumsum en shift staan in de rubric van Case 2 — dit is waar je ze leert.",
    ],
}


def titeldia(prs):
    dia = prs.slides.add_slide(prs.slide_layouts[6])
    vlak = dia.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    vlak.fill.solid()
    vlak.fill.fore_color.rgb = PRIMAIR
    vlak.line.fill.background()
    vlak.shadow.inherit = False

    tekstblok(dia, Inches(1.1), Inches(2.4), Inches(11.0), Inches(3.0), [
        ("WEEK 4 · WERKCOLLEGE 6", 12, True, KAART, 0),
        ("Visual Maandag", 42, True, KAART, 10),
        ("Spaghetti-grafieken, kleurcontrast en storytelling", 20, False, LIJN, 6),
        ("Geen nieuwe bot vandaag. Dezelfde data, een ander verhaal.", 14, False, LIJN, 20),
    ])
    return dia


def beelddia(prs, categorie, titel, plaatnaam, onderschrift):
    dia = nieuwe_dia(prs)
    kop(dia, categorie, titel)
    pad = os.path.join(PLOTMAP, plaatnaam + ".png")
    if os.path.exists(pad):
        # Op hoogte schalen en dan pas centreren: de platen hebben niet allemaal
        # dezelfde verhouding, en op breedte schalen liep de brede plaat over
        # zijn eigen onderschrift heen.
        plaat = dia.shapes.add_picture(pad, 0, Inches(1.72), height=Inches(4.40))
        if plaat.width > Inches(11.6):
            plaat.height = int(plaat.height * Inches(11.6) / plaat.width)
            plaat.width = Inches(11.6)
        plaat.left = int((prs.slide_width - plaat.width) / 2)
    else:
        print(f"Let op: {plaatnaam}.png ontbreekt -- draai eerst wc6plaatjes.py")
    if onderschrift:
        tekstblok(dia, Inches(1.35), Inches(6.35), Inches(10.6), Inches(0.9),
                  [(onderschrift, 12, False, GEDEMPT, 0)])
    return dia


def tekstdia(prs, categorie, titel, regels):
    dia = nieuwe_dia(prs)
    kop(dia, categorie, titel)
    kaart(dia, Inches(0.8), Inches(1.75), Inches(11.7), Inches(4.9))
    tekstblok(dia, Inches(1.25), Inches(2.1), Inches(10.8), Inches(4.2), regels)
    return dia


def slotdia(prs):
    dia = nieuwe_dia(prs)
    kop(dia, "AAN HET EIND VAN VANDAAG", SLOT["titel"])
    boven = 1.85
    for regel in SLOT["regels"]:
        kaart(dia, Inches(0.8), Inches(boven), Inches(11.7), Inches(0.82))
        tekstblok(dia, Inches(1.15), Inches(boven + 0.19), Inches(11.0), Inches(0.5),
                  [(regel, 13, False, PRIMAIR, 0)])
        boven += 0.97
    return dia


def controleer_tegen_notebook():
    """Staan de delen en de minuten nog zoals in het notebook?"""
    with open(NOTEBOOK, encoding="utf-8") as bestand:
        nb = json.load(bestand)
    koppen = {}
    for cel in nb["cells"]:
        if cel["cell_type"] != "markdown":
            continue
        for m in re.finditer(r"^## Deel (\d+) — (.+?) \((\d+) min\)", "".join(cel["source"]), re.M):
            koppen[int(m.group(1))] = int(m.group(3))

    klachten = []
    for categorie, titel, *_ in DIAS:
        m = re.match(r"DEEL (\d+) · (\d+) MIN", categorie)
        if not m:
            continue
        deel, minuten = int(m.group(1)), int(m.group(2))
        if deel not in koppen:
            klachten.append(f"Deel {deel} staat niet meer in het notebook")
        elif koppen[deel] != minuten:
            klachten.append(f"Deel {deel}: dia zegt {minuten} min, notebook zegt {koppen[deel]}")
    if klachten:
        print("Controle tegen het notebook:")
        for klacht in klachten:
            print("  -", klacht)
    else:
        print(f"Controle OK: de minuten op de dia's kloppen met {os.path.basename(NOTEBOOK)}.")
    return not klachten


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    titeldia(prs)
    for categorie, titel, plaat, regels, onderschrift in DIAS:
        if plaat:
            beelddia(prs, categorie, titel, plaat, onderschrift)
        else:
            tekstdia(prs, categorie, titel, regels)
    slotdia(prs)

    controleer_tegen_notebook()
    prs.save(UITVOER)
    print(f"{len(prs.slides._sldIdLst)} dia's -> {UITVOER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
