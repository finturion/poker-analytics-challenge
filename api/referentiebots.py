"""
Referentiebots: een vaste meetlat die meespeelt in het toernooi.

WAAROM ZE BESTAAN
-----------------
De uitslag van een toernooi zegt alleen iets over de klas van die week. Verandert
iedereen zijn bot, dan verschuift het hele veld en weet een student nog niet of
híj beter is geworden. Deze bots veranderen nooit. "Ik zit boven de pot-odds-bot
maar onder de scherpe" zegt daarom meer dan "ik sta 19e van de 44".

WAT ZE NIET ZIJN
----------------
Ze zijn geen AI-bots en heten dat ook niet. Dat is een bewuste keuze: noem je ze
zo, dan is de impliciete boodschap "een taalmodel is hier de maatstaf", en dat
nodigt precies de vergelijking uit die je niet wil. Het zijn bots met een
opgeschreven strategie, en de vraag is waar je staat ten opzichte van gedrag dat
je precies kent.

Ze kunnen ook geen bonuspunten van studenten afpakken. toernooi_runner voegt ze
toe NA het vastleggen van `namen_deelnemers`, en bonus_rooster rekent de ladder
alleen over die lijst. Ze beïnvloeden dus wel de chips aan tafel -- ze spelen echt
mee -- maar niet de verdeling van de punten.

HOE JE ER EEN TOEVOEGT
----------------------
Zet hem in REFERENTIEBOTS met een `niveau` en een `beschrijving`. Twee dingen
gaan gegarandeerd fout als je er niet op let:

1. **De parameternamen moeten exact kloppen.** De engine kiest zijn argumenten op
   naam uit: hand, stack, ronde, pot, inzet_om_te_callen,
   tegenstander_acties_deze_hand, strategie, bluf_kans. Noem je een parameter
   anders, dan wordt je functie zonder argumenten aangeroepen, crasht hij, en
   foldt de bot stil élke hand. Je merkt daar niets van behalve een slechte score.
2. **De kaartwaarden zijn strings.** `["A", "10"]`, niet `["A", 10]` en niet
   `["A", "T"]`. De tien heet hier "10".

scripts/test_referentiebots.py controleert beide, en meet daarna of de niveaus
ook echt oplopen. Draai dat na elke wijziging -- bij 500 tot 800 chips ruis is
"deze is beter" geen bewering die je op gevoel kunt doen.
"""

# In welke weken de referentiebots meespelen. Week 1 niet: daar kennen bots alleen
# hun eigen twee kaarten en zou een scherpe referentiebot alleen maar demoraliseren.
WEKEN_MET_REFERENTIEBOTS = (3, 5)

# Vanaf welke week hun code openbaar is. In week 3 is het een meetlat waar je
# tegen speelt; in week 5, als de pokerlijn afrondt, mag je zien hoe ze het doen --
# dan valt er nog van te leren voor de slotinzending.
OPENBAAR_VANAF_WEEK = 5

# Kaartwaarde -> getal, voor de bots hieronder. Dezelfde notatie als in de
# notebooks: de tien is "10".
_RANG = {"A": 14, "K": 13, "Q": 12, "J": 11, "10": 10, "9": 9, "8": 8,
         "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}


def _kracht(hand):
    """Grove handsterkte: de hoogste kaart, plus een bonus voor een paar."""
    hoog = max(_RANG.get(hand[0], 2), _RANG.get(hand[1], 2))
    return hoog + (4 if hand[0] == hand[1] else 0)


# --- PLAATSHOUDERS ---------------------------------------------------------
# Deze twee zijn er alleen om de leidingen te kunnen testen. Vervang ze door de
# echte set (matig tot scherp) zodra die klaar is; de vorm hieronder is het
# contract waar toernooi_runner en de tests op rekenen.

def _plaatshouder_voorzichtig(hand, stack, ronde="preflop"):
    """Doet alleen mee met een hoge kaart. Ondergrens van het veld."""
    if _kracht(hand) >= 13:
        return "call"
    return "fold"


def _plaatshouder_drempel(hand, stack, ronde="preflop"):
    """Vaste drempel, geen ronde-bewustzijn. De 'eerste bot die werkt'."""
    kracht = _kracht(hand)
    if kracht >= 15:
        return "raise"
    if kracht >= 11:
        return "call"
    return "fold"


REFERENTIEBOTS = {
    "Referentie_Voorzichtig": {
        "kies_actie": _plaatshouder_voorzichtig,
        "strategie": "tight",
        "bluf_kans": 0.0,
        "niveau": 1,
        "beschrijving": "Doet alleen mee met een heer of hoger, en verhoogt nooit. "
                        "Zit je hieronder, dan zit er waarschijnlijk een fout in je bot.",
    },
    "Referentie_Drempel": {
        "kies_actie": _plaatshouder_drempel,
        "strategie": "tight",
        "bluf_kans": 0.1,
        "niveau": 2,
        "beschrijving": "Eén vaste drempel op handsterkte, dezelfde in elke ronde. "
                        "Dit is het niveau van een bot die werkt maar nergens op reageert.",
    },
}


def referentiebots_voor(week):
    """De bots die deze week meespelen, in de vorm die speel_toernooi verwacht."""
    if week not in WEKEN_MET_REFERENTIEBOTS:
        return {}
    return {
        naam: {"kies_actie": info["kies_actie"],
               "strategie": info["strategie"],
               "bluf_kans": info["bluf_kans"]}
        for naam, info in REFERENTIEBOTS.items()
    }


def beschrijvingen(week):
    """
    Naam, niveau en beschrijving van de bots die deze week meespelen.

    Altijd zichtbaar: een meetlat waarvan je niet weet wat hij doet, is geen
    meetlat. De broncode komt er pas vanaf OPENBAAR_VANAF_WEEK bij.
    """
    if week not in WEKEN_MET_REFERENTIEBOTS:
        return []
    return sorted(
        ({"naam": naam, "niveau": info["niveau"], "beschrijving": info["beschrijving"]}
         for naam, info in REFERENTIEBOTS.items()),
        key=lambda r: r["niveau"],
    )


def broncode(week):
    """
    De broncode van de referentiebots, of None zolang die nog niet openbaar is.

    Dit is docentcode, geen studentwerk -- die vrijgeven kost niemand zijn
    bonuspunt en er valt van te leren.
    """
    if week < OPENBAAR_VANAF_WEEK or week not in WEKEN_MET_REFERENTIEBOTS:
        return None
    import inspect
    return {naam: inspect.getsource(info["kies_actie"]) for naam, info in REFERENTIEBOTS.items()}
