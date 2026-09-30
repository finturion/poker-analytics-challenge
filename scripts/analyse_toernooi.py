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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
from bonus_rooster import MAX_BONUS, puntenverdeling, winst_per_bot

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
PLOTMAP = os.path.join(REPO, "powerpoints", "plots_wc8")
BRON = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HIER, "toernooi_test.json")

# Draait dit op het nagebootste toernooi, dan staan er verzonnen studentnummers
# in. Die mogen nooit per ongeluk als echte uitslag op een dia belanden, dus
# zetten we er een waarschuwing in het plaatje zelf -- die reist mee, ook als
# iemand alleen de png doorstuurt.
IS_TESTDATA = os.path.basename(BRON) == "toernooi_test.json"
os.makedirs(PLOTMAP, exist_ok=True)

INKT = "#121E31"
GEDEMPT = "#5A646B"
LIJN = "#DCE1E6"
WIT = "#FFFFFF"
BLAUW, ORANJE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"

# Sequentieel (oplopende schaal, bv. fold -> all_in): van lichtblauw naar
# donkergroen. Lichtheid daalt monotoon, dat is de eis voor een sequentiële ramp.
BLAUWGROEN = ["#d7e6f2", "#a8cfdc", "#6fb8ae", "#3a8f7a", "#1B5E4A"]

# Diverging (winst heeft een richting): blauw en groen om een grijs midden.
# Rood is hier weg op verzoek -- en blauw <-> groen is bovendien de sterkere
# combinatie: CVD Delta-E 23,1 (protan), tegen 9,1 voor geel <-> groen.
DIV_LAAG, DIV_MIDDEN, DIV_HOOG = "#2a78d6", "#F0F2F3", "#1B5E4A"
GROENRAMP = BLAUWGROEN

RANGEN = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]
RANGORDE = {r: i for i, r in enumerate(reversed(RANGEN))}

plt.rcParams.update({
    "font.size": 10, "text.color": INKT, "axes.labelcolor": INKT,
    "xtick.color": GEDEMPT, "ytick.color": GEDEMPT,
    "axes.edgecolor": LIJN, "axes.linewidth": 1.0,
})


def kort(naam):
    """Botnaam zoals hij op een dia hoort. Het achtervoegsel __w5 zit er alleen
    in als het toernooi twee weken vergelijkt; anders is de naam al het
    studentnummer."""
    return naam.split("__")[0]


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
# Welke bot we als "jouw bot" aanwijzen op de dia's. Meegeven kan:
#     python3 scripts/analyse_toernooi.py uitslag.json 500859283
# Zonder argument pakken we een student uit het midden van de uitslag -- niet de
# winnaar, want dan lijkt elke grafiek een succesverhaal, en niet de laatste.
# Referentie- en testbots vallen af: die horen niemand toe.
_STUDENTEN = [naam for naam in resultaat["eindstand_per_bot"]
              if naam not in set(resultaat.get("referentiebots") or [])
              and naam not in set(resultaat.get("testbots") or [])]
_OP_VOLGORDE = sorted(_STUDENTEN, key=lambda n: -resultaat["eindstand_per_bot"][n])
JIJ = sys.argv[2] if len(sys.argv) > 2 else _OP_VOLGORDE[len(_OP_VOLGORDE) // 2]
if JIJ not in resultaat["eindstand_per_bot"]:
    sys.exit(f"{JIJ} staat niet in deze uitslag. Keuze uit: {', '.join(_OP_VOLGORDE[:8])} ...")

hand_log = pd.DataFrame(resultaat["hand_log"])
hand_log = hand_log.sort_values(["bot_naam", "simulatie", "hand_nummer"])
hand_log["winst"] = hand_log.groupby(["bot_naam", "simulatie"])["stack"].diff()
hand_log["hand_naam"] = hand_log["hand"].apply(hand_naam)
# Twee filters, en het tweede is makkelijk te vergeten.
#
# 1. Alleen de handen waarin een bot aan de beurt kwam en nog chips had; anders
#    tel je lege regels mee van bots die al uitgespeeld waren.
# 2. Alleen de STUDENTEN. Aan tafel zitten ook vijf referentiebots en een
#    testbot -- die beinvloeden de chips, maar het zijn geen klasgenoten.
#    Dat is niet vrijblijvend: met hen erbij komt de correlatie tussen
#    fold-percentage en eindstand op +0,27 uit, zonder hen op -0,15. De
#    Testbot_CalltAlles foldt namelijk nooit en Referentie_Allrounder bijna
#    altijd, en met 6 van de 28 bots trekken ze de lijn recht. bonus_rooster
#    maakt dezelfde scheiding, via namen_deelnemers.
KLAS = set(resultaat.get("namen_deelnemers") or resultaat["eindstand_per_bot"])
speelde_mee = hand_log[hand_log["aan_zet"] & ~hand_log["uitgespeeld"]
                       & hand_log["bot_naam"].isin(KLAS)].copy()

VOLGORDE = ["fold", "call", "raise", "grote_raise", "all_in"]
aanwezig = [a for a in VOLGORDE if a in set(speelde_mee["actie"])]

print(f"{hand_log['bot_naam'].nunique()} bots ({len(KLAS)} studenten), "
      f"{hand_log['simulatie'].nunique()} simulaties, "
      f"{len(hand_log)} regels, {len(speelde_mee)} beslissingen")

cijfers = {"bots": int(len(KLAS)),
           "bots_aan_tafel": int(hand_log["bot_naam"].nunique()),
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
    ax.set_title("Hoe defensief speelt de klas?", color=INKT, fontsize=12.5, pad=12, loc="left")
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
    ax.set_title(f"Is defensief spelen beter?   correlatie r = {r:+.2f}",
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
        cmap = LinearSegmentedColormap.from_list(
            "winst", [DIV_LAAG, DIV_MIDDEN, DIV_HOOG])
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
                 "gemiddelde winst per hand in chips  ·  groen is winst, blauw is verlies",
                 "wc8_matrix_winst", diverging=True, eenheid="gemiddelde winst (chips)")

    # het interessante snijpunt: vaak gefold maar wel winstgevend
    kans = genoeg[(genoeg["fold_pct"] > 0.5) & (genoeg["gem_winst"] > 0)]
    cijfers["weggegooid_maar_winstgevend"] = (
        kans.sort_values("gem_winst", ascending=False)
        .head(6)[["keren", "fold_pct", "gem_winst"]].round(2).to_dict("index"))
    return genoeg


# ------------------------------------------------- 6. spreiding per bot
def plaat_spreiding():
    per_sim = (hand_log[hand_log["bot_naam"].isin(KLAS)].sort_values("hand_nummer")
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
    ax.set_xticklabels([kort(b) + ("  (jij)" if b == JIJ else "")
                        for b in toon], fontsize=9, rotation=20, ha="right")
    ax.set_ylabel("eindstand per simulatie (chips)")
    ax.set_title(f"Hoe stevig is een plek in de top-5?",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    kaal(ax)
    spreiding = per_sim.groupby("bot_naam")["eindstand"].agg(["mean", "std"])
    besten = spreiding.sort_values("mean", ascending=False).head(2)
    cijfers["top2"] = besten.round(0).to_dict("index")
    return bewaar(fig, "wc8_spreiding")


# ------------------------------------- 7. jouw stack door de simulaties heen
def plaat_stackverloop():
    """Spaghetti + uitlichten, precies zoals Werkcollege 6 Deel 1 t/m 3."""
    eigen = hand_log[hand_log["bot_naam"] == JIJ]
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for sim, deel in eigen.groupby("simulatie"):
        ax.plot(deel["hand_nummer"], deel["stack"], color=GEDEMPT,
                linewidth=1.0, alpha=0.35, zorder=2)
    # de twee uitersten uitlichten: dat is de boodschap
    laatste = eigen.sort_values("hand_nummer").groupby("simulatie").last()["stack"]
    for sim, kleur, label in ((laatste.idxmax(), AQUA, "beste simulatie"),
                              (laatste.idxmin(), BLAUW, "slechtste simulatie")):
        deel = eigen[eigen["simulatie"] == sim].sort_values("hand_nummer")
        ax.plot(deel["hand_nummer"], deel["stack"], color=kleur, linewidth=2.5,
                zorder=4, label=f"{label} ({int(laatste[sim])} chips)")
    ax.axhline(1000, color=GEDEMPT, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.set_xlabel("hand")
    ax.set_ylabel("stack (chips)")
    ax.set_title("Dezelfde bot, dezelfde regels — twintig keer een ander verhaal",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    kaal(ax)
    cijfers["eigen_beste"] = int(laatste.max())
    cijfers["eigen_slechtste"] = int(laatste.min())
    return bewaar(fig, "wc8_stackverloop")


# ------------------------------ 8. jouw acties tegenover die van de klas
def plaat_jij_tegenover_klas():
    eigen = speelde_mee[speelde_mee["bot_naam"] == JIJ]
    rest = speelde_mee[speelde_mee["bot_naam"] != JIJ]
    acties = [a for a in VOLGORDE if a in set(eigen["actie"]) | set(rest["actie"])]
    mijn = eigen.groupby("actie")["winst"].mean().reindex(acties)
    hun = rest.groupby("actie")["winst"].mean().reindex(acties)
    aantal = eigen.groupby("actie")["winst"].size().reindex(acties).fillna(0)

    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    y = np.arange(len(acties))
    ax.barh(y + 0.19, hun.values, height=0.36, color=GEDEMPT, alpha=0.55,
            label="de rest van de klas")
    ax.barh(y - 0.19, mijn.values, height=0.36, color=ORANJE, label="jouw bot")
    for i, (waarde, n) in enumerate(zip(mijn.values, aantal.values)):
        if np.isnan(waarde):
            continue
        kant = "left" if waarde >= 0 else "right"
        ax.text(waarde + (6 if waarde >= 0 else -6), i - 0.19,
                f"{waarde:+.0f}  (n={int(n)})", va="center", ha=kant,
                color=INKT, fontsize=9.5, fontweight="bold")
    ax.axvline(0, color=INKT, linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([a.replace("_", " ") for a in acties], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("gemiddelde winst per hand (chips)")
    ax.set_title("Levert jouw raise meer op dan die van de klas?",
                 color=INKT, fontsize=12.5, pad=26, loc="left")
    # De legenda boven de as, anders loopt hij over de onderste balken heen.
    ax.legend(frameon=False, fontsize=10, ncol=2, loc="lower right",
              bbox_to_anchor=(1.0, 1.005))
    kaal(ax, y=False)
    # ruimte voor de labels aan beide uiteinden
    alles = [v for v in list(mijn.values) + list(hun.values) if not np.isnan(v)]
    marge = (max(alles) - min(min(alles), 0)) * 0.28
    ax.set_xlim(min(min(alles), 0) - marge, max(alles) + marge)
    return bewaar(fig, "wc8_jij_tegenover_klas")


# ------------------------- 9. waar ging je geld heen? totale bijdrage per hand
def plaat_totale_bijdrage():
    """Niet het gemiddelde maar het TOTAAL: een hand die vaak voorkomt telt zwaarder."""
    eigen = speelde_mee[speelde_mee["bot_naam"] == JIJ]
    totaal = eigen.groupby("hand_naam")["winst"].agg(["sum", "size"])
    totaal = totaal[totaal["size"] >= 3].sort_values("sum")
    uitersten = pd.concat([totaal.head(7), totaal.tail(7)])

    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    kleuren = [BLAUW if v < 0 else DIV_HOOG for v in uitersten["sum"]]
    ax.barh(range(len(uitersten)), uitersten["sum"].values, color=kleuren, height=0.66)
    for i, (waarde, n) in enumerate(zip(uitersten["sum"], uitersten["size"])):
        kant = "left" if waarde >= 0 else "right"
        ax.text(waarde + (30 if waarde >= 0 else -30), i, f"{waarde:+,.0f}".replace(",", "."),
                va="center", ha=kant, color=INKT, fontsize=9.5, fontweight="bold")
    ax.axvline(0, color=INKT, linewidth=1.2)
    ax.set_yticks(range(len(uitersten)))
    ax.set_yticklabels([f"{h}  ({int(n)}x)" for h, n in
                        zip(uitersten.index, uitersten["size"])], fontsize=9.5)
    ax.set_xlabel("totale winst of verlies over het hele toernooi (chips)")
    ax.set_title("Waar ging jouw geld heen? De zeven duurste en zeven beste handen",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    kaal(ax, y=False)
    marge = abs(uitersten["sum"]).max() * 0.22
    ax.set_xlim(uitersten["sum"].min() - marge, uitersten["sum"].max() + marge)
    cijfers["duurste_hand"] = {
        "hand": uitersten.index[0], "totaal": int(uitersten["sum"].iloc[0]),
        "keren": int(uitersten["size"].iloc[0])}
    cijfers["beste_hand"] = {
        "hand": uitersten.index[-1], "totaal": int(uitersten["sum"].iloc[-1]),
        "keren": int(uitersten["size"].iloc[-1])}
    return bewaar(fig, "wc8_totale_bijdrage")


# --------------------------------------------- 10. de uitslag en de bonus
def plaat_uitslag(n=12):
    """
    Het klassement met de bonuspunten erbij.

    De puntenverdeling komt uit bonus_rooster.puntenverdeling() -- dezelfde
    functie die de API gebruikt -- en niet uit een eigen sommetje hier. Zo kan
    de dia niet afwijken van wat een student op zijn eigen bonuspagina ziet,
    inclusief de regel voor gedeelde plekken.
    """
    verdeling = puntenverdeling(resultaat)
    winst = winst_per_bot(resultaat)
    op_volgorde = sorted(verdeling.items(), key=lambda kv: (kv[1]["plek"], kv[0]))[:n]

    fig, ax = plt.subplots(figsize=(9.6, 5.4))
    namen = [kort(naam) for naam, _ in op_volgorde]
    waarden = [winst[naam] for naam, _ in op_volgorde]
    # de prijsplekken donker, de rest gedempt: de kleur zegt "hier hangt geld aan"
    kleuren = [GROENRAMP[4] if i < 2 else (GROENRAMP[3] if i < 5 else "#CBD5D0")
               for i in range(len(op_volgorde))]
    ax.barh(range(len(op_volgorde)), waarden, color=kleuren, height=0.66)

    for i, (naam, info) in enumerate(op_volgorde):
        if info["punten"]:
            tekst = f"+{info['punten']:.1f}".replace(".", ",") + " punt"
            gedeeld = "  (gedeeld)" if info["gedeeld_met"] else ""
            ax.text(waarden[i] + max(waarden) * 0.02, i, tekst + gedeeld,
                    va="center", ha="left", color=INKT, fontsize=10.5, fontweight="bold")

    ax.set_yticks(range(len(op_volgorde)))
    ax.set_yticklabels([f"{info['plek']:>2}.  {naam}"
                        for naam, info in zip(namen, [i for _, i in op_volgorde])],
                       fontsize=10)
    ax.invert_yaxis()
    ax.set_xlim(0, max(waarden) * 1.30)
    ax.set_xlabel("gewonnen chips in dit toernooi")
    pad_boven = 30 if IS_TESTDATA else 12
    ax.set_title(f"De eerste vijf pakken een bonuspunt   ·   top {n} van "
                 f"{len(verdeling)} bots", color=INKT, fontsize=12.5,
                 pad=pad_boven, loc="left")
    if IS_TESTDATA:
        ax.text(0, 1.035, "VOORBEELDUITSLAG — verzonnen studentnummers uit een testtoernooi, "
                          "niet de echte klas", transform=ax.transAxes, ha="left", va="bottom",
                color=ORANJE, fontsize=10, fontweight="bold")
    kaal(ax, y=False)
    ax.set_xticks([])

    cijfers["bonus"] = [
        {"plek": info["plek"], "student": kort(naam),
         "eindstand": int(resultaat["eindstand_per_bot"][naam]),
         "winst": int(winst[naam]), "punten": info["punten"]}
        for naam, info in sorted(verdeling.items(), key=lambda kv: (kv[1]["plek"], kv[0]))[:5]]
    # Let op het verschil: dit is wat er in DEZE ronde is uitgekeerd (altijd 1,5 --
    # de ladder 0,5 t/m 0,1), terwijl MAX_BONUS het plafond per student over de
    # hele week is (twee tellende toernooien, dus hoogstens 0,5 + 0,5).
    cijfers["uitgekeerd_deze_ronde"] = round(sum(i["punten"] for i in verdeling.values()), 2)
    cijfers["max_bonus_per_student"] = MAX_BONUS
    return bewaar(fig, "wc8_uitslag")


# ------------------------------------------ 11. de ruwe data, zoals hij is
def plaat_ruwe_data():
    """Vijf echte regels uit het logboek, als tabel. Geen grafiek maar een blik."""
    kolommen = ["bot_naam", "simulatie", "hand_nummer", "hand", "actie",
                "aan_zet", "uitgespeeld", "stack"]
    voorbeeld = (hand_log[hand_log["bot_naam"] == JIJ]
                 .sort_values(["simulatie", "hand_nummer"])
                 .head(5)[kolommen].copy())
    voorbeeld["bot_naam"] = voorbeeld["bot_naam"].apply(kort)
    voorbeeld["hand"] = voorbeeld["hand"].apply(lambda h: " ".join(h))

    fig, ax = plt.subplots(figsize=(11.6, 3.4))
    ax.axis("off")
    tabel = ax.table(cellText=voorbeeld.astype(str).values,
                     colLabels=kolommen, cellLoc="center", loc="center")
    tabel.auto_set_font_size(False)
    tabel.set_fontsize(10)
    tabel.scale(1, 1.75)
    for (rij, kol), cel in tabel.get_celld().items():
        cel.set_edgecolor(WIT)
        cel.set_linewidth(2)
        if rij == 0:
            cel.set_facecolor(GROENRAMP[4]); cel.set_text_props(color=WIT, weight="bold")
        else:
            cel.set_facecolor("#F4F6F5" if rij % 2 else "#EAEEEC")
            cel.set_text_props(color=INKT)
    ax.set_title("Eén regel per bot per hand — dit is alles wat je krijgt",
                 color=INKT, fontsize=13, pad=18, loc="left")
    ax.text(0, -0.12, f"{len(hand_log):,}".replace(",", ".") + " van deze regels, "
            f"{hand_log['bot_naam'].nunique()} bots, "
            f"{hand_log['simulatie'].nunique()} simulaties",
            transform=ax.transAxes, ha="left", va="top", color=GEDEMPT, fontsize=10)
    return bewaar(fig, "wc8_ruwe_data")


# ------------------------------------------- 12. de stand of de stroom
def plaat_stand_stroom():
    """Hetzelfde verhaal als het hoorcollege, maar op hun eigen toernooi."""
    # Niet de simulatie met de grootste uitschieter: één piek van 2000 drukt al
    # het andere plat en dan laat de rechterhelft juist niets meer zien. Wel die
    # met de meeste handen waarin écht iets gebeurde -- meer dan een big blind.
    alles = hand_log[hand_log["bot_naam"] == JIJ]
    beweging = (alles.assign(raak=alles["winst"].abs() > 20)
                .groupby("simulatie")["raak"].sum())
    eigen = alles[alles["simulatie"] == beweging.idxmax()].sort_values("hand_nummer")
    fig, assen = plt.subplots(1, 2, figsize=(12.0, 4.2), sharex=True)

    assen[0].plot(eigen["hand_nummer"], eigen["stack"], color=GEDEMPT, linewidth=2.2)
    assen[0].axhline(1000, color=GEDEMPT, linewidth=1, linestyle=(0, (4, 3)))
    assen[0].set_title("de STAND:  stack", color=INKT, fontsize=12, pad=10, loc="left")
    assen[0].set_ylabel("chips")
    assen[0].text(0.02, 0.05, "de kolom die je krijgt", transform=assen[0].transAxes,
                  color=GEDEMPT, fontsize=9.5)

    winst = eigen["winst"].fillna(0)
    kleuren = [DIV_HOOG if w >= 0 else DIV_LAAG for w in winst]
    assen[1].bar(eigen["hand_nummer"], winst, color=kleuren, width=0.75)
    assen[1].axhline(0, color=INKT, linewidth=1.1)
    assen[1].set_title("de STROOM:  winst per hand  =  .diff()",
                       color=INKT, fontsize=12, pad=10, loc="left")
    assen[1].set_ylabel("chips per hand")
    # De grootste beweging, positief of negatief: dát is het moment waar de
    # linkerhelft een knik laat zien en de rechterhelft een getal.
    ergste = winst.abs().idxmax()
    assen[1].annotate(f"{winst[ergste]:+.0f} chips in één hand\nhier gebeurde het",
                      xy=(eigen.loc[ergste, "hand_nummer"], winst[ergste]),
                      xytext=(0.52, 0.88), textcoords="axes fraction",
                      color=INKT, fontsize=10, fontweight="bold", linespacing=1.4,
                      arrowprops=dict(arrowstyle="->", color=GEDEMPT, linewidth=1.4,
                                      connectionstyle="arc3,rad=-0.25"))

    for ax in assen:
        ax.set_xlabel("hand")
        kaal(ax)
    fig.suptitle("Dezelfde bot, dezelfde handen — en pas rechts zie je wannéér",
                 color=INKT, fontsize=13, x=0.005, ha="left", y=1.02)
    return bewaar(fig, "wc8_stand_stroom")


def main():
    print("platen:")
    plaat_uitslag()
    plaat_ruwe_data()
    plaat_stand_stroom()
    plaat_acties()
    plaat_foldverdeling()
    plaat_fold_vs_eindstand()
    platen_handmatrix()
    plaat_spreiding()
    plaat_stackverloop()
    plaat_jij_tegenover_klas()
    plaat_totale_bijdrage()
    with open(os.path.join(PLOTMAP, "cijfers.json"), "w") as f:
        json.dump(cijfers, f, indent=1, ensure_ascii=False)
    print("\ncijfers:")
    print(json.dumps(cijfers, indent=1, ensure_ascii=False)[:1400])
    return 0


if __name__ == "__main__":
    sys.exit(main())
