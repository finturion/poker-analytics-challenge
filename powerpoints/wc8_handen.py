#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tekent een hand uit het toernooi als plaat voor het deck.

    python3 powerpoints/wc8_handen.py --ronde 6   ->  plots_wc8/hand_*.png

Eén plaat per hand: de tafel bovenaan, daaronder vier kolommen voor preflop,
flop, turn en river met het bord en de zetten in volgorde.

Studentnummers staan er afgekort op. Deze platen gaan het scherm op in een zaal
waar die studenten zelf zitten, en wie tweeduizend chips verliest hoeft daar niet
met zijn volledige nummer bij.

De volgorde binnen een straat is gereconstrueerd uit de pot -- zie de docstring
van scripts/laat_hand_zien.py. Dat staat ook als voetnoot op de plaat zelf, want
een plaat die een reconstructie als waarneming presenteert liegt.
"""
import argparse
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTMAP = os.path.join(HIER, "plots_wc8")
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "scripts"))

from laat_hand_zien import (STRAAT_VOLGORDE, winst_per_hand, zet_volgorde,  # noqa: E402
                            leesbaar, kaart)

INKT = "#121E31"
GEDEMPT = "#5A646B"
BLAUW = "#2a78d6"
GROEN = "#1B5E4A"
ORANJE = "#eb6834"
WIT = "#FFFFFF"
LICHT = "#EEF2F0"
ROOD_KAART = "#C0392B"

STRATEN = ["preflop", "flop", "turn", "river"]


def _kaartje(ax, x, y, code, breedte=0.030, hoogte=0.070):
    """Eén speelkaart. Harten en ruiten rood, schoppen en klaveren zwart."""
    tekst = kaart(code)
    rood = tekst.endswith("♥") or tekst.endswith("♦")
    ax.add_patch(FancyBboxPatch((x, y), breedte, hoogte,
                                boxstyle="round,pad=0.004,rounding_size=0.010",
                                facecolor=WIT, edgecolor=GEDEMPT, linewidth=1.0, zorder=3))
    ax.text(x + breedte / 2, y + hoogte / 2, tekst, ha="center", va="center",
            color=ROOD_KAART if rood else INKT, fontsize=10, fontweight="bold", zorder=4)
    return x + breedte + 0.006


def teken_hand(sleutel, rijen, winst, kort, pad):
    simulatie, tafel, nummer = sleutel
    gesorteerd = sorted(rijen, key=zet_volgorde)

    eersten = {}
    for r in gesorteerd:
        eersten.setdefault(r["bot_naam"], r)
    resultaat = {b: winst.get((b, simulatie, nummer), 0) for b in eersten}
    winnaar = max(resultaat, key=resultaat.get)
    verliezer = min(resultaat, key=resultaat.get)
    # Vaker dan je denkt verliezen meerdere spelers evenveel -- iedereen all-in
    # met dezelfde stack. Dan is er geen reden om er een willekeurige uit te
    # lichten; ze krijgen alledrie dezelfde kleur.
    diepste = resultaat[verliezer]
    zwaarste_verliezers = {b for b, w in resultaat.items() if w == diepste}
    pot_eind = max(r["pot"] for r in gesorteerd)

    fig, ax = plt.subplots(figsize=(12.6, 5.9), dpi=200)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax.text(0.0, 0.975, f"Simulatie {simulatie} · tafel {tafel} · hand {nummer}",
            fontsize=10.5, color=GEDEMPT, va="top")
    ax.text(0.0, 0.930, f"De pot liep op tot {pot_eind:,}".replace(",", "."),
            fontsize=17, color=INKT, fontweight="bold", va="top")

    # De tafel: wie zat erin, met welke kaarten, en wat het opleverde.
    x = 0.0
    for bot, eerste in sorted(eersten.items(), key=lambda kv: -resultaat[kv[0]]):
        w = resultaat[bot]
        kleur = GROEN if bot == winnaar else (
            ORANJE if bot in zwaarste_verliezers else GEDEMPT)
        ax.text(x, 0.845, kort(bot), fontsize=9.5, color=INKT, va="top")
        kx = x
        for code in (eerste.get("hand_met_kleur") or eerste.get("hand") or []):
            kx = _kaartje(ax, kx, 0.735, code)
        ax.text(x, 0.700, f"{w:+,}".replace(",", "."), fontsize=11.5, color=kleur,
                fontweight="bold", va="top")
        x += 0.168

    # Vier kolommen, een per straat.
    kolom_x = [0.0, 0.253, 0.506, 0.759]
    kolom_b = 0.232
    for i, straat in enumerate(STRATEN):
        zetten = [r for r in gesorteerd if r["ronde"] == straat]
        x0 = kolom_x[i]
        if not zetten:
            # Een lege kolom zonder uitleg leest als een fout in de plaat.
            ax.text(x0 + 0.012, 0.615, straat.upper(), fontsize=10.5, color="#AEB6BC",
                    fontweight="bold", va="top")
            ax.text(x0 + 0.012, 0.555, "niet gespeeld -- de hand\nwas hiervoor beslist",
                    fontsize=9, color="#AEB6BC", va="top", style="italic", linespacing=1.5)
            continue
        ax.add_patch(FancyBboxPatch((x0, 0.035), kolom_b, 0.605,
                                    boxstyle="round,pad=0.008,rounding_size=0.015",
                                    facecolor=LICHT, edgecolor="none", zorder=0))
        ax.text(x0 + 0.012, 0.615, straat.upper(), fontsize=10.5, color=BLAUW,
                fontweight="bold", va="top")

        bord = zetten[0]["bord"]
        if bord:
            kx = x0 + 0.012
            for code in bord:
                kx = _kaartje(ax, kx, 0.495, code, breedte=0.026, hoogte=0.058)
        else:
            ax.text(x0 + 0.012, 0.525, "nog geen kaarten", fontsize=9, color=GEDEMPT,
                    va="center", style="italic")

        # De regelafstand schaalt mee met het aantal zetten. Een vaste afstand
        # liet de drukste straat overlopen, en juist daar gebeurt het.
        top, bodem = 0.450, 0.065
        stap = min(0.048, (top - bodem) / max(len(zetten) - 1, 1))
        grootte = 9.0 if stap > 0.034 else 7.8
        y = top
        for r in zetten:
            kleur = GROEN if r["bot_naam"] == winnaar else (
                ORANJE if r["bot_naam"] in zwaarste_verliezers else INKT)
            ax.text(x0 + 0.012, y, kort(r["bot_naam"]).replace("student ", ""),
                    fontsize=grootte - 0.5, color=GEDEMPT, va="center")
            ax.text(x0 + kolom_b - 0.012, y, leesbaar(r), fontsize=grootte, color=kleur,
                    fontweight="bold", ha="right", va="center")
            y -= stap

    ax.text(0.0, -0.012,
            "Volgorde binnen een straat gereconstrueerd uit de pot: die groeit "
            "alleen als er chips in gaan.",
            fontsize=8, color=GEDEMPT, va="top")

    fig.savefig(pad, bbox_inches="tight", facecolor=WIT, pad_inches=0.22)
    plt.close(fig)
    return os.path.basename(pad)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde", type=int, default=6)
    p.add_argument("--aantal", type=int, default=1)
    args = p.parse_args()

    scripts = os.path.join(os.path.dirname(HIER), "scripts")
    with open(os.path.join(scripts, f"uitslag_week{args.week}_ronde{args.ronde}.json")) as f:
        uitslag = json.load(f)
    with open(os.path.join(scripts, f"uitgebreid_week{args.week}_ronde{args.ronde}.json")) as f:
        regels = json.load(f)["regels"]

    referentie = set(uitslag.get("referentiebots") or []) | set(uitslag.get("testbots") or [])

    def kort(naam):
        return naam if naam in referentie else f"student ...{naam[-4:]}"

    winst = winst_per_hand(uitslag["hand_log"])
    per_hand = {}
    for r in regels:
        per_hand.setdefault((r["simulatie"], r["tafel"], r["hand_nummer"]), []).append(r)

    kandidaten = []
    for sleutel, rijen in per_hand.items():
        simulatie, _, nummer = sleutel
        namen = {r["bot_naam"] for r in rijen}
        if len(namen) < 3:
            continue
        res = {b: winst.get((b, simulatie, nummer), 0) for b in namen}
        kandidaten.append({"beste": max(res.values()), "slechtste": min(res.values()),
                           "sleutel": sleutel, "rijen": rijen})

    os.makedirs(PLOTMAP, exist_ok=True)
    gekozen, gezien = [], set()
    for soort, sleutelfunctie in (("winst", lambda k: -k["beste"]),
                                  ("verlies", lambda k: k["slechtste"])):
        for k in sorted(kandidaten, key=sleutelfunctie)[:args.aantal + 2]:
            if k["sleutel"] in gezien:
                continue
            gezien.add(k["sleutel"])
            gekozen.append((soort, k))
            if sum(1 for s, _ in gekozen if s == soort) >= args.aantal:
                break

    for soort, k in gekozen:
        s, t, n = k["sleutel"]
        naam = f"hand_{soort}_r{args.ronde}_s{s}t{t}h{n}.png"
        teken_hand(k["sleutel"], k["rijen"], winst, kort, os.path.join(PLOTMAP, naam))
        print(f"   {naam}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
