#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speelt een hand uit het toernooi na, straat voor straat.

    python3 scripts/laat_hand_zien.py --ronde 6
    python3 scripts/laat_hand_zien.py --ronde 6 --bot 500123456 --soort verlies

Standaard laat hij de uitschieters zien: de handen waarin de meeste chips van
eigenaar wisselden. Dat zijn de leerzaamste, want daar maakte een beslissing
echt verschil.

WAT HIER GERECONSTRUEERD IS
---------------------------
De uitgebreide log bewaart per bot zijn eigen beslissingen, niet de tafel als
geheel: alle zetten van bot A staan bij elkaar, daarna die van bot B. De
vololgorde binnen een straat staat er dus niet in.

Die is hier teruggerekend uit de pot. Die groeit alleen als er chips in gaan, dus
oplopende pot = latere zet. Bij een gelijke pot legde niemand iets bij; dan komen
de spelers die niets bijlegden eerst en de speler die de pot ophoogde als
laatste. Op alle 23988 straten van ronde 6 loopt de pot na die sortering netjes
op, dus de reconstructie spreekt zichzelf nergens tegen -- maar het blijft een
reconstructie. Twee spelers die achter elkaar folden kunnen in werkelijkheid
andersom hebben gezeten.

Wat er WEL hard in staat: wie wat deed, op welke straat, met welk bord, bij welke
pot en tegen welke inzet. Dat is genoeg om te zien waaróm een hand liep zoals hij
liep.
"""
import argparse
import json
import os
from collections import defaultdict

HIER = os.path.dirname(os.path.abspath(__file__))
STARTSTACK = 1000

STRAAT_VOLGORDE = {"preflop": 0, "flop": 1, "turn": 2, "river": 3}
ZET_CHIPS_IN = {"call", "raise", "grote_raise", "all_in"}

KLEUREN = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}


def kaart(code):
    """'SK' -> 'K♠'. Zonder kleur (oude data) blijft het zoals het is."""
    if len(code) >= 2 and code[0] in KLEUREN:
        return f"{code[1:]}{KLEUREN[code[0]]}"
    return str(code)


def toon_hand(regel):
    kaarten = regel.get("hand_met_kleur") or regel.get("hand") or []
    return " ".join(kaart(k) for k in kaarten)


def zet_volgorde(regel):
    return (STRAAT_VOLGORDE[regel["ronde"]], regel["pot"],
            regel["gekozen"] in ZET_CHIPS_IN)


def leesbaar(regel):
    """Een call zonder iets te callen is een check, en zo hoort het er ook te staan."""
    gekozen = regel["gekozen"]
    if gekozen == "call" and not regel["inzet_om_te_callen"]:
        return "check"
    if gekozen == "call":
        return f"call {regel['inzet_om_te_callen']}"
    return gekozen


def winst_per_hand(hand_log):
    """
    {(bot, simulatie, hand_nummer): winst}

    De stack in hand_log is die aan het EIND van de hand, dus de winst is het
    verschil met de hand ervoor. De eerste hand vergelijkt met de startstack.
    """
    per_bot = defaultdict(dict)
    for rij in hand_log:
        per_bot[(rij["bot_naam"], rij["simulatie"])][rij["hand_nummer"]] = rij["stack"]

    winst = {}
    for (bot, sim), standen in per_bot.items():
        vorige = STARTSTACK
        for nummer in sorted(standen):
            winst[(bot, sim, nummer)] = standen[nummer] - vorige
            vorige = standen[nummer]
    return winst


def laad(week, ronde):
    uitslag_pad = os.path.join(HIER, f"uitslag_week{week}_ronde{ronde}.json")
    log_pad = os.path.join(HIER, f"uitgebreid_week{week}_ronde{ronde}.json")
    for pad in (uitslag_pad, log_pad):
        if not os.path.exists(pad):
            raise SystemExit(
                f"Niet gevonden: {pad}\n"
                f"Draai eerst: python3 scripts/draai_toernooi_lokaal.py "
                f"--week {week} --ronde {ronde}")
    with open(uitslag_pad) as f:
        uitslag = json.load(f)
    with open(log_pad) as f:
        regels = json.load(f)["regels"]
    return uitslag, regels


def speel_na(sleutel, rijen, winst, kort):
    """Eén hand, straat voor straat."""
    simulatie, tafel, nummer = sleutel
    gesorteerd = sorted(rijen, key=zet_volgorde)

    spelers = {}
    for r in gesorteerd:
        spelers.setdefault(r["bot_naam"], r)

    resultaten = {b: winst.get((b, simulatie, nummer), 0) for b in spelers}
    winnaar = max(resultaten, key=resultaten.get)
    pot_eind = max(r["pot"] for r in gesorteerd)

    print(f"\n{'=' * 74}")
    print(f"  Simulatie {simulatie}, tafel {tafel}, hand {nummer}"
          f"   --   pot liep op tot {pot_eind}")
    print(f"{'=' * 74}")
    print("  aan tafel:")
    for bot, eerste in spelers.items():
        teken = "+" if resultaten[bot] > 0 else ""
        print(f"     {kort(bot):<22s} {toon_hand(eerste):<12s} "
              f"stack {eerste['stack']:<5d} {teken}{resultaten[bot]}")

    straat_nu = None
    for r in gesorteerd:
        if r["ronde"] != straat_nu:
            straat_nu = r["ronde"]
            bord = " ".join(kaart(k) for k in r["bord"]) or "(nog geen kaarten)"
            print(f"\n  {straat_nu.upper():<8s} {bord}")
        print(f"     {kort(r['bot_naam']):<22s} {toon_hand(r):<12s} "
              f"pot {r['pot']:<5d} te callen {r['inzet_om_te_callen']:<4d} "
              f"-> {leesbaar(r)}")

    verliezer = min(resultaten, key=resultaten.get)
    print(f"\n  {kort(winnaar)} wint {resultaten[winnaar]}; "
          f"{kort(verliezer)} verliest {-resultaten[verliezer]}.")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde", type=int, default=6)
    p.add_argument("--aantal", type=int, default=3)
    p.add_argument("--soort", choices=["winst", "verlies", "allebei"], default="allebei")
    p.add_argument("--bot", default=None, help="alleen handen waarin deze bot meespeelde")
    p.add_argument("--minimaal", type=int, default=3,
                   help="minimaal zoveel spelers aan zet (standaard 3)")
    args = p.parse_args()

    uitslag, regels = laad(args.week, args.ronde)
    referentie = set(uitslag.get("referentiebots") or []) | set(uitslag.get("testbots") or [])

    def kort(naam):
        """Studentnummers afkorten; referentiebots houden hun naam."""
        return naam if naam in referentie else f"student ...{naam[-4:]}"

    winst = winst_per_hand(uitslag["hand_log"])

    per_hand = defaultdict(list)
    for r in regels:
        per_hand[(r["simulatie"], r["tafel"], r["hand_nummer"])].append(r)

    kandidaten = []
    for sleutel, rijen in per_hand.items():
        simulatie, _, nummer = sleutel
        namen = {r["bot_naam"] for r in rijen}
        if args.bot and args.bot not in namen:
            continue
        # Een hand waarin maar een speler aan zet kwam is geen hand om na te
        # spelen: iedereen foldde naar de blinds, en er valt niets te zien.
        if len(namen) < args.minimaal:
            continue
        resultaten = {b: winst.get((b, simulatie, nummer), 0) for b in namen}
        if not resultaten:
            continue
        if args.bot:
            beste = slechtste = resultaten.get(args.bot, 0)
        else:
            beste, slechtste = max(resultaten.values()), min(resultaten.values())
        kandidaten.append({"beste": beste, "slechtste": slechtste,
                           "sleutel": sleutel, "rijen": rijen})

    if not kandidaten:
        raise SystemExit("Geen handen gevonden die aan de filters voldoen.")

    print(f"Week {args.week}, ronde {args.ronde} -- {len(per_hand)} handen in de log")
    if args.bot:
        print(f"Alleen handen van {kort(args.bot)}")

    gekozen = []
    if args.soort in ("winst", "allebei"):
        op_winst = sorted(kandidaten, key=lambda k: -k["beste"])[:args.aantal]
        gekozen += [("De grootste potten", k) for k in op_winst]
    if args.soort in ("verlies", "allebei"):
        # Het grootste VERLIES van een speler, niet de grootste winst van de
        # tafel. Dat zijn andere handen: hier gaat het om wie betaalde.
        op_verlies = sorted(kandidaten, key=lambda k: k["slechtste"])[:args.aantal]
        gekozen += [("De duurste handen", k) for k in op_verlies]

    vorig_kopje = None
    getoond = set()
    for kopje, k in gekozen:
        if kopje != vorig_kopje:
            print(f"\n\n{'#' * 74}\n#  {kopje}\n{'#' * 74}")
            vorig_kopje = kopje
        if k["sleutel"] in getoond:
            print(f"\n  (simulatie {k['sleutel'][0]}, tafel {k['sleutel'][1]}, "
                  f"hand {k['sleutel'][2]} stond hierboven al)")
            continue
        getoond.add(k["sleutel"])
        speel_na(k["sleutel"], k["rijen"], winst, kort)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
