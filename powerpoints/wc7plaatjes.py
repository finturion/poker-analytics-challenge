#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
De platen bij het hoorcollege van week 5 (Werkcollege 7).

    python3 powerpoints/wc7plaatjes.py

Schrijft naar powerpoints/plots_week5/.

De flowchart is met de hand getekend in matplotlib en niet met mermaid. Mermaid
rendert wel in een notebook en in Brightspace, maar niet naar een plaatje dat je
in een dia kunt zetten -- en deze figuur moet op allebei de plekken hetzelfde
zijn, want studenten zien hem eerst op de beamer en daarna in hun notebook.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTMAP = os.path.join(HIER, "plots_week5")

INKT = "#121E31"
VILT = "#1B4D3E"
GEDEMPT = "#5A646B"
ROOD = "#B3261E"
LICHT = "#EEF2EF"

# Gemeten met scripts/meet_toernooi_variantie.py: 44 bots met bekende kwaliteit
# (de raise-drempel is de enige knop, dus hoger = objectief beter), 20 simulaties
# per bot -- precies wat de bonusweek draait -- over 5 verschillende seeds.
#
# Twee getallen, en ze zeggen allebei iets anders. De ladder BELOONT skill: 76%
# van de bonuspunten gaat naar de betere helft van het veld, tegen 50% als het
# puur toeval was. Maar WIE van die goede bots in de prijzen valt, is grotendeels
# de kaartverdeling: deel je hetzelfde veld opnieuw, dan gaat gemiddeld maar 0,9
# van de 5 plekken naar dezelfde bot.
GEMETEN_OVERLAP = 0.9
NAAR_BETERE_HELFT = 76
WIT = "#FFFFFF"


def _bewaar(fig, naam):
    os.makedirs(PLOTMAP, exist_ok=True)
    pad = os.path.join(PLOTMAP, naam + ".png")
    fig.savefig(pad, facecolor=WIT, dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return pad


def _doos(ax, x, y, b, h, tekst, vul=WIT, rand=GEDEMPT, kleur=INKT,
          grootte=9.5, vet=False):
    ax.add_patch(FancyBboxPatch((x, y), b, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                facecolor=vul, edgecolor=rand, linewidth=1.3, zorder=2))
    ax.text(x + b / 2, y + h / 2, tekst, ha="center", va="center", color=kleur,
            fontsize=grootte, fontweight="bold" if vet else "normal",
            zorder=3, linespacing=1.35)
    return (x + b / 2, y, x + b / 2, y + h)


def _pijl(ax, van, naar, kleur=GEDEMPT):
    ax.add_patch(FancyArrowPatch(van, naar, arrowstyle="-|>", mutation_scale=13,
                                 color=kleur, linewidth=1.2,
                                 shrinkA=2, shrinkB=2, zorder=1))


def plaat_overzicht():
    """
    Waar je bot op kan letten: vijf vragen, één beslissing.

    Elke invoer staat recht boven de vraag waar hij bij hoort. In de eerste
    versie stonden ze in de volgorde waarin de API ze aanbiedt, en dan kruisen
    de pijlen elkaar zes keer -- precies het soort plaat waar Werkcollege 6 over
    gaat. De volgorde van de kolommen is dus niet willekeurig maar het ontwerp.
    """
    fig, ax = plt.subplots(figsize=(13.0, 6.4), dpi=200)
    ax.set_xlim(0, 13); ax.set_ylim(0, 6.4); ax.axis("off")

    kolommen = [
        (0.20, 2.40, "hand · hand_met_kleur\nbord",
         "hoe sterk\nsta ik?",
         "schat_winkans(hand_met_kleur,\nbord=bord, tegenstanders=n)"),
        (2.75, 2.40, "ronde · pot\ninzet_om_te_callen",
         "wat kost\nmeedoen?",
         "inzet / (pot + inzet)\n= het % dat je nodig hebt"),
        (5.30, 2.40, "stack",
         "hoeveel kan\nik verliezen?",
         "korte stack → all_in of fold\ndiepe stack → ruimte"),
        (7.85, 2.40, "tegenstander_acties\n_deze_hand",
         "wat doet\nde tafel?",
         "filter op ronde!\nraiste iemand op DEZE straat?"),
        (10.40, 2.40, "bluf_kans",
         "ga ik\nbluffen?",
         "random.random() < bluf_kans\nen: alleen zonder tegenstand"),
    ]

    ax.text(0.20, 6.10, "WAT JE BOT BINNENKRIJGT", color=VILT, fontsize=10,
            fontweight="bold")
    middens = []
    for x, b, invoer, vraag, hoe in kolommen:
        cx = x + b / 2
        middens.append(cx)
        _doos(ax, x, 5.25, b, 0.66, invoer, vul=LICHT, rand=VILT, grootte=9)
        _doos(ax, x, 3.95, b, 0.62, vraag, vul=WIT, rand=VILT, grootte=10.5, vet=True)
        _doos(ax, x, 2.90, b, 0.86, hoe, vul=WIT, rand="#C8D2CC", grootte=7.8,
              kleur=GEDEMPT)
        _pijl(ax, (cx, 5.25), (cx, 4.57))
        _pijl(ax, (cx, 3.95), (cx, 3.76))

    _doos(ax, 4.55, 1.45, 3.9, 0.72, "jouw beslisregel", vul=VILT, rand=VILT,
          kleur=WIT, grootte=13, vet=True)
    for cx in middens:
        _pijl(ax, (cx, 2.90), (6.5, 2.17))
    _doos(ax, 3.9, 0.35, 5.2, 0.68,
          "fold  ·  call  ·  raise  ·  grote_raise  ·  all_in",
          vul=LICHT, rand=VILT, grootte=11, vet=True)
    _pijl(ax, (6.5, 1.45), (6.5, 1.03), kleur=VILT)

    ax.text(12.80, 0.80, "je krijgt een parameter\nalleen als je hem zelf\nopschrijft — exact zo",
            ha="right", va="center", color=ROOD, fontsize=8.5, fontweight="bold",
            linespacing=1.4)
    return _bewaar(fig, "wc7_overzicht")


def plaat_locatie():
    """Waarom je je locatie meegeeft: maandag grijs, woensdag gekleurd."""
    import folium  # noqa: F401  (alleen om te melden als hij mist)
    fig, assen = plt.subplots(1, 2, figsize=(11.0, 4.2), dpi=200)
    steden = {"Amsterdam": (4.90, 52.37), "Rotterdam": (4.48, 51.92),
              "Utrecht": (5.12, 52.09), "Groningen": (6.57, 53.22),
              "Eindhoven": (5.48, 51.44), "Nijmegen": (5.85, 51.84),
              "Tilburg": (5.09, 51.56), "Den Haag": (4.31, 52.08)}
    eind = [None, None, None, None, None, None, None, None]
    echt = [1748, 890, 1256, 640, 1020, 780, 1180, 950]

    for ax, standen, titel in ((assen[0], eind, "maandag — je levert een locatie in"),
                               (assen[1], echt, "woensdag — het toernooi is gedraaid")):
        for (naam, (lon, lat)), stand in zip(steden.items(), standen):
            kleur = GEDEMPT if stand is None else (VILT if stand >= 1000 else ROOD)
            ax.scatter(lon, lat, s=190, color=kleur, alpha=0.85,
                       edgecolor="white", linewidth=1.5, zorder=3)
        ax.set_xlim(3.5, 7.3); ax.set_ylim(50.9, 53.7)
        ax.set_title(titel, color=INKT, fontsize=11, pad=10)
        ax.set_xticks([]); ax.set_yticks([])
        for kant in ("top", "right", "left", "bottom"):
            ax.spines[kant].set_color("#DDE3DE")
    assen[0].text(5.4, 51.0, "alles grijs: er is nog niet gespeeld",
                  ha="center", color=GEDEMPT, fontsize=9)
    assen[1].text(5.4, 51.0, "groen boven de startstack, rood eronder",
                  ha="center", color=GEDEMPT, fontsize=9)
    return _bewaar(fig, "wc7_locatie")


def _dagblok(ax, x, y, b, h, dag, regels, deadline=False):
    """Eén dag in de planning: een kopregel met de datum, daaronder wat er gebeurt."""
    rand = ROOD if deadline else "#C9D2CC"
    ax.add_patch(FancyBboxPatch((x, y), b, h, boxstyle="round,pad=0.008,rounding_size=0.02",
                                facecolor=WIT, edgecolor=rand, linewidth=1.8 if deadline else 1.2,
                                zorder=2))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.075), b, 0.075,
                                boxstyle="square,pad=0", facecolor=ROOD if deadline else VILT,
                                edgecolor="none", zorder=3))
    ax.text(x + b / 2, y + h - 0.0375, dag, ha="center", va="center", color=WIT,
            fontsize=9.5, fontweight="bold", zorder=4)
    for i, (tekst, dik) in enumerate(regels):
        ax.text(x + 0.013, y + h - 0.105 - i * 0.048, tekst, ha="left", va="top",
                color=INKT if dik else GEDEMPT, fontsize=8.3,
                fontweight="bold" if dik else "normal", zorder=4, linespacing=1.3)


def plaat_planning():
    """Wat er de komende twee weken gebeurt, met de deadlines eruit gelicht."""
    fig, ax = plt.subplots(figsize=(12.4, 5.4), dpi=200)
    # Iets ruimer dan 0-1: de afgeronde hoeken van het laatste blok steken net
    # buiten de as, en die worden anders weggeknipt.
    ax.set_xlim(-0.006, 1.006); ax.set_ylim(-0.01, 1.01); ax.axis("off")

    ax.text(0.005, 0.965, "DEZE WEEK", fontsize=10.5, fontweight="bold", color=VILT)
    ax.plot([0.10, 0.995], [0.955, 0.955], color="#C9D2CC", linewidth=1.2)

    breedte, ruimte = 0.2355, 0.018
    deze_week = [
        ("maandag 28 sep", [("Werkcollege 7", True), ("Bot v3 bouwen", False),
                            ("groepscase toegelicht", True), ("kies vandaag een onderwerp", False)], False),
        ("woensdag 30 sep", [("09:00 bot inleveren", True), ("toernooi 1 — telt mee", False),
                             ("Werkcollege 8", True), ("eindopdracht uitgelegd", True)], True),
        ("donderdag 1 okt", [("oefenronde", True), ("telt NIET mee", False),
                             ("zie wat je aanpassing deed", False)], False),
        ("vrijdag 2 okt", [("18:00 definitieve bot", True), ("laatste inzending van de reeks", False),
                           ("toernooi 2 — telt mee", True)], True),
    ]
    for i, (dag, regels, deadline) in enumerate(deze_week):
        _dagblok(ax, 0.004 + i * (breedte + ruimte), 0.545, breedte, 0.36, dag, regels, deadline)

    ax.text(0.005, 0.455, "VOLGENDE WEEK", fontsize=10.5, fontweight="bold", color=VILT)
    ax.plot([0.155, 0.995], [0.445, 0.445], color="#C9D2CC", linewidth=1.2)

    _dagblok(ax, 0.004, 0.015, 0.489, 0.40, "maandag 5 oktober", [
        ("13:00 – 13:15  samen aan de groepscase werken", True),
        ("13:30  onderwerp definitief vastleggen", True),
        ("Werkcollege 9 — Visual Maandag", True),
        ("alleen de visuele kant: je kaart uit week 5", False),
        ("opnieuw ontwerpen in twee lagen", False),
        ("wie moet herkansen, doet dat deze middag", False),
    ])
    _dagblok(ax, 0.509, 0.015, 0.489, 0.40, "woensdag 7 oktober", [
        ("overhoring bonuspunten", True),
        ("wie bonus scoorde, legt uit hoe zijn bot werkt:", False),
        ("welke regels, in welke volgorde, en waarom", False),
        ("", False),
        ("dus: schrijf op waarom je iets veranderde,", True),
        ("terwijl je het verandert", True),
    ])
    return _bewaar(fig, "wc7_planning")


def plaat_bonus(overlap=None):
    """De bonusladder, en hoeveel van de uitslag kaartgeluk is."""
    fig, assen = plt.subplots(1, 2, figsize=(12.0, 4.8), dpi=200,
                              gridspec_kw={"width_ratios": [1.1, 1]})

    links = assen[0]
    plekken = ["1e", "2e", "3e", "4e", "5e", "6e\nen lager"]
    punten = [0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
    kleuren = [VILT] * 5 + ["#D8DEDA"]
    balken = links.bar(plekken, punten, color=kleuren, width=0.6)
    for balk, punt in zip(balken, punten):
        links.text(balk.get_x() + balk.get_width() / 2, punt + 0.018,
                   f"{punt:.1f}".replace(".", ","), ha="center", va="bottom",
                   color=INKT, fontsize=12, fontweight="bold")
    links.set_ylim(0, 0.66)
    links.set_title("bonuspunten per toernooi,\nop je plek in de eindstand",
                    color=INKT, fontsize=11.5, pad=14, linespacing=1.4)
    links.text(0.5, -0.255, "twee toernooien die meetellen\nsamen maximaal 1,0 bonuspunt",
               transform=links.transAxes, ha="center", va="top", color=VILT,
               fontsize=11, fontweight="bold", linespacing=1.4)
    links.set_yticks([]); links.tick_params(axis="x", length=0, labelsize=10)
    for kant in ("top", "right", "left"):
        links.spines[kant].set_visible(False)
    links.spines["bottom"].set_color("#C9D2CC")

    rechts = assen[1]
    rechts.set_xlim(0, 1); rechts.set_ylim(0, 1.14); rechts.axis("off")
    rechts.text(0.5, 1.10, "en wie die plekken pakt, is deels kaartgeluk",
                ha="center", va="top", color=INKT, fontsize=11.5)
    rechts.text(0.22, 0.955, "toernooi 1", ha="center", va="center",
                color=GEDEMPT, fontsize=9.5)
    rechts.text(0.78, 0.955, "zelfde bots, andere kaarten", ha="center", va="center",
                color=GEDEMPT, fontsize=9.5)

    blijft = 5 if overlap is None else round(overlap)
    hoog, stap, top = 0.082, 0.113, 0.815
    for i in range(5):
        y = top - i * stap
        vast = i < blijft
        for x, kleur in ((0.075, VILT), (0.625, VILT if vast else ROOD)):
            rechts.add_patch(FancyBboxPatch((x, y), 0.29, hoog,
                                            boxstyle="round,pad=0.004,rounding_size=0.02",
                                            facecolor=kleur, edgecolor="none", zorder=2))
            rechts.text(x + 0.145, y + hoog / 2, f"{i + 1}e plek", ha="center",
                        va="center", color=WIT, fontsize=9.5, fontweight="bold", zorder=3)
        _pijl(rechts, (0.385, y + hoog / 2), (0.605, y + hoog / 2),
              kleur=GEDEMPT if vast else ROOD)

    if overlap is not None:
        komma = f"{overlap:.1f}".replace(".", ",")
        rechts.text(0.5, 0.235, f"gemeten: gemiddeld {komma} van de 5 plekken"
                                "\ngaat naar dezelfde bot",
                    ha="center", va="top", color=ROOD, fontsize=11,
                    fontweight="bold", linespacing=1.4)
        rechts.text(0.5, 0.045, f"én: {NAAR_BETERE_HELFT}% van de punten gaat naar de betere"
                                " helft van het veld\nbij puur toeval zou dat 50% zijn —"
                                " goed spelen loont dus wél",
                    ha="center", va="top", color=VILT, fontsize=9.8, linespacing=1.4)
    return _bewaar(fig, "wc7_bonus")


def main():
    print(" ", plaat_overzicht())
    print(" ", plaat_planning())
    print(" ", plaat_bonus(overlap=GEMETEN_OVERLAP))
    try:
        print(" ", plaat_locatie())
    except ImportError:
        print("  folium niet geïnstalleerd — locatieplaat overgeslagen")
    return 0


if __name__ == "__main__":
    sys.exit(main())
