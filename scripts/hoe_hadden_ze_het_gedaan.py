#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hoe hadden bot_handsterkte en bot_uitbuiter het gedaan in het echte week
5-veld, tussen de ingeleverde bots van de klas?

Vijf van de bots uit mijn_bots/ draaien al mee als referentiebot, en van die
vijf weten we de echte uitslag dus gewoon (scripts/uitslag_week5_ronde*.json).
Twee niet: handsterkte en uitbuiter staan niet in api/referentiebots/. Die
worden hier aan hetzelfde veld toegevoegd en meegespeeld.

WAT HIER WEL EN NIET EXACT IS
-----------------------------
De studentbots zijn de echte, uit scripts/bots_week5/. Hun bluf_kans is dat
NIET: die stond in de database en is hier niet beschikbaar, dus iedereen krijgt
dezelfde BLUF_KANS_AANNAME. Alle 28 gebruiken bluf_kans, 26 ook echt in hun
beslisregel, dus dat verschuift de uitslag. Daarom:

- de officiele uitslag wordt hier NIET gereproduceerd;
- het script ijkt zichzelf op de vijf referentiebots, want van die vijf weten we
  de echte plek wel. Gemeten op ronde 6 zet de reconstructie Tafellezer en
  PotOdds precies goed, maar Inzetgrootte, Bluffer en Allrounder 17 tot 25
  percentielpunten te HOOG. De reconstructie vleit agressieve bots dus, en een
  bot die hier onderaan eindigt zou in het echt eerder lager dan hoger staan;
- en elke seed wordt twee keer gedraaid, met en zonder de twee extra bots, zodat
  je ziet hoeveel het veld er sowieso van schuift.

Draaien:  python3 scripts/hoe_hadden_ze_het_gedaan.py
Kost ongeveer een half uur; het draait de seeds parallel over je cores.
"""
import argparse
import concurrent.futures as futures
import glob
import json
import os
import statistics
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(REPO, "api"))
sys.path.insert(0, os.path.join(REPO, "mijn_bots"))

# De knoppen.
SEEDS = [52, 56, 151, 152, 153, 154]   # 52 en 56 zijn de echte rondes 2 en 6
N_SIMULATIES = 10
N_HANDEN = 50
BLUF_KANS_AANNAME = 0.2
# Let op: Referentie_Inzetgrootte komt uit api/referentiebots/ en is de OUDE
# versie met de vaste preflop-tabel. De nieuwe versie uit mijn_bots/ moet er dus
# als aparte bot bij, anders meet je de verandering helemaal niet. Zo spelen oud
# en nieuw in hetzelfde veld tegen elkaar, wat precies de vergelijking is.
EXTRA_BOTS = {"Extra_Handsterkte": ("bot_handsterkte", "balanced", 0.0),
              "Extra_Uitbuiter": ("bot_uitbuiter", "balanced", 0.25),
              "Extra_Inzetgrootte_nieuw": ("bot_inzetgrootte", "aggressive", 0.25)}
UITVOER = os.path.join(HIER, "hoe_hadden_ze_het_gedaan.json")
UITVOER_NA = os.path.join(HIER, "hoe_hadden_ze_het_gedaan_met_bord.json")


def bouw_veld(met_extra):
    """Het veld, opgebouwd in dít proces -- exec'te functies zijn niet picklebaar."""
    from poker_adapter import speel_toernooi  # noqa: F401  (import hier houden)
    from referentiebots import referentiebots_voor
    from toernooi_runner import TESTBOTS
    from winkans import schat_winkans
    import importlib

    bots, onbruikbaar = {}, []
    for pad in sorted(glob.glob(os.path.join(HIER, "bots_week5", "*.py"))):
        sid = os.path.basename(pad)[:-3]
        ruimte = {"schat_winkans": schat_winkans}
        try:
            exec(open(pad).read(), ruimte)
        except Exception:
            onbruikbaar.append(sid)
            continue
        functie = ruimte.get("kies_actie")
        if not callable(functie):
            onbruikbaar.append(sid)
            continue
        bots[sid] = {"kies_actie": functie, "strategie": "balanced",
                     "bluf_kans": BLUF_KANS_AANNAME}

    bots.update(referentiebots_voor(5))
    for naam, functie in TESTBOTS.items():
        bots[naam] = {"kies_actie": functie, "strategie": None, "bluf_kans": None}

    if met_extra:
        for naam, (modulenaam, strategie, bluf) in EXTRA_BOTS.items():
            module = importlib.import_module(modulenaam)
            bots[naam] = {"kies_actie": module.kies_actie,
                          "strategie": strategie, "bluf_kans": bluf}
    return bots, onbruikbaar


def draai_een(opdracht):
    """Eén (seed, met_extra)-combinatie. Draait in een eigen proces."""
    seed, met_extra = opdracht
    from poker_adapter import speel_toernooi
    bots, onbruikbaar = bouw_veld(met_extra)
    uitkomst = speel_toernooi(bots, n_simulaties=N_SIMULATIES, n_handen=N_HANDEN, seed=seed)
    return {"seed": seed, "met_extra": met_extra, "n_bots": len(bots),
            "onbruikbaar": onbruikbaar,
            "eindstand": uitkomst["eindstand_per_bot"]}


def rangcorrelatie(a, b):
    """Spearman over de namen die in allebei voorkomen, zonder scipy."""
    gedeeld = sorted(set(a) & set(b))
    if len(gedeeld) < 3:
        return None, 0
    def rangen(d):
        volgorde = sorted(gedeeld, key=lambda n: -d[n])
        return {naam: i for i, naam in enumerate(volgorde)}
    ra, rb = rangen(a), rangen(b)
    n = len(gedeeld)
    som = sum((ra[naam] - rb[naam]) ** 2 for naam in gedeeld)
    return 1 - 6 * som / (n * (n * n - 1)), n


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--werkers", type=int, default=6)
    args = p.parse_args()

    opdrachten = [(seed, met) for seed in SEEDS for met in (False, True)]
    print(f"{len(opdrachten)} runs ({len(SEEDS)} seeds x met/zonder), "
          f"{N_SIMULATIES} simulaties x {N_HANDEN} handen, {args.werkers} parallel")
    print(f"bluf_kans van de klas is niet bekend en staat voor iedereen op "
          f"{BLUF_KANS_AANNAME}\n")

    resultaten = []
    with futures.ProcessPoolExecutor(max_workers=args.werkers) as pool:
        for klaar in futures.as_completed([pool.submit(draai_een, o) for o in opdrachten]):
            r = klaar.result()
            resultaten.append(r)
            label = "met extra" if r["met_extra"] else "zonder   "
            print(f"  seed {r['seed']:>4} {label}  ({r['n_bots']} bots)  "
                  f"-- {len(resultaten)}/{len(opdrachten)} klaar", flush=True)

    with open(UITVOER_NA, "w") as f:
        json.dump(resultaten, f, indent=2)
    print(f"\nweggeschreven naar {os.path.basename(UITVOER_NA)}")
    rapporteer(resultaten)
    return 0


def rapporteer(resultaten):
    met = [r for r in resultaten if r["met_extra"]]
    zonder = [r for r in resultaten if not r["met_extra"]]

    print(f"\n{'=' * 78}\nIJKING: hoe dicht komt dit bij de echte ronde 6?\n{'=' * 78}")
    # Ronde 6 en niet ronde 2: ronde 2 is op 3 oktober opnieuw gedraaid zonder
    # referentiebots, en dan valt er voor deze ijking niets te vergelijken.
    officieel_pad = os.path.join(HIER, "uitslag_week5_ronde6.json")
    if os.path.exists(officieel_pad):
        with open(officieel_pad) as f:
            officieel = json.load(f)["eindstand_per_bot"]
        eigen = next((r["eindstand"] for r in zonder if r["seed"] == 56), None)
        if eigen:
            rho, n = rangcorrelatie(officieel, eigen)
            print(f"  Spearman over {n} gedeelde bots: {rho:+.2f}")
            print("  1,00 zou betekenen dat de volgorde exact klopt. Het verschil zit in")
            print("  de bluf_kans van de klas, die hier voor iedereen gelijk staat.")

    print(f"\n{'=' * 78}\nDE UITSLAG MET DE TWEE EXTRA BOTS ERBIJ\n{'=' * 78}")
    toon_standen(met, set(EXTRA_BOTS))

    print(f"\n{'=' * 78}\nWAT DE TWEE EXTRA BOTS MET DE REST DEDEN\n{'=' * 78}")
    print(f"  {'bot':<26}{'zonder':>10}{'met':>10}{'verschil':>11}")
    namen = sorted(set(zonder[0]["eindstand"]) & set(met[0]["eindstand"]))
    for naam in namen:
        if not (naam.startswith("Referentie") or naam.startswith("Testbot")):
            continue
        a = statistics.mean([r["eindstand"][naam] for r in zonder])
        b = statistics.mean([r["eindstand"][naam] for r in met])
        print(f"  {naam:<26}{a:>10.0f}{b:>10.0f}{b - a:>+11.0f}")


def toon_standen(runs, uitlichten):
    per_bot = {}
    for r in runs:
        for naam, stand in r["eindstand"].items():
            per_bot.setdefault(naam, []).append(stand)
    ranglijst = sorted(per_bot, key=lambda n: -statistics.mean(per_bot[n]))
    n_bots = len(ranglijst)
    print(f"  {n_bots} bots, gemiddeld over {len(runs)} seeds\n")
    print(f"  {'plek':>5}  {'bot':<26}{'gem. eindstack':>16}{'onzekerheid':>13}")
    for plek, naam in enumerate(ranglijst, start=1):
        bijzonder = naam in uitlichten or naam.startswith("Referentie")
        if not (bijzonder or plek <= 3 or plek > n_bots - 2):
            continue
        waarden = per_bot[naam]
        fout = statistics.stdev(waarden) / len(waarden) ** 0.5 if len(waarden) > 1 else 0.0
        merk = "  <--" if naam in uitlichten else ""
        print(f"  {plek:>5}  {naam:<26}{statistics.mean(waarden):>16.0f}{fout:>13.0f}{merk}")


if __name__ == "__main__":
    sys.exit(main())
