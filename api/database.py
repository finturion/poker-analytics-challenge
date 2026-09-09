"""
Opslag-laag voor de Poker Analytics Challenge API.

Elke "tabel" (submissions, gallery, reviews, tokens, ...) is gewoon één
sleutel in een key-value store: {"submissions_db.json": {...grote dict...}}.
Dat is bewust simpel gehouden — de rest van de API (main.py, toernooi_runner.py)
kent alleen laad_x()/sla_x_op()-functies en weet niet of daarachter Postgres
of een lokaal bestand zit.

Is de omgevingsvariabele DATABASE_URL gezet (op Render: automatisch, zodra je
een Postgres-database aan deze service koppelt), dan gaat alles naar Postgres
— dat overleeft een herstart/redeploy van de API, in tegenstelling tot lokale
bestanden op een host zonder persistente disk (bv. Render's gratis webservice-plan).
Zonder DATABASE_URL (lokaal ontwikkelen) val je automatisch terug op platte
JSON-bestanden, zodat je niet voor elke test een Postgres-server nodig hebt.
"""
import hashlib
import json
import os
import re
import time
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SUBMISSIONS_FILE = "submissions_db.json"
GALLERY_FILE = "gallery_db.json"
REVIEWS_FILE = "reviews_db.json"
TOKENS_FILE = "tokens_db.json"
DOCENT_TOKEN_FILE = "docent_token.json"
TOERNOOI_RESULTATEN_FILE = "toernooi_resultaten_db.json"
DATACAMP_FILE = "datacamp_db.json"

security_bearer = HTTPBearer()

DATABASE_URL = os.environ.get("DATABASE_URL")


if DATABASE_URL:
    import psycopg

    def _connectie():
        # Render's DATABASE_URL gebruikt het schema "postgres://", psycopg wil "postgresql://".
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        return psycopg.connect(url, autocommit=True)

    def _zorg_voor_tabel():
        with _connectie() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL
                )
                """
            )

    _zorg_voor_tabel()

    def _laad(sleutel: str) -> dict:
        with _connectie() as conn:
            rij = conn.execute("SELECT value FROM kv_store WHERE key = %s", (sleutel,)).fetchone()
            return rij[0] if rij else {}

    def _sla_op(sleutel: str, data: dict):
        with _connectie() as conn:
            conn.execute(
                """
                INSERT INTO kv_store (key, value) VALUES (%s, %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                """,
                (sleutel, json.dumps(data)),
            )

else:

    def _laad(sleutel: str) -> dict:
        if os.path.exists(sleutel):
            with open(sleutel, "r") as f:
                return json.load(f)
        return {}

    def _sla_op(sleutel: str, data: dict):
        with open(sleutel, "w") as f:
            json.dump(data, f, indent=2)


def laad_submissions() -> dict:
    """
    Vorm: {week: {student_id: [inzending, inzending, ...]}}.

    Elke keer dat een student iets inlevert, wordt er een nieuwe inzending
    AAN de lijst toegevoegd — eerdere pogingen worden nooit overschreven of
    weggegooid. Overal waar je "de" inzending van een student nodig hebt
    (status, docent-export, toernooi, locaties), gebruik je nieuwste_inzending()
    hieronder, die gewoon de laatste van de lijst pakt.
    """
    return _laad(SUBMISSIONS_FILE)


def sla_submissions_op(data: dict):
    _sla_op(SUBMISSIONS_FILE, data)


def nieuwste_inzending(inzendingen: list) -> dict | None:
    """Laatste (= meest recente) inzending uit een lijst, of None als er nog geen is."""
    return inzendingen[-1] if inzendingen else None


def laad_gallery() -> dict:
    return _laad(GALLERY_FILE)


def sla_gallery_op(data: dict):
    _sla_op(GALLERY_FILE, data)


def laad_reviews() -> dict:
    return _laad(REVIEWS_FILE)


def sla_reviews_op(data: dict):
    _sla_op(REVIEWS_FILE, data)


def laad_datacamp() -> dict:
    """
    Vorm: {"laatste": "2026-09-08", "snapshots": {"2026-09-08": {...}}}.

    Eén sleutel per peildatum, zodat je later kunt terugkijken hoe de klas er
    halverwege het blok voor stond -- handig bij een discussie over "ik had het
    wél gedaan". De snapshots zijn klein (een dict per student), dus alle tien
    blokweken passen ruim in één kv-regel.
    """
    return _laad(DATACAMP_FILE)


def sla_datacamp_op(data: dict):
    _sla_op(DATACAMP_FILE, data)


def bootstrap_geheimen_uit_omgeving():
    """
    Op een host zonder shell-toegang (bv. Render's gratis webservice-plan) is
    er geen manier om handmatig tokens neer te zetten — die staan bewust in
    .gitignore, dus ze bestaan nergens totdat je ze zet. De omgevingsvariabelen
    POKER_TOKENS_JSON en POKER_DOCENT_TOKEN zijn daarom de bron van waarheid:
    bij ELKE opstart wordt de opgeslagen data overschreven met wat er in de
    env var staat (als die gezet is).

    Bewust GEEN "alleen als het nog leeg is"-check: als je de studentenlijst
    op Render bijwerkt en de service herstart, moet dat ook echt effect
    hebben. Zonder dit zou een eerder gezette (bv. test-)lijst voor altijd
    blijven hangen, ook nadat je de env var wijzigt — precies dat gebeurde
    met de eerste testtokens uit de ontwikkelfase.

    Een kapotte env var (bv. een verminkte JSON-paste) mag nooit de hele API
    platleggen — dat gebeurde hier wél, want een JSONDecodeError in een
    FastAPI-startup-handler laat de héle applicatie stoppen (Render's
    "Application startup failed. Exiting."), voor alle endpoints, voor
    iedereen. Daarom vangen we een ongeldige POKER_TOKENS_JSON hier af: de
    API start gewoon door met de tokens die er al waren (of leeg, als er nog
    nooit een geldige gezet is), en de fout verschijnt in de logs in plaats
    van de hele service mee te trekken.
    """
    ruwe_tokens = os.environ.get("POKER_TOKENS_JSON")
    if ruwe_tokens:
        try:
            tokens = json.loads(ruwe_tokens)
        except json.JSONDecodeError as e:
            print(f"WAARSCHUWING: POKER_TOKENS_JSON is geen geldige JSON, tokens NIET bijgewerkt ({e}).")
        else:
            _sla_op(TOKENS_FILE, tokens)

    docent_token = os.environ.get("POKER_DOCENT_TOKEN")
    if docent_token:
        _sla_op(DOCENT_TOKEN_FILE, {"docent_token": docent_token})


def laad_tokens() -> dict:
    return _laad(TOKENS_FILE)


_TOERNOOI_SLEUTEL = re.compile(r"^[A-Za-z0-9_]+$")


def _toernooi_bestand(cache_key: str) -> str:
    """
    De opslagsleutel van één toernooironde.

    De cache_key wordt een bestandsnaam (of een primary key in Postgres), dus
    hij mag alleen letters, cijfers en underscores bevatten. In de praktijk
    komt hij uit toernooi_runner._cache_sleutel() en is hij opgebouwd uit
    weeknummers en vaste woorden, maar dat wil je niet hoeven vertrouwen op de
    plek waar er een pad van gemaakt wordt.
    """
    if not _TOERNOOI_SLEUTEL.match(cache_key):
        raise ValueError(f"Ongeldige toernooi-cachesleutel: {cache_key!r}")
    return f"toernooi_ronde_{cache_key}.json"


def laad_toernooi_resultaat(cache_key: str) -> dict | None:
    """
    Eén toernooironde, of None als die nog niet gedraaid is.

    Elke ronde staat apart. Dat moet ook: met 20 simulaties is het hand-log van
    één ronde in de bonusweek bijna 5 MB, en toen alle rondes van alle weken nog
    samen in één blob zaten werd die hele blob gelezen én herschreven bij elke
    aanroep -- ook bij een cache-hit, en ook voor de bonusberekening. Drie rondes
    in week 5 plus de eerdere weken tikte dat op naar tientallen megabytes per
    request.

    Rondes die nog onder de oude, gebundelde sleutel staan worden hier gewoon
    gevonden: bestaande uitslagen blijven dus leesbaar, en zodra een ronde
    opnieuw wordt weggeschreven staat hij apart.
    """
    resultaat = _laad(_toernooi_bestand(cache_key))
    if resultaat:
        return resultaat
    return _laad(TOERNOOI_RESULTATEN_FILE).get(cache_key)


def sla_toernooi_resultaat_op(cache_key: str, resultaat: dict):
    _sla_op(_toernooi_bestand(cache_key), resultaat)


def anonimiseer_id(student_id: str, week: int) -> str:
    """
    Maakt een niet-terugleidbaar ID voor de Streamlit peer-review hub.
    Zelfde student+week geeft altijd hetzelfde anon_id (nodig om dubbele
    reviews en zelf-review te kunnen blokkeren), maar het ID onthult de
    student_id niet.
    """
    ruw = f"{student_id}-week{week}-poker-analytics-salt"
    return hashlib.sha256(ruw.encode()).hexdigest()[:12]


MAX_MISLUKTE_POGINGEN = 5
LOCKOUT_SECONDEN = 60

# In-memory, niet naar schijf — dit is een korte rate-limit-teller, geen
# permanente data. Reset bij een herstart van de API, en dat is prima: het
# doel is een geautomatiseerd script afremmen, niet elke poging ooit onthouden.
_mislukte_pogingen: dict[str, list[float]] = {}
_mislukte_docent_pogingen: list[float] = []


def _recente_pogingen(pogingen: list[float]) -> list[float]:
    nu = time.time()
    return [t for t in pogingen if nu - t < LOCKOUT_SECONDEN]


def _is_student_geblokkeerd(student_id: str) -> bool:
    return len(_recente_pogingen(_mislukte_pogingen.get(student_id, []))) >= MAX_MISLUKTE_POGINGEN


def _registreer_mislukte_studentpoging(student_id: str):
    pogingen = _recente_pogingen(_mislukte_pogingen.get(student_id, []))
    pogingen.append(time.time())
    _mislukte_pogingen[student_id] = pogingen


def verifieer_student_token(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
):
    """
    Controleert of het meegestuurde Bearer-token bij dit student_id hoort.

    Na te veel mislukte pogingen op rij (bv. een script dat alle 52
    kaartnamen afgaat) wordt dit specifieke student_id tijdelijk geblokkeerd.
    De foutmelding is voor elke reden van falen identiek — of het student_id
    onbekend is, of het token onjuist — zodat een aanvaller niet kan afleiden
    welke studentnummers echt bestaan.
    """
    if _is_student_geblokkeerd(student_id):
        raise HTTPException(
            status_code=429,
            detail=f"Te veel mislukte pogingen voor dit student_id. Probeer over {LOCKOUT_SECONDEN} seconden opnieuw.",
        )

    tokens = laad_tokens()
    token = credentials.credentials

    if student_id not in tokens or tokens[student_id] != token:
        _registreer_mislukte_studentpoging(student_id)
        raise HTTPException(status_code=401, detail="Onbekend student_id of onjuist token.")

    _mislukte_pogingen.pop(student_id, None)
    return True


def verifieer_docent_token(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
):
    """Voor de docent-only export-endpoints. Dezelfde rate-limit, één gedeelde teller."""
    global _mislukte_docent_pogingen
    _mislukte_docent_pogingen = _recente_pogingen(_mislukte_docent_pogingen)
    if len(_mislukte_docent_pogingen) >= MAX_MISLUKTE_POGINGEN:
        raise HTTPException(
            status_code=429,
            detail=f"Te veel mislukte pogingen. Probeer over {LOCKOUT_SECONDEN} seconden opnieuw.",
        )

    docent_data = _laad(DOCENT_TOKEN_FILE)
    verwacht_token = docent_data.get("docent_token")
    if not verwacht_token or credentials.credentials != verwacht_token:
        _mislukte_docent_pogingen.append(time.time())
        raise HTTPException(status_code=401, detail="Geen geldig docent-token.")

    _mislukte_docent_pogingen = []
    return True
