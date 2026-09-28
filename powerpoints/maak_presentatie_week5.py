#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Het deck bij Werkcollege 7 (Week 5): Bot v3.

    python3 powerpoints/wc7plaatjes.py          # eerst de platen
    python3 powerpoints/maak_presentatie_week5.py

Schrijft powerpoints/Pokerbot_Upgrade_Week5.pptx.

Weinig tekst, veel beeld. De kern is één dia: het overzicht van alles waar de bot
op kan letten. Daar hoort een opdracht bij die vóór het programmeren komt --
eerst je eigen schema tekenen, dan pas typen. Een beslisregel die je niet kunt
tekenen, kun je ook niet debuggen.

Dezelfde flowchart staat in het notebook, als mermaid. Deze versie is getekend
met matplotlib omdat mermaid niet naar een plaatje rendert dat je in een dia kunt
zetten -- zie wc7plaatjes.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dekstijl import (ACCENT, GEDEMPT, KAART, LIJN, MONO, PRIMAIR, WAARSCHUWING,
                      kaart, kop, nieuwe_dia, tekstblok)
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(HIER, "plots_week5")
UITVOER = os.path.join(HIER, "Pokerbot_Upgrade_Week5.pptx")


def r(tekst, grootte=14, vet=False, kleur=PRIMAIR, ruimte=8, lettertype=None):
    return (tekst, grootte, vet, kleur, ruimte, lettertype)


DIAS = [
    ("DEEL 1 · DE BOUWSTENEN", "Vijf blokjes, één voor één", None, [
        r("1A  hand · stack      →  heb ik nog ruimte om te spelen?", 15, True, PRIMAIR, 0, MONO),
        r("1B  winkans           →  hoe sterk sta ik, nu ook mét het bord", 15, True, PRIMAIR, 6, MONO),
        r("1C  pot · inzet       →  wat kost meedoen?", 15, True, PRIMAIR, 6, MONO),
        r("1D  tegenstander_acties →  wat doet de tafel?", 15, True, ACCENT, 6, MONO),
        r("1E  bluf_kans         →  ga ik bluffen?", 15, True, ACCENT, 6, MONO),
        r("De laatste twee zijn nieuw. 1D is nieuw in soort: voor het eerst krijgt je bot "
          "informatie over iemand anders.", 13, False, GEDEMPT, 18),
        r("Elk blokje krijgt één simpele regel. In Deel 2 plak je ze achter elkaar en schrijf "
          "je ze weg naar mijn_bot_week5.py.", 14, False, PRIMAIR, 10),
    ], "Het idee van deze opzet: niemand kan een bot van vijftig regels in één keer bedenken.\n\n"
       "Elke regel geeft óf een actie, óf None — 'ik ga hier niet over'. Daardoor is samenvoegen "
       "in Deel 2 niets meer dan de regels in een volgorde zetten."),

    ("HET OVERZICHT", "Waar je bot allemaal op kan letten", "wc7_overzicht.png", [], None),

    ("VÓÓR JE GAAT TYPEN · 5 MIN", "Teken eerst je eigen schema", None, [
        r("Welke van die vijf vragen stel jij, in welke volgorde, en waar valt de beslissing?",
          16, True, PRIMAIR, 0),
        r("Op papier. Geen code.", 15, True, ACCENT, 14),
        r("Je hoeft niet alles te gebruiken. Een bot die twee takken goed doet, verslaat "
          "er een die er vijf half doet.", 14, False, PRIMAIR, 14),
        r("Een beslisregel die je niet kunt tekenen, kun je ook niet debuggen. En woensdag "
          "over een week moet je 'm kunnen uitleggen — dan heb je je tekening al.",
          13, False, GEDEMPT, 16),
    ], "Laat ze het echt doen, vijf minuten, en loop rond. Wie meteen begint te typen komt "
       "later vast te zitten op precies de plek waar zijn schema een gat had.\n\n"
       "Vraag bij twee of drie mensen: welke tak heb je weggelaten, en waarom? Dat is een "
       "betere vraag dan 'is het gelukt'."),

    ("1B · DE SCHAAL", "Waar komen je drempels vandaan?", None, [
        r("schat_winkans(..., tegenstanders=N) verandert je hand niet —", 16, True, PRIMAIR, 0),
        r("het verandert de schaal waarop je hem afleest.", 16, True, PRIMAIR, 2),
        r("tegenstanders    gemiddelde hand wint    'goed' begint rond", 13, True, GEDEMPT, 18, MONO),
        r("      1                  50%                    60%", 14, False, PRIMAIR, 6, MONO),
        r("      2                  33%                    45%", 14, True, ACCENT, 4, MONO),
        r("      5                  17%                    25%", 14, False, PRIMAIR, 4, MONO),
        r("Kies één getal, houd het vast, en kies je drempels op díe schaal. "
          "De bot in Deel 2 rekent met 2.", 14, True, PRIMAIR, 18),
        r("Zet je drempel op 50 terwijl je tegen vijf rekent, dan doe je nooit mee — zelfs A-A "
          "haalt daar 50,2%. Vorig jaar was 92% van alle beslissingen een fold.",
          13, False, WAARSCHUWING, 12),
    ], "Vraag het eerst aan de zaal: 'wat is een góede winkans?' Je krijgt 60, 70, 80 — en dat "
       "klopt alleen als je tegen één iemand speelt.\n\n"
       "Het punt is niet welk getal ze kiezen, maar dát ze er één kiezen en hun drempels erop "
       "afstemmen. Wie tegen 5 rekent en een drempel van 50 aanhoudt, heeft een bot die foldt.\n\n"
       "In 1D staat hoe je het aantal tegenstanders kunt schatten uit de actielijst. Dat mag, "
       "maar dan moeten de drempels meeschuiven — dat staat er expliciet bij."),

    ("EN WAT HIJ NIET WEET", "Drie dingen die er niet in staan", None, [
        r("Welke kaarten de anderen hebben", 16, True, PRIMAIR, 0),
        r("En ook niet hun stacks.", 12, False, GEDEMPT, 2),
        r("Wat er in eerdere handen gebeurde", 16, True, PRIMAIR, 16),
        r("Elke hand begint schoon.", 12, False, GEDEMPT, 2),
        r("Hoeveel tegenstanders er nog meespelen", 16, True, PRIMAIR, 16),
        r("Staat er niet bij — maar dit kun je wél schatten uit tegenstander_acties_deze_hand: "
          "tel de namen, haal eruit wie foldde.", 12, False, GEDEMPT, 2),
        r("En let op de namen: je krijgt een parameter alleen als je hem zelf opschrijft, exact "
          "zo gespeld. Verkeerd gespeld = je krijgt hem niet, zonder foutmelding.",
          13, False, WAARSCHUWING, 18),
    ], None),

    ("DEEL 4 EN 5 · HUISWERK", "Waarom je een locatie meegeeft", "wc7_locatie.png", [],
     "Dit is de dia waar de vraag 'moet dat nou' wordt beantwoord.\n\n"
     "Maandag lever je een lat/lon in en bouw je de kaart met een verzonnen klas — er is "
     "nog niets om op te halen. Die kaart is wél de grafiek die je woensdag inlevert.\n\n"
     "Woensdag is het toernooi gedraaid en kleurt dezelfde kaart zichzelf in. In "
     "Werkcollege 9 wordt het een choropleth van heel Nederland, met de gemeentegrenzen "
     "uit een API."),

    ("DE BONUS", "Wat het oplevert, en wat toeval is", "wc7_bonus.png", [],
     "De cijfers rechts komen uit scripts/meet_toernooi_variantie.py: 44 bots met bekende "
     "kwaliteit, 20 simulaties per bot (wat de bonusweek ook draait), vijf verschillende "
     "kaartverdelingen.\n\n"
     "Zeg allebei de kanten eerlijk. Goed spelen loont: 76% van de punten gaat naar de betere "
     "helft van het veld, terwijl dat bij puur toeval 50% zou zijn. Maar wie precies in de "
     "top 5 valt, wisselt: deel opnieuw en er gaat gemiddeld nog maar 0,9 van de 5 plekken "
     "naar dezelfde bot.\n\n"
     "De boodschap: je kunt je kánsen vergroten, je kunt de bonus niet afdwingen. En andersom "
     "— val je net buiten de prijzen, dan is dat geen oordeel over je bot."),

    ("EN DAARNA", "Wie bonus scoort, legt zijn bot uit", None, [
        r("Woensdag 7 oktober overhoor ik iedereen die bonuspunten heeft gescoord.",
          17, True, PRIMAIR, 0),
        r("Geen strikvragen. Drie dingen:", 15, True, ACCENT, 16),
        r("1.  welke regels zitten in je bot?", 15, False, PRIMAIR, 8, MONO),
        r("2.  in welke volgorde staan ze, en waarom?", 15, False, PRIMAIR, 4, MONO),
        r("3.  wat heb je veranderd na het eerste toernooi, en waarop?", 15, False, PRIMAIR, 4, MONO),
        r("Dus: schrijf op waarom je iets verandert, terwijl je het verandert. Een comment van "
          "één regel is genoeg — achteraf reconstrueren lukt niemand.",
          14, True, WAARSCHUWING, 20),
    ], "Dit is er niet om mensen te betrappen, en dat mag je ook hardop zeggen. Het is er omdat "
       "de bonus anders beloont dat je iemands bot overneemt.\n\n"
       "Wie zijn eigen bot heeft gebouwd, heeft hier vijf minuten werk aan. Wie dat niet heeft, "
       "merkt dat meteen."),

    ("DE PLANNING", "De komende twee weken", "wc7_planning.png", [],
     "Twee dingen waar ze op moeten letten.\n\n"
     "Vandaag: de groepscase komt na de pauze, en ze kiezen vandaag een onderwerp. Woensdag "
     "leg ik de eindopdracht uit.\n\n"
     "Maandag 5 oktober: vanaf 13:00/13:15 is er tijd om samen aan de case te werken, om 13:30 "
     "leggen we de onderwerpen definitief vast. Het werkcollege zelf gaat die middag alleen "
     "over de visuele kant — de kaart uit week 5 opnieuw ontwerpen in twee lagen. Wie moet "
     "herkansen, doet dat die middag."),
]


def titeldia(prs):
    dia = prs.slides.add_slide(prs.slide_layouts[6])
    vlak = dia.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    vlak.fill.solid()
    vlak.fill.fore_color.rgb = PRIMAIR
    vlak.line.fill.background()
    vlak.shadow.inherit = False
    tekstblok(dia, Inches(1.1), Inches(2.5), Inches(11.0), Inches(3.0), [
        ("WEEK 5 · WERKCOLLEGE 7", 12, True, KAART, 0),
        ("Bot v3", 44, True, KAART, 10),
        ("Bluffen, tegenstanders lezen, en je laatste versie", 20, False, LIJN, 6),
        ("Dit is de bot waarmee je de reeks afsluit.", 14, False, LIJN, 20),
    ])
    return dia


def bouw(prs, eyebrow, titel, plaat, regels, notitie):
    dia = nieuwe_dia(prs)
    kop(dia, eyebrow, titel)
    boven = 1.75
    if plaat:
        pad = os.path.join(PLOTS, plaat)
        if os.path.exists(pad):
            beeld = dia.shapes.add_picture(pad, 0, Inches(boven), height=Inches(4.9))
            if beeld.width > Inches(11.9):
                beeld.height = int(beeld.height * Inches(11.9) / beeld.width)
                beeld.width = Inches(11.9)
            beeld.left = int((prs.slide_width - beeld.width) / 2)
            beeld.top = Inches(boven)
        else:
            print(f"  ontbreekt: {plaat} — draai eerst wc7plaatjes.py")
    if regels:
        kaart(dia, Inches(0.8), Inches(boven), Inches(11.7), Inches(4.9))
        tekstblok(dia, Inches(1.25), Inches(boven + 0.35), Inches(10.8), Inches(4.2), regels)
    if notitie:
        dia.notes_slide.notes_text_frame.text = notitie.strip()
    return dia


def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    titeldia(prs)
    for spec in DIAS:
        bouw(prs, *spec)
    prs.save(UITVOER)
    met = sum(1 for s in DIAS if s[4])
    print(f"{len(prs.slides._sldIdLst)} dia's -> {os.path.basename(UITVOER)}")
    print(f"{met} dia's hebben sprekersnotities.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
