# --- Bot v3: v2 + strategie, bluffen, en kijken wat de tafel deed ---
import random

WINKANS = {
    "AA": 85.7, "KK": 82.8, "QQ": 79.9, "JJ": 77.5,
    "KA": 65.7, "QA": 65.4, "QK": 63.4, "QJ": 59.6, "910": 53.8, "72": 34.6,
}
MARGE = {
    "tight":      {"preflop": 10, "flop": 12, "turn": 15, "river": 20},
    "loose":      {"preflop": -5, "flop": 0,  "turn": 3,  "river": 5},
    "balanced":   {"preflop": 0,  "flop": 5,  "turn": 8,  "river": 10},
    "aggressive": {"preflop": -3, "flop": 2,  "turn": 4,  "river": 6},
}
RAISE_GRENS = {"tight": 75, "loose": 60, "balanced": 68, "aggressive": 55}


def hand_sleutel(hand):
    return "".join(sorted(hand, reverse=True))


def iemand_heeft_geraised(acties):
    """acties is een lijst met dicts: {'bot_naam': ..., 'actie': ..., 'bedrag': ...}."""
    for actie in acties or []:
        if actie.get("actie") == "raise":
            return True
    return False


def kies_actie(hand, stack, strategie, bluf_kans, ronde="preflop", pot=0,
               inzet_om_te_callen=0, tegenstander_acties_deze_hand=None):
    winkans = WINKANS.get(hand_sleutel(hand), 40)
    marge = MARGE.get(strategie, MARGE["balanced"]).get(ronde, 10)
    raise_grens = RAISE_GRENS.get(strategie, 68)
    tafel_toonde_kracht = iemand_heeft_geraised(tegenstander_acties_deze_hand)

    if stack < 150:
        return "all_in" if winkans >= 60 else "fold"

    # bluffen: alleen als niemand al kracht heeft getoond, anders is het weggegooid geld
    if not tafel_toonde_kracht and winkans < 45 and random.random() < bluf_kans:
        return "raise"

    if inzet_om_te_callen == 0:
        return "raise" if winkans >= raise_grens else "call"

    vereiste_winkans = inzet_om_te_callen / (pot + inzet_om_te_callen) * 100
    if tafel_toonde_kracht:
        marge += 5   # iemand heeft geraised: wees strenger
    if winkans < vereiste_winkans + marge:
        return "fold"
    return "raise" if winkans >= raise_grens else "call"
