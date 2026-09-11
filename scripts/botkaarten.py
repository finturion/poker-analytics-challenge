"""
Eén kaartje per bot: wat deed hij werkelijk, en waar wijkt hij af van de klas?

Bedoeld voor de overhoring op maandag in week 6. Je leest het kaartje van een
student en hebt je vraag zonder voorbereiding -- en omdat de getallen uit zijn
eigen log komen, kan hij ze niet hebben voorbereid: hij heeft er zelf nooit naar
gekeken.

Draai hem voor de héle klas, niet alleen voor wie punten scoorde. Het kaartje
kost niets extra per student, en de confrontatie tussen "wat ik dacht dat mijn
bot deed" en "wat hij deed" is het leereffect. De overhoring is de controle
daarop, niet de bron ervan.

    python3 scripts/botkaarten.py --json uitslag.json
    python3 scripts/botkaarten.py --api --ronde 2        # haalt zelf op
    python3 scripts/botkaarten.py --api --student 500123456

Met --api lees je STUDENT_ID en TOKEN uit de omgeving:

    export POKER_STUDENT_ID=... POKER_TOKEN=...

WAT HET LOG WEL EN NIET WEET
----------------------------
Het hand-log bewaart per hand één regel, met de EERSTE actie van die hand en
geen straat. "Hoe vaak foldde hij op de river" is er dus niet uit te halen --
daarvoor zou poker_adapter elke beslissing moeten wegschrijven in plaats van de
eerste. Wat er wel in zit is genoeg: welke twee kaarten, wat hij ermee deed, en
wat het opleverde. Dat laatste is af te leiden uit het stackverloop.
"""

import argparse
import io
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(WORTEL, "api"))

API_URL = "https://poker-analytics-api.onrender.com"
STARTSTACK = 1000

HOGE_KAARTEN = {"A", "K", "Q", "J", "10"}


# ---------------------------------------------------------------------------
# Data binnenhalen
# ---------------------------------------------------------------------------

def haal_van_api(week, ronde):
    import urllib.parse
    import urllib.request

    student_id = os.environ.get("POKER_STUDENT_ID")
    token = os.environ.get("POKER_TOKEN")
    if not (student_id and token):
        sys.exit("Zet POKER_STUDENT_ID en POKER_TOKEN in je omgeving, of gebruik --json.")

    vraag = urllib.parse.urlencode({"student_id": student_id, "ronde": ronde})
    verzoek = urllib.request.Request(
        f"{API_URL}/toernooi/{week}?{vraag}",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(verzoek, timeout=900) as antwoord:
        return json.load(antwoord)


# ---------------------------------------------------------------------------
# Rekenen
# ---------------------------------------------------------------------------

def winst_per_regel(log, startstacks=None):
    """
    Wat elke hand opleverde, afgeleid uit het stackverloop.

    Het log schrijft de stack ná elke hand. De winst van een hand is dus het
    verschil met de hand ervoor, binnen dezelfde (bot, simulatie, tafel) --
    over die grenzen heen vergelijken slaat nergens op, want dat zijn andere
    parallelle werelden.

    `startstacks` moet je meegeven vanaf ronde 2. Daar begint niemand op 1000:
    iedereen speelt door met de chips uit de vorige ronde plus 1000 erbij, en
    de uitslag bewaart die beginstanden. Reken je dan toch tegen 1000, dan is
    de eerste hand van elke zitting honderden chips te goed of te kwaad -- en
    precies dat getal zet je op het kaartje waar je iemand op bevraagt.
    """
    startstacks = startstacks or {}
    per_zitting = defaultdict(list)
    for rij in log:
        sleutel = (rij["bot_naam"], rij.get("simulatie"), rij.get("tafel"))
        per_zitting[sleutel].append(rij)

    verrijkt = []
    for regels in per_zitting.values():
        regels.sort(key=lambda r: r["hand_nummer"])
        begin = startstacks.get(regels[0]["bot_naam"], STARTSTACK)
        vorige = None
        for rij in regels:
            basis = begin if vorige is None else vorige
            verrijkt.append({**rij, "winst": rij["stack"] - basis})
            vorige = rij["stack"]
    return verrijkt


def handsoort(hand):
    """Grof genoeg om over te praten, fijn genoeg om iets te zien."""
    if not hand or len(hand) != 2:
        return "onbekend"
    if hand[0] == hand[1]:
        return "paar"
    if hand[0] in HOGE_KAARTEN and hand[1] in HOGE_KAARTEN:
        return "twee hoge"
    if hand[0] in HOGE_KAARTEN or hand[1] in HOGE_KAARTEN:
        return "één hoge"
    return "twee lage"


def profiel(regels):
    """De cijfers van één bot."""
    aan_zet = [r for r in regels if r.get("aan_zet")]
    niet_aan_zet = [r for r in regels if not r.get("aan_zet")]

    acties = Counter(r["actie"] for r in aan_zet)
    winst_per_actie = defaultdict(list)
    for r in aan_zet:
        winst_per_actie[r["actie"]].append(r["winst"])

    per_soort = defaultdict(Counter)
    for r in aan_zet:
        per_soort[handsoort(r.get("hand"))][r["actie"]] += 1

    return {
        "handen": len(regels),
        "aan_zet": len(aan_zet),
        "uitgespeeld": sum(1 for r in niet_aan_zet if r.get("uitgespeeld")),
        "zonder_tegenstand": sum(1 for r in niet_aan_zet if not r.get("uitgespeeld")),
        "acties": acties,
        "winst_per_actie": {a: statistics.mean(w) for a, w in winst_per_actie.items() if w},
        "per_handsoort": per_soort,
        "regels": regels,
    }


def opvallende_handen(regels, hoeveel=3):
    """
    Handen waar iets gebeurde waar je naar kunt vragen.

    Drie soorten, in deze volgorde: een sterke hand die is weggelegd, een zwakke
    hand waarmee is geraised, en het grootste verlies. Ze overlappen soms; dan
    vult de lijst zich aan met het eerstvolgende dat er nog niet in staat.
    """
    aan_zet = [r for r in regels if r.get("aan_zet") and r.get("hand")]
    gekozen, gezien = [], set()

    def voeg_toe(rij, waarom):
        sleutel = (rij.get("simulatie"), rij.get("tafel"), rij["hand_nummer"])
        if rij and sleutel not in gezien:
            gezien.add(sleutel)
            gekozen.append((rij, waarom))

    paren_gefold = [r for r in aan_zet if handsoort(r["hand"]) == "paar" and r["actie"] == "fold"]
    if paren_gefold:
        voeg_toe(min(paren_gefold, key=lambda r: r["winst"]), "je had een paar en je foldde")

    laag_agressief = [r for r in aan_zet
                      if handsoort(r["hand"]) == "twee lage"
                      and r["actie"] in ("raise", "grote_raise", "all_in")]
    if laag_agressief:
        slechtste = min(laag_agressief, key=lambda r: r["winst"])
        voeg_toe(slechtste, f"je {slechtste['actie']}te met twee lage kaarten")

    if aan_zet:
        voeg_toe(min(aan_zet, key=lambda r: r["winst"]), "je grootste verlies van het toernooi")

    for rij in sorted(aan_zet, key=lambda r: r["winst"]):
        if len(gekozen) >= hoeveel:
            break
        voeg_toe(rij, f"{rij['actie']} met {rij['hand']}")

    return gekozen[:hoeveel]


# ---------------------------------------------------------------------------
# Afdrukken
# ---------------------------------------------------------------------------

def percentage(deel, geheel):
    return f"{100 * deel / geheel:4.0f}%" if geheel else "   -"


def druk_kaart(naam, prof, eindstand, plek, aantal_bots, klas_mediaan, begonnen_met=None):
    print("=" * 68)
    kop = f"{naam}"
    if eindstand is not None:
        kop += f"   eindstand {eindstand:.0f}"
        if begonnen_met is not None:
            kop += f"   (begon op {begonnen_met}, dus {eindstand - begonnen_met:+.0f})"
    if plek:
        kop += f"   plek {plek} van {aantal_bots}"
    print(kop)
    print("=" * 68)

    print(f"\n{prof['handen']} handen gespeeld, {prof['aan_zet']} keer aan zet.")
    print(f"Niet aan zet: {prof['zonder_tegenstand']}× kreeg je de pot zonder te spelen, "
          f"{prof['uitgespeeld']}× was je al uitgespeeld.")

    print("\nWat je bot deed als hij aan zet kwam (eerste actie van de hand)")
    for actie, aantal in prof["acties"].most_common():
        gemiddeld = prof["winst_per_actie"].get(actie, 0)
        afwijking = ""
        if actie in klas_mediaan and prof["aan_zet"]:
            eigen = 100 * aantal / prof["aan_zet"]
            verschil = eigen - klas_mediaan[actie]
            if abs(verschil) >= 8:
                richting = "meer" if verschil > 0 else "minder"
                afwijking = (f"   <- {richting} dan de klas "
                             f"(mediaan {klas_mediaan[actie]:.0f}%)")
        print(f"   {actie or 'onbekend':<12} {aantal:>4} ×  {percentage(aantal, prof['aan_zet'])}"
              f"   gemiddeld {gemiddeld:+7.0f} chips{afwijking}")

    print("\nWat je deed met welke kaarten")
    for soort in ("paar", "twee hoge", "één hoge", "twee lage"):
        teller = prof["per_handsoort"].get(soort)
        if not teller:
            continue
        totaal = sum(teller.values())
        verdeling = "  ".join(f"{a} {percentage(n, totaal)}" for a, n in teller.most_common())
        print(f"   {soort:<12} {totaal:>4} handen   {verdeling}")

    print("\nDrie handen om naar te vragen")
    for rij, waarom in opvallende_handen(prof["regels"]):
        plaats = f"sim {rij.get('simulatie')}, tafel {rij.get('tafel')}, hand {rij['hand_nummer']}"
        print(f"   {plaats:<34} {rij['hand']} -> {rij['actie']}, {rij['winst']:+.0f} chips")
        print(f"   {'':<34} \"{waarom} — waarom?\"")
    print()


def klas_medianen(profielen):
    """Wat de klas gemiddeld doet, zodat 'afwijkend' iets betekent."""
    per_actie = defaultdict(list)
    for prof in profielen.values():
        if not prof["aan_zet"]:
            continue
        for actie in ("fold", "call", "raise", "all_in", "grote_raise", "check"):
            per_actie[actie].append(100 * prof["acties"].get(actie, 0) / prof["aan_zet"])
    return {a: statistics.median(v) for a, v in per_actie.items() if any(v)}


# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    bron = p.add_mutually_exclusive_group(required=True)
    bron.add_argument("--json", help="een opgeslagen antwoord van /toernooi/{week}")
    bron.add_argument("--api", action="store_true", help="zelf ophalen bij de API")
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde", type=int, default=2, help="2 = de slotronde van vrijdag")
    p.add_argument("--student", help="alleen dit studentnummer")
    p.add_argument("--map", dest="uitvoermap",
                   help="schrijf één tekstbestand per bot in deze map, "
                        "in plaats van alles naar het scherm")
    args = p.parse_args()

    uitslag = (json.load(open(args.json, encoding="utf-8")) if args.json
               else haal_van_api(args.week, args.ronde))

    if uitslag.get("gedraaid") is False:
        sys.exit(f"Ronde {args.ronde} van week {args.week} is nog niet gedraaid.")

    log = uitslag.get("hand_log") or []
    if not log:
        sys.exit("Geen hand_log in deze uitslag.")

    # None in ronde 1 (iedereen begint op 1000), gevuld vanaf ronde 2.
    startstacks = uitslag.get("startstacks") or {}
    if args.ronde > 1 and not startstacks and not args.json:
        sys.exit(f"Ronde {args.ronde} zonder startstacks in de uitslag — dan klopt "
                 "de winst per hand niet. Controleer de uitslag voordat je verder gaat.")

    eindstand = uitslag.get("eindstand_per_bot") or {}
    volgorde = sorted(eindstand, key=lambda n: -eindstand[n])
    plek_van = {naam: i + 1 for i, naam in enumerate(volgorde)}

    verrijkt = winst_per_regel(log, startstacks)
    per_bot = defaultdict(list)
    for rij in verrijkt:
        per_bot[rij["bot_naam"]].append(rij)

    profielen = {naam: profiel(regels) for naam, regels in per_bot.items()}
    medianen = klas_medianen(profielen)

    namen = [args.student] if args.student else volgorde or sorted(profielen)
    ontbreekt = [n for n in namen if n not in profielen]
    if ontbreekt:
        sys.exit(f"Geen log gevonden voor: {', '.join(ontbreekt)}")

    if args.uitvoermap:
        os.makedirs(args.uitvoermap, exist_ok=True)

    for naam in namen:
        if args.uitvoermap:
            # Zo kun je ze uitdelen: iedereen zijn eigen kaartje, en dat kost
            # niets extra ten opzichte van alleen de tien die je overhoort.
            pad = os.path.join(args.uitvoermap, f"{naam}.txt")
            eigen = io.StringIO()
            oud, sys.stdout = sys.stdout, eigen
            try:
                druk_kaart(naam, profielen[naam], eindstand.get(naam),
                           plek_van.get(naam), len(volgorde), medianen,
                           startstacks.get(naam, STARTSTACK))
            finally:
                sys.stdout = oud
            with open(pad, "w", encoding="utf-8") as f:
                f.write(eigen.getvalue())
        else:
            druk_kaart(naam, profielen[naam], eindstand.get(naam),
                       plek_van.get(naam), len(volgorde), medianen,
                       startstacks.get(naam, STARTSTACK))

    if args.uitvoermap:
        print(f"{len(namen)} kaartjes geschreven in {args.uitvoermap}/")


if __name__ == "__main__":
    main()
