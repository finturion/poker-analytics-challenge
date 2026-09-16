"""
Kan een ingeleverde bot de winkans mét bord uitrekenen?

Loopt de hele keten langs: de validator keurt zo'n bot goed, het toernooi laat
hem echt spelen, en de twee kopieen van schat_winkans geven hetzelfde antwoord.
"""
import os
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "api"))
sys.path.insert(0, os.path.join(WORTEL, "notebooks"))

geslaagd, gezakt = 0, []


def check(naam, voorwaarde, detail=""):
    global geslaagd
    if voorwaarde:
        geslaagd += 1
        print(f"  ok   {naam}")
    else:
        gezakt.append(f"{naam} — {detail}")
        print(f"  FOUT {naam}  {detail}")


# --- 1. De twee kopieen mogen niet uit elkaar lopen -------------------------
# Studenten rekenen in hun notebook met de ene en hun bot speelt met de andere.
# Geven die verschillende antwoorden, dan klopt hun tabel niet met hun spel.
print("\n--- De twee kopieen van schat_winkans ---")
from winkans import schat_winkans as op_de_server
from _hulpfuncties_week3 import schat_winkans as in_het_notebook

gevallen = [
    (["A", "A"], None, 5),
    (["7", "2"], None, 5),
    (["SA", "HA"], ["DA", "C7", "S2"], 3),
    (["S7", "S8"], ["S2", "S9", "DK"], 3),
    (["S7", "S8"], ["S2", "S9", "DK", "ST", "C4"], 3),
]
for hand, bord, tegen in gevallen:
    a = op_de_server(hand, bord=bord, simulaties=300, seed=7, tegenstanders=tegen)
    b = in_het_notebook(hand, bord=bord, simulaties=300, seed=7, tegenstanders=tegen)
    check(f"zelfde antwoord voor {hand} op {bord}", a == b, f"server {a} vs notebook {b}")

# --- 2. De kleur telt echt mee ---------------------------------------------
print("\n--- Telt de kleur mee? ---")
bord = ["S2", "S9", "DK"]
met = op_de_server(["S7", "S8"], bord=bord, simulaties=1200, seed=2, tegenstanders=3)
zonder = op_de_server(["H7", "C8"], bord=bord, simulaties=1200, seed=2, tegenstanders=3)
check("een flushdraw is duidelijk meer waard", met > zonder + 15, f"{met}% tegen {zonder}%")

try:
    op_de_server(["7", "8"], bord=bord, tegenstanders=3)
    check("zonder kleur mét bord wordt geweigerd", False, "kwam er doorheen")
except ValueError as e:
    check("zonder kleur mét bord wordt geweigerd", "kleuren" in str(e), str(e)[:60])

check("zonder bord mag het nog steeds zonder kleur",
      isinstance(op_de_server(["A", "K"], simulaties=200, seed=1), float), "")

# --- 3. De validator keurt zo'n bot goed ------------------------------------
print("\n--- De validator ---")
from bot_validator import valideer_bot_code

BOT = '''
def kies_actie(hand, hand_met_kleur, bord, stack, strategie, bluf_kans, pot, inzet_om_te_callen):
    if bord:
        kans = schat_winkans(hand_met_kleur, bord=bord, simulaties=60, tegenstanders=3)
    else:
        kans = schat_winkans(hand, simulaties=60, tegenstanders=3)
    nodig = 100 * inzet_om_te_callen / (pot + inzet_om_te_callen) if (pot + inzet_om_te_callen) else 0
    if kans < nodig:
        return "fold"
    return "raise" if kans > 70 else "call"
'''
r = valideer_bot_code(BOT, 5, strategie="tight", bluf_kans=0.3)
check("een bot die schat_winkans aanroept wordt goedgekeurd", r["geldig"] is True,
      (r["foutmelding"] or "")[:140])
check("hij is op meerdere straten getest", r["actie_resultaten"] and len(r["actie_resultaten"]) >= 9,
      len(r["actie_resultaten"] or []))

# Een bot die het preflop-geval vergeet hoort te struikelen, want preflop is het
# bord leeg en dan weigert schat_winkans een hand zonder kleur... of juist mét.
VERGEET = BOT.replace(
    "    if bord:\n        kans = schat_winkans(hand_met_kleur, bord=bord, simulaties=60, tegenstanders=3)\n"
    "    else:\n        kans = schat_winkans(hand, simulaties=60, tegenstanders=3)\n",
    "    kans = schat_winkans(hand, bord=bord, simulaties=60, tegenstanders=3)\n")
r2 = valideer_bot_code(VERGEET, 5, strategie="tight", bluf_kans=0.3)
check("een bot die kleur en bord door elkaar haalt wordt afgekeurd", r2["geldig"] is False, r2)
check("met een melding waar 'kleur' in staat", "kleur" in (r2["foutmelding"] or ""),
      (r2["foutmelding"] or "")[:140])

# --- 4. En hij speelt echt mee in een toernooi ------------------------------
print("\n--- In een echt toernooi ---")
from toernooi_runner import _laad_kies_actie
from poker_adapter import speel_toernooi

kies_actie = _laad_kies_actie(BOT)
check("de bot laadt met schat_winkans in zijn naamruimte", callable(kies_actie), "")

def simpel(hand, stack):
    return "call" if hand[0] == hand[1] else "fold"

bots = {"bordbot": {"kies_actie": kies_actie, "strategie": "tight", "bluf_kans": 0.3}}
for i in range(3):
    bots[f"bot{i}"] = {"kies_actie": simpel, "strategie": "tight", "bluf_kans": 0.2}

uit = speel_toernooi(bots, n_simulaties=1, n_handen=30, seed=21)
log = [r for r in uit["hand_log"] if r["bot_naam"] == "bordbot"]
gekozen = {r["actie"] for r in log if r["aan_zet"]}
check("hij speelt en kiest meer dan alleen fold", gekozen - {"fold", None}, gekozen)
check("zijn stack is veranderd", uit["eindstand_per_bot"]["bordbot"] != 1000,
      uit["eindstand_per_bot"]["bordbot"])

print(f"\n{geslaagd} geslaagd, {len(gezakt)} gezakt")
for r in gezakt:
    print("   ", r)
sys.exit(1 if gezakt else 0)
