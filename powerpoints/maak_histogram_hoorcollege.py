"""
Tekent de verdeling van de eindstanden voor het hoorcollege.

    python3 powerpoints/maak_histogram_hoorcollege.py uitslag.json

Schrijft powerpoints/plots_week3/eindstanden_histogram.png. vul_hoorcollege_aan.py
zet die plaat op de dia zodra hij bestaat.

Waarom de eindstanden en niet de winst per hand: de winst per hand is voor 92%
een blind van 10 of 20 chips, dus je krijgt één balk rond nul en verder wit. Die
verdeling staat als tabel op de dia ervoor, waar hij leesbaar is. Getekend is de
eindstand het verhaal: 27 bots, iedereen begon op 1000, en dan zie je in één blik
waar ze zijn geëindigd.

Geen tekst in de plaat. Wat erover gezegd moet worden staat in de notities van de
dia, en een bijschrift dat niet meebeweegt met een nieuwe ronde gaat vroeg of laat
iets beweren wat niet meer klopt.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from toernooicijfers import STARTSTACK

HIER = os.path.dirname(os.path.abspath(__file__))
UITVOER = os.path.join(HIER, "plots_week3", "eindstanden_histogram.png")

VILT = "#1B4D3E"
INKT = "#121E31"
GEDEMPT = "#5A646B"
BAKJE = 100


def teken(eindstanden, pad=UITVOER):
    waarden = np.asarray(sorted(eindstanden), dtype=float)
    laag = np.floor(waarden.min() / BAKJE) * BAKJE
    hoog = np.ceil(waarden.max() / BAKJE) * BAKJE
    randen = np.arange(laag, hoog + BAKJE, BAKJE)

    fig, ax = plt.subplots(figsize=(9.2, 4.3), dpi=200)
    ax.hist(waarden, bins=randen, color=VILT, edgecolor="white", linewidth=0.6)

    # De startstack. Links ervan staat iedereen die chips heeft ingeleverd.
    ax.axvline(STARTSTACK, color=INKT, linestyle="--", linewidth=1.2, zorder=3)

    ax.set_xlabel("eindstand (chips)", color=INKT, fontsize=11)
    ax.set_ylabel("aantal bots", color=INKT, fontsize=11)
    ax.set_xticks(randen[::2])
    ax.yaxis.get_major_locator().set_params(integer=True)
    ax.tick_params(colors=GEDEMPT, labelsize=9)
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    for kant in ("left", "bottom"):
        ax.spines[kant].set_color(GEDEMPT)

    fig.tight_layout()
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    fig.savefig(pad, facecolor="white")
    plt.close(fig)
    return pad


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as bestand:
        uitslag = json.load(bestand)
    standen = uitslag.get("eindstand_per_bot")
    if not standen:
        print("Geen eindstand_per_bot in deze uitslag.")
        return 2
    waarden = list(standen.values())
    pad = teken(waarden)
    boven = sum(1 for w in waarden if w > STARTSTACK)
    print(f"{len(waarden)} bots · {boven} boven de startstack · "
          f"van {min(waarden):.0f} tot {max(waarden):.0f} -> {pad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
