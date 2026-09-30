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
    ("DE UITSLAG", "Wie pakt er een bonuspunt?", "wc8_uitslag.png", [],
     "Hiermee open je, want dit is wat iedereen wil weten.\n\n"
     "De ladder: 0,5 - 0,4 - 0,3 - 0,2 - 0,1 voor de eerste vijf, en verder niets. Twee "
     "toernooien die meetellen, dus maximaal 1,0 bonuspunt over de hele week. Eindigen twee "
     "bots op exact dezelfde winst, dan delen ze de plekken en krijgen ze allebei het "
     "gemiddelde van die punten — anders bepaalt een toevallige volgorde wie de hogere plek "
     "krijgt, en daar hang je geen bonuspunt aan op.\n\n"
     "LET OP: zolang de oranje regel er staat zijn dit verzonnen studentnummers uit een "
     "testtoernooi. Draai scripts/analyse_toernooi.py op de echte export en de dia klopt "
     "vanzelf — inclusief deze sprekersnotitie, want die getallen komen uit hetzelfde "
     "cijfers.json.\n\n"
     "Wie hier net buiten valt: dia 13 laat zien hoe dun dat verschil is."),

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

    ("TERUG NAAR VISUAL MAANDAG", "Vijf dingen die je vandaag meteen nodig hebt", None, [
        r("1.  filteren        dertig bots in één plot is spaghetti", 15, False, PRIMAIR, 0, MONO),
        r("2.  uitlichten      jouw bot in kleur, de rest grijs", 15, False, PRIMAIR, 6, MONO),
        r("3.  actietitel      beweer iets, benoem niet alleen", 15, True, ACCENT, 6, MONO),
        r("4.  annoteren       waar gebeurt het? zet er een streep bij", 15, False, PRIMAIR, 6, MONO),
        r("5.  contrast-check  leest je kleur ook voor de rest van de klas?", 15, False, PRIMAIR, 6, MONO),
        r("Alles wat hierna komt is daarop gebouwd. De kleurschalen lopen van blauw naar "
          "groen en niet van rood naar groen, omdat rood en groen voor een deel van je "
          "klasgenoten bijna dezelfde kleur zijn.", 13, False, GEDEMPT, 20),
        r("Dat is geen detail. Dat is Werkcollege 6, Deel 6 — nu op jullie eigen data.",
          14, True, PRIMAIR, 12),
    ], "Kort ophalen, niet opnieuw uitleggen. Ze hebben dit vorige week gedaan; het punt is dat "
       "ze zien dat het nu ergens voor dient.\n\n"
       "De kleurkeuze mag je hardop verantwoorden: ik heb het groen-rood van onze eigen "
       "huisstijl door een kleurenblindheidstest gehaald en het zakte — de twee liggen voor "
       "protanopie te dicht bij elkaar. Vandaar blauw. Dat is precies het soort controle dat "
       "zij in Deel 6 hebben geleerd."),

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

    ("DE VERRASSING", f"Defensief spelen wérkt hier   ·   r = {met_teken(C['correlatie_fold_eindstand'])}",
     "wc8_fold_vs_eindstand.png", [],
     f"Dit is de statistiek die ik er zelf bij heb gezocht, en de uitkomst verraste me: een "
     f"correlatie van {met_teken(C['correlatie_fold_eindstand'])} tussen fold-percentage en "
     "eindstand. In dít veld deden de defensievere bots het beter.\n\n"
     "Belangrijk om erbij te zeggen: dat is geen algemene pokerwaarheid. Het zegt iets over "
     "dit veld — er zitten een paar bots in die alles callen, en die verliezen langzaam hun "
     "chips aan iedereen. Tegen een tafel vol defensieve bots zou de lijn andersom kunnen lopen.\n\n"
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

    ("JOUW EIGEN SPEL", "Dezelfde bot, twintig keer een ander verhaal",
     "wc8_stackverloop.png", [],
     f"Hier staat Visual Maandag in één plaat: twintig grijze lijnen, twee uitgelicht, en een "
     f"titel die iets beweert.\n\n"
     f"Deze bot eindigde in zijn beste simulatie op {getal(C['eigen_beste'])} chips en in zijn "
     f"slechtste op {getal(C['eigen_slechtste'])}. Zelfde code, zelfde drempels, andere kaarten.\n\n"
     "Laat ze dit zelf maken voor hun eigen bot — het is één groupby en een plot, en het is de "
     "meest persoonlijke grafiek van de middag."),

    ("JOUW ACTIES", "Levert jouw raise meer op dan die van de klas?",
     "wc8_jij_tegenover_klas.png", [],
     "Dit is de grafiek die het dichtst bij 'wat moet ik veranderen' komt. Per actiesoort: wat "
     "leverde die jou op, en wat leverde die de rest op?\n\n"
     "Let op de n= achter elk getal, en maak daar een punt van. In dit voorbeeld verliest de "
     "grote raise 84 chips per hand terwijl de klas er 175 mee wint — maar over zeven handen. "
     "Dat is geen conclusie, dat is een aanwijzing waar je verder moet kijken.\n\n"
     "Wie hier een echt verschil ziet bij een actie die hij vaak doet, heeft zijn verandering "
     "voor Deel 4 gevonden."),

    ("WAAR GING JE GELD HEEN?", "Niet het gemiddelde, maar het totaal",
     "wc8_totale_bijdrage.png", [],
     f"Een gemiddelde verstopt hoe vaak iets voorkwam. Hier staat de optelsom: welke handen "
     f"hebben jou over het hele toernooi het meeste gekost, en welke het meeste opgeleverd.\n\n"
     f"In dit voorbeeld is {C['duurste_hand']['hand']} de duurste hand "
     f"({getal(C['duurste_hand']['totaal'])} chips over {C['duurste_hand']['keren']} handen) en "
     f"{C['beste_hand']['hand']} de beste (+{getal(C['beste_hand']['totaal'])} over "
     f"{C['beste_hand']['keren']}).\n\n"
     "De vraag die ze zichzelf moeten stellen: speel ik die duurste hand eigenlijk wel bewust, "
     "of valt hij per ongeluk binnen een van mijn drempels?"),

    ("3.5 · HOEVEEL IS TOEVAL?", "Hoe stevig is een plek in de top-5?", "wc8_spreiding.png", [],
     f"De beste bot haalde gemiddeld {getal(list(C['top2'].values())[0]['mean'])} chips, met een "
     f"standaarddeviatie van {getal(list(C['top2'].values())[0]['std'])}. De nummer twee zit op "
     f"{getal(list(C['top2'].values())[1]['mean'])}.\n\n"
     "Het verschil tussen nummer 1 en nummer 2 is kleiner dan de spreiding binnen één bot. "
     "Laat dat even staan.\n\n"
     "Daarom loopt de bonus over twee toernooien, en daarom is 'ik ben gezakt van plek 3 naar "
     "plek 9' geen bewijs dat je bot slechter is geworden."),

    ("EN DAARNA", "Waar kun je nog naar kijken?", "wc8_routes.png", [],
     "Dit is het antwoord op 'ik ben klaar, wat nu'. Drie sporen, en het middelste is het "
     "belangrijkste en het minst voor de hand liggende.\n\n"
     "Neem even de tijd voor die rode regel onderin. Het logboek heeft ÉÉN regel per hand, "
     "met alleen de eerste actie van die hand. Alles wat per ronde, per pot of per "
     "tegenstander speelt staat er dus niet in. Dat is geen omissie maar een ontwerpkeuze: "
     "een regel per beslissing zou het logboek vijf keer zo groot maken.\n\n"
     "Wie dáár iets over wil weten, moet zijn bot het zelf laten opschrijven. Dat is de "
     "volgende dia."),

    ("HOE VERZIN JE ZO'N VRAAG?", "Je leest hem af van je eigen bot", "wc8_regels.png", [],
     "Dit is de dia waar ik de meeste waarde van verwacht, want 'bedenk een analyse' is een "
     "opdracht waar de meesten op vastlopen.\n\n"
     "Het punt: je verzint niets. Je hebt in Werkcollege 7 vijf regels geschreven, en in elke "
     "regel staat een getal dat je op gevoel hebt gekozen — 150, STERK, MEEDOEN, ZWAK. Elk van "
     "die getallen is een hypothese. Stel over elk dezelfde twee vragen: hoe vaak vuurt deze "
     "regel, en wat levert hij op als hij vuurt?\n\n"
     "Loop ze samen langs en laat ze bij hun eigen bot kijken. Wie een regel heeft die nooit "
     "vuurt, heeft dode code — en dat is op zichzelf al een bevinding.\n\n"
     "De kleur rechts zegt waar het antwoord vandaan komt, en sluit aan op de vorige dia: "
     "blauw is het logboek, oranje moet je zelf laten opschrijven."),

    ("SPOOR 2", "Laat je bot opschrijven wat hij doet", None, [
        r("Drie regels erbij, en je hebt data die niemand anders heeft:", 15, True, PRIMAIR, 0),
        r("BESLISSINGEN = []", 13, False, PRIMAIR, 14, MONO),
        r("", 13, False, PRIMAIR, 2, MONO),
        r("def kies_actie(hand, ..., ronde, pot, inzet_om_te_callen, ...):", 13, False, GEDEMPT, 2, MONO),
        r("    winkans = schat_winkans(...)", 13, False, GEDEMPT, 2, MONO),
        r("    ...", 13, False, GEDEMPT, 2, MONO),
        r("    BESLISSINGEN.append({\"ronde\": ronde, \"winkans\": winkans,", 13, True, ACCENT, 2, MONO),
        r("                         \"pot\": pot, \"regel\": \"bluf\", \"actie\": actie})", 13, True, ACCENT, 2, MONO),
        r("    return actie", 13, False, GEDEMPT, 2, MONO),
        r("Daarna speel_duel() draaien en pd.DataFrame(BESLISSINGEN) analyseren. Nu kun je "
          "wél zien wat je winkans per straat was, hoe vaak je bluf-regel vuurde, en welke "
          "van je vijf regels de beslissing nam.", 13, False, PRIMAIR, 16),
        r("Let op: dit doe je LOKAAL. In je inzending hoort geen logboek — daar telt alleen "
          "wat kies_actie teruggeeft.", 13, True, WAARSCHUWING, 10),
    ], "Dit is de meest waardevolle dia van het hele slot, en de makkelijkste om over te slaan.\n\n"
       "Het idee is simpel: je bot weet op het moment van beslissen alles — de ronde, de pot, "
       "zijn winkans, welke regel er vuurde. Die kennis gooit hij nu weg. Eén append per "
       "beslissing en je houdt hem vast.\n\n"
       "Koppel het aan de vijf-regelstructuur uit Werkcollege 7: door 'regel' mee te loggen "
       "kun je achteraf per regel uitrekenen wat hij opleverde. Dan weet je welke van je vijf "
       "regels het werk doet en welke er alleen maar staat."),

    ("SPOOR 3", "Meer weten over je hand — dat kan gewoon", None, [
        r("schat_winkans(hand_met_kleur, bord=bord, tegenstanders=n)", 14, True, ACCENT, 0, MONO),
        r("De winkans verandert enorm met het bord en met het aantal tegenstanders. "
          "Dezelfde A-K: 38,5% preflop, 75,5% na de ene flop, 22,3% na de andere.",
          13, False, PRIMAIR, 6),
        r("beschrijf_hand(hand_met_kleur, bord)", 14, True, ACCENT, 18, MONO),
        r("Geeft terug wat je wérkelijk hebt: 'one pair', 'three of a kind', 'flush'. "
          "Daarmee kun je regels schrijven op handsóórt in plaats van op een percentage.",
          13, False, PRIMAIR, 6),
        r("vergelijk_handen(jouw_hand, andere_hand, bord)", 14, True, ACCENT, 18, MONO),
        r("Wie wint deze showdown? Zelfde evaluatie als het toernooi, dus inclusief kickers.",
          13, False, PRIMAIR, 6),
        r("Alle drie staan in _hulpfuncties_week3.py. Je kent ze uit Werkcollege 5, en "
          "in week 5 heeft bijna niemand ze nog gebruikt.", 13, True, GEDEMPT, 18),
    ], "Sluit hiermee af als er tijd over is. Het punt: ze denken dat ze alleen een percentage "
       "hebben, terwijl beschrijf_hand() ze de handsóórt geeft.\n\n"
       "Een regel als 'bij three of a kind of beter ga ik door, wat de winkans ook zegt' is "
       "voor sommigen begrijpelijker dan drempels, en het is een volwaardige strategie.\n\n"
       "vergelijk_handen is vooral nuttig om te begrijpen waarom je een hand verloor die je "
       "dacht te winnen — kickers."),

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
