"""
De tekeningen bij de spelregels: speelkaarten, de tafel, de vier straten en
het verloop van één hand.

Zelf getekend en niet van internet geplukt. Twee redenen: afbeeldingen van
kaartspellen zijn bijna altijd van iemand, en de beelden die je vindt komen uit
de gokhoek -- precies wat er niet in HvA-materiaal hoort. Getekend passen ze
bovendien in hetzelfde palet als de rest van het deck, en kun je ze aanpassen.

Alles komt uit matplotlib, dus er is geen extra afhankelijkheid.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

PRIMAIR = "#121E31"
ACCENT = "#1B4D3E"
GEDEMPT = "#505A64"
LIJN = "#DCE1E6"
PAPIER = "#F8F9FA"
ROOD = "#B3261E"
GROEN_LICHT = "#4FC3A1"

# De vier kleuren, met hun symbool en of ze rood zijn.
KLEUREN = {
    "S": ("♠", False, "schoppen", "Spades"),
    "H": ("♥", True, "harten", "Hearts"),
    "D": ("♦", True, "ruiten", "Diamonds"),
    "C": ("♣", False, "klaveren", "Clubs"),
}


def teken_kaart(ax, x, y, kaart, breedte=1.0, hoogte=1.45, gedekt=False):
    """
    Eén speelkaart op positie (x, y), linksonder.

    `kaart` is de notatie uit de engine: eerst de kleur, dan de rang -- "HQ" is
    harten vrouw. Dat is dezelfde volgorde als in het notebook, want als de dia
    het andersom doet dan de code, leren studenten het verkeerd.
    """
    if gedekt:
        vak = FancyBboxPatch((x, y), breedte, hoogte, boxstyle="round,pad=0.02,rounding_size=0.08",
                             facecolor=PRIMAIR, edgecolor=LIJN, linewidth=1.2, zorder=3)
        ax.add_patch(vak)
        for rij in range(4):
            for kol in range(3):
                ax.plot(x + 0.2 + kol * 0.3, y + 0.25 + rij * 0.32, marker="o",
                        markersize=2.0, color=GROEN_LICHT, zorder=4)
        return

    kleurletter, rang = kaart[0], kaart[1:]
    symbool, is_rood, _, _ = KLEUREN[kleurletter]
    inkt = ROOD if is_rood else PRIMAIR

    # De lettergroottes moeten meeschalen met de kaart. Stonden ze vast, dan
    # overschreeuwde het symbool de rang zodra de kaart klein werd -- op de
    # handsterkte-tabel liepen ze zelfs door elkaar heen.
    rang_fs = max(5.5, breedte * 13)
    symbool_fs = max(7.0, breedte * 17)
    marge = breedte * 0.14

    vak = FancyBboxPatch((x, y), breedte, hoogte, boxstyle="round,pad=0.02,rounding_size=0.08",
                         facecolor="white", edgecolor=LIJN, linewidth=1.2, zorder=3)
    ax.add_patch(vak)
    ax.text(x + marge, y + hoogte - marge, rang, ha="left", va="top",
            fontsize=rang_fs, fontweight="bold", color=inkt, zorder=4)
    ax.text(x + breedte * 0.62, y + hoogte * 0.34, symbool, ha="center", va="center",
            fontsize=symbool_fs, color=inkt, zorder=4)
    # Het hoekcijfer op zijn kop hoort bij een echte speelkaart, maar onder de
    # centimeter wordt het een vlekje. Dan liever weglaten.
    if breedte >= 0.9:
        ax.text(x + breedte - marge, y + marge, rang, ha="right", va="bottom",
                fontsize=rang_fs * 0.72, fontweight="bold", color=inkt, zorder=4,
                rotation=180)


def _kale_assen(figsize, xlim, ylim):
    fig, ax = plt.subplots(figsize=figsize, dpi=200)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(PAPIER)
    return fig, ax


def bewaar(fig, map_, naam):
    os.makedirs(map_, exist_ok=True)
    pad = os.path.join(map_, f"{naam}.png")
    fig.savefig(pad, bbox_inches="tight", facecolor=PAPIER)
    plt.close(fig)
    return pad


# ---------------------------------------------------------------------------

def plaat_hole_cards(map_):
    """Wat jij ziet en wat de rest ziet: twee open kaarten, vijf gedekte."""
    fig, ax = _kale_assen((7.4, 2.4), (-0.3, 11.2), (-0.7, 2.2))

    ax.text(0, 1.95, "JOUW hole cards", fontsize=10, fontweight="bold", color=ACCENT)
    teken_kaart(ax, 0, 0.3, "SA")
    teken_kaart(ax, 1.2, 0.3, "HA")
    ax.text(1.2, -0.35, "prive: alleen jij ziet ze", fontsize=8.5, color=GEDEMPT, ha="center")

    ax.text(3.6, 1.95, "Wat de anderen hebben", fontsize=10, fontweight="bold", color=GEDEMPT)
    for i in range(5):
        teken_kaart(ax, 3.6 + i * 1.2, 0.3, "XX", gedekt=True)
    ax.text(6.0, -0.35, "dicht: je weet het niet, je schat het", fontsize=8.5,
            color=GEDEMPT, ha="center")
    return bewaar(fig, map_, "hole_cards")


def plaat_tafel(map_):
    """Zes stoelen, de blinds, en wat er al in de pot zit voordat iemand kiest."""
    fig, ax = _kale_assen((7.2, 4.6), (-5.2, 5.2), (-4.2, 3.6))

    tafel = FancyBboxPatch((-3.5, -2.1), 7.0, 4.2,
                           boxstyle="round,pad=0.1,rounding_size=1.9",
                           facecolor=ACCENT, edgecolor=ACCENT, alpha=0.12,
                           linewidth=1.4, zorder=1)
    ax.add_patch(tafel)

    # Stoelen op de rand van het blad, niet ernaast.
    stoelen = [(0, 2.25, "1", "bot 1"), (3.15, 1.1, "2", "bot 2"),
               (3.15, -1.1, "3", "bot 3"), (0, -2.25, "4", "bot 4"),
               (-3.15, -1.1, "SB", "small blind"), (-3.15, 1.1, "BB", "big blind")]
    for x, y, kort, label in stoelen:
        blind = kort in ("SB", "BB")
        stoel = Circle((x, y), 0.5, facecolor="white",
                       edgecolor=ACCENT if blind else LIJN,
                       linewidth=2.2 if blind else 1.3, zorder=3)
        ax.add_patch(stoel)
        ax.text(x, y, kort, fontsize=11 if blind else 12, ha="center", va="center",
                fontweight="bold", color=ACCENT if blind else GEDEMPT, zorder=4)
        onder = y < 0
        ax.text(x, y - 0.7 if onder else y + 0.7, label, fontsize=8.5, ha="center",
                va="top" if onder else "bottom",
                color=ACCENT if blind else GEDEMPT,
                fontweight="bold" if blind else "normal")

    ax.text(0, 0.62, "POT", fontsize=10, fontweight="bold", color=GEDEMPT, ha="center")
    ax.text(0, -0.15, "30", fontsize=30, fontweight="bold", color=PRIMAIR, ha="center")
    ax.text(0, -0.85, "small blind 10 + big blind 20", fontsize=9, color=GEDEMPT, ha="center")

    ax.text(0, -3.75, "Er ligt al geld in de pot voordat iemand een keuze heeft gemaakt.",
            fontsize=10.5, color=PRIMAIR, ha="center", style="italic")
    return bewaar(fig, map_, "tafel")


def plaat_straten(map_):
    """De vier straten: hoe het bord groeit, en wanneer er geboden wordt."""
    fig, ax = _kale_assen((8.4, 4.6), (-0.4, 12.6), (-1.2, 6.4))

    rijen = [
        ("preflop", [], "alleen je eigen twee kaarten"),
        ("flop", ["S2", "C7", "SK"], "drie kaarten erbij"),
        ("turn", ["S2", "C7", "SK", "S9"], "de vierde"),
        ("river", ["S2", "C7", "SK", "S9", "S10"], "de vijfde en laatste"),
    ]
    for i, (naam, bord, uitleg) in enumerate(rijen):
        y = 4.7 - i * 1.75
        ax.text(-0.3, y + 0.6, naam, fontsize=12, fontweight="bold", color=ACCENT)
        ax.text(-0.3, y + 0.18, uitleg, fontsize=8.5, color=GEDEMPT)
        for k, kaart in enumerate(bord):
            teken_kaart(ax, 2.9 + k * 1.15, y - 0.55, kaart, breedte=0.95, hoogte=1.35)
        for k in range(len(bord), 5):
            vak = FancyBboxPatch((2.9 + k * 1.15, y - 0.55), 0.95, 1.35,
                                 boxstyle="round,pad=0.02,rounding_size=0.08",
                                 facecolor="none", edgecolor=LIJN, linewidth=1.0,
                                 linestyle=(0, (3, 3)), zorder=2)
            ax.add_patch(vak)
        ax.text(9.9, y + 0.1, "→  inzetronde", fontsize=9.5, color=PRIMAIR)

    ax.text(6.2, -0.95, "Na elke straat wordt er opnieuw geboden. Je bot beslist dus vier keer per hand.",
            fontsize=10, color=PRIMAIR, ha="center", style="italic")
    return bewaar(fig, map_, "straten")


def plaat_handverloop(map_):
    """Twee azen tegen 7-8 schoppen: waarom twee kaarten niet genoeg zijn."""
    fig, ax = _kale_assen((9.6, 4.4), (-0.4, 15.6), (0.0, 7.4))

    ax.text(-0.3, 6.95, "Speler A", fontsize=11.5, fontweight="bold", color=PRIMAIR)
    teken_kaart(ax, -0.3, 5.35, "SA", breedte=0.92, hoogte=1.32)
    teken_kaart(ax, 0.78, 5.35, "HA", breedte=0.92, hoogte=1.32)

    ax.text(-0.3, 4.1, "Speler B", fontsize=11.5, fontweight="bold", color=PRIMAIR)
    teken_kaart(ax, -0.3, 2.5, "S7", breedte=0.92, hoogte=1.32)
    teken_kaart(ax, 0.78, 2.5, "S8", breedte=0.92, hoogte=1.32)

    stappen = [
        ("flop", ["S2", "C7", "DA"], "A: drie azen", "B: paar + 3 schoppen", False),
        ("turn", ["S2", "C7", "DA", "S9"], "A: nog voor", "B: 4 schoppen", False),
        ("river", ["S2", "C7", "DA", "S9", "S10"], "A: drie azen", "B: FLUSH, wint", True),
    ]
    # Ruim uit elkaar: eerder stonden de kolommen 3,2 breed en liepen de
    # onderschriften van flop en turn dwars door elkaar heen.
    for i, (naam, bord, tekst_a, tekst_b, kantelt) in enumerate(stappen):
        x = 3.6 + i * 4.0
        ax.text(x, 6.95, naam, fontsize=12, fontweight="bold",
                color=ROOD if kantelt else ACCENT)
        for k, kaart in enumerate(bord):
            teken_kaart(ax, x + (k % 3) * 0.86, 5.4 - (k // 3) * 1.25, kaart,
                        breedte=0.74, hoogte=1.08)
        ax.text(x, 3.6, tekst_a, fontsize=9, color=GEDEMPT)
        ax.text(x, 3.1, tekst_b, fontsize=9,
                color=ROOD if kantelt else GEDEMPT,
                fontweight="bold" if kantelt else "normal")

    ax.text(7.6, 1.35, "Preflop leek dit geen wedstrijd. Op de river wint 7-8 van twee azen.",
            fontsize=11.5, color=PRIMAIR, ha="center", fontweight="bold")
    ax.text(7.6, 0.65, "De uitslag hangt af van vijf kaarten die je bij het beslissen nog niet kent.",
            fontsize=10, color=GEDEMPT, ha="center", style="italic")
    return bewaar(fig, map_, "handverloop")


def plaat_kleuren(map_):
    """De vier letters, en waarom D en C niet kloppen met het Nederlands."""
    fig, ax = _kale_assen((7.6, 2.6), (-0.4, 11.6), (-1.3, 2.4))

    for i, (letter, (symbool, is_rood, nl, en)) in enumerate(KLEUREN.items()):
        x = i * 2.9
        teken_kaart(ax, x, 0.45, f"{letter}A", breedte=0.95, hoogte=1.35)
        ax.text(x + 1.25, 1.55, letter, fontsize=17, fontweight="bold",
                color=ROOD if is_rood else PRIMAIR, va="top")
        ax.text(x + 1.25, 1.0, nl, fontsize=10, color=PRIMAIR, va="top")
        ax.text(x + 1.25, 0.62, f"van {en}", fontsize=8.5, color=GEDEMPT, va="top")

    ax.text(5.6, -0.85,
            "Alleen H klopt met het Nederlandse woord. Haal D en C door elkaar "
            "en je bouwt een flush die er niet is.",
            fontsize=9.5, color=ROOD, ha="center")
    return bewaar(fig, map_, "kleuren")


def plaat_flowchart(map_):
    """De flowchart uit het notebook: wat je bot per straat binnenkrijgt."""
    fig, ax = _kale_assen((8.8, 4.4), (-0.5, 13.5), (-2.9, 3.4))

    straten = [("Nieuwe hand", "2 hole cards"), ("preflop", "nog geen bord"),
               ("flop", "3 kaarten erbij"), ("turn", "4e kaart"),
               ("river", "5e kaart"), ("showdown", "beste 5 tellen")]
    breedte, hoogte, tussen = 1.85, 0.95, 0.32
    xs = []
    for i, (titel, onder) in enumerate(straten):
        x = i * (breedte + tussen)
        xs.append(x)
        laatste = i == len(straten) - 1
        vak = FancyBboxPatch((x - 0.06, 1.9), breedte + 0.12, hoogte,
                             boxstyle="round,pad=0.04,rounding_size=0.12",
                             facecolor=ACCENT if laatste else "white",
                             edgecolor=ACCENT, linewidth=1.4, zorder=3)
        ax.add_patch(vak)
        ax.text(x + breedte / 2, 2.58, titel, fontsize=9.5, fontweight="bold",
                ha="center", color="white" if laatste else PRIMAIR, zorder=4)
        ax.text(x + breedte / 2, 2.18, onder, fontsize=7.5, ha="center",
                color="#D8E6E0" if laatste else GEDEMPT, zorder=4)
        if i:
            ax.add_patch(FancyArrowPatch(
                (xs[i - 1] + breedte, 2.38), (x, 2.38),
                arrowstyle="-|>", mutation_scale=11, color=ACCENT, linewidth=1.3, zorder=2))

    # De vier straten waarin je bot aan zet komt, met een stippellijn omlaag.
    for i in (1, 2, 3, 4):
        ax.add_patch(FancyArrowPatch(
            (xs[i] + breedte / 2, 1.9), (6.1, 0.85),
            arrowstyle="-|>", mutation_scale=9, color=GEDEMPT,
            linewidth=0.9, linestyle=(0, (2, 2)), zorder=2,
            connectionstyle="arc3,rad=0.12"))

    vak = FancyBboxPatch((3.1, -0.35), 6.0, 1.2,
                         boxstyle="round,pad=0.05,rounding_size=0.12",
                         facecolor="white", edgecolor=PRIMAIR, linewidth=1.6, zorder=3)
    ax.add_patch(vak)
    ax.text(6.1, 0.55, "kies_actie krijgt:", fontsize=10, fontweight="bold",
            ha="center", color=PRIMAIR, zorder=4)
    ax.text(6.1, 0.12, "hand · stack · ronde · pot · inzet_om_te_callen",
            fontsize=9, ha="center", color=ACCENT, zorder=4)

    ax.add_patch(FancyArrowPatch((6.1, -0.35), (6.1, -1.05), arrowstyle="-|>",
                                 mutation_scale=11, color=PRIMAIR, linewidth=1.3, zorder=2))
    vak = FancyBboxPatch((2.9, -2.3), 6.4, 1.0,
                         boxstyle="round,pad=0.05,rounding_size=0.12",
                         facecolor="#F0F6F3", edgecolor=ACCENT, linewidth=1.4, zorder=3)
    ax.add_patch(vak)
    ax.text(6.1, -1.5, "jouw besluit", fontsize=9, ha="center", color=GEDEMPT, zorder=4)
    ax.text(6.1, -1.95, "fold · call · raise · grote_raise · all_in",
            fontsize=10.5, fontweight="bold", ha="center", color=PRIMAIR, zorder=4)

    ax.text(6.4, -2.75, "Je kies_actie wordt vier keer per hand aangeroepen — "
                        "een keer per straat, elke keer met een andere ronde.",
            fontsize=9.5, color=PRIMAIR, ha="center", style="italic")
    return bewaar(fig, map_, "flowchart")


def plaat_raiseladder(map_):
    """Wat een raise kost, en wat grote_raise daarnaast doet."""
    fig, ax = _kale_assen((8.0, 3.2), (-0.5, 12.5), (-1.6, 3.0))

    stappen = [("20", "op tafel"), ("40", "raise"), ("60", "raise"), ("80", "raise")]
    for i, (bedrag, label) in enumerate(stappen):
        x = i * 1.75
        vak = FancyBboxPatch((x, 1.35), 1.3, 0.85,
                             boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor="white", edgecolor=LIJN, linewidth=1.3, zorder=3)
        ax.add_patch(vak)
        ax.text(x + 0.65, 1.9, bedrag, fontsize=14, fontweight="bold",
                ha="center", color=PRIMAIR, zorder=4)
        ax.text(x + 0.65, 1.52, label, fontsize=7.5, ha="center", color=GEDEMPT, zorder=4)
        if i:
            ax.add_patch(FancyArrowPatch((x - 0.45, 1.78), (x, 1.78), arrowstyle="-|>",
                                         mutation_scale=11, color=ACCENT, linewidth=1.3))
            ax.text(x - 0.22, 2.35, "+20", fontsize=8.5, ha="center", color=ACCENT)

    ax.text(0, 0.75, "Een raise gaat naar het volgende veelvoud van de big blind — geen verdubbeling.",
            fontsize=10, color=PRIMAIR)
    ax.text(0, 0.28, "Gemeten in een echt toernooi: 72% van de raises voegt 20 toe, 28% voegt 10 toe.",
            fontsize=9, color=GEDEMPT)

    vak = FancyBboxPatch((7.6, 1.1), 4.4, 1.3,
                         boxstyle="round,pad=0.05,rounding_size=0.12",
                         facecolor="#F0F6F3", edgecolor=ACCENT, linewidth=1.5, zorder=3)
    ax.add_patch(vak)
    ax.text(9.8, 2.06, "grote_raise", fontsize=12, fontweight="bold",
            ha="center", color=ACCENT, zorder=4)
    # Op een regel liep dit net buiten het kader.
    ax.text(9.8, 1.66, "in een keer naar 200", fontsize=9, ha="center",
            color=PRIMAIR, zorder=4)
    ax.text(9.8, 1.32, "tien big blinds", fontsize=9, ha="center",
            color=GEDEMPT, zorder=4)

    ax.text(0, -0.55, "Max twee raises per straat. Een derde raise wordt automatisch een call;",
            fontsize=9.5, color=PRIMAIR)
    ax.text(0, -1.0, "all_in mag altijd. Daardoor kun je een grote inzet terugpakken.",
            fontsize=9.5, color=PRIMAIR)
    return bewaar(fig, map_, "raiseladder")


def plaat_handsterkte(map_):
    """
    De negen handsoorten met een voorbeeld in kaarten, zwakste bovenaan.

    De voorbeelden zijn echte vijfkaartshanden en geen losse plaatjes: elke rij
    is precies wat er bij een showdown op tafel zou liggen. Twee kaarten van
    dezelfde waarde EN dezelfde kleur bestaan niet, dus de rijen zijn nagelopen
    op dubbele kaarten -- zie de controle onderaan deze functie.
    """
    rijen = [
        ("hoge kaart", ["SA", "H9", "D7", "C4", "S2"], "niks bijzonders; je hoogste kaart telt"),
        ("een paar", ["SK", "HK", "D9", "C5", "S2"], "2 kaarten van dezelfde waarde"),
        ("twee paar", ["SQ", "HQ", "D8", "C8", "S3"], "2 x een paar"),
        ("three of a kind", ["SJ", "HJ", "DJ", "C6", "S2"], "3 kaarten van dezelfde waarde"),
        ("straat", ["S9", "H8", "D7", "C6", "S5"], "5 opeenvolgende waardes; kleur maakt niet uit"),
        ("flush", ["SA", "SJ", "S8", "S5", "S3"], "5 kaarten van dezelfde kleur; volgorde maakt niet uit"),
        ("full house", ["S10", "H10", "D10", "C4", "S4"], "three of a kind + een paar"),
        ("four of a kind", ["S7", "H7", "D7", "C7", "S2"], "4 kaarten van dezelfde waarde"),
        ("straight flush", ["S9", "S8", "S7", "S6", "S5"], "een straat en een flush tegelijk"),
    ]

    for naam, kaarten, _ in rijen:
        if len(set(kaarten)) != 5:
            raise AssertionError(f"{naam}: dezelfde kaart komt twee keer voor -> {kaarten}")

    hoog = 0.95
    fig, ax = _kale_assen((14.0, 6.2), (-0.4, 23.5), (-0.9, len(rijen) * hoog + 0.7))

    for i, (naam, kaarten, uitleg) in enumerate(rijen):
        y = (len(rijen) - 1 - i) * hoog
        sterkste = i == len(rijen) - 1
        if i % 2 == 0:
            ax.add_patch(FancyBboxPatch((-0.3, y - 0.08), 23.4, hoog - 0.06,
                                        boxstyle="square,pad=0",
                                        facecolor="white", edgecolor="none", zorder=0))
        ax.text(-0.15, y + 0.38, str(i + 1), fontsize=10, color=GEDEMPT,
                ha="left", va="center", fontweight="bold")
        for k, kaart in enumerate(kaarten):
            teken_kaart(ax, 0.6 + k * 0.92, y + 0.02, kaart, breedte=0.82, hoogte=0.86)
        ax.text(5.6, y + 0.55, naam, fontsize=12,
                fontweight="bold", color=ROOD if sterkste else PRIMAIR, va="center")
        ax.text(5.6, y + 0.2, uitleg, fontsize=9.5, color=GEDEMPT, va="center")

    ax.annotate("", xy=(23.0, 0.35), xytext=(23.0, (len(rijen) - 1) * hoog + 0.55),
                arrowprops=dict(arrowstyle="-|>", color=ACCENT, linewidth=1.8))
    ax.text(23.2, (len(rijen) - 1) * hoog * 0.5 + 0.45, "sterker", fontsize=10,
            color=ACCENT, rotation=270, va="center", fontweight="bold")

    ax.text(0.6, -0.55, "Elke speler maakt de beste 5-kaartshand uit zijn 2 hole cards "
                        "plus de 5 kaarten op tafel.",
            fontsize=10, color=PRIMAIR, style="italic")
    return bewaar(fig, map_, "handsterkte")


def plaat_montecarlo(map_):
    """
    Wat Monte Carlo is: één worp zegt niets, duizend worpen zeggen genoeg.

    Bewust met munten en niet met kaarten -- het idee moet los staan van poker
    voordat je het erop toepast. De lijn is een echte simulatie, geen getekende
    curve: als het idee klopt, hoort hij vanzelf naar de goede waarde te lopen.
    """
    import random

    random.seed(7)
    worpen, aandeel, kop = [], [], 0
    for n in range(1, 2001):
        kop += random.random() < 0.5
        worpen.append(n)
        aandeel.append(100 * kop / n)

    fig, ax = plt.subplots(figsize=(9.0, 3.9), dpi=200)
    fig.patch.set_facecolor(PAPIER)
    ax.set_facecolor(PAPIER)
    ax.plot(worpen, aandeel, color=ACCENT, linewidth=1.4)
    ax.axhline(50, color=ROOD, linestyle="--", linewidth=1.2)
    ax.text(2010, 50, " de echte kans", color=ROOD, fontsize=9, va="center")
    ax.set_xlim(1, 2000)
    ax.set_ylim(0, 100)
    ax.set_xscale("log")
    ax.set_xlabel("aantal keer gegooid (logaritmisch)")
    ax.set_ylabel("% kop tot nu toe")
    ax.set_title("Tien worpen zeggen niets. Duizend worpen zeggen genoeg.",
                 loc="left", fontsize=12, fontweight="bold", color=PRIMAIR)
    for rand in ("top", "right"):
        ax.spines[rand].set_visible(False)
    ax.annotate("na 10 worpen: nog alle kanten op", xy=(10, aandeel[9]),
                xytext=(13, 84), fontsize=9, color=GEDEMPT,
                arrowprops=dict(arrowstyle="->", color=GEDEMPT, linewidth=0.9))
    ax.annotate("na 1000: dicht bij de waarheid", xy=(1000, aandeel[999]),
                xytext=(190, 18), fontsize=9, color=GEDEMPT,
                arrowprops=dict(arrowstyle="->", color=GEDEMPT, linewidth=0.9))
    fig.tight_layout()
    return bewaar(fig, map_, "montecarlo")


def plaat_montecarlo_poker(map_):
    """Hoe dezelfde truc je winkans geeft: uitspelen, tellen, delen."""
    fig, ax = _kale_assen((10.4, 4.0), (-0.5, 17.5), (-1.9, 4.4))

    stappen = [
        ("1. Jouw hand staat vast", "A-A, dat weet je"),
        ("2. Deel de rest willekeurig", "tegenstanders + bord"),
        ("3. Speel uit tot de showdown", "wie heeft de beste vijf?"),
        ("4. Turf of jij won", "1 of 0"),
        ("5. Doe dat 1000 keer", "winkans = gewonnen / 1000"),
    ]
    for i, (titel, onder) in enumerate(stappen):
        x = i * 3.4
        laatste = i == len(stappen) - 1
        vak = FancyBboxPatch((x, 1.5), 2.9, 1.5,
                             boxstyle="round,pad=0.05,rounding_size=0.14",
                             facecolor=ACCENT if laatste else "white",
                             edgecolor=ACCENT, linewidth=1.5, zorder=3)
        ax.add_patch(vak)
        ax.text(x + 1.45, 2.52, titel, fontsize=9.5, fontweight="bold", ha="center",
                color="white" if laatste else PRIMAIR, zorder=4, wrap=True)
        ax.text(x + 1.45, 1.92, onder, fontsize=8.5, ha="center",
                color="#D8E6E0" if laatste else GEDEMPT, zorder=4)
        if i:
            ax.add_patch(FancyArrowPatch((x - 0.5, 2.25), (x, 2.25), arrowstyle="-|>",
                                         mutation_scale=12, color=ACCENT, linewidth=1.4))

    ax.text(8.3, 0.65, "Dat is precies wat schat_winkans() voor je doet.",
            fontsize=12, fontweight="bold", color=PRIMAIR, ha="center")
    ax.text(8.3, -0.1, "Je hoeft het niet te bouwen — je moet weten wat het getal betekent, "
                       "en tegen hoeveel mensen het gerekend is.",
            fontsize=10, color=GEDEMPT, ha="center", style="italic")
    ax.text(8.3, -1.0, "Zelfde idee als n_simulaties in het toernooi: één toernooi is toeval, "
                       "twintig toernooien zijn een meting.",
            fontsize=10, color=ACCENT, ha="center")
    return bewaar(fig, map_, "montecarlo_poker")


ALLE_PLATEN = [plaat_hole_cards, plaat_tafel, plaat_straten, plaat_handverloop,
               plaat_kleuren, plaat_handsterkte, plaat_flowchart, plaat_raiseladder,
               plaat_montecarlo, plaat_montecarlo_poker]


def maak_alles(map_):
    return [maker(map_) for maker in ALLE_PLATEN]


if __name__ == "__main__":
    import sys
    doel = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "plots_week3")
    for pad in maak_alles(doel):
        print(" ", pad)
