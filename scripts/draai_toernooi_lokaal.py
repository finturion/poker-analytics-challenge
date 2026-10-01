#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Haalt de ingeleverde bots op en draait het toernooi op je eigen machine.

    python3 scripts/draai_toernooi_lokaal.py --week 5 --ronde 1

Vraagt om je docent-token (wordt niet getoond en niet bewaard), schrijft de
bots naar scripts/bots_week{N}/ en de uitslag naar scripts/uitslag_week{N}.json.

WAAROM LOKAAL
-------------
Sinds Werkcollege 7 rekenen bots hun winkans live uit met schat_winkans, en de
bonusweek draait twintig simulaties. Gemeten kost één beslissing 16 tot 19 ms,
en een veld van dertig bots komt daarmee op negen tot veertien minuten -- op een
laptop. Render is trager, en een HTTP-verbinding houdt dat niet vol: je krijgt
een timeout terwijl de server nog rekent.

Lokaal heb je die grens niet. En omdat de seed van het toernooi vastligt op
week * 10 + ronde is dit geen benadering: met dezelfde bots en dezelfde
instellingen komt er exact dezelfde uitslag uit als de server zou berekenen.

DE UITSLAG NAAR DE STUDENTEN
----------------------------
Met --upload gaat hij na afloop naar de server, onder de normale cache-sleutel.
Studenten zien hem dan via /toernooi/{week} precies zoals een uitslag die de
server zelf heeft gedraaid, en de uitgebreide log komt er in stukken achteraan.
Zonder --upload blijft alles lokaal; voor het deck is dat genoeg.

Elke ronde begint schoon op 1000, ook in de bonusweek -- net als op de server.
Twee rondes van dezelfde week zijn daardoor onderling te vergelijken.
"""
import argparse
import getpass
import json
import os
import sys
import time

HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(REPO, "api"))

import requests

from poker_adapter import STANDAARD_N_HANDEN, speel_toernooi
from toernooi_runner import TESTBOTS, n_simulaties_voor, referentiebots_voor
from winkans import schat_winkans

API_URL = "https://poker-analytics-api.onrender.com"


def laad_kies_actie(code):
    """
    Zelfde aanpak als toernooi_runner._laad_kies_actie: schat_winkans staat
    klaar in de naamruimte, zodat een bot hem zonder import kan aanroepen.
    """
    ruimte = {"schat_winkans": schat_winkans}
    try:
        exec(code, ruimte)
    except Exception as fout:
        return None, f"{type(fout).__name__}: {fout}"
    functie = ruimte.get("kies_actie")
    return (functie, None) if callable(functie) else (None, "geen kies_actie() gevonden")



# Eén verzoek met de hele uitgebreide log is tientallen megabytes. Per groepje
# bots blijft elk verzoek rond de paar megabyte, en een bot gaat altijd in zijn
# geheel mee -- de server vervangt hem per bot.
BOTS_PER_VERZOEK = 5



def verstuur_bewaarde_uitslag(args, token):
    """De uitslag die al op schijf staat alsnog versturen."""
    doel = os.path.join(HIER, f"uitslag_week{args.week}.json")
    doel_uitgebreid = os.path.join(HIER, f"uitgebreid_week{args.week}.json")
    if not os.path.exists(doel):
        print(f"Geen bewaarde uitslag gevonden: {doel}")
        print("Draai eerst zonder --alleen-upload.")
        return 1

    with open(doel) as f:
        resultaat = json.load(f)
    uitgebreid = []
    if os.path.exists(doel_uitgebreid):
        with open(doel_uitgebreid) as f:
            uitgebreid = json.load(f).get("regels") or []

    print(f"{len(resultaat['hand_log'])} handregels en {len(uitgebreid)} beslissingen "
          f"uit {os.path.basename(doel)}")
    stuur_naar_server(resultaat, uitgebreid, args.week, args.ronde,
                      token, args.overschrijven)
    return 0


def stuur_naar_server(resultaat, uitgebreid, week, ronde, token, overschrijven):
    """Zet de uitslag en de uitgebreide log op de server, voor de studenten."""
    kop = {"Authorization": f"Bearer {token}"}
    print("\nNaar de server:")

    antwoord = requests.post(
        f"{API_URL}/toernooi/{week}/upload",
        params={"ronde": ronde, "overschrijven": str(overschrijven).lower()},
        json={"resultaat": resultaat}, headers=kop, timeout=300)
    if antwoord.status_code == 409:
        print(f"   GESTOPT: {antwoord.json().get('detail')}")
        print("   Weet je het zeker? Draai hetzelfde commando met --overschrijven.")
        return
    antwoord.raise_for_status()
    uit = antwoord.json()
    print(f"   uitslag geplaatst: {uit['n_bots']} bots, {uit['n_handregels']} handregels")

    per_bot = {}
    for regel in uitgebreid:
        per_bot.setdefault(regel["bot_naam"], []).append(regel)

    namen = sorted(per_bot)
    for i in range(0, len(namen), BOTS_PER_VERZOEK):
        groep = namen[i:i + BOTS_PER_VERZOEK]
        antwoord = requests.post(
            f"{API_URL}/toernooi/{week}/upload/uitgebreid",
            params={"ronde": ronde},
            json={"bots": {n: per_bot[n] for n in groep}}, headers=kop, timeout=300)
        antwoord.raise_for_status()
        uit = antwoord.json()
        print(f"   uitgebreide log: {uit['n_bots_totaal']}/{len(namen)} bots, "
              f"{uit['n_regels_totaal']} regels")

    print(f"   klaar -- studenten zien week {week} ronde {ronde} nu via /toernooi/{week}")


def haal_bots_op(week, token):
    antwoord = requests.get(f"{API_URL}/export/{week}/bots",
                            headers={"Authorization": f"Bearer {token}"}, timeout=90)
    if antwoord.status_code != 200:
        sys.exit(f"Ophalen mislukt ({antwoord.status_code}): "
                 f"{antwoord.json().get('detail', antwoord.text[:200])}")
    return antwoord.json()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde", type=int, default=1)
    p.add_argument("--handen", type=int, default=STANDAARD_N_HANDEN)
    p.add_argument("--upload", action="store_true",
                   help="zet de uitslag na afloop op de server, voor de studenten")
    p.add_argument("--alleen-upload", action="store_true", dest="alleen_upload",
                   help="niets draaien, alleen de al bewaarde uitslag versturen")
    p.add_argument("--overschrijven", action="store_true",
                   help="met --upload: een bestaande ronde echt vervangen")
    p.add_argument("--simulaties", type=int, default=None,
                   help="standaard: wat de server voor deze week gebruikt")
    args = p.parse_args()

    token = os.environ.get("POKER_DOCENT_TOKEN") or getpass.getpass("Docent-token: ")

    if args.alleen_upload:
        # De uitslag staat al op schijf. Dit is het pad voor als het rekenen wél
        # lukte maar het versturen niet -- dan hoef je geen twaalf minuten opnieuw.
        return verstuur_bewaarde_uitslag(args, token)

    inzendingen = haal_bots_op(args.week, token)
    if not args.upload:
        del token

    botmap = os.path.join(HIER, f"bots_week{args.week}")
    os.makedirs(botmap, exist_ok=True)

    bots, overgeslagen = {}, []
    for rij in inzendingen:
        sid = rij["student_id"]
        with open(os.path.join(botmap, f"{sid}.py"), "w") as f:
            f.write(rij["bot_code"])
        if not rij["geldig"]:
            overgeslagen.append((sid, rij.get("foutmelding") or "afgekeurd"))
            continue
        functie, fout = laad_kies_actie(rij["bot_code"])
        if functie is None:
            overgeslagen.append((sid, fout))
            continue
        bots[sid] = {"kies_actie": functie, "strategie": rij.get("strategie"),
                     "bluf_kans": rij.get("bluf_kans")}

    print(f"{len(inzendingen)} inzendingen opgehaald, code staat in {botmap}")
    print(f"{len(bots)} bots doen mee")
    for sid, reden in overgeslagen:
        print(f"   overgeslagen: {sid} — {reden[:90]}")
    if len(bots) < 2:
        sys.exit("Minder dan 2 geldige bots; er valt niets te draaien.")

    namen_deelnemers = sorted(bots)
    referentie = referentiebots_voor(args.week)
    for naam, info in referentie.items():
        bots.setdefault(naam, info)
    for naam, functie in TESTBOTS.items():
        bots.setdefault(naam, {"kies_actie": functie, "strategie": None, "bluf_kans": None})

    n_sim = args.simulaties or n_simulaties_voor(args.week)
    # Elke ronde begint schoon op 1000, net als op de server.
    startstacks = None

    print(f"\n{len(bots)} bots aan tafel (incl. {len(referentie)} referentie- en "
          f"{len(TESTBOTS)} testbots)")
    print(f"{n_sim} simulaties x {args.handen} handen, seed {args.week * 10 + args.ronde}")
    print("Dit duurt even. Reken op tien tot vijftien minuten bij een volle klas.\n")

    begin = time.time()
    uitkomst = speel_toernooi(bots, n_simulaties=n_sim, n_handen=args.handen,
                              seed=args.week * 10 + args.ronde, startstacks=startstacks)
    duur = time.time() - begin

    resultaat = {
        "week": args.week, "vergelijk_met_week": None, "ronde": args.ronde,
        "formatief": False, "n_bots": len(bots),
        "namen_deelnemers": namen_deelnemers, "aangevuld_met_oefenbots": 0,
        "referentiebots": sorted(referentie), "testbots": sorted(TESTBOTS),
        "n_simulaties": n_sim, "startstacks": startstacks,
        "hand_log": uitkomst["hand_log"],
        "eindstand_per_bot": uitkomst["eindstand_per_bot"],
    }
    doel = os.path.join(HIER, f"uitslag_week{args.week}.json")
    with open(doel, "w") as f:
        json.dump(resultaat, f)

    # De uitgebreide log gaat naar een eigen bestand. Eén regel per beslissing in
    # plaats van één per hand, dus ongeveer 3,5 keer zoveel -- in uitslag_week*.json
    # erbij zou analyse_toernooi.py elke keer tientallen megabytes moeten inlezen
    # voor data die het niet gebruikt.
    uitgebreid = uitkomst.get("uitgebreid_hand_log") or []
    doel_uitgebreid = os.path.join(HIER, f"uitgebreid_week{args.week}.json")
    with open(doel_uitgebreid, "w") as f:
        json.dump({"week": args.week, "ronde": args.ronde, "regels": uitgebreid}, f)

    print(f"Klaar in {duur / 60:.1f} minuten. {len(resultaat['hand_log'])} logregels -> {doel}")
    print(f"{len(uitgebreid)} beslissingen (met bord en ronde) -> {doel_uitgebreid}")

    if args.upload:
        stuur_naar_server(resultaat, uitgebreid, args.week, args.ronde,
                          token, args.overschrijven)
        del token

    print("\nNu de analyse en het deck:")
    print(f"   python3 scripts/analyse_toernooi.py {doel}")
    print("   python3 powerpoints/maak_presentatie_wc8.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
