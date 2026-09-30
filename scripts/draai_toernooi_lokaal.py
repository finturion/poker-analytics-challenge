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

WAT DIT SCRIPT NIET DOET
------------------------
De uitslag terugzetten in de API. Studenten halen hun toernooi op via
/toernooi/5, en die leest de servercache. Wil je dat zij dezelfde uitslag zien,
dan moet de server hem alsnog zelf draaien -- of er moet een upload-endpoint
komen. Voor het werkcollege en het deck heb je genoeg aan het JSON-bestand.

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
    p.add_argument("--simulaties", type=int, default=None,
                   help="standaard: wat de server voor deze week gebruikt")
    args = p.parse_args()

    token = os.environ.get("POKER_DOCENT_TOKEN") or getpass.getpass("Docent-token: ")
    inzendingen = haal_bots_op(args.week, token)
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
    print("\nNu de analyse en het deck:")
    print(f"   python3 scripts/analyse_toernooi.py {doel}")
    print("   python3 powerpoints/maak_presentatie_wc8.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
