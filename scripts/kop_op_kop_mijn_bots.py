"""
Elke bot uit mijn_bots/ één-tegen-één tegen elke andere.

Waarom apart van vergelijk_mijn_bots.py: aan een volle tafel gaat een groot
deel van je resultaat over wie er tóevallig ook nog in de hand zat. Kop-op-kop
speel je élke hand, is de pot altijd van jullie samen, en werkt een bluf al als
één speler foldt. Dat is de enige eerlijke test voor een bot die van een
uitbuit-idee leeft: bot_uitbuiter rekent voor dat stelen tegen één speler loont
vanaf een pot van 133 en tegen drie vrijwel nooit, dus aan een tafel van zeven
komt hij bijna niet aan zijn eigen hoofdlijn toe.

Kop-op-kop is 2 x 1000 chips, dus het gemiddelde is 1000: boven de 1000 heb je
van die tegenstander gewonnen. Per paar wordt hetzelfde aantal tafels gespeeld
als in het hoofdscript, en de onzekerheid staat erbij -- zonder dat getal is
een verschil van 100 chips niets.

Draaien:  python3 scripts/kop_op_kop_mijn_bots.py
Kost een paar minuten (21 paren x SEEDS x N_SIMULATIES tafels).
"""
import itertools
import os
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(PROJECT, "api"))
sys.path.insert(0, os.path.join(PROJECT, "mijn_bots"))

from poker_adapter import STANDAARD_INITIAL_STACK, speel_toernooi

sys.path.insert(0, HIER)
from vergelijk_mijn_bots import N_HANDEN, VELD, eindstanden_per_tafel, kop

SEEDS = [51, 52, 53, 54, 55, 56]
N_SIMULATIES = 20


def speel_paar(naam_a, naam_b):
    """Alle SEEDS x N_SIMULATIES tafels voor dit ene paar, als DataFrame."""
    bots = {
        naam: {"kies_actie": VELD[naam]["module"].kies_actie,
               "strategie": VELD[naam]["strategie"], "bluf_kans": VELD[naam]["bluf_kans"]}
        for naam in (naam_a, naam_b)
    }
    logs = []
    for seed in SEEDS:
        uitslag = speel_toernooi(bots, n_simulaties=N_SIMULATIES, n_handen=N_HANDEN, seed=seed)
        frame = pd.DataFrame(uitslag["hand_log"])
        frame["seed"] = seed
        logs.append(frame)
    return pd.concat(logs, ignore_index=True)


def main():
    namen = list(VELD)
    kop(f"Kop-op-kop: {len(namen)} bots, {len(namen) * (len(namen) - 1) // 2} paren, "
        f"{len(SEEDS) * N_SIMULATIES} tafels per paar")
    print(f"  {N_HANDEN} handen per tafel, 2 x {STANDAARD_INITIAL_STACK} chips, "
          f"dus 1000 is gelijkspel.\n")

    resultaten = {}
    for naam_a, naam_b in itertools.combinations(namen, 2):
        start = time.time()
        eindstanden = eindstanden_per_tafel(speel_paar(naam_a, naam_b))
        tafels = eindstanden.pivot_table(index=["seed", "simulatie"],
                                         columns="bot_naam", values="stack")
        verschil = tafels[naam_a] - tafels[naam_b]
        fout = verschil.std() / (len(tafels) ** 0.5)
        resultaten[(naam_a, naam_b)] = (verschil.mean(), fout)
        print(f"  {naam_a:>13} vs {naam_b:<13} {verschil.mean():>+7.0f} "
              f"+/- {1.96 * fout:>4.0f}   ({time.time() - start:.0f}s)")

    print("\n  Matrix: gemiddelde chips die de RIJ-bot van de KOLOM-bot afpakt.")
    print("  Een getal is pas iets als het buiten zijn eigen interval hierboven valt.\n")
    print("               " + "".join(f"{n[:11]:>13}" for n in namen))
    for rij in namen:
        cellen = []
        for kolom in namen:
            if rij == kolom:
                cellen.append(f"{'-':>13}")
            elif (rij, kolom) in resultaten:
                cellen.append(f"{resultaten[(rij, kolom)][0]:>+13.0f}")
            else:
                cellen.append(f"{-resultaten[(kolom, rij)][0]:>+13.0f}")
        print(f"  {rij[:11]:<11}" + "".join(cellen))

    print("\n  Gemiddelde over al zijn tegenstanders (hoe goed is deze bot kop-op-kop?):")
    totalen = {}
    for naam in namen:
        punten = [resultaten[(naam, k)][0] if (naam, k) in resultaten
                  else -resultaten[(k, naam)][0] for k in namen if k != naam]
        totalen[naam] = sum(punten) / len(punten)
    for naam, waarde in sorted(totalen.items(), key=lambda p: -p[1]):
        print(f"    {naam:<14}{waarde:>+8.0f}")


if __name__ == "__main__":
    main()
