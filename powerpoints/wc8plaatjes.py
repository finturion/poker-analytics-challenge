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


def plaat_regels():
    """
    Van je eigen vijf regels naar vijf onderzoeksvragen.

    Dit is het antwoord op "hoe verzin ik zo'n analyse": je verzint hem niet, je
    leest hem af van je eigen code. Elke regel die je in Werkcollege 7 hebt
    geschreven bevat een getal dat je op gevoel hebt gekozen, en over elk van die
    getallen kun je dezelfde twee vragen stellen -- hoe vaak vuurt deze regel, en
    wat levert hij op als hij vuurt.
    """
    fig, ax = plt.subplots(figsize=(12.8, 6.4), dpi=200)
    ax.set_xlim(-0.006, 1.006); ax.set_ylim(-0.02, 1.02); ax.axis("off")

    ax.text(0.5, 0.995,
            "Elke regel in je bot bevat een getal dat je op gevoel koos.",
            ha="center", va="top", color=INKT, fontsize=13, fontweight="bold")
    ax.text(0.5, 0.945,
            "Stel over elk van die getallen dezelfde twee vragen:  "
            "hoe vaak vuurt deze regel, en wat levert hij op?",
            ha="center", va="top", color=ORANJE, fontsize=11, fontweight="bold")

    koppen = [(0.005, 0.300, "JOUW REGEL"),
              (0.325, 0.375, "DE VRAAG DIE JE EROVER STELT"),
              (0.715, 0.280, "WAAR HET ANTWOORD VANDAAN KOMT")]
    for x, b, kop in koppen:
        ax.text(x + 0.010, 0.898, kop, ha="left", va="center", color=GEDEMPT,
                fontsize=9, fontweight="bold")

    rijen = [
        ("1 · korte stack\nstack < 150 → all_in / fold",
         "Hoe vaak zakte je onder die grens,\nen wat leverde all_in daar op?",
         "logboek", BLAUW),
        ("2 · de tafel las mee\niemand raiste → fold onder STERK",
         "Hoe vaak hield deze regel je tegen,\nen had hij achteraf gelijk?",
         "zelf loggen", ORANJE),
        ("3 · de prijs\nwinkans < pot odds → fold",
         "Hoe vaak was meedoen te duur?\nEn foldde je handen die wonnen?",
         "zelf loggen", ORANJE),
        ("4 · bluffen\nwinkans < ZWAK → soms raise",
         "Vuurt je bluf-regel überhaupt,\nen leveren die handen iets op?",
         "logboek + zelf loggen", ORANJE),
        ("5 · het vangnet\nSTERK / MEEDOEN",
         "Klopt je drempel, gegeven de\nwinkans die je per hand kunt uitrekenen?",
         "logboek", BLAUW),
    ]

    y0, hoogte, ruimte = 0.722, 0.130, 0.019
    for i, (regel, vraag, route, kleur) in enumerate(rijen):
        y = y0 - i * (hoogte + ruimte)
        _doos(ax, 0.005, y, 0.300, hoogte, regel, vul=LICHT, rand=LICHT, grootte=9)
        _doos(ax, 0.325, y, 0.375, hoogte, vraag, vul=WIT, rand="#C9D2CC", grootte=9.2)
        _doos(ax, 0.715, y, 0.280, hoogte, route, vul=kleur, rand=kleur,
              kleur=WIT, grootte=10, vet=True)

    ax.text(0.5, 0.020,
            "Je verzint een analyse dus niet — je leest hem af van je eigen code.",
            ha="center", va="bottom", color=INKT, fontsize=11, fontweight="bold")

    os.makedirs(PLOTMAP, exist_ok=True)
    pad = os.path.join(PLOTMAP, "wc8_regels.png")
    fig.savefig(pad, facecolor=WIT, dpi=200, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print("  ", pad)
    return pad



def plaat_features():
    """
    Van ruwe kolom naar inzicht, met de drie bewerkingen uit het hoorcollege.

    Het hoorcollege van deze week gaat over feature engineering: data ombouwen
    naar nieuwe bruikbare data. Daar staan diff, cumsum en transform al op, met
    de laadpaal, het gebouw en het HR-voorbeeld ernaast. Deze plaat is dezelfde
    les op hun eigen toernooi, zodat de brug expliciet is en niet impliciet.
    """
    fig, ax = plt.subplots(figsize=(12.8, 6.0), dpi=200)
    ax.set_xlim(-0.006, 1.006); ax.set_ylim(-0.02, 1.02); ax.axis("off")

    koppen = [(0.005, 0.255, "WAT JE KRIJGT", GEDEMPT),
              (0.300, 0.400, "WAT JE ZELF MAAKT", ORANJE),
              (0.745, 0.250, "WAT JE DAN ZIET", GROEN)]
    for x, b, kop, kleur in koppen:
        _doos(ax, x, 0.885, b, 0.080, kop, vul=kleur, rand=kleur, kleur=WIT,
              grootte=10.5, vet=True)

    ruw = ["bot_naam", "simulatie", "hand_nummer", "hand",
           "actie", "aan_zet", "uitgespeeld", "stack"]
    _doos(ax, 0.005, 0.135, 0.255, 0.720, "", vul=LICHT, rand=LICHT)
    for i, kolom in enumerate(ruw):
        ax.text(0.022, 0.800 - i * 0.082, kolom, ha="left", va="center",
                color=INKT, fontsize=10, family="monospace")
    ax.text(0.132, 0.095, "8 kolommen, één regel per hand",
            ha="center", va="top", color=GEDEMPT, fontsize=9)

    gemaakt = [
        ("winst", ".groupby(...)[\"stack\"].diff()", "de laadpaal", ORANJE),
        ("totaal", ".groupby(...)[\"winst\"].cumsum()", "het gebouw", ORANJE),
        ("fold_pct", ".groupby(\"bot_naam\")[...].mean()", "het HR-voorbeeld", ORANJE),
        ("hand_naam", "sorteren op rangwaarde", "zelf bedacht", GEDEMPT),
        ("speelde_mee", "aan_zet & niet uitgespeeld", "een filter", GEDEMPT),
        ("winkans", "schat_winkans(hand, ...)", "van buiten gehaald", BLAUW),
    ]
    for i, (naam, hoe, herkomst, kleur) in enumerate(gemaakt):
        y = 0.760 - i * 0.118
        _doos(ax, 0.300, y, 0.400, 0.098, "", vul=WIT, rand="#C9D2CC")
        ax.text(0.315, y + 0.066, naam, ha="left", va="center", color=INKT,
                fontsize=10.5, fontweight="bold", family="monospace")
        ax.text(0.315, y + 0.030, hoe, ha="left", va="center", color=GEDEMPT,
                fontsize=8.6, family="monospace")
        ax.text(0.688, y + 0.049, herkomst, ha="right", va="center", color=kleur,
                fontsize=8.6, style="italic")
        _pijl(ax, (0.264, y + 0.049), (0.296, y + 0.049))

    ziet = ["de verdeling van de klas", "wie er defensief speelt",
            "welke handen geld opleveren", "waar jouw geld heen ging",
            "hoeveel ervan toeval is"]
    _doos(ax, 0.745, 0.135, 0.250, 0.720, "", vul=LICHT, rand=LICHT)
    for i, punt in enumerate(ziet):
        ax.text(0.760, 0.780 - i * 0.135, "·  " + punt, ha="left", va="center",
                color=INKT, fontsize=9.5)
    _pijl(ax, (0.704, 0.495), (0.741, 0.495), kleur=GROEN)

    ax.text(0.5, 0.055,
            "diff, cumsum en transform zijn dezelfde drie bewerkingen als in het hoorcollege "
            "— nu op jullie eigen toernooi.",
            ha="center", va="top", color=INKT, fontsize=10.5, fontweight="bold")
    ax.text(0.5, 0.005,
            "En let op de groupby: zonder die trek je de eerste hand van de ene bot af van "
            "de laatste van de andere.",
            ha="center", va="top", color=ORANJE, fontsize=9.5)

    os.makedirs(PLOTMAP, exist_ok=True)
    pad = os.path.join(PLOTMAP, "wc8_features.png")
    fig.savefig(pad, facecolor=WIT, dpi=200, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print("  ", pad)
    return pad


if __name__ == "__main__":
    plaat_routes()
    plaat_regels()
    plaat_features()
    sys.exit(0)
