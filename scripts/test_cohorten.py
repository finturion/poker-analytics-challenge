#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bewijst dat twee lichtingen elkaars data niet zien.

    python3 scripts/test_cohorten.py

Waarom dit bestaat: alle opslag is alleen op WEEK gesleuteld. Zonder cohort
landt week 3 van de tweede lichting bovenop week 3 van de eerste -- inzendingen,
galerij, reviews en de toernooi-uitslag. Dat is niet iets wat je merkt aan een
foutmelding; je merkt het aan een ranglijst met vreemde namen erin.

De test draait database.py drie keer in een verse interpreter: zonder cohort, en
met twee verschillende. Verse interpreter omdat COHORT bij het importeren wordt
gelezen -- een env var halverwege omzetten verandert niets meer.
"""
import json
import os
import subprocess
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
API = os.path.join(os.path.dirname(HIER), "api")

geslaagd = gezakt = 0


def check(voorwaarde, omschrijving):
    global geslaagd, gezakt
    if voorwaarde:
        geslaagd += 1
        print(f"  ok  {omschrijving}")
    else:
        gezakt += 1
        print(f"  XX  {omschrijving}")


SCRIPT = """
import json, os, sys
sys.path.insert(0, %(api)r)
import database as db
actie = sys.argv[1]
if actie == "schrijf":
    db.sla_submissions_op({"3": {sys.argv[2]: ["inzending"]}})
    db.sla_toernooi_resultaat_op("3", {"wie": sys.argv[2]})
print(json.dumps({
    "cohort": db.COHORT,
    "submissions": db.laad_submissions(),
    "toernooi": db.laad_toernooi_resultaat("3"),
    "sleutel": db._met_cohort("submissions_db.json"),
}))
"""


def draai(werkmap, cohort, actie, naam=""):
    omgeving = dict(os.environ)
    omgeving.pop("DATABASE_URL", None)
    omgeving.pop("POKER_TOKENS_JSON", None)
    if cohort is None:
        omgeving.pop("POKER_COHORT", None)
    else:
        omgeving["POKER_COHORT"] = cohort
    uit = subprocess.run(
        [sys.executable, "-c", SCRIPT % {"api": API}, actie, naam],
        cwd=werkmap, env=omgeving, capture_output=True, text=True)
    if uit.returncode != 0:
        return {"fout": uit.stderr.strip().split("\n")[-1]}
    return json.loads(uit.stdout.strip().split("\n")[-1])


werkmap = tempfile.mkdtemp()
print("1. Zonder cohort verandert er niets aan de sleutels\n")
zonder = draai(werkmap, None, "schrijf", "eerste_lichting")
check(zonder["sleutel"] == "submissions_db.json",
      f"sleutel blijft kaal: {zonder['sleutel']}")
check(zonder["submissions"] == {"3": {"eerste_lichting": ["inzending"]}},
      "wat je schrijft lees je terug")

print("\n2. Een tweede lichting ziet de eerste niet\n")
tweede = draai(werkmap, "2027-sem2", "schrijf", "tweede_lichting")
check(tweede["sleutel"] == "2027-sem2/submissions_db.json",
      f"sleutel krijgt voorvoegsel: {tweede['sleutel']}")
check("eerste_lichting" not in json.dumps(tweede["submissions"]),
      "de inzending van de eerste lichting is onzichtbaar")
check(tweede["toernooi"] == {"wie": "tweede_lichting"},
      "week 3 van de tweede lichting is een eigen toernooi")

print("\n3. En de eerste is niet overschreven\n")
nogmaals = draai(werkmap, None, "lees")
check(nogmaals["submissions"] == {"3": {"eerste_lichting": ["inzending"]}},
      "de eerste lichting staat er nog precies zo")
check(nogmaals["toernooi"] == {"wie": "eerste_lichting"},
      "ook haar toernooi van week 3 is intact")

print("\n4. Een derde lichting ziet geen van beide\n")
derde = draai(werkmap, "2028-sem1", "lees")
check(derde["submissions"] == {}, "schone lei")
# laad_toernooi_resultaat geeft None als er niets staat, geen lege dict.
check(not derde["toernooi"], "geen toernooi uit een andere lichting")

print("\n5. Een gevaarlijk voorvoegsel wordt geweigerd\n")
for slecht in ("../ontsnapt", "met/schuine/streep", "-begint-met-streepje"):
    uit = draai(werkmap, slecht, "lees")
    check("fout" in uit, f"{slecht!r} geweigerd")

print(f"\n{geslaagd} geslaagd, {gezakt} gezakt")
sys.exit(1 if gezakt else 0)
