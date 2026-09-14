"""
Het deck bij Werkcollege 4 (Week 3): per onderdeel een theoriedia en een
opdrachtdia.

Bedoeld om aan het begin van het werkcollege in één keer door te lopen: wat
komt er vandaag, waarom staat het er, en wat lever je aan het eind in. De
opdrachtdia sluit elk onderdeel af met één regel "inleveren", zodat het hele
huiswerk al aan het begin op tafel ligt.

    python3 powerpoints/maak_presentatie_week3.py

Schrijft powerpoints/Pokerbot_Upgrade_Week3.pptx. Overschrijft alleen zichzelf;
het Week 1-deck blijft ongemoeid.

DE INHOUD KOMT UIT HET NOTEBOOK
-------------------------------
De titels, minuten en beweringen hieronder zijn overgenomen uit
notebooks/Week3_Werkcollege4.ipynb. Verandert dat notebook, dan hoort dit mee
te veranderen -- er is niets dat de twee synchroon houdt, dus de controle
onderaan dit bestand vergelijkt in elk geval de deel-titels en de minuten.
"""

import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pokerplaatjes
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
NOTEBOOK = os.path.join(WORTEL, "notebooks", "Week3_Werkcollege4.ipynb")
PLOTMAP = os.path.join(HIER, "plots_week3")
UITVOER = os.path.join(HIER, "Pokerbot_Upgrade_Week3.pptx")

# Zelfde palet als het Week 1-deck.
BG = RGBColor(248, 249, 250)
PRIMAIR = RGBColor(18, 30, 49)
ACCENT = RGBColor(27, 77, 62)
GEDEMPT = RGBColor(80, 90, 100)
KAART = RGBColor(255, 255, 255)
LIJN = RGBColor(220, 225, 230)
LICHTGROEN = RGBColor(79, 195, 161)
WAARSCHUWING = RGBColor(179, 38, 30)


# ---------------------------------------------------------------------------
# De inhoud, één blok per onderdeel van het notebook
#
# theorie : wat het is en waarom het er staat -- wat je aan het begin vertelt
# opdracht: wat ze doen
# inleveren: wat er aan het eind van moet staan. Precies één regel, want dat is
#            wat je wil dat blijft hangen.
# ---------------------------------------------------------------------------

ONDERDELEN = [
    {
        "nummer": 1,
        "titel": "Python basis",
        "minuten": 33,
        "huiswerk": False,
        "kern": "Functies, list comprehensions, dictionaries, pandas en Plotly",
        "theorie": [
            ("Default-argumenten", "Een parameter met een standaardwaarde: "
             "kies_call_drempel(stack, standaard=30). Je hoeft hem niet mee te geven, "
             "tenzij je hem bewust wil overschrijven."),
            ("Dictionaries", "Een tabel in code: sleutel → waarde. Je bot gebruikt hem "
             "zo meteen om per handsoort een drempel op te zoeken."),
            ("pandas: filteren en groupby", "Van 'alle regels' naar 'alleen wat ik nodig heb', "
             "en dan per groep één getal."),
            ("Plotly express", "Zelfde grafiek als matplotlib, maar je kunt erin klikken "
             "en hoveren. Voor Deel 9."),
        ],
        "opdracht": [
            "Vier korte oefeningen: eerst een gegeven voorbeeld, dan een half voorbeeld "
            "dat je afmaakt.",
            "Dit is gereedschap, geen doel. Alles wat hier langskomt gebruik je vandaag nog.",
        ],
        "inleveren": "Niets apart — dit is de basis voor Deel 3 tot en met 9.",
    },
    {
        "nummer": 2,
        "titel": "Pokerbot Upgrade: hoe het spel écht werkt",
        "minuten": 16,
        "huiswerk": False,
        "kern": "De regels van Texas Hold'em, en wat Bot v2 erbij krijgt",
        # De spelregels zijn het onderdeel waar tekst het slechtst werkt: je
        # moet zien hoe het bord groeit en hoe een hand kantelt. Daarom hier
        # zes beelddia's tussen de theorie en de opdracht.
        "beelddias": [
            ("Twee kaarten van jezelf, vijf van de tafel", "hole_cards",
             "Jouw twee hole cards zijn privé. Wat de anderen hebben weet je niet — "
             "je schat het. Dat schatten is waar Deel 5 over gaat."),
            ("Er ligt al geld in de pot voordat iemand kiest", "tafel",
             "Twee spelers leggen verplicht in: de small blind en de big blind, "
             "twee keer zo groot. Daarom is folden nooit gratis."),
            ("Vier straten, vier keer bieden", "straten",
             "preflop → flop → turn → river. Na elke straat wordt er opnieuw geboden, "
             "dus je bot beslist vier keer per hand."),
            ("Waarom twee kaarten niet genoeg zijn", "handverloop",
             "Twee azen tegen 7-8 schoppen. Preflop is dat geen wedstrijd; "
             "op de river wint 7-8. Dit is geen uitzondering die we hebben opgezocht."),
            ("De kleuren: twee tekens per kaart", "kleuren",
             "Eerst de kleur, dan de rang. SA is schoppen aas. Let op de tien: "
             "in de hulpfuncties heet die T, in je eigen bot \"10\"."),
            ("Wat je bot per beslissing binnenkrijgt", "flowchart",
             "Dit is de hele upgrade van deze week: je kies_actie wordt vier keer "
             "per hand aangeroepen, elke keer met een andere ronde."),
            ("Wat kost een raise eigenlijk?", "raiseladder",
             "Geen verdubbeling: het bod gaat naar het volgende veelvoud van de "
             "big blind. grote_raise is iets anders — die zet in één keer naar 200."),
        ],
        "theorie": [
            ("Twee hole cards", "Privé, alleen jij ziet ze. 'Hole' = in het gat: ze liggen "
             "dicht op tafel. Je hoort ook 'pocket cards'; dat is hetzelfde."),
            ("Blinds", "Twee spelers leggen verplicht in vóór er een kaart is gedeeld. "
             "Er zit dus altijd al geld in de pot voordat iemand een keuze maakt."),
            ("Vier straten", "preflop (alleen je hole cards) → flop (3 erbij) → "
             "turn (4) → river (5). Na elke straat een inzetronde."),
            ("Wat v2 erbij krijgt", "Zijn eigen stack, en straks ook de ronde. Daarmee "
             "reageert hij voor het eerst op de SITUATIE en niet alleen op zijn kaarten."),
        ],
        "opdracht": [
            "Live demo van één hand, en daarna bouw je zelf een rondje op in code.",
            "Let op de raise-regel: maximaal twee raises per straat — een derde wordt een call.",
        ],
        "inleveren": "Niets — dit is de uitleg waar Deel 3 op verder bouwt.",
    },
    {
        "nummer": 3,
        "titel": "Zelf starten: Bot v2 skeleton",
        "minuten": 12,
        "huiswerk": False,
        "kern": "kies_actie(hand, stack) — reageren op twee dingen tegelijk",
        "theorie": [
            ("Van één naar twee parameters", "Bot v1 kende alleen je hand. Bot v2 krijgt "
             "je stack erbij: hoeveel risico kun je je veroorloven?"),
            ("Een patroon, geen voorschrift", "stack > 700 kun je wachten of druk zetten; "
             "300–700 normaal spelen; onder 300 korte-stack-modus. Bedenk je eigen getallen."),
            ("Vier acties", "fold, call, raise, all_in. Wat elke actie doet staat in Deel 2."),
        ],
        "opdracht": [
            "Schrijf kies_actie(hand, stack) in mijn_bot_week3.py.",
            "Bouw hem stap voor stap op: eerst de hand, dan de stack erbij.",
        ],
        "inleveren": "Een werkend skeleton — de rest van de week maak je hem beter.",
    },
    {
        "nummer": 4,
        "titel": "Handsterkte: wat wint er eigenlijk?",
        "minuten": 14,
        "huiswerk": False,
        "kern": "De negen handsoorten, van hoge kaart tot straight flush",
        "theorie": [
            ("Negen soorten", "hoge kaart · één paar · twee paar · three of a kind · straat · "
             "flush · full house · four of a kind · straight flush."),
            ("Vijf uit zeven", "Elke speler maakt de beste 5-kaartshand uit zijn 2 hole cards "
             "plus de 5 gedeelde kaarten."),
            ("Kleur telt hier wél", "Twee tekens: eerst de kleur, dan de rang. SA is "
             "schoppen aas, HK harten heer, DQ ruiten vrouw, CJ klaveren boer. "
             "Zonder kleur kun je geen flush herkennen."),
        ],
        "beelddias": [
            ("De negen handsoorten, zwakste bovenaan", "handsterkte",
             "Elke rij is een echte vijfkaartshand. Let op het verschil tussen "
             "straat (waardes op volgorde) en flush (dezelfde kleur) — en "
             "straight flush, die allebei tegelijk is."),
        ],
        "opdracht": [
            "Laat de helper een paar handen beoordelen en kijk of je de uitkomst had voorspeld.",
            "Let op: de helper klaagt niet als je dezelfde kaart twee keer gebruikt.",
        ],
        "inleveren": "Niets — maar zonder dit is Deel 5 een black box.",
    },
    {
        "nummer": 5,
        "titel": "Winkans: wat je ECHT hebt",
        "minuten": 32,
        "huiswerk": False,
        "kern": "schat_winkans(hand, simulaties=1000, tegenstanders=1)",
        "theorie": [
            ("Monte Carlo", "Speel je hand duizenden keren uit tegen willekeurige "
             "tegenstanders en een willekeurig bord, en tel hoe vaak je wint. "
             "Dezelfde aanpak als n_simulaties in het toernooi."),
            ("Tegen hoeveel mensen?", "Dit is het belangrijkste argument. De standaardwaarde "
             "is 1, maar je zit aan een tafel van zes."),
            ("Gemeten verschil", "A-A gaat van 85,3% naar 50,2% als je van vijf mensen moet "
             "winnen in plaats van één. 7-2 zakt van 33,9% naar 9,3%."),
            ("Advies", "Ga uit van 5 tegenstanders, tenzij je weet dat het er minder zijn."),
        ],
        "opdracht": [
            "Test schat_winkans op bekende sterke en zwakke starthanden.",
            "Draai dezelfde hand met tegenstanders=1 en tegenstanders=5 en leg het verschil uit.",
        ],
        "inleveren": "Je bot gebruikt schat_winkans() met tegenstanders=5.",
        "plot": "winkans",
        "beelddias": [
            ("Monte Carlo: wat is dat eigenlijk?", "montecarlo",
             "Als je een kans niet kunt uitrekenen, probeer je hem gewoon heel vaak. "
             "Tien worpen zeggen niets, duizend worpen komen dicht bij de waarheid. "
             "Meer proberen maakt het antwoord preciezer, nooit anders."),
            ("Zo komt je winkans tot stand", "montecarlo_poker",
             "Je hoeft het niet te bouwen — je moet weten wat het getal betekent, en "
             "tegen hoeveel mensen het gerekend is. Hetzelfde idee als n_simulaties in "
             "het toernooi: één toernooi is toeval, twintig zijn een meting."),
        ],
    },
    {
        "nummer": 6,
        "titel": "Pot odds × winkans: een echte beslisregel",
        "minuten": 16,
        "huiswerk": False,
        "kern": "Call als je winkans hoger is dan wat de pot odds eisen",
        "theorie": [
            ("De twee helften", "bereken_pot_odds(pot, inzet) zegt wat je MINIMAAL moet "
             "winnen. schat_winkans zegt wat je NAAR VERWACHTING wint."),
            ("Rekenen, geen vuistregel", "Pot 100, je moet 20 bijleggen: 20/(100+20) ≈ 17% nodig."),
            ("Waar het stil fout gaat", "Vergelijk je een kop-op-kop-winkans met de prijs aan "
             "een tafel van zes, dan lijkt bijna elke hand de moeite waard. Je bot crasht niet — "
             "hij verliest alleen chips."),
            ("Zelfde regel, ander advies", "Met 7-2: bij 1 tegenstander zegt de regel CALL, "
             "bij 5 tegenstanders FOLD."),
        ],
        "opdracht": [
            "Reken de regel twee keer uit: met tegenstanders=1 en met tegenstanders=5.",
            "Kies daarna je eigen drempel en verdedig hem.",
        ],
        "inleveren": "Een beslisregel in je bot die beide getallen vergelijkt.",
        "plot": "potodds",
    },
    {
        "nummer": 7,
        "titel": "Bot v2 afmaken en verbeteren",
        "minuten": None,
        "huiswerk": True,
        "kern": "Het grootste onderdeel van de week — 4 tot 8 uur",
        "theorie": [
            ("Geen invuloefening", "Er is geen goed antwoord dat wij achter de hand houden. "
             "Hier zit je zelf aan het stuur."),
            ("Waar je tijd in gaat zitten", "kies_actie uitbreiden met ronde, pot en "
             "inzet_om_te_callen: 1–2 uur. De winkans-regel inbouwen en drempels afstemmen: "
             "1–2 uur. Een eigen testset bouwen: 1–2 uur. Reageren op de uitslag: 1–2 uur."),
            ("Twee momenten", "Woensdag 09:00 een werkende bot voor het toernooi. "
             "Donderdag 18:00 je verbeterde versie."),
        ],
        "opdracht": [
            "Bouw verder op je skeleton uit Deel 3.",
            "Test met je eigen situaties, niet alleen met de gegeven voorbeelden.",
        ],
        "inleveren": "wo 09:00 een werkende Bot v2 · do 18:00 je verbeterde versie.",
        "keuzelijst": {
            "titel": "Wat kun je meenemen in Bot v2?",
            "onder": "Je hoeft ze niet alle zes te doen. Kies er twee of drie die bij "
                     "jouw idee van een goede bot passen, en werk die dan ook echt uit.",
            "items": [
                ("Je winkans-grens",
                 "Vanaf welke winkans doe je mee, en vanaf welke raise je? Dat is een getal "
                 "dat jij kiest — en waarvan je kunt meten of een ander getal beter werkt."),
                ("Een andere grens per straat",
                 "Preflop weet je alleen je twee kaarten en komen er nog vijf bij; op de "
                 "river ligt alles er al. Dezelfde 40% betekent daar dus iets anders."),
                ("De pot-odds-regel",
                 "Wiskundig correct maar naief: hij foldt bijna nooit preflop. Wil je dat?"),
                ("Stack-bewustzijn",
                 "Met 90 chips speel je anders dan met 900. Wanneer is all_in een plan?"),
                ("Je twee raises per straat",
                 "Meteen druk zetten, of pas als je het bord ziet? En pak je terug?"),
                ("Hoeveel je inzet",
                 "raise is het minimum, grote_raise zet naar 200. Wanneer is dat het waard?"),
            ],
        },
        "codedias": [
            ("Hoe dat er los in code uitziet",
             "Zes losse stukjes. Geen van alle is af — het zijn de vormen, niet de antwoorden.",
             [("1 · je winkans-grens",
               '# vanaf welke winkans doe je mee?\nGRENS = 40\nwinkans = schat_winkans(hand, tegenstanders=5)\nif winkans > GRENS:\n    return "raise"'),
              ("2 · een andere grens per straat",
               '# zelfde idee, per straat een eigen getal\nGRENS = {"preflop": 45, "flop": 40,\n         "turn": 35, "river": 30}\nif winkans > GRENS[ronde]:\n    return "raise"'),
              ("3 · de pot-odds-regel",
               'nodig = bereken_pot_odds(pot, inzet_om_te_callen)\nif winkans < nodig:\n    return "fold"'),
              ("4 · stack-bewustzijn",
               'if stack < 200:\n    return "all_in" if winkans > 50 else "fold"'),
              ("5 · heeft iemand al geraised?",
               'geraised = any(a["actie"] == "raise"\n               and a["ronde"] == ronde\n               for a in tegenstander_acties_deze_hand)'),
              ("6 · hoeveel zet je in",
               'return "grote_raise" if winkans > 70 else "raise"')]),
            ("En hoe je ze samenvoegt",
             "De volgorde is de hele truc: wat je eerst controleert, overschrijft de rest. "
             "Dit is het skelet — de getallen erin zijn van jou.",
             [("de vorm van je kies_actie",
               'def kies_actie(hand, stack, ronde="preflop",\n'
               '               pot=0, inzet_om_te_callen=0):\n'
               '\n'
               '    winkans = schat_winkans(hand, tegenstanders=5)\n'
               '    nodig   = bereken_pot_odds(pot, inzet_om_te_callen)\n'
               '    grens   = DREMPELS[ronde]\n'
               '\n'
               '    # eerst wat alles overschrijft\n'
               '    if stack < 200:\n'
               '        return "all_in" if winkans > 50 else "fold"\n'
               '\n'
               '    # dan: is deze call de prijs waard?\n'
               '    if winkans < nodig:\n'
               '        return "fold"\n'
               '\n'
               '    # en pas dan: hoe sterk sta je?\n'
               '    if winkans > grens:\n'
               '        return "raise"\n'
               '    return "call"')]),
        ],
    },
    {
        "nummer": 8,
        "titel": "Lokaal testen tegen je eigen Week 1-bot",
        "minuten": 10,
        "huiswerk": True,
        "kern": "Is v2 werkelijk slimmer dan v1?",
        "theorie": [
            ("Zelfde handen, twee bots", "Laat Bot v2 en Bot v1 dezelfde testhanden zien "
             "en vergelijk wat ze kiezen."),
            ("De vraag erachter", "Verwacht je dat v2 slimmer speelt? Waarom wel of niet, "
             "gegeven dat v2 nu ook de stack meeweegt?"),
        ],
        "opdracht": [
            "Bedenk minstens vier testhanden waar je vermoedt dat ze het oneens zijn.",
        ],
        "inleveren": "Niets apart — maar het is je laatste check vóór je inlevert.",
    },
    {
        "nummer": 9,
        "titel": "Plotly-grafiek van het Week 1-toernooi",
        "minuten": 15,
        "huiswerk": True,
        "kern": "Alle bots tegelijk, niet alleen die van jou",
        "theorie": [
            ("Kleur per bot", "Eén lijn per bot, kleur als onderscheid."),
            ("Beperk je scope", "Eén tafel en één simulatie, anders krijg je een "
             "spaghetti-grafiek — daar ga je in Werkcollege 6 mee aan de slag."),
            ("De vraag om te onthouden", "Kun je zónder de legenda af te lezen zien wie er wint? "
             "Bewaar dat gevoel voor Werkcollege 6."),
        ],
        "opdracht": [
            "Bouw de grafiek in Plotly express en geef hem een echte actietitel.",
        ],
        "inleveren": "Een Plotly-grafiek met titel, x_label en y_label.",
    },
    {
        "nummer": 10,
        "titel": "Inleveren via de API",
        "minuten": 10,
        "huiswerk": True,
        "kern": "Zelfde recept als Week 1, met één parameter meer",
        "theorie": [
            ("Drie stappen", "Je bot-bestand inlezen, je grafiek klaarzetten met "
             "export_chart_info(), en versturen met lever_in()."),
            ("Wat er verandert", "Je bot-functie heeft nu 2 parameters in plaats van 1. "
             "Verder verandert er niets. Vanaf Week 5 komen strategie en bluf_kans erbij."),
            ("geldig: False?", "Lees resultaat['bot_check'] en resultaat['chart_check'] — "
             "daar staat in het Nederlands wat er mis is."),
            ("Zo vaak als je wil", "Het systeem gebruikt altijd je laatste geldige inzending."),
        ],
        "opdracht": [
            "Lever in, lees het antwoord, en los op wat er nog niet klopt.",
        ],
        "inleveren": "Een inzending met geldig: True.",
    },
]

SLOT = {
    "wo 09:00": "Een werkende Bot v2 — anders speel je niet mee in het toernooi van woensdag",
    "wo werkcollege": "Je ziet de uitslag terug in Werkcollege 5",
    "do 18:00": "Je verbeterde Bot v2, plus de Plotly-grafiek, plus het onderwerp van Case 2",
}


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def maak_plots():
    """De twee grafieken, plus de tekeningen uit pokerplaatjes.py."""
    os.makedirs(PLOTMAP, exist_ok=True)
    pokerplaatjes.maak_alles(PLOTMAP)

    # Winkans tegen 1 en tegen 5 tegenstanders -- de gemeten cijfers uit Deel 5.
    handen = ["A-A", "K-K", "A-K", "10-9", "7-2"]
    tegen_1 = [85.3, 82.4, 65.4, 57.2, 33.9]
    tegen_5 = [50.2, 43.1, 28.6, 20.8, 9.3]

    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    x = range(len(handen))
    ax.bar([i - 0.2 for i in x], tegen_1, width=0.4, label="1 tegenstander",
           color="#C8D2DC")
    ax.bar([i + 0.2 for i in x], tegen_5, width=0.4, label="5 tegenstanders",
           color="#1B4D3E")
    ax.set_xticks(list(x))
    ax.set_xticklabels(handen)
    ax.set_ylabel("winkans in %")
    ax.set_title("Dezelfde hand, een andere tafel", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=9)
    for rand in ("top", "right"):
        ax.spines[rand].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTMAP, "winkans.png"), bbox_inches="tight")
    plt.close(fig)

    # Pot odds: welke winkans heb je nodig bij welke prijs?
    inzetten = [10, 20, 40, 80, 160]
    pot = 100
    nodig = [i / (pot + i) * 100 for i in inzetten]

    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    ax.plot(inzetten, nodig, marker="o", color="#1B4D3E", linewidth=2)
    ax.axhline(9.3, color="#B3261E", linestyle="--", linewidth=1.2)
    ax.text(163, 10.5, "7-2 aan een volle tafel: 9,3%", color="#B3261E",
            fontsize=8, ha="right")
    ax.set_xlabel("wat je moet bijleggen (pot = 100)")
    ax.set_ylabel("winkans die je minimaal nodig hebt, in %")
    ax.set_title("Hoe duurder de call, hoe vaker je moet winnen", loc="left", fontsize=11)
    for rand in ("top", "right"):
        ax.spines[rand].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTMAP, "potodds.png"), bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Dia-bouwstenen
# ---------------------------------------------------------------------------

def nieuwe_dia(prs):
    dia = prs.slides.add_slide(prs.slide_layouts[6])
    achtergrond = dia.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                       prs.slide_width, prs.slide_height)
    achtergrond.fill.solid()
    achtergrond.fill.fore_color.rgb = BG
    achtergrond.line.fill.background()
    achtergrond.shadow.inherit = False
    return dia


def kop(dia, categorie, titel):
    vak = dia.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.7), Inches(1.1))
    tf = vak.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = categorie
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ACCENT

    p2 = tf.add_paragraph()
    p2.text = titel
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = PRIMAIR
    p2.space_before = Pt(4)


def kaart(dia, links, boven, breedte, hoogte, kleur=KAART):
    vorm = dia.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, links, boven, breedte, hoogte)
    vorm.fill.solid()
    vorm.fill.fore_color.rgb = kleur
    vorm.line.color.rgb = LIJN
    vorm.line.width = Pt(0.75)
    vorm.shadow.inherit = False
    vorm.adjustments[0] = 0.03
    return vorm


def tekstblok(dia, links, boven, breedte, hoogte, regels):
    """regels: lijst van (tekst, puntgrootte, vet, kleur, ruimte_ervoor)."""
    vak = dia.shapes.add_textbox(links, boven, breedte, hoogte)
    tf = vak.text_frame
    tf.word_wrap = True
    for i, (tekst, grootte, vet, kleur, ruimte) in enumerate(regels):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = tekst
        p.font.size = Pt(grootte)
        p.font.bold = vet
        p.font.color.rgb = kleur
        if ruimte:
            p.space_before = Pt(ruimte)
    return vak


def titeldia(prs):
    dia = prs.slides.add_slide(prs.slide_layouts[6])
    vlak = dia.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    vlak.fill.solid()
    vlak.fill.fore_color.rgb = PRIMAIR
    vlak.line.fill.background()
    vlak.shadow.inherit = False

    tekstblok(dia, Inches(1.2), Inches(2.2), Inches(11), Inches(3.2), [
        ("WEEK 3 · WERKCOLLEGE 4", 13, True, LICHTGROEN, 0),
        ("Bot v2: functies, dictionaries, pandas en Plotly", 38, True,
         RGBColor(255, 255, 255), 8),
        ("123 minuten werkcollege · 4 tot 8 uur huiswerk · "
         "twee deadlines: woensdag 09:00 en donderdag 18:00",
         17, False, RGBColor(200, 210, 220), 14),
    ])
    return dia


def overzichtsdia(prs):
    dia = nieuwe_dia(prs)
    kop(dia, "WERKCOLLEGE 4", "Wat komt er vandaag langs?")

    kolommen = [ONDERDELEN[:4], ONDERDELEN[4:7], ONDERDELEN[7:]]
    for k, groep in enumerate(kolommen):
        links = Inches(0.8 + k * 4.0)
        kaart(dia, links, Inches(1.75), Inches(3.7), Inches(4.9))
        regels = []
        for onderdeel in groep:
            tijd = ("huiswerk" if onderdeel["huiswerk"] and not onderdeel["minuten"]
                    else f"{onderdeel['minuten']} min" if onderdeel["minuten"] else "")
            merk = " (huiswerk)" if onderdeel["huiswerk"] and onderdeel["minuten"] else ""
            regels.append((f"Deel {onderdeel['nummer']} — {onderdeel['titel']}",
                           13, True, PRIMAIR, 14 if regels else 0))
            regels.append((f"{tijd}{merk} · {onderdeel['kern']}", 10, False, GEDEMPT, 2))
        tekstblok(dia, links + Inches(0.3), Inches(2.0), Inches(3.1), Inches(4.4), regels)
    return dia


def theoriedia(prs, onderdeel):
    dia = nieuwe_dia(prs)
    tijd = (f"{onderdeel['minuten']} MIN" if onderdeel["minuten"] else "HUISWERK")
    merk = " · HUISWERK" if onderdeel["huiswerk"] and onderdeel["minuten"] else ""
    kop(dia, f"DEEL {onderdeel['nummer']} · {tijd}{merk} · DE THEORIE",
        onderdeel["titel"])

    plot = onderdeel.get("plot")
    breedte = Inches(6.6) if plot else Inches(11.7)

    kaart(dia, Inches(0.8), Inches(1.75), breedte, Inches(4.9))
    regels = []
    for i, (label, uitleg) in enumerate(onderdeel["theorie"]):
        regels.append((label, 14, True, ACCENT, 14 if i else 0))
        regels.append((uitleg, 11.5, False, PRIMAIR, 3))
    tekstblok(dia, Inches(1.1), Inches(2.0), breedte - Inches(0.6), Inches(4.4), regels)

    if plot:
        pad = os.path.join(PLOTMAP, f"{plot}.png")
        if os.path.exists(pad):
            dia.shapes.add_picture(pad, Inches(7.7), Inches(2.3), width=Inches(4.8))
    return dia


BEELD_CATEGORIE = {2: "DE SPELREGELS", 4: "DE RANGORDE",
                   5: "MONTE CARLO", 7: "AAN DE SLAG"}


def beelddia(prs, onderdeel, titel, plaatnaam, uitleg):
    """
    Eén plaat groot in beeld, met één alinea eronder.

    Bewust weinig tekst: dit zijn de dia's waar je bij praat. Staat de uitleg
    er volledig op, dan leest de zaal mee in plaats van te kijken.
    """
    dia = nieuwe_dia(prs)
    categorie = BEELD_CATEGORIE.get(onderdeel["nummer"], "IN BEELD")
    kop(dia, f"DEEL {onderdeel['nummer']} · {categorie}", titel)

    pad = os.path.join(PLOTMAP, f"{plaatnaam}.png")
    if os.path.exists(pad):
        from PIL import Image
        with Image.open(pad) as afbeelding:
            verhouding = afbeelding.height / afbeelding.width
        max_b, max_h = Inches(11.7), Inches(4.45)
        breedte = max_b
        if breedte * verhouding > max_h:
            breedte = Inches(max_h.inches / verhouding)
        links = Inches((13.333 - breedte.inches) / 2)
        dia.shapes.add_picture(pad, links, Inches(1.7), width=breedte)

    tekstblok(dia, Inches(1.1), Inches(6.4), Inches(11.1), Inches(0.85),
              [(uitleg, 12.5, False, PRIMAIR, 0)])
    return dia


def keuzelijstdia(prs, onderdeel, lijst):
    """De dingen die je in je bot kunt stoppen, op een rij en genummerd."""
    dia = nieuwe_dia(prs)
    kop(dia, f"DEEL {onderdeel['nummer']} · 4 TOT 8 UUR", lijst["titel"])

    items = lijst["items"]
    helft = -(-len(items) // 2)
    for kolom in (0, 1):
        links = Inches(0.8 + kolom * 6.05)
        kaart(dia, links, Inches(1.72), Inches(5.75), Inches(3.9))
        regels = []
        for i, (naam, uitleg) in enumerate(items[kolom * helft:(kolom + 1) * helft]):
            nummer = kolom * helft + i + 1
            regels.append((f"{nummer}.  {naam}", 14, True, ACCENT, 16 if i else 0))
            regels.append((uitleg, 11, False, PRIMAIR, 3))
        tekstblok(dia, links + Inches(0.3), Inches(1.98), Inches(5.15), Inches(3.4), regels)

    strook = kaart(dia, Inches(0.8), Inches(5.9), Inches(11.7), Inches(0.95),
                   RGBColor(240, 246, 243))
    strook.line.color.rgb = ACCENT
    tekstblok(dia, Inches(1.1), Inches(6.08), Inches(11.1), Inches(0.7),
              [(lijst["onder"], 12, False, PRIMAIR, 0)])
    return dia


def codedia(prs, onderdeel, titel, onderschrift, blokken):
    """
    Codevoorbeelden in monospace, op een donkere kaart.

    Bewust onaf: de vorm laten zien zonder de getallen weg te geven. Een blok
    dat je kunt overtypen en dat dan werkt, neemt de opdracht weg.
    """
    dia = nieuwe_dia(prs)
    kop(dia, f"DEEL {onderdeel['nummer']} · IN CODE", titel)

    kolommen = 2 if len(blokken) > 1 else 1
    per_kolom = -(-len(blokken) // kolommen)
    breedte = Inches(5.75 if kolommen == 2 else 11.7)

    for index, (label, code) in enumerate(blokken):
        kolom = index // per_kolom
        rij = index % per_kolom
        links = Inches(0.8 + kolom * 6.05)
        hoogte = Inches(4.25 / per_kolom - 0.12)
        boven = Inches(1.72 + rij * (hoogte.inches + 0.12))

        vak = kaart(dia, links, boven, breedte, hoogte, PRIMAIR)
        vak.line.color.rgb = ACCENT

        tekstvak = dia.shapes.add_textbox(links + Inches(0.22), boven + Inches(0.1),
                                          breedte - Inches(0.44), hoogte - Inches(0.2))
        tf = tekstvak.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = LICHTGROEN
        for i, regel in enumerate(code.split("\n")):
            pc = tf.add_paragraph()
            pc.text = regel or " "
            pc.font.size = Pt(10.5 if kolommen == 1 else 9)
            pc.font.name = "Consolas"
            pc.font.color.rgb = RGBColor(232, 238, 244)
            if i == 0:
                pc.space_before = Pt(5)

    tekstblok(dia, Inches(1.1), Inches(6.25), Inches(11.1), Inches(0.9),
              [(onderschrift, 12, False, PRIMAIR, 0)])
    return dia


def opdrachtdia(prs, onderdeel):
    dia = nieuwe_dia(prs)
    tijd = (f"{onderdeel['minuten']} MIN" if onderdeel["minuten"] else "4 TOT 8 UUR")
    kop(dia, f"DEEL {onderdeel['nummer']} · {tijd} · WAT JIJ DOET", onderdeel["titel"])

    kaart(dia, Inches(0.8), Inches(1.75), Inches(11.7), Inches(2.7))
    regels = []
    for i, regel in enumerate(onderdeel["opdracht"]):
        regels.append((f"•  {regel}", 14, False, PRIMAIR, 12 if i else 0))
    tekstblok(dia, Inches(1.1), Inches(2.0), Inches(11.1), Inches(2.2), regels)

    strook = kaart(dia, Inches(0.8), Inches(4.75), Inches(11.7), Inches(1.5),
                   RGBColor(240, 246, 243))
    strook.line.color.rgb = ACCENT
    tekstblok(dia, Inches(1.1), Inches(4.95), Inches(11.1), Inches(1.1), [
        ("WAT JE HIERVAN INLEVERT", 10, True, ACCENT, 0),
        (onderdeel["inleveren"], 15, True, PRIMAIR, 5),
    ])
    return dia


def slotdia(prs):
    dia = nieuwe_dia(prs)
    kop(dia, "WERKCOLLEGE 4 · SLOT", "Wat lever je in, en wanneer?")

    kaart(dia, Inches(0.8), Inches(1.75), Inches(11.7), Inches(3.0))
    regels = []
    for i, (wanneer, wat) in enumerate(SLOT.items()):
        regels.append((wanneer, 16, True, ACCENT, 16 if i else 0))
        regels.append((wat, 13, False, PRIMAIR, 3))
    tekstblok(dia, Inches(1.1), Inches(2.0), Inches(11.1), Inches(2.5), regels)

    strook = kaart(dia, Inches(0.8), Inches(5.05), Inches(11.7), Inches(1.3),
                   RGBColor(252, 242, 241))
    strook.line.color.rgb = WAARSCHUWING
    tekstblok(dia, Inches(1.1), Inches(5.25), Inches(11.1), Inches(0.9), [
        ("De deadline handhaaft zichzelf", 12, True, WAARSCHUWING, 0),
        ("Een toernooi speelt met de bots die er op dat moment zijn. Lever je woensdagmiddag "
         "in, dan doe je niet mee aan het woensdagtoernooi.", 12, False, PRIMAIR, 4),
    ])
    return dia


# ---------------------------------------------------------------------------
# Controle: loopt het deck niet uit de pas met het notebook?
# ---------------------------------------------------------------------------

def controleer_tegen_notebook():
    """
    De titels en minuten hier zijn met de hand overgenomen uit het notebook.
    Verandert daar iets, dan hoort dit deck mee te veranderen -- en deze
    controle is het enige dat dat merkt.
    """
    import json

    with open(NOTEBOOK, encoding="utf-8") as f:
        nb = json.load(f)
    markdown = "\n".join("".join(c["source"]) for c in nb["cells"]
                         if c["cell_type"] == "markdown")

    fouten = []
    for onderdeel in ONDERDELEN:
        patroon = rf"^##\s+Deel {onderdeel['nummer']} — (.+)$"
        m = re.search(patroon, markdown, re.M)
        if not m:
            fouten.append(f"Deel {onderdeel['nummer']} staat niet in het notebook")
            continue
        kop_regel = m.group(1)
        minuten = re.search(r"±?\s*(\d+)\s*min", kop_regel)
        if onderdeel["minuten"] and (not minuten or int(minuten.group(1)) != onderdeel["minuten"]):
            fouten.append(
                f"Deel {onderdeel['nummer']}: deck zegt {onderdeel['minuten']} min, "
                f"notebook zegt \"{kop_regel.strip()}\"")

    if fouten:
        print("\nCONTROLE MISLUKT — het deck loopt uit de pas met het notebook:")
        for f in fouten:
            print("  -", f)
        return False
    print(f"Controle OK: alle {len(ONDERDELEN)} delen en hun minuten kloppen met het notebook.")
    return True


def main():
    if not controleer_tegen_notebook():
        return 1

    maak_plots()

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    titeldia(prs)
    overzichtsdia(prs)
    for onderdeel in ONDERDELEN:
        theoriedia(prs, onderdeel)
        for titel, plaat, uitleg in onderdeel.get("beelddias", []):
            beelddia(prs, onderdeel, titel, plaat, uitleg)
        if onderdeel.get("keuzelijst"):
            keuzelijstdia(prs, onderdeel, onderdeel["keuzelijst"])
        for titel, onderschrift, blokken in onderdeel.get("codedias", []):
            codedia(prs, onderdeel, titel, onderschrift, blokken)
        opdrachtdia(prs, onderdeel)
    slotdia(prs)

    prs.save(UITVOER)
    print(f"{len(prs.slides.__iter__.__self__._sldIdLst)} dia's -> {UITVOER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
