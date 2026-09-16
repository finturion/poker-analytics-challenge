"""
De cijfers van een toernooi-uitslag, als dict in plaats van als print.

Eén bron voor drie afnemers: collegecijfers.py print ze voor het doorloopblad,
maak_histogram_hoorcollege.py tekent er de verdeling mee, en
vul_hoorcollege_aan.py zet ze op de dia's.

Dat is niet netheid maar noodzaak. Bij de vorige ronde zijn deze getallen met de
hand overgetypt naar het doorloopblad, en toen werd "5 handen onder de -200" een
9. Dat soort fout ziet niemand terug: het is een plausibel getal op een nette dia.
"""
import numpy as np
import pandas as pd

STARTSTACK = 1000

# De grenzen van de verdeling. Ongelijk verdeeld met opzet: rond nul zit 92% van
# de handen, dus daar wil je fijne bakjes, en de staarten zijn zo dun dat ze
# alleen als één bakje zichtbaar blijven.
RANDEN = [-10_000, -200, -100, -50, -20, -1, 0, 20, 50, 100, 200, 10_000]

# Welke bakjes op de dia komen. De rest is te fijn voor een zaal.
DIA_BAKJES = [
    ("-200 en lager", -10_000, -200),
    ("-100 tot -20", -100, -20),
    ("-20 tot -1", -20, -1),
    ("0 tot 20", 0, 20),
    ("20 tot 50", 20, 50),
    ("200 en hoger", 200, 10_000),
]


def bouw_dataframe(uitslag):
    """Het hand-log als DataFrame, met de winst per hand erbij."""
    df = pd.DataFrame(uitslag["hand_log"]).sort_values(
        ["bot_naam", "simulatie", "hand_nummer"]
    )
    df["winst"] = (df.groupby(["bot_naam", "simulatie"])["stack"].diff()
                     .fillna(df["stack"] - STARTSTACK))
    return df


def _nl(getal, decimalen=1):
    """Nederlandse komma, want deze getallen gaan naar een dia."""
    return f"{getal:.{decimalen}f}".replace(".", ",")


def _heel(getal):
    """Een heel getal met teken, maar nul is gewoon nul en niet +0."""
    return f"{getal:+.0f}" if round(getal) else "0"


def cijfers_uit(uitslag, df=None):
    """
    Alles wat het hoorcollege van een toernooi nodig heeft, in één dict.

    De vorm is precies die van CIJFERS in vul_hoorcollege_aan.py, zodat je hem
    daar in kunt plakken als je een keer zonder de uitslag wilt draaien.
    """
    if df is None:
        df = bouw_dataframe(uitslag)
    winst = df["winst"]
    az = df[df["aan_zet"]]

    tellingen, _ = np.histogram(winst, bins=RANDEN)
    per_rand = dict(zip(zip(RANDEN[:-1], RANDEN[1:]), tellingen))
    bakjes = []
    for label, links, rechts in DIA_BAKJES:
        # Een dia-bakje kan meerdere rekenbakjes beslaan (-100 tot -20 = twee).
        n = sum(aantal for (a, b), aantal in per_rand.items() if links <= a and b <= rechts)
        bakjes.append((label, int(n)))

    acties = []
    for actie, groep in az.groupby("actie")["winst"]:
        acties.append((actie, len(groep), 100 * len(groep) / len(az),
                       groep.mean(), groep.median()))
    acties.sort(key=lambda r: -r[1])

    eind = pd.Series(uitslag["eindstand_per_bot"])
    fold = az.groupby("bot_naam")["actie"].apply(lambda s: (s == "fold").mean() * 100)
    samen = pd.DataFrame({"eindstand": eind, "fold": fold}).dropna().sort_values(
        "eindstand", ascending=False)

    top = list(samen.head(4).itertuples())
    uitslag_rijen = [
        (i + 1, r.Index, int(round(r.eindstand)), f"{r.fold:.1f}%".replace(".", ","))
        for i, r in enumerate(top)
    ]
    voorsprong = (int(round(top[0].eindstand - top[1].eindstand))
                  if len(top) > 1 else 0)

    namen = set(uitslag.get("namen_deelnemers") or [])
    return {
        "ronde": uitslag.get("ronde"),
        "bots": uitslag.get("n_bots"),
        "studenten": len(namen) if namen else None,
        "logregels": len(df),
        "simulaties": uitslag.get("n_simulaties"),

        "gemiddelde": _nl(winst.mean()),
        "mediaan": _nl(winst.median()),
        "std": f"{winst.std():.0f}",
        "laagste": f"{winst.min():.0f}",
        "hoogste": f"{winst.max():+.0f}",

        "bakjes": bakjes,
        "acties": [
            (actie, f"{aandeel:.1f}%".replace(".", ","), _heel(gem), _heel(med))
            for actie, _, aandeel, gem, med in acties
        ],

        "uitslag": uitslag_rijen,
        "correlatie": f"{samen['fold'].corr(samen['eindstand']):.2f}".replace(".", ","),
        "voorsprong": voorsprong,
    }
