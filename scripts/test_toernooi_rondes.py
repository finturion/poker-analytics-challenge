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
from poker_adapter import STANDAARD_INITIAL_STACK, bereken_startstacks
from toernooi_runner import _cache_sleutel, draai_toernooi, haal_gecacht_resultaat_op

geslaagd = 0


def check(voorwaarde, omschrijving):
    global geslaagd
    assert voorwaarde, f"GEZAKT: {omschrijving}"
    geslaagd += 1
    print(f"  ok  {omschrijving}")


# ---------------------------------------------------------------------------
# 1. Cachesleutels
# ---------------------------------------------------------------------------
print("Cachesleutels")
check(_cache_sleutel(5) == "5", "ronde 1 houdt de oude sleutel '5'")
check(_cache_sleutel(5, 1) == "5_vs_1", "ronde 1 met vergelijking houdt '5_vs_1'")
check(_cache_sleutel(5, None, 2) == "5_ronde2", "ronde 2 krijgt een eigen sleutel")
check(_cache_sleutel(5, 1, 2) == "5_vs_1_ronde2", "ronde 2 met vergelijking ook")
check(
    _cache_sleutel(5, None, 1) != _cache_sleutel(5, None, 2),
    "ronde 1 en 2 botsen niet",
)

# ---------------------------------------------------------------------------
# 2. Startstacks: eindstand + 1000
# ---------------------------------------------------------------------------
print("\nStartstacks")
eind = {"tight": 1110.0, "loose": 1083.3, "stub": 700.0}
stacks = bereken_startstacks(eind)
check(stacks["tight"] == 1110 + STANDAARD_INITIAL_STACK, "winnaar neemt zijn winst mee")
check(stacks["stub"] == 700 + STANDAARD_INITIAL_STACK, "verliezer neemt zijn verlies mee")
check(
    stacks["tight"] - stacks["stub"] == 410,
    "het verschil van ronde 1 blijft precies staan",
)
check(all(isinstance(v, int) for v in stacks.values()), "stacks zijn hele chips")

# ---------------------------------------------------------------------------
# 3. Twee rondes achter elkaar, met een neptafel-cache
# ---------------------------------------------------------------------------
print("\nTwee rondes achter elkaar")


def tight(hand, stack, ronde, strategie, bluf_kans):
    return "raise" if hand[0] in ("A", "K", "Q") else "fold"


def loose(hand, stack, ronde, strategie, bluf_kans):
    return "call"


def stub(hand, stack, ronde, strategie, bluf_kans):
    return "fold"


nep_cache = {}
toernooi_runner.db.laad_toernooi_resultaten = lambda: nep_cache
toernooi_runner.db.sla_toernooi_resultaten_op = lambda d: nep_cache.update(d)
toernooi_runner._verzamel_bots_over_weken = lambda week, vergelijk: (
    {
        naam: {"kies_actie": fn, "strategie": "tight", "bluf_kans": 0.1}
        for naam, fn in [("tight", tight), ("loose", loose), ("stub", stub)]
    },
    ["tight", "loose", "stub"],
)

ronde1 = draai_toernooi(5, n_simulaties=2, n_handen=20, ronde=1)
ronde2 = draai_toernooi(5, n_simulaties=2, n_handen=20, ronde=2)

check(ronde1["startstacks"] is None, "ronde 1 start zonder startstacks")
check(ronde2["startstacks"] is not None, "ronde 2 krijgt startstacks mee")
check(
    ronde2["startstacks"] == bereken_startstacks(ronde1["eindstand_per_bot"]),
    "die startstacks komen uit de eindstand van ronde 1",
)
check(
    "5" in nep_cache and "5_ronde2" in nep_cache,
    "beide rondes staan naast elkaar in de cache",
)
check(
    haal_gecacht_resultaat_op(5, ronde=1)["eindstand_per_bot"] == ronde1["eindstand_per_bot"],
    "de woensdaguitslag is na ronde 2 nog steeds op te halen",
)
check(
    haal_gecacht_resultaat_op(5, ronde=3)["gedraaid"] is False,
    "een ronde die nog niet gedraaid is meldt dat netjes",
)

chips_in = sum(ronde2["startstacks"].values())
chips_uit = sum(ronde2["eindstand_per_bot"].values())
check(
    abs(chips_in - chips_uit) < 1e-6,
    f"chips blijven behouden in ronde 2 ({chips_in} in, {chips_uit} uit)",
)

# ---------------------------------------------------------------------------
# 3b. De formatieve donderdagronde: een repetitie die niets verschuift
# ---------------------------------------------------------------------------
print("\nFormatieve ronde")
from toernooi_runner import _cache_sleutel as sleutel

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

print(f"\n{geslaagd} checks geslaagd.")
