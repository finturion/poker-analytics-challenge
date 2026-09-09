"""
Poker Analytics Challenge — Inlever-API

Doel: nul handmatige nakijkdruk voor de docent.
- POST /submit          -> technische check van bot-code + grafiek-JSON
- GET  /gallery/{week}  -> anonieme grafieken voor de Streamlit peer-review hub
- POST /peer-review     -> student beoordeelt 3 anonieme grafieken op Visual Hierarchy
- GET  /status/{...}    -> voldaan/niet-voldaan (submission technisch ok + 3 reviews gegeven)
- GET  /export/{week}   -> docent-only voortgangsexport, geen los nakijkwerk nodig
- GET  /toernooi/{week} -> echt pokertoernooi (PyPokerEngine) tussen alle goedgekeurde bots
- POST /toernooi/{week}/opnieuw -> docent-only: forceer een nieuwe toernooi-run
- GET  /toernooi/{week}/resultaat -> docent-only: laatst gecachte uitslag, draait NOOIT zelf een toernooi
- GET  /locaties/{week} -> geolocaties van alle bots (vanaf Week 5), met eindstand indien bekend
- GET  /bonus/{student_id} -> student ziet zijn EIGEN bonuspunt met de opbouw per week
- GET  /bonus            -> docent-only: de bonus van de hele klas
- POST /datacamp/snapshot -> docent-only: wekelijkse DataCamp-voortgang wegschrijven
- GET  /datacamp/overzicht -> docent-only: hele klas langs de roosterdeadlines, incl. achterblijvers
- GET  /datacamp/stand/{student_id} -> student ziet zijn EIGEN DataCamp-stand + anoniem klasgemiddelde

Start lokaal met:  uvicorn main:app --reload
"""
import random
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
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
from bot_validator import valideer_bot_code
from chart_validator import valideer_chart_json
from locatie_validator import valideer_locatie
from toernooi_runner import draai_toernooi, haal_gecacht_resultaat_op

WEEK_VANAF_LOCATIE_VERPLICHT = 5

app = FastAPI(title="Poker Analytics Challenge API")


@app.on_event("startup")
def _bij_opstarten():
    db.bootstrap_geheimen_uit_omgeving()

MIN_REVIEWS_VOOR_VOLDAAN = 3
GALLERY_STEEKPROEF = 3


# ---------------------------------------------------------------------------
# Modellen
# ---------------------------------------------------------------------------
class Submission(BaseModel):
    week: int = Field(..., description="1, 3 of 5")
    bot_code: str
    chart: dict
    strategie: str | None = Field(None, description="Verplicht vanaf Week 3: tight, loose, balanced of aggressive")
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
    ronde: int = 1,
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
    elkaars uitslag overschrijven. Ronde 1 is de woensdag-run; vanaf ronde 2
    speelt iedereen door met de chips uit de vorige ronde + 1000 erbij.

    `formatief=true` draait een repetitie van die ronde: dezelfde startstacks,
    maar met de bots van dit moment, en weggeschreven onder een eigen sleutel.
    Bedoeld voor de oefenronde op donderdag in week 5 -- die telt niet mee voor
    de bonus en verschuift de vrijdaguitslag niet.

    hand_log kun je direct in een DataFrame zetten: pd.DataFrame(response.json()["hand_log"])
    """
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
def locaties(week: int, student_id: str, ok: bool = Depends(db.verifieer_student_token)):
    """
    Geolocatie van elke technisch goedgekeurde bot, met de eindstand erbij
    zodra het toernooi van deze week gedraaid is (anders eindstand: null —
    je krijgt dan wel alle posities, maar nog geen winst/verlies-kleur).
    """
    week_key = str(week)
    submissions = db.laad_submissions().get(week_key, {})
    eindstand_per_bot = (db.laad_toernooi_resultaat(week_key) or {}).get("eindstand_per_bot", {})

    resultaat = []
    for bot_student_id, inzendingen in submissions.items():
        submission = db.nieuwste_inzending(inzendingen)
        if not submission or not submission.get("geldig") or not submission.get("locatie"):
            continue
        resultaat.append(
            {
                "student_id": bot_student_id,
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
