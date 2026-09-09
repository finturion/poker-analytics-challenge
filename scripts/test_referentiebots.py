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
import random
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

# De bots zitten nu in een pakket met een `module` per bot in plaats van een losse
# functie; deze helper houdt de rest van het script gelijk.
for _info in REFERENTIEBOTS.values():
    _info.setdefault("kies_actie", _info["module"].kies_actie)

TOEGESTANE_PARAMETERS = {"hand", "stack", "ronde", "pot", "inzet_om_te_callen",
                         "tegenstander_acties_deze_hand", "strategie", "bluf_kans"}
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88]
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
print("0. Kopieën in api/ gelijk aan de werkplaats in mijn_bots/\n")
# render.yaml deployt met rootDir: api, dus alleen api/ komt op de server. De
# originelen in mijn_bots/ zijn de werkplaats. Lopen die twee uit elkaar, dan
# werkt het lokaal en niet in productie -- de ergste soort verschil.
WERKPLAATS = os.path.join(os.path.dirname(HIER), "mijn_bots")
PAKKET = os.path.join(os.path.dirname(HIER), "api", "referentiebots")
for naam, info in sorted(REFERENTIEBOTS.items()):
    bestand = os.path.basename(info["module"].__file__)
    origineel = os.path.join(WERKPLAATS, bestand)
    kopie = os.path.join(PAKKET, bestand)
    if not os.path.exists(origineel):
        check(True, f"{bestand}: geen origineel in mijn_bots/ (alleen in api/) — prima")
        continue
    with open(origineel, "rb") as a, open(kopie, "rb") as b:
        check(a.read() == b.read(), f"{bestand}: api/-kopie is gelijk aan mijn_bots/")

print("\n1. Parameternamen — de stille killer\n")
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
check(niveaus == sorted(niveaus), f"de niveaus zijn oplopend gesorteerd: {niveaus}")
check(min(niveaus) == 1 and set(niveaus) == set(range(1, max(niveaus) + 1)),
      f"de niveaus zijn 1 t/m {max(niveaus)} zonder gaten")
check(all(r["beschrijving"].strip() for r in beschrijvingen(5)), "elke bot heeft een beschrijving")
check(broncode(3) is None, "in week 3 is de broncode nog niet openbaar")
check(broncode(OPENBAAR_VANAF_WEEK) is not None, f"vanaf week {OPENBAAR_VANAF_WEEK} wel")

# ---------------------------------------------------------------------------
print(f"\n4. Lopen de niveaus op in het veld dat er echt komt? "
      f"({len(SEEDS)} seeds x {N_SIMULATIES} simulaties)\n")

# Meten tegen 44 studentachtige bots, niet tegen elkaar. Dat is geen detail: in
# een veld met alleen deze vijf en twee andere bots was PotOdds de zwakste van
# allemaal, en hier is hij dat niet. Een niveau is een eigenschap van een bot
# TUSSEN ANDEREN, en het veld dat telt is een klas van 44.
RANG = {"A": 14, "K": 13, "Q": 12, "J": 11, "10": 10, "9": 9, "8": 8,
        "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}


def maak_studentbot(drempel, groot_vanaf, allin_onder):
    def kies_actie(hand, stack, ronde, strategie, bluf_kans):
        if allin_onder and stack < allin_onder:
            return "all_in"
        waarde = max(RANG[hand[0]], RANG[hand[1]]) + (4 if hand[0] == hand[1] else 0)
        if waarde >= drempel:
            if groot_vanaf and waarde >= groot_vanaf:
                return "grote_raise"
            return "raise"
        return "call" if waarde >= drempel - 3 else "fold"
    return kies_actie


rng = random.Random(2)
veld = {}
for i in range(44):
    drempel = rng.choice([6, 8, 9, 10, 11, 11, 12, 12, 13, 13, 14, 15])
    veld[f"_student_{i:02d}"] = {
        "kies_actie": maak_studentbot(drempel,
                                      drempel + 3 if rng.random() < 0.4 else None,
                                      150 if rng.random() < 0.5 else 0),
        "strategie": rng.choice(["tight", "loose", "balanced", "aggressive"]),
        "bluf_kans": round(rng.uniform(0, 0.4), 2),
    }
veld.update(referentiebots_voor(WEKEN_MET_REFERENTIEBOTS[-1]))

per_bot = {}
for seed in SEEDS:
    uitslag = speel_toernooi(veld, n_simulaties=N_SIMULATIES, n_handen=50, seed=seed)
    for naam, stand in uitslag["eindstand_per_bot"].items():
        per_bot.setdefault(naam, []).append(stand)

gemiddeld = {naam: statistics.mean(per_bot[naam]) for naam in REFERENTIEBOTS}
fouten = {naam: statistics.stdev(per_bot[naam]) / len(per_bot[naam]) ** 0.5
          for naam in REFERENTIEBOTS}
studenten = sorted(statistics.mean(v) for n, v in per_bot.items() if n.startswith("_student_"))
volgorde = sorted(per_bot, key=lambda n: -statistics.mean(per_bot[n]))

print(f"  {'bot':26}{'niveau':>7}{'gemiddeld':>11}{'± se':>7}{'plek':>13}")
for naam in sorted(REFERENTIEBOTS, key=lambda n: (REFERENTIEBOTS[n]["niveau"], n)):
    print(f"  {naam:26}{REFERENTIEBOTS[naam]['niveau']:>7}{gemiddeld[naam]:>11.0f}"
          f"{fouten[naam]:>7.0f}{volgorde.index(naam) + 1:>9} /{len(volgorde):>3}")
print(f"\n  studenten in dit testveld: mediaan {statistics.median(studenten):.0f}, "
      f"laagste {studenten[0]:.0f}, hoogste {studenten[-1]:.0f}")

# Groepen vergelijken, niet losse bots: bots met hetzelfde niveau horen niet
# onderscheidbaar te zijn, en opeenvolgende niveaus juist wel.
groepen = {}
for naam, info in REFERENTIEBOTS.items():
    groepen.setdefault(info["niveau"], []).append(naam)

print()
for niveau, namen in sorted(groepen.items()):
    if len(namen) < 2:
        continue
    waarden = [gemiddeld[n] for n in namen]
    grootste = max(abs(a - b) for a in waarden for b in waarden)
    se = max(fouten[n] for n in namen)
    check(grootste <= 2 * se,
          f"niveau {niveau} bevat {len(namen)} bots die elkaars gelijke zijn "
          f"(grootste verschil {grootste:.0f}, 2×se {2 * se:.0f})")

for lager, hoger in zip(sorted(groepen), sorted(groepen)[1:]):
    a = statistics.mean(gemiddeld[n] for n in groepen[lager])
    b = statistics.mean(gemiddeld[n] for n in groepen[hoger])
    se = max(max(fouten[n] for n in groepen[lager]), max(fouten[n] for n in groepen[hoger]))
    check(b - a > 2 * se,
          f"niveau {hoger} ligt aantoonbaar boven niveau {lager} "
          f"({b - a:+.0f}, 2×se {2 * se:.0f})")

print(f"\n{geslaagd} checks geslaagd" + (f", {len(problemen)} MISLUKT:" if problemen else "."))
for p in problemen:
    print(f"  - {p}")
sys.exit(1 if problemen else 0)
