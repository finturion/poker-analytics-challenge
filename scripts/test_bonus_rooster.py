"""
Test het bonuspuntenschema van de pokerlijn.

De regel: twee toernooien in week 5, en je plek levert in elk toernooi punten op
(1e 0,5 / 2e 0,4 / 3e 0,3 / 4e 0,2 / 5e 0,1, daarna niets). Samen max 1,0.

Draaien:  python3 scripts/test_bonus_rooster.py
"""
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HIER), "api"))

import bonus_rooster as bonus
from bonus_rooster import (
    BONUSWEEK,
    GESCOORDE_RONDES,
    MAX_BONUS,
    PUNTEN_PER_PLEK,
    STANDAARD_STARTSTACK,
    bonus_hele_klas,
    bonus_per_student,
    klassement,
    punten_voor_plek,
    puntentabel,
    puntenverdeling,
    winst_per_bot,
)

geslaagd = 0


def check(voorwaarde, omschrijving):
    global geslaagd
    assert voorwaarde, f"GEZAKT: {omschrijving}"
    geslaagd += 1
    print(f"  ok  {omschrijving}")


# ---------------------------------------------------------------------------
print("Het schema zelf")
check(PUNTEN_PER_PLEK == [0.5, 0.4, 0.3, 0.2, 0.1], "de ladder is 0,5 / 0,4 / 0,3 / 0,2 / 0,1")
check(len(GESCOORDE_RONDES) == 2, "er zijn twee toernooien die punten opleveren")
check(
    abs(len(GESCOORDE_RONDES) * PUNTEN_PER_PLEK[0] - MAX_BONUS) < 1e-9,
    "twee keer de eerste plek is precies het maximum van 1,0",
)
check(punten_voor_plek(1) == 0.5, "plek 1 levert 0,5 op")
check(punten_voor_plek(2) == 0.4, "plek 2 levert 0,4 op")
check(punten_voor_plek(3) == 0.3, "plek 3 levert 0,3 op")
check(punten_voor_plek(len(PUNTEN_PER_PLEK) + 1) == 0.0, "de eerste plek buiten de tabel levert niets op")
check(punten_voor_plek(44) == 0.0, "en onderaan het veld ook niet")
check(len(puntentabel()) == len(PUNTEN_PER_PLEK), "de tabel voor studenten dekt de hele ladder")

# De startstack staat los in bonus_rooster zodat dat bestand geen pypokerengine
# hoeft te importeren; hier controleren we dat de twee niet uit elkaar lopen.
from poker_adapter import STANDAARD_INITIAL_STACK

check(
    STANDAARD_STARTSTACK == STANDAARD_INITIAL_STACK,
    "de startstack in bonus_rooster is gelijk aan die in poker_adapter",
)

# ---------------------------------------------------------------------------
print("\nRanken op winst, niet op eindstand")
# Ronde 1: iedereen begint op 1000, dus winst en eindstand geven dezelfde orde.
ronde1 = {
    "eindstand_per_bot": {"anna": 1400, "bram": 1100, "cem": 900, "dana": 600},
    "namen_deelnemers": ["anna", "bram", "cem", "dana"],
}
check(
    winst_per_bot(ronde1) == {"anna": 400, "bram": 100, "cem": -100, "dana": -400},
    "zonder startstacks wordt er vanaf de standaardstack gerekend",
)
check(klassement(ronde1) == ["anna", "bram", "cem", "dana"], "het klassement van ronde 1 staat op winst")

# Ronde 2: dana speelt het beste toernooi, maar staat door de carry-over nog
# niet bovenaan in absolute chips. Op winst hoort ze eerste te zijn.
ronde2 = {
    "eindstand_per_bot": {"anna": 2500, "bram": 2200, "cem": 1800, "dana": 2100},
    "startstacks": {"anna": 2400, "bram": 2100, "cem": 1900, "dana": 1600},
    "namen_deelnemers": ["anna", "bram", "cem", "dana"],
}
check(
    winst_per_bot(ronde2) == {"anna": 100, "bram": 100, "cem": -100, "dana": 500},
    "met startstacks wordt de winst van dit toernooi berekend",
)
check(klassement(ronde2)[0] == "dana", "wie het meest wint in ronde 2 staat daar eerste")
check(
    sorted(ronde2["eindstand_per_bot"], key=lambda n: -ronde2["eindstand_per_bot"][n])[0] == "anna",
    "op absolute eindstand zou anna eerste zijn — dat is precies de dubbeltelling die we vermijden",
)

oefenbot = {
    "eindstand_per_bot": {"anna": 1400, "oefenbot_tight": 9999},
    "namen_deelnemers": ["anna"],
}
check(klassement(oefenbot) == ["anna"], "oefenbots tellen niet mee in het klassement")

# ---------------------------------------------------------------------------
print("\nVier studenten door beide toernooien")
toernooien = {
    str(BONUSWEEK): ronde1,
    f"{BONUSWEEK}_ronde2": ronde2,
}
submissions = {str(BONUSWEEK): {naam: [{"geldig": True}] for naam in ["anna", "bram", "cem", "dana", "eva"]}}
resultaten = {r["student_id"]: r for r in bonus_hele_klas(submissions, toernooien.get)}

for r in bonus_hele_klas(submissions, toernooien.get):
    regels = "  |  ".join(f"{p['toernooi']}: {p['uitleg']} → {p['punten']}" for p in r["per_ronde"])
    print(f"    {r['student_id']:6} {r['bonus']:.1f}   {regels}")

check(resultaten["anna"]["bonus"] == 0.5 + 0.35, "anna: eerste (0,5), daarna gedeeld tweede (0,35)")
check(resultaten["dana"]["bonus"] == 0.2 + 0.5, "dana: vierde in ronde 1 (0,2) maar eerste in ronde 2 (0,5)")
check(
    resultaten["anna"]["per_ronde"][1]["punten"] == resultaten["bram"]["per_ronde"][1]["punten"],
    "anna en bram wonnen exact evenveel en krijgen dus exact hetzelfde",
)
check(
    "gedeeld met 1" in resultaten["anna"]["per_ronde"][1]["uitleg"],
    "en dat staat er ook bij",
)
check(
    resultaten["eva"]["bonus"] == 0.0,
    "eva leverde in maar speelde niet mee: 0,0, en ze staat wel in het overzicht",
)
check(
    all(p["punten"] == 0.0 for p in resultaten["eva"]["per_ronde"]),
    "en bij eva staat per toernooi 0,0 en niet null",
)
check(
    "niet meegespeeld" in resultaten["eva"]["per_ronde"][0]["uitleg"],
    "met de reden erbij, zodat de docent ziet waarom",
)
check(
    all(r["bonus"] <= MAX_BONUS + 1e-9 for r in resultaten.values()),
    "niemand komt boven de 1,0 uit",
)

# ---------------------------------------------------------------------------
print("\nGelijke standen worden gedeeld")
gelijk = {
    "eindstand_per_bot": {"a": 1500, "b": 1500, "c": 1500, "d": 900},
    "namen_deelnemers": ["a", "b", "c", "d"],
}
verdeling = puntenverdeling(gelijk)
check(
    verdeling["a"]["punten"] == verdeling["b"]["punten"] == verdeling["c"]["punten"],
    "drie bots met dezelfde winst krijgen alle drie hetzelfde",
)
check(
    abs(verdeling["a"]["punten"] - (0.5 + 0.4 + 0.3) / 3) < 1e-9,
    "namelijk het gemiddelde van plek 1, 2 en 3: 0,4",
)
check(verdeling["d"]["plek"] == 4, "de volgende bot staat vierde, niet tweede")
check(
    abs(sum(v["punten"] for v in verdeling.values()) - (0.5 + 0.4 + 0.3 + 0.2)) < 1e-9,
    "delen verandert niets aan het totaal dat wordt uitgekeerd",
)

# ---------------------------------------------------------------------------
print("\nEen toernooi dat nog niet gedraaid is")
alleen_ronde1 = {str(BONUSWEEK): ronde1}
r = bonus_per_student("anna", alleen_ronde1.get)
check(r["per_ronde"][0]["punten"] == 0.5, "het gedraaide toernooi levert gewoon punten op")
check(r["per_ronde"][1]["punten"] is None, "het toernooi dat nog moet komen geeft null, niet 0")
check(r["bonus"] == 0.5, "en telt dus nog niet mee in het totaal")

r = bonus_per_student("anna", {}.get)
check(r["bonus"] == 0.0, "zonder enig toernooi is de bonus 0,0")
check(
    all(p["punten"] is None for p in r["per_ronde"]),
    "met beide toernooien op null in plaats van op nul",
)

# ---------------------------------------------------------------------------
print("\nDe formatieve donderdagronde telt niet mee")
# Een oefenronde staat onder een eigen sleutel. Al zou iemand daarin eerste
# worden, dan levert dat niets op -- en hij mag de echte uitslag niet vervangen.
met_oefenronde = {
    str(BONUSWEEK): ronde1,
    f"{BONUSWEEK}_ronde2_formatief": {
        "eindstand_per_bot": {"eva": 9999, "anna": 1000},
        "namen_deelnemers": ["eva", "anna"],
        "formatief": True,
    },
}
r_eva = bonus_per_student("eva", met_oefenronde.get)
check(r_eva["bonus"] == 0.0, "eerste worden in de oefenronde levert 0,0 op")
check(
    r_eva["per_ronde"][1]["punten"] is None,
    "het vrijdagtoernooi staat nog steeds op 'nog niet gedraaid'",
)
check(
    bonus_per_student("anna", met_oefenronde.get)["bonus"] == 0.5,
    "en de echte woensdaguitslag blijft gewoon staan",
)

# ---------------------------------------------------------------------------
print("\nEen realistisch veld van 44")
groot = {
    "eindstand_per_bot": {f"s{i:02d}": 2000 - i * 25 for i in range(44)},
    "namen_deelnemers": [f"s{i:02d}" for i in range(44)],
}
uitslagen = {str(BONUSWEEK): groot}
verdeeld = [bonus_per_student(f"s{i:02d}", uitslagen.get)["per_ronde"][0]["punten"] for i in range(44)]
check(verdeeld[:5] == [0.5, 0.4, 0.3, 0.2, 0.1], "de top 5 van 44 krijgt de hele ladder")
check(set(verdeeld[5:]) == {0.0}, "de andere 39 krijgen niets voor dit toernooi")
check(
    abs(sum(verdeeld) - sum(PUNTEN_PER_PLEK)) < 1e-9,
    f"er wordt per toernooi precies {sum(PUNTEN_PER_PLEK)} punt uitgekeerd, ongeacht de klasgrootte",
)
check(
    f"buiten de top {len(PUNTEN_PER_PLEK)}" in bonus_per_student("s20", uitslagen.get)["per_ronde"][0]["uitleg"],
    "en wie erbuiten valt leest dat er ook",
)

# ---------------------------------------------------------------------------
print("\nEr worden alleen de rondes gelezen die meetellen")
gelezen = []


def tel_lezen(sleutel):
    gelezen.append(sleutel)
    return toernooien.get(sleutel)


bonus_hele_klas({str(BONUSWEEK): {n: [{"geldig": True}] for n in "abcdefgh"}}, tel_lezen)
check(
    len(gelezen) == len(GESCOORDE_RONDES),
    f"acht studenten leiden tot {len(GESCOORDE_RONDES)} leesacties, niet tot acht keer zoveel",
)
check(
    set(gelezen) == {str(BONUSWEEK), f"{BONUSWEEK}_ronde2"},
    "en dat zijn precies de twee rondes die punten opleveren",
)
check(
    not any("formatief" in s for s in gelezen),
    "de oefenronde wordt niet eens opgehaald",
)

print(f"\n{geslaagd} checks geslaagd.")
