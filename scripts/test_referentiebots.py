"""
Controleert de referentiebots, en meet of hun niveaus echt oplopen.

Drie dingen, in deze volgorde:

1. **Doen ze het technisch goed?** De engine kiest zijn argumenten op
   PARAMETERNAAM. Noem je een parameter anders dan hand/stack/ronde/pot/
   inzet_om_te_callen/tegenstander_acties_deze_hand/strategie/bluf_kans, dan
   wordt je functie zonder argumenten aangeroepen, crasht hij, en foldt de bot
   stil élke hand. Dat is de meest kostbare stille fout in dit project en de
   enige manier om hem te vinden is ernaar kijken.

2. **Geven ze geldige acties terug?** Alleen wat de validator per week toestaat.

3. **Lopen de niveaus op?** Dit is de reden dat dit script bestaat. Bij 500 tot
   800 chips ruis op één bot is "deze is beter dan die" geen bewering die je op
   gevoel kunt doen. Het script draait ze tegen elkaar over meerdere seeds en
   meldt het als de gemeten orde niet klopt met het opgegeven `niveau`.

Draaien:  python3 scripts/test_referentiebots.py

Let op: met de PLAATSHOUDERS in referentiebots.py faalt check 4 met opzet -- die
twee liggen te dicht bij elkaar. Dat is precies wat dit script hoort te melden.
"""
import inspect
import os
import statistics
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "api"))

from bot_validator import (TOEGESTANE_ACTIES, TOEGESTANE_ACTIES_MET_SIZING,
                           VERWACHTE_FUNCTIES)
from poker_adapter import speel_toernooi
from referentiebots import (OPENBAAR_VANAF_WEEK, REFERENTIEBOTS,
                            WEKEN_MET_REFERENTIEBOTS, beschrijvingen,
                            broncode, referentiebots_voor)

TOEGESTANE_PARAMETERS = {"hand", "stack", "ronde", "pot", "inzet_om_te_callen",
                         "tegenstander_acties_deze_hand", "strategie", "bluf_kans"}
SEEDS = [51, 52, 53, 54, 55]
N_SIMULATIES = 20

geslaagd = 0
problemen = []


def check(voorwaarde, omschrijving):
    global geslaagd
    if voorwaarde:
        geslaagd += 1
        print(f"  ok  {omschrijving}")
    else:
        problemen.append(omschrijving)
        print(f"  XX  {omschrijving}")


# ---------------------------------------------------------------------------
print("1. Parameternamen — de stille killer\n")
for naam, info in sorted(REFERENTIEBOTS.items()):
    parameters = set(inspect.signature(info["kies_actie"]).parameters)
    onbekend = parameters - TOEGESTANE_PARAMETERS
    check(not onbekend, f"{naam}: alle parameters worden door de engine gevuld"
                        + (f" — ONBEKEND: {sorted(onbekend)}" if onbekend else ""))
    check("hand" in parameters, f"{naam}: heeft in elk geval `hand`")

print("\n2. Geldige acties op een setje situaties\n")
SITUATIES = [
    {"hand": ["A", "A"], "stack": 1000, "ronde": "preflop", "pot": 30, "inzet_om_te_callen": 20},
    {"hand": ["7", "2"], "stack": 1000, "ronde": "river", "pot": 400, "inzet_om_te_callen": 200},
    {"hand": ["A", "10"], "stack": 40, "ronde": "flop", "pot": 100, "inzet_om_te_callen": 100},
    {"hand": ["10", "10"], "stack": 1000, "ronde": "turn", "pot": 0, "inzet_om_te_callen": 0},
]
for naam, info in sorted(REFERENTIEBOTS.items()):
    functie = info["kies_actie"]
    parameters = set(inspect.signature(functie).parameters)
    acties = []
    gecrasht = None
    for situatie in SITUATIES:
        argumenten = {k: v for k, v in situatie.items() if k in parameters}
        if "strategie" in parameters:
            argumenten["strategie"] = info["strategie"]
        if "bluf_kans" in parameters:
            argumenten["bluf_kans"] = info["bluf_kans"]
        try:
            acties.append(functie(**argumenten))
        except Exception as e:
            gecrasht = f"{type(e).__name__}: {e}"
            break
    check(gecrasht is None, f"{naam}: crasht niet" + (f" — {gecrasht}" if gecrasht else ""))
    if gecrasht is None:
        ongeldig = [a for a in acties if not isinstance(a, str) or a.lower() not in TOEGESTANE_ACTIES_MET_SIZING]
        check(not ongeldig, f"{naam}: geeft alleen geldige acties terug"
                            + (f" — ONGELDIG: {ongeldig}" if ongeldig else ""))
        check(len(set(acties)) > 1 or naam.endswith("Voorzichtig"),
              f"{naam}: reageert verschillend op verschillende situaties")

print("\n3. Opzet en zichtbaarheid\n")
check(set(REFERENTIEBOTS) == set(referentiebots_voor(WEKEN_MET_REFERENTIEBOTS[0])),
      f"alle bots spelen mee in week {WEKEN_MET_REFERENTIEBOTS[0]}")
check(referentiebots_voor(1) == {}, "in week 1 spelen ze niet mee")
niveaus = [r["niveau"] for r in beschrijvingen(WEKEN_MET_REFERENTIEBOTS[-1])]
check(len(niveaus) == len(set(niveaus)), f"elk niveau komt één keer voor: {niveaus}")
check(all(r["beschrijving"].strip() for r in beschrijvingen(5)), "elke bot heeft een beschrijving")
check(broncode(3) is None, "in week 3 is de broncode nog niet openbaar")
check(broncode(OPENBAAR_VANAF_WEEK) is not None, f"vanaf week {OPENBAAR_VANAF_WEEK} wel")

# ---------------------------------------------------------------------------
print(f"\n4. Lopen de niveaus op? ({len(SEEDS)} seeds x {N_SIMULATIES} simulaties)\n")
if len(REFERENTIEBOTS) < 2:
    print("  (minder dan twee bots — niets te vergelijken)")
else:
    veld = referentiebots_voor(WEKEN_MET_REFERENTIEBOTS[-1])
    # aanvullen tot een realistische tafel, anders spelen ze alleen tegen elkaar
    RANG = {"A": 14, "K": 13, "Q": 12, "J": 11, "10": 10, "9": 9, "8": 8,
            "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}

    def maak_vulbot(drempel):
        def kies_actie(hand, stack, ronde):
            waarde = max(RANG[hand[0]], RANG[hand[1]]) + (4 if hand[0] == hand[1] else 0)
            return "raise" if waarde >= drempel else ("call" if waarde >= drempel - 3 else "fold")
        return kies_actie

    for i in range(12):
        veld[f"_vulbot_{i}"] = {"kies_actie": maak_vulbot(15 - (i % 8)),
                                "strategie": "tight", "bluf_kans": 0.1}

    per_bot = {}
    for seed in SEEDS:
        uitslag = speel_toernooi(veld, n_simulaties=N_SIMULATIES, n_handen=50, seed=seed)
        for naam in REFERENTIEBOTS:
            per_bot.setdefault(naam, []).append(uitslag["eindstand_per_bot"][naam])

    gemiddeld = {naam: statistics.mean(v) for naam, v in per_bot.items()}
    ruis = statistics.mean(max(v) - min(v) for v in per_bot.values())

    print(f"  {'bot':26}{'niveau':>8}{'eindstand':>12}{'spreiding':>12}")
    op_niveau = sorted(REFERENTIEBOTS, key=lambda n: REFERENTIEBOTS[n]["niveau"])
    for naam in op_niveau:
        v = per_bot[naam]
        print(f"  {naam:26}{REFERENTIEBOTS[naam]['niveau']:>8}{gemiddeld[naam]:>12.0f}"
              f"{max(v) - min(v):>12.0f}")
    print(f"\n  gemiddelde ruis binnen één bot: {ruis:.0f} chips")

    verwacht = op_niveau
    gemeten = sorted(REFERENTIEBOTS, key=lambda n: gemiddeld[n])
    check(verwacht == gemeten,
          "de gemeten orde klopt met de opgegeven niveaus"
          + ("" if verwacht == gemeten else f" — gemeten: {gemeten}"))

    verschillen = [(a, b, gemiddeld[b] - gemiddeld[a])
                   for a, b in zip(op_niveau, op_niveau[1:])]
    krap = [(a, b, d) for a, b, d in verschillen if d <= ruis / 2]
    check(not krap,
          f"elk niveau ligt duidelijk boven het vorige (drempel: halve ruis = {ruis / 2:.0f} chips)")
    for a, b, d in krap:
        print(f"      {a} en {b} verschillen maar {d:.0f} chips — dat is te weinig om")
        print(f"      betrouwbaar te scheiden. Zet ze verder uit elkaar, of voeg ze samen:")
        print(f"      twee niveaus die niemand kan onderscheiden zijn één niveau.")

print(f"\n{geslaagd} checks geslaagd" + (f", {len(problemen)} MISLUKT:" if problemen else "."))
for p in problemen:
    print(f"  - {p}")
sys.exit(1 if problemen else 0)
