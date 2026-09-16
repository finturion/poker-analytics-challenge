"""
Doet de ijkbot mee, callt hij alles, en blijft hij van de bonus af?

De laatste vraag is de belangrijkste: hij speelt echt mee en beinvloedt de chips
aan tafel, maar hij mag geen enkele student een bonuspunt kosten.
"""
import json
import os
import sys
import tempfile

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WERKMAP = tempfile.mkdtemp(prefix="ijkbottest_")

TOKENS = {f"5000000{i:02d}": f"token{i}" for i in range(8)}
os.environ.pop("DATABASE_URL", None)
os.environ["POKER_TOKENS_JSON"] = json.dumps(TOKENS)
os.environ["POKER_DOCENT_TOKEN"] = "docent-testtoken"
os.chdir(WERKMAP)

sys.path.insert(0, os.path.join(WORTEL, "api"))
import database as db
from bonus_rooster import puntenverdeling
from poker_adapter import speel_toernooi
from toernooi_runner import IJKBOTS, OEFENBOTS

geslaagd, gezakt = 0, []


def check(naam, voorwaarde, detail=""):
    global geslaagd
    if voorwaarde:
        geslaagd += 1
        print(f"  ok   {naam}")
    else:
        gezakt.append(f"{naam} — {detail}")
        print(f"  FOUT {naam}  {detail}")


print("\n--- Er is precies één ijkbot, en die callt ---")
check("precies één ijkbot", len(IJKBOTS) == 1, sorted(IJKBOTS))
naam, functie = next(iter(IJKBOTS.items()))
check("zijn naam zegt wat hij doet", "callt" in naam.lower(), naam)
antwoorden = {functie(hand) for hand in (["A", "A"], ["7", "2"], ["K", "3"], ["10", "10"])}
check("hij callt ongeacht zijn kaarten", antwoorden == {"call"}, antwoorden)
check("hij is geen oefenbot", naam not in OEFENBOTS, "")

print("\n--- In een echt toernooi ---")
def tight(hand, stack):
    return "raise" if hand[0] == hand[1] else "fold"

bots = {f"5000000{i:02d}": {"kies_actie": tight, "strategie": None, "bluf_kans": None}
        for i in range(5)}
bots[naam] = {"kies_actie": functie, "strategie": None, "bluf_kans": None}

uit = speel_toernooi(bots, n_simulaties=2, n_handen=40, seed=9)
log = [r for r in uit["hand_log"] if r["bot_naam"] == naam]
acties = {r["actie"] for r in log if r["aan_zet"]}
check("hij speelt mee", len(log) > 0, len(log))
check("en kiest alleen call", acties == {"call"}, acties)
check("zijn eindstand staat in de uitslag", naam in uit["eindstand_per_bot"], "")

print("\n--- Maar hij pakt geen bonuspunten af ---")
# namen_deelnemers bevat alleen de studenten; de ijkbot hoort er niet in.
toernooi = {
    "eindstand_per_bot": {**uit["eindstand_per_bot"], naam: 9999},
    "namen_deelnemers": [b for b in bots if b != naam],
    "startstacks": None,
}
verdeling = puntenverdeling(toernooi)
check("de ijkbot komt niet in de puntenverdeling voor", naam not in verdeling, sorted(verdeling))
check("alle punten gaan naar studenten",
      set(verdeling) <= {b for b in bots if b != naam}, sorted(verdeling))
check("en er wordt wél uitgekeerd",
      sum(r["punten"] for r in verdeling.values()) > 0, verdeling)

print(f"\n{geslaagd} geslaagd, {len(gezakt)} gezakt")
for r in gezakt:
    print("   ", r)
sys.exit(1 if gezakt else 0)
