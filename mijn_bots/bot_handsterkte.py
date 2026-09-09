# --- Bot "Handsterkte": alleen je eigen twee kaarten beslissen ---------------
#
# HET IDEE: één getal erin, één actie eruit. Deze bot kijkt naar niets anders
# dan de winkans van zijn starthand en legt die op een vaste ladder. Geen pot,
# geen inzet, geen tegenstanders, geen toeval: dezelfde hand geeft altijd
# dezelfde actie. Dat maakt hem de meetlat voor de andere drie -- alles wat zij
# extra doen, doen ze bovenop dit.
#
# Wat hij bewust NIET doet: bluffen. `bluf_kans` staat alleen in de signatuur
# omdat de week 5-validator die altijd meegeeft. Een bluf is een uitspraak over
# je tegenstander, en die kent deze bot niet. Zijn spel is daardoor volledig af
# te lezen uit de kolom `hand` in het hand-log, en dat is precies de bedoeling.
#
# Eén ding dat geen kaart is, gebruikt hij wel: onder KORTE_STACK is er niets
# meer te manoeuvreren, dus dan is het alles of niets.

# De knoppen. Winkans is het percentage uit WINKANS hieronder.
CALL_GRENS = 52.0          # hieronder wegleggen
RAISE_GRENS = 62.0         # hierboven zelf verhogen
KORTE_STACK = 150          # minder chips dan dit: geen manoeuvreerruimte meer
ALL_IN_GRENS_KORT = 55.0   # met een korte stack: hierboven alles inzetten
ONBEKENDE_HAND = 40.0      # vangnet als een hand niet in de tabel staat

# Vier archetypes schuiven de hele ladder op. Positief = strenger.
STRATEGIE_SCHUIF = {"tight": 6.0, "balanced": 0.0, "aggressive": -3.0, "loose": -6.0}

# Winkans preflop tegen één willekeurige tegenstander, gemeten met
# schat_winkans() uit _hulpfuncties_week3.py (30.000 simulaties per hand).
# Staat hier als vaste tabel omdat _hulpfuncties_week3 op de server niet
# bestaat -- een bot die dat importeert wordt afgekeurd.
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
    """['K', 'A'] en ['A', 'K'] geven dezelfde sleutel, dus de volgorde maakt niet uit."""
    return "".join(sorted(hand, reverse=True))


def kies_actie(hand, stack, strategie, bluf_kans):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    schuif = STRATEGIE_SCHUIF.get(strategie, 0.0)

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT + schuif else "fold"

    if winkans >= RAISE_GRENS + schuif:
        return "raise"
    if winkans >= CALL_GRENS + schuif:
        return "call"
    return "fold"
