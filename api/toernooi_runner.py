"""
Orkestreert een echt pokertoernooi tussen alle technisch goedgekeurde
bot-inzendingen van een week, gebouwd op poker_adapter.speel_toernooi().

Kan ook twee weken combineren in één toernooi (bv. Week 3 vs. Week 1), zodat
een student zijn nieuwe bot letterlijk tegen zijn eigen oude bot en die van
klasgenoten ziet spelen. Resultaten worden per (week, vergelijk_met_week)
gecached, zodat een toernooi maar één keer per combinatie hoeft te draaien.
"""
import database as db
from poker_adapter import speel_toernooi

# Reservebots vullen de tafel aan als er nog te weinig geldige inzendingen zijn
# (bv. vroeg in de week, of tijdens het uitproberen van deze API). Ze spelen
# mee om het toernooi draaibaar te houden, maar tellen niet mee voor een cijfer.
OEFENBOTS = {
    "OefenBot_Voorzichtig": lambda hand, **_: "call" if any(k in hand for k in ("A", "K", "Q")) else "fold",
    "OefenBot_Agressief": lambda hand, **_: "raise",
}


def _laad_kies_actie(bot_code):
    """Voert de ingeleverde bot-code uit en pakt de kies_actie-functie eruit."""
    namespace = {}
    try:
        exec(bot_code, namespace)
    except Exception:
        return None
    functie = namespace.get("kies_actie")
    return functie if callable(functie) else None


def _verzamel_geldige_bots(week):
    """
    Retourneert {student_id: {"kies_actie": fn, "strategie": ..., "bluf_kans": ...}}
    voor alle technisch goedgekeurde inzendingen van die week.
    """
    submissions = db.laad_submissions().get(str(week), {})
    bots = {}
    for student_id, inzending in submissions.items():
        if not inzending.get("geldig"):
            continue
        kies_actie = _laad_kies_actie(inzending["bot_code"])
        if kies_actie is not None:
            bots[student_id] = {
                "kies_actie": kies_actie,
                "strategie": inzending.get("strategie"),
                "bluf_kans": inzending.get("bluf_kans"),
            }
    return bots


def _verzamel_bots_over_weken(hoofdweek, vergelijk_met_week=None):
    """
    Bouwt de bot-dict voor het toernooi. Zonder vergelijk_met_week: gewoon
    alle geldige bots van hoofdweek. Mét vergelijk_met_week: bots van beide
    weken samen, met bot-namen als "student__w{week}" zodat je eigen oude en
    nieuwe bot naast elkaar in dezelfde uitslag verschijnen, niet overschreven
    door elkaar (submissions_db.json bewaart per week een los record per
    student, dus dat botst hier niet — alleen de bot-naam in het toernooi zelf
    moet uniek zijn per week).
    """
    if vergelijk_met_week is None:
        bots_hoofdweek = _verzamel_geldige_bots(hoofdweek)
        return {naam: info for naam, info in bots_hoofdweek.items()}, []

    bots = {}
    deelnemers_hoofdweek = []
    for week in (hoofdweek, vergelijk_met_week):
        for student_id, info in _verzamel_geldige_bots(week).items():
            bot_naam = f"{student_id}__w{week}"
            bots[bot_naam] = info
            if week == hoofdweek:
                deelnemers_hoofdweek.append(bot_naam)
    return bots, deelnemers_hoofdweek


def draai_toernooi(week, vergelijk_met_week=None, n_simulaties=5, n_handen=50, forceer_opnieuw=False):
    """
    Draait (of hergebruikt uit cache) het toernooi voor `week`, optioneel
    samengevoegd met de bots van `vergelijk_met_week`.

    Retourneert:
        {
            "week": int,
            "vergelijk_met_week": int | None,
            "n_bots": int,
            "namen_deelnemers": [...],       # bot-namen van `week` zelf
            "aangevuld_met_oefenbots": int,
            "hand_log": [...],
            "eindstand_per_bot": {...},
        }
    """
    alle_resultaten = db.laad_toernooi_resultaten()
    cache_key = str(week) if vergelijk_met_week is None else f"{week}_vs_{vergelijk_met_week}"

    if not forceer_opnieuw and cache_key in alle_resultaten:
        return alle_resultaten[cache_key]

    bots, namen_hoofdweek = _verzamel_bots_over_weken(week, vergelijk_met_week)
    if vergelijk_met_week is None:
        namen_hoofdweek = list(bots.keys())

    aangevuld = 0
    for oefen_naam, oefen_functie in OEFENBOTS.items():
        if len(bots) >= 2:
            break
        bots[oefen_naam] = {"kies_actie": oefen_functie, "strategie": None, "bluf_kans": None}
        aangevuld += 1

    if len(bots) < 2:
        resultaat = {
            "week": week,
            "vergelijk_met_week": vergelijk_met_week,
            "n_bots": len(bots),
            "namen_deelnemers": namen_hoofdweek,
            "aangevuld_met_oefenbots": aangevuld,
            "hand_log": [],
            "eindstand_per_bot": {},
            "boodschap": "Nog geen 2 geldige inzendingen — toernooi kan nog niet draaien.",
        }
        return resultaat

    uitkomst = speel_toernooi(bots, n_simulaties=n_simulaties, n_handen=n_handen, seed=week)

    resultaat = {
        "week": week,
        "vergelijk_met_week": vergelijk_met_week,
        "n_bots": len(bots),
        "namen_deelnemers": namen_hoofdweek,
        "aangevuld_met_oefenbots": aangevuld,
        "hand_log": uitkomst["hand_log"],
        "eindstand_per_bot": uitkomst["eindstand_per_bot"],
    }

    alle_resultaten[cache_key] = resultaat
    db.sla_toernooi_resultaten_op(alle_resultaten)
    return resultaat
