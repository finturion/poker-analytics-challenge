# --- Bot "Uitbuiter": speelt niet tegen kaarten maar tegen dit soort bots ---
#
# HET IDEE: alle andere bots hier proberen goed te pokeren. Deze probeert iets
# anders: hij gaat ervan uit dat zijn tegenstanders door een taalmodel of uit
# een opzoektabel zijn geschreven, en buit uit wat dat soort bots gemeen heeft.
# Drie dingen, en ik heb ze op dit veld gemeten in plaats van ze aan te nemen
# (zes bots, alle 91 handen, dezelfde situatie voorgelegd):
#
# 1. ZE ZIJN GEVOELIG VOOR INZETGROOTTE, MAAR EENZIJDIG. Tegen een minimum
#    raise van 60 foldt dit veld gemiddeld 60% van zijn handen; tegen een
#    grote raise van 200 foldt het 76%. Groot inzetten is dus goedkoper dan het
#    lijkt -- maar veel minder goedkoop dan dat getal suggereert, zie hieronder.
#
# 2. ZE RAISEN EERLIJK. Als een bot uit dit veld zelf verhoogt, heeft hij
#    gemiddeld 63 tot 73% winkans. Een raise is geen verhaal maar een
#    mededeling. Dus: geloof hem, en gooi alles onder GELOOF_EEN_RAISE weg.
#
# 3. ZE PASSEN ZICH NIET AAN. Geen van de zes houdt bij wat jij eerder deed --
#    de engine geeft alleen de acties van DEZE hand. Je hoeft dus niet
#    gebalanceerd te spelen: een lek dat werkt, blijft werken. Daarom steelt
#    hij met een vaste rekensom in plaats van met een frequentie.
#
# DE VALKUIL WAAR IK EERST IN LIEP, want dit is de hele bot. Die 76% is de
# foldkans over ALLE 91 handen. Maar je steelt niet van alle handen -- je
# steelt van een tegenstander die al in de pot zit, en dat is een SELECTIE van
# zijn sterkere handen. Opnieuw gemeten, nu alleen over de handen waarmee elke
# bot preflop meedoet, foldt dit veld nog maar 60% tegen die grote raise. Op
# 0,82 stal deze bot in potten waar het niet loonde en verloor hij; op de
# conditionele 0,60 gaat de drempel van pot 44 naar pot 133, en tegen twee
# spelers naar pot 356.
#
# En de mooiste uitkomst van die meting: bot_handsterkte foldt 0% van zijn
# meespeel-handen tegen een grote raise. Niet omdat hij dapper is, maar omdat
# `inzet_om_te_callen` niet in zijn signatuur staat. Wie je inzet niet KAN
# zien, kan er ook niet door weggeduwd worden. De simpelste bot van het veld
# is immuun voor de hele opzet van deze bot.
#
# EERLIJK OVER DE ZWAKKE PLEK: die 60% is gemeten op precies de zes bots
# waartegen hij speelt, en ik kon hun code inzien. In het echte toernooi met 44
# inzendingen kun je dat niet. Wat wél overdraagbaar is, is de vorm van het
# lek -- tight, drempel-gedreven, niet-aanpassend -- niet het exacte getal.
# Zet GEMETEN_FOLDKANS_GROTE_RAISE lager en hij wordt automatisch voorzichtiger.

import random

# Wat er gemeten is aan dit veld. Dit zijn de twee getallen om aan te draaien
# als je hem tegen een ander veld zet.
GEMETEN_FOLDKANS_GROTE_RAISE = 0.60  # aandeel MEESPEEL-handen dat dit veld weggooit
                                     # tegen een raise van 200. Conditioneel, niet over
                                     # alle 91 handen -- dat scheelt 76% vs 60%.
STEAL_INZET = 200                    # wat de engine van "grote_raise" maakt

# Tegen kracht: dit veld raist eerlijk, dus geloof het.
GELOOF_EEN_RAISE = 64.0     # tegen één raise alleen doorgaan vanaf deze winkans
GELOOF_TWEE_RAISES = 77.0   # tegen twee raises pas vanaf deze
HERRAISE_GRENS = 79.0       # en zelf terugpakken vanaf deze

# Eigen waarde-spel, zonder tegenstand.
VALUE_GROOT = 69.0          # hierboven groot inzetten voor waarde
VALUE_KLEIN = 57.0          # hierboven het minimum inzetten
SHOWDOWN_GRENS = 48.0       # hierboven meekijken, en niet als steal-materiaal gebruiken

# Tegen een niet-aanpassend veld zou 100% stelen optimaal zijn. Toch niet
# helemaal: één tegenstander die wél meekijkt (een mens, of een bot die telt)
# rekent een bot af die dit altijd doet. Dit is de rem.
#
# bluf_kans is hier een VERSTERKER en geen los kansje: bij de standaard 0,25
# steelt hij 0,25 x 2,5 = 63% van de keren dat de rekensom groen licht geeft.
# Belangrijk is dat bluf_kans = 0 hem ook echt uitzet -- dat stond eerst als
# `0.55 + bluf_kans`, en toen stal hij op nul nog 55% van de tijd. Een knop die
# op nul niet uit staat, is geen knop.
STEAL_VERSTERKING = 2.5

GOEDKOPE_CALL = 60
KORTE_STACK = 150
ALL_IN_GRENS_KORT = 55.0
ONBEKENDE_HAND = 40.0

# Vier archetypes schuiven de waarde-grenzen. Positief = strenger.
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
    Hoeveel raises deze hand, hoeveel tegenstanders zitten er nog in, en toont
    er iemand NU kracht?

    Die laatste is het belangrijkste. De lijst loopt over alle straten van de
    hand, dus aan een tafel van zeven staat er bijna altijd wel ergens een
    raise in -- in 35% van de beslissingen een raise van een VORIGE straat.
    Wie op "is er geraised?" test, gelooft dus nog op de river de raise van
    preflop en foldt vanaf de flop alles onder zijn geloof-grens.
    """
    raises = 0
    binnen = []
    gefold = []
    for actie in acties or []:
        naam = actie.get("bot_naam")
        soort = actie.get("actie", "")
        if soort == "raise":
            raises += 1
        if soort == "fold":
            if naam not in gefold:
                gefold.append(naam)
        elif naam not in binnen:
            binnen.append(naam)
    nog_binnen = [naam for naam in binnen if naam not in gefold]
    laatste_was_raise = bool(acties) and acties[-1].get("actie") == "raise"
    return raises, len(nog_binnen), laatste_was_raise


def steal_loont(pot, inzet, aantal_tegenstanders):
    """
    Levert een grote raise hier meer op dan hij kost?

    Je zet STEAL_INZET in om `pot` te winnen, dus de steal moet minstens
    STEAL_INZET / (pot + STEAL_INZET) van de tijd lukken. Wat hij oplevert is
    de gemeten foldkans -- maar wel bij ALLE tegenstanders tegelijk, dus die
    kans gaat tot de macht n. Bij 60% per bot is dat tegen één speler 0,60,
    tegen twee 0,36 en tegen drie 0,22.

    Gevolg, en dat is precies de bedoeling: heads-up loont stelen vanaf een pot
    van ongeveer 133, tegen twee spelers pas vanaf 356, en tegen drie vrijwel
    nooit. Bluffen is een heads-up wapen.
    """
    if pot + STEAL_INZET <= 0:
        return False
    nodig = STEAL_INZET / (pot + STEAL_INZET)
    verwacht = GEMETEN_FOLDKANS_GROTE_RAISE ** max(1, aantal_tegenstanders)
    return verwacht >= nodig


def kies_actie(hand, stack, strategie, bluf_kans, pot=0, inzet_om_te_callen=0,
               tegenstander_acties_deze_hand=None):
    winkans = WINKANS.get(hand_sleutel(hand), ONBEKENDE_HAND)
    pot = pot or 0
    inzet = inzet_om_te_callen or 0
    schuif = STRATEGIE_SCHUIF.get(strategie, 0.0)
    raises, tegenstanders, iemand_raiste_net = lees_tafel(tegenstander_acties_deze_hand)

    if stack < KORTE_STACK:
        return "all_in" if winkans >= ALL_IN_GRENS_KORT else "fold"

    # --- 1. Iemand toont NU kracht. Dit veld meent het dan, dus geloof het. -
    if iemand_raiste_net:
        grens = GELOOF_TWEE_RAISES if raises >= 2 else GELOOF_EEN_RAISE
        if winkans >= HERRAISE_GRENS + schuif:
            return "grote_raise"
        if winkans >= grens + schuif:
            return "call"
        return "fold"

    # --- 2. Niemand toonde kracht: waarde inzetten met wat sterk is ---------
    if winkans >= VALUE_GROOT + schuif:
        return "grote_raise"
    if winkans >= VALUE_KLEIN + schuif:
        return "raise"

    # --- 3. Showdown-waarde: meekijken, niet weggooien in een steal ---------
    if winkans >= SHOWDOWN_GRENS + schuif:
        if inzet == 0:
            return "check"
        return "call" if inzet <= GOEDKOPE_CALL else "fold"

    # --- 4. De onderkant: stelen als de gemeten foldkans het dekt -----------
    kans = min(1.0, bluf_kans * STEAL_VERSTERKING)
    if steal_loont(pot, inzet, tegenstanders) and random.random() < kans:
        return "grote_raise"
    return "check" if inzet == 0 else "fold"
