"""
Werkt inleveren zoals het notebook het doet?

Draait de echte API in dit proces (geen server, geen poort) met een tijdelijke
database en verzonnen tokens, en roept de ECHTE lever_in() aan uit
notebooks/_hulpfuncties.py -- die van de studenten. requests.post wordt
omgeleid naar de testclient, zodat de functie zelf onveranderd blijft: als
haar payload of header niet klopt, valt het hier om.

Wat dit wel test: de hele keten van notebook-cel tot opgeslagen inzending,
inclusief validatie, tokencontrole en opnieuw inleveren.
Wat dit niet test: of Render dezelfde omgeving heeft. Dat is apart gecheckt.
"""
import json
import os
import sys
import tempfile

WORTEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WERKMAP = tempfile.mkdtemp(prefix="inlevertest_")

STUDENT = "500000042"
TOKEN = "Harten 3, Klaveren Vrouw"

os.environ.pop("DATABASE_URL", None)
os.environ["POKER_TOKENS_JSON"] = json.dumps({STUDENT: TOKEN})
os.environ["POKER_DOCENT_TOKEN"] = "docent-testtoken"
os.chdir(WERKMAP)

sys.path.insert(0, os.path.join(WORTEL, "api"))
import main
from fastapi.testclient import TestClient

# Als contextmanager, anders draait de startup-hook niet en staan de tokens
# uit POKER_TOKENS_JSON nergens -- dan geeft elke aanroep 401.
_context = TestClient(main.app)
client = _context.__enter__()

# lever_in() laten praten tegen de testclient in plaats van tegen het internet.
sys.path.insert(0, os.path.join(WORTEL, "notebooks"))
import _hulpfuncties


def nep_post(url, headers=None, json=None, timeout=None):
    return client.post(url.replace(_hulpfuncties.API_URL, ""), headers=headers, json=json)


_hulpfuncties.requests.post = nep_post


def echte_grafiek(titel, x_label, y_label):
    """
    Een echte matplotlib-figuur door export_chart_info, net als in het notebook.

    Eerst stuurde deze test een handgeschreven dictje mee, en toen kwam alles
    terug als 'niet goedgekeurd' -- terecht: er ontbraken x_label, y_label,
    library en figuur_json. De bot was steeds wel goedgekeurd. Een test die de
    helft van de payload verzint, test de helft van de keten.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.bar(["paar", "twee hoge", "rest"], [12, 34, 54], color=["#2C5AA0", "#8E7CC3", "#DFE4E9"])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(titel)
    info = _hulpfuncties.export_chart_info(fig, titel, x_label, y_label,
                                           library="matplotlib", n_kleuren=3)
    plt.close(fig)
    return info

geslaagd, gezakt = 0, []


def check(naam, voorwaarde, detail=""):
    global geslaagd
    if voorwaarde:
        geslaagd += 1
        print(f"  ok   {naam}")
    else:
        gezakt.append(f"{naam} — {detail}")
        print(f"  FOUT {naam}  {detail}")


BOT_WEEK1 = '''def kies_actie(hand):
    if hand[0] == hand[1]:
        return "raise"
    return "fold"
'''

BOT_WEEK3 = '''HOOG = {"A", "K", "Q", "J", "10"}

def kies_actie(hand, stack):
    if stack < 200:
        return "all_in"
    if hand[0] == hand[1]:
        return "raise"
    if hand[0] in HOOG and hand[1] in HOOG:
        return "call"
    return "fold"
'''

BOT_WEEK5 = '''HOOG = {"A", "K", "Q", "J", "10"}

def kies_actie(hand, stack, strategie, bluf_kans):
    if stack < 200:
        return "all_in"
    if hand[0] == hand[1]:
        return "grote_raise"
    if hand[0] in HOOG and hand[1] in HOOG:
        return "raise" if strategie == "aggressive" else "call"
    return "fold"
'''

print("\n--- Week 1: inleveren zoals Werkcollege 1 het voordoet ---")
antwoord = _hulpfuncties.lever_in(
    student_id=STUDENT, token=TOKEN, week=1, bot_code=BOT_WEEK1,
    chart_info=echte_grafiek("Mijn bot foldt vier van de vijf handen",
                             "handtype", "percentage van de handen"),
)
check("lever_in() geeft antwoord", isinstance(antwoord, dict), antwoord)
check("de inzending is goedgekeurd", antwoord.get("geldig") is True, antwoord)
check("er zit geen bot_code in het antwoord", "bot_code" not in antwoord, sorted(antwoord))

print("\n--- Opnieuw inleveren mag, en de laatste telt ---")
tweede = _hulpfuncties.lever_in(
    student_id=STUDENT, token=TOKEN, week=1,
    bot_code=BOT_WEEK1.replace('"fold"', '"call"'),
    chart_info=echte_grafiek("Versie 2 callt waar versie 1 foldde",
                             "handtype", "percentage van de handen"),
)
check("tweede inzending lukt ook", tweede.get("geldig") is True, tweede)
status = client.get(f"/status/{STUDENT}/1", params={"student_id": STUDENT},
                    headers={"Authorization": f"Bearer {TOKEN}"}).json()
check("status kent de inzending", bool(status), status)
check("het aantal pogingen klopt", status.get("aantal_inzendingen") in (2, None), status)

print("\n--- Een kapotte bot hoort te worden afgekeurd, met uitleg ---")
try:
    kapot = _hulpfuncties.lever_in(
        student_id=STUDENT, token=TOKEN, week=1,
        bot_code="def kies_actie(hand)\n    return 'fold'\n",
        chart_info=echte_grafiek("Deze hoort te worden afgekeurd",
                                 "handtype", "percentage"),
    )
    check("kapotte bot wordt niet goedgekeurd", kapot.get("geldig") is False, kapot)
    check("de bot-check wijst hem af",
          kapot.get("bot_check", {}).get("geldig") is False, kapot.get("bot_check"))
    check("met een leesbare foutmelding",
          "Syntaxfout" in (kapot.get("bot_check", {}).get("foutmelding") or ""),
          kapot.get("bot_check"))
except Exception as e:                                   # noqa: BLE001
    check("kapotte bot geeft geen crash maar een antwoord", False, f"{type(e).__name__}: {e}")

print("\n--- Verkeerd token hoort te worden geweigerd ---")
try:
    _hulpfuncties.lever_in(student_id=STUDENT, token="Schoppen 2, Ruiten 3", week=1,
                           bot_code=BOT_WEEK1,
                           chart_info=echte_grafiek("Verkeerd token", "x", "y"))
    check("verkeerd token wordt geweigerd", False, "kwam er gewoon doorheen")
except Exception as e:                                   # noqa: BLE001
    check("verkeerd token wordt geweigerd", "401" in str(e), str(e)[:120])

print("\n--- Week 3: stack erbij, strategie verplicht ---")
w3 = _hulpfuncties.lever_in(student_id=STUDENT, token=TOKEN, week=3, bot_code=BOT_WEEK3,
                            chart_info=echte_grafiek("Bot v2 wint het meest op de flop",
                                                     "ronde", "winst in chips"),
                            strategie="tight")
check("week 3 met strategie wordt goedgekeurd", w3.get("geldig") is True, w3)

print("\n--- Week 5: bluf_kans en locatie verplicht ---")
w5 = _hulpfuncties.lever_in(student_id=STUDENT, token=TOKEN, week=5, bot_code=BOT_WEEK5,
                            chart_info=echte_grafiek("Meer bluffen levert pas boven 0,3 iets op",
                                                     "bluf_kans", "winst in chips"),
                            strategie="aggressive", bluf_kans=0.3,
                            locatie={"lat": 52.37, "lon": 4.89, "plaatsnaam": "Amsterdam"})
check("week 5 compleet wordt goedgekeurd", w5.get("geldig") is True, w5)

print("\n--- Wat de docent terugziet ---")
export = client.get("/export/5", headers={"Authorization": "Bearer docent-testtoken"}).json()
check("de student staat in de export", any(r.get("student_id") == STUDENT for r in export), export)
check("de export deelt geen bot_code uit",
      all("bot_code" not in r for r in export), sorted(export[0]) if export else "leeg")

_context.__exit__(None, None, None)

print(f"\n{geslaagd} geslaagd, {len(gezakt)} gezakt")
for r in gezakt:
    print("   ", r)
sys.exit(1 if gezakt else 0)
