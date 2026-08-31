"""
Opslag-laag voor de Poker Analytics Challenge API.

Gebruikt platte JSON-bestanden als database (zelfde aanpak als de Hackathon-API),
zodat er geen aparte database-server nodig is voor een 6-wekelijks vak.
"""
import hashlib
import json
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SUBMISSIONS_FILE = "submissions_db.json"
GALLERY_FILE = "gallery_db.json"
REVIEWS_FILE = "reviews_db.json"
TOKENS_FILE = "tokens_db.json"
DOCENT_TOKEN_FILE = "docent_token.json"
TOERNOOI_RESULTATEN_FILE = "toernooi_resultaten_db.json"

security_bearer = HTTPBearer()


def _laad(pad: str) -> dict:
    if os.path.exists(pad):
        with open(pad, "r") as f:
            return json.load(f)
    return {}


def _sla_op(pad: str, data: dict):
    with open(pad, "w") as f:
        json.dump(data, f, indent=2)


def laad_submissions() -> dict:
    return _laad(SUBMISSIONS_FILE)


def sla_submissions_op(data: dict):
    _sla_op(SUBMISSIONS_FILE, data)


def laad_gallery() -> dict:
    return _laad(GALLERY_FILE)


def sla_gallery_op(data: dict):
    _sla_op(GALLERY_FILE, data)


def laad_reviews() -> dict:
    return _laad(REVIEWS_FILE)


def sla_reviews_op(data: dict):
    _sla_op(REVIEWS_FILE, data)


def laad_tokens() -> dict:
    return _laad(TOKENS_FILE)


def laad_toernooi_resultaten() -> dict:
    return _laad(TOERNOOI_RESULTATEN_FILE)


def sla_toernooi_resultaten_op(data: dict):
    _sla_op(TOERNOOI_RESULTATEN_FILE, data)


def anonimiseer_id(student_id: str, week: int) -> str:
    """
    Maakt een niet-terugleidbaar ID voor de Streamlit peer-review hub.
    Zelfde student+week geeft altijd hetzelfde anon_id (nodig om dubbele
    reviews en zelf-review te kunnen blokkeren), maar het ID onthult de
    student_id niet.
    """
    ruw = f"{student_id}-week{week}-poker-analytics-salt"
    return hashlib.sha256(ruw.encode()).hexdigest()[:12]


def verifieer_student_token(
    student_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
):
    """Controleert of het meegestuurde Bearer-token bij dit student_id hoort."""
    tokens = laad_tokens()
    token = credentials.credentials

    if student_id not in tokens:
        raise HTTPException(status_code=401, detail="Onbekend student_id.")
    if tokens[student_id] != token:
        raise HTTPException(status_code=401, detail="Authenticatie mislukt: onjuist token.")
    return True


def verifieer_docent_token(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
):
    """Voor de docent-only export-endpoints."""
    docent_data = _laad(DOCENT_TOKEN_FILE)
    verwacht_token = docent_data.get("docent_token")
    if not verwacht_token or credentials.credentials != verwacht_token:
        raise HTTPException(status_code=401, detail="Geen geldig docent-token.")
    return True
