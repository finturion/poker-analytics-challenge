#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maakt een toernooibestand waarmee week 1 en 2 kunnen werken zonder API.

    python3 scripts/maak_voorbeeldtoernooi.py

Leest een echt gedraaid toernooi en schrijft notebooks/data/voorbeeldtoernooi.json:
dezelfde structuur, dezelfde getallen, maar met verzonnen botnamen in plaats van
studentnummers.

WAAROM DIT BESTAAT
------------------
De API zit nu vanaf werkcollege 1 in de stof: inleveren in WC1, en in WC2 een
deel over wat een API is, het toernooi ophalen en peer review. Dat is 45 van de
85 minuten van WC2, in dezelfde week waarin ook tien programmeerconcepten
binnenkomen -- en het brengt een hele categorie fouten mee die niets met
programmeren te maken heeft: tokens, 401's, netwerk.

Met dit bestand kunnen week 1 en 2 op echte data werken zonder dat er iets over
de lijn gaat. De API komt dan in week 3, als er een bot is die het waard is om
in te leveren.

ECHTE DATA, GEEN VERZINSEL
--------------------------
De getallen komen uit een toernooi dat werkelijk is gespeeld: dezelfde
stackverlopen, hetzelfde foldgedrag, dezelfde spreiding. Alleen de namen zijn
vervangen. Dat is belangrijk voor de les -- een verzonnen dataset heeft geen
rare uitschieters, en juist die maken een grafiek de moeite waard.

Studentnummers gaan er dus uit. Een vaste naam per bot, zodat een student die
het bestand twee keer laadt dezelfde namen ziet.
"""
import argparse
import json
import os
import random

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
DOEL = '/Users/jerome/Library/Mobile Documents/com~apple~CloudDocs/Full_Stack_dev/HvA_voorbereidingen/IDS_2026_2027_SEM2/Werkcolleges/data/voorbeeldtoernooi.json'

# Namen in plaats van nummers. Herkenbaar genoeg om over te praten ("waarom doet
# Mees zo veel fold?") en duidelijk niet van een echte student.
NAMEN = [
    "Mees", "Suze", "Tobias", "Nora", "Youssef", "Fenna", "Lars", "Amira",
    "Jonas", "Lotte", "Ravi", "Sanne", "Bram", "Iris", "Daan", "Noor",
    "Teun", "Hanna", "Milan", "Jade", "Sem", "Luna", "Finn", "Maud",
    "Olivier", "Vera", "Stijn", "Esmee", "Thijs", "Benthe", "Kaj", "Lieke",
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bron", default="uitslag_week5_ronde1_woensdag.json",
                   help="bestand in scripts/ om van te lezen")
    p.add_argument("--handen", type=int, default=20,
                   help="hoeveel handen per simulatie meenemen (kleiner = sneller laden)")
    p.add_argument("--simulaties", type=int, default=5)
    args = p.parse_args()

    bron = os.path.join(HIER, args.bron)
    if not os.path.exists(bron):
        raise SystemExit(f"Bron niet gevonden: {bron}")
    with open(bron) as f:
        u = json.load(f)

    deelnemers = sorted(set(u["namen_deelnemers"]))
    rng = random.Random(20260108)          # vast, zodat de namen niet elk jaar schuiven
    namen = NAMEN[:]
    rng.shuffle(namen)
    if len(deelnemers) > len(namen):
        raise SystemExit(f"{len(deelnemers)} deelnemers maar maar {len(namen)} namen.")
    vertaal = dict(zip(deelnemers, namen))
    # Referentie- en testbots houden hun naam: die zijn niet van een student.
    for n in (u.get("referentiebots") or []) + (u.get("testbots") or []):
        vertaal.setdefault(n, n)

    log = [
        {**r, "bot_naam": vertaal.get(r["bot_naam"], r["bot_naam"])}
        for r in u["hand_log"]
        if r["simulatie"] < args.simulaties and r["hand_nummer"] <= args.handen
    ]

    uit = {
        "waar_komt_dit_vandaan": (
            "Een echt gespeeld toernooi uit een eerdere lichting. De getallen zijn "
            "onveranderd; alleen de studentnummers zijn vervangen door namen."
        ),
        "week": 1,
        "n_bots": len(vertaal),
        "n_simulaties": args.simulaties,
        "namen_deelnemers": sorted(vertaal[d] for d in deelnemers),
        "referentiebots": sorted(u.get("referentiebots") or []),
        "testbots": sorted(u.get("testbots") or []),
        "eindstand_per_bot": {
            vertaal.get(k, k): v for k, v in u["eindstand_per_bot"].items()},
        "hand_log": log,
    }

    os.makedirs(os.path.dirname(DOEL), exist_ok=True)
    with open(DOEL, "w") as f:
        json.dump(uit, f, ensure_ascii=False)

    import re
    rest = re.findall(r"\b5\d{8}\b", json.dumps(uit))
    print(f"{len(log)} logregels, {len(vertaal)} bots -> {os.path.relpath(DOEL, WORTEL)}")
    print(f"{os.path.getsize(DOEL)/1024:.0f} kB")
    print(f"studentnummers in het bestand: {len(rest)}"
          + ("  <-- FOUT, er mag er geen één in" if rest else "  (goed)"))
    return 1 if rest else 0


if __name__ == "__main__":
    raise SystemExit(main())
