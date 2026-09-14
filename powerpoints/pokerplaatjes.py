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
    """
    Waar de zeven kaarten vandaan komen waaruit jij je beste vijf maakt.

    Drie bronnen naast elkaar: jouw twee open kaarten, de dichte kaarten van de
    anderen, en het deck waar de vijf op tafel nog uit moeten komen.

    Eerder stond hieronder "je weet niet wat de anderen hebben, je schat het".
    Dat is fout: je schat niet hun kaarten, je schat je eigen winkans. Het
    verschil is precies waar Deel 5 over gaat, dus daar mag de eerste dia van
    het werkcollege niet overheen stappen.
    """
    fig, ax = _kale_assen((10.2, 3.7), (-0.4, 16.4), (-2.3, 3.85))

    ax.text(0, 3.45, "JIJ", fontsize=11, fontweight="bold", color=ACCENT)
    teken_kaart(ax, 0, 1.35, "SA", breedte=0.95, hoogte=1.38)
    teken_kaart(ax, 1.1, 1.35, "HA", breedte=0.95, hoogte=1.38)
    ax.text(1.05, 0.95, "je 2 hole cards", fontsize=9.5, color=PRIMAIR, ha="center", va="top")
    ax.text(1.05, 0.5, "open voor jou, dicht voor de rest",
            fontsize=8.5, color=GEDEMPT, ha="center", va="top")

    ax.text(4.2, 3.45, "DE ANDEREN", fontsize=11, fontweight="bold", color=GEDEMPT)
    for tegenstander in range(2):
        basis = 4.2 + tegenstander * 2.3
        for k in range(2):
            teken_kaart(ax, basis + k * 0.62, 1.35, "XX", breedte=0.95, hoogte=1.38, gedekt=True)
    ax.text(5.85, 0.95, "ieder 2 kaarten, dicht", fontsize=9.5, color=PRIMAIR,
            ha="center", va="top")
    ax.text(5.85, 0.5, "je ziet ze pas bij de showdown",
            fontsize=8.5, color=GEDEMPT, ha="center", va="top")

    ax.text(10.2, 3.45, "HET DECK", fontsize=11, fontweight="bold", color=GEDEMPT)
    for k in range(4):
        teken_kaart(ax, 10.2 + k * 0.14, 1.35 + k * 0.1, "XX",
                    breedte=0.95, hoogte=1.38, gedekt=True)
    ax.add_patch(FancyArrowPatch((11.95, 2.05), (13.05, 2.05), arrowstyle="-|>",
                                 mutation_scale=13, color=ACCENT, linewidth=1.5))
    ax.text(13.3, 2.45, "5 kaarten", fontsize=10, fontweight="bold", color=ACCENT)
    ax.text(13.3, 2.0, "komen open op tafel", fontsize=9.5, color=PRIMAIR)
    ax.text(13.3, 1.55, "de rest blijft dicht", fontsize=9, color=GEDEMPT)

    ax.text(8.0, -0.7, "Jij maakt de beste 5 uit jouw 2 + de 5 op tafel — 7 kaarten om uit te kiezen.",
            fontsize=12, fontweight="bold", color=PRIMAIR, ha="center")
    ax.text(8.0, -1.45, "Je weet niet wat de anderen hebben, en je hoeft dat ook niet te raden: "
                        "wat je schat is je eigen winkans.",
            fontsize=10, color=ACCENT, ha="center", style="italic")
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
    """
    De vier letters, en welke twee niet met het Nederlandse woord kloppen.

    S en H kloppen allebei: Spades/schoppen en Hearts/harten beginnen in beide
    talen met dezelfde letter. D en C niet -- die komen van Diamonds en Clubs,
    terwijl wij ruiten en klaveren zeggen. Dat zijn dus de twee die je door
    elkaar haalt, en dan bouw je een flush die er niet is.
    """
    fig, ax = _kale_assen((8.4, 3.0), (-0.4, 12.4), (-1.8, 2.6))

    for i, (letter, (symbool, is_rood, nl, en)) in enumerate(KLEUREN.items()):
        x = i * 3.0
        klopt = letter == nl[0].upper()
        teken_kaart(ax, x, 0.5, f"{letter}A", breedte=0.98, hoogte=1.4)
        ax.text(x + 1.3, 1.9, letter, fontsize=18, fontweight="bold",
                color=ROOD if is_rood else PRIMAIR, va="top")
        ax.text(x + 1.3, 1.28, nl, fontsize=10.5, color=PRIMAIR, va="top")
        ax.text(x + 1.3, 0.88, en, fontsize=9, color=GEDEMPT, va="top", style="italic")
        ax.text(x + 1.3, 0.48, "zelfde letter" if klopt else "NIET onze letter",
                fontsize=8.5, color=ACCENT if klopt else ROOD, va="top",
                fontweight="normal" if klopt else "bold")

    ax.text(5.8, -1.05, "S en H kloppen in allebei de talen. D en C niet — "
                        "haal die twee door elkaar en je bouwt een flush die er niet is.",
            fontsize=10.5, color=PRIMAIR, ha="center")
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
    """
    Twee regels naast elkaar: hoe het in het echte spel gaat, en wat onze
    engine ervan maakt.

    De echte regel is niet "het volgende veelvoud van 20". Hij is: je verhoogt
    met minstens zoveel als de vorige verhoging, en nooit met minder dan de big
    blind. Raist iemand van 20 naar 100 -- een verhoging van 80 -- dan moet de
    volgende minstens naar 180. Dat is precies de regel die bluffen duur maakt.

    Onze engine doet iets simpelers, en die +10 die daar soms uit komt bestaat
    in het echte spel niet. Dat staat er daarom bij: studenten die het opzoeken
    horen niet te denken dat wij het fout uitleggen.
    """
    fig, ax = _kale_assen((10.6, 4.6), (-0.5, 17.0), (-3.0, 4.6))

    # ---- de echte regel ----
    ax.text(0, 4.15, "IN HET ECHTE SPEL", fontsize=10.5, fontweight="bold", color=ACCENT)
    ax.text(0, 3.7, "Je verhoogt met minstens zoveel als de vorige verhoging — "
                    "en nooit met minder dan de big blind.",
            fontsize=10, color=PRIMAIR)

    echte = [("20", "big blind", ""), ("40", "minimaal", "+20"),
             ("100", "mag ook", "+60"), ("160", "dan minimaal", "+60")]
    for i, (bedrag, label, stap) in enumerate(echte):
        x = i * 2.6
        vak = FancyBboxPatch((x, 1.85), 1.5, 0.95,
                             boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor="white", edgecolor=LIJN, linewidth=1.3, zorder=3)
        ax.add_patch(vak)
        ax.text(x + 0.75, 2.48, bedrag, fontsize=15, fontweight="bold",
                ha="center", color=PRIMAIR, zorder=4)
        ax.text(x + 0.75, 2.06, label, fontsize=7.5, ha="center", color=GEDEMPT, zorder=4)
        if stap:
            ax.add_patch(FancyArrowPatch((x - 1.0, 2.32), (x, 2.32), arrowstyle="-|>",
                                         mutation_scale=11, color=ACCENT, linewidth=1.3))
            ax.text(x - 0.5, 2.9, stap, fontsize=9, ha="center", color=ACCENT,
                    fontweight="bold")

    ax.text(10.6, 2.75, "Wie 80 erbij legt,", fontsize=9.5, color=PRIMAIR)
    ax.text(10.6, 2.3, "dwingt de volgende", fontsize=9.5, color=PRIMAIR)
    ax.text(10.6, 1.85, "ook 80 erbij te leggen.", fontsize=9.5, color=PRIMAIR)

    # ---- wat onze engine doet ----
    ax.text(0, 1.05, "IN ONZE ENGINE", fontsize=10.5, fontweight="bold", color=ROOD)
    ax.text(0, 0.6, "Simpeler: het bod gaat naar het volgende veelvoud van 20. "
                    "Geen verdubbeling, en geen groeiende verhoging.",
            fontsize=10, color=PRIMAIR)

    onze = [("20", ""), ("40", "+20"), ("60", "+20"), ("80", "+20")]
    for i, (bedrag, stap) in enumerate(onze):
        x = i * 2.6
        vak = FancyBboxPatch((x, -1.35), 1.5, 0.9,
                             boxstyle="round,pad=0.04,rounding_size=0.1",
                             facecolor="white", edgecolor=LIJN, linewidth=1.3, zorder=3)
        ax.add_patch(vak)
        ax.text(x + 0.75, -0.85, bedrag, fontsize=15, fontweight="bold",
                ha="center", va="center", color=PRIMAIR, zorder=4)
        if stap:
            ax.add_patch(FancyArrowPatch((x - 1.0, -0.9), (x, -0.9), arrowstyle="-|>",
                                         mutation_scale=11, color=ROOD, linewidth=1.3))
            ax.text(x - 0.5, -0.42, stap, fontsize=9, ha="center", color=ROOD)

    ax.text(10.6, -0.6, "Gemeten in een echt toernooi:", fontsize=9.5, color=GEDEMPT)
    ax.text(10.6, -1.05, "72% van de raises voegt 20 toe,", fontsize=9.5, color=PRIMAIR)
    ax.text(10.6, -1.5, "28% voegt er maar 10 toe — na een", fontsize=9.5, color=PRIMAIR)
    ax.text(10.6, -1.95, "all-in die een oneven bedrag achterlaat.", fontsize=9.5, color=PRIMAIR)

    vak = FancyBboxPatch((0, -2.85), 9.3, 0.75,
                         boxstyle="round,pad=0.04,rounding_size=0.1",
                         facecolor="#F0F6F3", edgecolor=ACCENT, linewidth=1.4, zorder=3)
    ax.add_patch(vak)
    ax.text(0.3, -2.47, "grote_raise", fontsize=11.5, fontweight="bold",
            color=ACCENT, va="center", zorder=4)
    ax.text(2.5, -2.47, "zet in een keer naar 200 — tien big blinds, een vijfde van je startstack.",
            fontsize=10, color=PRIMAIR, va="center", zorder=4)

    ax.text(10.6, -2.47, "Max 2 raises per straat.", fontsize=9.5, color=GEDEMPT, va="center")
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
    """
    Hoe dezelfde truc je winkans geeft: uitspelen, tellen, delen.

    De titels staan op twee regels en niet op een. Matplotlib breekt tekst niet
    af binnen een vorm, dus een titel die breder is dan zijn kader loopt gewoon
    de buurman in -- en dat deed hij: "1. Jouw hand staat vast" schoof dwars
    door stap 2 heen.

    De afsluitende zinnen staan hier niet meer: die staan al onder de dia, en
    twee keer hetzelfde is precies wat een dia druk maakt.
    """
    fig, ax = _kale_assen((10.8, 2.9), (-0.5, 17.3), (-0.9, 2.9))

    stappen = [
        ("Jouw hand\nstaat vast", "A-A, dat weet je"),
        ("Deel de rest\nwillekeurig", "tegenstanders + bord"),
        ("Speel uit tot\nde showdown", "wie heeft de beste vijf?"),
        ("Turf of\njij won", "1 of 0"),
        ("Doe dat\n1000 keer", "gewonnen / 1000"),
    ]
    for i, (titel, onder) in enumerate(stappen):
        x = i * 3.45
        laatste = i == len(stappen) - 1
        vak = FancyBboxPatch((x, 0.15), 2.95, 1.95,
                             boxstyle="round,pad=0.05,rounding_size=0.14",
                             facecolor=ACCENT if laatste else "white",
                             edgecolor=ACCENT, linewidth=1.5, zorder=3)
        ax.add_patch(vak)
        ax.text(x + 0.18, 1.92, str(i + 1), fontsize=9, fontweight="bold",
                color=GROEN_LICHT if laatste else ACCENT, va="top", zorder=4)
        ax.text(x + 1.48, 1.62, titel, fontsize=10, fontweight="bold", ha="center",
                va="top", linespacing=1.35,
                color="white" if laatste else PRIMAIR, zorder=4)
        ax.text(x + 1.48, 0.45, onder, fontsize=8, ha="center",
                color="#D8E6E0" if laatste else GEDEMPT, zorder=4)
        if i:
            ax.add_patch(FancyArrowPatch((x - 0.5, 1.12), (x, 1.12), arrowstyle="-|>",
                                         mutation_scale=12, color=ACCENT, linewidth=1.4))

    ax.text(8.4, -0.55, "Dat is precies wat schat_winkans() voor je doet.",
            fontsize=12.5, fontweight="bold", color=PRIMAIR, ha="center")
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
