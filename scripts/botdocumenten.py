#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eén document per bot die bonuspunten scoorde, om mee aan tafel te gaan.

    python3 scripts/botdocumenten.py
    python3 scripts/botdocumenten.py --iedereen          # niet alleen de scoorders
    python3 scripts/botdocumenten.py --student 500123456

Schrijft scripts/botdocumenten/<studentnummer>.html: de plots die ze in
Werkcollege 8 zelf hebben gemaakt, maar dan over hún bot, met daaronder de
vragen die uit die cijfers volgen.

WAAROM DIT WERKT ALS OVERHORING
-------------------------------
De getallen komen uit het log van zijn eigen toernooi. Dat log heeft hij nooit
gezien -- hij kent zijn bot van de code, niet van wat die 972 handen lang
werkelijk deed. De confrontatie tussen "wat ik dacht dat mijn bot deed" en wat
er staat, is de vraag. Voorbereiden kan niet, want hij weet niet welk getal er
uit komt.

De vragen zijn daarom ook geen quizvragen met één goed antwoord. Het goede
antwoord is een redenering over zijn eigen regels.

Alle plaatjes zitten als data-URI in het bestand, dus één HTML per student is
compleet -- geen map met losse PNG's die kwijtraakt.
"""
import argparse
import base64
import io
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

from botkaarten import (handsoort, klas_medianen, opvallende_handen,  # noqa: E402
                        profiel, winst_per_regel)
from laat_hand_zien import kaart, leesbaar, zet_volgorde  # noqa: E402

INKT = "#121E31"
GEDEMPT = "#5A646B"
BLAUW = "#2a78d6"
ORANJE = "#eb6834"
AQUA = "#1baf7a"
GROEN = "#1B5E4A"
LIJN = "#DCE3DE"

VOLGORDE = ["fold", "call", "raise", "grote_raise", "all_in"]

# De vijf acties hebben een VOLGORDE: fold is opgeven, all_in is alles erin. Dat
# is geen categorie maar een oplopende schaal, dus een tint die donkerder wordt
# naarmate er meer wordt ingezet -- niet vijf losse kleuren. Dezelfde ramp als
# analyse_toernooi.py gebruikt, lichtheid monotoon van 0,775 naar 0,087 en 6,0:1
# tussen de uitersten. De percentages staan erbij, want de lichtste stap haalt
# in zijn eentje geen 3:1 met de achtergrond.
ACTIEKLEUR = dict(zip(VOLGORDE,
                      ["#d7e6f2", "#a8cfdc", "#6fb8ae", "#3a8f7a", "#1B5E4A"]))
# Op welke stappen een wit label leesbaar is.
ACTIE_LABEL_WIT = {"grote_raise", "all_in"}
STRATEN = ["preflop", "flop", "turn", "river"]


def kaal(ax, y=True):
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    ax.spines["left"].set_color(LIJN)
    ax.spines["bottom"].set_color(LIJN)
    ax.tick_params(colors=GEDEMPT, labelsize=10)
    if y:
        ax.grid(axis="y", color=LIJN, linewidth=0.8)
        ax.set_axisbelow(True)


def nl(getal):
    """1829 -> '1.829'. Nederlandse duizendtallen."""
    return f"{getal:,}".replace(",", ".")


def als_uri(fig):
    """De plaat als data-URI, zodat het document één bestand blijft."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", pad_inches=0.2)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


# ---------------------------------------------------------------- de klas
def klas_handsoorten(profielen):
    """Per handsoort het GEMIDDELDE aandeel per actie over de klas.

    Let op: een gemiddelde wordt getrokken door uitschieters -- één bot die alles
    callt verschuift het call-aandeel van de hele klas. De mediaan is daar
    ongevoelig voor, maar het gemiddelde is wat je intuïtief verwacht als er
    "de klas" staat, en dat telt zwaarder bij een document dat je aan tafel leest.
    Omdat het per actie wordt gemiddeld tellen de aandelen wel netjes op tot 100.
    """
    per_soort = defaultdict(lambda: defaultdict(list))
    for prof in profielen.values():
        for soort, teller in prof["per_handsoort"].items():
            totaal = sum(teller.values())
            if totaal < 5:
                continue
            for actie in VOLGORDE:
                per_soort[soort][actie].append(100 * teller.get(actie, 0) / totaal)
    return {soort: {a: statistics.fmean(v) if v else 0.0 for a, v in acties.items()}
            for soort, acties in per_soort.items()}


def klas_trechter(beslissingen_per_bot, klas):
    """Welk deel van de preflop-beslissingen elke straat haalt, gemiddeld over de klas."""
    per_bot = []
    for bot in klas:
        bs = beslissingen_per_bot.get(bot) or []
        if not bs:
            continue
        telling = Counter(b["ronde"] for b in bs)
        preflop = telling.get("preflop", 0)
        if preflop < 20:
            continue
        per_bot.append({s: 100 * telling.get(s, 0) / preflop for s in STRATEN})
    if not per_bot:
        return {}
    return {s: statistics.fmean([r[s] for r in per_bot]) for s in STRATEN}


def klas_stackmediaan(hand_log, klas):
    """De gemiddelde stack per handnummer over alle bots en simulaties van de klas."""
    per_hand = defaultdict(list)
    for r in hand_log:
        if r["bot_naam"] in klas:
            per_hand[r["hand_nummer"]].append(r["stack"])
    return {n: statistics.fmean(v) for n, v in sorted(per_hand.items())}


def klas_actiewinst(per_bot, klas):
    """Wat elke actie de klas gemiddeld oplevert, gemiddeld over de bots."""
    per_actie = defaultdict(list)
    for bot in klas:
        eigen = defaultdict(list)
        for r in per_bot.get(bot, []):
            if r["actie"]:
                eigen[r["actie"]].append(r["winst"])
        for actie, winsten in eigen.items():
            if len(winsten) >= 10:
                per_actie[actie].append(statistics.fmean(winsten))
    return {a: statistics.fmean(v) for a, v in per_actie.items() if v}


def klas_potodds(beslissingen_per_bot, klas):
    """Welk deel van de pot de klas gemiddeld betaalt als ze callen."""
    per_bot = []
    for bot in klas:
        odds = [b["inzet_om_te_callen"] / (b["pot"] + b["inzet_om_te_callen"])
                for b in beslissingen_per_bot.get(bot, [])
                if b["gekozen"] == "call" and b["inzet_om_te_callen"] > 0]
        if len(odds) >= 10:
            per_bot.append(100 * statistics.fmean(odds))
    return statistics.fmean(per_bot) if per_bot else None


# ---------------------------------------------------------------- de platen
def plaat_stackverloop(eigen_log, klasmediaan=None):
    """Twintig simulaties, met de beste en de slechtste uitgelicht.

    De klasmediaan ligt erdoorheen: dan zie je niet alleen de spreiding van deze
    bot, maar ook of hij boven of onder de klas zat en vanaf welke hand.
    """
    per_sim = defaultdict(list)
    for r in eigen_log:
        per_sim[r["simulatie"]].append((r["hand_nummer"], r["stack"]))
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    eind = {}
    for sim, punten in per_sim.items():
        punten.sort()
        x = [p[0] for p in punten]
        y = [p[1] for p in punten]
        eind[sim] = y[-1]
        ax.plot(x, y, color=GEDEMPT, linewidth=1.0, alpha=0.35, zorder=2)
    # Welke twee licht je uit? Normaal de beste en de slechtste eindstand. Maar een
    # bot die in elke simulatie op 0 eindigt heeft die niet: dan vallen de twee
    # lijnen samen, staat er twee keer "0 chips" in de legenda, en ligt het echte
    # verhaal -- een simulatie die eerst naar 3300 liep -- in het grijs.
    piek = {sim: max(s for _, s in punten) for sim, punten in per_sim.items()}
    if len(set(eind.values())) > 1:
        uitgelicht = ((max(eind, key=eind.get), AQUA, "beste simulatie",
                       lambda s: f"{eind[s]} chips"),
                      (min(eind, key=eind.get), BLAUW, "slechtste simulatie",
                       lambda s: f"{eind[s]} chips"))
    else:
        gelijk = next(iter(eind.values()))
        uitgelicht = ((max(piek, key=piek.get), AQUA, "hoogste piek",
                       lambda s: f"tot {piek[s]} chips"),
                      (min(piek, key=piek.get), BLAUW, "laagste piek",
                       lambda s: f"tot {piek[s]} chips"))
        ax.text(0.985, 0.955,
                f"elke simulatie eindigde op {gelijk}",
                transform=ax.transAxes, ha="right", va="top",
                color=GEDEMPT, fontsize=10, style="italic")

    for sim, kleur, label, waarde in uitgelicht:
        punten = sorted(per_sim[sim])
        ax.plot([p[0] for p in punten], [p[1] for p in punten],
                color=kleur, linewidth=2.5, zorder=4,
                label=f"{label} ({waarde(sim)})")
    ax.axhline(1000, color=GEDEMPT, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    if klasmediaan:
        nummers = sorted(klasmediaan)
        ax.plot(nummers, [klasmediaan[n] for n in nummers], color=INKT,
                linewidth=1.8, linestyle=(0, (5, 2)), zorder=5,
                label="gemiddelde van de klas")
    ax.set_xlabel("hand")
    ax.set_ylabel("stack (chips)")
    ax.set_title("Dezelfde bot, dezelfde regels — twintig keer een ander verhaal",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    kaal(ax)
    return als_uri(fig), {"beste": max(eind.values()), "slechtste": min(eind.values())}


def plaat_acties_tegenover_klas(eigen, rest):
    """Wat elke actie oplevert, naast wat diezelfde actie de klas oplevert."""
    def gemiddelden(regels):
        per = defaultdict(list)
        for r in regels:
            if r["actie"]:
                per[r["actie"]].append(r["winst"])
        return {a: statistics.fmean(v) for a, v in per.items()}, \
               {a: len(v) for a, v in per.items()}

    mijn, aantal = gemiddelden(eigen)
    hun, _ = gemiddelden(rest)
    acties = [a for a in VOLGORDE if a in mijn or a in hun]

    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    y = np.arange(len(acties))
    ax.barh(y + 0.19, [hun.get(a, 0) for a in acties], height=0.36,
            color=GEDEMPT, alpha=0.55, label="de rest van de klas")
    ax.barh(y - 0.19, [mijn.get(a, 0) for a in acties], height=0.36,
            color=ORANJE, label="deze bot")
    for i, a in enumerate(acties):
        if a not in mijn:
            continue
        waarde = mijn[a]
        ax.text(waarde + (6 if waarde >= 0 else -6), i - 0.19,
                f"{waarde:+.0f}  (n={aantal[a]})", va="center",
                ha="left" if waarde >= 0 else "right",
                color=INKT, fontsize=9.5, fontweight="bold")
    ax.axvline(0, color=INKT, linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([a.replace("_", " ") for a in acties], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("gemiddelde winst per hand (chips)")
    ax.set_title("Levert zijn raise meer op dan die van de klas?",
                 color=INKT, fontsize=12.5, pad=26, loc="left")
    ax.legend(frameon=False, fontsize=10, ncol=2, loc="lower right",
              bbox_to_anchor=(1.0, 1.005))
    kaal(ax, y=False)
    alles = [v for v in list(mijn.values()) + list(hun.values())]
    marge = (max(alles) - min(min(alles), 0)) * 0.3
    ax.set_xlim(min(min(alles), 0) - marge, max(alles) + marge)
    return als_uri(fig)


def plaat_handsoorten(prof, klasbeeld):
    """Per soort hand wat hij ermee deed, met de klas eronder op dezelfde schaal."""
    soorten = [s for s in ("paar", "twee hoge", "één hoge", "twee lage")
               if s in prof["per_handsoort"]]
    if not soorten:
        return None

    fig, assen = plt.subplots(2, 1, figsize=(9.2, 6.4), sharex=True,
                              gridspec_kw={"hspace": 0.40})
    for ax, bron, titel in ((assen[0], "eigen", "Deze bot"),
                            (assen[1], "klas", "De klas (gemiddelde per handsoort)")):
        links = np.zeros(len(soorten))
        for actie in VOLGORDE:
            waarden = []
            for s in soorten:
                if bron == "eigen":
                    teller = prof["per_handsoort"][s]
                    totaal = sum(teller.values()) or 1
                    waarden.append(100 * teller.get(actie, 0) / totaal)
                else:
                    waarden.append(klasbeeld.get(s, {}).get(actie, 0.0))
            waarden = np.array(waarden)
            if waarden.sum() == 0:
                continue
            ax.barh(soorten, waarden, left=links, height=0.62,
                    color=ACTIEKLEUR[actie],
                    label=actie.replace("_", " ") if bron == "eigen" else None)
            for i, w in enumerate(waarden):
                if w >= 8:
                    ax.text(links[i] + w / 2, i, f"{w:.0f}%", ha="center", va="center",
                            color="white" if actie in ACTIE_LABEL_WIT else INKT,
                            fontsize=9.5, fontweight="bold")
            links += waarden
        ax.set_xlim(0, 100)
        ax.invert_yaxis()
        ax.set_title(titel, color=INKT, fontsize=11, loc="left", pad=6)
        kaal(ax, y=False)
        ax.tick_params(axis="y", labelsize=11)

    assen[1].set_xlabel("aandeel van de handen van dat soort (%)")
    assen[0].legend(frameon=False, fontsize=9.5, ncol=5, loc="lower right",
                    bbox_to_anchor=(1.0, 1.12))
    fig.suptitle("Wat deed hij met welke kaarten — en wat deed de klas?",
                 color=INKT, fontsize=12.5, x=0.055, y=0.99, ha="left")
    return als_uri(fig)


def plaat_per_ronde(beslissingen, klastrechter):
    """Hoe ver kwam hij per hand, en hoe ver komt de klas?

    Zijn aantallen en die van de klas zijn niet vergelijkbaar -- de een speelt meer
    handen dan de ander. Rechts daarom als percentage van de eigen
    preflop-beslissingen: van elke honderd handen, hoeveel haalt de flop, de turn,
    de river?
    """
    if not beslissingen:
        return None
    telling = Counter(b["ronde"] for b in beslissingen)
    preflop = telling.get("preflop", 0)
    if not preflop:
        return None
    straten = [s for s in STRATEN if telling.get(s)]

    fig, assen = plt.subplots(1, 2, figsize=(9.6, 3.9),
                              gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.34})

    ax = assen[0]
    onder = np.zeros(len(straten))
    for actie in VOLGORDE:
        waarden = np.array([Counter(b["gekozen"] for b in beslissingen
                                    if b["ronde"] == s).get(actie, 0) for s in straten])
        if waarden.sum() == 0:
            continue
        ax.bar(straten, waarden, bottom=onder, width=0.58,
               color=ACTIEKLEUR[actie], label=actie.replace("_", " "))
        onder += waarden
    for i, s in enumerate(straten):
        ax.text(i, telling[s] + max(onder) * 0.03, str(telling[s]), ha="center",
                color=INKT, fontsize=9.5, fontweight="bold")
    ax.set_ylabel("aantal beslissingen")
    ax.set_title("Wat deed hij per straat?", color=INKT, fontsize=11, loc="left", pad=6)
    ax.legend(frameon=False, fontsize=8.5, ncol=3, loc="upper right")
    kaal(ax)
    ax.set_ylim(0, max(onder) * 1.30)

    # Preflop is per definitie 100% voor iedereen; die balk zegt niets. Alleen
    # de straten erna laten zien hoe ver iemand komt.
    ax = assen[1]
    verder = [s for s in STRATEN if s != "preflop"]
    x = np.arange(len(verder))
    mijn = [100 * telling.get(s, 0) / preflop for s in verder]
    hun = [klastrechter.get(s, 0) for s in verder]
    ax.bar(x - 0.2, mijn, width=0.38, color=ORANJE, label="deze bot")
    ax.bar(x + 0.2, hun, width=0.38, color=GEDEMPT, alpha=0.55, label="klasgemiddelde")
    for i, (a, b) in enumerate(zip(mijn, hun)):
        ax.text(i - 0.2, a + 2.5, f"{a:.0f}", ha="center", color=INKT,
                fontsize=9, fontweight="bold")
        ax.text(i + 0.2, b + 2.5, f"{b:.0f}", ha="center", color=GEDEMPT, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(verder, fontsize=9.5)
    ax.set_ylabel("% van je preflop-handen")
    ax.set_title("Hoe ver kom je ná preflop?", color=INKT, fontsize=11,
                 loc="left", pad=6)
    ax.legend(frameon=False, fontsize=9)
    kaal(ax)
    ax.set_ylim(0, max(max(mijn), max(hun)) * 1.24)
    return als_uri(fig)


# De handmatrix, net als in analyse_toernooi.py: hoogste kaart op de rij, laagste
# op de kolom, alleen de bovenste driehoek gevuld. A-K en K-A zijn dezelfde hand.
MATRIX_RANGEN = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]
DIV_LAAG, DIV_MIDDEN, DIV_HOOG = "#2a78d6", "#F0F2F3", "#1B5E4A"
ACTIERAMP = ["#d7e6f2", "#a8cfdc", "#6fb8ae", "#3a8f7a", "#1B5E4A"]


def _matrix_van(waarden):
    m = np.full((13, 13), np.nan)
    for naam, waarde in waarden.items():
        hoog, laag = naam.split("-")
        if hoog not in MATRIX_RANGEN or laag not in MATRIX_RANGEN:
            continue
        i, j = MATRIX_RANGEN.index(hoog), MATRIX_RANGEN.index(laag)
        m[min(i, j), max(i, j)] = waarde
    return m


def _heatmap(m, titel, ondertitel, eenheid, cmap, norm, labelformaat,
             lichtgrens=None):
    """Eén handmatrix. lichtgrens: boven deze waarde wordt het celletje wit gezet."""
    fig, ax = plt.subplots(figsize=(7.6, 6.5))
    cmap.set_bad("#F7F8F8")
    beeld = ax.imshow(np.ma.masked_invalid(m), cmap=cmap, norm=norm, aspect="equal")
    for i in range(13):
        for j in range(13):
            if np.isnan(m[i, j]):
                continue
            licht = lichtgrens is not None and m[i, j] >= lichtgrens
            ax.text(j, i, labelformaat(m[i, j]), ha="center", va="center",
                    fontsize=6.6, color="white" if licht else INKT)
    ax.set_xticks(range(13)); ax.set_xticklabels(MATRIX_RANGEN, fontsize=9)
    ax.set_yticks(range(13)); ax.set_yticklabels(MATRIX_RANGEN, fontsize=9)
    ax.set_xticks(np.arange(-0.5, 13, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 13, 1), minor=True)
    ax.grid(which="minor", color="#FFFFFF", linewidth=1.5)
    ax.tick_params(which="both", length=0)
    for kant in ("top", "right", "bottom", "left"):
        ax.spines[kant].set_visible(False)
    ax.set_title(titel, color=INKT, fontsize=12.5, pad=30, loc="left")
    ax.text(-0.5, -0.95, ondertitel, color=GEDEMPT, fontsize=9.5, va="bottom")
    balk = fig.colorbar(beeld, ax=ax, fraction=0.046, pad=0.03)
    balk.set_label(eenheid, color=GEDEMPT, fontsize=9.5)
    balk.outline.set_visible(False)
    balk.ax.tick_params(length=0, labelsize=9)
    return als_uri(fig)


def plaat_matrix_actie(eigen, minimaal=4):
    """Per starthand hoe hard hij speelde, op de schaal fold (0) tot all in (4).

    Dezelfde drempel als de winstmatrix, met opzet: de twee zijn bedoeld om naast
    elkaar te leggen, en dan moeten dezelfde vakjes gevuld zijn. Anders lijkt een
    leeg vakje een bewering terwijl het een drempelverschil is.
    """
    schaal = {a: i for i, a in enumerate(VOLGORDE)}
    per_hand = defaultdict(list)
    for r in eigen:
        if r["actie"] in schaal:
            per_hand[handnaam(r["hand"])].append(schaal[r["actie"]])
    genoeg = {h: statistics.fmean(v) for h, v in per_hand.items()
              if len(v) >= minimaal}
    if len(genoeg) < 10:
        return None
    cmap = LinearSegmentedColormap.from_list("actie", ACTIERAMP)
    return _heatmap(
        _matrix_van(genoeg),
        "Hoe hard speelde hij elke starthand?",
        f"0 = altijd fold, 4 = altijd all in  ·  hoogste kaart op de rij  ·  "
        f"alleen handen die minstens {minimaal}x voorkwamen "
        f"({len(genoeg)} van de {len(per_hand)})",
        "gemiddelde keuze (fold → all in)", cmap,
        plt.Normalize(vmin=0, vmax=4), lambda v: f"{v:.1f}", lichtgrens=2.6)


def plaat_matrix_winst(eigen, minimaal=4):
    """Per starthand wat hij er gemiddeld mee verdiende of verloor."""
    per_hand = defaultdict(list)
    for r in eigen:
        if r["actie"] is not None:
            per_hand[handnaam(r["hand"])].append(r["winst"])
    genoeg = {h: statistics.fmean(v) for h, v in per_hand.items()
              if len(v) >= minimaal}
    if len(genoeg) < 10:
        return None
    m = _matrix_van(genoeg)
    # Niet op het maximum schalen: één uitschieter maakt dan alle andere vakjes
    # kleurloos. Op het 92e percentiel schalen houdt het midden leesbaar.
    grens = float(np.nanpercentile(np.abs(m), 92)) or 1.0
    cmap = LinearSegmentedColormap.from_list("winst", [DIV_LAAG, DIV_MIDDEN, DIV_HOOG])
    return _heatmap(
        m, "En met welke starthanden verdiende hij?",
        f"gemiddelde winst per keer dat die hand voorkwam  ·  groen is winst, "
        f"blauw is verlies  ·  minstens {minimaal}x voorgekomen "
        f"({len(genoeg)} van de {len(per_hand)})",
        "gemiddelde winst (chips)", cmap,
        TwoSlopeNorm(vmin=-grens, vcenter=0, vmax=grens), lambda v: f"{v:+.0f}")


RANGORDE = {rang: i for i, rang in enumerate(
    ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"])}


def handnaam(hand):
    """['K', 'A'] en ['A', 'K'] geven allebei 'A-K'.

    Sorteren op rangwaarde en niet alfabetisch, anders komt "10" voor "9" --
    het is tekst, geen getal.
    """
    hoog, laag = sorted(hand, key=lambda r: RANGORDE.get(str(r), -1), reverse=True)
    return f"{hoog}-{laag}"


def _per_handnaam(regels, minimaal=6):
    """{handnaam: lijst winsten}, alleen handen die vaak genoeg voorkwamen.

    Onder een stuk of zes keer is een gemiddelde geen gemiddelde maar een
    anekdote, en die wil je niet op een plaat zetten waar iemand op bevraagd wordt.
    """
    per_hand = defaultdict(list)
    for r in regels:
        if r["actie"] is None:
            continue
        per_hand[handnaam(r["hand"])].append(r["winst"])
    return {h: w for h, w in per_hand.items() if len(w) >= minimaal}


def plaat_winst_per_hand(eigen, klas_regels, hoeveel=10):
    """Met welke kaarten verdiende hij, en met welke verloor hij?

    Gemiddelde winst per keer dat de hand voorkwam, niet het totaal: anders
    vergelijk je een hand die hij vaak kreeg met een hand die de klas vaak kreeg.
    """
    mijn = _per_handnaam(eigen)
    if not mijn:
        return None
    hun = _per_handnaam(klas_regels, minimaal=20)

    gemiddeld = {h: statistics.fmean(w) for h, w in mijn.items()}
    op_winst = sorted(gemiddeld, key=gemiddeld.get)
    gekozen = list(dict.fromkeys(op_winst[:hoeveel // 2] + op_winst[-(hoeveel // 2):]))

    fig, ax = plt.subplots(figsize=(9.2, 0.42 * len(gekozen) + 2.0))
    y = np.arange(len(gekozen))
    waarden = [gemiddeld[h] for h in gekozen]
    ax.barh(y, waarden, height=0.62,
            color=[GROEN if w > 0 else ORANJE for w in waarden])
    eerste = True
    for i, h in enumerate(gekozen):
        if h in hun:
            ax.plot([statistics.fmean(hun[h])], [i], marker="D", markersize=6,
                    color=INKT, zorder=5,
                    label="klasgemiddelde" if eerste else None)
            eerste = False
    for i, (h, w) in enumerate(zip(gekozen, waarden)):
        ax.text(w + (10 if w >= 0 else -10), i, f"{w:+.0f}  (n={len(mijn[h])})",
                va="center", ha="left" if w >= 0 else "right",
                color=INKT, fontsize=9, fontweight="bold")
    ax.axvline(0, color=INKT, linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels(gekozen, fontsize=10.5, fontfamily="monospace")
    ax.set_xlabel("gemiddelde winst per keer dat je die hand kreeg (chips)")
    ax.set_title("Met welke kaarten verdiende hij, en met welke verloor hij?",
                 color=INKT, fontsize=12.5, pad=24, loc="left")
    if not eerste:
        ax.legend(frameon=False, fontsize=9.5, loc="lower right",
                  bbox_to_anchor=(1.0, 1.005))
    kaal(ax, y=False)
    marge = (max(waarden) - min(min(waarden), 0)) * 0.38
    ax.set_xlim(min(min(waarden), 0) - marge, max(max(waarden), 0) + marge)
    return als_uri(fig)


def plaat_agressie_per_hand(eigen, klas_regels, hoeveel=12):
    """Hoe hard speelt hij elke hand, op de schaal fold -> all in?

    Elke actie krijgt een plek op die schaal: fold 0, call 1, raise 2, grote raise
    3, all in 4. Het gemiddelde per hand is dan één getal dat zegt hoe ver hij met
    die kaarten gaat, en dat is direct naast de klas te leggen.
    """
    schaal = {a: i for i, a in enumerate(VOLGORDE)}

    def gemiddelde(regels, minimaal):
        """Per hand: het gemiddelde op de schaal, hoe vaak, en wat hij het VAAKST koos."""
        per_hand = defaultdict(list)
        for r in regels:
            if r["actie"] in schaal:
                per_hand[handnaam(r["hand"])].append(r["actie"])
        uit = {}
        for h, acties in per_hand.items():
            if len(acties) < minimaal:
                continue
            vaakst = Counter(acties).most_common(1)[0][0]
            uit[h] = (statistics.fmean([schaal[a] for a in acties]), len(acties), vaakst)
        return uit

    mijn = gemiddelde(eigen, 6)
    if not mijn:
        return None
    hun = gemiddelde(klas_regels, 20)
    gekozen = sorted(mijn, key=lambda h: mijn[h][0], reverse=True)[:hoeveel]

    fig, ax = plt.subplots(figsize=(9.2, 0.40 * len(gekozen) + 2.1))
    y = np.arange(len(gekozen))
    waarden = [mijn[h][0] for h in gekozen]
    # De LENGTE is het gemiddelde op de schaal, de KLEUR is wat hij met die hand
    # het vaakst koos. Twee dingen die uit elkaar kunnen lopen: een bot die meestal
    # foldt maar af en toe all-in gaat heeft een korte balk in fold-kleur.
    ax.barh(y, waarden, height=0.6, color=[ACTIEKLEUR[mijn[h][2]] for h in gekozen])
    eerste = True
    for i, h in enumerate(gekozen):
        if h in hun:
            ax.plot([hun[h][0]], [i], marker="D", markersize=6, color=INKT,
                    zorder=5, label="klasgemiddelde" if eerste else None)
            eerste = False
        ax.text(waarden[i] + 0.07, i,
                f"{mijn[h][2].replace('_', ' ')} · n={mijn[h][1]}", va="center",
                color=GEDEMPT, fontsize=8.5)
    ax.set_yticks(y)
    ax.set_yticklabels(gekozen, fontsize=10.5, fontfamily="monospace")
    ax.invert_yaxis()
    ax.set_xlim(0, 5.5)
    ax.set_xticks(range(5))
    ax.set_xticklabels([a.replace("_", " ") for a in VOLGORDE], fontsize=9.5)
    ax.set_xlabel("gemiddelde keuze met die hand")
    ax.set_title("Hoe hard speelt hij elke hand — en de klas?",
                 color=INKT, fontsize=12.5, pad=24, loc="left")
    ax.set_xticks(range(5))
    if not eerste:
        ax.legend(frameon=False, fontsize=9.5, loc="lower right",
                  bbox_to_anchor=(1.0, 1.005))
    kaal(ax, y=False)
    ax.grid(axis="x", color=LIJN, linewidth=0.8)
    ax.set_axisbelow(True)
    return als_uri(fig)


# ---------------------------------------------------------------- de vragen
def maak_vragen(prof, mediaan, klasbeeld, klastrechter, klaswinst, klas_odds,
                beslissingen, plek, aantal, stand):
    """
    Vragen die uit de VERSCHILLEN met de klas volgen.

    Absolute drempels werken hier niet. "Minder dan 8% haalt de river" klinkt als
    weinig, maar is de klasmediaan 2%, dan gaat deze bot juist drie keer zo ver --
    en dan stel je de omgekeerde vraag. Elke vraag zet zijn getal dus naast dat
    van de klas, en de richting volgt uit het verschil.

    Geen quizvragen: het goede antwoord is een redenering over zijn eigen regels.
    """
    vragen = []
    totaal = prof["aan_zet"] or 1

    def deel(actie):
        return 100 * prof["acties"].get(actie, 0) / totaal

    # 1 -- de grootste afwijking in wat hij kiest
    afwijkingen = [(abs(deel(a) - mediaan.get(a, 0)), a, deel(a), mediaan.get(a, 0))
                   for a in VOLGORDE if prof["acties"].get(a, 0) >= 10]
    if afwijkingen:
        _, actie, mijn, hun = max(afwijkingen)
        keer = mijn / hun if hun > 0.5 else None
        hoeveel = (f"{keer:.0f} keer zo vaak" if keer and keer >= 1.8
                   else ("vaker" if mijn > hun else "minder vaak"))
        vragen.append((
            f"Je bot koos <b>{actie.replace('_', ' ')}</b> in {mijn:.0f}% van de handen "
            f"waarin hij aan zet kwam. De klas zit gemiddeld op {hun:.0f}%.",
            f"Je doet dit {hoeveel} als de rest. Welke regel in jouw code "
            f"veroorzaakt dat, en was dat de bedoeling?"))

    # 2 -- de handsoort waar hij het meest van de klas afwijkt
    kandidaten = []
    for soort, teller in prof["per_handsoort"].items():
        n = sum(teller.values())
        if n < 15 or soort not in klasbeeld:
            continue
        for actie in VOLGORDE:
            mijn = 100 * teller.get(actie, 0) / n
            hun = klasbeeld[soort].get(actie, 0)
            if mijn >= 10 or hun >= 10:
                kandidaten.append((abs(mijn - hun), soort, actie, mijn, hun, n))
    if kandidaten:
        _, soort, actie, mijn, hun, n = max(kandidaten)
        vragen.append((
            f"Met <b>{soort}</b> koos je {mijn:.0f}% van de keren "
            f"<b>{actie.replace('_', ' ')}</b> — bij de klas is dat {hun:.0f}%. "
            f"Je speelde {n} van zulke handen.",
            f"Dat is {'veel vaker' if mijn > hun else 'veel minder'} dan de rest. "
            f"Wat weet jouw bot over dit soort hand dat de anderen niet gebruiken "
            f"— of andersom?"))

    # 3 -- dezelfde actie, een ander resultaat dan bij de klas
    verschillen = [(abs(w - klaswinst[a]), a, w, klaswinst[a])
                   for a, w in prof["winst_per_actie"].items()
                   if a in klaswinst and prof["acties"].get(a, 0) >= 10]
    if verschillen:
        _, actie, mijn, hun = max(verschillen)
        vragen.append((
            f"<b>{actie.replace('_', ' ')}</b> leverde jou gemiddeld {mijn:+.0f} chips "
            f"per hand op. Bij de klas levert diezelfde actie {hun:+.0f} op.",
            f"Dezelfde zet, een ander resultaat — dus het zit in wannéér je hem "
            f"kiest. Wat maakt jouw {actie.replace('_', ' ')} "
            f"{'beter' if mijn > hun else 'duurder'} dan die van de rest?"))

    # 4 -- hoe ver kom je, naast de klas
    if beslissingen and klastrechter:
        telling = Counter(b["ronde"] for b in beslissingen)
        preflop = telling.get("preflop", 0) or 1
        mijn = 100 * telling.get("river", 0) / preflop
        hun = klastrechter.get("river", 0)
        if hun > 0.3 and abs(mijn - hun) / max(hun, 0.3) > 0.4:
            if mijn > hun:
                vragen.append((
                    f"Van je preflop-handen haalt <b>{mijn:.0f}%</b> de river. "
                    f"Bij de klas is dat gemiddeld {hun:.0f}%.",
                    "Je blijft dus veel langer in de hand zitten dan de rest. "
                    "Kijkt je bot onderweg nog of zijn hand nog goed is, of "
                    "beslist hij vooral preflop en betaalt hij daarna door?"))
            else:
                vragen.append((
                    f"Van je preflop-handen haalt maar <b>{mijn:.0f}%</b> de river. "
                    f"Bij de klas is dat gemiddeld {hun:.0f}%.",
                    "Je bent eerder uit de hand dan de rest. Dat is veilig, maar "
                    "je wint ook nooit een grote pot. Waar zit die rem in je code?"))

        calls = [b for b in beslissingen
                 if b["gekozen"] == "call" and b["inzet_om_te_callen"] > 0]
        if len(calls) >= 10 and klas_odds:
            mijn_odds = 100 * statistics.fmean(
                [b["inzet_om_te_callen"] / (b["pot"] + b["inzet_om_te_callen"])
                 for b in calls])
            vragen.append((
                f"Als je callde, betaalde je gemiddeld <b>{mijn_odds:.0f}%</b> van de "
                f"pot om mee te mogen doen ({len(calls)} keer, over alle straten). "
                f"De klas betaalt {klas_odds:.0f}%.",
                "Je hand hoeft maar in dat percentage van de gevallen de beste te "
                "zijn om callen lonend te maken. Rekent je bot dat uit, of callt "
                "hij op de kaarten alleen?"))

    # 5 -- altijd: de spreiding
    vragen.append((
        f"Je eindigde op <b>{nl(stand)}</b> chips, plek {plek} van {aantal}.",
        "Over twintig simulaties zat daar een flinke spreiding in. Wat zou er "
        "gebeuren als we dit toernooi met een andere kaartverdeling opnieuw "
        "draaiden — en hoeveel van je plek is dan nog van jou?"))
    return vragen


# ---------------------------------------------------------------- het document
STIJL = """
  :root{
    --vilt:#1B4D3E;--inkt:#121E31;--papier:#F7F8F6;--vlak:#FFFFFF;
    --vlak-zacht:#EEF2EF;--gedempt:#59636B;--lijn:#DCE3DE;--oker:#8A6A12;
  }
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --vilt:#5FB894;--inkt:#E6EDE9;--papier:#10171A;--vlak:#161F23;
    --vlak-zacht:#1C282B;--gedempt:#9AA8A4;--lijn:#2A3A3B;--oker:#D8B25A;}}
  :root[data-theme="dark"]{
    --vilt:#5FB894;--inkt:#E6EDE9;--papier:#10171A;--vlak:#161F23;
    --vlak-zacht:#1C282B;--gedempt:#9AA8A4;--lijn:#2A3A3B;--oker:#D8B25A;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--papier);color:var(--inkt);
    font-family:"Public Sans","Segoe UI",system-ui,-apple-system,sans-serif;
    font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
  .blad{max-width:52rem;margin:0 auto;padding:2.8rem 1.4rem 5rem}
  h1,h2{font-family:Literata,Georgia,serif;text-wrap:balance;margin:0}
  h1{font-size:2.1rem;font-weight:700;line-height:1.16;letter-spacing:-.015em}
  h2{font-size:1.4rem;font-weight:600;margin:2.8rem 0 .3rem}
  .stempel{font-family:"IBM Plex Mono",monospace;font-size:.72rem;
    text-transform:uppercase;letter-spacing:.12em;color:var(--vilt);
    font-weight:500;display:block;margin-bottom:.8rem}
  header{border-bottom:2px solid var(--vilt);padding-bottom:1.6rem;margin-bottom:1.4rem}
  .kerncijfers{display:flex;flex-wrap:wrap;gap:1.6rem 2.6rem;margin-top:1.2rem}
  .kerncijfer .label{font-family:"IBM Plex Mono",monospace;font-size:.7rem;
    text-transform:uppercase;letter-spacing:.08em;color:var(--gedempt);display:block}
  .kerncijfer .waarde{font-size:1.5rem;font-weight:700;
    font-variant-numeric:tabular-nums;line-height:1.2}
  .sub{color:var(--gedempt);font-size:.88rem;margin:.2rem 0 1rem;max-width:42rem}
  figure{margin:1.4rem 0 0}
  figure img{width:100%;height:auto;display:block;border:1px solid var(--lijn);border-radius:4px}
  .vraag{background:var(--vlak);border-left:3px solid var(--vilt);
    padding:1rem 1.1rem;margin:1rem 0 0;border-radius:0 4px 4px 0}
  .vraag .cijfer{margin:0;font-size:.95rem}
  .vraag .stel{margin:.55rem 0 0;font-weight:600;color:var(--vilt)}
  .handtitel{font-weight:600;margin:1.8rem 0 0;max-width:42rem}
  .nummer{font-family:"IBM Plex Mono",monospace;font-size:.72rem;color:var(--gedempt);
    letter-spacing:.08em;display:block;margin-bottom:.35rem}
  table{border-collapse:collapse;width:100%;font-size:.88rem;margin-top:1rem}
  th,td{text-align:left;padding:.4rem .8rem .4rem 0;border-bottom:1px solid var(--lijn)}
  th{font-family:"IBM Plex Mono",monospace;font-size:.7rem;text-transform:uppercase;
    letter-spacing:.06em;color:var(--gedempt);font-weight:500}
  td.getal{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
  footer{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--lijn);
    color:var(--gedempt);font-size:.82rem}
  code{font-family:"IBM Plex Mono",monospace;font-size:.89em;
    background:var(--vlak-zacht);padding:.08em .34em;border-radius:3px}

  /* een uitgespeelde hand */
  .hand{background:var(--vlak);border:1px solid var(--lijn);border-radius:6px;
    padding:1.1rem 1.2rem;margin:.9rem 0 0}
  .handkop{font-family:"IBM Plex Mono",monospace;font-size:.72rem;
    text-transform:uppercase;letter-spacing:.08em;color:var(--gedempt);
    display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;
    border-bottom:1px solid var(--lijn);padding-bottom:.6rem}
  .handkop .pot{color:var(--vilt);font-weight:500}
  .tafel{display:flex;flex-wrap:wrap;gap:.5rem 1.5rem;margin:.9rem 0 .2rem}
  .speler{display:flex;align-items:center;gap:.45rem;font-size:.86rem}
  .speler .naam{color:var(--gedempt);font-variant-numeric:tabular-nums}
  .speler.ik .naam{color:var(--inkt);font-weight:700}
  .speler .winst{font-family:"IBM Plex Mono",monospace;font-weight:600;
    font-variant-numeric:tabular-nums}
  .speler .winst.plus{color:var(--vilt)}
  .speler .winst.min{color:#B3261E}
  @media (prefers-color-scheme:dark){
    :root:not([data-theme="light"]) .speler .winst.min{color:#F08A80}}
  :root[data-theme="dark"] .speler .winst.min{color:#F08A80}
  .kaart{display:inline-block;min-width:1.6em;padding:.05em .28em;margin-right:.13em;
    border:1px solid var(--lijn);border-radius:3px;background:#fff;color:#121E31;
    font-size:.8rem;font-weight:700;text-align:center}
  .kaart.rood{color:#C0392B}
  .geenkaart{color:var(--gedempt);font-style:italic;font-size:.8rem}
  .straten{display:grid;grid-template-columns:repeat(auto-fit,minmax(12.5rem,1fr));
    gap:.85rem;margin-top:.9rem}
  .straat{background:var(--vlak-zacht);border-radius:4px;padding:.6rem .7rem}
  .straatkop{display:flex;align-items:center;gap:.45rem;flex-wrap:wrap;margin-bottom:.45rem}
  .straatnaam{font-family:"IBM Plex Mono",monospace;font-size:.66rem;
    text-transform:uppercase;letter-spacing:.08em;color:var(--vilt);font-weight:600}
  table.zetten{font-size:.78rem;margin:0}
  table.zetten th{font-size:.6rem;padding:.2rem .45rem .2rem 0}
  table.zetten td{padding:.22rem .45rem .22rem 0;border-bottom:1px solid var(--lijn)}
  table.zetten tr:last-child td{border-bottom:none}
  table.zetten .naam{color:var(--gedempt);font-variant-numeric:tabular-nums}
  table.zetten tr.ik .naam{color:var(--inkt);font-weight:700}
  table.zetten .zet{font-weight:600}
  table.zetten tr.ik .zet{color:var(--vilt)}
  .reconstructie{color:var(--gedempt);font-size:.74rem;margin:.8rem 0 0;font-style:italic}
"""


def hand_als_html(sleutel, rijen, student, winst_van, kort):
    """
    Eén hand, straat voor straat, als HTML.

    Dezelfde reconstructie als scripts/laat_hand_zien.py: de log bewaart per bot
    zijn eigen zetten, niet de tafel als geheel, dus de volgorde binnen een straat
    komt uit de pot. Die groeit alleen als er chips in gaan, dus een hogere pot is
    een latere zet; bij een gelijke pot kwam de speler die hem ophoogde als
    laatste. Dat staat ook onder de hand vermeld -- een reconstructie die zich
    voordoet als waarneming liegt.
    """
    simulatie, tafel, nummer = sleutel
    gesorteerd = sorted(rijen, key=zet_volgorde)

    eersten = {}
    for r in gesorteerd:
        eersten.setdefault(r["bot_naam"], r)
    resultaat = {b: winst_van(b, simulatie, nummer) for b in eersten}
    winnaar = max(resultaat, key=resultaat.get)
    pot_eind = max(r["pot"] for r in gesorteerd)

    def kaartjes(codes):
        uit = []
        for code in codes or []:
            tekst = kaart(code)
            rood = tekst.endswith("\u2665") or tekst.endswith("\u2666")
            klasse = "kaart rood" if rood else "kaart"
            uit.append(f'<span class="{klasse}">{tekst}</span>')
        return "".join(uit)

    spelers = []
    for bot, eerste in sorted(eersten.items(), key=lambda kv: -resultaat[kv[0]]):
        w = resultaat[bot]
        klasse = "ik" if bot == student else ("winnaar" if bot == winnaar else "")
        kleur = "plus" if w > 0 else ("min" if w < 0 else "")
        spelers.append(
            f'<div class="speler {klasse}"><span class="naam">{kort(bot)}</span>'
            f'<span class="kaarten">{kaartjes(eerste.get("hand_met_kleur") or eerste.get("hand"))}</span>'
            f'<span class="winst {kleur}">{w:+d}</span></div>')

    straten_html = []
    for straat in STRATEN:
        zetten = [r for r in gesorteerd if r["ronde"] == straat]
        if not zetten:
            continue
        bord = (kaartjes(zetten[0]["bord"]) if zetten[0]["bord"]
                else '<span class="geenkaart">nog geen kaarten</span>')
        regels = "".join(
            f'<tr class="{"ik" if r["bot_naam"] == student else ""}">'
            f'<td class="naam">{kort(r["bot_naam"])}</td>'
            f'<td class="getal">{r["pot"]}</td>'
            f'<td class="getal">{r["inzet_om_te_callen"] or "—"}</td>'
            f'<td class="zet">{leesbaar(r)}</td></tr>' for r in zetten)
        straten_html.append(
            f'<div class="straat"><div class="straatkop">'
            f'<span class="straatnaam">{straat}</span>{bord}</div>'
            f'<table class="zetten"><thead><tr><th>wie</th><th class="getal">pot</th>'
            f'<th class="getal">te callen</th><th>deed</th></tr></thead>'
            f'<tbody>{regels}</tbody></table></div>')

    return (f'<div class="hand"><div class="handkop">'
            f'simulatie {simulatie} · tafel {tafel} · hand {nummer}'
            f'<span class="pot">pot liep op tot {nl(pot_eind)}</span></div>'
            f'<div class="tafel">{"".join(spelers)}</div>'
            f'<div class="straten">{"".join(straten_html)}</div>'
            f'<p class="reconstructie">Volgorde binnen een straat teruggerekend uit '
            f'de pot — die groeit alleen als er chips in gaan.</p></div>')


def bouw_document(student, bonus, plek, aantal, stand, platen, vragen, handen,
                  week, ronde):
    def figuur(uri, bijschrift):
        if not uri:
            return ""
        return (f'<figure><img src="{uri}" alt="{bijschrift}">'
                f'<figcaption class="sub">{bijschrift}</figcaption></figure>')

    vraagblokken = "".join(
        f'<div class="vraag"><span class="nummer">Vraag {i}</span>'
        f'<p class="cijfer">{cijfer}</p><p class="stel">{stel}</p></div>'
        for i, (cijfer, stel) in enumerate(vragen, 1))

    handblokken = "".join(
        f'<p class="handtitel">{waarom}</p>{html_hand}'
        for waarom, html_hand in handen)

    return f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bot {student}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600;7..72,700&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{STIJL}</style></head><body><div class="blad">

<header>
  <span class="stempel">Poker Analytics Challenge &middot; week {week}, toernooi {ronde} &middot; overhoring</span>
  <h1>Bot {student}</h1>
  <div class="kerncijfers">
    <div class="kerncijfer"><span class="label">eindstand</span>
      <span class="waarde">{nl(stand)}</span></div>
    <div class="kerncijfer"><span class="label">plek</span>
      <span class="waarde">{plek} <span style="font-size:.95rem;font-weight:400;color:var(--gedempt)">van {aantal}</span></span></div>
    <div class="kerncijfer"><span class="label">bonus</span>
      <span class="waarde" style="color:var(--vilt)">{bonus}</span></div>
  </div>
</header>

<p class="sub">Alle cijfers hieronder komen uit het logboek van dit toernooi. Die data
heeft deze student nooit gezien: hij kent zijn bot van de code, niet van wat die
honderden handen lang werkelijk deed.</p>

<h2>Wat zijn bot deed</h2>
{figuur(platen.get("handsoorten"),
        "Per soort hand: welk deel ging weg, welk deel werd gespeeld — met de "
        "klas eronder op dezelfde schaal.")}
{figuur(platen.get("per_ronde"),
        "Links: op welke straat viel de beslissing, en welke. Rechts welk deel "
        "van zijn preflop-handen de flop, turn en river haalt — als percentage, "
        "want de een speelt nu eenmaal meer handen dan de ander.")}
{figuur(platen.get("matrix_actie"),
        "Dezelfde vraag over alle starthanden tegelijk: de hoogste kaart staat op "
        "de rij, de laagste op de kolom, dus A-K en K-A zijn hetzelfde vakje. "
        "Donker is hard spelen.")}
{figuur(platen.get("agressie_per_hand"),
        "Elke actie krijgt een plek op de schaal fold → all in; de bálklengte is "
        "het gemiddelde met die kaarten, de kléur is wat hij er het vaakst mee "
        "deed, en het ruitje is de klas met dezelfde hand. De twaalf handen "
        "waarmee hij het hardst speelt.")}

<h2>Wat het opleverde</h2>
{figuur(platen.get("matrix_winst"),
        "Dezelfde matrix, maar nu wat elke starthand opleverde. Leg hem naast de "
        "vorige: waar donkergroen in de ene naast blauw in de andere staat, speelt "
        "hij hard met kaarten die hem geld kosten.")}
{figuur(platen.get("winst_per_hand"),
        "De vijf kaarten waarmee hij het meest verloor en de vijf waarmee hij het "
        "meest verdiende, gemiddeld per keer dat hij die hand kreeg. Het ruitje is "
        "wat de klas met dezelfde kaarten haalde.")}
{figuur(platen.get("acties"),
        "Gemiddelde winst per hand, per actie, naast dezelfde actie bij de rest "
        "van de klas.")}
{figuur(platen.get("stackverloop"),
        "Twintig simulaties met dezelfde code. De spreiding is het punt; de "
        "gestreepte lijn is het gemiddelde van de klas op hetzelfde moment.")}

<h2>Vragen om te stellen</h2>
<p class="sub">Geen quizvragen. Het goede antwoord is een redenering over zijn eigen
regels — en of hij het verschil ziet tussen wat hij dacht dat zijn bot deed en wat
er staat.</p>
{vraagblokken}

<h2>Handen om op door te vragen</h2>
<p class="sub">Drie handen waar iets gebeurde, helemaal uitgespeeld. Zijn eigen regel
staat vet. Je hoeft niets op te zoeken — dit is de hand zoals hij gespeeld is.</p>
{handblokken}

<footer>
  Gemaakt met <code>scripts/botdocumenten.py</code> uit het logboek van week {week},
  toernooi {ronde}. De plots zijn dezelfde als in Werkcollege 8, maar dan over deze bot.
</footer>

</div></body></html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde", default="2")
    p.add_argument("--student", help="alleen dit studentnummer")
    p.add_argument("--iedereen", action="store_true",
                   help="ook de studenten zonder bonuspunten")
    args = p.parse_args()

    with open(os.path.join(HIER, f"uitslag_week{args.week}_ronde{args.ronde}.json")) as f:
        uitslag = json.load(f)
    uitgebreid = []
    pad = os.path.join(HIER, f"uitgebreid_week{args.week}_ronde{args.ronde}.json")
    if os.path.exists(pad):
        with open(pad) as f:
            uitgebreid = json.load(f)["regels"]

    bonussen = {}
    pad_bonus = os.path.join(HIER, f"bonus_week{args.week}.json")
    if os.path.exists(pad_bonus):
        with open(pad_bonus) as f:
            for s in json.load(f)["studenten"]:
                bonussen[s["student_id"]] = s["bonus"]

    KLAS = set(uitslag["namen_deelnemers"])
    referentie = set(uitslag.get("referentiebots") or []) | set(uitslag.get("testbots") or [])

    def kort_naam(naam):
        """Klasgenoten afgekort: dit document gaat naar één student."""
        return naam if naam in referentie else f"...{naam[-4:]}"
    regels = winst_per_regel(uitslag["hand_log"])
    per_bot = defaultdict(list)
    for r in regels:
        per_bot[r["bot_naam"]].append(r)
    profielen = {b: profiel(rs) for b, rs in per_bot.items() if b in KLAS}
    mediaan = klas_medianen(profielen)

    stand = sorted(((v, k) for k, v in uitslag["eindstand_per_bot"].items() if k in KLAS),
                   reverse=True)
    plekken = {k: i for i, (_, k) in enumerate(stand, 1)}

    beslissingen_per_bot = defaultdict(list)
    per_hand = defaultdict(list)
    for b in uitgebreid:
        beslissingen_per_bot[b["bot_naam"]].append(b)
        per_hand[(b["simulatie"], b["tafel"], b["hand_nummer"])].append(b)

    # De klascijfers: één keer uitrekenen, elk document gebruikt dezelfde.
    handsoortbeeld = klas_handsoorten(profielen)
    trechter = klas_trechter(beslissingen_per_bot, KLAS)
    stackmediaan = klas_stackmediaan(uitslag["hand_log"], KLAS)
    klaswinst = klas_actiewinst(per_bot, KLAS)
    klas_odds = klas_potodds(beslissingen_per_bot, KLAS)

    if args.student:
        doelen = [args.student]
    elif args.iedereen:
        doelen = [k for _, k in stand]
    else:
        doelen = [k for _, k in stand if bonussen.get(k, 0) > 0]
        if not doelen:
            raise SystemExit(
                f"Geen bonusscoorders gevonden in bonus_week{args.week}.json.\n"
                f"Haal hem op met scripts/controleer_opslag.py, of gebruik --iedereen.")

    uitvoer = os.path.join(HIER, "botdocumenten")
    os.makedirs(uitvoer, exist_ok=True)
    print(f"Week {args.week}, toernooi {args.ronde} — {len(doelen)} document(en)\n")

    for student in doelen:
        if student not in profielen:
            print(f"   {student}: niet in dit toernooi")
            continue
        eigen = per_bot[student]
        rest = [r for b, rs in per_bot.items() if b in KLAS and b != student for r in rs]
        prof = profielen[student]
        eigen_log = [r for r in uitslag["hand_log"] if r["bot_naam"] == student]
        beslissingen = beslissingen_per_bot.get(student, [])

        platen = {}
        platen["stackverloop"], _ = plaat_stackverloop(eigen_log, stackmediaan)
        platen["acties"] = plaat_acties_tegenover_klas(eigen, rest)
        platen["handsoorten"] = plaat_handsoorten(prof, handsoortbeeld)
        platen["per_ronde"] = plaat_per_ronde(beslissingen, trechter)
        platen["winst_per_hand"] = plaat_winst_per_hand(eigen, rest)
        platen["agressie_per_hand"] = plaat_agressie_per_hand(eigen, rest)
        platen["matrix_actie"] = plaat_matrix_actie(eigen)
        platen["matrix_winst"] = plaat_matrix_winst(eigen)

        vragen = maak_vragen(prof, mediaan, handsoortbeeld, trechter, klaswinst,
                             klas_odds, beslissingen, plekken[student], len(stand),
                             int(uitslag["eindstand_per_bot"][student]))
        # opvallende_handen geeft (regel, waarom) terug. De hand erbij zoeken in de
        # uitgebreide log, zodat hij hier uitgespeeld kan worden in plaats van als
        # tabelregel.
        winsten = {(r["simulatie"], r["hand_nummer"]): int(r["winst"])
                   for rs in per_bot.values() for r in rs}
        winsten_per_bot = defaultdict(dict)
        for bot, rs in per_bot.items():
            for r in rs:
                winsten_per_bot[bot][(r["simulatie"], r["hand_nummer"])] = int(r["winst"])

        def winst_van(bot, simulatie, nummer):
            return winsten_per_bot.get(bot, {}).get((simulatie, nummer), 0)

        handen = []
        for r, waarom in opvallende_handen(eigen, 3):
            sleutel = (r["simulatie"], r["tafel"], r["hand_nummer"])
            kop = (f"{waarom[0].upper()}{waarom[1:]} — {'-'.join(r['hand'])}, "
                   f"{r['actie'] or 'niet aan zet'}, {int(r['winst']):+d} chips")
            rijen = per_hand.get(sleutel)
            if not rijen:
                handen.append((kop, '<p class="sub">Deze hand staat niet in de '
                                    'uitgebreide log van deze ronde.</p>'))
                continue
            handen.append((kop, hand_als_html(sleutel, rijen, student,
                                              winst_van, kort_naam)))

        bonus = bonussen.get(student)
        html = bouw_document(
            student, f"{bonus:.1f}".replace(".", ",") if bonus else "—",
            plekken[student], len(stand),
            int(uitslag["eindstand_per_bot"][student]),
            platen, vragen, handen, args.week, args.ronde)
        doel = os.path.join(uitvoer, f"{student}.html")
        with open(doel, "w") as f:
            f.write(html)
        print(f"   {student}  plek {plekken[student]:>2d}  bonus {bonus or 0:.1f}  "
              f"{len(vragen)} vragen  ->  botdocumenten/{student}.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
