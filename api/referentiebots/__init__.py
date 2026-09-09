"""
Referentiebots: een vaste meetlat die meespeelt in het toernooi.

WAAROM ZE BESTAAN
-----------------
De uitslag van een toernooi zegt alleen iets over de klas van die week. Verandert
iedereen zijn bot, dan verschuift het hele veld en weet een student nog niet of
híj beter is geworden. Deze vijf veranderen nooit. "Ik zit boven de tafellezer
maar onder de allrounder" zegt daarom meer dan "ik sta 19e van de 44".

WAT ZE NIET ZIJN
----------------
Ze zijn geen AI-bots en heten dat ook niet. Dat is een bewuste keuze: noem je ze
zo, dan is de impliciete boodschap "een taalmodel is hier de maatstaf", en dat
nodigt precies de vergelijking uit die je niet wil. Het zijn bots met een
opgeschreven strategie -- de code staat vanaf week 5 open -- en de vraag is waar
je staat ten opzichte van gedrag dat je precies kent.

Ze kunnen ook geen bonuspunten van studenten afpakken. toernooi_runner voegt ze
toe NA het vastleggen van `namen_deelnemers`, en bonus_rooster rekent de ladder
alleen over die lijst. Ze beïnvloeden dus wel de chips aan tafel -- ze spelen echt
mee -- maar niet de verdeling van de punten.

WAAROM DE BESTANDEN HIER STAAN EN NIET IN mijn_bots/
----------------------------------------------------
render.yaml deployt met `rootDir: api`, dus alleen deze map komt op de server.
Een bot in mijn_bots/ zou lokaal werken en in productie ontbreken. De originelen
blijven in mijn_bots/ staan als werkplaats; scripts/test_referentiebots.py
controleert dat de twee kopieën byte-voor-byte gelijk zijn, zodat ze niet stil uit
elkaar lopen.

HOE JE ER EEN TOEVOEGT OF WIJZIGT
---------------------------------
Zet het bestand in deze map, registreer hem hieronder met een `niveau` en een
`beschrijving`, en draai scripts/test_referentiebots.py. Twee dingen gaan
gegarandeerd fout als je er niet op let:

1. **De parameternamen moeten exact kloppen.** De engine kiest zijn argumenten op
   naam uit: hand, stack, ronde, pot, inzet_om_te_callen,
   tegenstander_acties_deze_hand, strategie, bluf_kans. Noem je een parameter
   anders, dan wordt je functie zonder argumenten aangeroepen, crasht hij, en
   foldt de bot stil élke hand.
2. **De kaartwaarden zijn strings.** `["A", "10"]`, niet `["A", 10]` en niet
   `["A", "T"]`.
"""
from . import (bot_allrounder, bot_bluffer, bot_inzetgrootte, bot_potodds,
               bot_tafellezer)

# In welke weken ze meespelen. Week 1 niet: daar kennen bots alleen hun eigen twee
# kaarten en zou een scherpe referentiebot alleen demoraliseren.
WEKEN_MET_REFERENTIEBOTS = (3, 5)

# Vanaf welke week hun code openbaar is. In week 3 is het een meetlat waar je
# tegen speelt; in week 5, als de pokerlijn afrondt, mag je zien hoe ze het doen --
# dan valt er nog van te leren voor de slotinzending.
OPENBAAR_VANAF_WEEK = 5

# DRIE NIVEAUS, NIET VIJF -- en dat is een meetuitkomst, geen ontwerpkeuze.
#
# Gemeten in het veld dat er echt komt (44 studentachtige bots + deze vijf,
# 8 seeds x 20 simulaties), met de standaardfout erbij:
#
#   Tafellezer     733 ± 44     44e van 49
#   PotOdds        877 ± 89     37e van 49
#   Allrounder    1090 ± 96     14e van 49
#   Bluffer       1585 ± 150     2e van 49
#   Inzetgrootte  1616 ± 193     1e van 49
#
# Twee paren zijn niet van elkaar te onderscheiden: PotOdds en Tafellezer
# verschillen -145 ± 100, Bluffer en Inzetgrootte +32 ± 244. Die krijgen dus
# hetzelfde niveau. Doen alsof er vijf treden zijn maakt van "ik zit boven
# niveau 3" een bewering die de data niet draagt.
#
# Let op dat de orde afhangt van het VELD. In een toernooi met alleen deze vijf
# en twee andere bots was PotOdds de zwakste van allemaal; hier is hij dat niet.
# Een niveau is dus geen eigenschap van een bot maar van een bot tussen anderen.
# scripts/test_referentiebots.py rekent het na en klaagt als het verschuift.
REFERENTIEBOTS = {
    "Referentie_PotOdds": {
        "module": bot_potodds,
        "strategie": "balanced",
        "bluf_kans": 0.15,
        "niveau": 1,
        "beschrijving": "Rekent bij elke beslissing de prijs uit: wat je moet bijleggen "
                        "gedeeld door wat er dan in de pot zit. Doet daardoor mee met "
                        "matige handen als het bijna niets kost — en dat is zijn zwakte, "
                        "want zijn winkans-tabel is kop-op-kop terwijl hij aan een tafel "
                        "van zes zit. De meeste studenten verslaan hem.",
    },
    "Referentie_Tafellezer": {
        "module": bot_tafellezer,
        "strategie": "tight",
        "bluf_kans": 0.1,
        "niveau": 1,
        "beschrijving": "Kijkt naar wat de tegenstanders deze hand deden en past zich "
                        "daarop aan. Verliest zelden groot, maar wint ook nooit groot: hij "
                        "min-raist zijn goede handen en haalt er te weinig uit. De laagste "
                        "van de vijf; kom je hier niet boven, dan zit er iets fout.",
    },
    "Referentie_Allrounder": {
        "module": bot_allrounder,
        "strategie": "balanced",
        "bluf_kans": 0.2,
        "niveau": 2,
        "beschrijving": "Weegt handsterkte, prijs, tegenstanders en inzetgrootte samen "
                        "tot één getal. Doet alles een beetje en niets uitgesproken. Zit "
                        "net boven de mediaan van een klas: hem verslaan is een redelijk "
                        "doel voor deze week.",
    },
    "Referentie_Bluffer": {
        "module": bot_bluffer,
        "strategie": "aggressive",
        "bluf_kans": 0.35,
        "niveau": 3,
        "beschrijving": "Rekent bluf-odds: hoe vaak moet deze inzet werken om winst te "
                        "maken? Zet druk op mensen die te veel folden. Om hem te "
                        "verslaan moet je vaker meegaan dan comfortabel voelt. In de "
                        "meting eindigde geen enkele testbot boven hem.",
    },
    "Referentie_Inzetgrootte": {
        "module": bot_inzetgrootte,
        "strategie": "aggressive",
        "bluf_kans": 0.25,
        "niveau": 3,
        "beschrijving": "Kiest bewust hoeveel hij inzet: het minimum, 200, of alles. Zijn "
                        "voorsprong komt bijna volledig uit preflop-agressie, niet uit slim "
                        "spel later in de hand. Samen met de Bluffer de bovengrens: "
                        "verslaan is een stretchdoel, niet de verwachting.",
    },
}


def referentiebots_voor(week):
    """De bots die deze week meespelen, in de vorm die speel_toernooi verwacht."""
    if week not in WEKEN_MET_REFERENTIEBOTS:
        return {}
    return {
        naam: {"kies_actie": info["module"].kies_actie,
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
    return {naam: inspect.getsource(info["module"]) for naam, info in REFERENTIEBOTS.items()}
