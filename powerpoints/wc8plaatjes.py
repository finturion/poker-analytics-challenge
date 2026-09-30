#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
De routekaart bij het slot van het Werkcollege 8-deck.

    python3 powerpoints/wc8plaatjes.py   ->  plots_wc8/wc8_routes.png

Waarom deze plaat er is: studenten willen na afloop weten "wat kan ik nog meer
uitzoeken", en het eerlijke antwoord is dat dat van de vráág afhangt. Een deel
zit in het toernooi-logboek, een deel moet je zelf meten door je bot te laten
opschrijven wat hij doet, en een deel is geen analyse maar een functie die je
gewoon kunt aanroepen.

Het middelste spoor is het belangrijkste en het minst voor de hand liggende: het
logboek heeft één regel per hand, met alleen de eerste actie. Alles wat per
ronde, per pot of per tegenstander speelt staat er dus niet in -- dat kun je
alleen zien als je bot het zelf opschrijft.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTMAP = os.path.join(HIER, "plots_wc8")

INKT = "#121E31"
GEDEMPT = "#5A646B"
BLAUW = "#2a78d6"
GROEN = "#1B5E4A"
ORANJE = "#eb6834"
WIT = "#FFFFFF"
LICHT = "#EEF2F0"


def _doos(ax, x, y, b, h, tekst, vul=WIT, rand=GEDEMPT, kleur=INKT,
          grootte=9.5, vet=False, dik=1.2):
    ax.add_patch(FancyBboxPatch((x, y), b, h,
                                boxstyle="round,pad=0.008,rounding_size=0.018",
                                facecolor=vul, edgecolor=rand, linewidth=dik, zorder=2))
    ax.text(x + b / 2, y + h / 2, tekst, ha="center", va="center", color=kleur,
            fontsize=grootte, fontweight="bold" if vet else "normal",
            zorder=3, linespacing=1.4)


def _pijl(ax, van, naar, kleur=GEDEMPT):
    ax.add_patch(FancyArrowPatch(van, naar, arrowstyle="-|>", mutation_scale=13,
                                 color=kleur, linewidth=1.3, shrinkA=3, shrinkB=3, zorder=1))


def plaat_routes():
    fig, ax = plt.subplots(figsize=(12.6, 5.8), dpi=200)
    ax.set_xlim(-0.006, 1.006); ax.set_ylim(-0.02, 1.02); ax.axis("off")

    _doos(ax, 0.275, 0.885, 0.45, 0.095,
          "Wat wil je weten over je eigen strategie?", vul=INKT, rand=INKT,
          kleur=WIT, grootte=12, vet=True)

    kolommen = [
        (0.005, BLAUW, "UIT HET LOGBOEK",
         "alles wat per HAND speelt",
         ["winkans per hand — toets je drempel",
          "je eerste actie tegen de uitkomst",
          "hoe lang je overleeft per simulatie",
          "je stack-verloop over 40 handen",
          "tafelgrootte, als die verschilt"]),
        (0.345, ORANJE, "JE BOT LAAT HET OPSCHRIJVEN",
         "alles wat per RONDE of per BESLISSING speelt",
         ["winkans per straat: preflop → river",
          "hoe vaak je bluf-regel écht vuurde",
          "welke van je vijf regels besliste",
          "wat pot odds je hebben gekost",
          "hoeveel tegenstanders er nog in zaten"]),
        (0.685, GROEN, "GEWOON OPVRAGEN",
         "geen analyse, één functie-aanroep",
         ["schat_winkans(hand, bord=…)",
          "schat_winkans(…, tegenstanders=n)",
          "beschrijf_hand() → 'three of a kind'",
          "vergelijk_handen() → wie wint?",
          "dit staat al in je hulpfuncties"]),
    ]

    for x, kleur, kop, onder, punten in kolommen:
        _doos(ax, x, 0.700, 0.310, 0.105, kop, vul=kleur, rand=kleur,
              kleur=WIT, grootte=11, vet=True)
        ax.text(x + 0.155, 0.668, onder, ha="center", va="top", color=GEDEMPT,
                fontsize=9, style="italic")
        _pijl(ax, (0.5, 0.885), (x + 0.155, 0.806))
        _doos(ax, x, 0.185, 0.310, 0.430, "", vul=LICHT, rand=LICHT)
        for i, punt in enumerate(punten):
            ax.text(x + 0.018, 0.575 - i * 0.082, "·  " + punt, ha="left", va="top",
                    color=INKT, fontsize=8.8)

    ax.text(0.5, 0.135,
            "Het logboek heeft één regel per hand, met alleen je eerste actie. "
            "Ronde, pot, bord en tegenstander-acties staan er niet in.",
            ha="center", va="top", color=ORANJE, fontsize=10, fontweight="bold")
    ax.text(0.5, 0.075,
            "Wil je dáár iets over weten, dan is er maar één weg: je bot schrijft het zelf op, "
            "en je draait hem met speel_duel().",
            ha="center", va="top", color=GEDEMPT, fontsize=9.5)

    os.makedirs(PLOTMAP, exist_ok=True)
    pad = os.path.join(PLOTMAP, "wc8_routes.png")
    fig.savefig(pad, facecolor=WIT, dpi=200, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print("  ", pad)
    return pad


if __name__ == "__main__":
    plaat_routes()
    sys.exit(0)
