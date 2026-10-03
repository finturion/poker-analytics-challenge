#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kijkt of de API nog bij zijn opgeslagen data kan.

    python3 scripts/controleer_opslag.py

Vraagt om je docent-token en haalt een paar dingen op die alleen uit de database
kunnen komen. Bedoeld om te draaien na een wijziging aan de opslag -- een
cohort-voorvoegsel, een nieuwe sleutel, een migratie. Een API die start en op
/versie antwoordt bewijst namelijk niets: die antwoordt precies zo met een lege
database.
"""
import getpass
import json
import os
import sys

import requests

API_URL = "https://poker-analytics-api.onrender.com"


def main():
    token = os.environ.get("POKER_DOCENT_TOKEN") or getpass.getpass("Docent-token: ")
    kop = {"Authorization": f"Bearer {token}"}

    versie = requests.get(f"{API_URL}/versie", timeout=30).json()
    print(f"commit  {versie['kort']}   cohort: {versie.get('cohort', '(geen veld)')}")
    print()

    goed = True

    bonus = requests.get(f"{API_URL}/bonus", headers=kop, timeout=60)
    if bonus.status_code != 200:
        print(f"  XX  /bonus gaf HTTP {bonus.status_code}")
        goed = False
    else:
        data = bonus.json()
        scoorders = [s for s in data["studenten"] if s["bonus"] > 0]
        hoogste = max([s["bonus"] for s in scoorders], default=0)
        print(f"  ok  {len(data['studenten'])} studenten bekend, "
              f"{len(scoorders)} met bonus, hoogste {hoogste}")
        if not data["studenten"]:
            print("      LET OP: leeg. De API praat met een lege opslag.")
            goed = False

    for ronde, wat in ((1, "woensdag"), (2, "eindronde")):
        uit = requests.get(f"{API_URL}/toernooi/5/uitgebreid-docent",
                           params={"ronde": ronde}, headers=kop, timeout=120)
        if uit.status_code != 200:
            print(f"  XX  uitgebreide log ronde {ronde} gaf HTTP {uit.status_code}")
            goed = False
            continue
        d = uit.json()
        if d["beschikbaar"]:
            print(f"  ok  ronde {ronde} ({wat}): {d['n_regels']} beslissingen "
                  f"over {len(d['bots'])} bots")
        else:
            print(f"  --  ronde {ronde} ({wat}): geen uitgebreide log "
                  f"(van voor 30 september, dat klopt)")

    print()
    print("Opslag is bereikbaar." if goed else "ER IS IETS MIS met de opslag.")
    return 0 if goed else 1


if __name__ == "__main__":
    sys.exit(main())
