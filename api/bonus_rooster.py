"""
Het bonuspuntenschema van de Pokerbot Analytics Challenge.

De vakbeschrijving belooft studenten maximaal +1,0 bonuspunt "op basis van de
toernooiprestaties en het correct doorlopen van de sprints". Dit bestand is de
enige plek waar staat wat dat precies betekent. Verschuift een deadline of een
weging, dan pas je dit bestand aan en klopt de rest vanzelf.

DRIE BOT-WEKEN, ONGELIJK GEWOGEN
--------------------------------
Week 1 (Bot v1) telt niet mee. Dat is de week waarin je leert inleveren, de API
leert kennen en voor het eerst een toernooi ziet. Wie daar chips verliest omdat
hij het nog niet snapt, hoort daar geen punten voor te verliezen.

Week 3 (Bot v2) telt voor 20% en week 5 (Bot v3) voor 80%. Het zwaartepunt ligt
op het eind, want de bonus hoort te belonen waar je uitkomt, niet waar je begon.
Week 3 telt wel iets mee, anders is er drie weken lang geen enkele reden om
serieus mee te doen en wordt week 5 een sprint vanuit stilstand.

SPRINT (60%) ZWAARDER DAN PRESTATIE (40%)
-----------------------------------------
Per week is 60% van het gewicht te verdienen met het doorlopen van de sprint
(op tijd een echte bot inleveren, en 'm daarna verbeteren) en 40% met je plek
in de eindstand. Dat is bewust die kant op: dit is een introductievak, dus de
bonus hoort vooral te belonen dat je meedoet en doorwerkt -- niet dat je goed
bent in poker. Het houdt ook de ruisgevoelige helft klein: de eindstand van een
toernooi hangt nu eenmaal deels van de kaarten af, en die helft is met 0,32 van
de 1,0 punt begrensd.

WAAROM ALLEEN DE LAATSTE RONDE MEETELT
--------------------------------------
Binnen een week draait het toernooi twee keer: woensdag (ronde 1) en later in
de week (ronde 2). In ronde 2 speelt iedereen door met de chips uit ronde 1 --
zie poker_adapter.bereken_startstacks(). Je woensdagresultaat zit dus al ín de
eindstand van ronde 2. Zou je beide rondes apart scoren en optellen, dan telde
woensdag dubbel. Daarom scoort de prestatiecomponent uitsluitend de laatste
gedraaide ronde van die week; de carry-over doet het werk.
"""

from datetime import datetime, timezone

# Zomertijd loopt in 2026 tot 25 oktober, dus alle deadlines hieronder vallen in
# CEST. De offset staat er expliciet in: dan is er geen tijdzone-database nodig
# op de server en is aan de string zelf te zien welk moment bedoeld wordt.
_ZOMERTIJD = "+02:00"

MAX_BONUS = 1.0

# Verdeling binnen een week. Moet optellen tot 1,0.
AANDEEL_SPRINT = 0.6
AANDEEL_PRESTATIE = 0.4

# Verdeling binnen de sprint. Moet optellen tot 1,0.
AANDEEL_WOENSDAG = 0.5
AANDEEL_VRIJDAG = 0.5

# Een bot die op elke testhand hetzelfde antwoordt is technisch geldig maar
# speelt geen poker (zie bot_validator._is_constante_bot). Dat is geen reden om
# af te keuren, wel om er niet de volle woensdagpunten voor te geven.
FACTOR_CONSTANTE_BOT = 0.5

BOT_WEKEN = [
    {
        "week": 1,
        "bot": "Bot v1",
        "gewicht": 0.0,
        "deadline_woensdag": f"2026-09-02T09:00:00{_ZOMERTIJD}",
        "deadline_vrijdag": f"2026-09-04T17:00:00{_ZOMERTIJD}",
        "toelichting": "Oefenweek: telt niet mee voor de bonus.",
    },
    {
        "week": 3,
        "bot": "Bot v2",
        "gewicht": 0.2,
        "deadline_woensdag": f"2026-09-16T09:00:00{_ZOMERTIJD}",
        "deadline_vrijdag": f"2026-09-18T12:00:00{_ZOMERTIJD}",
        "toelichting": "Woensdag Bot v2, vrijdagochtend een verbeterde versie.",
    },
    {
        "week": 5,
        "bot": "Bot v3",
        "gewicht": 0.8,
        "deadline_woensdag": f"2026-09-30T09:00:00{_ZOMERTIJD}",
        "deadline_vrijdag": f"2026-10-02T17:00:00{_ZOMERTIJD}",
        "toelichting": "Woensdag Bot v3, vrijdagmiddag de slotinzending.",
    },
]

WEKEN = [item["week"] for item in BOT_WEKEN]


# ---------------------------------------------------------------------------
# Sprintscore: heb je op tijd een echte bot ingeleverd, en 'm daarna verbeterd?
# ---------------------------------------------------------------------------
def _op_tijd(inzendingen, deadline_iso):
    """
    De laatste inzending die vóór `deadline_iso` binnenkwam, of None.

    Bewust de laatste en niet de eerste: je mag zo vaak opnieuw inleveren als je
    wilt, en het is de versie waarmee je de deadline haalt die meedoet in het
    toernooi (zie db.nieuwste_inzending()).
    """
    deadline = datetime.fromisoformat(deadline_iso)
    op_tijd = [
        inzending
        for inzending in inzendingen
        if _tijdstip(inzending) is not None and _tijdstip(inzending) <= deadline
    ]
    return op_tijd[-1] if op_tijd else None


def _tijdstip(inzending):
    """Het inlevermoment als aware datetime, of None als het onleesbaar is."""
    tekst = inzending.get("ingeleverd_op")
    if not tekst:
        return None
    try:
        moment = datetime.fromisoformat(tekst)
    except ValueError:
        return None
    # Oudere records zijn zonder tijdzone weggeschreven; die zijn UTC.
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def sprintscore(inzendingen, week_item):
    """
    Score 0..1 voor het doorlopen van de sprint van één week, plus uitleg.

    Woensdag (de helft): een geldige bot vóór 09:00. Is die bot constant --
    hij doet bij elke testhand hetzelfde -- dan telt het half: ingeleverd is
    ingeleverd, maar het is nog geen pokerbot.

    Vrijdag (de andere helft): een geldige bot vóór de vrijdagdeadline die
    verschilt van je woensdaginzending. De opdracht is een verbeterde versie,
    dus dezelfde code opnieuw insturen levert niets op.
    """
    woensdag = _op_tijd(inzendingen, week_item["deadline_woensdag"])
    vrijdag = _op_tijd(inzendingen, week_item["deadline_vrijdag"])

    if woensdag is None or not woensdag.get("geldig"):
        score_woensdag = 0.0
        uitleg_woensdag = "geen goedgekeurde bot vóór woensdag 09:00"
    elif woensdag.get("bot_check", {}).get("constante_bot"):
        score_woensdag = AANDEEL_WOENSDAG * FACTOR_CONSTANTE_BOT
        uitleg_woensdag = "woensdag ingeleverd, maar de bot doet altijd hetzelfde"
    else:
        score_woensdag = AANDEEL_WOENSDAG
        uitleg_woensdag = "woensdag een werkende bot ingeleverd"

    if vrijdag is None or not vrijdag.get("geldig"):
        score_vrijdag = 0.0
        uitleg_vrijdag = "geen goedgekeurde bot vóór de vrijdagdeadline"
    elif woensdag is not None and vrijdag.get("bot_code") == woensdag.get("bot_code"):
        score_vrijdag = 0.0
        uitleg_vrijdag = "vrijdag dezelfde code als woensdag — geen verbeterde versie"
    else:
        score_vrijdag = AANDEEL_VRIJDAG
        uitleg_vrijdag = "vrijdag een verbeterde versie ingeleverd"

    return score_woensdag + score_vrijdag, [uitleg_woensdag, uitleg_vrijdag]


# ---------------------------------------------------------------------------
# Prestatiescore: je plek in de eindstand van de laatste ronde
# ---------------------------------------------------------------------------
def prestatiescore(eindstand, student_id, deelnemers=None):
    """
    Score 0..1 op basis van je plek in `eindstand`: de beste krijgt 1,0, de
    laatste 0,0, de rest lineair daartussen.

    Op plek in plaats van op chips, omdat chips niet vergelijkbaar zijn tussen
    rondes (in ronde 2 begint iedereen hoger) en één uitschieter anders de hele
    schaal bepaalt.

    `deelnemers` beperkt het klassement tot echte studenten; de oefenbots die
    het toernooi aanvullen als er nog te weinig inzendingen zijn, horen niet in
    de ranglijst thuis.
    """
    if not eindstand:
        return None, "nog geen toernooi gedraaid"

    if deelnemers is not None:
        eindstand = {naam: stand for naam, stand in eindstand.items() if naam in set(deelnemers)}

    if student_id not in eindstand:
        return 0.0, "niet meegespeeld in dit toernooi"

    aantal = len(eindstand)
    if aantal == 1:
        return 1.0, "als enige deelnemer"

    op_volgorde = sorted(eindstand.items(), key=lambda kv: -kv[1])
    plek = [naam for naam, _ in op_volgorde].index(student_id) + 1
    return (aantal - plek) / (aantal - 1), f"plek {plek} van {aantal}"


# ---------------------------------------------------------------------------
# Alles bij elkaar
# ---------------------------------------------------------------------------
def _laatste_ronde(toernooi_resultaten, week):
    """
    De uitslag van de hoogst gedraaide ronde van `week`, of None.

    Alleen die telt mee: door de carry-over zit het woensdagresultaat al in de
    eindstand van de ronde erna (zie de moduledocstring).
    """
    gevonden = None
    ronde = 1
    while True:
        sleutel = str(week) if ronde == 1 else f"{week}_ronde{ronde}"
        resultaat = toernooi_resultaten.get(sleutel)
        if resultaat is None:
            return gevonden
        if resultaat.get("eindstand_per_bot"):
            gevonden = resultaat
        ronde += 1


def bonus_per_student(student_id, inzendingen_per_week, toernooi_resultaten):
    """
    Rekent de bonus van één student uit en laat zien hoe die is opgebouwd.

    `inzendingen_per_week` is {weeknummer (str of int): [inzending, ...]} --
    precies wat db.laad_submissions() per student bevat.

    Retourneert {"bonus": float, "bonus_afgerond": float, "per_week": [...]},
    waarbij elke week z'n eigen sprint- en prestatiescore toont, zodat een
    student kan zien waar zijn punt vandaan komt en de docent het kan navertellen.
    """
    per_week = []
    totaal = 0.0

    for week_item in BOT_WEKEN:
        week = week_item["week"]
        inzendingen = inzendingen_per_week.get(str(week)) or inzendingen_per_week.get(week) or []

        sprint, uitleg_sprint = sprintscore(inzendingen, week_item)

        toernooi = _laatste_ronde(toernooi_resultaten, week) or {}
        prestatie, uitleg_prestatie = prestatiescore(
            toernooi.get("eindstand_per_bot") or {},
            student_id,
            deelnemers=toernooi.get("namen_deelnemers") or None,
        )

        # Nog geen toernooi gedraaid: de prestatiehelft is dan nog niet te
        # bepalen. Die telt als 0 zolang dat zo is -- niet als "gemist", maar
        # als "nog niet bekend", en dat staat ook in de uitleg.
        weekscore = AANDEEL_SPRINT * sprint + AANDEEL_PRESTATIE * (prestatie or 0.0)
        punten = MAX_BONUS * week_item["gewicht"] * weekscore
        totaal += punten

        per_week.append(
            {
                "week": week,
                "bot": week_item["bot"],
                "gewicht": week_item["gewicht"],
                "maximaal": round(MAX_BONUS * week_item["gewicht"], 3),
                "sprintscore": round(sprint, 3),
                "prestatiescore": None if prestatie is None else round(prestatie, 3),
                "punten": round(punten, 3),
                "uitleg": uitleg_sprint + [uitleg_prestatie],
            }
        )

    return {
        "student_id": student_id,
        "bonus": round(totaal, 3),
        # Op het eindcijfer telt één decimaal; dit is het getal dat de student krijgt.
        "bonus_afgerond": round(totaal, 1),
        "maximaal": MAX_BONUS,
        "per_week": per_week,
    }


def bonus_hele_klas(submissions, toernooi_resultaten):
    """
    Hetzelfde voor iedereen die ooit iets heeft ingeleverd, hoogste bonus eerst.

    `submissions` is de hele db.laad_submissions(): {week: {student_id: [...]}}.
    """
    per_student = {}
    for week_key, inzendingen_per_student in submissions.items():
        for student_id, inzendingen in inzendingen_per_student.items():
            per_student.setdefault(student_id, {})[week_key] = inzendingen

    overzicht = [
        bonus_per_student(student_id, weken, toernooi_resultaten)
        for student_id, weken in per_student.items()
    ]
    return sorted(overzicht, key=lambda r: -r["bonus"])
