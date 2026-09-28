#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Krijgt een bot bij de VALIDATIE hetzelfde te zien als in het TOERNOOI?

    python3 scripts/test_validatie_als_toernooi.py

Waarom dit bestaat. In september 2026 stond in bot_validator._TEST_RONDE_SCENARIOS
een tegenstander-actie zonder veld `ronde`:

    {"bot_naam": "TestBot", "actie": "call", "bedrag": 20}

terwijl poker_adapter dat veld er in een echt toernooi altijd bij zet. Gevolg: een
bot die netjes filtert op `a["ronde"] == ronde` -- precies wat Werkcollege 7 leert,
want de lijst loopt over de hele hand -- crashte bij het inleveren op
KeyError: 'ronde' en werd afgekeurd. Een bot die dat filter NIET had, kwam er
zonder klacht doorheen. De validatie beloonde dus de fout die ze moest vangen.

Dat is geen bug in één dict maar een soort bug: zodra de twee kanten uit elkaar
lopen, faalt de goede student. Deze test vergelijkt ze daarom rechtstreeks, door
echt een paar handen te spelen en op te schrijven wat een bot binnenkrijgt.
"""
import os
import sys

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORTEL, "api"))

from bot_validator import _TEST_RONDE_SCENARIOS, valideer_bot_code
from poker_adapter import speel_toernooi

geslaagd, gezakt = 0, []


def check(naam, voorwaarde, detail=""):
    global geslaagd
    if voorwaarde:
        geslaagd += 1
        print(f"  ok   {naam}")
    else:
        gezakt.append(f"{naam} — {detail}")
        print(f"  FOUT {naam}  {detail}")


# ---------- 1. wat ziet een bot in een ECHT toernooi? ----------
gezien_in_toernooi = []


def spion(hand, stack, ronde, tegenstander_acties_deze_hand=None):
    for actie in tegenstander_acties_deze_hand or []:
        gezien_in_toernooi.append(actie)
    return "call"


def tegenspeler(hand, stack):
    return "raise" if ("A" in hand or "K" in hand or hand[0] == hand[1]) else "call"


print("\n--- Een paar echte handen spelen om te zien wat de engine meegeeft ---")
speel_toernooi({"Spion": spion, "Tegenspeler A": tegenspeler, "Tegenspeler B": tegenspeler},
               n_simulaties=2, n_handen=25, seed=3)
check("de spion heeft tegenstander-acties gezien", len(gezien_in_toernooi) > 0,
      f"{len(gezien_in_toernooi)} acties")

sleutels_toernooi = set()
for actie in gezien_in_toernooi:
    sleutels_toernooi |= set(actie)
print(f"       velden in het toernooi: {sorted(sleutels_toernooi)}")


# ---------- 2. en wat ziet hij bij de VALIDATIE? ----------
sleutels_validatie = set()
acties_in_validatie = 0
for scenario in _TEST_RONDE_SCENARIOS:
    for actie in scenario.get("tegenstander_acties_deze_hand") or []:
        acties_in_validatie += 1
        sleutels_validatie |= set(actie)
print(f"       velden bij de validatie: {sorted(sleutels_validatie)}")

check("de validatie test ook mét tegenstander-acties", acties_in_validatie > 0,
      f"{acties_in_validatie} acties")
check("elk veld uit het toernooi zit ook in de validatie",
      sleutels_toernooi <= sleutels_validatie,
      f"mist bij de validatie: {sorted(sleutels_toernooi - sleutels_validatie)}")
check("de validatie verzint geen velden die het toernooi niet heeft",
      sleutels_validatie <= sleutels_toernooi,
      f"alleen bij de validatie: {sorted(sleutels_validatie - sleutels_toernooi)}")


# ---------- 3. de test moet filteren ook belonen ----------
# Staat er in een scenario alleen een actie uit dezelfde ronde, dan geven een bot
# mét en zonder filter hetzelfde antwoord en meet de validatie niets.
verschil_mogelijk = any(
    any(a.get("ronde") != s["ronde"] for a in (s.get("tegenstander_acties_deze_hand") or []))
    for s in _TEST_RONDE_SCENARIOS)
check("minstens één scenario heeft een actie uit een ANDERE ronde", verschil_mogelijk,
      "zonder dat geeft filteren op ronde hetzelfde antwoord als niet filteren")


# ---------- 4. de bot die het goed doet, moet erdoor ----------
BOT_MET_FILTER = '''
def kies_actie(hand, stack, ronde, bluf_kans, tegenstander_acties_deze_hand=None):
    """Zoals Werkcollege 7 het leert: filter op ronde, de lijst loopt over de hele hand."""
    acties = tegenstander_acties_deze_hand or []
    geraised = any(a["actie"] == "raise" and a["ronde"] == ronde for a in acties)
    if geraised:
        return "fold"
    return "raise" if "A" in hand else "call"
'''

print("\n--- De bot uit het werkcollege inleveren ---")
uitslag = valideer_bot_code(BOT_MET_FILTER, week=5, strategie=None, bluf_kans=0.3)
check("een bot die op ronde filtert wordt goedgekeurd", uitslag["geldig"] is True,
      uitslag.get("foutmelding"))
check("en hij geeft niet overal hetzelfde antwoord",
      uitslag.get("constante_bot") is False, uitslag.get("constante_bot"))

print(f"\n{geslaagd} geslaagd, {len(gezakt)} gezakt")
for regel in gezakt:
    print("   ", regel)
sys.exit(1 if gezakt else 0)
