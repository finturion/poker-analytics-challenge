# --- Bot "Inzetgrootte": niet OF je inzet, maar HOEVEEL ---------------------
#
# HET IDEE: de andere drie bots kiezen tussen meedoen en wegleggen. Deze kiest
# tussen drie BEDRAGEN: "raise" is het wettelijke minimum (mediaan 40 chips),
# "grote_raise" zet 200 in (tien big blinds), "all_in" alles. Hij speelt
# gepolariseerd -- groot met zijn beste handen EN met zijn bluffs, klein met de
# middenmoot. Wie zijn inzetgrootte probeert te lezen krijgt dus altijd twee
# antwoorden: de nuts, of niets.
#
# De tweede knop is stackdiepte. 200 chips uit een stack van 1800 is een prikje,
# uit een stack van 500 is het een derde van je toernooi. Boven
# GROTE_RAISE_MAX_DEEL van zijn stack valt er niets meer te doseren: dan ruilt
# hij de grote raise in voor het minimum, en gaat de topklasse in één keer
# all-in.
#
# Uit poker_adapter.py: "grote_raise" werkt alleen omdat `strategie` in de
# signatuur staat, en "all_in" alleen omdat `stack` erin staat -- dat zijn de
# gates. Ook goed om te weten: maximaal 2 raises per straat, en een grote raise
# telt daarvoor even zwaar als een kleine. Groot inzetten kost dus een van je
# twee kogels.

import random

# De knoppen: grenzen in winkans-procenten, bedragen in chips.
ALL_IN_GRENS = 79.0        # hierboven: de absolute topklasse
GROOT_GRENS = 65.0         # hierboven: groot inzetten
KLEIN_GRENS = 54.0         # hierboven: klein inzetten of goedkoop meegaan
MEEDOEN_GRENS = 46.0       # hierboven: gratis meekijken, maar niets betalen

GROTE_RAISE_CHIPS = 200    # wat de engine van "grote_raise" maakt
GROTE_RAISE_MAX_DEEL = 0.4  # past 200 niet binnen dit deel van je stack, dan valt er
                            # niets meer te doseren: topklasse gaat all-in, de rest
                            # zet het minimum in
GROTE_INZET_GRENS = 100    # een middenhand betaalt nooit meer dan dit
BLUF_POT_MIN = 60          # onder deze pot is stelen de moeite niet waard
KORTE_STACK = 150
ALL_IN_GRENS_KORT = 55.0
ONBEKENDE_HAND = 40.0

# Vier archetypes schuiven alle grenzen op. Positief = strenger.
STRATEGIE_SCHUIF = {"tight": 5.0, "balanced": 0.0, "aggressive": -4.0, "loose": -6.0}

# Winkans preflop tegen één willekeurige tegenstander, gemeten met
# schat_winkans() uit _hulpfuncties_week3.py (30.000 simulaties per hand).
WINKANS = {
    "AA": 85.3, "KA": 65.8, "QA": 65.2, "JA": 64.7, "A10": 63.6, "A9": 61.8, "A8": 60.5, "A7": 59.9, "A6": 59.2, "A5": 57.3, "A4": 56.2, "A3": 54.4, "A2": 53.4,
    "KK": 82.7, "QK": 62.7, "KJ": 61.7, "K10": 60.9, "K9": 59.0, "K8": 57.4, "K7": 56.5, "K6": 56.0, "K5": 54.1, "K4": 52.8, "K3": 51.1, "K2": 50.0,
    "QQ": 80.1, "QJ": 60.0, "Q10": 58.9, "Q9": 56.8, "Q8": 54.9, "Q7": 53.6, "Q6": 52.3, "Q5": 51.1, "Q4": 49.8, "Q3": 48.4, "Q2": 46.8,
    "JJ": 77.6, "J10": 56.4, "J9": 54.6, "J8": 52.6, "J7": 51.0, "J6": 49.3, "J5": 47.9, "J4": 46.9, "J3": 45.3, "J2": 43.9,
    "1010": 75.0, "910": 53.0, "810": 51.0, "710": 49.8, "610": 47.3, "510": 45.4, "410": 44.1, "310": 42.3, "210": 41.3,
    "99": 71.7, "98": 49.2, "97": 48.1, "96": 45.8, "95": 43.3, "94": 41.0, "93": 39.7, "92": 38.3,
    "88": 69.0, "87": 46.1, "86": 44.4, "85": 42.3, "84": 39.8, "83": 37.4, "82": 36.2,
    "77": 66.4, "76": 43.5, "75": 41.5, "74": 38.8, "73": 36.6, "72": 34.2,
    "66": 63.1, "65": 40.8, "64": 38.8, "63": 36.3, "62": 33.7,
    "55": 59.4, "54": 36.5, "53": 34.3, "52": 31.8,
    "44": 56.5, "43": 32.5, "42": 30.3,
    "33": 52.5, "32": 28.4,
    "22": 48.9,
}


def hand_sleutel(hand):
    return "".join(sorted(hand, reverse=True))


def past_de_grote_raise(stack):
    """Is 200 chips nog een inzet, of al bijna je hele stack?"""
    return GROTE_RAISE_CHIPS <= GROTE_RAISE_MAX_DEEL * stack


def kies_actie(hand, stack, strategie, bluf_kans, pot=0, inzet_om_te_callen=0):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    # bluf_kans kan None zijn: een inzending zonder bluf_kans (week 3) krijgt hem
    # toch aangeboden zodra hij in je handtekening staat. Zonder deze regel crasht
    # de vergelijking hieronder en foldt de engine je stil elke hand.
    bluf_kans = bluf_kans or 0.0
    pot = pot or 0
    inzet = inzet_om_te_callen or 0
    schuif = STRATEGIE_SCHUIF.get(strategie, 0.0)

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT else "fold"

    # Topklasse: zo groot als deze stack toelaat.
    if winkans >= ALL_IN_GRENS + schuif:
        return "grote_raise" if past_de_grote_raise(stack) else "all_in"

    # Sterk: groot inzetten, tenzij 200 chips te veel van deze stack is.
    if winkans >= GROOT_GRENS + schuif:
        return "grote_raise" if past_de_grote_raise(stack) else "raise"

    # Middenmoot: klein houden. Zelf het minimum inzetten als het gratis is,
    # en nooit een grote inzet van een tegenstander betalen.
    if winkans >= KLEIN_GRENS + schuif:
        if inzet == 0:
            return "raise"
        return "call" if inzet <= GROTE_INZET_GRENS else "fold"

    # Zwak maar niet hopeloos: gratis meekijken mag, betalen niet.
    if winkans >= MEEDOEN_GRENS + schuif:
        return "check" if inzet == 0 else "fold"

    # De onderkant. Bluffen met precies dezelfde inzet als de topklasse -- dat
    # is het hele punt van polariseren -- maar alleen als de pot het waard is
    # en niemand al een grote inzet heeft neergelegd.
    if pot >= BLUF_POT_MIN and inzet <= GROTE_INZET_GRENS and random.random() < bluf_kans:
        return "grote_raise" if past_de_grote_raise(stack) else "raise"
    return "check" if inzet == 0 else "fold"
