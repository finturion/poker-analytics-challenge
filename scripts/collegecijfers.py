"""
De cijfers voor het doorloopblad, uit een toernooi-uitslag.

Draai dit na elk toernooi en je hebt de vier blokken van het doorloopblad met
actuele getallen. Zo blijft het blad een format en geen momentopname.

    python3 scripts/collegecijfers.py uitslag.json
    python3 scripts/collegecijfers.py --api --week 3 --ronde 1

Met --api leest hij STUDENT_ID en TOKEN uit de omgeving:

    export POKER_STUDENT_ID=... POKER_TOKEN='...'

LET OP: --api roept /toernooi/{week} aan, en dat endpoint DRAAIT het toernooi
als er nog geen uitslag is. Wil je alleen kijken, gebruik dan eerst de
docent-variant /toernooi/{week}/resultaat, die nooit iets start.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

STARTSTACK = 1000


def haal_van_api(week, ronde):
    import urllib.parse
    import urllib.request

    student_id = os.environ.get("POKER_STUDENT_ID")
    token = os.environ.get("POKER_TOKEN")
    if not (student_id and token):
        sys.exit("Zet POKER_STUDENT_ID en POKER_TOKEN in je omgeving, of geef een bestand mee.")
    vraag = urllib.parse.urlencode({"student_id": student_id, "ronde": ronde})
    verzoek = urllib.request.Request(
        f"https://poker-analytics-api.onrender.com/toernooi/{week}?{vraag}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(verzoek, timeout=900) as antwoord:
        return json.load(antwoord)


def bouw_dataframe(uitslag):
    """
    Het hand-log als tabel, met winst per hand erbij.

    Het log bewaart de stack ná elke hand, dus winst is het verschil met de hand
    ervoor -- binnen dezelfde (bot, simulatie, tafel), want simulaties zijn
    parallelle werelden. Vanaf ronde 2 begint niemand op 1000, dus dan komen de
    startstacks uit de uitslag zelf.
    """
    df = pd.DataFrame(uitslag["hand_log"]).sort_values(
        ["bot_naam", "simulatie", "tafel", "hand_nummer"])
    startstacks = uitslag.get("startstacks") or {}
    begin = df["bot_naam"].map(startstacks).fillna(STARTSTACK)
    df["winst"] = df.groupby(["bot_naam", "simulatie", "tafel"])["stack"].diff()
    df["winst"] = df["winst"].fillna(df["stack"] - begin)
    return df


def blok1(df):
    print("\n1 · WAT DE SAMENVATTING VERBERGT")
    beschrijving = df["winst"].describe()
    for label, sleutel in [("gemiddelde", "mean"), ("mediaan", "50%"),
                           ("std", "std"), ("laagste", "min"), ("hoogste", "max")]:
        print(f"   {label:<12} {beschrijving[sleutel]:>9.1f}")
    print(f"   {'nulsom':<12} {df['winst'].sum():>+9.0f}   (moet 0 zijn)")


def blok2(df):
    print("\n2 · DE VERDELING")
    randen = [-10_000, -200, -100, -50, -20, -1, 0, 20, 50, 100, 200, 10_000]
    tellingen, _ = np.histogram(df["winst"], bins=randen)
    breedste = max(tellingen.max(), 1)
    for n, links, rechts in zip(tellingen, randen[:-1], randen[1:]):
        l = "  laagste" if links == randen[0] else f"{links:>9.0f}"
        r = "hoogste" if rechts == randen[-1] else f"{rechts:>6.0f}"
        print(f"   {l} tot {r}  {n:>5}  {'#' * int(46 * n / breedste)}")


def blok3(df, uitslag):
    print("\n3 · WAT DE KLAS DEED")
    az = df[df["aan_zet"]]
    tabel = az.groupby("actie")["winst"].agg(["count", "mean", "median"]).round(1)
    tabel["aandeel"] = (100 * tabel["count"] / len(az)).round(1)
    print(tabel.sort_values("count", ascending=False).to_string())

    fold = az.groupby("bot_naam")["actie"].apply(lambda s: (s == "fold").mean() * 100)
    eind = pd.Series(uitslag["eindstand_per_bot"])
    samen = pd.DataFrame({"fold": fold, "eindstand": eind}).dropna()
    groepen = pd.cut(samen["fold"], [0, 90, 97, 99, 100.1],
                     labels=["< 90%", "90-97%", "97-99%", "99-100%"])
    print("\n   foldpercentage tegenover eindstand:")
    print(samen.groupby(groepen, observed=True)["eindstand"]
          .agg(["count", "mean"]).round(0).to_string())
    print(f"\n   correlatie fold% met eindstand: {samen['fold'].corr(samen['eindstand']):+.2f}")
    print(f"   de klas foldt {(az['actie'] == 'fold').mean() * 100:.1f}% van alle beslissingen")


def blok4(df, uitslag):
    print("\n4 · RUIS TEGENOVER SIGNAAL")
    eind = df.groupby(["bot_naam", "simulatie"])["stack"].last().unstack()
    binnen = (eind.max(axis=1) - eind.min(axis=1)).median()
    gemiddeld = eind.mean(axis=1)
    tussen = gemiddeld.max() - gemiddeld.min()
    print(f"   spreiding BINNEN een bot (mediaan): {binnen:>8.0f}")
    print(f"   verschil TUSSEN beste en slechtste: {tussen:>8.0f}")
    if tussen:
        verhouding = binnen / tussen
        print(f"   ruis is {verhouding:.1f}x het signaal", end="   ")
        print("-> een enkele run zegt weinig" if verhouding > 1
              else "-> de rangorde ligt redelijk vast")
    e = pd.Series(uitslag["eindstand_per_bot"])
    print(f"\n   {len(e)} bots · mediaan {e.median():.0f} · "
          f"van {e.min():.0f} tot {e.max():.0f} · "
          f"{(e > STARTSTACK).sum()} boven de startstack")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    bron = p.add_mutually_exclusive_group(required=True)
    bron.add_argument("bestand", nargs="?", help="een opgeslagen toernooi-uitslag")
    bron.add_argument("--api", action="store_true")
    p.add_argument("--week", type=int, default=3)
    p.add_argument("--ronde", type=int, default=1)
    args = p.parse_args()

    uitslag = (haal_van_api(args.week, args.ronde) if args.api
               else json.load(open(args.bestand, encoding="utf-8")))
    if not uitslag.get("hand_log"):
        sys.exit(uitslag.get("boodschap") or "Geen hand_log in deze uitslag.")

    df = bouw_dataframe(uitslag)
    print(f"Toernooi week {uitslag.get('week')} ronde {uitslag.get('ronde')} · "
          f"{uitslag.get('n_bots')} bots · {len(df)} logregels · "
          f"{uitslag.get('n_simulaties')} simulaties")
    blok1(df)
    blok2(df)
    blok3(df, uitslag)
    blok4(df, uitslag)


if __name__ == "__main__":
    main()
