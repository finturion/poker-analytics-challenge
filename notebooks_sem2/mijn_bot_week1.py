def kies_actie(hand):
    """hand: lijst met 2 kaartwaarden, bv. ['A', 'K']. Geeft 'raise', 'call' of 'fold' terug."""
    if "A" in hand or "K" in hand:
        return "raise"
    if hand[0] == hand[1]:
        return "call"
    return "fold"
