# --- Bot "Allrounder": alle vier de ideeën in één getal ---------------------
#
# HET IDEE: de andere bots kiezen elk één ding om naar te kijken. Deze telt ze
# op tot één getal, `voordeel`: hoeveel procentpunt zit ik boven wat deze
# situatie van me vraagt? Daar hangt dan zowel de keuze als de inzetgrootte
# aan. Alle vier de ingrediënten zitten erin:
#
#   handsterkte  -> de winkans uit de tabel
#   pot-odds     -> wat de prijs minimaal van je vraagt
#   tafellezen   -> DRUK_LAATSTE_RAISE en DRUK_PER_TEGENSTANDER
#   inzetgrootte -> groot voordeel = grote raise, klein voordeel = minimum
#
# TWEE VRAGEN, TWEE REKENSOMMEN. Dat is het enige echt subtiele hier. "Mag ik
# zelf inzetten?" is een vraag over rangorde: heb ik waarschijnlijk de beste
# hand? Daar is de kop-op-kop-tabel genoeg voor. "Mag ik meegaan?" is een
# vraag over een absoluut getal tegen een absolute prijs, en dáár is die tabel
# gevaarlijk: hij gaat over één tegenstander, en aan tafel zitten er meer.
# Voor die tweede vraag rekent hij zijn winkans dus eerst om.
#
# Waarom dat uitmaakt, gemeten: bot_potodds verliest gemiddeld 17 chips per
# call over 3635 calls, omdat 7-2 met 34% "winkans" een prijs van 17% lijkt te
# verslaan. Tegen drie tegenstanders is die 34% in werkelijkheid 14%, en dan is
# diezelfde call gewoon verlies. Dit is dezelfde pot-odds-regel, met het lek
# eruit.

import random

# De knoppen. Alles in procentpunten winkans, behalve waar het chips zegt.
EIGEN_DREMPEL = 50.0        # onder 50% kop-op-kop ben je geen favoriet
GROOT_VOORDEEL = 22.0       # hierboven: groot inzetten
KLEIN_VOORDEEL = 8.0        # hierboven: het minimum inzetten

STRAAT_MARGE = {"preflop": 0.0, "flop": 4.0, "turn": 7.0, "river": 10.0}
DRUK_LAATSTE_RAISE = 7.0        # iemand verhoogde NET: dat is de druk van dit moment
DRUK_PER_EERDERE_RAISE = 2.0    # elke raise eerder in deze hand telt lichter mee. De
                                # lijst loopt over alle straten, dus een raise erin kan
                                # van preflop zijn; vol meerekenen maakte hem op de
                                # river zo streng dat hij 81% van de tijd checkte
DRUK_PER_TEGENSTANDER = 2.0     # elke extra speler die meedoet ook -- maar alleen
                                # bij "zelf inzetten", zie kies_actie()
MINIMUM_TEGENSTANDERS = 2       # bij zijn eerste beslissing weet hij nog niets:
                                # doe dan alsof er minstens zoveel meespelen

GROTE_RAISE_CHIPS = 200         # wat de engine van "grote_raise" maakt
GROTE_RAISE_MAX_DEEL = 0.4      # past dat niet in je stack, dan all-in
BLUF_POT_MIN = 60               # onder deze pot is stelen de moeite niet
BLUF_MAX_WINKANS = 42.0         # alleen bluffen met handen die nooit showdown winnen
KORTE_STACK = 150
ALL_IN_GRENS_KORT = 55.0
ONBEKENDE_HAND = 40.0

# Vier archetypes tellen mee als extra druk. Positief = strenger.
STRATEGIE_SCHUIF = {"tight": 5.0, "balanced": 0.0, "aggressive": -4.0, "loose": -6.0}

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
    Hoeveel raises deden de tegenstanders, hoeveel van ze legden geld in, en
    verhoogde er NET iemand? Die laatste is niet hetzelfde als de eerste: de
    lijst wordt niet per straat leeggemaakt.
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


def winkans_tegen_meer_spelers(winkans, aantal_tegenstanders):
    """
    De tabel geeft je winkans tegen ÉÉN tegenstander. Aan tafel moet je van
    allemaal winnen, en als benadering is dat kans tot de macht n.

    Gemeten met 8000 simulaties per hand is die benadering consequent iets te
    pessimistisch -- tegenstanders delen hetzelfde bord, dus hun handen zijn
    niet onafhankelijk -- en het scheelt het meest bij de zwakste handen:

        A-A tegen 3 spelers: benadering 62%, echt gemeten 64%
        7-2 tegen 3 spelers: benadering  4%, echt gemeten 14%

    Te pessimistisch is hier precies de goede kant om te missen: het houdt hem
    weg van de goedkope calls met troep, en dat is het enige waar deze
    correctie voor bedoeld is.
    """
    kans = max(0.0, min(1.0, winkans / 100.0))
    return 100.0 * kans ** max(1, aantal_tegenstanders)


def kies_actie(hand, stack, strategie, bluf_kans, ronde="preflop", pot=0,
               inzet_om_te_callen=0, tegenstander_acties_deze_hand=None):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    pot = pot or 0
    inzet = inzet_om_te_callen or 0
    raises, meedoeners, iemand_raiste_net = lees_tafel(tegenstander_acties_deze_hand)
    tegenstanders = max(meedoeners, MINIMUM_TEGENSTANDERS)

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT else "fold"

    # Alles wat deze situatie moeilijker maakt, opgeteld tot één getal.
    eerdere_raises = max(0, raises - (1 if iemand_raiste_net else 0))
    druk = ((DRUK_LAATSTE_RAISE if iemand_raiste_net else 0.0)
            + DRUK_PER_EERDERE_RAISE * eerdere_raises
            + STRAAT_MARGE.get(ronde, 8.0)
            + STRATEGIE_SCHUIF.get(strategie, 0.0))

    # Vraag 1: zelf inzetten? Dat is een vraag over rangorde. Hier telt het
    # aantal tegenstanders als losse straf mee, want er wordt niets omgerekend.
    voordeel_inzetten = (winkans - EIGEN_DREMPEL - druk
                         - DRUK_PER_TEGENSTANDER * (tegenstanders - 1))
    if voordeel_inzetten >= GROOT_VOORDEEL:
        if GROTE_RAISE_CHIPS <= GROTE_RAISE_MAX_DEEL * stack:
            return "grote_raise"
        return "all_in"
    if voordeel_inzetten >= KLEIN_VOORDEEL:
        return "raise"

    if inzet == 0:
        return "check"

    # Vraag 2: meegaan? Dat is een vraag over een prijs, en dus over een
    # absolute winkans -- hier moet de tabel wél omgerekend worden. En dan NIET
    # ook nog DRUK_PER_TEGENSTANDER erbij: het aantal spelers zit al in die
    # omrekening, en twee keer straffen maakte hem zo tight dat hij A-9 voor
    # 20 chips in een pot van 100 weggooide.
    vereiste_winkans = inzet / (pot + inzet) * 100
    voordeel_meegaan = (winkans_tegen_meer_spelers(winkans, tegenstanders)
                        - vereiste_winkans - druk)
    if voordeel_meegaan >= 0:
        return "call"

    if (pot >= BLUF_POT_MIN and not iemand_raiste_net and winkans < BLUF_MAX_WINKANS
            and random.random() < bluf_kans):
        return "raise"
    return "fold"
