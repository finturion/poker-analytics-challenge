"""
Wekelijkse DataCamp-snapshot voor de Minor Data Science.

Waarom een script en geen export: DataCamp's CSV-export en Data Connector
zitten achter het Enterprise-plan, dus een Classroom-groep kan er niet bij.
Wat wél kan: het GraphQL-endpoint dat de webapp zelf gebruikt, opgevraagd
vanuit een ingelogde browser. Dit script doet precies dat en niets meer.

Twee queries zijn genoeg:
- paginatedLeaderboards  -> alle groepsleden met XP/chapters vanaf een zelf
                            gekozen begindatum (dus vanaf blokstart, niet
                            "laatste 30 dagen" zoals de webpagina toont).
- userProgressReportV2   -> per lid welke course wanneer is afgerond.

Gebruik:
    python datacamp_snapshot.py --login     # eenmalig: browser opent, jij logt in
    python datacamp_snapshot.py             # wekelijkse run
    python datacamp_snapshot.py --stuur-naar-hub

Eenmalig installeren:
    pip install playwright requests

WAAROM JE ECHTE CHROME EN NIET DE BROWSER VAN PLAYWRIGHT:
DataCamp zit achter Cloudflare. De Chromium die Playwright meelevert wordt als
bot gefingerprint en blijft hangen op "Beveiliging wordt geverifieerd" -- je
komt niet eens bij het inlogscherm. Daarom gebruiken we het echte
Google Chrome dat al op deze Mac staat, met een eigen profielmap
(~/.datacamp_chrome_profiel) los van je dagelijkse Chrome:

- --login start dat profiel als een volkomen normale Chrome, zonder debug-poort
  en zonder automatisering. Cloudflare en de HvA-login zien dus een gewone
  browser, en JIJ logt daar in. Dit script kent je wachtwoord niet.
- De wekelijkse run start hetzelfde profiel mét een debug-poort en praat er via
  CDP tegen. De sessie- en Cloudflare-cookies staan dan al in het profiel, dus
  er hoeft niets meer geverifieerd te worden. Niet headless: een headless
  Chrome wordt door Cloudflare alsnog geweigerd, dus het venster start
  buiten het zichtbare deel van je scherm.
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

GROEP_SLUG = "minor-data-science-2627-s1"
BLOKSTART = "2026-08-31"  # XP vanaf deze datum tellen we mee; eerder is vorig blok/eigen werk
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_PROFIEL = Path.home() / ".datacamp_chrome_profiel"
CDP_POORT = 9222
CLOUDFLARE_TEKSTEN = ("geverifieerd", "Verifying", "Just a moment", "verifying you are human")
HIER = Path(__file__).resolve().parent

# Klaslijst en uitvoermap staan normaal naast dit script, maar zijn met
# omgevingsvariabelen te verplaatsen. Dat is niet voor de sier: de wekelijkse
# LaunchAgent draait vanuit ~/Library/Application Support/datacamp-snapshot,
# omdat launchd bestanden in iCloud Drive niet mág lezen ("Operation not
# permitted", ook als het bestand bestaat).
KLASLIJST = Path(os.environ.get("DATACAMP_KLASLIJST") or HIER / "klaslijst_datacamp.csv")
UITVOER_MAP = Path(os.environ.get("DATACAMP_UITVOER") or HIER / "datacamp_snapshots")
LEADERBOARD_URL = f"https://app.datacamp.com/groups/{GROEP_SLUG}/leaderboard"

# De harvest draait in de pagina zelf: daar zit de ingelogde sessie, en
# fetch() met credentials:'include' mag vanaf app.datacamp.com naar
# www.datacamp.com/groups/graphql (dat doet de webapp zelf ook).
HARVEST_JS = """
async ({slug, sinds}) => {
  const GQL = 'https://www.datacamp.com/groups/graphql';
  const post = async (query) => {
    const r = await fetch(GQL, {
      method: 'POST', credentials: 'include',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({query}),
    });
    const j = await r.json();
    if (j.errors) throw new Error(j.errors.map(e => e.message).join(' | '));
    return j.data;
  };

  const lbQuery = `{ paginatedLeaderboards(groupSlug:"${slug}",
      pagination:{currentPage:1,pageSize:200}, searchTerm:"", since:${sinds},
      sort:{field:xp,order:desc}, teamFilter:{everyone:true,notInTeam:false}) {
      pagination{totalRecords}
      leaderboards{ userId totalCourses totalChapters totalXp lastXp user{ email fullName } } } }`;
  const lb = (await post(lbQuery)).paginatedLeaderboards.leaderboards;

  const leden = [];
  for (const m of lb) {
    const pQuery = `{ userProgressReportV2(groupSlug:"${slug}", interval:all_time,
        scope:sinceJoining, userId:${m.userId}, from:null, to:null) {
        data{ title contentType completedAt } } }`;
    const rapport = (await post(pQuery)).userProgressReportV2.data || [];
    const courses = {};
    for (const item of rapport) {
      if (item.contentType === 'Course' && item.completedAt) {
        courses[item.title] = item.completedAt.slice(0, 10);
      }
    }
    leden.push({
      user_id: m.userId,
      email: (m.user.email || '').toLowerCase(),
      naam_in_datacamp: m.user.fullName || '',
      xp: m.totalXp || 0,
      chapters: m.totalChapters || 0,
      laatste_xp_op: m.lastXp || null,
      courses,
    });
  }
  return leden;
}
"""


def _epoch(datum_iso: str) -> int:
    """Middernacht lokale tijd, net zoals de webapp de datumfilter opstuurt."""
    return int(datetime.fromisoformat(datum_iso).timestamp())


def _controleer_chrome():
    if not Path(CHROME).exists():
        sys.exit(f"Google Chrome niet gevonden op {CHROME}. Installeer Chrome of pas CHROME aan.")


def _start_chrome(poort: int | None, zichtbaar: bool) -> subprocess.Popen:
    """
    Start het eigen Chrome-profiel. Zonder poort is dit een gewone Chrome (om in
    te loggen); met poort erbij kan CDP eraan praten.

    Het venster staat standaard buiten het zichtbare scherm in plaats van
    headless: headless Chrome wordt door Cloudflare wél geweigerd.
    """
    _controleer_chrome()
    argumenten = [
        CHROME,
        f"--user-data-dir={CHROME_PROFIEL}",
        "--no-first-run",
        "--no-default-browser-check",
        # Chrome wordt na elke run hard afgesloten. Zonder deze twee vlaggen
        # begint de volgende start met "Chrome is onverwacht afgesloten -
        # pagina's herstellen?", en dat wil je niet in een onbeheerde run.
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
    ]
    if poort is not None:
        argumenten.append(f"--remote-debugging-port={poort}")
    if not zichtbaar:
        argumenten += ["--window-position=-2400,-2400", "--window-size=1280,900"]
    argumenten.append(LEADERBOARD_URL)
    return subprocess.Popen(argumenten, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _wacht_op_poort(poort: int, seconden: int = 30) -> bool:
    for _ in range(seconden * 2):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{poort}/json/version", timeout=1).read()
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _stop_chrome(proc: subprocess.Popen):
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except Exception:
        proc.kill()


def _wacht_tot_pagina_klaar(pagina, seconden: int = 90) -> str:
    """
    Geeft "ok", "inloggen" of "cloudflare" terug.

    De Cloudflare-check kan een paar seconden duren; met een profiel dat er al
    eerder door is, is hij meestal meteen klaar. Blijft hij hangen, dan is dat
    een echt antwoord en geen reden om oneindig te wachten.
    """
    einde = time.time() + seconden
    while time.time() < einde:
        if "sign_in" in pagina.url:
            return "inloggen"
        try:
            tekst = pagina.inner_text("body")[:600]
        except Exception:
            tekst = ""
        if not any(t in tekst for t in CLOUDFLARE_TEKSTEN):
            return "ok"
        time.sleep(2)
    return "cloudflare"


def haal_uit_datacamp(sinds: str, zichtbaar: bool, poort: int = CDP_POORT) -> list[dict]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("Playwright ontbreekt. Eenmalig installeren:\n    pip install playwright requests")

    if not CHROME_PROFIEL.exists():
        sys.exit("Nog geen Chrome-profiel voor DataCamp. Draai eenmalig:  python datacamp_snapshot.py --login")

    proc = _start_chrome(poort, zichtbaar)
    try:
        if not _wacht_op_poort(poort):
            sys.exit(
                f"Chrome opende geen debug-poort {poort}. Draait er al een Chrome met dit profiel? "
                "Sluit die en probeer opnieuw, of kies een andere poort met --poort."
            )
        with sync_playwright() as pw:
            browser = pw.chromium.connect_over_cdp(f"http://127.0.0.1:{poort}")
            context = browser.contexts[0]
            pagina = context.pages[0] if context.pages else context.new_page()
            if not pagina.url.startswith("https://app.datacamp.com"):
                pagina.goto(LEADERBOARD_URL, wait_until="domcontentloaded", timeout=60000)

            toestand = _wacht_tot_pagina_klaar(pagina)
            if toestand == "inloggen":
                sys.exit("Niet (meer) ingelogd bij DataCamp.\nDraai eenmalig:  python datacamp_snapshot.py --login")
            if toestand == "cloudflare":
                sys.exit(
                    "Cloudflare liet deze sessie niet door (de botcheck bleef hangen).\n"
                    "Draai eenmaal 'python datacamp_snapshot.py --login --zichtbaar', klik de check zelf weg, "
                    "en probeer het daarna opnieuw."
                )

            leden = pagina.evaluate(HARVEST_JS, {"slug": GROEP_SLUG, "sinds": _epoch(sinds)})
            browser.close()
    finally:
        _stop_chrome(proc)
    return leden


def inloggen(zichtbaar: bool = True, poort: int = CDP_POORT):
    """
    Eenmalig inloggen in een GEWONE Chrome: geen debug-poort, geen
    automatisering, niets dat Cloudflare of de HvA-login kan opvallen.
    """
    proc = _start_chrome(None, zichtbaar=True)
    print("Er is een Chrome-venster geopend met een apart profiel voor DataCamp.")
    print("Log daar in met je HvA-account (j.j.mies@hva.nl) tot je de leaderboard van de groep ziet.")
    print("")
    print("BELANGRIJK: vink 'Remember me' aan op het inlogscherm.")
    print("Zonder dat vinkje geeft DataCamp een sessie-cookie dat Chrome weggooit zodra dit")
    print("venster sluit -- en dit script sluit het venster direct na je Enter. De wekelijkse")
    print("run vindt dan geen sessie en meldt 'Niet (meer) ingelogd'.")
    print("")
    input("Klaar? Druk hier op Enter (het venster wordt dan gesloten)... ")
    _stop_chrome(proc)
    time.sleep(3)  # Chrome moet het profiel eerst vrijgeven voor de volgende start

    print("Controleren of de sessie bruikbaar is voor de wekelijkse run...")
    try:
        leden = haal_uit_datacamp(BLOKSTART, zichtbaar=False, poort=poort)
    except SystemExit as fout:
        raise SystemExit(f"Nog niet gelukt: {fout}")
    print(f"Gelukt: {len(leden)} DataCamp-accounts opgehaald. De wekelijkse run kan nu zonder inloggen.")


def lees_klaslijst() -> list[dict]:
    if not KLASLIJST.exists():
        sys.exit(
            f"Klaslijst niet gevonden: {KLASLIJST}\n"
            "Verwachte kolommen: studentnummer,naam,team,klas,datacamp_email"
        )
    with open(KLASLIJST, newline="", encoding="utf-8") as f:
        return [rij for rij in csv.DictReader(f) if (rij.get("studentnummer") or "").strip()]


def koppel(leden: list[dict], klaslijst: list[dict]) -> dict:
    """
    Koppelt DataCamp-accounts aan studentnummers op e-mailadres.

    De e-mail is de enige harde sleutel: namen staan in DataCamp vaak leeg of
    anders gespeld ("milan rada", "Xavi Van Marle"). Alles wat niet matcht
    komt in de snapshot terecht als losse melding in plaats van stil te
    verdwijnen -- een student die je niet ziet, is het echte probleem.
    """
    per_email = {lid["email"]: lid for lid in leden if lid["email"]}
    studenten, zonder_account, gebruikt = [], [], set()

    for rij in klaslijst:
        email = (rij.get("datacamp_email") or "").strip().lower()
        lid = per_email.get(email)
        if lid is None:
            zonder_account.append(rij["naam"])
            continue
        gebruikt.add(email)
        studenten.append(
            {
                "studentnummer": rij["studentnummer"].strip(),
                "naam": rij["naam"],
                "team": rij.get("team") or None,
                "klas": rij.get("klas") or None,
                "datacamp_email": lid["email"],
                "xp": lid["xp"],
                "chapters": lid["chapters"],
                "courses": lid["courses"],
            }
        )

    niet_gekoppeld = sorted(e for e in per_email if e not in gebruikt)
    return {
        "opgehaald_op": datetime.now().astimezone().isoformat(timespec="seconds"),
        "studenten": studenten,
        "zonder_account": zonder_account,
        "niet_gekoppeld": niet_gekoppeld,
    }


def stuur_naar_hub(snapshot: dict, api_url: str, docent_token: str):
    import requests

    antwoord = requests.post(
        f"{api_url.rstrip('/')}/datacamp/snapshot",
        json=snapshot,
        headers={"Authorization": f"Bearer {docent_token}"},
        timeout=60,
    )
    if antwoord.status_code != 200:
        print(f"Versturen naar de hub mislukt ({antwoord.status_code}): {antwoord.text[:300]}")
        return False
    print(f"Naar de hub gestuurd: {antwoord.json()}")
    return True


def main():
    p = argparse.ArgumentParser(description="Haalt de DataCamp-voortgang van de minor op.")
    p.add_argument("--login", action="store_true", help="Eenmalig inloggen in een echt browservenster.")
    p.add_argument("--sinds", default=BLOKSTART, help=f"XP tellen vanaf deze datum (default {BLOKSTART}).")
    p.add_argument("--zichtbaar", action="store_true", help="Chrome-venster zichtbaar tijdens de run (debuggen).")
    p.add_argument("--poort", type=int, default=CDP_POORT, help=f"Debug-poort voor Chrome (default {CDP_POORT}).")
    p.add_argument("--uit-ruw", metavar="BESTAND", help="Sla de browser over en gebruik een eerder ruw-bestand.")
    p.add_argument("--stuur-naar-hub", action="store_true", help="Snapshot naar de Poker-Analytics-API POSTen.")
    p.add_argument("--api", default=os.environ.get("POKER_API_URL", "https://poker-analytics-api.onrender.com"))
    p.add_argument("--docent-token", default=os.environ.get("POKER_DOCENT_TOKEN", ""))
    args = p.parse_args()

    if args.login:
        inloggen(poort=args.poort)
        return

    if args.uit_ruw:
        leden = json.loads(Path(args.uit_ruw).read_text())
    else:
        leden = haal_uit_datacamp(args.sinds, args.zichtbaar, args.poort)

    UITVOER_MAP.mkdir(parents=True, exist_ok=True)
    vandaag = date.today().isoformat()
    ruw_bestand = UITVOER_MAP / f"{vandaag}-ruw.json"
    ruw_bestand.write_text(json.dumps(leden, indent=1, ensure_ascii=False))

    snapshot = koppel(leden, lees_klaslijst())
    snapshot_bestand = UITVOER_MAP / f"{vandaag}.json"
    snapshot_bestand.write_text(json.dumps(snapshot, indent=1, ensure_ascii=False))

    print(f"{len(leden)} DataCamp-accounts opgehaald, {len(snapshot['studenten'])} aan een studentnummer gekoppeld.")
    if snapshot["zonder_account"]:
        print(f"Geen DataCamp-account ({len(snapshot['zonder_account'])}): {', '.join(snapshot['zonder_account'])}")
    if snapshot["niet_gekoppeld"]:
        print(f"Niet in de klaslijst ({len(snapshot['niet_gekoppeld'])}): {', '.join(snapshot['niet_gekoppeld'])}")
    print(f"Weggeschreven: {snapshot_bestand}")

    if args.stuur_naar_hub:
        if not args.docent_token:
            sys.exit("Geen docent-token: zet POKER_DOCENT_TOKEN of gebruik --docent-token.")
        if not stuur_naar_hub(snapshot, args.api, args.docent_token):
            # Bewust een foutcode: het lokale bestand staat er wel, maar de hub
            # is niet bijgewerkt. Zonder deze exit meldt de wrapper "Klaar" en
            # denk je dat studenten een nieuwe stand zien terwijl dat niet zo is.
            sys.exit(1)


if __name__ == "__main__":
    main()
