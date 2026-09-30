"""
Het bonuspuntenschema van de Pokerbot Analytics Challenge.

De hele regel past in twee zinnen: in week 5 draaien er twee toernooien, één met
je woensdagbot en één met je definitieve bot, en in elk toernooi levert je plek
punten op -- eerste 0,5, tweede 0,4, derde 0,3, vierde 0,2, vijfde 0,1, daarna
niets. Twee keer 0,5 is samen het maximum van 1,0.

Dat is bewust alles. Een eerdere versie woog drie weken tegen elkaar af en
splitste elke week in een sprint- en een prestatiedeel; dat was niet uit te
leggen zonder tabel. Nu is er geen weging, geen deelscore en geen
deadlinecontrole in de puntentelling.

DE DEADLINE HANDHAAFT ZICHZELF
------------------------------
Er staat hier niets over te laat inleveren, en dat hoeft ook niet: een toernooi
speelt met de bots die er op dat moment zijn. Wie zijn woensdagbot pas
woensdagmiddag inlevert, doet niet mee aan het woensdagtoernooi en haalt daar
dus geen punten. Wie niets inlevert speelt niet mee. Dat is de handhaving.

WAAROM OP WINST EN NIET OP EINDSTAND
------------------------------------
Er wordt gerankt op wat je in dát toernooi hebt gewónnen: eindstand minus
startstack. Sinds september 2026 begint elke ronde schoon op 1000, dus is dat
getal gelijk aan de eindstand min 1000 en maakt de keuze voor de volgorde niets
uit.

Het blijft toch zo staan, om twee redenen. Het is de eerlijke formulering van
wat de ladder beloont -- niet hoeveel chips je hebt, maar hoeveel je er hebt
bijgespeeld -- en winst_per_bot() leest de startstacks uit de uitslag, dus als
er ooit weer met carry-over wordt gedraaid klopt de puntentelling zonder dat
hier iets aan hoeft.
"""

import itertools

MAX_BONUS = 1.0

# De week waarin de bonus te verdienen is. Weken 1 en 3 leveren geen punten op;
# dat zijn de weken waarin je de bot leert bouwen.
BONUSWEEK = 5

# Wat elke plek oplevert, per toernooi. De lijst is de hele regel: index 0 is
# plek 1. Daarbuiten is het nul. Wil je dieper of vlakker uitbetalen, dan is
# deze lijst het enige wat verandert.
PUNTEN_PER_PLEK = [0.5, 0.4, 0.3, 0.2, 0.1]

# De toernooien die punten opleveren, met de naam die de student ervoor ziet.
# Draai je er nog een tussendoor als oefening, geef die dan een rondenummer dat
# hier niet in staat; dan telt hij niet mee.
GESCOORDE_RONDES = {
    1: "je woensdagbot",
    2: "je definitieve bot",
}

# Waar elke bot in het eerste toernooi op begint. Gelijk aan
# poker_adapter.STANDAARD_INITIAL_STACK; hier los neergezet zodat dit bestand
# geen pypokerengine hoeft te importeren om een cijfer te kunnen uitrekenen.
# scripts/test_bonus_rooster.py controleert dat de twee niet uit elkaar lopen.
STANDAARD_STARTSTACK = 1000


def punten_voor_plek(plek):
    """Wat plek `plek` in één toernooi oplevert."""
    if plek < 1 or plek > len(PUNTEN_PER_PLEK):
        return 0.0
    return PUNTEN_PER_PLEK[plek - 1]


def puntentabel():
    """De hele uitbetaling op een rij, voor de uitleg aan studenten."""
    return [{"plek": plek, "punten": punten} for plek, punten in enumerate(PUNTEN_PER_PLEK, start=1)]


def _cache_sleutel(week, ronde):
    """Dezelfde sleutel die toernooi_runner gebruikt om een uitslag te bewaren."""
    return str(week) if ronde == 1 else f"{week}_ronde{ronde}"


def winst_per_bot(toernooi):
    """
    Wat elke bot in dít toernooi heeft gewonnen: eindstand minus startstack.

    Er staan geen startstacks in de uitslag zolang elke ronde schoon op
    STANDAARD_STARTSTACK begint. Het veld wordt wel gelezen, zodat een uitslag
    die ze wél heeft (bv. een oude, of een toekomstige carry-over-ronde) nog
    steeds goed wordt geteld.
    """
    eindstand = toernooi.get("eindstand_per_bot") or {}
    startstacks = toernooi.get("startstacks") or {}
    deelnemers = toernooi.get("namen_deelnemers")

    winst = {
        naam: stand - startstacks.get(naam, STANDAARD_STARTSTACK)
        for naam, stand in eindstand.items()
    }
    if deelnemers:
        # De oefenbots die het toernooi aanvullen als er nog te weinig
        # inzendingen zijn, horen niet in het klassement.
        winst = {naam: gewonnen for naam, gewonnen in winst.items() if naam in set(deelnemers)}
    return winst


def klassement(toernooi):
    """De bot-namen van dit toernooi op volgorde: meest gewonnen eerst."""
    return [naam for naam, _ in sorted(winst_per_bot(toernooi).items(), key=lambda kv: -kv[1])]


def puntenverdeling(toernooi):
    """
    Wat elke bot aan dit toernooi overhoudt: {naam: {"plek", "gedeeld_met", "punten"}}.

    Bots met exact dezelfde winst delen de plekken die ze samen innemen, en
    krijgen allemaal het gemiddelde van de punten voor die plekken. Twee bots
    die samen tweede en derde zijn krijgen dus elk (0,4 + 0,3) / 2 = 0,35. Zonder
    die regel bepaalt de willekeurige volgorde in een dictionary wie de hogere
    plek krijgt, en dat is geen verschil om een bonuspunt aan op te hangen.
    """
    winst = winst_per_bot(toernooi)
    verdeling = {}
    plek = 1
    for _, groep in itertools.groupby(sorted(winst.items(), key=lambda kv: -kv[1]), key=lambda kv: kv[1]):
        namen = [naam for naam, _ in groep]
        plekken = range(plek, plek + len(namen))
        punten = sum(punten_voor_plek(p) for p in plekken) / len(namen)
        for naam in namen:
            verdeling[naam] = {
                "plek": plek,
                "gedeeld_met": len(namen) - 1,
                "punten": round(punten, 4),
            }
        plek += len(namen)
    return verdeling


def bonus_per_student(student_id, haal_uitslag):
    """
    De bonus van één student, met per toernooi wat het opleverde en waarom.

    `haal_uitslag` is een functie die één cachesleutel aanneemt en de uitslag
    van die toernooironde teruggeeft, of None als die nog niet gedraaid is --
    in de API is dat database.laad_toernooi_resultaat. Een functie en geen
    dictionary, omdat elke ronde apart wordt opgeslagen: zo worden alleen de
    twee rondes gelezen die meetellen, en niet alles wat er ooit is gedraaid.

    Retourneert {"bonus": float, "per_ronde": [...]}. Een toernooi dat nog niet
    gedraaid is levert punten: null op -- dat is "nog niet bekend", geen nul.
    """
    per_ronde = []
    totaal = 0.0

    for ronde, omschrijving in sorted(GESCOORDE_RONDES.items()):
        toernooi = haal_uitslag(_cache_sleutel(BONUSWEEK, ronde)) or {}
        verdeling = puntenverdeling(toernooi)

        if not verdeling:
            per_ronde.append(
                {
                    "ronde": ronde,
                    "toernooi": omschrijving,
                    "maximaal": PUNTEN_PER_PLEK[0],
                    "plek": None,
                    "punten": None,
                    "uitleg": "dit toernooi is nog niet gedraaid",
                }
            )
            continue

        if student_id not in verdeling:
            per_ronde.append(
                {
                    "ronde": ronde,
                    "toernooi": omschrijving,
                    "maximaal": PUNTEN_PER_PLEK[0],
                    "plek": None,
                    "punten": 0.0,
                    "uitleg": "niet meegespeeld — geen goedgekeurde bot toen dit toernooi draaide",
                }
            )
            continue

        mijn = verdeling[student_id]
        plek, punten, gedeeld = mijn["plek"], mijn["punten"], mijn["gedeeld_met"]
        totaal += punten

        plek_tekst = f"plek {plek}"
        if gedeeld:
            plek_tekst = f"plek {plek}-{plek + gedeeld} (gedeeld met {gedeeld})"
        buiten = "" if punten else f" — buiten de top {len(PUNTEN_PER_PLEK)}"
        per_ronde.append(
            {
                "ronde": ronde,
                "toernooi": omschrijving,
                "maximaal": PUNTEN_PER_PLEK[0],
                "plek": plek,
                "punten": punten,
                "uitleg": f"{plek_tekst} van {len(verdeling)}{buiten}",
            }
        )

    return {
        "student_id": student_id,
        "bonus": round(totaal, 3),
        "maximaal": MAX_BONUS,
        "per_ronde": per_ronde,
    }


def bonus_hele_klas(submissions, haal_uitslag):
    """
    Hetzelfde voor iedereen die ooit iets heeft ingeleverd, hoogste bonus eerst.

    `submissions` is de hele db.laad_submissions(): {week: {student_id: [...]}}.
    Wie nooit inleverde staat er niet in; wie inleverde maar niet meespeelde
    staat er met 0,0, zodat de docent ziet dat er iemand buiten de boot valt.

    De uitslagen worden één keer opgehaald en daarna hergebruikt voor alle
    studenten -- anders leest een klas van 44 dezelfde twee rondes 44 keer.
    """
    studenten = {
        student_id
        for inzendingen_per_student in submissions.values()
        for student_id in inzendingen_per_student
    }
    gelezen = {
        sleutel: haal_uitslag(sleutel)
        for sleutel in (_cache_sleutel(BONUSWEEK, ronde) for ronde in GESCOORDE_RONDES)
    }
    overzicht = [bonus_per_student(student_id, gelezen.get) for student_id in studenten]
    return sorted(overzicht, key=lambda r: (-r["bonus"], r["student_id"]))
