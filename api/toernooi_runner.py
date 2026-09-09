"""
Orkestreert een echt pokertoernooi tussen alle technisch goedgekeurde
bot-inzendingen van een week, gebouwd op poker_adapter.speel_toernooi().

Kan ook twee weken combineren in één toernooi (bv. Week 3 vs. Week 1), zodat
een student zijn nieuwe bot letterlijk tegen zijn eigen oude bot en die van
klasgenoten ziet spelen. Resultaten worden per (week, vergelijk_met_week)
gecached, zodat een toernooi maar één keer per combinatie hoeft te draaien.
"""
import database as db
from bonus_rooster import BONUSWEEK
from referentiebots import referentiebots_voor
from poker_adapter import bereken_startstacks, speel_toernooi

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
    for student_id, inzendingen in submissions.items():
        inzending = db.nieuwste_inzending(inzendingen)
        if not inzending or not inzending.get("geldig"):
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


# Hoeveel keer het hele veld opnieuw over de tafels wordt verdeeld. De eindstand
# is het gemiddelde over deze simulaties, dus dit getal bepaalt hoeveel van de
# uitslag skill is en hoeveel toeval.
#
# In de bonusweek staat er iets op het spel, dus meten we serieuzer: 20 in plaats
# van 5 simulaties, oftewel 1000 handen per bot in plaats van 250. Met 5 ging
# ongeveer de helft van de punten naar de betere helft van het veld -- een
# muntworp (52%); met 20 is dat 83%. Met 30 werd het 84%, dus daarboven koop je
# niets meer -- 20 is waar de curve vlak wordt.
#
# Het is bewust niet meer dan 20. De exacte volgorde binnen de top wordt er niet
# reproduceerbaar van: bots van gelijke sterkte zijn gelijk sterk, dus wie van hen
# wint blijft toeval, en dat los je met geen enkel aantal simulaties op. Wat je met
# meer simulaties koopt is dat de prijzen bij de goede bots terechtkomen, en dat
# doen ze bij 20 al. Wat je ervoor betaalt is rekentijd en een groter hand-log dat
# studenten moeten downloaden. Zie scripts/meet_toernooi_variantie.py.
#
# De andere weken houden 5. Daar telt de uitslag niet mee voor punten; hij is
# invoer voor de visualisatie-opdracht van de week erna, en die heeft geen 1000
# handen per bot nodig.
STANDAARD_N_SIMULATIES = 5
N_SIMULATIES_BONUSWEEK = 20


def n_simulaties_voor(week):
    """
    Hoeveel simulaties een toernooi in deze week draait.

    Op week en niet op ronde, zodat de formatieve donderdagronde in de bonusweek
    net zo zwaar meet als de ronde die hij voorspelt. Een repetitie met een
    andere steekproefgrootte voorspelt niets.
    """
    return N_SIMULATIES_BONUSWEEK if week == BONUSWEEK else STANDAARD_N_SIMULATIES


def cache_sleutel(week, vergelijk_met_week=None, ronde=1, formatief=False):
    """
    De sleutel waaronder een toernooi-uitkomst wordt bewaard.

    De ronde hoort erin. Zonder ronde in de sleutel overschrijft de tweede run
    van een week de eerste -- en juist die eerste (woensdag) is het bewijs
    waarop de woensdag-inzending wordt beoordeeld, en de data waarmee het
    werkcollege van die dag werkt.

    Ronde 1 houdt bewust de oude sleutel ("5" of "5_vs_1"), zodat alles wat
    vóór deze wijziging is gedraaid gewoon vindbaar blijft.

    Een formatieve run krijgt een eigen sleutel naast de echte ronde. Hij is een
    repetitie van die ronde: hij draait met dezelfde startstacks, maar met de
    bots van dát moment. Zo kan de donderdagronde de vrijdaguitslag voorspellen
    zonder hem te bezetten of te beïnvloeden.
    """
    basis = str(week) if vergelijk_met_week is None else f"{week}_vs_{vergelijk_met_week}"
    sleutel = basis if ronde == 1 else f"{basis}_ronde{ronde}"
    return f"{sleutel}_formatief" if formatief else sleutel


def haal_gecacht_resultaat_op(week, vergelijk_met_week=None, ronde=1, formatief=False):
    """
    Haalt het laatst gecachte toernooi-resultaat op zonder OOIT een nieuwe
    run te starten -- ook niet als er nog niks gecacht is. Voor de docent-knop
    "uitslag ophalen" op de Streamlit hub: die wil zien wat er nu al bekend is
    zonder het (mogelijk net lopende) toernooi opnieuw te forceren.

    Retourneert {"gedraaid": False, "week": ..., "vergelijk_met_week": ...} als
    er nog geen resultaat is voor deze combinatie, anders het opgeslagen
    resultaat aangevuld met "gedraaid": True.
    """
    resultaat = db.laad_toernooi_resultaat(cache_sleutel(week, vergelijk_met_week, ronde, formatief))
    if resultaat is None:
        return {
            "gedraaid": False,
            "week": week,
            "vergelijk_met_week": vergelijk_met_week,
            "ronde": ronde,
            "formatief": formatief,
        }
    return {**resultaat, "gedraaid": True}


def _startstacks_uit_vorige_ronde(week, vergelijk_met_week, ronde):
    """
    De startstacks voor `ronde`, afgeleid uit de eindstand van de ronde ervoor.

    Retourneert None voor ronde 1 en ook als de vorige ronde niet (meer) in de
    cache staat -- dan begint iedereen gewoon weer op de standaardstack, wat
    het oude gedrag is.

    Er wordt altijd naar de échte vorige ronde gekeken, nooit naar een
    formatieve run. Daardoor krijgt de formatieve repetitie van een ronde
    precies dezelfde startstacks als die ronde zelf, en kan een oefenronde de
    uitslag die meetelt niet verschuiven.
    """
    if ronde <= 1:
        return None
    vorige = db.laad_toernooi_resultaat(cache_sleutel(week, vergelijk_met_week, ronde - 1))
    if not vorige or not vorige.get("eindstand_per_bot"):
        return None
    return bereken_startstacks(vorige["eindstand_per_bot"])


def draai_toernooi(
    week,
    vergelijk_met_week=None,
    n_simulaties=None,
    n_handen=50,
    forceer_opnieuw=False,
    ronde=1,
    formatief=False,
):
    """
    Draait (of hergebruikt uit cache) het toernooi voor `week`, optioneel
    samengevoegd met de bots van `vergelijk_met_week`.

    `ronde` maakt meerdere toernooien binnen dezelfde week mogelijk zonder dat
    ze elkaar overschrijven: ronde 1 is de woensdag-run, ronde 2 de run later
    in de week. Elke ronde krijgt een eigen cachesleutel én een eigen seed.

    `formatief` draait een repetitie van `ronde`: dezelfde startstacks en
    dezelfde seed, maar met de bots van dit moment, weggeschreven onder een
    eigen sleutel. Bedoeld voor de donderdagronde in week 5 -- studenten zien
    wat hun aanpassing zou doen, zonder dat het de uitslag raakt die meetelt.

    Dat de seed hetzelfde blijft is een keuze, niet een vergeetachtigheid: het
    maakt de oefenronde een gecontroleerd experiment. Dezelfde kaarten, dezelfde
    startposities, alleen een andere bot -- dus het verschil dat een student
    ziet is zíjn verandering en niet de shuffle. Precies wat "verander, meet,
    corrigeer" in Werkcollege 8 nodig heeft. Met een andere seed zou een student
    niet kunnen weten of zijn aanpassing hielp of dat hij gewoon betere kaarten
    kreeg.

    Vanaf ronde 2 spelen de bots door met wat ze verdiend hebben: hun stack is
    de eindstand van de vorige ronde + 1000 voor iedereen. Wie op woensdag niet
    (of met een niks-doende bot) meedeed, begint dus achter op wie dat wel deed.
    De bot zelf mag tussen de rondes wél vernieuwd zijn -- er wordt altijd de
    nieuwste goedgekeurde inzending gebruikt; alleen de chips zijn erfelijk.

    Retourneert:
        {
            "week": int,
            "vergelijk_met_week": int | None,
            "n_bots": int,
            "namen_deelnemers": [...],       # bot-namen van `week` zelf
            "aangevuld_met_oefenbots": int,
            "referentiebots": [...],         # spelen mee, tellen niet voor de bonus
            "ronde": int,
            "formatief": bool,               # True = oefenronde, telt niet mee
            "n_simulaties": int,             # over hoeveel simulaties gemiddeld is
            "startstacks": {...} | None,     # None in ronde 1
            "hand_log": [...],
            "eindstand_per_bot": {...},
        }
    """
    if n_simulaties is None:
        n_simulaties = n_simulaties_voor(week)

    cache_key = cache_sleutel(week, vergelijk_met_week, ronde, formatief)

    if not forceer_opnieuw:
        bestaand = db.laad_toernooi_resultaat(cache_key)
        if bestaand is not None:
            return bestaand

    bots, namen_hoofdweek = _verzamel_bots_over_weken(week, vergelijk_met_week)
    if vergelijk_met_week is None:
        namen_hoofdweek = list(bots.keys())

    # De referentiebots komen HIER, ná het vastleggen van namen_hoofdweek. Dat is
    # geen detail: bonus_rooster rekent de puntenladder alleen over die lijst, dus
    # een referentiebot die de hele klas verslaat pakt niemand zijn bonus af. Hij
    # beïnvloedt wel de chips aan tafel -- hij speelt echt mee.
    referentie = referentiebots_voor(week)
    for naam, info in referentie.items():
        bots.setdefault(naam, info)

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
            "ronde": ronde,
            "formatief": formatief,
            "n_bots": len(bots),
            "namen_deelnemers": namen_hoofdweek,
            "aangevuld_met_oefenbots": aangevuld,
            "referentiebots": sorted(referentie),
            "n_simulaties": n_simulaties,
            "hand_log": [],
            "eindstand_per_bot": {},
            "boodschap": "Nog geen 2 geldige inzendingen — toernooi kan nog niet draaien.",
        }
        return resultaat

    startstacks = _startstacks_uit_vorige_ronde(week, vergelijk_met_week, ronde)

    uitkomst = speel_toernooi(
        bots,
        n_simulaties=n_simulaties,
        n_handen=n_handen,
        seed=week * 10 + ronde,
        startstacks=startstacks,
    )

    resultaat = {
        "week": week,
        "vergelijk_met_week": vergelijk_met_week,
        "ronde": ronde,
        "formatief": formatief,
        "n_bots": len(bots),
        "namen_deelnemers": namen_hoofdweek,
        "aangevuld_met_oefenbots": aangevuld,
        "referentiebots": sorted(referentie),
        "n_simulaties": n_simulaties,
        "startstacks": startstacks,
        "hand_log": uitkomst["hand_log"],
        "eindstand_per_bot": uitkomst["eindstand_per_bot"],
    }

    db.sla_toernooi_resultaat_op(cache_key, resultaat)
    return resultaat
