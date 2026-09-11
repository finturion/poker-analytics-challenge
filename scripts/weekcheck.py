"""
De weekbriefing: wat geef je deze week, en is het materiaal klaar?

Eerst wat je gaat bespreken (werkcolleges met hun delen en minuten, de
deadlines, de DataCamp-courses), daarna wat er nog niet klopt. De checks zijn
zo gekozen dat ze fouten vinden die je op maandagochtend niet meer wilt
ontdekken: een notebook dat een bestand opent dat niet bestaat, een
Brightspace-pagina die niet meer bij het script past, een API-endpoint dat
lokaal wel bestaat maar op de server niet.

    python3 scripts/weekcheck.py            # de week waar vandaag in valt
    python3 scripts/weekcheck.py --week 5   # een andere week
    python3 scripts/weekcheck.py --offline  # zonder de server te bevragen
    python3 scripts/weekcheck.py --kort     # alleen wat er nog moet

Eigen punten zet je in docs/weekchecklist.md; alles wat daar nog als "- [ ]"
staat komt hieronder terug.

Afsluitcode 0 als alles klopt, 1 als er iets openstaat. Zo kan een routine
hierop afgaan.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
os.chdir(WORTEL)
sys.path.insert(0, "api")
sys.path.insert(0, "scripts")

import datacamp_rooster
from genereer_brightspace_paginas import (
    ANDERE_NAAM_OP_BRIGHTSPACE,
    API,
    WEKEN,
    datum_nl,
    weekdatums,
    weekpagina,
    overzichtspagina,
)

CHECKLIST = "docs/weekchecklist.md"
TESTS = ["test_bonus_rooster.py", "test_toernooi_rondes.py",
         "test_referentiebots.py", "test_datacamp_rooster.py"]

OK, LET_OP, FOUT, OVERGESLAGEN = "ok", "!?", "!!", "--"
problemen = []


def meld(status, regel, uitleg=""):
    """
    Print de uitkomst, en onthoud hem als er iets aan te doen valt.

    OVERGESLAGEN is er apart van LET_OP: een check die niet kón draaien (geen
    netwerk, --offline) is geen openstaand punt. Zet je hem wel in de lijst, dan
    staat er elke offline run een regel "overgeslagen" bij het werk dat je nog
    moet doen, en daar raakt de lijst van los.
    """
    print(f"  [{status}] {regel}")
    if uitleg:
        for r in uitleg.split("\n"):
            print(f"         {r}")
    if status in (LET_OP, FOUT):
        problemen.append((status, regel, uitleg))


def kop(tekst):
    print(f"\n{tekst}\n{'-' * len(tekst)}")


# ---------------------------------------------------------------------------
# Welke week is het?
# ---------------------------------------------------------------------------

def huidige_week(vandaag=None):
    """
    De onderwijsweek waar vandaag in valt. In het weekend kijk je vooruit: op
    zaterdag en zondag krijg je de week die maandag begint, want dat is de week
    waarvoor je nog iets kunt klaarzetten.
    """
    vandaag = vandaag or date.today()
    for w in WEKEN:
        ma, vr = weekdatums(w["week"])
        if ma <= vandaag <= vr:
            return w["week"]
        if vr < vandaag < ma + timedelta(days=7):   # het weekend erna
            return w["week"] + 1
    eerste_ma, _ = weekdatums(WEKEN[0]["week"])
    if vandaag < eerste_ma:
        return WEKEN[0]["week"]
    return WEKEN[-1]["week"]


def week_data(nummer):
    for w in WEKEN:
        if w["week"] == nummer:
            return w
    return None


# ---------------------------------------------------------------------------
# Notebooks lezen
# ---------------------------------------------------------------------------

def lees_notebook(pad):
    with open(pad, encoding="utf-8") as f:
        return json.load(f)


def markdown_van(nb):
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "markdown")


def code_van(nb):
    return "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")


# De negen notebooks zijn niet in dezelfde stijl geschreven: WC4 gebruikt
# "Deel 1 — ... (33 min)", WC3 "Ronde 0 — Opfrissen" zonder minuten, WC9 begint
# met "Voorwerk — ... (± 40 min)". Een parser die alleen "Deel" kent telt bij
# drie van de negen nul minuten en meldt dan vrolijk dat alles klopt.
# Koppen die geen lesonderdeel zijn maar inleiding of overzicht.
GEEN_ONDERDEEL = re.compile(r"^(Tijdsindicatie|Wat leer je|Waar gaat dit over|Wat is Visual Hierarchy)", re.I)
# Onderdelen die de student thuis doet; die tellen niet mee in de werkcollegetijd.
IS_HUISWERK = re.compile(r"huiswerk|thuis|^Voorwerk|^\*\*Voorwerk|^Totaal", re.I)


def delen_van(nb):
    """
    Elk lesonderdeel met zijn minuten en of het huiswerk is.

    Geeft (titel, minuten of None, huiswerk) terug. Niet elke kop noemt een
    tijd -- "Deel 7 — Bot v2 afmaken (4 tot 8 uur)" en "Reflectievragen" niet --
    en dat is precies wat de vergelijking hieronder in de gaten moet houden.
    """
    delen = []
    for kop_regel in re.findall(r"^##\s+(.+)$", markdown_van(nb), re.M):
        if GEEN_ONDERDEEL.match(kop_regel.strip()):
            continue
        minuten = re.search(r"±?\s*(\d+)\s*min", kop_regel)
        titel = re.sub(r"\s*\(.*?\)\s*$", "", kop_regel).strip()
        delen.append((titel, int(minuten.group(1)) if minuten else None,
                      bool(IS_HUISWERK.search(kop_regel))))
    return delen


def tijdstabel_totaal(nb):
    """
    De minuten uit de tabel onder "Tijdsindicatie". Alle negen notebooks
    gebruiken daar dezelfde vorm -- | Moment | Duur | Onderdeel | -- met de
    duur in de tweede kolom, soms vetgedrukt en soms leeg bij een tussenkop.

    Geeft None als er geen tabel staat, zodat "geen tabel" te onderscheiden is
    van "een tabel die op nul uitkomt".
    """
    tekst = markdown_van(nb)
    begin = tekst.find("Tijdsindicatie")
    if begin == -1:
        return None
    # Tot de eerstvolgende kop na de tabel.
    volgende = re.search(r"^#{1,3}\s", tekst[begin + 20:], re.M)
    blok = tekst[begin:begin + 20 + (volgende.start() if volgende else len(tekst))]

    rijen = []
    for regel in blok.split("\n"):
        kolommen = [k.strip() for k in regel.split("|")]
        if len(kolommen) < 4:
            continue
        m = re.fullmatch(r"\**\s*(\d+)\s*min\s*\**", kolommen[2])
        if m:
            rijen.append((int(m.group(1)), bool(IS_HUISWERK.search(kolommen[1]))))
    return rijen or None


def endpoints_van(nb):
    """Welke API-paden roept dit notebook aan? Als pad-patroon, niet als URL."""
    paden = set()
    for ruw in re.findall(r'f?"\{API_URL\}(/[^"]*)"', code_van(nb)):
        pad = ruw.split("?")[0]
        pad = re.sub(r"\{[^}]+\}", "{x}", pad)
        # /toernooi/5 -> /toernooi/{x}: de server beschrijft zijn routes zo.
        pad = re.sub(r"/\d+", "/{x}", pad)
        paden.add(pad)
    return paden


def lokale_bestanden_van(nb):
    """Bestanden die het notebook opent of importeert, relatief aan notebooks/."""
    code = code_van(nb)
    nodig = set(re.findall(r'["\']([\w./-]+\.(?:csv|geojson|json|txt))["\']', code))
    for naam in re.findall(r"^\s*(?:from|import)\s+(_\w+)", code, re.M):
        nodig.add(f"{naam}.py")
    return nodig


# ---------------------------------------------------------------------------
# De briefing
# ---------------------------------------------------------------------------

def briefing(week):
    w = week_data(week)
    ma, vr = weekdatums(week)
    print(f"\nWEEKBRIEFING — week {week}: {w['titel']}")
    print(f"{datum_nl(ma)} t/m {datum_nl(vr)} 2026")
    print(f"\n{w['lead']}")

    kop("Wat je geeft")
    for bestand, label, _ in w["werkcolleges"]:
        pad = os.path.join("notebooks", bestand)
        if not os.path.exists(pad):
            print(f"  {label}  -- NOTEBOOK ONTBREEKT")
            continue
        nb = lees_notebook(pad)
        delen = delen_van(nb)
        les = sum(m for _, m, hw in delen if m and not hw)
        hw_min = sum(m for _, m, hw in delen if m and hw)
        staart = f" + {hw_min} min huiswerk" if hw_min else ""
        print(f"\n  {label}   ({les} min werkcollege{staart})")
        for titel, minuten, huiswerk in delen:
            merk = " (huiswerk)" if huiswerk else ""
            print(f"      {str(minuten) + ' min' if minuten else '     ':>8}  {titel}{merk}")

    if w["deadlines"]:
        kop("Deadlines deze week")
        for wanneer, wat in w["deadlines"]:
            schoon = re.sub(r"<[^>]+>", "", wat)
            print(f"  {wanneer:<18} {schoon}")

    courses = [c for c in datacamp_rooster.ROOSTER if c["week"] == week]
    if courses:
        kop("DataCamp deze week")
        for c in courses:
            deadline = date.fromisoformat(c["deadline"])
            print(f"  {c['code']:<7} {c['titel']}  (vóór {datum_nl(deadline)})")

    if w["let_op"]:
        kop("Let op")
        print("  " + re.sub(r"<[^>]+>", "", w["let_op"]))


# ---------------------------------------------------------------------------
# De checks
# ---------------------------------------------------------------------------

def check_notebooks(week):
    w = week_data(week)
    kop("Notebooks en hun bestanden")
    for bestand, label, _ in w["werkcolleges"]:
        pad = os.path.join("notebooks", bestand)
        if not os.path.exists(pad):
            meld(FOUT, f"{bestand} bestaat niet")
            continue
        try:
            nb = lees_notebook(pad)
        except json.JSONDecodeError as e:
            meld(FOUT, f"{bestand} is geen geldige JSON", str(e))
            continue

        ontbreekt = [n for n in sorted(lokale_bestanden_van(nb))
                     if not os.path.exists(os.path.join("notebooks", n))]
        if ontbreekt:
            meld(FOUT, f"{bestand} opent bestanden die er niet zijn",
                 "\n".join(ontbreekt))
        else:
            meld(OK, f"{bestand}: alle bestanden die het opent bestaan")

        leeg = [i for i, c in enumerate(nb["cells"]) if not "".join(c["source"]).strip()]
        if leeg:
            meld(LET_OP, f"{bestand} heeft {len(leeg)} lege cel(len)", f"cel {leeg}")

        uitvoer = [i for i, c in enumerate(nb["cells"])
                   if c["cell_type"] == "code" and c.get("outputs")]
        if uitvoer:
            meld(LET_OP, f"{bestand} heeft nog uitvoer in {len(uitvoer)} cel(len)",
                 "Studenten zien dan de antwoorden al staan.")


def check_tijden(week):
    """De minuten in de Deel-koppen moeten optellen tot wat de tijdstabel zegt."""
    w = week_data(week)
    kop("Tijdsindicatie")
    for bestand, label, _ in w["werkcolleges"]:
        pad = os.path.join("notebooks", bestand)
        if not os.path.exists(pad):
            continue
        nb = lees_notebook(pad)
        rijen = tijdstabel_totaal(nb)
        if rijen is None:
            meld(LET_OP, f"{bestand}: geen tijdstabel gevonden om tegen te vergelijken")
            continue

        # Alleen de werkcollegetijd vergelijken. De tabel dekt ook het huiswerk
        # (en in Werkcollege 1 zelfs een totaalregel); die horen niet in de
        # 120 minuten die je voor de zaal plant.
        koppen = [(t, m) for t, m, hw in delen_van(nb) if not hw]
        tabel_min = [m for m, hw in rijen if not hw]
        totaal = sum(tabel_min)

        # Koppen en tabelrijen staan allebei in leesvolgorde. Zijn het er
        # evenveel, dan horen ze een-op-een bij elkaar en is een verschil op
        # een kop die wel een tijd noemt een echte fout. Een kop zonder tijd
        # (Reflectievragen, of een deel dat uren kost) slaan we over in plaats
        # van er elke week een waarschuwing over te geven die nergens op slaat.
        if len(koppen) != len(tabel_min):
            meld(OK, f"{bestand}: {totaal} min werkcollege volgens de tabel",
                 f"{len(koppen)} koppen tegen {len(tabel_min)} tabelrijen -- "
                 "niet één-op-één na te rekenen.")
            continue

        afwijkend = [(t, m, d) for (t, m), d in zip(koppen, tabel_min) if m and m != d]
        if afwijkend:
            meld(FOUT, f"{bestand}: {len(afwijkend)} kop(pen) wijken af van de tijdstabel",
                 "\n".join(f"{t}: kop {m} min, tabel {d} min" for t, m, d in afwijkend))
        else:
            meld(OK, f"{bestand}: {totaal} min werkcollege, koppen en tabel zijn het eens")


def check_brightspace(week):
    """Staat de gegenereerde pagina nog gelijk aan wat het script nu zou maken?"""
    kop("Brightspace-pagina")
    pad = f"brightspace/week{week}.html"
    if not os.path.exists(pad):
        meld(FOUT, f"{pad} bestaat niet", "python3 scripts/genereer_brightspace_paginas.py")
        return
    with open(pad, encoding="utf-8") as f:
        op_schijf = f.read()
    if op_schijf == weekpagina(week_data(week)):
        meld(OK, f"{pad} is gelijk aan wat het script nu maakt")
    else:
        meld(FOUT, f"{pad} loopt achter op het script",
             "Iemand heeft met de hand aangepast, of het script is veranderd.\n"
             "python3 scripts/genereer_brightspace_paginas.py")


def check_api(week, offline=False):
    kop("Live API")
    if offline:
        meld(OVERGESLAGEN, "overgeslagen (--offline)")
        return
    try:
        with urllib.request.urlopen(f"{API}/openapi.json", timeout=60) as r:
            routes = set(json.load(r).get("paths", {}))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        meld(LET_OP, "server niet bereikbaar", f"{type(e).__name__}: {e}")
        return

    # De server noemt zijn padparameters bij naam; wij hebben ze tot {x}
    # teruggebracht, dus doe dat bij de server ook.
    genormaliseerd = {re.sub(r"\{[^}]+\}", "{x}", r) for r in routes}

    gevraagd = set()
    for bestand, _, _ in week_data(week)["werkcolleges"]:
        pad = os.path.join("notebooks", bestand)
        if os.path.exists(pad):
            gevraagd |= endpoints_van(lees_notebook(pad))

    if not gevraagd:
        meld(OK, "de notebooks van deze week roepen de API niet aan")
        return

    ontbreekt = sorted(p for p in gevraagd if p not in genormaliseerd)
    if ontbreekt:
        meld(FOUT, "de notebooks roepen endpoints aan die de server niet heeft",
             "\n".join(ontbreekt) + "\nStudenten krijgen hier een 404.")
    else:
        meld(OK, f"alle {len(gevraagd)} aangeroepen endpoints bestaan op de server")


def check_deploy(offline=False):
    kop("Deploy")
    try:
        if not offline:
            subprocess.run(["git", "fetch", "-q", "origin"], timeout=60, check=False)
        uit = subprocess.run(["git", "rev-list", "--count", "origin/main..HEAD"],
                             capture_output=True, text=True, timeout=30)
        if uit.returncode != 0:
            meld(LET_OP, "kon niet tegen origin/main vergelijken", uit.stderr.strip())
            return
        aantal = int(uit.stdout.strip() or 0)
        api_uit = subprocess.run(["git", "diff", "--name-only", "origin/main..HEAD", "--", "api/"],
                                 capture_output=True, text=True, timeout=30)
        api_bestanden = [r for r in api_uit.stdout.split("\n") if r.strip()]
    except (subprocess.SubprocessError, OSError, ValueError) as e:
        meld(LET_OP, "deploycheck mislukt", str(e))
        return

    if aantal == 0:
        meld(OK, "origin/main is bij — de server draait wat hier staat")
    elif api_bestanden:
        meld(FOUT, f"{aantal} commits niet gepusht, waarvan {len(api_bestanden)} in api/",
             "Render deployt van origin/main, dus die wijzigingen zijn niet live.\n"
             "git push origin main")
    else:
        meld(LET_OP, f"{aantal} commits niet gepusht (niets in api/)",
             "Raakt de server niet, maar het staat alleen op deze machine.")


def check_tests():
    kop("Tests")
    for naam in TESTS:
        pad = os.path.join("scripts", naam)
        if not os.path.exists(pad):
            meld(LET_OP, f"{naam} bestaat niet")
            continue
        uit = subprocess.run([sys.executable, pad], capture_output=True, text=True, timeout=600)
        laatste = [r for r in uit.stdout.strip().split("\n") if r.strip()]
        samenvatting = laatste[-1] if laatste else ""
        if uit.returncode == 0:
            meld(OK, f"{naam}: {samenvatting}")
        else:
            meld(FOUT, f"{naam} faalt", (uit.stdout + uit.stderr).strip()[-600:])


def check_eigen_punten(week):
    kop("Je eigen checklist")
    if not os.path.exists(CHECKLIST):
        meld(LET_OP, f"{CHECKLIST} bestaat niet",
             "Zet daar je eigen punten in onder een kop '## Week N'.")
        return
    with open(CHECKLIST, encoding="utf-8") as f:
        tekst = f.read()

    blok = re.search(rf"^##\s*Week\s*{week}\b(.*?)(?=^##\s|\Z)", tekst, re.M | re.S)
    algemeen = re.search(r"^##\s*Elke week\b(.*?)(?=^##\s|\Z)", tekst, re.M | re.S)

    # Een punt mag doorlopen op de volgende regel, zolang die inspringt. Zonder
    # dat kapt de melding af op de eerste regeleinde en lees je een halve zin.
    open_punten = []
    for stuk in (blok, algemeen):
        if not stuk:
            continue
        huidig = None
        for regel in stuk.group(1).split("\n"):
            begin = re.match(r"\s*-\s*\[( |x|X)\]\s*(.*)$", regel)
            if begin:
                if huidig:
                    open_punten.append(huidig)
                huidig = begin.group(2).strip() if begin.group(1) == " " else None
            elif huidig is not None and regel.startswith((" ", "\t")) and regel.strip():
                huidig += " " + regel.strip()
            elif not regel.strip():
                if huidig:
                    open_punten.append(huidig)
                huidig = None
        if huidig:
            open_punten.append(huidig)

    if not open_punten:
        meld(OK, f"geen openstaande punten voor week {week}")
    else:
        for punt in open_punten:
            meld(LET_OP, punt.strip())


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--week", type=int, help="welke onderwijsweek (standaard: nu)")
    p.add_argument("--offline", action="store_true", help="server en git-fetch overslaan")
    p.add_argument("--kort", action="store_true", help="alleen wat er nog moet")
    p.add_argument("--geen-tests", action="store_true", help="de testscripts niet draaien")
    args = p.parse_args()

    week = args.week or huidige_week()
    if week_data(week) is None:
        print(f"Week {week} bestaat niet in WEKEN.")
        return 2

    if not args.kort:
        briefing(week)
        print("\n" + "=" * 68)

    check_notebooks(week)
    check_tijden(week)
    check_brightspace(week)
    check_api(week, offline=args.offline)
    check_deploy(offline=args.offline)
    if not args.geen_tests:
        check_tests()
    check_eigen_punten(week)

    print("\n" + "=" * 68)
    fouten = [p for p in problemen if p[0] == FOUT]
    aandacht = [p for p in problemen if p[0] == LET_OP]
    if not problemen:
        print(f"\nAlles klaar voor week {week}.")
        return 0

    print(f"\nNOG TE DOEN — week {week}\n")
    for status, regel, uitleg in fouten + aandacht:
        merk = "MOET" if status == FOUT else "check"
        print(f"  {merk:>5}  {regel}")
        for r in uitleg.split("\n"):
            if r.strip():
                print(f"         {r}")
    print(f"\n{len(fouten)} moeten opgelost, {len(aandacht)} om even naar te kijken.")
    return 1 if fouten else 0


if __name__ == "__main__":
    sys.exit(main())
