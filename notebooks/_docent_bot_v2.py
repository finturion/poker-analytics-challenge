# --- Bot v2: opzoektabel + pot odds, met een marge die per straat strenger wordt ---
WINKANS = {
    "AA": 85.7, "KK": 82.8, "QQ": 79.9, "JJ": 77.5,
    "KA": 65.7, "QA": 65.4, "QK": 63.4, "QJ": 59.6, "910": 53.8, "72": 34.6,
}
MARGE_PER_RONDE = {"preflop": 0, "flop": 5, "turn": 10, "river": 15}


def hand_sleutel(hand):
    """['K', 'A'] en ['A', 'K'] geven dezelfde sleutel, dus de volgorde maakt niet uit."""
    return "".join(sorted(hand, reverse=True))


def kies_actie(hand, stack, ronde="preflop", pot=0, inzet_om_te_callen=0):
    winkans = WINKANS.get(hand_sleutel(hand), 40)
    marge = MARGE_PER_RONDE.get(ronde, 10)

    if stack < 150:
        return "all_in" if winkans >= 60 else "fold"

    if inzet_om_te_callen == 0:
        return "raise" if winkans >= 70 else "call"

    vereiste_winkans = inzet_om_te_callen / (pot + inzet_om_te_callen) * 100
    if winkans < vereiste_winkans + marge:
        return "fold"
    return "raise" if winkans >= 70 else "call"
