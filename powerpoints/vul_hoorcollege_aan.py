"""
Voegt dia's toe aan het hoorcollege-deck over EDA en datamanipulatie.

Het origineel wordt NOOIT overschreven: dit script leest het bronbestand en
schrijft een nieuwe kopie ernaast. De opmaak volgt die van het deck zelf --
Arial, titel 32pt in #25167A op (2.17, 1.03), tekstblok op (2.17, 2.28) --
zodat de nieuwe dia's niet opvallen tussen de bestaande.

    python3 powerpoints/vul_hoorcollege_aan.py "/pad/naar/03_Exploring Manipulating Data.pptx"

Schrijft powerpoints/hoorcollege/03_Exploring_Manipulating_Data_aangevuld.pptx
"""
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

HIER = os.path.dirname(os.path.abspath(__file__))
UITVOER = os.path.join(HIER, "hoorcollege", "03_Exploring_Manipulating_Data_aangevuld.pptx")
# Getekend door maak_histogram_hoorcollege.py. Ontbreekt hij, dan slaat de dia hem over.
HISTOGRAM = os.path.join(HIER, "plots_week3", "winst_histogram.png")

TITELKLEUR = RGBColor(0x25, 0x16, 0x7A)
TEKSTKLEUR = RGBColor(0x00, 0x00, 0x00)
ACCENT = RGBColor(0x1B, 0x4D, 0x3E)
GEDEMPT = RGBColor(0x50, 0x5A, 0x64)

# De cijfers van het toernooi, op één plek.
#
# Elke ronde verschuiven ze en het verhaal niet, dus ze staan hier en niet
# verspreid door de dia's. Draai na een nieuwe ronde:
#
#     python3 scripts/collegecijfers.py --api --week 3 --ronde N --bewaar uitslag.json
#
# en neem de vier blokken die dat print hieronder over. De dia's, de notities en
# het doorloopblad lezen allemaal uit deze dict.
CIJFERS = {
    "ronde": 3,
    "bots": 27,
    "studenten": 26,
    "logregels": 6750,
    "simulaties": 5,

    # blok 1 -- df["winst"].describe()
    "gemiddelde": "0,0",
    "mediaan": "0,0",
    "std": "39",
    "laagste": "-1030",
    "hoogste": "+1750",

    # blok 2 -- de verdeling van winst per hand
    "bakjes": [
        ("-200 en lager", 9),
        ("-100 tot -20", 53),
        ("-20 tot -1", 1488),
        ("0 tot 20", 4838),
        ("20 tot 50", 310),
        ("200 en hoger", 7),
    ],

    # blok 3 -- acties, alleen over de handen waarin de bot aan zet was
    "acties": [
        ("fold", "92,2%", "-3", "0"),
        ("call", "5,9%", "+10", "+30"),
        ("raise", "1,3%", "+65", "+30"),
        ("grote_raise", "0,6%", "+19", "+30"),
    ],

    # blok 4 -- de kop van de uitslag
    "uitslag": [
        (1, "Testbot_CalltAlles", 1748, "0%"),
        (2, "501011284", 1738, "82,5%"),
        (3, "500959250", 1256, "58,7%"),
        (4, "500851324", 1202, "96,3%"),
    ],
    "correlatie": "-0,69",
    "voorsprong": 10,
}

def doorloopblad_dias(c):
    """
    De vier blokken van het doorloopblad als dia's, opgebouwd uit de cijfers.

    Ze horen bij elkaar en in deze volgorde: eerst wat de samenvatting verbergt,
    dan waarom je dat in de verdeling wél ziet, dan wat de klas deed, en dan wie
    er won. Elk blok begint met de regel code die het getal maakt, zodat een
    student de dia in zijn eigen notebook kan navolgen.
    """
    verdeling = [(1, f"{label} · {aantal} handen", False, TEKSTKLEUR) for label, aantal in c["bakjes"]]
    acties = [
        (1, f"{actie} · {aandeel} van alle beslissingen · gemiddeld {gem} chips, mediaan {med}",
         False, ACCENT if actie != "fold" else TEKSTKLEUR)
        for actie, aandeel, gem, med in c["acties"]
    ]
    uitslag = [
        (1, f"{plek}.  {naam} · {eind} chips · foldt {foldt}", False,
         ACCENT if plek == 1 else TEKSTKLEUR)
        for plek, naam, eind, foldt in c["uitslag"]
    ]
    return [
        (
            "Wat de samenvatting verbergt",
            [
                (0, 'df["winst"].describe()', True, ACCENT),
                (1, f"gemiddelde {c['gemiddelde']} · nulsom: wat de een wint, verliest de ander", False, TEKSTKLEUR),
                (1, f"mediaan {c['mediaan']} · in de meeste handen gebeurt er niets", False, TEKSTKLEUR),
                (1, f"standaarddeviatie {c['std']}", False, TEKSTKLEUR),
                (1, f"laagste {c['laagste']} · hoogste {c['hoogste']} — iemand verloor zijn hele stack in één hand", False, TEKSTKLEUR),
                (0, "Gemiddelde nul, mediaan nul. Maar in één hand ging er "
                    f"{c['hoogste'].lstrip('+')} om.", True, TITELKLEUR),
                (1, "Wat zeggen die drie getallen dan eigenlijk?", False, TEKSTKLEUR),
            ],
        ),
        (
            "En dat zie je in het histogram",
            [
                (0, 'df["winst"].hist(bins=40)', True, ACCENT),
            ] + verdeling + [
                (0, "Bijna alles zit in één bakje rond nul: weggelegd zonder in de blinds te zitten.", True, TEKSTKLEUR),
                (1, f"{c['bakjes'][-1][1]} handen van de {c['logregels']} bepalen het hele beeld —", False, TEKSTKLEUR),
                (1, "en die zie je in geen enkel samenvattend getal terug", False, GEDEMPT),
            ],
        ),
        (
            "Hetzelfde, getekend",
            [],
            HISTOGRAM,
        ),
        (
            "Categorisch, dan bivariaat",
            [
                (0, 'az = df[df["aan_zet"]]', True, ACCENT),
                (0, 'az["actie"].value_counts(normalize=True)', True, ACCENT),
            ] + acties + [
                (0, f"De klas foldt {c['acties'][0][1]} van alles. "
                    "En elke andere actie levert gemiddeld géld op.", True, TITELKLEUR),
                (1, "Let op aan_zet: zonder dat filter tel je handen mee waarin de bot nooit iets koos", False, GEDEMPT),
            ],
        ),
        (
            "De bot die niet nadenkt wint",
            [
                (0, 'df.groupby("bot_naam")["stack"].last()', True, ACCENT),
            ] + uitslag + [
                (0, "Kijkt niet naar zijn kaarten, rekent geen winkans uit, kent geen pot odds.", True, TEKSTKLEUR),
                (1, f"Hij wint van {c['bots'] - 1} bots waar uren aan is gewerkt, met {c['voorsprong']} chips voorsprong", False, TEKSTKLEUR),
                (1, f"En die ene die bijna won foldt {c['uitslag'][1][3]}, niet 99%", False, TEKSTKLEUR),
                (0, f"Correlatie fold% met eindstand: {c['correlatie']}", True, TITELKLEUR),
            ],
        ),
    ]


# (titel, [(niveau, tekst, vet, kleur), ...])
NIEUWE_DIAS = [
    (
        "Deze week in twee werkcolleges",
        [
            (0, "Werkcollege 4 — de stapeling", True, TITELKLEUR),
            (1, "standaardwaarde in een functie · dictionary als opzoektabel · filteren en groeperen", False, TEKSTKLEUR),
            (1, "de spelregels: vier straten, dus je bot beslist vier keer per hand", False, TEKSTKLEUR),
            (1, "handsterkte · winkans · pot odds — die laatste twee naast elkaar is een beslisregel", False, ACCENT),
            (0, "Werkcollege 5 — van bot naar data", True, TITELKLEUR),
            (1, "live testen tegen een klasgenoot · v2 naast v1 · de spelregels in je eigen log", False, TEKSTKLEUR),
            (1, "peer review · aftrap Case 2 · twee tabellen samenvoegen · van notebook naar Streamlit", False, TEKSTKLEUR),
            (0, "Het hoofdwerk zit in het huiswerk: reken op 4 tot 8 uur eigen botwerk.", True, TEKSTKLEUR),
        ],
    ),
    (
        "Wat je bot tot nu toe kon: alleen de openingshand",
        [
            (0, "In week 3 rekent je bot met twee kaarten en verder niets.", True, TEKSTKLEUR),
            (1, "schat_winkans([\"A\", \"K\"], tegenstanders=5) → één getal, vóór de flop", False, TEKSTKLEUR),
            (1, "Dat getal verandert de hele hand niet meer — ook niet als er drie schoppen vallen", False, TEKSTKLEUR),
            (0, "Waarom dat kon: winkansen preflop veranderen nooit.", True, TEKSTKLEUR),
            (1, "169 mogelijke starthanden, dus je rekent ze één keer uit en plakt de tabel in je bot", False, TEKSTKLEUR),
            (1, "Precies waar een dictionary voor bedoeld is: sleutel → waarde", False, TEKSTKLEUR),
            (0, "Wat je bot dus niet weet:", True, TEKSTKLEUR),
            (1, "of het bord bij zijn kaarten past, of iemand anders aan een flush werkt", False, GEDEMPT),
        ],
    ),
    (
        "Vanaf week 5: per straat opnieuw rekenen",
        [
            (0, "Je bot krijgt het bord erbij, en zijn eigen kaarten mét kleur.", True, TEKSTKLEUR),
            (1, "schat_winkans(hand_met_kleur, bord=bord, tegenstanders=3)", False, ACCENT),
            (1, "De ontbrekende kaarten worden om jouw bord heen gedeeld — geen willekeurig bord meer", False, TEKSTKLEUR),
            (0, "Kleur is hier niet optioneel. Zelfde rangen, bord met drie schoppen:", True, TEKSTKLEUR),
            (1, "S7 S8, allebei schoppen: 36,6% op de flop — en 94,1% op de river, met de flush", False, ACCENT),
            (1, "H7 C8, gemengde kleuren: 8,0% op de flop — en 0,0% op de river", False, GEDEMPT),
            (0, "En een opzoektabel werkt hier niet meer.", True, TEKSTKLEUR),
            (1, "Binnen de categorie \"één paar\" op de flop loopt de echte winkans van 8,5% tot 75,5%", False, TEKSTKLEUR),
            (1, "Een tabelwaarde van gemiddeld 33,8% zit dan in beide richtingen ver mis", False, GEDEMPT),
        ],
    ),
    (
        "Wat moest, en wat mocht — week 3",
        [
            (0, "VERPLICHT — zonder dit wordt je inzending afgekeurd", True, TITELKLEUR),
            (1, "kies_actie(hand, stack)   — die twee namen, exact zo gespeld", False, TEKSTKLEUR),
            (1, "je bot geeft één string terug: fold, call, raise, all_in of grote_raise", False, TEKSTKLEUR),
            (0, "OPTIONEEL — je krijgt ze alleen als je ze zelf opschrijft", True, ACCENT),
            (1, "ronde · pot · inzet_om_te_callen · tegenstander_acties_deze_hand", False, ACCENT),
            (1, "De engine kijkt naar je parameternamen. Verkeerd gespeld = je krijgt hem niet.", False, TEKSTKLEUR),
            (0, "Twee dingen die pas aangaan mét stack:", True, TEKSTKLEUR),
            (1, "all_in en grote_raise mogen dan pas: zonder je stack kun je dat niet afwegen", False, TEKSTKLEUR),
            (1, "en de cap van twee raises per straat gaat gelden", False, TEKSTKLEUR),
        ],
    ),
    *doorloopblad_dias(CIJFERS),
    (
        "Groepscase 2 — wat je oplevert",
        [
            (0, "Een Streamlit-dashboard over een onderwerp dat je zelf kiest.", True, TEKSTKLEUR),
            (1, "Gepubliceerd via GitHub op share.streamlit.io, te openen met een link", False, TEKSTKLEUR),
            (1, "De app haalt de data zelf op bij een openbare API — niet met de hand gedownload", False, TEKSTKLEUR),
            (1, "Minimaal één join: twee bronnen die je tot één tabel samenvoegt", False, ACCENT),
            (0, "Loopt over week 3 en week 4. Dat is kort.", True, TEKSTKLEUR),
            (1, "Donderdag 18:00 staat je onderwerp vast: welke vraag, welke twee bronnen,", False, TEKSTKLEUR),
            (1, "op welke kolom die aan elkaar passen, en wie in de groep wat doet", False, TEKSTKLEUR),
            (0, "Zoek nu al op of die twee bronnen écht een gemeenschappelijke kolom hebben.", True, TITELKLEUR),
            (1, "\"Den Haag\" en \"'s-Gravenhage\" passen niet op elkaar zonder werk", False, GEDEMPT),
        ],
    ),
    (
        "Waar je cijfer vandaan komt",
        [
            (0, "Drie criteria voor IDS — de data-kant", True, TITELKLEUR),
            (1, "Data verzameling · twee bronnen, plus de sleutel en de rijen vóór en ná de join", False, TEKSTKLEUR),
            (1, "Data verkenning · lege waarden, bereik, dubbele rijen — en wat je ermee deed", False, TEKSTKLEUR),
            (1, "Analyse · een conclusie die de data draagt, niet meer dan dat", False, TEKSTKLEUR),
            (0, "Vier criteria voor VA — de verhaalkant", True, TITELKLEUR),
            (1, "Opbouw en verhaallijn · Interactiviteit · Dashboardontwerp", False, TEKSTKLEUR),
            (1, "Vergelijken en annoteren · het verschil, het opgetelde verloop, of de waarde", False, TEKSTKLEUR),
            (1, "ten opzichte van het moment ervoor — diff, cumsum, shift", False, ACCENT),
            (0, "Vijf niveaus, van Ontbreekt (1) tot Uitstekend (9).", True, TEKSTKLEUR),
        ],
    ),
    (
        "Vijf voorwaarden — die gaan van je cijfer af",
        [
            (0, "Dit zijn geen criteria maar drempels. Beide cijfers, IDS en VA.", True, TEKSTKLEUR),
            (1, "App niet online, of een schone clone draait niet zonder handwerk", False, TEKSTKLEUR),
            (1, "     -1,0", False, TITELKLEUR),
            (1, "Presentatie langer dan 10 minuten, exclusief vragen", False, TEKSTKLEUR),
            (1, "     -1,0", False, TITELKLEUR),
            (1, "Geen slider, checkbox én dropdown, elk gekoppeld aan een tabel of grafiek", False, TEKSTKLEUR),
            (1, "     -0,5", False, TITELKLEUR),
            (0, "En twee zonder aftrek, maar niet vrijblijvend:", True, TEKSTKLEUR),
            (1, "Onderwerp op tijd gemeld · code van anderen met bron erbij, en uit te leggen", False, GEDEMPT),
        ],
    ),
    (
        "Dat heb je vanmiddag al gedaan",
        [
            (0, "De demo van zojuist was Case 2 in het klein:", True, TEKSTKLEUR),
            (1, "twee tabellen op bot_naam samengevoegd, rijen geteld vóór en ná", False, ACCENT),
            (1, "     → criterium Data verzameling", False, TEKSTKLEUR),
            (1, "928 lege waarden gevonden, en gezien wat ze met je percentage deden", False, ACCENT),
            (1, "     → criterium Data verkenning", False, TEKSTKLEUR),
            (1, "diff en cumsum over het verloop van een stack", False, ACCENT),
            (1, "     → criterium Vergelijken en annoteren", False, TEKSTKLEUR),
            (0, "Het verschil met de case: daar kiest niemand de dataset voor je,", True, TEKSTKLEUR),
            (1, "en staat er geen kolom aan_zet klaar om je fout te laten zien.", False, GEDEMPT),
        ],
    ),
]


# Het doorloopblad, maar dan in de notities van de dia waar het over gaat.
#
# Waarom hier en niet als dia: driekwart van het blad is tegen jou gericht en
# niet tegen de zaal ("dit is het gesprek van vandaag"). In de presentatorweergave
# staat het naast de dia, en Afdrukken > Notitiepagina's geeft je hetzelfde A4 terug.
#
# De sleutel is het dianummer in het samengestelde deck. 1 t/m 21 zijn het
# origineel, daarna volgen NIEUWE_DIAS in volgorde. Schuift het origineel, dan
# schuiven deze nummers mee -- vandaar dat de tekst begint met waar hij hoort.
NOTITIES = {
    4: """[EDA-recept] Dit recept is precies de volgorde van de demo straks:
describe -> univariaat -> bivariaat. Blok 1 is describe, blok 3 is bivariaat.
Zeg dat je het zo meteen op hun eigen toernooi doet, dan luisteren ze anders.""",

    5: """[Blok 1 - wat de samenvatting verbergt] Op het toernooi van deze week:
gemiddelde 0,0 - mediaan 0,0 - std 39 - laagste -1030 - hoogste +1750.

Het gemiddelde is exact nul en dat is geen toeval: poker is een nulsom, wat de
een wint verliest de ander. Dat is meteen je controle. Komt er geen nul uit je
eigen berekening, dan klopt je groepering niet.

Mediaan nul betekent: in de meeste handen gebeurt er niets. En toch ging er in
een van die handen 1750 chips om. Vier getallen, en geen van de vier vertelt dat.""",

    7: """[Blok 2 - de verdeling] Op hun data: 4838 van de 6750 handen vallen
tussen 0 en 20 chips. 1488 tussen -20 en -1. En dan de staarten: 53 handen tussen
-100 en -20, negen onder de -200, zeven boven de +200.

Die ene piek rond nul zijn handen die zijn weggelegd zonder in de blinds te zitten.
Het echte spel zit in de zeven handen rechts. Vraag aan de zaal: welk van de vier
getallen van de vorige dia had je dat verteld? Geen enkel.""",

    8: """[Central tendency] Hier maakt de keuze het verschil tussen twee conclusies,
en dat kun je op hun data laten zien. Gemiddelde winst per hand: 0. Mediaan: 0.
Allebei nul, allebei waar, en samen verbergen ze een hand van +1750.

Bij de bots ligt het andersom: de mediaan van de eindstand is 946, het gemiddelde
1000 (want nulsom). Dat verschil van 54 chips is de scheefheid - een paar bots
hebben veel, de meeste iets minder dan waarmee ze begonnen.""",

    9: """[np.random] Dit is precies wat schat_winkans() doet. Je kunt de winkans
van A-K tegen vijf tegenstanders niet uitrekenen met een formule; je deelt duizend
keer willekeurige kaarten en telt hoe vaak je wint. Een verdeling maken om een
getal te schatten dat je niet kunt afleiden - dat is Monte Carlo, en dat zit al
sinds werkcollege 4 in hun bot.""",

    16: """[Filteren] De twee filters uit de demo:

  handen[handen["bot_naam"] == "500959250"]      -- rijen op inhoud
  handen.loc[handen["aan_zet"], "actie"]         -- boolean mask

Die tweede is de belangrijkste regel van het college. aan_zet is een kolom vol
True/False; in .loc zetten houdt alleen de rijen waar hij True is. 928 van de 6750
logregels zijn handen waarin de bot nooit iets koos - hij zat in de blinds en de
hand was al voorbij.""",

    19: """[Nieuwe variabelen] De winst-kolom is hier het voorbeeld, en hij komt
niet uit het log maar reken je zelf uit:

  handen["winst"] = handen.groupby(["bot_naam","simulatie"])["stack"].diff()
                          .fillna(handen["stack"] - 1000)

Het log bewaart de stack NA elke hand, dus winst is het verschil met de hand
ervoor. Twee dingen die misgaan: groeperen zonder simulatie (dan trek je de
eerste hand van zitting 1 af van de laatste van zitting 0), en de NaN van de
eerste hand laten staan.

Controle: alle winst samen is precies 0.""",

    20: """[Groupby] Een-op-een met de vorige dia:

  gapminder.groupby('continent')['pop'].sum()
  handen.groupby('bot_naam')['winst'].sum()

Letterlijk dezelfde regel. En dan de valkuil, die je moet laten zien:

  handen.groupby('bot_naam')['stack'].sum()   ->  258.550 chips

Geen foutmelding, keurig getal, volslagen onzin. Een stack is een STAND, geen
stroom. Dat over 250 handen optellen is hetzelfde als de bevolking van Europa
over alle twaalf gapminder-jaren optellen. Voor een stand wil je .last().""",

    21: """[Opdracht] De opdracht is dit jaar niet gapminder maar hun eigen
toernooi: 03_demo_college_toernooi.ipynb. Dezelfde acht bewerkingen, hun eigen data.

Ze hebben hun token nodig. Wie dat kwijt is pakt toernooi_week3.json van
Brightspace. Reken op vijf minuten opstarten - de eerste API-aanroep wekt de server.

De drie TODO's onderaan zijn de kern: eindstand als tabel, fold% per bot, en
.corr() tussen die twee. Uitwerkingen staan in 03_demo_college_uitwerkingen.ipynb.""",
}

# De notities bij de nieuwe dia's, op titel in plaats van op nummer.
NOTITIES_NIEUW = {
    "Deze week in twee werkcolleges": """Kort houden - dit is de kaart, niet de reis.
Het enige dat ze moeten onthouden: winkans en pot odds naast elkaar is de
beslisregel, en dat is de hele week. De rest is gereedschap om die regel te maken.""",

    "Wat je bot tot nu toe kon: alleen de openingshand": """Dit is de grens van week 3,
en het is een bewuste grens. Preflop-winkansen veranderen nooit, dus 169 starthanden
kun je een keer uitrekenen en in een dictionary plakken. Daarom kon het.

Vraag die altijd komt: ziet mijn bot het bord? Nee. Twee kaarten, elke straat, de
hele hand lang. Dat is deze week zo en dat verandert in week 5.""",

    "Vanaf week 5: per straat opnieuw rekenen": """De kleur is hier het punt, niet de
techniek. Zelfde rangen, bord met drie schoppen: 36,6% tegen 8,0%. Op de river 94,1%
tegen 0,0%. Dezelfde kaarten qua waarde, een compleet andere hand.

En de opzoektabel houdt op te werken: binnen "een paar" op de flop loopt de echte
winkans van 8,5% tot 75,5%. Elke tabelwaarde zit in beide richtingen ver mis.""",

    "Wat moest, en wat mocht — week 3": """Loop de verplichte regel langzaam langs. De
engine kijkt naar je PARAMETERNAMEN; verkeerd gespeld betekent dat je die informatie
niet krijgt, zonder foutmelding. Dat is de stilste fout in het hele vak.""",

    "Wat de samenvatting verbergt": """[Blok 1] Vier getallen op tafel en dan stil zijn.

Het gemiddelde is exact nul en dat is geen toeval: poker is een nulsom, wat de een
wint verliest de ander. Daarmee is het meteen je controle -- komt er geen nul uit je
eigen berekening, dan klopt je groepering niet en is alles daarna onzin.

Mediaan nul betekent: in de meeste handen gebeurt er niets. En toch ging er in een
van die handen meer dan duizend chips om. Vraag het aan de zaal voordat je het zegt:
welk van deze vier getallen had je dat verteld?""",

    "En dat zie je in het histogram": """[Blok 2] De bakjes zijn met opzet ongelijk.
Rond nul zit bijna alles, dus daar wil je fijn verdelen; de staarten zijn zo dun dat
ze alleen als één bakje zichtbaar blijven.

Die piek rond nul zijn handen die zijn weggelegd zonder in de blinds te zitten: je
verliest niets en je wint niets. Het spel gebeurt in de handen aan de randen, en dat
zijn er een paar van de duizenden.""",

    "Hetzelfde, getekend": """De y-as is logaritmisch, en dat is geen truc maar de
enige manier om allebei te zien: de piek is duizenden handen hoog en de staart is
één hand. Lineair zie je één balk en verder wit.

Goede vraag aan de zaal: df["winst"].hist(bins=40) geeft precies dat lege plaatje.
Wie had gemerkt dat er iets ontbrak? De standaardinstelling van een grafiek is een
keuze die iemand anders voor je heeft gemaakt.""",

    "Categorisch, dan bivariaat": """[Blok 3 - het gesprek van vandaag] Laat ze de
tabel zelf lezen voordat je iets zegt.

De vraag is niet "waarom foldt de klas zoveel" maar "waarom levert elke andere actie
gemiddeld geld op, en doet niemand het". Antwoord: aan een tafel van folders wint de
big blind de small blind. Folden kost je bijna niets - en levert je ook niets op.

Let op bij het navolgen: filter op aan_zet, anders tel je handen mee waarin de bot
nooit iets koos en komt elk percentage te laag uit. Dat is dezelfde val als in de
demo van vanmiddag.""",

    "De bot die niet nadenkt wint": """[Blok 4 - hier eindig je] Laat de uitslag
even staan voordat je hem uitlegt.

Het gaat niet om "de domme bot wint". Het gaat om: jullie drempels staan zo hoog dat
niet meedoen bijna net zo goed werkt als meedoen. Kijk naar nummer twee - die foldt
ruim tachtig procent en niet negenennegentig, en dat is het verschil.

Over de correlatie: niet doorslaan. Een handvol bots draagt dat getal en een paar
tientallen punten is weinig. Dat onderscheid, zie ik een verband tegenover heb ik
iets aangetoond, is precies wat het criterium Analyse van Case 2 beoordeelt.

De vraag voor donderdag is niet "moet ik minder folden" maar "waar liggen mijn
drempels, en waarom daar".""",

    "Groepscase 2 — wat je oplevert": """De deadline is donderdag 18:00 en dat is geen
inlevermoment maar een BESLUIT: welke vraag, welke twee bronnen, op welke kolom die
aan elkaar passen, wie doet wat.

Het zinnetje over Den Haag en 's-Gravenhage is niet grappig bedoeld. Laat ze nu al
een keer kijken of hun twee bronnen echt een gemeenschappelijke kolom hebben met
dezelfde schrijfwijze.""",

    "Waar je cijfer vandaan komt": """Vergelijken en annoteren is het criterium waar
groepen punten laten liggen. Het vraagt diff, cumsum of shift - het verschil met het
moment ervoor, niet alleen de waarde. Ze hebben diff vanmiddag al gebruikt om de
winst-kolom te maken; zeg dat er hardop bij.""",

    "Vijf voorwaarden — die gaan van je cijfer af": """Deze dia is saai en bespaart je
in week 4 een half uur discussie. De aftrek gaat van BEIDE cijfers af, IDS en VA.

"Een schone clone draait zonder handmatige stappen" is de zwaarste: hun app moet het
doen op een computer die hun notebook nooit heeft gezien.""",

    "Dat heb je vanmiddag al gedaan": """Dit is de dia die de curriculum-audit vroeg.
Studenten leggen de koppeling tussen werkcollege en rubric zelf niet. Een zin - dit
is het criterium waarop je case wordt beoordeeld - is het verschil tussen een
oefening en een reden.""",
}


def zet_notitie(dia, tekst):
    """Zet het stuk doorloopblad onder de dia, in de notities."""
    if not tekst:
        return
    dia.notes_slide.notes_text_frame.text = tekst.strip()


def voeg_dia_toe(prs, titel, regels, nummer, plaatje=None):
    """
    Eén dia in de stijl van het deck: leeg canvas, twee tekstvakken, paginanummer.

    Met `plaatje` komt er een afbeelding onder de titel. Een dia met een plaat en
    zonder tekst geeft hem de hele hoogte; ontbreekt het bestand, dan blijft de
    dia gewoon leeg in plaats van dat het script omvalt.
    """
    dia = prs.slides.add_slide(prs.slide_layouts[0])

    kop = dia.shapes.add_textbox(Inches(2.17), Inches(1.03), Inches(9.0), Inches(1.25))
    p = kop.text_frame.paragraphs[0]
    p.text = titel
    p.font.name = "Arial"
    p.font.size = Pt(32)
    p.font.color.rgb = TITELKLEUR
    kop.text_frame.word_wrap = True

    vak = dia.shapes.add_textbox(Inches(2.17), Inches(2.28), Inches(9.6), Inches(4.42))
    tf = vak.text_frame
    tf.word_wrap = True
    for i, (niveau, tekst, vet, kleur) in enumerate(regels):
        alinea = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        alinea.text = tekst
        alinea.level = niveau
        alinea.font.name = "Arial"
        alinea.font.size = Pt(17 if niveau == 0 else 14)
        alinea.font.bold = vet
        alinea.font.color.rgb = kleur
        if niveau == 0 and i:
            alinea.space_before = Pt(13)

    if plaatje and os.path.exists(plaatje):
        breedte = 8.6 if not regels else 6.4
        boven = 2.10 if not regels else 4.00
        links = 2.17 + (9.6 - breedte) / 2
        dia.shapes.add_picture(plaatje, Inches(links), Inches(boven), width=Inches(breedte))
    elif plaatje:
        print(f"Let op: {os.path.basename(plaatje)} bestaat niet, dia '{titel}' blijft leeg.")

    nr = dia.shapes.add_textbox(Inches(10.69), Inches(6.70), Inches(0.69), Inches(0.40))
    pn = nr.text_frame.paragraphs[0]
    pn.text = str(nummer)
    pn.font.name = "Arial"
    pn.font.size = Pt(12)
    pn.font.color.rgb = GEDEMPT
    return dia


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bron = sys.argv[1]
    if not os.path.exists(bron):
        print(f"Bronbestand niet gevonden: {bron}")
        return 2
    if os.path.abspath(bron) == os.path.abspath(UITVOER):
        print("Bron en uitvoer zijn hetzelfde bestand. Dat doen we niet.")
        return 2

    prs = Presentation(bron)
    begin = len(prs.slides)
    for i, invoer in enumerate(NIEUWE_DIAS):
        titel, regels, plaatje = (invoer + (None,))[:3]
        dia = voeg_dia_toe(prs, titel, regels, begin + i + 1, plaatje)
        zet_notitie(dia, NOTITIES_NIEUW.get(titel))

    dias = list(prs.slides)
    ontbreekt = [n for n in NOTITIES if not 1 <= n <= len(dias)]
    if ontbreekt:
        print(f"Let op: geen dia {ontbreekt} -- die notities zijn niet geplaatst.")
    for nummer, tekst in NOTITIES.items():
        if 1 <= nummer <= len(dias):
            zet_notitie(dias[nummer - 1], tekst)

    os.makedirs(os.path.dirname(UITVOER), exist_ok=True)
    prs.save(UITVOER)
    aantal_notities = len(NOTITIES) + sum(1 for d in NIEUWE_DIAS if d[0] in NOTITIES_NIEUW)
    print(f"{begin} dia's uit het origineel + {len(NIEUWE_DIAS)} nieuwe -> {UITVOER}")
    print(f"{aantal_notities} dia's hebben het doorloopblad in hun notities staan.")
    print(f"Het origineel is niet aangeraakt: {bron}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
