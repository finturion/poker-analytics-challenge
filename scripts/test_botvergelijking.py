#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vergelijkt Werkcollege 8, Deel 1 twee bots op DEZELFDE situatie?

    python3 scripts/test_botvergelijking.py

In dat deel zet een student zijn eigen bot naast die van een klasgenoot. Zijn
eigen bot roept hij aan met vraag_eigen_bot() uit _hulpfuncties_week5; die van
de klasgenoot draait op de server via speel_testgevallen(). Twee verschillende
stukken code, en de hele oefening staat of valt ermee dat ze hetzelfde invullen.

Twee dingen die hier zijn misgegaan en die deze test vastzet:

1. Een bot uit Werkcollege 7 vraagt hand_met_kleur, bord, pot en
   inzet_om_te_callen zonder default, want het toernooi vult ze altijd. Een
   testgeval met alleen hand/stack/ronde gaf daarom
   "TypeError: missing 4 required positional arguments" -- precies bij de bot
   die het werkcollege volgt.
2. Vullen beide kanten die gaten anders op, dan staan er twee acties naast
   elkaar die over twee verschillende situaties gaan. Dat ziet er goed uit en
   is stil fout, wat erger is dan een foutmelding.
"""
import os
import re
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "api"))
sys.path.insert(0, os.path.join(WORTEL, "notebooks"))

import nbformat

from bot_validator import _STANDAARD_TESTGEVAL, speel_testgevallen
from _hulpfuncties_week5 import vraag_eigen_bot

geslaagd, gezakt = 0, []


def check(naam, voorwaarde, detail=""):
    global geslaagd
    if voorwaarde:
        geslaagd += 1
        print(f"  ok   {naam}")
    else:
        gezakt.append(f"{naam} — {detail}")
        print(f"  FOUT {naam}  {detail}")


def skelet_uit_werkcollege7():
    """De bot die studenten in Deel 2 van Werkcollege 7 wegschrijven."""
    nb = nbformat.read(os.path.join(WORTEL, "notebooks", "Week5_Werkcollege7.ipynb"),
                       as_version=4)
    for cel in nb.cells:
        bron = "".join(cel.source)
        if bron.startswith("%%writefile mijn_bot_week5.py"):
            return re.sub(r"^%%writefile.*\n", "", bron)
    raise SystemExit("de %%writefile-cel van Werkcollege 7 niet gevonden")


SKELET = skelet_uit_werkcollege7()

# Precies de testgevallen die in Werkcollege 8, Deel 1 staan.
TESTGEVALLEN = [
    {"hand": ["7", "2"], "stack": 1000, "ronde": "preflop"},
    {"hand": ["A", "A"], "stack": 1000, "ronde": "preflop"},
    {"hand": ["7", "2"], "stack": 50, "ronde": "preflop"},
]

print("\n--- De bot van je klasgenoot, via de server ---")
uitslag = speel_testgevallen(SKELET, week=5, testgevallen=TESTGEVALLEN,
                             strategie=None, bluf_kans=0.0)
check("het skelet uit Werkcollege 7 crasht niet op deze testgevallen",
      uitslag["foutmelding"] is None, uitslag["foutmelding"])
check("en geeft voor elk testgeval een actie",
      uitslag["acties"] is not None and len(uitslag["acties"]) == len(TESTGEVALLEN),
      uitslag["acties"])

print("\n--- Dezelfde bot, maar dan als 'jouw eigen bot' in het notebook ---")
# schat_winkans staat klaar VOORDAT de botcode draait, net als op de server
# (api/winkans.py) en net als laad_bot() het in het notebook doet.
from _hulpfuncties_week3 import schat_winkans

ruimte = {"schat_winkans": schat_winkans}
exec(SKELET, ruimte)
eigen = ruimte["kies_actie"]
acties_eigen = [vraag_eigen_bot(eigen, bluf_kans=0.0, **geval) for geval in TESTGEVALLEN]
check("vraag_eigen_bot() komt er ook doorheen", all(isinstance(a, str) for a in acties_eigen),
      acties_eigen)

print("\n--- En vullen ze dezelfde gaten? ---")
for geval, van_server, van_notebook in zip(TESTGEVALLEN, uitslag["acties"] or [], acties_eigen):
    gelijk = van_server == van_notebook
    check(f"{str(geval['hand']):10} stack {geval['stack']:>5}: server {van_server} "
          f"== notebook {van_notebook}", gelijk,
          "de twee kolommen gaan over verschillende situaties")

print("\n--- De standaardwaarden staan aan beide kanten gelijk ---")
# vraag_eigen_bot heeft ze als default-argumenten; de server in een dict.
import inspect
defaults = {naam: p.default for naam, p in inspect.signature(vraag_eigen_bot).parameters.items()
            if p.default is not inspect.Parameter.empty}
for veld in ("ronde", "pot", "inzet_om_te_callen"):
    check(f"{veld}: server {_STANDAARD_TESTGEVAL[veld]!r} == notebook {defaults.get(veld)!r}",
          _STANDAARD_TESTGEVAL[veld] == defaults.get(veld))

print("\n--- Eigen kleuren meesturen moet blijven werken ---")
FLUSHBOT = '''
def kies_actie(hand_met_kleur, bord):
    return "raise" if len({k[0] for k in hand_met_kleur}) == 1 else "fold"
'''
met_kleur = speel_testgevallen(
    FLUSHBOT, week=5, strategie=None, bluf_kans=0.0,
    testgevallen=[{"hand": ["A", "K"], "hand_met_kleur": ["SA", "SK"]},
                  {"hand": ["A", "K"], "hand_met_kleur": ["SA", "HK"]}])
check("een testgeval met eigen kleuren wordt niet overschreven",
      met_kleur["acties"] == ["raise", "fold"], met_kleur)

print(f"\n{geslaagd} geslaagd, {len(gezakt)} gezakt")
for regel in gezakt:
    print("   ", regel)
sys.exit(1 if gezakt else 0)
