"""
Het DataCamp-deel van het blokrooster, plus de statusberekening die de
hub-endpoints gebruiken.

Waarom hier en niet in het snapshot-script: het script haalt alleen ruwe
feiten op ("deze student heeft deze course op deze datum afgerond"). Wat een
deadline is, en dus wat "te laat" of "gemist" betekent, staat alleen hier.
Verschuift er een deadline, dan pas je dit bestand aan en zijn alle oude
snapshots meteen opnieuw correct beoordeeld -- zonder opnieuw te scrapen.

ROOSTER_DEADLINE is de datum uit het papieren rooster; DEADLINE is de datum
die daadwerkelijk in de DataCamp-assignment staat. Die twee lopen alleen bij
week 1 uiteen: DataCamp weigert een due date in het verleden, dus de drie
week-1 courses kregen 11-9 als inhaaldeadline. Studenten zien 11-9, dus dat
is ook waarop we ze beoordelen.

VERPLICHT scheidt de courses die voorwaardelijk zijn voor een eindresultaat
van de courses die alleen verdiepen. De regel die we daarvoor aanhouden: een
course is verplicht als een werkcollege of een case hem nodig heeft, en
aanbevolen als hij het onderwerp alleen verder uitdiept.

Dat onderscheid telt door in alles wat de hub laat zien: "af / totaal" en de
lijst met gemiste deadlines gaan uitsluitend over de verplichte courses, want
dat is waar een student op wordt afgerekend. De aanbevolen courses worden apart
geteld en leveren nooit een waarschuwing op -- een aanbevolen course die over
de deadline is, is geen achterstand.
"""
from datetime import date

ROOSTER = [
    {"code": "IDS 1", "titel": "Introduction to Python", "week": 1, "rooster_deadline": "2026-09-04", "deadline": "2026-09-11", "verplicht": True},
    {"code": "IDS 2", "titel": "Intermediate Python", "week": 1, "rooster_deadline": "2026-09-04", "deadline": "2026-09-11", "verplicht": True},
    {"code": "VA 1", "titel": "Introduction to Data Visualization with Matplotlib", "week": 1, "rooster_deadline": "2026-09-04", "deadline": "2026-09-11", "verplicht": True},
    {"code": "IDS 3", "titel": "Data Manipulation with pandas", "week": 2, "rooster_deadline": "2026-09-11", "deadline": "2026-09-11", "verplicht": True},
    {"code": "VA 2", "titel": "Introduction to Data Visualization with Seaborn", "week": 2, "rooster_deadline": "2026-09-11", "deadline": "2026-09-11", "verplicht": True},
    {"code": "VA 3", "titel": "Introduction to Data Visualization with Plotly in Python", "week": 3, "rooster_deadline": "2026-09-18", "deadline": "2026-09-18", "verplicht": True},
    {"code": "IDS 4", "titel": "Introduction to Functions in Python", "week": 3, "rooster_deadline": "2026-09-18", "deadline": "2026-09-18", "verplicht": True},
    {"code": "IDS 5", "titel": "Cleaning Data in Python", "week": 5, "rooster_deadline": "2026-10-02", "deadline": "2026-10-02", "verplicht": True},
    {"code": "IDS 6", "titel": "Exploratory Data Analysis in Python", "week": 5, "rooster_deadline": "2026-10-02", "deadline": "2026-10-02", "verplicht": True},
    {"code": "IDS 7", "titel": "Working with Categorical Data in Python", "week": 6, "rooster_deadline": "2026-10-09", "deadline": "2026-10-09", "verplicht": True},
    {"code": "VA 5", "titel": "Data Communication Concepts", "week": 6, "rooster_deadline": "2026-10-09", "deadline": "2026-10-09", "verplicht": True},
]

AF_OP_TIJD = "af"
AF_TE_LAAT = "te laat af"
GEMIST = "gemist"
OPEN = "open"


def _vandaag() -> str:
    return date.today().isoformat()


def status_per_course(courses: dict, peildatum: str | None = None) -> list[dict]:
    """
    Zet {course-titel: afrondingsdatum} om in een lijst met één regel per
    roostercourse. Courses die een student buiten het rooster heeft gedaan
    (bv. Introduction to Git) blijven bewust buiten beschouwing: dit is een
    rooster-overzicht, geen totaalscore.
    """
    peildatum = peildatum or _vandaag()
    regels = []
    for item in ROOSTER:
        afgerond_op = courses.get(item["titel"])
        if afgerond_op:
            status = AF_OP_TIJD if afgerond_op <= item["deadline"] else AF_TE_LAAT
        elif not item["verplicht"]:
            # aanbevolen: geen deadline om te missen, alleen af of nog niet
            status = OPEN
        else:
            status = GEMIST if peildatum > item["deadline"] else OPEN
        regels.append({**item, "afgerond_op": afgerond_op, "status": status})
    return regels


def samenvatting(courses: dict, peildatum: str | None = None) -> dict:
    """
    Telt de statussen op tot de cijfers waar de hub op sorteert.

    Alles wat over voldoen gaat -- af, totaal, te_laat, gemist, verstreken --
    kijkt uitsluitend naar de VERPLICHTE courses. Een aanbevolen course die
    over zijn deadline is, mag geen achterstand opleveren; die tellen we apart
    in aanbevolen_af / aanbevolen_totaal, zodat de hub 'm kan tonen zonder
    alarm te slaan.
    """
    peildatum = peildatum or _vandaag()
    regels = status_per_course(courses, peildatum)
    verplicht = [r for r in regels if r["verplicht"]]
    aanbevolen = [r for r in regels if not r["verplicht"]]
    af = [r for r in verplicht if r["status"] in (AF_OP_TIJD, AF_TE_LAAT)]
    return {
        "af": len(af),
        "totaal": len(verplicht),
        "te_laat": len([r for r in verplicht if r["status"] == AF_TE_LAAT]),
        "gemist": [r["code"] for r in verplicht if r["status"] == GEMIST],
        "verstreken": len([r for r in verplicht if peildatum > r["deadline"]]),
        "aanbevolen_af": len([r for r in aanbevolen if r["status"] in (AF_OP_TIJD, AF_TE_LAAT)]),
        "aanbevolen_totaal": len(aanbevolen),
    }
