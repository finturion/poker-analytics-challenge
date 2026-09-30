# -*- coding: utf-8 -*-
"""Draait alle Data Science-analyses van Werkcollege 8 en tekent de platen.

    python3 scripts/analyse_toernooi.py                    # op scripts/toernooi_test.json
    python3 scripts/analyse_toernooi.py uitslag_week5.json # op een echte export

Schrijft naar powerpoints/plots_wc8/, plus cijfers.json met de getallen die in
het deck staan -- zodat daar niets is overgetypt.

Palet: de drie categorische kleuren zijn de gevalideerde standaard (blauw,
oranje, aqua -- alle zes checks PASS, contrast-WARN op aqua opgevangen met
directe labels). De actie-verdeling is geen categorische maar een OPLOPENDE
schaal (fold -> all_in), dus daar staat een sequentiële groenramp,
lichtheid-monotoon. Winst is polariteit, dus diverging: rood/groen om nul.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PLOTMAP = os.path.join(REPO, "powerpoints", "plots_wc8")
BRON = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HIER, "toernooi_test.json")
os.makedirs(PLOTMAP, exist_ok=True)

INKT = "#121E31"
GEDEMPT = "#5A646B"
LIJN = "#DCE1E6"
WIT = "#FFFFFF"
BLAUW, ORANJE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GROENRAMP = ["#d8e6df", "#a9c9ba", "#6fa68e", "#3a7a61", "#1B4D3E"]
ROOD, GROEN = "#B3261E", "#1B4D3E"

RANGEN = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]
RANGORDE = {r: i for i, r in enumerate(reversed(RANGEN))}

plt.rcParams.update({
    "font.size": 10, "text.color": INKT, "axes.labelcolor": INKT,
    "xtick.color": GEDEMPT, "ytick.color": GEDEMPT,
    "axes.edgecolor": LIJN, "axes.linewidth": 1.0,
})


def bewaar(fig, naam):
    pad = os.path.join(PLOTMAP, naam + ".png")
    fig.savefig(pad, facecolor=WIT, dpi=200, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print("  ", pad)
    return pad


def kaal(ax, x=True, y=True):
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    if not x:
        ax.spines["bottom"].set_visible(False)
    if not y:
        ax.spines["left"].set_visible(False)
    ax.tick_params(length=0)


def hand_naam(hand):
    hoog, laag = sorted(hand, key=RANGORDE.get, reverse=True)
    return f"{hoog}-{laag}"


# ---------------------------------------------------------------- data
resultaat = json.load(open(BRON))
JIJ = "500100001__w5"          # de bot die we als "jij" aanwijzen

hand_log = pd.DataFrame(resultaat["hand_log"])
hand_log = hand_log.sort_values(["bot_naam", "simulatie", "hand_nummer"])
hand_log["winst"] = hand_log.groupby(["bot_naam", "simulatie"])["stack"].diff()
hand_log["hand_naam"] = hand_log["hand"].apply(hand_naam)
speelde_mee = hand_log[hand_log["aan_zet"] & ~hand_log["uitgespeeld"]].copy()

VOLGORDE = ["fold", "call", "raise", "grote_raise", "all_in"]
aanwezig = [a for a in VOLGORDE if a in set(speelde_mee["actie"])]

print(f"{hand_log['bot_naam'].nunique()} bots, "
      f"{hand_log['simulatie'].nunique()} simulaties, "
      f"{len(hand_log)} regels, {len(speelde_mee)} beslissingen")

cijfers = {"bots": int(hand_log["bot_naam"].nunique()),
           "simulaties": int(hand_log["simulatie"].nunique()),
           "regels": len(hand_log), "beslissingen": len(speelde_mee)}


# --------------------------------------------------- 1. actie-verdeling
def plaat_acties():
    deel = (speelde_mee["actie"].value_counts(normalize=True) * 100).reindex(aanwezig).fillna(0)
    fig, ax = plt.subplots(figsize=(8.6, 3.6))
    kleuren = GROENRAMP[:len(aanwezig)]
    balken = ax.barh(range(len(deel)), deel.values, color=kleuren, height=0.62)
    for i, (naam, waarde) in enumerate(zip(deel.index, deel.values)):
        ax.text(waarde + 0.8, i, f"{waarde:.1f}%", va="center", ha="left",
                color=INKT, fontsize=11, fontweight="bold")
    ax.set_yticks(range(len(deel)))
    ax.set_yticklabels([n.replace("_", " ") for n in deel.index], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlim(0, max(deel.values) * 1.22)
    ax.set_xticks([])
    ax.set_title("Wat doet de klas? Aandeel van alle beslissingen",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    kaal(ax, x=False, y=False)
    cijfers["verdeling"] = {k: round(float(v), 1) for k, v in deel.items()}
    return bewaar(fig, "wc8_acties")


# ------------------------------------------- 2. fold-percentage per bot
per_bot = (speelde_mee.assign(is_fold=speelde_mee["actie"].eq("fold"))
           .groupby("bot_naam")
           .agg(fold_pct=("is_fold", "mean"), beslissingen=("is_fold", "size")))
per_bot["fold_pct"] *= 100
eindstand = pd.Series(resultaat["eindstand_per_bot"], name="eindstand")
per_bot = per_bot.join(eindstand)


def plaat_foldverdeling():
    fig, ax = plt.subplots(figsize=(8.6, 3.8))
    ax.hist(per_bot["fold_pct"], bins=14, color=GROENRAMP[1],
            edgecolor=WIT, linewidth=1.5)
    mijn = per_bot.loc[JIJ, "fold_pct"]
    mediaan = per_bot["fold_pct"].median()
    ax.axvline(mediaan, color=GEDEMPT, linewidth=1.5, linestyle=(0, (4, 3)))
    ax.axvline(mijn, color=ORANJE, linewidth=2.5)
    top = ax.get_ylim()[1]
    ax.text(mediaan, top * 0.97, f" mediaan {mediaan:.0f}%", color=GEDEMPT,
            fontsize=10, va="top", ha="left")
    ax.text(mijn, top * 0.80, f" jouw bot {mijn:.0f}%", color=ORANJE,
            fontsize=11, fontweight="bold", va="top", ha="left")
    ax.set_xlabel("percentage van de beslissingen dat een fold was")
    ax.set_ylabel("aantal bots")
    ax.set_title("Hoe tight speelt de klas?", color=INKT, fontsize=12.5, pad=12, loc="left")
    kaal(ax)
    cijfers["fold_mediaan"] = round(float(mediaan), 1)
    cijfers["fold_jij"] = round(float(mijn), 1)
    return bewaar(fig, "wc8_foldverdeling")


# ----------------------------------- 3. fold% tegen eindstand (nieuw!)
def plaat_fold_vs_eindstand():
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    anderen = per_bot.drop(index=JIJ)
    ax.scatter(anderen["fold_pct"], anderen["eindstand"], s=70, color=BLAUW,
               alpha=0.75, edgecolor=WIT, linewidth=1.5, zorder=3, label="een bot in de klas")
    ax.scatter([per_bot.loc[JIJ, "fold_pct"]], [per_bot.loc[JIJ, "eindstand"]],
               s=150, color=ORANJE, edgecolor=WIT, linewidth=2, zorder=4, label="jouw bot")
    ax.axhline(1000, color=GEDEMPT, linewidth=1, linestyle=(0, (4, 3)))
    ax.text(ax.get_xlim()[1], 1000, " startstack", color=GEDEMPT, fontsize=9,
            va="center", ha="left")

    r = per_bot["fold_pct"].corr(per_bot["eindstand"])
    # trendlijn alleen als er iets te zien is
    helling, snijpunt = np.polyfit(per_bot["fold_pct"], per_bot["eindstand"], 1)
    xs = np.array([per_bot["fold_pct"].min(), per_bot["fold_pct"].max()])
    ax.plot(xs, helling * xs + snijpunt, color=GEDEMPT, linewidth=1.5,
            linestyle=(0, (5, 4)), zorder=2)
    ax.set_xlabel("fold-percentage")
    ax.set_ylabel("eindstand (chips)")
    ax.set_title(f"Is tight spelen beter?   correlatie r = {r:+.2f}",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    kaal(ax)
    cijfers["correlatie_fold_eindstand"] = round(float(r), 2)
    return bewaar(fig, "wc8_fold_vs_eindstand")


# ------------------------------------------ 4 & 5. de 13x13 handmatrix
def matrix_van(waarden):
    m = np.full((13, 13), np.nan)
    for naam, waarde in waarden.items():
        hoog, laag = naam.split("-")
        i, j = RANGEN.index(hoog), RANGEN.index(laag)
        m[min(i, j), max(i, j)] = waarde
    return m


def plaat_matrix(waarden, titel, ondertitel, naam, diverging, eenheid):
    m = matrix_van(waarden)
    fig, ax = plt.subplots(figsize=(7.4, 6.4))
    if diverging:
        # Niet op het maximum schalen: A-A ligt zo ver boven de rest dat alle
        # andere vakjes dan wit worden. Op het 92e percentiel schalen houdt het
        # midden leesbaar; wat daarboven ligt loopt tegen het uiteinde aan.
        grens = float(np.nanpercentile(np.abs(m), 92))
        cmap = LinearSegmentedColormap.from_list("winst", [ROOD, "#F2F4F3", GROEN])
        norm = TwoSlopeNorm(vmin=-grens, vcenter=0, vmax=grens)
    else:
        cmap = LinearSegmentedColormap.from_list("fold", GROENRAMP)
        norm = None
    cmap.set_bad("#F7F8F8")
    beeld = ax.imshow(np.ma.masked_invalid(m), cmap=cmap, norm=norm, aspect="equal")
    ax.set_xticks(range(13)); ax.set_xticklabels(RANGEN, fontsize=9)
    ax.set_yticks(range(13)); ax.set_yticklabels(RANGEN, fontsize=9)
    ax.set_xticks(np.arange(-0.5, 13, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 13, 1), minor=True)
    ax.grid(which="minor", color=WIT, linewidth=1.5)
    ax.tick_params(which="both", length=0)
    for kant in ("top", "right", "bottom", "left"):
        ax.spines[kant].set_visible(False)
    ax.set_title(titel, color=INKT, fontsize=12.5, pad=30, loc="left")
    ax.text(-0.5, -0.95, ondertitel, color=GEDEMPT, fontsize=9.5, va="bottom")
    balk = fig.colorbar(beeld, ax=ax, fraction=0.046, pad=0.03)
    balk.set_label(eenheid, color=GEDEMPT, fontsize=9.5)
    balk.outline.set_visible(False)
    balk.ax.tick_params(length=0, labelsize=9)
    return bewaar(fig, naam)


def platen_handmatrix():
    basis = (speelde_mee.assign(is_fold=speelde_mee["actie"].eq("fold"))
             .groupby("hand_naam")
             .agg(keren=("is_fold", "size"), fold_pct=("is_fold", "mean"),
                  gem_winst=("winst", "mean")))
    genoeg = basis[basis["keren"] >= 20]
    cijfers["handen_totaal"] = int(len(basis))
    cijfers["handen_genoeg"] = int(len(genoeg))

    plaat_matrix((genoeg["fold_pct"] * 100).to_dict(),
                 "Welke starthanden gooit de klas weg?",
                 "per starthand het percentage beslissingen dat een fold was  ·  "
                 f"alleen handen die minstens 20x voorkwamen ({len(genoeg)} van {len(basis)})",
                 "wc8_matrix_fold", diverging=False, eenheid="fold-percentage")

    plaat_matrix(genoeg["gem_winst"].to_dict(),
                 "En met welke handen werd er geld verdiend?",
                 "gemiddelde winst per hand in chips  ·  groen is winst, rood is verlies",
                 "wc8_matrix_winst", diverging=True, eenheid="gemiddelde winst (chips)")

    # het interessante snijpunt: vaak gefold maar wel winstgevend
    kans = genoeg[(genoeg["fold_pct"] > 0.5) & (genoeg["gem_winst"] > 0)]
    cijfers["weggegooid_maar_winstgevend"] = (
        kans.sort_values("gem_winst", ascending=False)
        .head(6)[["keren", "fold_pct", "gem_winst"]].round(2).to_dict("index"))
    return genoeg


# ------------------------------------------------- 6. spreiding per bot
def plaat_spreiding():
    per_sim = (hand_log.sort_values("hand_nummer")
               .groupby(["bot_naam", "simulatie"], as_index=False)
               .last()[["bot_naam", "simulatie", "stack"]]
               .rename(columns={"stack": "eindstand"}))
    top = per_bot["eindstand"].sort_values(ascending=False).head(6).index.tolist()
    toon = top + ([JIJ] if JIJ not in top else [])
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    data = [per_sim[per_sim["bot_naam"] == b]["eindstand"].values for b in toon]
    doos = ax.boxplot(data, vert=True, patch_artist=True, widths=0.55,
                      medianprops=dict(color=INKT, linewidth=2),
                      whiskerprops=dict(color=GEDEMPT, linewidth=1.2),
                      capprops=dict(color=GEDEMPT, linewidth=1.2),
                      flierprops=dict(marker="o", markersize=4,
                                      markerfacecolor=GEDEMPT, markeredgecolor="none",
                                      alpha=0.6))
    for i, vak in enumerate(doos["boxes"]):
        vak.set_facecolor(ORANJE if toon[i] == JIJ else BLAUW)
        vak.set_alpha(0.75); vak.set_edgecolor(WIT); vak.set_linewidth(1.5)
    ax.axhline(1000, color=GEDEMPT, linewidth=1, linestyle=(0, (4, 3)))
    ax.set_xticklabels([b.replace("__w5", "") + ("  (jij)" if b == JIJ else "")
                        for b in toon], fontsize=9, rotation=20, ha="right")
    ax.set_ylabel("eindstand per simulatie (chips)")
    ax.set_title(f"Dezelfde bot, {cijfers['simulaties']} keer gespeeld",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    kaal(ax)
    spreiding = per_sim.groupby("bot_naam")["eindstand"].agg(["mean", "std"])
    besten = spreiding.sort_values("mean", ascending=False).head(2)
    cijfers["top2"] = besten.round(0).to_dict("index")
    return bewaar(fig, "wc8_spreiding")


def main():
    print("platen:")
    plaat_acties()
    plaat_foldverdeling()
    plaat_fold_vs_eindstand()
    platen_handmatrix()
    plaat_spreiding()
    with open(os.path.join(PLOTMAP, "cijfers.json"), "w") as f:
        json.dump(cijfers, f, indent=1, ensure_ascii=False)
    print("\ncijfers:")
    print(json.dumps(cijfers, indent=1, ensure_ascii=False)[:1400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
