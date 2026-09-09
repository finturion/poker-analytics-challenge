"""
Hulpfuncties specifiek voor Week 3 (Werkcollege 4 en 5).

Los van _hulpfuncties.py, want studenten hebben dat bestand al gedownload
voordat dit erbij kwam -- een update daarvan zou hen niet bereiken.

Bevat:
- speel_voorbeeldhand() (Werkcollege 4, Deel 2): laat PyPokerEngine echt één
  hand spelen, zodat studenten het spelverloop zien zonder zelf een
  PyPokerEngine-speler-klasse te hoeven lezen of schrijven.
- beschrijf_hand() / vergelijk_handen() (Werkcollege 5): handsterkte van een
  showdown aflezen en twee handen tegen elkaar afwegen.
- schat_winkans() (Werkcollege 5): Monte Carlo-schatting van hoe vaak een hand
  wint tegen een willekeurige tegenstander, met PyPokerEngine's eigen
  hand-evaluatie (dus inclusief kleur/flush/straat, ook al werkt de rest van
  de cursus met kaartwaarden zonder kleur).
"""
import random

from pypokerengine.api.game import setup_config, start_poker
from pypokerengine.engine.card import Card
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards

# PyPokerEngine's eigen verbose-logging toont community cards en acties, maar
# NOOIT hole cards (terecht voor echte spelers, die mogen elkaars kaarten niet
# zien) en ook geen handsterkte bij de showdown. Voor de demo willen we juist
# alles laten zien, dus printen we dat zelf erbij.
_HANDSTERKTE_NL = {
    "HIGHCARD": "hoge kaart",
    "ONEPAIR": "één paar",
    "TWOPAIR": "twee paar",
    "THREECARD": "three of a kind",
    "STRAIGHT": "straat",
    "FLASH": "flush",
    "FULLHOUSE": "full house",
    "FOURCARD": "four of a kind",
    "STRAIGHTFLASH": "straight flush",
}


class _DemoBot(BasePokerPlayer):
    """Sterk vereenvoudigde speler, puur om het spelverloop te laten zien -- niet hoe je straks je eigen kies_actie schrijft."""

    def __init__(self, naam, altijd):
        self.naam = naam
        self.altijd = altijd

    def declare_action(self, valid_actions, hole_card, round_state):
        toegestaan = {a["action"]: a for a in valid_actions}
        actie = self.altijd if self.altijd in toegestaan else "call"
        bedrag = toegestaan[actie]["amount"]
        if isinstance(bedrag, dict):
            bedrag = bedrag["min"]
        return actie, bedrag

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        print(f"{self.naam} krijgt: {hole_card}")

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, new_action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        eigen_hand = next((info for info in hand_info if info["uuid"] == self.uuid), None)
        if eigen_hand:
            sterkte = eigen_hand["hand"]["hand"]["strength"]
            print(f"{self.naam} had: {_HANDSTERKTE_NL.get(sterkte, sterkte)}")


def speel_voorbeeldhand():
    """
    Laat PyPokerEngine één echte hand spelen tussen twee simpele demo-bots
    (niet je eigen bot). Print ieders hole cards, per straat de community
    cards en elke actie, en aan het einde ieders handsterkte en de
    showdown-uitslag.
    """
    config = setup_config(max_round=1, initial_stack=1000, small_blind_amount=10)
    config.register_player(name="Tight", algorithm=_DemoBot("Tight", "call"))
    config.register_player(name="Aggressief", algorithm=_DemoBot("Aggressief", "raise"))
    return start_poker(config, verbose=1)


_RANG_NAAR_GETAL = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 11, "Q": 12, "K": 13, "A": 14,
}
_KLEUREN = [Card.CLUB, Card.DIAMOND, Card.HEART, Card.SPADE]


def _volledig_deck():
    return [Card(kleur, rang) for kleur in _KLEUREN for rang in range(2, 15)]


def schat_winkans(hand, simulaties=1000, seed=None, tegenstanders=1):
    """
    Monte Carlo-schatting van je winkans preflop: hoeveel procent van de tijd
    wint `hand`, over `simulaties` volledig uitgespeelde (willekeurige) borden?

    hand: lijst met 2 kaartWAARDEN, zoals overal in de cursus (bv. ["A", "K"]).
    De kleur van je eigen kaarten maakt voor de winkans niet uit en wordt
    willekeurig gekozen; PyPokerEngine's eigen hand-evaluatie (dus inclusief
    flush/straat) bepaalt per simulatie wie wint.

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

    rng = random.Random(seed)
    overwinningen = 0.0
    for _ in range(simulaties):
        deck = _volledig_deck()
        rng.shuffle(deck)

        gebruikt = []
        eigen_hole = []
        for rang in hand:
            kandidaten = [k for k in deck if k.rank == _RANG_NAAR_GETAL[rang] and k not in gebruikt]
            gekozen = rng.choice(kandidaten)
            eigen_hole.append(gekozen)
            gebruikt.append(gekozen)

        resterend = [k for k in deck if k not in gebruikt]
        rng.shuffle(resterend)
        handen_tegen = [resterend[2 * i:2 * i + 2] for i in range(tegenstanders)]
        bord = resterend[2 * tegenstanders:2 * tegenstanders + 5]

        mijn_sterkte = HandEvaluator.eval_hand(eigen_hole, bord)
        sterktes_tegen = [HandEvaluator.eval_hand(h, bord) for h in handen_tegen]
        beste_tegen = max(sterktes_tegen)

        if mijn_sterkte > beste_tegen:
            overwinningen += 1
        elif mijn_sterkte == beste_tegen:
            overwinningen += 0.5

    return round(100 * overwinningen / simulaties, 1)


# --- Werkcollege 5, Deel 3: handsterkte leren lezen -------------------------
# Deze twee gebruiken kaarten MET kleur, in dezelfde notatie als de demo van
# Werkcollege 4: "HA" = Hartenaas, "SK" = Schoppenheer, "D7" = Ruiten 7,
# "CT" = Klaveren 10. Kleur is hier wel nodig: zonder kleur kun je geen flush
# herkennen.
def beschrijf_hand(hole, community):
    """
    Welke handsoort leveren deze 2 hole cards + community cards samen op?

    beschrijf_hand(["HA", "SA"], ["DA", "C7", "S2"]) -> 'three of a kind'
    """
    info = HandEvaluator.gen_hand_rank_info(gen_cards(hole), gen_cards(community))
    sterkte = info["hand"]["strength"]
    return _HANDSTERKTE_NL.get(sterkte, sterkte)


def vergelijk_handen(hole_a, hole_b, community):
    """
    Wie wint deze showdown? Retourneert "A", "B" of "gelijkspel".

    Vergelijkt met exact dezelfde evaluatie als het echte toernooi, dus
    inclusief kickers: twee spelers met "één paar" kunnen alsnog verschillen.
    """
    bord = gen_cards(community)
    sterkte_a = HandEvaluator.eval_hand(gen_cards(hole_a), bord)
    sterkte_b = HandEvaluator.eval_hand(gen_cards(hole_b), bord)
    if sterkte_a > sterkte_b:
        return "A"
    if sterkte_b > sterkte_a:
        return "B"
    return "gelijkspel"
