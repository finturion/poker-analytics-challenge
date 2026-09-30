"""
Poker Analytics Challenge — Inlever-API

Doel: nul handmatige nakijkdruk voor de docent.
- POST /submit          -> technische check van bot-code + grafiek-JSON
- GET  /gallery/{week}  -> anonieme grafieken voor de Streamlit peer-review hub
- POST /peer-review     -> student beoordeelt 3 anonieme grafieken op Visual Hierarchy
- GET  /status/{...}    -> voldaan/niet-voldaan (submission technisch ok + 3 reviews gegeven)
- GET  /export/{week}   -> docent-only voortgangsexport, geen los nakijkwerk nodig
- GET  /export/{week}/bots -> docent-only: de ingeleverde bot-code, om lokaal mee te draaien
- GET  /toernooi/{week} -> echt pokertoernooi (PyPokerEngine) tussen alle goedgekeurde bots
- POST /toernooi/{week}/opnieuw -> docent-only: forceer een nieuwe toernooi-run
- GET  /toernooi/{week}/resultaat -> docent-only: laatst gecachte uitslag, draait NOOIT zelf een toernooi
- GET  /locaties/{week} -> geolocaties van alle bots (vanaf Week 5), met eindstand indien bekend
- POST /bot-test/{student_id} -> test de bot van een klasgenoot op je eigen situaties (geen code)
- GET  /referentiebots/{week} -> de vaste meetlat-bots: altijd hun beschrijving, vanaf Week 5 ook hun code
- GET  /bonus/{student_id} -> student ziet zijn EIGEN bonuspunt met de opbouw per week
- GET  /bonus            -> docent-only: de bonus van de hele klas
- POST /datacamp/snapshot -> docent-only: wekelijkse DataCamp-voortgang wegschrijven
- GET  /datacamp/overzicht -> docent-only: hele klas langs de roosterdeadlines, incl. achterblijvers
- GET  /datacamp/stand/{student_id} -> student ziet zijn EIGEN DataCamp-stand + anoniem klasgemiddelde
- GET  /versie          -> welke commit draait er, en sinds wanneer (openbaar, geen token)

Start lokaal met:  uvicorn main:app --reload
"""
import os
import random
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

import database as db
import datacamp_rooster as rooster
from bonus_rooster import (
    BONUSWEEK,
    GESCOORDE_RONDES,
    MAX_BONUS,
    bonus_hele_klas,
    bonus_per_student,
    puntentabel,
)
from bot_validator import MAX_TESTGEVALLEN_PEER, speel_testgevallen, valideer_bot_code
from referentiebots import beschrijvingen as referentie_beschrijvingen
from referentiebots import OPENBAAR_VANAF_WEEK, broncode as referentie_broncode
from chart_validator import valideer_chart_json
from locatie_validator import valideer_locatie
from toernooi_runner import (cache_sleutel, draai_toernooi, haal_gecacht_resultaat_op,
                             laatste_gedraaide_ronde)

WEEK_VANAF_LOCATIE_VERPLICHT = 5

app = FastAPI(title="Poker Analytics Challenge API")



@app.exception_handler(Exception)
def alles_wat_misgaat_blijft_json(verzoek: Request, fout: Exception):
    """
    Een onverwachte fout mag nooit als kale tekst terugkomen.

    Studenten roepen deze API aan met requests.get(...).json(). Kwam er dan
    "Internal Server Error" als text/plain uit, dan kregen ze een JSONDecodeError
    diep uit de json-module -- een foutmelding die niets zegt over wat er echt
    misging en waar ze zelf niets mee kunnen. Dat gebeurde op 30 september 2026
    op /toernooi/5, en het kostte meer tijd om te vinden dan de oorzaak waard was.

    Nu komt er altijd JSON terug, met het type fout erin zodat de docent er iets
    aan heeft. Geen traceback: die hoort in de serverlog, niet in een notebook.
    """
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Er ging iets mis op de server. Probeer het zo nog eens; "
                      "blijft het gebeuren, meld het bij je docent.",
            "soort": type(fout).__name__,
        },
    )


@app.on_event("startup")
def _bij_opstarten():
    db.bootstrap_geheimen_uit_omgeving()


# Het moment waarop dit proces begon. Verandert alleen bij een herstart, en een
# deploy is een herstart -- dus dit is het antwoord op "staat mijn fix er al op?".
_GESTART = datetime.now(timezone.utc)


@app.get("/versie")
def versie():
    """
    Welke commit draait hier, en sinds wanneer.

    Openbaar en zonder token, want anders is hij nutteloos voor precies het geval
    waarvoor hij bestaat: net gepusht, en je wilt weten of Render het al heeft
    opgepikt. Hij geeft niets prijs -- de commit-hash staat ook gewoon op GitHub.

    Aanleiding: in september 2026 stond er een fix klaar voor een KeyError bij het
    inleveren, en er was geen enkele manier om van buitenaf te zien of die al live
    stond. Een draaiende oude versie antwoordt op elk ander endpoint precies
    hetzelfde als een draaiende nieuwe.

    RENDER_GIT_COMMIT zet Render zelf klaar. Lokaal is die er niet; dan proberen
    we git, en anders staat er "onbekend" -- geen foutmelding, want dit endpoint
    mag nooit de reden zijn dat de API niet start.
    """
    commit = os.environ.get("RENDER_GIT_COMMIT") or _commit_uit_git() or "onbekend"
    draait_al = datetime.now(timezone.utc) - _GESTART
    return {
        "commit": commit,
        "kort": commit[:7] if commit != "onbekend" else commit,
        "branch": os.environ.get("RENDER_GIT_BRANCH") or "onbekend",
        "gestart": _GESTART.isoformat(),
        "draait_al_seconden": int(draait_al.total_seconds()),
    }


def _commit_uit_git():
    """Alleen voor lokaal draaien. Op Render staat RENDER_GIT_COMMIT al klaar."""
    import subprocess
    try:
        uit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, timeout=2,
                             cwd=os.path.dirname(os.path.abspath(__file__)))
        return uit.stdout.strip() or None
    except Exception:
        return None

MIN_REVIEWS_VOOR_VOLDAAN = 3
GALLERY_STEEKPROEF = 3


# ---------------------------------------------------------------------------
# Modellen
# ---------------------------------------------------------------------------
class Submission(BaseModel):
    week: int = Field(..., description="1, 3 of 5")
    bot_code: str
    chart: dict
    # Sinds september 2026 optioneel en nergens meer voor nodig. Het veld blijft
    # bestaan zodat oude inzendingen en bots die het in hun handtekening hebben
    # blijven werken.
    strategie: str | None = Field(None, description="Optioneel: tight, loose, balanced of aggressive. "
                                                    "Je bot krijgt hem terug als hij erom vraagt.")
    bluf_kans: float | None = Field(None, description="Verplicht vanaf Week 5: kans tussen 0 en 1")
    locatie: dict | None = Field(
        None, description="Verplicht vanaf Week 5: {'lat': float, 'lon': float, 'plaatsnaam': str}"
    )


class PeerReview(BaseModel):
    """
    Elk criterium heeft nu zowel een score als een verplichte toelichting.
    Een score alleen ("3") vertelt de indiener niet wát er beter kan; de
    toelichting is waar het leereffect van peer review vandaan komt.
    """

    week: int
    anon_id: str = Field(..., description="anon_id van de te beoordelen grafiek, uit /gallery")
    focal_point_score: int = Field(..., ge=1, le=5)
    focal_point_opmerking: str = Field(..., min_length=1)
    kleur_contrast_score: int = Field(..., ge=1, le=5)
    kleur_contrast_opmerking: str = Field(..., min_length=1)
    actietitel_score: int = Field(..., ge=1, le=5)
    actietitel_opmerking: str = Field(..., min_length=1)


class DataCampStudent(BaseModel):
    studentnummer: str
    naam: str | None = None
    team: str | None = None
    klas: str | None = None
    datacamp_email: str | None = None
    xp: int = 0
    chapters: int = 0
    courses: dict[str, str] = Field(
        default_factory=dict, description="{course-titel: afrondingsdatum YYYY-MM-DD}"
    )


class DataCampSnapshot(BaseModel):
    """Ruwe feiten uit DataCamp; het beoordelen gebeurt in datacamp_rooster.py."""

    opgehaald_op: str = Field(..., description="ISO-datum(tijd) van de scrape")
    studenten: list[DataCampStudent]
    zonder_account: list[str] = Field(
        default_factory=list, description="Namen uit de klaslijst zonder DataCamp-account"
    )
    niet_gekoppeld: list[str] = Field(
        default_factory=list, description="DataCamp-e-mails die niet aan een studentnummer te koppelen zijn"
    )


class BotTestVerzoek(BaseModel):
    """Een setje situaties waarop je de bot van een klasgenoot wil zien reageren."""
    week: int
    van_student_id: str
    testgevallen: list[dict]


# ---------------------------------------------------------------------------
# Inleveren
# ---------------------------------------------------------------------------
@app.post("/submit/{student_id}")
def inleveren(
    student_id: str,
    inzending: Submission,
    ok: bool = Depends(db.verifieer_student_token),
):
    bot_resultaat = valideer_bot_code(
        inzending.bot_code, inzending.week, strategie=inzending.strategie, bluf_kans=inzending.bluf_kans
    )
    chart_resultaat = valideer_chart_json(inzending.chart)

    locatie_verplicht = inzending.week >= WEEK_VANAF_LOCATIE_VERPLICHT
    if locatie_verplicht or inzending.locatie is not None:
        locatie_resultaat = valideer_locatie(inzending.locatie)
    else:
        locatie_resultaat = {"geldig": True, "problemen": []}

    geldig = bot_resultaat["geldig"] and chart_resultaat["geldig"] and locatie_resultaat["geldig"]

    submissions = db.laad_submissions()
    week_key = str(inzending.week)
    submissions.setdefault(week_key, {})
    submissions[week_key].setdefault(student_id, [])
    # Aanvullen, nooit overschrijven: je mag zo vaak opnieuw inleveren als je
    # wilt, en elke eerdere poging blijft bewaard. Alleen de laatste poging
    # telt mee voor status/toernooi/gallery (zie db.nieuwste_inzending()).
    submissions[week_key][student_id].append(
        {
            "bot_code": inzending.bot_code,
            "chart": inzending.chart,
            "strategie": inzending.strategie,
            "bluf_kans": inzending.bluf_kans,
            "locatie": inzending.locatie,
            "bot_check": bot_resultaat,
            "chart_check": chart_resultaat,
            "locatie_check": locatie_resultaat,
            "geldig": geldig,
            "ingeleverd_op": datetime.now(timezone.utc).isoformat(),
        }
    )
    db.sla_submissions_op(submissions)

    if geldig:
        anon_id = db.anonimiseer_id(student_id, inzending.week)
        gallery = db.laad_gallery()
        gallery.setdefault(week_key, {})
        gallery[week_key][anon_id] = {
            "chart": inzending.chart,
            "_student_id": student_id,  # intern nodig om zelf-review te blokkeren, nooit publiek serveren
        }
        db.sla_gallery_op(gallery)

    if geldig:
        boodschap = "Ingeleverd en technisch goedgekeurd. Je grafiek staat nu klaar voor peer-review."
        if bot_resultaat.get("constante_bot"):
            # Geen afkeuring: dit mág. Maar de student hoort te weten dat zijn
            # bot bij elke testhand hetzelfde doet, want in het toernooi
            # verliest zo'n bot chips die hij in de volgende ronde mist.
            boodschap += (
                " Let op: je bot geeft bij elke testhand dezelfde actie terug —"
                " hij kijkt dus niet naar zijn kaarten of zijn stack."
            )
    else:
        boodschap = "Ingeleverd, maar nog niet goedgekeurd — los de problemen hieronder op en lever opnieuw in."

    return {
        "geldig": geldig,
        "poging_nummer": len(submissions[week_key][student_id]),
        "bot_check": bot_resultaat,
        "chart_check": chart_resultaat,
        "locatie_check": locatie_resultaat,
        "boodschap": boodschap,
    }


# ---------------------------------------------------------------------------
# Streamlit peer-review hub
# ---------------------------------------------------------------------------
@app.get("/gallery/{week}")
def gallery(week: int, student_id: str, ok: bool = Depends(db.verifieer_student_token)):
    """Geeft een willekeurige steekproef van anonieme grafieken, exclusief die van de student zelf."""
    week_key = str(week)
    gallery_data = db.laad_gallery().get(week_key, {})
    reviews_gegeven = {
        r["anon_id"] for r in db.laad_reviews().get(week_key, {}).get(student_id, [])
    }

    kandidaten = [
        {"anon_id": anon_id, "chart": info["chart"]}
        for anon_id, info in gallery_data.items()
        if info["_student_id"] != student_id and anon_id not in reviews_gegeven
    ]
    random.shuffle(kandidaten)
    return kandidaten[:GALLERY_STEEKPROEF]


@app.post("/peer-review/{student_id}")
def peer_review(student_id: str, review: PeerReview, ok: bool = Depends(db.verifieer_student_token)):
    week_key = str(review.week)
    gallery_data = db.laad_gallery().get(week_key, {})

    if review.anon_id not in gallery_data:
        raise HTTPException(status_code=404, detail="Onbekend anon_id voor deze week.")
    if gallery_data[review.anon_id]["_student_id"] == student_id:
        raise HTTPException(status_code=400, detail="Je kan je eigen grafiek niet beoordelen.")

    reviews = db.laad_reviews()
    reviews.setdefault(week_key, {})
    reviews[week_key].setdefault(student_id, [])

    if any(r["anon_id"] == review.anon_id for r in reviews[week_key][student_id]):
        raise HTTPException(status_code=400, detail="Je hebt deze grafiek al beoordeeld.")

    reviews[week_key][student_id].append(
        {
            "anon_id": review.anon_id,
            "focal_point_score": review.focal_point_score,
            "focal_point_opmerking": review.focal_point_opmerking,
            "kleur_contrast_score": review.kleur_contrast_score,
            "kleur_contrast_opmerking": review.kleur_contrast_opmerking,
            "actietitel_score": review.actietitel_score,
            "actietitel_opmerking": review.actietitel_opmerking,
            "beoordeeld_op": datetime.now(timezone.utc).isoformat(),
        }
    )
    db.sla_reviews_op(reviews)

    aantal = len(reviews[week_key][student_id])
    return {
        "opgeslagen": True,
        "reviews_gegeven": aantal,
        "nog_nodig": max(0, MIN_REVIEWS_VOOR_VOLDAAN - aantal),
    }


# ---------------------------------------------------------------------------
# Status (voldaan / niet voldaan) en docent-export
# ---------------------------------------------------------------------------
@app.get("/status/{student_id}/{week}")
def status(student_id: str, week: int, ok: bool = Depends(db.verifieer_student_token)):
    """Kijkt altijd naar je MEEST RECENTE inzending — eerdere pogingen tellen niet mee, maar blijven bewaard."""
    week_key = str(week)
    inzendingen = db.laad_submissions().get(week_key, {}).get(student_id, [])
    submission = db.nieuwste_inzending(inzendingen)
    reviews_gegeven = len(db.laad_reviews().get(week_key, {}).get(student_id, []))

    technisch_ok = bool(submission and submission["geldig"])
    voldaan = technisch_ok and reviews_gegeven >= MIN_REVIEWS_VOOR_VOLDAAN

    return {
        "week": week,
        "ingeleverd": submission is not None,
        "aantal_pogingen": len(inzendingen),
        "technisch_goedgekeurd": technisch_ok,
        "reviews_gegeven": reviews_gegeven,
        "reviews_nodig": MIN_REVIEWS_VOOR_VOLDAAN,
        "voldaan": voldaan,
    }


@app.get("/toernooi/{week}")
def toernooi(
    week: int,
    student_id: str,
    vergelijk_met_week: int | None = None,
    ronde: int | None = None,
    formatief: bool = False,
    ok: bool = Depends(db.verifieer_student_token),
):
    """
    Laat alle technisch goedgekeurde bots van deze week echt tegen elkaar
    spelen (PyPokerEngine), verdeeld over meerdere tafels en simulaties.
    De eerste aanroep draait het toernooi en cachet het resultaat; latere
    aanroepen (van andere studenten) krijgen dezelfde uitslag terug.

    Geef `vergelijk_met_week` mee om twee weken in één toernooi te combineren
    (bv. Week 3 vs. Week 1): elke bot-naam wordt dan "student_id__w{week}",
    zodat je eigen oude en nieuwe bot naast elkaar in dezelfde uitslag staan.

    Met `ronde` draai je meerdere toernooien in dezelfde week zonder dat ze
    elkaars uitslag overschrijven. Ronde 1 is de woensdag-run.

    Elke ronde begint schoon op 1000, ook in de bonusweek. Zo meet elke ronde
    alleen de bot die op dat moment is ingeleverd.

    `formatief=true` draait een repetitie van die ronde: met de bots van dit
    moment, en weggeschreven onder een eigen sleutel.
    Bedoeld voor de oefenronde op donderdag in week 5 -- die telt niet mee voor
    de bonus en verschuift de vrijdaguitslag niet.

    Laat je `ronde` weg, dan krijg je de LAATST GEDRAAIDE ronde van deze week
    terug, en pas als er nog helemaal niets is gedraaid begint er een nieuwe
    ronde 1. Dat stond eerst hard op 1, en dat pakte slecht uit: draaide de
    docent zijn toernooi onder een ander rondenummer, dan startte élke student
    die zijn notebook uitvoerde een eigen run van twintig minuten op een lege
    ronde 1 -- en kreeg daar een timeout voor terug.

    hand_log kun je direct in een DataFrame zetten: pd.DataFrame(response.json()["hand_log"])
    """
    if ronde is None:
        ronde = laatste_gedraaide_ronde(week, vergelijk_met_week) or 1
    return draai_toernooi(week, vergelijk_met_week=vergelijk_met_week, ronde=ronde, formatief=formatief)


@app.post("/toernooi/{week}/opnieuw")
def toernooi_opnieuw(
    week: int,
    vergelijk_met_week: int | None = None,
    ronde: int = 1,
    formatief: bool = False,
    ok: bool = Depends(db.verifieer_docent_token),
):
    """Docent-only: forceer een nieuwe toernooi-run (bv. na te late inzendingen)."""
    return draai_toernooi(
        week,
        vergelijk_met_week=vergelijk_met_week,
        forceer_opnieuw=True,
        ronde=ronde,
        formatief=formatief,
    )


@app.get("/toernooi/{week}/resultaat")
def toernooi_resultaat_ophalen(
    week: int,
    vergelijk_met_week: int | None = None,
    ronde: int = 1,
    formatief: bool = False,
    ok: bool = Depends(db.verifieer_docent_token),
):
    """
    Docent-only: haal de laatst gecachte toernooi-uitslag op, ZONDER ooit
    zelf een toernooi te starten. Voor de docent die tussendoor even wil
    zien hoe de klas ervoor staat, zonder de (mogelijk voor iedereen net
    goede) bestaande uitslag te overschrijven met een nieuwe run.
    """
    return haal_gecacht_resultaat_op(
        week, vergelijk_met_week=vergelijk_met_week, ronde=ronde, formatief=formatief
    )


@app.get("/locaties/{week}")
def locaties(
    week: int,
    student_id: str,
    ronde: int | None = None,
    ok: bool = Depends(db.verifieer_student_token),
):
    """
    Geolocatie van elke technisch goedgekeurde bot, met de eindstand erbij
    zodra het toernooi van deze week gedraaid is (anders eindstand: null —
    je krijgt dan wel alle posities, maar nog geen winst/verlies-kleur).

    `ronde` hoort erbij om dezelfde reden als bij /toernooi: week 5 draait twee
    toernooien die meetellen, en die staan onder eigen sleutels. Zonder deze
    parameter kwam hier altijd de eindstand van de woensdagronde uit, ook in
    Week 6 waar de kaart juist de eindstand van de hele reeks moet laten zien.
    Ronde 1 blijft de standaard, zodat Werkcollege 8 (de woensdagkaart)
    ongewijzigd blijft werken.
    """
    week_key = str(week)
    submissions = db.laad_submissions().get(week_key, {})
    # Zonder rondenummer: de laatst gedraaide ronde, net als bij /toernooi.
    # Stond hier hard op 1, en dan bleef de kaart grijs zodra de docent onder een
    # ander rondenummer had gedraaid -- terwijl de eindstanden gewoon bestonden.
    if ronde is None:
        ronde = laatste_gedraaide_ronde(week) or 1
    resultaat_sleutel = cache_sleutel(week, ronde=ronde)
    eindstand_per_bot = (db.laad_toernooi_resultaat(resultaat_sleutel) or {}).get("eindstand_per_bot", {})

    resultaat = []
    for bot_student_id, inzendingen in submissions.items():
        submission = db.nieuwste_inzending(inzendingen)
        if not submission or not submission.get("geldig") or not submission.get("locatie"):
            continue
        resultaat.append(
            {
                "student_id": bot_student_id,
                "ronde": ronde,
                "lat": submission["locatie"]["lat"],
                "lon": submission["locatie"]["lon"],
                "plaatsnaam": submission["locatie"]["plaatsnaam"],
                "eindstand": eindstand_per_bot.get(bot_student_id),
            }
        )
    return resultaat


@app.get("/export/{week}")
def export(week: int, ok: bool = Depends(db.verifieer_docent_token)):
    """Docent-only: overzicht per student, zonder dat er handmatig nagekeken hoeft te worden."""
    week_key = str(week)
    submissions = db.laad_submissions().get(week_key, {})
    reviews = db.laad_reviews().get(week_key, {})

    overzicht = []
    for student_id, inzendingen in submissions.items():
        submission = db.nieuwste_inzending(inzendingen)
        if submission is None:
            continue
        reviews_gegeven = len(reviews.get(student_id, []))
        overzicht.append(
            {
                "student_id": student_id,
                "aantal_pogingen": len(inzendingen),
                "technisch_goedgekeurd": submission["geldig"],
                # Geen afkeuring, wel zichtbaar: deze bot doet bij elke testhand
                # hetzelfde en kijkt dus niet naar kaarten of stack.
                "constante_bot": submission.get("bot_check", {}).get("constante_bot", False),
                "reviews_gegeven": reviews_gegeven,
                "voldaan": submission["geldig"] and reviews_gegeven >= MIN_REVIEWS_VOOR_VOLDAAN,
                "laatst_ingeleverd_op": submission["ingeleverd_op"],
            }
        )
    return overzicht


@app.get("/export/{week}/bots")
def export_bots(week: int, ok: bool = Depends(db.verifieer_docent_token)):
    """
    Docent-only: de ingeleverde bot-code van alle studenten van deze week.

    WAAROM DIT BESTAAT, EN WAAROM ALLEEN VOOR DE DOCENT
    ---------------------------------------------------
    Studenten kunnen elkaars code met opzet niet opvragen: /bot-test geeft
    gedrag terug en geen broncode, juist omdat er een bonuspunt aan het toernooi
    hangt. Die regel blijft. Maar de docent moet er wél bij kunnen -- om na te
    kijken, om een crash te onderzoeken, en om het toernooi lokaal te draaien.

    Dat laatste is de directe aanleiding. Sinds Werkcollege 7 rekenen bots hun
    winkans live uit met schat_winkans, en in de bonusweek draaien er twintig
    simulaties. Een toernooi duurt daardoor tientallen minuten, en dat is langer
    dan een HTTP-verbinding het volhoudt. Met deze export haal je de bots op en
    draai je hetzelfde toernooi op je eigen machine -- scripts/draai_toernooi_lokaal.py
    gebruikt dezelfde seed (week * 10 + ronde), dus de uitslag is niet een
    benadering maar identiek aan wat de server zou uitrekenen.

    Alleen de nieuwste inzending per student, want dat is ook wat het toernooi
    speelt. Afgekeurde inzendingen staan er wel bij, met geldig=False, zodat je
    kunt zien wie er is vastgelopen en waarop.
    """
    submissions = db.laad_submissions().get(str(week), {})
    uit = []
    for student_id, inzendingen in submissions.items():
        inzending = db.nieuwste_inzending(inzendingen)
        if inzending is None:
            continue
        uit.append({
            "student_id": student_id,
            "bot_code": inzending["bot_code"],
            "strategie": inzending.get("strategie"),
            "bluf_kans": inzending.get("bluf_kans"),
            "geldig": inzending["geldig"],
            "foutmelding": inzending.get("foutmelding"),
            "ingeleverd_op": inzending["ingeleverd_op"],
        })
    return sorted(uit, key=lambda r: r["student_id"])


@app.get("/referentiebots/{week}")
def referentiebots(week: int, student_id: str, ok: bool = Depends(db.verifieer_student_token)):
    """
    De referentiebots die deze week meespelen: een vaste meetlat.

    Ze veranderen nooit, dus "ik zit boven de pot-odds-bot" betekent elke week
    hetzelfde — anders dan je plek in de klas, die meebeweegt met wat iedereen
    inlevert. Ze spelen echt mee in het toernooi en beïnvloeden de chips, maar ze
    staan niet in de puntenladder: die wordt alleen over studenten gerekend.

    Hun beschrijving en niveau zijn altijd zichtbaar — een meetlat waarvan je niet
    weet wat hij doet is geen meetlat. De broncode komt er vanaf Week 5 bij, als de
    pokerlijn afrondt: dan valt er nog van te leren voor je slotinzending, en het
    kost niemand een bonuspunt want het is docentcode.
    """
    return {
        "week": week,
        "bots": referentie_beschrijvingen(week),
        "broncode_openbaar_vanaf_week": OPENBAAR_VANAF_WEEK,
        "broncode": referentie_broncode(week),
    }


@app.post("/bot-test/{student_id}")
def bot_test(
    student_id: str,
    verzoek: BotTestVerzoek,
    ok: bool = Depends(db.verifieer_student_token),
):
    """
    Test de bot van een klasgenoot op situaties die JIJ bedenkt.

    Je stuurt een lijstje testgevallen in (elk minstens een `hand`, en verder
    wat je wil: `stack`, `ronde`, `pot`, `inzet_om_te_callen`,
    `tegenstander_acties_deze_hand`) en krijgt terug wat die bot daarop doet.

    Wat je NIET terugkrijgt is zijn code. Dat is een bewuste keuze: er hangt een
    bonuspunt aan het toernooi, en een endpoint dat andermans bot uitdeelt maakt
    die competitie kopieerbaar. Je ziet gedrag, en gedrag is precies wat je wil
    vergelijken -- dezelfde situaties, twee bots, verschillende antwoorden.

    De `strategie` en `bluf_kans` waarmee getest wordt zijn die van zijn eigen
    inzending, niet die van jou. Parameters die zijn functie niet accepteert
    worden weggelaten, net als in het echte toernooi.

    Maximaal MAX_TESTGEVALLEN_PEER situaties per aanvraag.
    """
    inzendingen = db.laad_submissions().get(str(verzoek.week), {}).get(verzoek.van_student_id)
    inzending = db.nieuwste_inzending(inzendingen) if inzendingen else None

    if inzending is None:
        raise HTTPException(
            status_code=404,
            detail=f"Geen inzending gevonden voor {verzoek.van_student_id} in week {verzoek.week}.",
        )
    if not inzending.get("geldig"):
        raise HTTPException(
            status_code=409,
            detail=(f"De laatste inzending van {verzoek.van_student_id} is technisch nog niet "
                    "goedgekeurd, dus er is geen werkende bot om tegen te testen."),
        )

    uitkomst = speel_testgevallen(
        inzending["bot_code"],
        verzoek.week,
        verzoek.testgevallen,
        strategie=inzending.get("strategie"),
        bluf_kans=inzending.get("bluf_kans"),
    )
    if uitkomst["foutmelding"]:
        raise HTTPException(status_code=400, detail=uitkomst["foutmelding"])

    return {
        "van_student_id": verzoek.van_student_id,
        "week": verzoek.week,
        "strategie": inzending.get("strategie"),
        "bluf_kans": inzending.get("bluf_kans"),
        "acties": uitkomst["acties"],
        "gebruikte_parameters": uitkomst["gebruikte_parameters"],
    }


# ---------------------------------------------------------------------------
# Bonuspunten pokerlijn
# ---------------------------------------------------------------------------
def _spelregels() -> dict:
    """Het schema zelf, zodat niemand hoeft te raden hoe de punten tot stand komen."""
    return {
        "maximaal": MAX_BONUS,
        "week": BONUSWEEK,
        "toernooien": [
            {"ronde": ronde, "toernooi": omschrijving}
            for ronde, omschrijving in sorted(GESCOORDE_RONDES.items())
        ],
        "punten_per_plek": puntentabel(),
    }


@app.get("/bonus/{student_id}")
def bonus(student_id: str, ok: bool = Depends(db.verifieer_student_token)):
    """
    Je bonuspunt voor de pokerlijn, met de opbouw erbij.

    In week 5 draaien twee toernooien: één met je woensdagbot en één met je
    definitieve bot. Je plek levert in elk toernooi punten op -- eerste 0,5,
    tweede 0,4, derde 0,3, vierde 0,2, vijfde 0,1, daarna niets. Samen dus
    maximaal 1,0. "spelregels" in het antwoord bevat de hele tabel.

    Een toernooi dat nog niet gedraaid is geeft punten: null -- dat is "nog
    niet bekend", geen nul.
    """
    resultaat = bonus_per_student(student_id, db.laad_toernooi_resultaat)
    return {**resultaat, "spelregels": _spelregels()}


@app.get("/bonus")
def bonus_overzicht(ok: bool = Depends(db.verifieer_docent_token)):
    """Docent-only: de bonus van de hele klas, hoogste eerst, met de opbouw per week."""
    return {
        **_spelregels(),
        "studenten": bonus_hele_klas(db.laad_submissions(), db.laad_toernooi_resultaat),
    }


# ---------------------------------------------------------------------------
# DataCamp-voortgang
# ---------------------------------------------------------------------------
def _laatste_snapshot() -> dict | None:
    data = db.laad_datacamp()
    laatste = data.get("laatste")
    if not laatste:
        return None
    return data.get("snapshots", {}).get(laatste)


@app.post("/datacamp/snapshot")
def datacamp_snapshot_opslaan(snapshot: DataCampSnapshot, ok: bool = Depends(db.verifieer_docent_token)):
    """
    Docent-only: de wekelijkse scrape wegschrijven (scripts/datacamp_snapshot.py).

    Eén snapshot per peildatum. Draai je op dezelfde dag twee keer, dan
    overschrijft de tweede run de eerste -- dat is bedoeld, zo blijft er per
    dag één waarheid staan in plaats van een rij bijna-identieke kopieën.
    """
    data = db.laad_datacamp()
    snapshots = data.get("snapshots", {})
    peildatum = snapshot.opgehaald_op[:10]
    snapshots[peildatum] = snapshot.model_dump()
    db.sla_datacamp_op({"laatste": max(snapshots), "snapshots": snapshots})
    return {"opgeslagen_voor": peildatum, "aantal_studenten": len(snapshot.studenten)}


@app.get("/datacamp/overzicht")
def datacamp_overzicht(ok: bool = Depends(db.verifieer_docent_token)):
    """Docent-only: de hele klas langs de roosterdeadlines, achterstand bovenaan."""
    snapshot = _laatste_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Nog geen DataCamp-snapshot opgeslagen.")

    peildatum = snapshot["opgehaald_op"][:10]
    regels = []
    for student in snapshot["studenten"]:
        vat = rooster.samenvatting(student["courses"], peildatum)
        regels.append(
            {
                "studentnummer": student["studentnummer"],
                "naam": student.get("naam"),
                "team": student.get("team"),
                "klas": student.get("klas"),
                "email": student.get("datacamp_email"),
                "af": vat["af"],
                "van_verstreken": vat["verstreken"],
                "te_laat": vat["te_laat"],
                "gemist": ", ".join(vat["gemist"]),
                "xp": student.get("xp", 0),
                "chapters": student.get("chapters", 0),
            }
        )
    regels.sort(key=lambda r: (-len(r["gemist"].split(", ")) if r["gemist"] else 0, r["af"], -r["xp"]))

    return {
        "peildatum": peildatum,
        "opgehaald_op": snapshot["opgehaald_op"],
        "rooster": rooster.ROOSTER,
        "studenten": regels,
        "achterblijvers": [r for r in regels if r["gemist"]],
        "zonder_account": snapshot.get("zonder_account", []),
        "niet_gekoppeld": snapshot.get("niet_gekoppeld", []),
    }


@app.get("/datacamp/stand/{student_id}")
def datacamp_eigen_stand(student_id: str, ok: bool = Depends(db.verifieer_student_token)):
    """
    De student ziet zijn EIGEN regel plus geanonimiseerde klascijfers.

    Bewust geen namen of e-mails van klasgenoten in het antwoord: de klas mag
    weten hoe de groep ervoor staat, niet wie er achterloopt. Wat een student
    hier ziet, moet hij ook op een scherm in het lokaal mogen zien.
    """
    snapshot = _laatste_snapshot()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Nog geen DataCamp-snapshot opgeslagen.")

    peildatum = snapshot["opgehaald_op"][:10]
    ikzelf = next((s for s in snapshot["studenten"] if s["studentnummer"] == student_id), None)

    alle_af = [rooster.samenvatting(s["courses"], peildatum)["af"] for s in snapshot["studenten"]]
    klas = {
        "aantal_studenten": len(alle_af),
        "gemiddeld_af": round(sum(alle_af) / len(alle_af), 1) if alle_af else 0,
        "verdeling_af": {str(n): alle_af.count(n) for n in sorted(set(alle_af))},
    }

    if ikzelf is None:
        # Geen DataCamp-account gevonden bij dit studentnummer -- dat is zelf
        # het belangrijkste bericht dat deze student kan krijgen.
        return {
            "peildatum": peildatum,
            "gevonden": False,
            "boodschap": (
                "We vinden geen DataCamp-account bij jouw studentnummer. Kijk of je de uitnodiging "
                "voor de groep 'Minor Data Science - 2627 - S1' hebt geaccepteerd, en meld het bij je docent."
            ),
            "klas": klas,
        }

    vat = rooster.samenvatting(ikzelf["courses"], peildatum)
    beter_dan = len([n for n in alle_af if n < vat["af"]])
    return {
        "peildatum": peildatum,
        "gevonden": True,
        "af": vat["af"],
        "totaal": vat["totaal"],
        "van_verstreken": vat["verstreken"],
        "te_laat": vat["te_laat"],
        "gemist": vat["gemist"],
        "aanbevolen_af": vat["aanbevolen_af"],
        "aanbevolen_totaal": vat["aanbevolen_totaal"],
        "xp": ikzelf.get("xp", 0),
        "courses": rooster.status_per_course(ikzelf["courses"], peildatum),
        "klas": {**klas, "jij_staat_boven_percentage": round(100 * beter_dan / len(alle_af)) if alle_af else 0},
    }
