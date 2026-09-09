# --- Bot "Tafellezer": wat de tafel deed weegt zwaarder dan wat jij hebt -----
#
# HET IDEE: dezelfde hand is niet dezelfde situatie. Deze bot kijkt eerst naar
# `tegenstander_acties_deze_hand` en pas daarna naar zijn kaarten. Iemand die
# net verhoogde heeft meestal iets, en dan gaat zelfs A-K weg. Een tafel die
# alleen maar meegaat heeft niets, en dan valt hij aan -- desnoods met troep,
# want tegen zwakte werkt een bluf. Zijn handsterkte gebruikt hij daarom grof:
# de TAFEL bepaalt welke grens geldt, de HAND alleen of je erboven zit.
#
# TWEE VALKUILEN IN DIT VELD, uit poker_adapter.py nagelezen:
#
# 1. `tegenstander_acties_deze_hand` loopt over ALLE straten van deze hand; hij
#    wordt niet per straat leeggemaakt. Wie alleen op "is er geraised?" test,
#    ziet op de river nog de raise van preflop en foldt vanaf de flop bijna
#    alles. Daarom kijkt deze bot ook naar de LAATSTE actie: dat is de druk van
#    nu, de rest is geschiedenis.
#
# 2. Bij zijn eerste beslissing van een hand is de lijst LEEG. "Niemand raiste"
#    is dan geen bewijs van zwakte maar afwezigheid van informatie, en dat is
#    een derde situatie met eigen grenzen -- niet dezelfde als een passieve
#    tafel, anders bluft hij elke hand blind vanuit early position.

import random

# De knoppen: per tafelbeeld een call- en een raise-grens in winkans-procenten.
GEEN_INFORMATIE = {"call": 52.0, "raise": 64.0}  # eerste beslissing, niemand handelde nog
PASSIEVE_TAFEL = {"call": 44.0, "raise": 53.0}   # wel gehandeld, geen enkele raise: aanvallen
BEDAARD = {"call": 54.0, "raise": 66.0}          # er wás een raise, maar de laatste actie was mee
NA_EEN_RAISE = {"call": 60.0, "raise": 72.0}     # iemand verhoogde net
NA_MEER_RAISES = {"call": 72.0, "raise": 81.0}   # er is al twee keer verhoogd: iemand meent het

MULTIWAY_STRAF = 3.0       # per extra tegenstander die meedeed: alle grenzen omhoog
KORTE_STACK = 150
ALL_IN_GRENS_KORT = 55.0
ONBEKENDE_HAND = 40.0

# Vier archetypes schuiven alle grenzen op. Positief = strenger.
STRATEGIE_SCHUIF = {"tight": 5.0, "balanced": 0.0, "aggressive": -4.0, "loose": -7.0}

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


def lees_tafel(acties):
    """
    Vat samen wat de tegenstanders deze hand deden.

    Geeft terug: (aantal raises, aantal tegenstanders dat geld inlegde,
    of de laatste actie een raise was). `or []` is het vangnet: bij de eerste
    beslissing van een hand is de lijst None of leeg.
    """
    raises = 0
    meedoeners = []
    for actie in acties or []:
        soort = actie.get("actie", "")
        if soort == "raise":
            raises += 1
        if soort in ("call", "raise") and actie.get("bot_naam") not in meedoeners:
            meedoeners.append(actie.get("bot_naam"))
    laatste_was_raise = bool(acties) and acties[-1].get("actie") == "raise"
    return raises, len(meedoeners), laatste_was_raise


def kies_actie(hand, stack, strategie, bluf_kans, tegenstander_acties_deze_hand=None):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    raises, meedoeners, laatste_was_raise = lees_tafel(tegenstander_acties_deze_hand)

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT else "fold"

    tafel_toonde_zwakte = bool(tegenstander_acties_deze_hand) and raises == 0

    if laatste_was_raise:
        grenzen = NA_MEER_RAISES if raises >= 2 else NA_EEN_RAISE
    elif not tegenstander_acties_deze_hand:
        grenzen = GEEN_INFORMATIE
    elif tafel_toonde_zwakte:
        grenzen = PASSIEVE_TAFEL
    else:
        grenzen = BEDAARD

    schuif = (STRATEGIE_SCHUIF.get(strategie, 0.0)
              + MULTIWAY_STRAF * max(0, meedoeners - 1))

    if winkans >= grenzen["raise"] + schuif:
        return "raise"
    if winkans >= grenzen["call"] + schuif:
        return "call"
    if tafel_toonde_zwakte and random.random() < bluf_kans:
        return "raise"   # niemand liet iets zien: dit is het moment om te stelen
    return "fold"
