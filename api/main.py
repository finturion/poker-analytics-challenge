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
- GET  /locaties/{week} -> geolocaties van alle bots (vanaf Week 5), met eindstand indien bekend

Start lokaal met:  uvicorn main:app --reload
"""
import random
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

import database as db
from bot_validator import valideer_bot_code
from chart_validator import valideer_chart_json
from locatie_validator import valideer_locatie
from toernooi_runner import draai_toernooi

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

    return {
        "geldig": geldig,
        "poging_nummer": len(submissions[week_key][student_id]),
        "bot_check": bot_resultaat,
        "chart_check": chart_resultaat,
        "locatie_check": locatie_resultaat,
        "boodschap": (
            "Ingeleverd en technisch goedgekeurd. Je grafiek staat nu klaar voor peer-review."
            if geldig
            else "Ingeleverd, maar nog niet goedgekeurd — los de problemen hieronder op en lever opnieuw in."
        ),
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

    hand_log kun je direct in een DataFrame zetten: pd.DataFrame(response.json()["hand_log"])
    """
    return draai_toernooi(week, vergelijk_met_week=vergelijk_met_week)


@app.post("/toernooi/{week}/opnieuw")
def toernooi_opnieuw(
    week: int,
    vergelijk_met_week: int | None = None,
    ok: bool = Depends(db.verifieer_docent_token),
):
    """Docent-only: forceer een nieuwe toernooi-run (bv. na te late inzendingen)."""
    return draai_toernooi(week, vergelijk_met_week=vergelijk_met_week, forceer_opnieuw=True)


@app.get("/locaties/{week}")
def locaties(week: int, student_id: str, ok: bool = Depends(db.verifieer_student_token)):
    """
    Geolocatie van elke technisch goedgekeurde bot, met de eindstand erbij
    zodra het toernooi van deze week gedraaid is (anders eindstand: null —
    je krijgt dan wel alle posities, maar nog geen winst/verlies-kleur).
    """
    week_key = str(week)
    submissions = db.laad_submissions().get(week_key, {})
    eindstand_per_bot = db.laad_toernooi_resultaten().get(week_key, {}).get("eindstand_per_bot", {})

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
                "reviews_gegeven": reviews_gegeven,
                "voldaan": submission["geldig"] and reviews_gegeven >= MIN_REVIEWS_VOOR_VOLDAAN,
                "laatst_ingeleverd_op": submission["ingeleverd_op"],
            }
        )
    return overzicht
