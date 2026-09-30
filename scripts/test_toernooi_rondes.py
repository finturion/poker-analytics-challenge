"""
Test de rondelogica van het toernooi:

1. de cachesleutel neemt de ronde mee (ronde 2 wist ronde 1 niet);
2. ronde 2 begint met de eindstand van ronde 1 + 1000 voor iedereen;
3. de validator vlagt een bot die altijd hetzelfde doet, zonder af te keuren.

Draaien:  python3 scripts/test_toernooi_rondes.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "api"))

import toernooi_runner
from bot_validator import valideer_bot_code
from poker_adapter import STANDAARD_INITIAL_STACK
from toernooi_runner import cache_sleutel, draai_toernooi, haal_gecacht_resultaat_op

geslaagd = 0


def check(voorwaarde, omschrijving, detail=""):
    global geslaagd
    assert voorwaarde, f"GEZAKT: {omschrijving} {detail}".rstrip()
    geslaagd += 1
    print(f"  ok  {omschrijving}")


# ---------------------------------------------------------------------------
# 1. Cachesleutels
# ---------------------------------------------------------------------------
print("Cachesleutels")
check(cache_sleutel(5) == "5", "ronde 1 houdt de oude sleutel '5'")
check(cache_sleutel(5, 1) == "5_vs_1", "ronde 1 met vergelijking houdt '5_vs_1'")
check(cache_sleutel(5, None, 2) == "5_ronde2", "ronde 2 krijgt een eigen sleutel")
check(cache_sleutel(5, 1, 2) == "5_vs_1_ronde2", "ronde 2 met vergelijking ook")
check(
    cache_sleutel(5, None, 1) != cache_sleutel(5, None, 2),
    "ronde 1 en 2 botsen niet",
)

# ---------------------------------------------------------------------------
# 2. Twee rondes achter elkaar, met een neptafel-cache
# ---------------------------------------------------------------------------
print("\nTwee rondes achter elkaar")


def tight(hand, stack, ronde, strategie, bluf_kans):
    return "raise" if hand[0] in ("A", "K", "Q") else "fold"


def loose(hand, stack, ronde, strategie, bluf_kans):
    return "call"


def stub(hand, stack, ronde, strategie, bluf_kans):
    return "fold"


nep_cache = {}
toernooi_runner.db.laad_toernooi_resultaat = nep_cache.get
toernooi_runner.db.sla_toernooi_resultaat_op = lambda sleutel, resultaat: nep_cache.__setitem__(sleutel, resultaat)
toernooi_runner._verzamel_bots_over_weken = lambda week, vergelijk: (
    {
        naam: {"kies_actie": fn, "strategie": "tight", "bluf_kans": 0.1}
        for naam, fn in [("tight", tight), ("loose", loose), ("stub", stub)]
    },
    ["tight", "loose", "stub"],
)

ronde1 = draai_toernooi(5, n_simulaties=2, n_handen=20, ronde=1)
ronde2 = draai_toernooi(5, n_simulaties=2, n_handen=20, ronde=2)

# Elke ronde begint schoon op 1000, ook in de bonusweek. Tot september 2026
# speelde week 5 vanaf ronde 2 door met de chips van de ronde ervoor; dat is
# eruit gehaald omdat je woensdagresultaat dan doorwerkte in je
# vrijdagstartpositie, en de vrijdaguitslag dus niet meer alleen de bot mat die
# je vrijdag had ingeleverd.
check(ronde1["startstacks"] is None, "ronde 1 start zonder startstacks")
check(ronde2["startstacks"] is None, "ronde 2 ook: elke ronde begint schoon")
check(
    abs(sum(ronde2["eindstand_per_bot"].values())
        - STANDAARD_INITIAL_STACK * len(ronde2["eindstand_per_bot"])) < 1e-6,
    "de chips in ronde 2 tellen op tot 1000 per bot",
)
check(
    "5" in nep_cache and "5_ronde2" in nep_cache,
    "beide rondes staan onder hun eigen sleutel opgeslagen",
)
check(
    haal_gecacht_resultaat_op(5, ronde=1)["eindstand_per_bot"] == ronde1["eindstand_per_bot"],
    "de woensdaguitslag is na ronde 2 nog steeds op te halen",
)
check(
    haal_gecacht_resultaat_op(5, ronde=3)["gedraaid"] is False,
    "een ronde die nog niet gedraaid is meldt dat netjes",
)

# --- en dat geldt in elke week, niet alleen in de bonusweek ---
# Een tweede ronde is een tweede poging: opnieuw draaien omdat er bots bij zijn
# gekomen, bijvoorbeeld. Dan moet iedereen weer op 1000 staan, anders meet ronde
# 2 vooral ronde 1 nog een keer en zijn de twee standen niet te vergelijken.
w3_ronde1 = draai_toernooi(3, n_simulaties=2, n_handen=20, ronde=1)
w3_ronde2 = draai_toernooi(3, n_simulaties=2, n_handen=20, ronde=2)

check(w3_ronde2["startstacks"] is None, "week 3 ronde 2 krijgt geen startstacks mee")
check(
    any(abs(stand - STANDAARD_INITIAL_STACK) > 1e-6
        for stand in w3_ronde1["eindstand_per_bot"].values()),
    "en dat is niet omdat de eindstand van ronde 1 toevallig overal 1000 was",
)
check(
    abs(sum(w3_ronde2["eindstand_per_bot"].values())
        - STANDAARD_INITIAL_STACK * len(w3_ronde2["eindstand_per_bot"])) < 1e-6,
    "de chips in week 3 ronde 2 tellen op tot 1000 per bot",
)
check(
    haal_gecacht_resultaat_op(3, ronde=1)["eindstand_per_bot"] == w3_ronde1["eindstand_per_bot"],
    "en ronde 1 van week 3 blijft gewoon naast ronde 2 staan",
)

chips_in = STANDAARD_INITIAL_STACK * len(ronde2["eindstand_per_bot"])
chips_uit = sum(ronde2["eindstand_per_bot"].values())
check(
    abs(chips_in - chips_uit) < 1e-6,
    f"chips blijven behouden in ronde 2 ({chips_in} in, {chips_uit} uit)",
)

# ---------------------------------------------------------------------------
# 3b. De formatieve donderdagronde: een repetitie die niets verschuift
# ---------------------------------------------------------------------------
print("\nFormatieve ronde")
from toernooi_runner import cache_sleutel as sleutel

check(sleutel(5, None, 2, formatief=True) == "5_ronde2_formatief", "een formatieve run heeft een eigen sleutel")
check(
    sleutel(5, None, 2, formatief=True) != sleutel(5, None, 2),
    "en bezet dus niet de plek van de ronde die meetelt",
)

vrijdag_voor = dict(ronde2["eindstand_per_bot"])
oefen = draai_toernooi(5, n_simulaties=2, n_handen=20, ronde=2, formatief=True)

check(oefen["formatief"] is True, "de uitslag zegt zelf dat hij formatief is")
check(
    oefen["startstacks"] == ronde2["startstacks"],
    "de repetitie draait met exact dezelfde startstacks als de echte ronde 2",
)
check(
    "5_ronde2_formatief" in nep_cache and nep_cache["5_ronde2"]["eindstand_per_bot"] == vrijdag_voor,
    "hij staat naast ronde 2 in de cache en heeft die niet aangeraakt",
)

# De echte ronde 2 opnieuw draaien mag niet ineens vanaf de oefenronde starten.
opnieuw = draai_toernooi(5, n_simulaties=2, n_handen=20, ronde=2, forceer_opnieuw=True)
check(
    opnieuw["startstacks"] == ronde2["startstacks"],
    "en de startstacks van ronde 2 komen nog steeds uit ronde 1, niet uit de oefenronde",
)
check(
    haal_gecacht_resultaat_op(5, ronde=3)["gedraaid"] is False,
    "een oefenronde wordt nooit de bron voor een volgende ronde",
)

# ---------------------------------------------------------------------------
# 4. constante_bot
# ---------------------------------------------------------------------------
print("\nValidator: constante_bot")
stub_code = 'def kies_actie(hand, stack, ronde, strategie, bluf_kans):\n    return "fold"\n'
echte_code = (
    "def kies_actie(hand, stack, ronde, strategie, bluf_kans):\n"
    "    if stack < 100:\n"
    '        return "all_in"\n'
    "    if hand[0] == hand[1]:\n"
    '        return "raise"\n'
    '    return "call"\n'
)
r_stub = valideer_bot_code(stub_code, 5, strategie="tight", bluf_kans=0.1)
r_echt = valideer_bot_code(echte_code, 5, strategie="tight", bluf_kans=0.1)
check(r_stub["geldig"] is True, "een constante bot wordt NIET afgekeurd")
check(r_stub["constante_bot"] is True, "maar hij wordt wel gevlagd")
check(r_echt["constante_bot"] is False, "een bot die varieert wordt niet gevlagd")

r_fout = valideer_bot_code("import os\n" + stub_code, 5, strategie="tight", bluf_kans=0.1)
check(
    "constante_bot" in r_fout,
    "ook een afgekeurde bot heeft het veld (vaste vorm van het resultaat)",
)

# --- de twee kopieën van de sleutel mogen niet uit de pas lopen ---
# bonus_rooster kan toernooi_runner niet importeren (die importeert bonus_rooster
# al), dus bouwt hij de sleutel zelf. Twee plekken die "5_ronde2" moeten spellen
# is een driftrisico; deze check maakt er een fout van in plaats van een stille
# afwijking waarbij de bonus in een lege uitslag kijkt.
import bonus_rooster

for week in (1, 3, 5):
    for ronde in (1, 2, 3):
        check(
            bonus_rooster._cache_sleutel(week, ronde) == sleutel(week, ronde=ronde),
            f"bonus_rooster en toernooi_runner spellen week {week} ronde {ronde} gelijk",
            f"{bonus_rooster._cache_sleutel(week, ronde)} != {sleutel(week, ronde=ronde)}",
        )

# --- /locaties moet dezelfde ronde kunnen aanwijzen als /toernooi ---
# Zonder ronde-parameter gaf /locaties altijd de eindstand van de woensdagronde,
# ook in Week 6 waar de kaart de eindstand van de hele reeks moet laten zien.
import inspect
import main

# Sinds 30 september 2026 staan beide standaard op None, wat betekent: pak de
# laatst gedraaide ronde. Dat is geen cosmetische keuze. Draaide de docent zijn
# toernooi onder een ander rondenummer -- bijvoorbeeld ronde 5 -- dan startte
# elke student die zijn notebook uitvoerde een nieuw toernooi op de lege ronde 1
# en kreeg daar een timeout voor, terwijl de uitslag gewoon klaarstond. En de
# kaart in Werkcollege 8 bleef grijs om dezelfde reden.
params = inspect.signature(main.locaties).parameters
check("ronde" in params, "/locaties kent een ronde-parameter")
check(params["ronde"].default is None, "/locaties pakt standaard de laatste gedraaide ronde")
check(
    inspect.signature(main.toernooi).parameters["ronde"].default is None,
    "/toernooi staat op dezelfde standaard",
)
# In de neptafel-cache hierboven staan voor week 5 de rondes 1 en 2, en voor
# week 3 hetzelfde. laatste_gedraaide_ronde hoort dus de HOOGSTE te vinden, en
# voor een week waarin niets is gedraaid None terug te geven.
check(
    toernooi_runner.laatste_gedraaide_ronde(5) == 2,
    "laatste_gedraaide_ronde vindt de hoogste ronde die er is",
    f"kreeg {toernooi_runner.laatste_gedraaide_ronde(5)}",
)
check(
    toernooi_runner.laatste_gedraaide_ronde(1) is None,
    "en None voor een week die nooit gedraaid heeft",
    f"kreeg {toernooi_runner.laatste_gedraaide_ronde(1)}",
)

print(f"\n{geslaagd} checks geslaagd.")
