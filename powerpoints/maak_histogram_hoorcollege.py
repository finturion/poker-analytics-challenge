"""
Tekent de twee verdelingen van een toernooi voor het hoorcollege.

    python3 powerpoints/maak_histogram_hoorcollege.py uitslag.json

Schrijft twee platen in powerpoints/plots_week3/:

    winst_per_hand_histogram.png   de winst per hand, over alle beslissingen
    eindstanden_histogram.png      waar de bots zijn geëindigd

Ze horen bij elkaar en vertellen niet hetzelfde. De winst per hand is voor ruim
negentig procent een blind van tien of twintig chips, dus lineair getekend krijg
je één balk en verder wit; daarom staat die y-as logaritmisch. De eindstand is
één getal per bot en past gewoon op een lineaire as.

Dat verschil is zelf de les: dezelfde dataset, twee eenheden, en de keuze van de
as bepaalt of je iets ziet.

Geen tekst in de platen. Wat erover gezegd moet worden staat in de notities van de
dia -- een bijschrift beweert na een nieuwe ronde vroeg of laat iets dat niet meer
klopt.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from toernooicijfers import STARTSTACK, bouw_dataframe

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTMAP = os.path.join(HIER, "plots_week3")
WINST_PAD = os.path.join(PLOTMAP, "winst_per_hand_histogram.png")
EINDSTAND_PAD = os.path.join(PLOTMAP, "eindstanden_histogram.png")

VILT = "#1B4D3E"
INKT = "#121E31"
GEDEMPT = "#5A646B"
EINDSTAND_BAKJE = 100


def _opmaak(ax, x_label, y_label):
    ax.set_xlabel(x_label, color=INKT, fontsize=11)
    ax.set_ylabel(y_label, color=INKT, fontsize=11)
    ax.tick_params(colors=GEDEMPT, labelsize=9)
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    for kant in ("left", "bottom"):
        ax.spines[kant].set_color(GEDEMPT)


def teken_winst(winst, pad=WINST_PAD):
    """De winst per hand. Log-y, want de piek is duizenden hoog en de staart één."""
    grens = max(abs(winst.min()), abs(winst.max()))
    randen = np.linspace(-grens, grens, 61)

    fig, ax = plt.subplots(figsize=(9.2, 4.0), dpi=200)
    ax.hist(winst, bins=randen, color=VILT, edgecolor="white", linewidth=0.3)
    ax.set_yscale("log")
    _opmaak(ax, "winst per hand (chips)", "aantal handen (logaritmisch)")

    fig.tight_layout()
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    fig.savefig(pad, facecolor="white")
    plt.close(fig)
    return pad


def teken_eindstanden(eindstanden, pad=EINDSTAND_PAD):
    """De eindstand per bot. Lineair; de stippellijn is de startstack."""
    waarden = np.asarray(sorted(eindstanden), dtype=float)
    laag = np.floor(waarden.min() / EINDSTAND_BAKJE) * EINDSTAND_BAKJE
    hoog = np.ceil(waarden.max() / EINDSTAND_BAKJE) * EINDSTAND_BAKJE
    randen = np.arange(laag, hoog + EINDSTAND_BAKJE, EINDSTAND_BAKJE)

    fig, ax = plt.subplots(figsize=(9.2, 4.0), dpi=200)
    ax.hist(waarden, bins=randen, color=VILT, edgecolor="white", linewidth=0.6)
    ax.axvline(STARTSTACK, color=INKT, linestyle="--", linewidth=1.2, zorder=3)
    _opmaak(ax, "eindstand (chips)", "aantal bots")
    ax.set_xticks(randen[::2])
    ax.yaxis.get_major_locator().set_params(integer=True)

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
    if not uitslag.get("hand_log") or not uitslag.get("eindstand_per_bot"):
        print("Deze uitslag heeft geen hand_log of geen eindstand_per_bot.")
        return 2

    winst = bouw_dataframe(uitslag)["winst"]
    teken_winst(winst)
    print(f"{len(winst)} handen · van {winst.min():.0f} tot {winst.max():+.0f} -> {WINST_PAD}")

    standen = list(uitslag["eindstand_per_bot"].values())
    teken_eindstanden(standen)
    boven = sum(1 for w in standen if w > STARTSTACK)
    print(f"{len(standen)} bots · {boven} boven de startstack · "
          f"van {min(standen):.0f} tot {max(standen):.0f} -> {EINDSTAND_PAD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
