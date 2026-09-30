# -*- coding: utf-8 -*-
"""Draait een toernooi met een nagebootste klas, om Werkcollege 8 mee te testen.

    python3 scripts/maak_testtoernooi.py      # duurt ~20 minuten

Schrijft scripts/toernooi_test.json. Daarmee kun je scripts/analyse_toernooi.py
draaien zonder op een echt toernooi te wachten -- handig om de opdrachten van
Werkcollege 8 te controleren voordat de klas ze krijgt.

Het veld bootst een klas na: de meesten hebben het skelet uit Werkcollege 7
genomen en aan de drempels gedraaid, een paar hebben iets simpels ingeleverd,
en een paar hebben echt iets eigens gebouwd.
"""
import json
import os
import random
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
UITVOER = os.path.join(REPO, "scripts", "toernooi_test.json")
sys.path.insert(0, os.path.join(REPO, "api"))

import nbformat
from poker_adapter import speel_toernooi
from winkans import schat_winkans

nb = nbformat.read(os.path.join(REPO, "notebooks", "Week5_Werkcollege7.ipynb"), as_version=4)
SKELET = next(re.sub(r"^%%writefile.*\n", "", "".join(c.source))
              for c in nb.cells if "".join(c.source).startswith("%%writefile mijn_bot_week5.py"))


def skelet_met(tegenstanders, sterk, meedoen, zwak):
    """Het skelet, maar met andere getallen bovenin -- zoals een student het aanpast."""
    bron = (SKELET
            .replace("TEGENSTANDERS = 2", f"TEGENSTANDERS = {tegenstanders}")
            .replace("STERK = 60", f"STERK = {sterk}")
            .replace("MEEDOEN = 45", f"MEEDOEN = {meedoen}")
            .replace("ZWAK = 32", f"ZWAK = {zwak}")
            .replace("SIMULATIES = 300", "SIMULATIES = 150"))
    ruimte = {"schat_winkans": schat_winkans}
    exec(bron, ruimte)
    return ruimte["kies_actie"]


def caller(hand, stack):
    return "call"

def muntje(hand, stack):
    return random.choice(["call", "fold", "raise"])

def goeiehanden(hand, stack):
    return "raise" if (hand[0] == hand[1] or "A" in hand) else ("call" if "K" in hand else "fold")

def superstight(hand, stack):
    return "raise" if hand[0] == hand[1] else "fold"

def altijd_raise(hand, stack):
    return "raise"

def potodds(hand, stack, pot, inzet_om_te_callen):
    w = schat_winkans(hand, tegenstanders=2, simulaties=120)
    if not inzet_om_te_callen:
        return "raise" if w > 45 else "call"
    prijs = 100 * inzet_om_te_callen / (pot + inzet_om_te_callen)
    return "call" if w >= prijs else "fold"

def tafellezer(hand, stack, ronde, bluf_kans, tegenstander_acties_deze_hand=None):
    acties = tegenstander_acties_deze_hand or []
    if any(a["actie"] == "raise" and a["ronde"] == ronde for a in acties):
        return "fold" if not (hand[0] == hand[1] or "A" in hand) else "call"
    w = schat_winkans(hand, tegenstanders=2, simulaties=120)
    if w < 30 and random.random() < bluf_kans:
        return "raise"
    return "raise" if w >= 55 else ("call" if w >= 38 else "fold")


# --- het veld ---
bots = {}
rng = random.Random(4)

# 18 studenten die aan het skelet hebben gedraaid
varianten = [(2, 60, 45, 32), (2, 55, 40, 30), (2, 70, 50, 35), (2, 65, 48, 25),
             (3, 50, 35, 22), (2, 58, 42, 34), (1, 75, 60, 45), (2, 62, 46, 30),
             (2, 68, 44, 28), (3, 45, 32, 20), (2, 60, 50, 38), (2, 72, 55, 40),
             (2, 56, 43, 31), (2, 64, 47, 33), (4, 40, 28, 18), (2, 59, 41, 29),
             (2, 66, 52, 36), (2, 61, 45, 26)]
for i, (t, s, m, z) in enumerate(varianten, start=1):
    bots[f"5001000{i:02d}__w5"] = {"kies_actie": skelet_met(t, s, m, z),
                                   "bluf_kans": round(rng.uniform(0.0, 0.45), 2),
                                   "strategie": None}

# 9 die iets anders hebben ingeleverd
eigen = [("50020001", caller), ("50020002", muntje), ("50020003", goeiehanden),
         ("50020004", superstight), ("50020005", altijd_raise), ("50020006", potodds),
         ("50020007", goeiehanden), ("50020008", caller), ("50020009", muntje)]
for sid, fn in eigen:
    bots[f"{sid}__w5"] = fn

# 3 die de tafel lezen en bluffen
for i, blufkans in enumerate([0.15, 0.3, 0.45], start=1):
    bots[f"5003000{i}__w5"] = {"kies_actie": tafellezer, "bluf_kans": blufkans,
                               "strategie": None}

print(f"{len(bots)} bots, 20 simulaties x 40 handen", file=sys.stderr)
uit = speel_toernooi(bots, n_simulaties=20, n_handen=40, seed=2026)
uit["bluf_kansen"] = {naam: (b.get("bluf_kans") if isinstance(b, dict) else None)
                      for naam, b in bots.items()}
with open(UITVOER, "w") as f:
    json.dump(uit, f)
print(f"klaar: {len(uit['hand_log'])} regels", file=sys.stderr)
