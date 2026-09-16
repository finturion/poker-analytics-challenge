"""
Tekent het histogram van de winst per hand voor het hoorcollege.

    python3 powerpoints/maak_histogram_hoorcollege.py uitslag.json

Schrijft powerpoints/plots_week3/winst_histogram.png. vul_hoorcollege_aan.py
zet die plaat op de dia zodra hij bestaat.

Waarom een eigen plaatje en niet df["winst"].hist(bins=40): met 40 gelijke bakjes
zie je één balk. 92% van de handen zit tussen -20 en +20 en de rest ligt honderden
chips verderop. Daarom staat de y-as logaritmisch -- dan zie je de staart waar het
college over gaat zónder de piek weg te poetsen. Dat is zelf al een les: de
standaardinstelling van een grafiek is een keuze die iemand voor je heeft gemaakt.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from toernooicijfers import bouw_dataframe

HIER = os.path.dirname(os.path.abspath(__file__))
UITVOER = os.path.join(HIER, "plots_week3", "winst_histogram.png")

VILT = "#1B4D3E"
INKT = "#121E31"
GEDEMPT = "#5A646B"
STARTSTACK = 1000


def winst_kolom(uitslag):
    """Dezelfde winst als op het doorloopblad en op de dia's -- zie toernooicijfers."""
    return bouw_dataframe(uitslag)["winst"]


def teken(winst, pad=UITVOER):
    fig, ax = plt.subplots(figsize=(9.2, 4.3), dpi=200)

    grens = max(abs(winst.min()), abs(winst.max()))
    randen = np.linspace(-grens, grens, 61)
    ax.hist(winst, bins=randen, color=VILT, edgecolor="white", linewidth=0.3)
    ax.set_yscale("log")

    ax.set_xlabel("winst per hand (chips)", color=INKT, fontsize=11)
    ax.set_ylabel("aantal handen (log)", color=INKT, fontsize=11)
    ax.tick_params(colors=GEDEMPT, labelsize=9)
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    for kant in ("left", "bottom"):
        ax.spines[kant].set_color(GEDEMPT)

    # Dezelfde grenzen als blok 2 van collegecijfers.py, zodat de plaat en de
    # dia niet twee verschillende getallen over dezelfde staart beweren.
    midden = int(((winst > -20) & (winst < 20)).sum())
    staart = int((winst < -200).sum() + (winst >= 200).sum())

    ax.annotate(f"{midden} van de {len(winst)} handen liggen tussen -20 en +20:\ndat zijn de blinds, niet het spel",
                xy=(0, 2500), xytext=(0.03, 0.80), textcoords="axes fraction",
                color=INKT, fontsize=10.5, linespacing=1.4,
                arrowprops=dict(arrowstyle="->", color=GEDEMPT, linewidth=1,
                                connectionstyle="arc3,rad=-0.15"))
    ax.annotate(f"{staart} handen van 200 chips of meer —\nhier gebeurt het spel",
                xy=(winst.max(), 1), xytext=(0.62, 0.46), textcoords="axes fraction",
                color=INKT, fontsize=10.5, linespacing=1.4,
                arrowprops=dict(arrowstyle="->", color=GEDEMPT, linewidth=1,
                                connectionstyle="arc3,rad=0.2"))

    fig.tight_layout()
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    fig.savefig(pad, facecolor="white")
    plt.close(fig)
    return pad, midden, staart


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as bestand:
        uitslag = json.load(bestand)
    if not uitslag.get("hand_log"):
        print("Geen hand_log in deze uitslag.")
        return 2
    winst = winst_kolom(uitslag)
    pad, midden, staart = teken(winst)
    print(f"{len(winst)} handen · {midden} rond nul · {staart} in de staart -> {pad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
