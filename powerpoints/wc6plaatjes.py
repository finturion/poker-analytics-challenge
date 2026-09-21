"""
De platen bij Werkcollege 6: van spaghetti naar één verhaal.

    python3 powerpoints/wc6plaatjes.py uitslag.json   # de echte uitslag
    python3 powerpoints/wc6plaatjes.py                # zonder uitslag: eigen toernooi

Schrijft naar powerpoints/plots_week4/. Elke plaat is een stap uit het notebook,
in dezelfde volgorde.

Geef de echte uitslag mee als je hem hebt -- dan is de rommel op de eerste dia
exact de rommel die studenten in Deel 1 zelf te zien krijgen, en dat is het halve
punt. Zonder argument speelt hij zelf een toernooi met een veld dat lijkt op de
klas: veel bots die bijna alles wegleggen, een paar die meedoen. De platen zien er
dan hetzelfde uit, alleen staan er geen studentnummers bij.

De platen zijn bewust zonder titel. Op de dia staat de titel als tekst, want daar
kun je hem aanpassen zonder de plaat opnieuw te tekenen -- en Deel 5 gaat er nu
juist over dat de titel een bewering is die je zelf schrijft.
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dekstijl import HEX
from toernooicijfers import bouw_dataframe

HIER = os.path.dirname(os.path.abspath(__file__))
PLOTMAP = os.path.join(HIER, "plots_week4")

INKT = HEX["primair"]
VILT = HEX["accent"]
GEDEMPT = HEX["gedempt"]
ROOD = HEX["rood"]
PAPIER = "#FFFFFF"

BREED = (9.6, 4.5)


def _assen(figsize=BREED, x="hand", y="stack (chips)"):
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    ax.set_xlabel(x, color=INKT, fontsize=10)
    ax.set_ylabel(y, color=INKT, fontsize=10)
    ax.tick_params(colors=GEDEMPT, labelsize=9)
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    for kant in ("left", "bottom"):
        ax.spines[kant].set_color(GEDEMPT)
    return fig, ax


def _bewaar(fig, naam):
    os.makedirs(PLOTMAP, exist_ok=True)
    pad = os.path.join(PLOTMAP, naam + ".png")
    fig.tight_layout()
    fig.savefig(pad, facecolor=PAPIER)
    plt.close(fig)
    return pad


def plaat_spaghetti(df):
    """Deel 1 -- alles, ongefilterd. Dit is het probleem."""
    fig, ax = _assen()
    for (naam, sim), groep in df.groupby(["bot_naam", "simulatie"]):
        ax.plot(groep["hand_nummer"], groep["stack"], linewidth=0.8, alpha=0.75)
    return _bewaar(fig, "1_spaghetti")


def plaat_gefilterd(df, tafel, simulatie):
    """Deel 2 -- één tafel, één zitting. Leesbaarder, nog steeds geen verhaal."""
    deel = df[(df["tafel"] == tafel) & (df["simulatie"] == simulatie)]
    fig, ax = _assen()
    for naam, groep in deel.groupby("bot_naam"):
        ax.plot(groep["hand_nummer"], groep["stack"], linewidth=1.6, label=naam)
    ax.legend(fontsize=7, frameon=False, ncol=3, loc="upper left")
    return _bewaar(fig, "2_gefilterd")


def plaat_uitgelicht(df, tafel, simulatie, held, naam="3_uitgelicht", kleurloos=False):
    """Deel 3 -- kleur, dikte en opacity op één lijn. Deel 6 -- dezelfde zonder kleur."""
    deel = df[(df["tafel"] == tafel) & (df["simulatie"] == simulatie)]
    fig, ax = _assen()
    for bot, groep in deel.groupby("bot_naam"):
        if bot == held:
            continue
        ax.plot(groep["hand_nummer"], groep["stack"],
                color="#9AA3AA", linewidth=1.0, alpha=0.45, zorder=1)
    eigen = deel[deel["bot_naam"] == held]
    ax.plot(eigen["hand_nummer"], eigen["stack"],
            color=GEDEMPT if kleurloos else VILT,
            linewidth=3.0, alpha=1.0, zorder=3, label=held)
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    return _bewaar(fig, naam)


def plaat_kantelpunt(df, tafel, simulatie, held, rivaal):
    """Deel 5 -- het moment waarop het verschil ontstaat, met een annotatie."""
    deel = df[(df["tafel"] == tafel) & (df["simulatie"] == simulatie)]
    a = deel[deel["bot_naam"] == held].set_index("hand_nummer")["stack"]
    b = deel[deel["bot_naam"] == rivaal].set_index("hand_nummer")["stack"]
    verschil = (a - b).dropna()
    kantel = int(verschil.idxmax())

    fig, ax = _assen()
    for bot, groep in deel.groupby("bot_naam"):
        if bot in (held, rivaal):
            continue
        ax.plot(groep["hand_nummer"], groep["stack"],
                color="#9AA3AA", linewidth=0.9, alpha=0.35, zorder=1)
    ax.plot(b.index, b.values, color=ROOD, linewidth=2.0, alpha=0.9, zorder=2, label=rivaal)
    ax.plot(a.index, a.values, color=VILT, linewidth=3.0, zorder=3, label=held)

    ax.axvline(kantel, color=INKT, linestyle="--", linewidth=1.0, alpha=0.6, zorder=2)
    ax.annotate(f"hand {kantel}: voorsprong {verschil.max():.0f} chips",
                xy=(kantel, a.loc[kantel]), xytext=(0.04, 0.90),
                textcoords="axes fraction", color=INKT, fontsize=10,
                arrowprops=dict(arrowstyle="->", color=GEDEMPT, linewidth=1,
                                connectionstyle="arc3,rad=0.2"))
    ax.legend(fontsize=9, frameon=False, loc="lower left")
    return _bewaar(fig, "4_kantelpunt"), kantel, float(verschil.max())


def plaat_niveau_vs_verloop(df, tafel, simulatie, held):
    """Deel 7 -- dezelfde bot, links de stand en rechts wat elke hand opleverde."""
    eigen = df[(df["tafel"] == tafel) & (df["simulatie"] == simulatie)
               & (df["bot_naam"] == held)]
    fig, assen = plt.subplots(1, 2, figsize=(9.6, 3.9), dpi=200, sharex=True)
    for ax in assen:
        ax.tick_params(colors=GEDEMPT, labelsize=9)
        for kant in ("top", "right"):
            ax.spines[kant].set_visible(False)
        for kant in ("left", "bottom"):
            ax.spines[kant].set_color(GEDEMPT)
        ax.set_xlabel("hand", color=INKT, fontsize=10)

    assen[0].plot(eigen["hand_nummer"], eigen["stack"], color=VILT, linewidth=2.2)
    assen[0].set_ylabel("stack -- de stand", color=INKT, fontsize=10)

    assen[1].bar(eigen["hand_nummer"], eigen["winst"],
                 color=[VILT if w >= 0 else ROOD for w in eigen["winst"]], width=0.85)
    assen[1].axhline(0, color=GEDEMPT, linewidth=0.8)
    assen[1].set_ylabel("winst -- de stroom (diff)", color=INKT, fontsize=10)
    return _bewaar(fig, "5_niveau_vs_verloop")


def plaat_kanalen():
    """De inleiding -- vier pre-attentieve kanalen, elk met dezelfde acht lijnen."""
    rng = np.random.default_rng(7)
    x = np.arange(0, 30)
    lijnen = [np.cumsum(rng.normal(0, 1, len(x))) for _ in range(8)]
    held = 3

    titels = ["geen enkel kanaal", "kleur", "kleur + dikte", "kleur + dikte + opacity"]
    fig, assen = plt.subplots(1, 4, figsize=(11.2, 2.9), dpi=200, sharey=True)
    for k, ax in enumerate(assen):
        for i, y in enumerate(lijnen):
            is_held = i == held
            if k == 0:
                kleur, dikte, alpha = GEDEMPT, 1.2, 1.0
            elif k == 1:
                kleur = VILT if is_held else "#9AA3AA"
                dikte, alpha = 1.2, 1.0
            elif k == 2:
                kleur = VILT if is_held else "#9AA3AA"
                dikte, alpha = (3.0, 1.0) if is_held else (1.0, 1.0)
            else:
                kleur = VILT if is_held else "#9AA3AA"
                dikte, alpha = (3.0, 1.0) if is_held else (1.0, 0.35)
            ax.plot(x, y, color=kleur, linewidth=dikte, alpha=alpha,
                    zorder=3 if is_held else 1)
        ax.set_title(titels[k], color=INKT, fontsize=10, pad=8)
        ax.set_xticks([]); ax.set_yticks([])
        for kant in ("top", "right", "left", "bottom"):
            ax.spines[kant].set_visible(False)
    return _bewaar(fig, "0_kanalen")


def eigen_toernooi(n_bots=24, seed=4):
    """
    Een toernooi met een veld dat lijkt op de klas, voor als de echte uitslag er
    niet is.

    De verhouding is niet verzonnen maar nagebouwd: in het toernooi van week 3
    foldde 92% van alle beslissingen, en negen van de 27 bots folden 99% of meer.
    Vandaar veel bots met een hoge drempel en een paar die wél meedoen -- anders
    krijg je vlakke lijnen en valt er niets uit te lichten.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "api"))
    from poker_adapter import speel_toernooi

    sterk = ("A", "K", "Q")
    def maak_bot(drempel):
        # drempel 0 = doet altijd mee, 3 = alleen met twee hoge kaarten
        def kies_actie(hand, stack):
            score = sum(1 for kaart in hand if kaart in sterk)
            if drempel == 0:
                return "call"
            if score >= drempel:
                return "raise" if score >= 2 else "call"
            return "fold"
        return kies_actie

    bots = {}
    for i in range(n_bots):
        drempel = 3 if i < n_bots * 2 // 3 else (2 if i < n_bots - 3 else 0)
        bots[f"bot_{i + 1:02d}"] = maak_bot(drempel)
    return speel_toernooi(bots, n_simulaties=5, n_handen=50, seed=seed)


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as bestand:
            uitslag = json.load(bestand)
        print(f"uitslag uit {sys.argv[1]}")
    else:
        uitslag = eigen_toernooi()
        print("geen uitslag meegegeven -- zelf een toernooi gespeeld")
    df = bouw_dataframe(uitslag)

    # Een tafel waar de winnaar aan zat: dan valt er iets te vertellen.
    eind = df.groupby("bot_naam")["stack"].last()
    held = str(eind.idxmax())
    zit = df[df["bot_naam"] == held].iloc[-1]
    tafel, simulatie = int(zit["tafel"]), int(zit["simulatie"])
    buren = df[(df["tafel"] == tafel) & (df["simulatie"] == simulatie)]
    rivaal = str(buren.groupby("bot_naam")["stack"].last().drop(held).idxmax())

    print(plaat_kanalen())
    print(plaat_spaghetti(df))
    print(plaat_gefilterd(df, tafel, simulatie))
    print(plaat_uitgelicht(df, tafel, simulatie, held))
    print(plaat_uitgelicht(df, tafel, simulatie, held, naam="6_kleurloos", kleurloos=True))
    pad, kantel, voorsprong = plaat_kantelpunt(df, tafel, simulatie, held, rivaal)
    print(pad)
    print(plaat_niveau_vs_verloop(df, tafel, simulatie, held))

    print(f"\nheld {held} · rivaal {rivaal} · tafel {tafel} simulatie {simulatie} · "
          f"kantelpunt hand {kantel} ({voorsprong:.0f} chips)")
    print(f"{buren['bot_naam'].nunique()} bots aan die tafel · "
          f"{df['bot_naam'].nunique()} bots in totaal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
