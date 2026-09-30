# --- Bot "Bluffer": bluffen als rekensom, niet als gok ----------------------
#
# HET IDEE: de andere bots bluffen als bijzaak -- "als ik zou folden, gooi dan
# een dobbel". Deze bot draait het om: bluffen is zijn hoofdlijn, en hij
# rekent per situatie uit of een bluf kan lonen. Drie dingen die hij anders
# doet dan de rest:
#
# 1. HIJ REKENT DE BLUF-ODDS UIT. Een bluf is een weddenschap net als een
#    call, alleen omgekeerd: je riskeert je inzet om de pot te winnen. Riskeer
#    je 40 om een pot van 120 te pakken, dan hoeft die bluf maar 40/160 = 25%
#    van de tijd te lukken. In een pot van 30 moet dezelfde bluf 57% lukken --
#    en dat is te veel gevraagd. Grote pot = goedkope bluf.
#
# 2. HIJ REKENT HET AANTAL TEGENSTANDERS MEE. Een bluf moet bij ALLEMAAL
#    lukken. Twee spelers die elk 70% van de tijd folden, folden samen maar
#    0,7 x 0,7 = 49% van de tijd. Daarom deelt hij de benodigde foldkans terug
#    naar per speler, en bluft hij niet meer tegen een volle tafel.
#
# 3. HIJ BLUFT MET ZIJN SLECHTSTE HANDEN, NIET MET ZIJN MIDDENMOOT. Een hand
#    van 50% winkans kan de pot nog winnen door hem gewoon te laten zien; die
#    in een bluf veranderen gooit die waarde weg. Een hand van 32% wint nooit
#    bij de showdown, en dus is bluffen daarmee gratis geleend geld. Dit is
#    het verschil tussen bluffen en gokken.
#
# Zijn waarde-spel is bewust simpel gehouden -- dat is niet waar deze bot over
# gaat. `bluf_kans` is bij hem geen bijschakelaar maar de hoofdknop: hij
# schaalt hoe vaak hij een goede plek ook echt pakt.

import random

# De knoppen. Grenzen in winkans-procenten.
TOP_GRENS = 78.0            # hierboven groot inzetten voor waarde
VALUE_GRENS = 63.0          # hierboven klein inzetten voor waarde
SHOWDOWN_GRENS = 48.0       # hierboven heb je showdown-waarde: NOOIT bluffen
GEEN_WAARDE_GRENS = 42.0    # hieronder win je nooit bij de showdown: bluf-materiaal

BLUF_INZET = 40             # wat een gewone raise kost (het wettelijke minimum)
MAX_FOLDKANS_PER_SPELER = 0.55  # meer dan dit van één tegenstander vragen is te veel.
                                # Dit is de knop die echt bijt: op 0,72 stond hij zo
                                # ruim dat zelfs een bluf die 67% moet lukken erdoor
                                # kwam, en dan is de rekensom decoratie.
MAX_TEGENSTANDERS = 3       # tegen meer spelers dan dit nooit bluffen
# Hoe later de straat, hoe geloofwaardiger een bluf: er komen geen kaarten meer
# die je verhaal onderuit halen, en wie tot hier meekwam en niet inzette, heeft
# meestal niets. Vermenigvuldigt de bluf_kans.
STRAAT_FACTOR = {"preflop": 0.3, "flop": 0.9, "turn": 1.2, "river": 1.5}

GOEDKOPE_CALL = 60          # met showdown-waarde tot dit bedrag meegaan
KORTE_STACK = 150
ALL_IN_GRENS_KORT = 55.0
ONBEKENDE_HAND = 40.0

# Vier archetypes schuiven de waarde-grenzen op. Positief = strenger.
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


def tel_tegenstanders(acties):
    """
    Hoeveel tegenstanders zitten er nog in, en toont er iemand NU kracht?

    `or []` is het vangnet: bij de eerste beslissing van een hand is de lijst
    leeg. Let op dat deze lijst over ALLE straten van de hand loopt -- wie
    foldde is echt weg, maar een raise van preflop staat er op de river nog in.
    """
    binnen = []
    gefold = []
    for actie in acties or []:
        naam = actie.get("bot_naam")
        soort = actie.get("actie", "")
        if soort == "fold":
            if naam not in gefold:
                gefold.append(naam)
        elif naam not in binnen:
            binnen.append(naam)
    nog_binnen = [naam for naam in binnen if naam not in gefold]
    # De DRUK VAN NU is de laatste actie, niet of er ooit in deze hand
    # verhoogd is. Dat verschil is hier geen detail: aan een tafel van zeven
    # heeft bijna elke hand ooit een raise gezien, dus wie op "iemand raiste"
    # test, komt na preflop nooit meer bij zijn eigen bluf-regel. Gemeten was
    # die regel daarmee in 0,5% van zijn beslissingen bereikbaar.
    laatste_was_raise = bool(acties) and acties[-1].get("actie") == "raise"
    return len(nog_binnen), laatste_was_raise


def benodigde_foldkans(pot, risico, aantal_tegenstanders):
    """
    Welke foldkans PER TEGENSTANDER heeft deze bluf minimaal nodig?

    Je zet `risico` in om `pot` te winnen, dus de bluf moet minstens
    risico / (pot + risico) van de tijd lukken -- dat is het break-even punt,
    precies de pot-odds-formule maar van de andere kant van de tafel.

    En hij moet bij ALLE tegenstanders lukken: folden ze elk met kans f, dan
    is de kans dat ze allemaal folden f tot de macht n. Dus wat je van één
    speler nodig hebt, is de n-de wortel uit wat je in totaal nodig hebt.
    """
    if pot + risico <= 0:
        return 1.0
    totaal_nodig = risico / (pot + risico)
    return totaal_nodig ** (1.0 / max(1, aantal_tegenstanders))


def kies_actie(hand, stack, strategie, bluf_kans, ronde="preflop", pot=0,
               inzet_om_te_callen=0, tegenstander_acties_deze_hand=None):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    # bluf_kans kan None zijn: een inzending zonder bluf_kans (week 3) krijgt hem
    # toch aangeboden zodra hij in je handtekening staat. Zonder deze regel crasht
    # de vergelijking hieronder en foldt de engine je stil elke hand.
    bluf_kans = bluf_kans or 0.0
    pot = pot or 0
    inzet = inzet_om_te_callen or 0
    schuif = STRATEGIE_SCHUIF.get(strategie, 0.0)
    tegenstanders, iemand_raiste_net = tel_tegenstanders(tegenstander_acties_deze_hand)

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT else "fold"

    # --- waarde-spel: kort en zonder verrassingen ---------------------------
    if winkans >= TOP_GRENS + schuif:
        return "grote_raise"
    if winkans >= VALUE_GRENS + schuif:
        return "raise"

    # --- showdown-waarde: meegaan, maar dit is geen bluf-materiaal ----------
    if winkans >= SHOWDOWN_GRENS + schuif:
        if inzet == 0:
            return "check"
        return "call" if inzet <= GOEDKOPE_CALL else "fold"

    # --- de tussenzone: te zwak voor waarde, te sterk om weg te gooien ------
    if winkans >= GEEN_WAARDE_GRENS + schuif:
        return "check" if inzet == 0 else "fold"

    # --- de onderkant: hier wordt gebluft, als de rekensom klopt ------------
    if iemand_raiste_net or tegenstanders > MAX_TEGENSTANDERS:
        return "check" if inzet == 0 else "fold"

    nodig = benodigde_foldkans(pot, inzet + BLUF_INZET, tegenstanders)
    kans = min(1.0, bluf_kans * STRAAT_FACTOR.get(ronde, 1.0))
    if nodig <= MAX_FOLDKANS_PER_SPELER and random.random() < kans:
        return "raise"
    return "check" if inzet == 0 else "fold"
