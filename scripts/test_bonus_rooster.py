"""
Test het bonuspuntenschema van de pokerlijn.

Draaien:  python3 scripts/test_bonus_rooster.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "api"))

import bonus_rooster as bonus
from bonus_rooster import (
    BOT_WEKEN,
    MAX_BONUS,
    PRESTATIE_PLEKKEN,
    bonus_hele_klas,
    bonus_per_student,
    prestatiescore,
    prestatietabel,
    score_voor_plek,
)

geslaagd = 0


def check(voorwaarde, omschrijving):
    global geslaagd
    assert voorwaarde, f"GEZAKT: {omschrijving}"
    geslaagd += 1
    print(f"  ok  {omschrijving}")


def inzending(moment, code, geldig=True, constant=False):
    return {
        "bot_code": code,
        "geldig": geldig,
        "bot_check": {"geldig": geldig, "constante_bot": constant},
        "ingeleverd_op": moment,
    }


WEEK = {item["week"]: item for item in BOT_WEKEN}

# ---------------------------------------------------------------------------
print("Het schema zelf")
check(abs(sum(i["gewicht"] for i in BOT_WEKEN) - 1.0) < 1e-9, "de weekgewichten tellen op tot 1,0")
check(WEEK[1]["gewicht"] == 0.0, "week 1 telt niet mee")
check(abs(WEEK[3]["gewicht"] * MAX_BONUS - 0.2) < 1e-9, "week 3 is 0,2 punt waard")
check(abs(WEEK[5]["gewicht"] * MAX_BONUS - 0.8) < 1e-9, "week 5 is 0,8 punt waard")
check(
    abs(bonus.AANDEEL_SPRINT + bonus.AANDEEL_PRESTATIE - 1.0) < 1e-9,
    "sprint en prestatie tellen op tot 1,0",
)
check(
    abs(MAX_BONUS * WEEK[5]["gewicht"] * bonus.AANDEEL_PRESTATIE - 0.32) < 1e-9,
    "de ruisgevoelige helft is nooit meer dan 0,32 punt",
)

# ---------------------------------------------------------------------------
print("\nPrestatiescore: exponentieel aflopende top")
tabel = prestatietabel()
check(len(tabel) == PRESTATIE_PLEKKEN, f"de tabel dekt precies {PRESTATIE_PLEKKEN} plekken")
check(score_voor_plek(1) == 1.0, "plek 1 krijgt het volle deel")
check(
    all(score_voor_plek(p) > score_voor_plek(p + 1) for p in range(1, PRESTATIE_PLEKKEN)),
    "elke plek levert minder op dan de plek erboven",
)
check(
    score_voor_plek(PRESTATIE_PLEKKEN + 1) == 0.0,
    f"buiten de top {PRESTATIE_PLEKKEN} is het nul",
)
check(
    abs(score_voor_plek(3) - score_voor_plek(2) * (score_voor_plek(2) / score_voor_plek(1))) < 1e-9,
    "de afname is exponentieel: elke stap is dezelfde factor",
)
check(
    abs(score_voor_plek(2) - 0.7) < 1e-9 and abs(score_voor_plek(3) - 0.49) < 1e-9,
    "de ladder is 1,00 - 0,70 - 0,49: het zwaartepunt ligt op het podium",
)
check(
    score_voor_plek(10) == 0.0,
    "vanaf plek 10 levert de competitie niets meer op",
)

# 44 studenten, zoals de echte klas
eindstand = {f"s{i:02d}": 3000 - i * 10 for i in range(44)}
check(prestatiescore(eindstand, "s00")[0] == 1.0, "de winnaar van 44 krijgt 1,0")
check(
    prestatiescore(eindstand, f"s{PRESTATIE_PLEKKEN - 1:02d}")[0] == score_voor_plek(PRESTATIE_PLEKKEN),
    "de laatste plek binnen de top krijgt nog iets",
)
check(
    prestatiescore(eindstand, f"s{PRESTATIE_PLEKKEN:02d}")[0] == 0.0,
    "de eerste plek buiten de top krijgt niets",
)
check(
    f"buiten de top {PRESTATIE_PLEKKEN}" in prestatiescore(eindstand, "s30")[1],
    "en dat staat er ook bij, zodat niemand hoeft te raden",
)
check(prestatiescore(eindstand, "z")[0] == 0.0, "wie niet meespeelde krijgt 0,0")
check(prestatiescore({}, "a")[0] is None, "zonder toernooi is de score onbekend, niet 0")
check(
    prestatiescore({"a": 2000, "oefenbot_tight": 9999}, "a", deelnemers=["a"])[0] == 1.0,
    "oefenbots tellen niet mee in het klassement",
)

# ---------------------------------------------------------------------------
print("\nVier profielen door het hele schema")

# Vier studenten: de trouwe zwoeger, de woensdag-stub, de laatbloeier en de
# student die alleen op vrijdag opduikt.
def week_inzendingen(week, wo_code, vr_code, wo_constant=False):
    """Bouwt de inzendingen van één student in één week: woensdag vroeg, tweede deadline net op tijd."""
    item = WEEK[week]
    wo_moment = item["deadline_woensdag"].replace("09:00", "08:30")
    vr_moment = item["deadline_definitief"].replace("18:00", "17:00")
    inzendingen = []
    if wo_code is not None:
        inzendingen.append(inzending(wo_moment, wo_code, constant=wo_constant))
    if vr_code is not None:
        inzendingen.append(inzending(vr_moment, vr_code))
    return inzendingen


submissions = {
    "3": {
        "zwoeger": week_inzendingen(3, "wo3", "vr3"),
        "stub": week_inzendingen(3, "fold", None, wo_constant=True),
        "laatbloeier": week_inzendingen(3, None, None),
        "vrijdagmens": week_inzendingen(3, None, "vr3"),
    },
    "5": {
        "zwoeger": week_inzendingen(5, "wo5", "vr5"),
        "stub": week_inzendingen(5, "fold", "fold", wo_constant=True),
        "laatbloeier": week_inzendingen(5, "wo5", "vr5"),
        "vrijdagmens": week_inzendingen(5, None, "vr5"),
    },
}
# Een realistisch veld: 40 naamloze klasgenoten eromheen, zodat de top 10 ook
# echt een top 10 is. Met een handjevol bots zit iedereen in de prijzen en meet
# de test niets.
def veld(posities):
    """posities: {naam: chips}. Vult aan tot 44 bots met een spreiding eromheen."""
    eindstand = dict(posities)
    for i in range(44 - len(posities)):
        eindstand[f"klasgenoot_{i:02d}"] = 2000 - i * 25
    return {"eindstand_per_bot": eindstand, "namen_deelnemers": list(eindstand)}


toernooien = {
    # zwoeger wint; laatbloeier net in de top; vrijdagmens halverwege; stub onderaan
    "3": veld({"zwoeger": 3000, "laatbloeier": 1850, "vrijdagmens": 1400, "stub": 900}),
    "5": veld({"zwoeger": 2900, "laatbloeier": 1900, "vrijdagmens": 1350, "stub": 850}),
    "5_ronde2": veld({"zwoeger": 3100, "laatbloeier": 1875, "vrijdagmens": 1300, "stub": 800}),
}

resultaten = {r["student_id"]: r for r in bonus_hele_klas(submissions, toernooien)}
for student_id, r in sorted(resultaten.items(), key=lambda kv: -kv[1]["bonus"]):
    week5 = [w for w in r["per_week"] if w["week"] == 5][0]
    print(f"    {student_id:12} bonus {r['bonus']:.3f} -> {r['bonus_afgerond']:.1f}"
          f"   (week5: sprint {week5['sprintscore']:.2f}, prestatie {week5['prestatiescore']:.2f}"
          f" — {week5['uitleg'][-1]})")

check(
    resultaten["zwoeger"]["bonus"] > resultaten["laatbloeier"]["bonus"] > resultaten["stub"]["bonus"],
    "wie de sprints doorloopt staat boven wie dat niet doet",
)
check(
    resultaten["zwoeger"]["bonus"] <= MAX_BONUS + 1e-9,
    "niemand komt boven de 1,0 uit",
)
week3_stub = [w for w in resultaten["stub"]["per_week"] if w["week"] == 3][0]
check(
    week3_stub["sprintscore"] == 0.25,
    "een woensdag-stub zonder vervolg haalt een kwart van de sprint",
)
week5_stub = [w for w in resultaten["stub"]["per_week"] if w["week"] == 5][0]
check(
    "geen verbeterde versie" in " ".join(week5_stub["uitleg"]),
    "dezelfde code opnieuw insturen levert geen punten voor de tweede deadline op",
)
check(
    week5_stub["prestatiescore"] == 0.0,
    "en onderaan het veld van 44 levert de competitie ook niets op",
)
week1 = [w for w in resultaten["zwoeger"]["per_week"] if w["week"] == 1][0]
check(week1["punten"] == 0.0, "week 1 levert geen punten op, ook niet voor de zwoeger")

# ---------------------------------------------------------------------------
print("\nAlleen de laatste ronde telt")
check(
    bonus._laatste_ronde(toernooien, 5)["eindstand_per_bot"]["zwoeger"]
    == toernooien["5_ronde2"]["eindstand_per_bot"]["zwoeger"],
    "week 5 pakt ronde 2, niet ronde 1",
)
check(
    bonus._laatste_ronde(toernooien, 3)["eindstand_per_bot"]["zwoeger"]
    == toernooien["3"]["eindstand_per_bot"]["zwoeger"],
    "week 3 pakt ronde 1, want ronde 2 bestaat daar niet",
)
check(bonus._laatste_ronde(toernooien, 4) is None, "een week zonder toernooi geeft None")

# ---------------------------------------------------------------------------
print("\nDeadlines")
te_laat = {
    "5": [
        inzending(WEEK[5]["deadline_woensdag"].replace("09:00", "09:30"), "wo5"),
        inzending(WEEK[5]["deadline_definitief"].replace("17:00", "23:00"), "vr5"),
    ]
}
r = bonus_per_student("treuzelaar", te_laat, {})
week5 = [w for w in r["per_week"] if w["week"] == 5][0]
check(
    "geen goedgekeurde bot vóór woensdag 09:00" in week5["uitleg"],
    "een half uur te laat op woensdag kost de woensdaghelft",
)
check(
    week5["sprintscore"] == 0.5,
    "maar telt wel als 'vóór de tweede deadline' -- die helft blijft staan",
)
check(
    "geen goedgekeurde bot vóór de vrijdagdeadline" not in week5["uitleg"],
    "de inzending van na de deadline is te laat, die van 09:30 redt die helft",
)

alleen_woensdag = {"5": [inzending(WEEK[5]["deadline_woensdag"].replace("09:00", "08:00"), "wo5")]}
r = bonus_per_student("eenmalig", alleen_woensdag, {})
week5 = [w for w in r["per_week"] if w["week"] == 5][0]
check(
    week5["sprintscore"] == 0.5,
    "op tijd inleveren maar nooit verbeteren levert precies de helft op",
)

op_tijd = {"5": [inzending(WEEK[5]["deadline_woensdag"], "wo5")]}
r = bonus_per_student("precies", op_tijd, {})
week5 = [w for w in r["per_week"] if w["week"] == 5][0]
check(week5["sprintscore"] == 0.5, "precies op de deadline telt nog mee")
check(week5["prestatiescore"] is None, "zonder gedraaid toernooi blijft de prestatie onbekend")

print(f"\n{geslaagd} checks geslaagd.")
