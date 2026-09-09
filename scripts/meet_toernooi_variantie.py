"""
Meet hoeveel van de toernooi-uitslag skill is en hoeveel toeval.

Waarom dit script bestaat: de bonus hangt aan je plek in de eindstand (1e 0,5,
2e 0,4, ... 5e 0,1). Dan moet je weten of die plek iets meet. Dit script zet een
veld van 44 bots neer met bekende kwaliteit -- de drempel waarboven ze raisen is
de enige knop, dus een lage drempel is objectief een slechtere bot -- en draait
hetzelfde veld met verschillende seeds.

Twee dingen om naar te kijken:

1. Komt de top 5 uit de goede bots? Dat is de vraag die telt. Als de vijf
   prijzen bij tight bots terechtkomen, belóónt de ladder skill, ook als de
   volgorde binnen die groep toeval is.
2. Is het dezelfde top 5 bij een andere seed? Dat wordt hij niet, en dat is geen
   meetfout die je wegsimuleert: bots van gelijke sterkte liggen dichter bij
   elkaar dan de ruis van 50 handen aan een tafel van zes.

Draaien:  python3 scripts/meet_toernooi_variantie.py
Dit kost een paar minuten -- het speelt honderdduizenden handen poker.
"""
import collections
import json
import os
import statistics
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "api"))

from bonus_rooster import PUNTEN_PER_PLEK, punten_voor_plek
from poker_adapter import speel_toernooi
from toernooi_runner import N_SIMULATIES_BONUSWEEK, STANDAARD_N_SIMULATIES

RANG = {"A": 14, "K": 13, "Q": 12, "J": 11, "T": 10, "9": 9, "8": 8,
        "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}
SEEDS = [51, 52, 53, 54, 55]
AANTAL_BOTS = 44
DREMPELS = 12  # 12 kwaliteitsklassen, dus ~4 bots per klasse


def maak_bot(drempel):
    """Een bot met precies één knop: raise vanaf `drempel`. Hoger = tighter = beter."""
    def kies_actie(hand, stack, ronde, strategie, bluf_kans):
        if stack < 150:
            return "all_in"
        waarde = max(RANG.get(hand[0], 2), RANG.get(hand[1], 2))
        if hand[0] == hand[1]:
            waarde += 4
        if waarde >= drempel:
            return "raise"
        return "call" if waarde >= drempel - 3 else "fold"
    return kies_actie


def bouw_veld():
    """44 bots, 12 kwaliteitsklassen, klasse in de naam zodat je 'm terugziet."""
    veld = {}
    for i in range(AANTAL_BOTS):
        drempel = 15 - (i % DREMPELS)
        veld[f"bot{i:02d}_drempel{drempel:02d}"] = {
            "kies_actie": maak_bot(drempel), "strategie": "tight", "bluf_kans": 0.1,
        }
    return veld


def drempel_van(naam):
    return int(naam.split("drempel")[1])


def draai(veld, n_simulaties, seed):
    uitslag = speel_toernooi(veld, n_simulaties=n_simulaties, n_handen=50, seed=seed)
    return sorted(uitslag["eindstand_per_bot"], key=lambda n: -uitslag["eindstand_per_bot"][n])


def rapporteer(n_simulaties, veld):
    print(f"\n{'=' * 78}")
    print(f"{n_simulaties} simulaties x 50 handen  ({n_simulaties * 50} handen per bot), {len(SEEDS)} seeds")
    print("=" * 78)

    ranglijsten = []
    for seed in SEEDS:
        t0 = time.time()
        ranglijsten.append(draai(veld, n_simulaties, seed))
        print(f"  seed {seed} gedraaid in {time.time() - t0:.0f}s")

    print(f"\n  De top 5 per seed (drempel tussen haakjes; 15 = tightst, 4 = wildst):")
    for seed, ranglijst in zip(SEEDS, ranglijsten):
        top = "  ".join(f"{drempel_van(n):>2}" for n in ranglijst[:5])
        print(f"    seed {seed}:  {top}")

    alle_drempels = sorted({drempel_van(n) for n in veld}, reverse=True)
    mediaan = statistics.median(alle_drempels)

    print(f"\n  {'drempel':>9}{'bots':>6}{'keer in de top 5':>19}{'punten totaal':>16}{'per bot':>10}")
    in_top5 = collections.Counter()
    punten = collections.Counter()
    for ranglijst in ranglijsten:
        for plek, naam in enumerate(ranglijst[:len(PUNTEN_PER_PLEK)], start=1):
            in_top5[drempel_van(naam)] += 1
            punten[drempel_van(naam)] += punten_voor_plek(plek)
    for drempel in alle_drempels:
        n_bots = sum(1 for n in veld if drempel_van(n) == drempel)
        print(f"  {drempel:>9}{n_bots:>6}{in_top5[drempel]:>19}{punten[drempel]:>16.1f}"
              f"{punten[drempel] / n_bots:>10.2f}")

    boven = sum(p for d, p in punten.items() if d > mediaan)
    onder = sum(p for d, p in punten.items() if d < mediaan)
    totaal = sum(punten.values())
    print(f"\n  Naar de betere helft van het veld : {boven:.1f} van {totaal:.1f} punt ({100 * boven / totaal:.0f}%)")
    print(f"  Naar de slechtere helft           : {onder:.1f} van {totaal:.1f} punt ({100 * onder / totaal:.0f}%)")

    overlappen = [
        len(set(a[:5]) & set(b[:5]))
        for i, a in enumerate(ranglijsten) for b in ranglijsten[i + 1:]
    ]
    print(f"  Dezelfde namen in de top 5 bij twee seeds: gemiddeld {statistics.mean(overlappen):.1f} van 5")

    # Wat de opzet kost aan data: het hand-log gaat mee in de API-respons en
    # wordt door studenten in een DataFrame gezet.
    uitslag = speel_toernooi(veld, n_simulaties=n_simulaties, n_handen=50, seed=SEEDS[0])
    regels = len(uitslag["hand_log"])
    print(f"  Hand-log: {regels:,} regels, {len(json.dumps(uitslag)) / 1e6:.1f} MB, "
          f"{regels // len(veld):,} regels per student")


if __name__ == "__main__":
    veld = bouw_veld()
    for n_simulaties in (STANDAARD_N_SIMULATIES, N_SIMULATIES_BONUSWEEK):
        rapporteer(n_simulaties, veld)
