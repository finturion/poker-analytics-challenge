"""
De winkansschatter, zoals de bots hem op de server kunnen aanroepen.

WAAROM DIT BESTAND BESTAAT
--------------------------
`schat_winkans` staat ook in notebooks/_hulpfuncties_week3.py, waar studenten
hem in hun notebook gebruiken. Maar render.yaml deployt met `rootDir: api`, dus
alleen deze map staat op de server -- een bot die `_hulpfuncties_week3`
importeert krijgt een ModuleNotFoundError, en `sys` staat op de verbodenlijst
dus hij kan er ook niet zelf naartoe wijzen.

Tot en met Week 3 was dat geen probleem: winkansen preflop veranderen niet, dus
studenten genereren een opzoektabel in hun notebook en plakken die in hun bot.
Vanaf Week 5 krijgt de bot het bord erbij, en dan werkt een tabel niet meer.
Gemeten op willekeurige flops met drie tegenstanders: binnen de categorie "een
paar" loopt de echte winkans van 8,5% tot 75,5%. Een tabelwaarde van gemiddeld
33,8% zit dan in beide richtingen ver mis. Dus moet de bot live kunnen rekenen,
en dus moet de functie hier staan.

Hij wordt in de naamruimte van de bot gezet (zie toernooi_runner._laad_kies_actie
en bot_validator._draai_in_apart_proces), zodat een student hem gewoon kan
aanroepen zonder te importeren.

TWEE KOPIEEN
------------
Deze en die in notebooks/_hulpfuncties_week3.py moeten hetzelfde antwoord
geven, anders rekent een student in zijn notebook iets anders uit dan zijn bot
in het toernooi. scripts/test_winkans_bord.py houdt ze tegen elkaar.
"""
import random
import re

from pypokerengine.engine.card import Card
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.utils.card_utils import gen_cards

_RANG_NAAR_GETAL = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13, "A": 14,
}
_KLEUREN = [Card.CLUB, Card.DIAMOND, Card.HEART, Card.SPADE]


def _volledig_deck():
    return [Card(kleur, rang) for kleur in _KLEUREN for rang in range(2, 15)]


def schat_winkans(hand, simulaties=1000, seed=None, tegenstanders=1, bord=None):
    """
    Monte Carlo-schatting van je winkans: hoeveel procent van de tijd wint
    `hand`, over `simulaties` uitgespeelde borden?

    hand: lijst met 2 kaartWAARDEN, zoals overal in de cursus (bv. ["A", "K"]).
    De kleur van je eigen kaarten maakt preflop voor de winkans niet uit en
    wordt willekeurig gekozen; PyPokerEngine's eigen hand-evaluatie (dus
    inclusief flush/straat) bepaalt per simulatie wie wint.

    MET EEN BORD ERBIJ (vanaf Week 5)
    ---------------------------------
    Geef `bord` mee zodra er kaarten op tafel liggen, dan rekent hij niet meer
    met een willekeurig bord maar met dat van jou -- de ontbrekende kaarten
    worden eromheen gedeeld:

        schat_winkans(["SA", "HA"], bord=["DA", "C7", "S2"], tegenstanders=3)

    Dan moet `hand` wél kleuren hebben, in dezelfde notatie als `bord` en als
    beschrijf_hand(): "SA" is schoppenaas, "CT" is klaveren tien. Zonder kleur
    kan niemand zien of jij aan een flush werkt, en dan is een winkans mét bord
    een slechtere schatting dan een zonder. Daarom weigert hij dat combinatie
    in plaats van stilletjes iets uit te rekenen wat niet klopt.

    TEGENSTANDERS IS HET BELANGRIJKSTE ARGUMENT
    -------------------------------------------
    Standaard rekent hij tegen ÉÉN tegenstander, en dat is bijna nooit de
    situatie waarin je bot zit. Aan een tafel van zes moet je van vijf mensen
    winnen, en dat is een heel andere vraag:

        schat_winkans(["A", "A"], tegenstanders=1)   ->  ongeveer 85%
        schat_winkans(["A", "A"], tegenstanders=5)   ->  ongeveer 50%
        schat_winkans(["7", "2"], tegenstanders=1)   ->  ongeveer 34%
        schat_winkans(["7", "2"], tegenstanders=5)   ->  ongeveer  9%

    Vergelijk je een kop-op-kop-winkans met pot odds aan een volle tafel, dan
    denk je systematisch dat je meer kans hebt dan waar is -- en dan zegt de
    rekensom "call" met 7-2 omdat 34% een prijs van 17% lijkt te verslaan. Dat
    is geen theoretisch probleem: een bot die precies dat doet werd in een
    testtoernooi de zwakste van zeven en brandde op 73% van de tafels af.

    Gebruik dus het aantal tegenstanders dat er écht is. In het toernooi zit je
    aan een tafel van maximaal zes, dus `tegenstanders=5` als iedereen nog
    meedoet en minder zodra er gefold is.

    Gelijkspel telt als een halve overwinning, ook als je met meer dan één
    tegenstander gelijk eindigt -- de pot wordt dan immers gedeeld.

    Duurt bij de standaard 1000 simulaties en één tegenstander ongeveer 30-50
    milliseconden -- ruim binnen de 2 seconden die het toernooi je per
    beslissing geeft (BESLISSING_TIMEOUT_SECONDS in poker_adapter.py). Met vijf
    tegenstanders is het ongeveer twee keer zo langzaam.
    """
    if tegenstanders < 1:
        raise ValueError("tegenstanders moet minstens 1 zijn")

    bord = list(bord or [])
    if len(bord) > 5:
        raise ValueError(f"Een bord heeft hoogstens 5 kaarten, je gaf er {len(bord)}.")

    heeft_kleur = all(len(str(k)) >= 2 and str(k)[0] in "SHDC" for k in hand)
    if bord and not heeft_kleur:
        raise ValueError(
            "Met een bord erbij moet `hand` kleuren hebben, net als `bord`: "
            'bv. schat_winkans(["SA", "HA"], bord=["DA", "C7", "S2"]). '
            "Zonder kleur kun je geen flush herkennen, en dan is de schatting "
            "slechter dan die zonder bord."
        )

    vast_bord = gen_cards(bord) if bord else []
    vaste_hole = gen_cards(hand) if heeft_kleur else None
    if vaste_hole is not None:
        dubbel = {str(k) for k in vaste_hole} & {str(k) for k in vast_bord}
        if dubbel:
            raise ValueError(f"Deze kaart ligt al op tafel: {', '.join(sorted(dubbel))}")

    rng = random.Random(seed)
    overwinningen = 0.0
    for _ in range(simulaties):
        deck = _volledig_deck()
        rng.shuffle(deck)

        if vaste_hole is not None:
            # Kleuren staan vast: neem precies deze kaarten uit het deck.
            bekend = {str(k) for k in vaste_hole} | {str(k) for k in vast_bord}
            eigen_hole = list(vaste_hole)
            gebruikt = [k for k in deck if str(k) in bekend]
        else:
            gebruikt, eigen_hole = [], []
            for rang in hand:
                kandidaten = [k for k in deck
                              if k.rank == _RANG_NAAR_GETAL[rang] and k not in gebruikt]
                gekozen = rng.choice(kandidaten)
                eigen_hole.append(gekozen)
                gebruikt.append(gekozen)

        resterend = [k for k in deck if k not in gebruikt]
        rng.shuffle(resterend)
        handen_tegen = [resterend[2 * i:2 * i + 2] for i in range(tegenstanders)]
        # Het bekende deel van het bord staat vast; de rest wordt eromheen gedeeld.
        nog_te_delen = 5 - len(vast_bord)
        volledig_bord = list(vast_bord) + resterend[
            2 * tegenstanders:2 * tegenstanders + nog_te_delen]

        mijn_sterkte = HandEvaluator.eval_hand(eigen_hole, volledig_bord)
        sterktes_tegen = [HandEvaluator.eval_hand(h, volledig_bord) for h in handen_tegen]
        beste_tegen = max(sterktes_tegen)

        if mijn_sterkte > beste_tegen:
            overwinningen += 1
        elif mijn_sterkte == beste_tegen:
            overwinningen += 0.5

    return round(100 * overwinningen / simulaties, 1)
