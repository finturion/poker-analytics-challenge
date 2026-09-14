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
            "Let op de raise-regel: maximaal twee raises per straat.",
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
    """De twee grafieken waar een getal beter landt dan als tekst."""
    os.makedirs(PLOTMAP, exist_ok=True)

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
        opdrachtdia(prs, onderdeel)
    slotdia(prs)

    prs.save(UITVOER)
    print(f"{len(prs.slides.__iter__.__self__._sldIdLst)} dia's -> {UITVOER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
