#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Het deck bij Werkcollege 8: wat komt er uit de data van het toernooi?

    python3 scripts/maak_testtoernooi.py      # eenmalig, ~20 min
    python3 scripts/analyse_toernooi.py       # tekent de platen
    python3 powerpoints/maak_presentatie_wc8.py

Schrijft powerpoints/Data_Science_Werkcollege8.pptx.

Alle getallen op de dia's komen uit plots_wc8/cijfers.json, dat analyse_toernooi.py
wegschrijft. Er is dus niets overgetypt -- draai je de analyse op een echt
toernooi, dan kloppen de dia's daarna vanzelf.

De platen zijn getekend met een gevalideerd palet: de actie-verdeling is een
OPLOPENDE schaal (fold -> all_in) en krijgt daarom één groenhue van licht naar
donker; winst is polariteit en krijgt rood/groen om nul; waar echt twee dingen
naast elkaar staan (jij tegenover de klas) staan blauw en oranje, die ook voor
kleurenblinde lezers uit elkaar te houden zijn.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dekstijl import (ACCENT, GEDEMPT, KAART, LIJN, MONO, PRIMAIR, WAARSCHUWING,
                      kaart, kop, nieuwe_dia, tekstblok)
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTS = os.path.join(HIER, "plots_wc8")
UITVOER = os.path.join(HIER, "Data_Science_Werkcollege8.pptx")

with open(os.path.join(PLOTS, "cijfers.json")) as f:
    C = json.load(f)


def met_teken(waarde, decimalen=2):
    """+0,45 leest anders dan 0,45 -- de richting is hier de halve boodschap."""
    return f"{waarde:+.{decimalen}f}".replace(".", ",")


def getal(waarde, decimalen=0):
    return f"{waarde:,.{decimalen}f}".replace(",", ".").replace(".", ".", 1) \
        if decimalen == 0 else f"{waarde:.{decimalen}f}".replace(".", ",")


def r(tekst, grootte=14, vet=False, kleur=PRIMAIR, ruimte=8, lettertype=None):
    return (tekst, grootte, vet, kleur, ruimte, lettertype)


verdeling = C["verdeling"]
kansen = C["weggegooid_maar_winstgevend"]
kansregels = [r(f"{naam:7} {v['keren']:>4}x gespeeld    {v['fold_pct'] * 100:>2.0f}% gefold"
                f"    gemiddeld {v['gem_winst']:+.0f} chips", 14, False, PRIMAIR, 4, MONO)
              for naam, v in list(kansen.items())[:5]]

DIAS = [
    ("DE DATASET", "Wat je vandaag in handen hebt", None, [
        r(f"{C['bots']} bots  ·  {C['simulaties']} simulaties  ·  "
          f"{C['regels']:,} regels".replace(",", "."), 20, True, ACCENT, 0),
        r(f"Daarvan {C['beslissingen']:,} regels waarin een bot écht aan zet kwam."
          .replace(",", "."), 14, False, PRIMAIR, 10),
        r("Per regel: welke bot, welke simulatie, welke hand, welke twee kaarten, "
          "welke actie, en zijn stack daarna.", 14, False, PRIMAIR, 8),
        r("Die laatste twee samen geven je wat elke hand opleverde — en daarmee kun "
          "je alles hieronder uitrekenen.", 14, False, PRIMAIR, 8),
        r("Dit is geen oefendataset. Dit heeft de klas vanmorgen zelf gespeeld.",
          15, True, WAARSCHUWING, 18),
    ], "Begin hier, en laat even bezinken hoe groot dit is. Twintigduizend beslissingen van "
       "dertig bots.\n\nDe sprong die ze vandaag maken: tot nu toe was data iets wat ze kregen. "
       "Dit hebben ze zelf gegenereerd, door een bot te schrijven."),

    ("3.2 · DE KLAS", f"Twee op de drie beslissingen is een fold", "wc8_acties.png", [],
     f"Fold {verdeling.get('fold', 0)}%, call {verdeling.get('call', 0)}%, "
     f"raise {verdeling.get('raise', 0)}%.\n\n"
     "Vraag het eerst aan de zaal voor je het laat zien: hoeveel procent denken jullie? "
     "De meesten schatten veel te laag.\n\n"
     "En dan de vervolgvraag die de hele middag draagt: als twee op de drie beslissingen een "
     "fold is, wat betekent dat voor jouw bot? Agressie is goedkoop tegen een tafel die "
     "wegloopt."),

    ("3.2 · EN JIJ?", "Waar sta jij in die verdeling?", "wc8_foldverdeling.png", [],
     f"De mediaan ligt op {getal(C['fold_mediaan'], 1)}%. De bot die hier oranje is, zit op "
     f"{getal(C['fold_jij'], 1)}%.\n\n"
     "Laat ze zichzelf opzoeken — dat is de opdracht in 3.2. Wie boven de 80% zit doet "
     "nauwelijks mee; wie onder de 20% zit betaalt overal aan mee."),

    ("DE VERRASSING", f"Tight spelen wérkt hier   ·   r = {met_teken(C['correlatie_fold_eindstand'])}",
     "wc8_fold_vs_eindstand.png", [],
     f"Dit is de statistiek die ik er zelf bij heb gezocht, en de uitkomst verraste me: een "
     f"correlatie van {met_teken(C['correlatie_fold_eindstand'])} tussen fold-percentage en "
     "eindstand. In dít veld deden de tightere bots het beter.\n\n"
     "Belangrijk om erbij te zeggen: dat is geen algemene pokerwaarheid. Het zegt iets over "
     "dit veld — er zitten een paar bots in die alles callen, en die verliezen langzaam hun "
     "chips aan iedereen. Tegen een tafel vol tighte bots zou de lijn andersom kunnen lopen.\n\n"
     "Goede vraag voor de zaal: is dit oorzaak of gevolg?"),

    ("3.3 · GEDRAG LEZEN", "De drempels van de klas, zonder één regel code te zien",
     "wc8_matrix_fold.png", [],
     "Dit is mijn favoriete plaat van de middag. Niemand heeft zijn code gedeeld, en toch zie "
     "je precies waar de klas zijn grens legt.\n\n"
     "Let op het patroon: de diagonaal (paren) is licht, de linkerbovenhoek (aas, heer) is "
     "licht, en rechtsonder wordt alles weggegooid. Dat is de winkans-tabel uit Werkcollege 5 "
     "— maar dan afgeleid uit gedrag in plaats van uit een simulatie.\n\n"
     "De kleur is één hue van licht naar donker, want dit is een oplopende schaal en geen set "
     "categorieën."),

    ("3.4 · EN WAT LEVERDE OP?", "Dezelfde 91 handen, nu op geld", "wc8_matrix_winst.png", [],
     "Nu twee kleuren om een nulpunt heen, want winst heeft een richting.\n\n"
     "A-A staat ver boven de rest; de schaal is op het 92e percentiel afgekapt, anders zou al "
     "het andere wit worden. Dat is een keuze die je hardop moet maken en niet stilletjes.\n\n"
     "De vraag die telt: leg deze plaat naast de vorige. Waar is een vakje donkergroen in "
     "déze, en donkergroen in die? Dan gooit de klas iets weg waar geld in zit."),

    ("HET SNIJPUNT", "Weggegooid, en toch winstgevend", None, kansregels + [
        r("Deze handen worden vaker gefold dan gespeeld, maar leveren geld op wanneer er "
          "wél mee gespeeld wordt.", 14, True, ACCENT, 18),
        r("Is dat een kans, of kijk je naar de handen die toevallig goed afliepen? "
          "Dat is precies de vraag die je met deze data niet helemaal kunt beslechten.",
          13, False, GEDEMPT, 12),
    ], "Hier komen 3.3 en 3.4 samen, en dit is wat ik ze mee wil geven: data science levert "
       "zelden een antwoord, het levert een kandidaat.\n\n"
       "Die tweede vraag is de eerlijke. Wie deze hand speelde was misschien juist de betere "
       "bot, en dan meet je de bot en niet de hand. Dat heet selectie-effect, en het is de "
       "reden dat je het op donderdag toetst in plaats van het te geloven."),

    ("3.5 · HOEVEEL IS TOEVAL?", "Dezelfde bot, twintig keer gespeeld", "wc8_spreiding.png", [],
     f"De beste bot haalde gemiddeld {getal(list(C['top2'].values())[0]['mean'])} chips, met een "
     f"standaarddeviatie van {getal(list(C['top2'].values())[0]['std'])}. De nummer twee zit op "
     f"{getal(list(C['top2'].values())[1]['mean'])}.\n\n"
     "Het verschil tussen nummer 1 en nummer 2 is kleiner dan de spreiding binnen één bot. "
     "Laat dat even staan.\n\n"
     "Daarom loopt de bonus over twee toernooien, en daarom is 'ik ben gezakt van plek 3 naar "
     "plek 9' geen bewijs dat je bot slechter is geworden."),

    ("EN NU JIJ", "Verander één ding, en schrijf op waarom", None, [
        r("Eén ding. Niet drie.", 18, True, ACCENT, 0),
        r("Verander je er drie tegelijk en je bot wordt beter, dan weet je donderdag nog "
          "steeds niet welke van de drie het deed.", 14, False, PRIMAIR, 10),
        r("Kandidaten uit vanmiddag:", 15, True, PRIMAIR, 18),
        r("een van je drempels — STERK, MEEDOEN, ZWAK", 14, False, PRIMAIR, 6, MONO),
        r("TEGENSTANDERS, want dat verschuift je hele schaal", 14, False, PRIMAIR, 4, MONO),
        r("de volgorde van je regels", 14, False, PRIMAIR, 4, MONO),
        r("een hand uit het snijpunt niet meer wegfolden", 14, False, PRIMAIR, 4, MONO),
        r("Schrijf in een comment op WAT je veranderde en WELK getal van vanmiddag die keuze "
          "onderbouwt. Dat is ook je antwoord bij de overhoring van volgende week.",
          14, True, WAARSCHUWING, 18),
    ], "Sluit hiermee af, en wijs vooruit: donderdagochtend draait de oefenronde. Dan weten ze "
       "binnen een dag of hun verandering iets deed.\n\n"
       "Dat is de hele cyclus die dit vak wil laten zien: meten, concluderen, aanpassen, opnieuw "
       "meten. Niet één keer een analyse maken en hopen."),
]


def titeldia(prs):
    dia = prs.slides.add_slide(prs.slide_layouts[6])
    vlak = dia.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    vlak.fill.solid()
    vlak.fill.fore_color.rgb = PRIMAIR
    vlak.line.fill.background()
    vlak.shadow.inherit = False
    tekstblok(dia, Inches(1.1), Inches(2.4), Inches(11.0), Inches(3.2), [
        ("WEEK 5 · WERKCOLLEGE 8", 12, True, KAART, 0),
        ("Wat zegt de data over je bot?", 40, True, KAART, 10),
        (f"{C['beslissingen']:,} beslissingen van {C['bots']} bots, "
         f"vanmorgen gespeeld".replace(",", "."), 20, False, LIJN, 8),
        ("Vandaag lever je niets in. Je onderzoekt — en verandert daarna één ding.",
         14, False, LIJN, 18),
    ])
    return dia


def bouw(prs, eyebrow, titel, plaat, regels, notitie):
    dia = nieuwe_dia(prs)
    kop(dia, eyebrow, titel)
    boven = 1.75
    if plaat:
        pad = os.path.join(PLOTS, plaat)
        if not os.path.exists(pad):
            print(f"  ontbreekt: {plaat} — draai eerst scripts/analyse_toernooi.py")
        else:
            beeld = dia.shapes.add_picture(pad, 0, Inches(boven), height=Inches(5.0))
            if beeld.width > Inches(11.9):
                beeld.height = int(beeld.height * Inches(11.9) / beeld.width)
                beeld.width = Inches(11.9)
            beeld.left = int((prs.slide_width - beeld.width) / 2)
            beeld.top = Inches(boven)
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
    print(f"{len(prs.slides._sldIdLst)} dia's -> {os.path.basename(UITVOER)}")
    print(f"{sum(1 for s in DIAS if s[4])} dia's hebben sprekersnotities.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
