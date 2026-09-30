# --- Bot "Pot-odds": de prijs beslist, niet de hand -------------------------
#
# HET IDEE: elke call is een weddenschap met een prijs. Wat je moet bijleggen,
# gedeeld door wat er dan in de pot zit, is de winkans die je MINIMAAL nodig
# hebt om break-even te spelen: 20 bijleggen in een pot van 80 vraagt 20%.
# Deze bot rekent die prijs bij elke beslissing uit en vergelijkt hem met de
# winkans van zijn hand. Daarom doet hij mee met een matige hand als het bijna
# niets kost, en gooit hij een goede hand weg als iemand te veel vraagt --
# precies omgekeerd aan bot_handsterkte, die de prijs helemaal niet ziet.
#
# De MARGE is de correctie op de enige zwakte van de tabel: die getallen gaan
# over je STARTHAND en zeggen niets over wat het bord ermee deed. Hoe later de
# straat, hoe meer buffer hij boven de rekenkundige prijs eist.
#
# Zelf verhogen doet hij ook op prijs: niet "mijn hand is goed", maar "mijn
# winkans zit RAISE_OVERSCHOT punten boven wat deze pot me vraagt".

import random

# De knoppen.
MARGE_PER_RONDE = {"preflop": 6.0, "flop": 9.0, "turn": 13.0, "river": 18.0}
STRATEGIE_MARGE = {"tight": 6.0, "balanced": 0.0, "aggressive": -3.0, "loose": -6.0}
RAISE_OVERSCHOT = 15.0     # zoveel punten boven de vereiste winkans -> zelf verhogen
FAVORIET_GRENS = 50.0      # onder 50% ben je geen favoriet tegen een willekeurige
                           # hand. Dan verhoog je niet, hoe goedkoop de call ook is:
                           # een goedkope call is een goede call, geen goede raise.
GRATIS_RAISE_GRENS = 58.0  # niets bijleggen: er is geen prijs, dus een vaste grens
BLUF_POT_MIN = 120         # een pot moet iets waard zijn voordat stelen loont
KORTE_STACK = 150
ALL_IN_GRENS_KORT = 55.0
ONBEKENDE_HAND = 40.0
ONBEKENDE_RONDE_MARGE = 10.0

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


def bereken_pot_odds(pot, inzet_om_te_callen):
    """
    De winkans die je minimaal nodig hebt om deze call break-even te maken,
    in procenten. Zonder inzet is er geen prijs, dan is dit 0.
    """
    if inzet_om_te_callen <= 0:
        return 0.0
    return inzet_om_te_callen / (pot + inzet_om_te_callen) * 100


def kies_actie(hand, stack, strategie, bluf_kans, ronde="preflop", pot=0,
               inzet_om_te_callen=0):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    # bluf_kans kan None zijn: een inzending zonder bluf_kans (week 3) krijgt hem
    # toch aangeboden zodra hij in je handtekening staat. Zonder deze regel crasht
    # de vergelijking hieronder en foldt de engine je stil elke hand.
    bluf_kans = bluf_kans or 0.0
    pot = pot or 0
    inzet = inzet_om_te_callen or 0
    marge = (MARGE_PER_RONDE.get(ronde, ONBEKENDE_RONDE_MARGE)
             + STRATEGIE_MARGE.get(strategie, 0.0))

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT else "fold"

    if inzet == 0:
        # Gratis meedoen: er valt geen prijs te berekenen, dus nooit folden.
        return "raise" if winkans >= GRATIS_RAISE_GRENS else "check"

    vereiste_winkans = bereken_pot_odds(pot, inzet)

    if winkans < vereiste_winkans + marge:
        # Te duur. Alleen als de pot groot genoeg is om te stelen, is een
        # bluf-raise nog beter dan wegleggen.
        if pot >= BLUF_POT_MIN and random.random() < bluf_kans:
            return "raise"
        return "fold"

    if winkans >= FAVORIET_GRENS and winkans >= vereiste_winkans + marge + RAISE_OVERSCHOT:
        return "raise"
    return "call"
