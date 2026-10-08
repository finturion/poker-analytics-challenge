"""
Hoe zouden de vier simpele bots het gedaan hebben in het week 3-toernooi?

De 27 échte inzendingen van week 3 staan in de database op de server en niet in
deze repo, dus dit is een RECONSTRUCTIE en geen herhaling. Wat er van dat
toernooi gedocumenteerd is, staat in api/toernooi_runner.py bij TESTBOTS:

    "in zijn eerste toernooi (week 3, 2026-2027) werd hij eerste van 27, tien
     chips voor nummer twee, in een veld dat 92,2% van alle beslissingen foldde
     en waarvan negen bots 99% of meer foldden"

Dat zijn vier getallen om op te mikken, en één uitkomst om tegen te ijken. Het
veld hieronder is dus niet verzonnen naar smaak: de drempels zijn zo gezet dat
het gemeten foldpercentage en het aantal ultra-tight bots kloppen, en daarna
wordt gecontroleerd of Testbot_CalltAlles het inderdaad wint. Lukt die
controle niet, dan is de reconstructie niet goed genoeg en zegt het script dat.

Week 3-regels: de veldbots hebben GEEN strategie in hun handtekening, en krijgen
daarmee ook geen "grote_raise" van de engine -- precies zoals in week 3. De vier
simpele bots hebben strategie wél in hun handtekening en houden die mogelijkheid
dus; dat staat in het verslag als voorbehoud.

Draaien:  python3 scripts/simpele_bots_in_week3.py
"""
import collections
import json
import os
import statistics
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(PROJECT, "api"))
sys.path.insert(0, os.path.join(PROJECT, "mijn_bots"))

from poker_adapter import speel_toernooi

import simpel_bluffer
import simpel_caller
import simpel_goeiehanden
import simpel_muntje

# De winkanstabel kwam uit bot_handsterkte, maar die is in oktober 2026
# herschreven: hij roept nu schat_winkans aan in plaats van een vaste tabel te
# raadplegen, en WINKANS bestaat daar niet meer. Het veld hieronder heeft wél een
# vaste tabel nodig -- de drempels zijn erop uitgerekend -- dus die komt nu uit
# een referentiebot, waar hij ongewijzigd staat.
from referentiebots import bot_allrounder

WINKANS = bot_allrounder.WINKANS
hand_sleutel = bot_allrounder.hand_sleutel

SEEDS = [51, 52, 53, 54, 55, 56]
N_SIMULATIES = 20
N_HANDEN = 50

# De doelen uit de documentatie van het echte toernooi.
DOEL_FOLDAANDEEL = 92.2
DOEL_AANTAL_ULTRATIGHT = 9
ULTRATIGHT_GRENS = 99.0

# Het veld: 26 inzendingen in Bot v2-vorm, elk met één drempel. De verdeling is
# niet naar smaak gekozen maar uitgerekend. Per drempel is bekend welk aandeel
# van de 1326 mogelijke starthanden erboven ligt -- gewogen met het echte aantal
# combinaties, want een paar komt in 6 vormen voor en een ongepaarde hand in 16:
#
#   drempel 82 -> speelt 0,9% van de handen  (alleen AA en KK)   -> 99,1% fold
#   drempel 70 -> speelt 2,7%                                    -> 97,3% fold
#   drempel 62 -> speelt 10,1%                                   -> 89,9% fold
#   drempel 57 -> speelt 23,8%                                   -> 76,2% fold
#
# Deze mix komt preflop uit op gemiddeld 93,0% fold, en levert precies de negen
# bots op die 99% of meer folden. Dat 93 en niet 92,2 is, is geen slordigheid:
# de 92,2 uit het echte toernooi telt ÁLLE beslissingen, ook die halverwege een
# hand, en daar zitten per definitie minder folds tussen -- wie foldt, neemt
# daarna geen beslissingen meer. Het hand-log hier bewaart alleen de eerste
# actie per hand, en dat getal hoort dus iets hoger te liggen.
VELD_DREMPELS = [82] * 10 + [70] * 10 + [62] * 3 + [57] * 3

SIMPELE_BOTS = {
    "de bluffer": simpel_bluffer,
    "de caller": simpel_caller,
    "alleen goeie handen": simpel_goeiehanden,
    "het muntje": simpel_muntje,
}


def maak_veldbot(drempel):
    """
    Een inzending zoals week 3 ze oplevert: opzoektabel, één drempel, pot odds.

    Bewust ZONDER strategie en bluf_kans in de handtekening. Dat is niet
    cosmetisch: poker_adapter gate't "grote_raise" op het woord `strategie` in
    je handtekening, dus een week 3-bot kan die actie helemaal niet gebruiken.
    """
    def kies_actie(hand, stack, ronde="preflop", pot=0, inzet_om_te_callen=0):
        winkans = WINKANS.get(hand_sleutel(hand), 40.0)
        inzet = inzet_om_te_callen or 0
        if stack < 150:
            return "all_in" if winkans >= drempel else "fold"
        if winkans < drempel:
            return "fold"
        if inzet == 0:
            return "raise" if winkans >= drempel + 6 else "check"
        vereist = inzet / ((pot or 0) + inzet) * 100
        if winkans < vereist + 8:
            return "fold"
        return "raise" if winkans >= drempel + 6 else "call"
    return kies_actie


def bouw_veld(met_simpele_bots):
    veld = {}
    for i, drempel in enumerate(VELD_DREMPELS):
        veld[f"inzending{i:02d}_d{drempel}"] = {"kies_actie": maak_veldbot(drempel),
                                                "strategie": None, "bluf_kans": None}
    veld["Testbot_CalltAlles"] = {"kies_actie": lambda hand, **_: "call",
                                  "strategie": None, "bluf_kans": None}
    if met_simpele_bots:
        for naam, module in SIMPELE_BOTS.items():
            veld[naam] = {"kies_actie": module.kies_actie,
                          "strategie": "balanced", "bluf_kans": 0.25}
    return veld


def draai(veld):
    """Alle seeds, en per (seed, simulatie, tafel, bot) de eindstack."""
    standen = collections.defaultdict(list)
    foldtellers = collections.Counter()
    beslissingen = collections.Counter()
    for seed in SEEDS:
        uitslag = speel_toernooi(veld, n_simulaties=N_SIMULATIES, n_handen=N_HANDEN, seed=seed)
        laatste = {}
        for rij in uitslag["hand_log"]:
            sleutel = (rij["bot_naam"], seed, rij["simulatie"], rij["tafel"])
            if sleutel not in laatste or rij["hand_nummer"] > laatste[sleutel]["hand_nummer"]:
                laatste[sleutel] = rij
            # actie is None als de bot deze hand niet aan de beurt kwam (of al
            # uitgespeeld was). Dat is geen beslissing en hoort dus in geen van
            # beide tellers -- meerekenen als fold maakte het foldpercentage
            # eerst 13 punten te laag.
            if rij["actie"] is None:
                continue
            beslissingen[rij["bot_naam"]] += 1
            if rij["actie"] == "fold":
                foldtellers[rij["bot_naam"]] += 1
        for (naam, _s, _sim, _t), rij in laatste.items():
            standen[naam].append(rij["stack"])
    return standen, foldtellers, beslissingen


def foldaandeel(foldtellers, beslissingen):
    totaal = sum(beslissingen.values())
    return 100 * sum(foldtellers.values()) / totaal if totaal else 0.0


IJKING = {}


def ijk_de_reconstructie():
    """Klopt het veld met de vier gedocumenteerde getallen?"""
    print(f"{'=' * 78}\nIJKING: klopt dit veld met het echte week 3-toernooi?\n{'=' * 78}")
    veld = bouw_veld(met_simpele_bots=False)
    standen, folds, beslissingen = draai(veld)

    aandeel = foldaandeel(folds, beslissingen)
    ultratight = sum(1 for naam in veld
                     if beslissingen[naam] and 100 * folds[naam] / beslissingen[naam] >= ULTRATIGHT_GRENS)
    ranglijst = sorted(standen, key=lambda n: -statistics.mean(standen[n]))
    plek_testbot = ranglijst.index("Testbot_CalltAlles") + 1
    tweede = statistics.mean(standen[ranglijst[1]])
    eerste = statistics.mean(standen[ranglijst[0]])

    print(f"  {'':<34}{'echt':>10}{'reconstructie':>16}")
    print(f"  {'aantal bots':<34}{27:>10}{len(veld):>16}")
    print(f"  {'foldaandeel (zie toelichting)':<34}{DOEL_FOLDAANDEEL:>9.1f}%{aandeel:>15.1f}%")
    print(f"  {'bots die 99% of meer folden':<34}{DOEL_AANTAL_ULTRATIGHT:>10}{ultratight:>16}")
    print(f"  {'plek van Testbot_CalltAlles':<34}{1:>10}{plek_testbot:>16}")
    print(f"  {'voorsprong op nummer twee (chips)':<34}{10:>10}{eerste - tweede:>16.0f}")

    IJKING["foldaandeel_27"] = round(aandeel, 1)
    IJKING["ultratight"] = ultratight
    goed = (abs(aandeel - DOEL_FOLDAANDEEL) <= 3.0
            and abs(ultratight - DOEL_AANTAL_ULTRATIGHT) <= 2
            and plek_testbot <= 3)
    if goed:
        print("\n  Het veld gedraagt zich als het echte: even tight, even veel ultra-tight")
        print("  bots, en de bot die alles callt wint het. Op die drie punten mag je de")
        print("  uitslag hieronder vertrouwen.")
    else:
        print("\n  LET OP: dit veld wijkt af van het echte toernooi. Lees de uitslag")
        print("  hieronder met dat voorbehoud.")
    print(f"\n  Wat NIET klopt: in het echte toernooi won de testbot met tien chips, hier")
    print(f"  met {eerste - tweede:.0f}. Het echte veld had dus iemand die bijna even goed was, en die")
    print("  zit hier niet in. De volgorde onderaan is daardoor betrouwbaarder dan de")
    print("  precieze afstanden bovenaan.")
    return goed


def rapporteer():
    print(f"\n{'=' * 78}\nDE VIER SIMPELE BOTS IN DAT VELD\n{'=' * 78}")
    veld = bouw_veld(met_simpele_bots=True)
    standen, folds, beslissingen = draai(veld)
    ranglijst = sorted(standen, key=lambda n: -statistics.mean(standen[n]))

    print(f"  {len(veld)} bots, {len(SEEDS)} seeds x {N_SIMULATIES} simulaties x {N_HANDEN} handen\n")
    print(f"  {'plek':>5}  {'bot':<24}{'gem. eindstack':>16}{'onzekerheid':>13}{'foldt':>8}")
    for plek, naam in enumerate(ranglijst, start=1):
        waarden = standen[naam]
        fout = statistics.stdev(waarden) / len(waarden) ** 0.5 if len(waarden) > 1 else 0.0
        fold = 100 * folds[naam] / beslissingen[naam] if beslissingen[naam] else 0.0
        opvallend = naam in SIMPELE_BOTS or naam == "Testbot_CalltAlles"
        if opvallend or plek <= 3:
            merk = "  <--" if naam in SIMPELE_BOTS else ""
            print(f"  {plek:>5}  {naam:<24}{statistics.mean(waarden):>16.0f}"
                  f"{fout:>13.0f}{fold:>7.0f}%{merk}")
    print(f"\n  (alleen de simpele bots, de testbot en de top 3 staan hierboven;"
          f" de overige\n   {len(VELD_DREMPELS)} reconstructie-inzendingen zijn weggelaten)")

    # Wegschrijven zodat de dia-plaat deze getallen kan overnemen in plaats van
    # ze over te typen. Een dia die niet meer klopt met het script eronder is
    # erger dan geen dia.
    uitvoer = {
        "veldgrootte": len(veld),
        "foldaandeel_veld": round(foldaandeel(folds, beslissingen), 1),
        "foldaandeel_27": IJKING.get("foldaandeel_27"),
        "ultratight": IJKING.get("ultratight"),
        "regels": [
            {"plek": plek, "naam": naam,
             "stack": round(statistics.mean(standen[naam])),
             "fout": round(statistics.stdev(standen[naam]) / len(standen[naam]) ** 0.5),
             "fold": round(100 * folds[naam] / beslissingen[naam]) if beslissingen[naam] else 0,
             "simpel": naam in SIMPELE_BOTS}
            for plek, naam in enumerate(ranglijst, start=1)
        ],
    }
    pad = os.path.join(PROJECT, "powerpoints", "plots_week5", "week3_uitslag.json")
    os.makedirs(os.path.dirname(pad), exist_ok=True)
    with open(pad, "w") as f:
        json.dump(uitvoer, f, indent=2)
    print(f"  uitslag weggeschreven naar plots_week5/week3_uitslag.json")
    return ranglijst, standen


def main():
    ijk_de_reconstructie()
    rapporteer()
    return 0


if __name__ == "__main__":
    sys.exit(main())
