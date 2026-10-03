#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eén document per bot die bonuspunten scoorde, om mee aan tafel te gaan.

    python3 scripts/botdocumenten.py
    python3 scripts/botdocumenten.py --iedereen          # niet alleen de scoorders
    python3 scripts/botdocumenten.py --student 500123456

Schrijft scripts/botdocumenten/<studentnummer>.html: de plots die ze in
Werkcollege 8 zelf hebben gemaakt, maar dan over hún bot, met daaronder de
vragen die uit die cijfers volgen.

WAAROM DIT WERKT ALS OVERHORING
-------------------------------
De getallen komen uit het log van zijn eigen toernooi. Dat log heeft hij nooit
gezien -- hij kent zijn bot van de code, niet van wat die 972 handen lang
werkelijk deed. De confrontatie tussen "wat ik dacht dat mijn bot deed" en wat
er staat, is de vraag. Voorbereiden kan niet, want hij weet niet welk getal er
uit komt.

De vragen zijn daarom ook geen quizvragen met één goed antwoord. Het goede
antwoord is een redenering over zijn eigen regels.

Alle plaatjes zitten als data-URI in het bestand, dus één HTML per student is
compleet -- geen map met losse PNG's die kwijtraakt.
"""
import argparse
import base64
import io
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)

from botkaarten import (handsoort, klas_medianen, opvallende_handen,  # noqa: E402
                        profiel, winst_per_regel)

INKT = "#121E31"
GEDEMPT = "#5A646B"
BLAUW = "#2a78d6"
ORANJE = "#eb6834"
AQUA = "#1baf7a"
GROEN = "#1B5E4A"
LIJN = "#DCE3DE"

VOLGORDE = ["fold", "call", "raise", "grote_raise", "all_in"]

# De vijf acties hebben een VOLGORDE: fold is opgeven, all_in is alles erin. Dat
# is geen categorie maar een oplopende schaal, dus een tint die donkerder wordt
# naarmate er meer wordt ingezet -- niet vijf losse kleuren. Dezelfde ramp als
# analyse_toernooi.py gebruikt, lichtheid monotoon van 0,775 naar 0,087 en 6,0:1
# tussen de uitersten. De percentages staan erbij, want de lichtste stap haalt
# in zijn eentje geen 3:1 met de achtergrond.
ACTIEKLEUR = dict(zip(VOLGORDE,
                      ["#d7e6f2", "#a8cfdc", "#6fb8ae", "#3a8f7a", "#1B5E4A"]))
# Op welke stappen een wit label leesbaar is.
ACTIE_LABEL_WIT = {"grote_raise", "all_in"}
STRATEN = ["preflop", "flop", "turn", "river"]


def kaal(ax, y=True):
    for kant in ("top", "right"):
        ax.spines[kant].set_visible(False)
    ax.spines["left"].set_color(LIJN)
    ax.spines["bottom"].set_color(LIJN)
    ax.tick_params(colors=GEDEMPT, labelsize=10)
    if y:
        ax.grid(axis="y", color=LIJN, linewidth=0.8)
        ax.set_axisbelow(True)


def nl(getal):
    """1829 -> '1.829'. Nederlandse duizendtallen."""
    return f"{getal:,}".replace(",", ".")


def als_uri(fig):
    """De plaat als data-URI, zodat het document één bestand blijft."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", pad_inches=0.2)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


# ---------------------------------------------------------------- de platen
def plaat_stackverloop(eigen_log):
    """Twintig simulaties, met de beste en de slechtste uitgelicht."""
    per_sim = defaultdict(list)
    for r in eigen_log:
        per_sim[r["simulatie"]].append((r["hand_nummer"], r["stack"]))
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    eind = {}
    for sim, punten in per_sim.items():
        punten.sort()
        x = [p[0] for p in punten]
        y = [p[1] for p in punten]
        eind[sim] = y[-1]
        ax.plot(x, y, color=GEDEMPT, linewidth=1.0, alpha=0.35, zorder=2)
    # Welke twee licht je uit? Normaal de beste en de slechtste eindstand. Maar een
    # bot die in elke simulatie op 0 eindigt heeft die niet: dan vallen de twee
    # lijnen samen, staat er twee keer "0 chips" in de legenda, en ligt het echte
    # verhaal -- een simulatie die eerst naar 3300 liep -- in het grijs.
    piek = {sim: max(s for _, s in punten) for sim, punten in per_sim.items()}
    if len(set(eind.values())) > 1:
        uitgelicht = ((max(eind, key=eind.get), AQUA, "beste simulatie",
                       lambda s: f"{eind[s]} chips"),
                      (min(eind, key=eind.get), BLAUW, "slechtste simulatie",
                       lambda s: f"{eind[s]} chips"))
    else:
        gelijk = next(iter(eind.values()))
        uitgelicht = ((max(piek, key=piek.get), AQUA, "hoogste piek",
                       lambda s: f"tot {piek[s]} chips"),
                      (min(piek, key=piek.get), BLAUW, "laagste piek",
                       lambda s: f"tot {piek[s]} chips"))
        ax.text(0.985, 0.955,
                f"elke simulatie eindigde op {gelijk}",
                transform=ax.transAxes, ha="right", va="top",
                color=GEDEMPT, fontsize=10, style="italic")

    for sim, kleur, label, waarde in uitgelicht:
        punten = sorted(per_sim[sim])
        ax.plot([p[0] for p in punten], [p[1] for p in punten],
                color=kleur, linewidth=2.5, zorder=4,
                label=f"{label} ({waarde(sim)})")
    ax.axhline(1000, color=GEDEMPT, linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    ax.set_xlabel("hand")
    ax.set_ylabel("stack (chips)")
    ax.set_title("Dezelfde bot, dezelfde regels — twintig keer een ander verhaal",
                 color=INKT, fontsize=12.5, pad=12, loc="left")
    ax.legend(frameon=False, fontsize=10, loc="upper left")
    kaal(ax)
    return als_uri(fig), {"beste": max(eind.values()), "slechtste": min(eind.values())}


def plaat_acties_tegenover_klas(eigen, rest):
    """Wat elke actie oplevert, naast wat diezelfde actie de klas oplevert."""
    def gemiddelden(regels):
        per = defaultdict(list)
        for r in regels:
            if r["actie"]:
                per[r["actie"]].append(r["winst"])
        return {a: statistics.fmean(v) for a, v in per.items()}, \
               {a: len(v) for a, v in per.items()}

    mijn, aantal = gemiddelden(eigen)
    hun, _ = gemiddelden(rest)
    acties = [a for a in VOLGORDE if a in mijn or a in hun]

    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    y = np.arange(len(acties))
    ax.barh(y + 0.19, [hun.get(a, 0) for a in acties], height=0.36,
            color=GEDEMPT, alpha=0.55, label="de rest van de klas")
    ax.barh(y - 0.19, [mijn.get(a, 0) for a in acties], height=0.36,
            color=ORANJE, label="deze bot")
    for i, a in enumerate(acties):
        if a not in mijn:
            continue
        waarde = mijn[a]
        ax.text(waarde + (6 if waarde >= 0 else -6), i - 0.19,
                f"{waarde:+.0f}  (n={aantal[a]})", va="center",
                ha="left" if waarde >= 0 else "right",
                color=INKT, fontsize=9.5, fontweight="bold")
    ax.axvline(0, color=INKT, linewidth=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([a.replace("_", " ") for a in acties], fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel("gemiddelde winst per hand (chips)")
    ax.set_title("Levert zijn raise meer op dan die van de klas?",
                 color=INKT, fontsize=12.5, pad=26, loc="left")
    ax.legend(frameon=False, fontsize=10, ncol=2, loc="lower right",
              bbox_to_anchor=(1.0, 1.005))
    kaal(ax, y=False)
    alles = [v for v in list(mijn.values()) + list(hun.values())]
    marge = (max(alles) - min(min(alles), 0)) * 0.3
    ax.set_xlim(min(min(alles), 0) - marge, max(alles) + marge)
    return als_uri(fig)


def plaat_handsoorten(prof):
    """Per soort hand: wat deed hij ermee? Gestapeld op percentage."""
    soorten = [s for s in ("paar", "twee hoge", "één hoge", "twee lage")
               if s in prof["per_handsoort"]]
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    links = np.zeros(len(soorten))
    for actie in VOLGORDE:
        waarden = []
        for s in soorten:
            teller = prof["per_handsoort"][s]
            totaal = sum(teller.values()) or 1
            waarden.append(100 * teller.get(actie, 0) / totaal)
        waarden = np.array(waarden)
        if waarden.sum() == 0:
            continue
        ax.barh(soorten, waarden, left=links, height=0.62,
                color=ACTIEKLEUR[actie], label=actie.replace("_", " "))
        for i, w in enumerate(waarden):
            if w >= 7:
                ax.text(links[i] + w / 2, i, f"{w:.0f}%", ha="center", va="center",
                        color="white" if actie in ACTIE_LABEL_WIT else INKT,
                        fontsize=9.5, fontweight="bold")
        links += waarden
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.set_xlabel("aandeel van de handen van dat soort")
    ax.set_title("Wat deed hij met welke kaarten?", color=INKT,
                 fontsize=12.5, pad=26, loc="left")
    ax.legend(frameon=False, fontsize=9.5, ncol=5, loc="lower right",
              bbox_to_anchor=(1.0, 1.005))
    kaal(ax, y=False)
    ax.tick_params(axis="y", labelsize=11)
    return als_uri(fig)


def plaat_per_ronde(beslissingen):
    """Hoe ver kwam hij per hand, en wat deed hij daar? Uit de uitgebreide log."""
    per_ronde = defaultdict(Counter)
    for b in beslissingen:
        per_ronde[b["ronde"]][b["gekozen"]] += 1
    straten = [s for s in STRATEN if s in per_ronde]
    if not straten:
        return None

    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    onder = np.zeros(len(straten))
    for actie in VOLGORDE:
        waarden = np.array([per_ronde[s].get(actie, 0) for s in straten])
        if waarden.sum() == 0:
            continue
        ax.bar(straten, waarden, bottom=onder, width=0.58,
               color=ACTIEKLEUR[actie], label=actie.replace("_", " "))
        onder += waarden
    for i, s in enumerate(straten):
        totaal = sum(per_ronde[s].values())
        ax.text(i, totaal + max(onder) * 0.025, str(totaal), ha="center",
                color=INKT, fontsize=10, fontweight="bold")
    ax.set_ylabel("aantal beslissingen")
    ax.set_title("Hoe ver kwam hij per hand, en wat deed hij daar?",
                 color=INKT, fontsize=12.5, pad=26, loc="left")
    ax.legend(frameon=False, fontsize=9.5, ncol=5, loc="lower right",
              bbox_to_anchor=(1.0, 1.005))
    kaal(ax)
    ax.set_ylim(0, max(onder) * 1.14)
    return als_uri(fig)


# ---------------------------------------------------------------- de vragen
def maak_vragen(prof, mediaan, eigen, beslissingen, plek, aantal, stand):
    """
    Vragen die uit zijn eigen cijfers volgen.

    Geen quizvragen: het goede antwoord is een redenering over zijn eigen regels.
    Elke vraag draagt het getal waar hij vandaan komt, zodat je hem kunt stellen
    zonder vooraf te rekenen.
    """
    vragen = []
    totaal = prof["aan_zet"] or 1

    def deel(actie):
        return 100 * prof["acties"].get(actie, 0) / totaal

    # 1 -- altijd: de afwijking die het grootst is
    afwijkingen = []
    for actie in VOLGORDE:
        mijn, hun = deel(actie), mediaan.get(actie, 0)
        if prof["acties"].get(actie, 0) >= 10:
            afwijkingen.append((abs(mijn - hun), actie, mijn, hun))
    if afwijkingen:
        _, actie, mijn, hun = max(afwijkingen)
        richting = "veel vaker" if mijn > hun else "veel minder vaak"
        vragen.append((
            f"Je bot koos <b>{actie.replace('_', ' ')}</b> in {mijn:.0f}% van de handen "
            f"waarin hij aan zet kwam. De klasmediaan is {hun:.0f}%.",
            f"Je doet dit dus {richting} dan de rest. Welke regel in jouw code "
            f"veroorzaakt dat, en was dat de bedoeling?"))

    # 2 -- een actie die geld kost
    verliezend = [(w, a) for a, w in prof["winst_per_actie"].items()
                  if w < 0 and prof["acties"].get(a, 0) >= 10]
    if verliezend:
        w, a = min(verliezend)
        vragen.append((
            f"<b>{a.replace('_', ' ')}</b> leverde je gemiddeld {w:+.0f} chips per hand op, "
            f"over de {prof['acties'][a]} handen waarin dat je <i>eerste</i> actie was.",
            "Dat is een actie die je geld kost. Wanneer kiest je bot hem, en wat zou "
            "er gebeuren als je die drempel verschuift?"))

    # 3 -- handsoort waar iets opvalt
    for soort in ("paar", "twee hoge"):
        teller = prof["per_handsoort"].get(soort)
        if not teller:
            continue
        n = sum(teller.values())
        gefold = 100 * teller.get("fold", 0) / n if n else 0
        if n >= 15 and gefold >= 20:
            vragen.append((
                f"Van je {n} handen met <b>{soort}</b> foldde je er "
                f"{teller['fold']} ({gefold:.0f}%).",
                "Dat zijn de sterkere handen. Welke voorwaarde in je code zorgt "
                "dat je die toch weggooit?"))
            break

    # 4 -- uit de uitgebreide log: hoe ver kom je
    if beslissingen:
        per_ronde = Counter(b["ronde"] for b in beslissingen)
        preflop = per_ronde.get("preflop", 0) or 1
        river = per_ronde.get("river", 0)
        aandeel = 100 * river / preflop
        if aandeel < 8:
            vragen.append((
                f"Van je {preflop} preflop-beslissingen kwamen er maar "
                f"<b>{river}</b> tot de river ({aandeel:.0f}%).",
                "Je bent vroeg uit de hand. Dat is veilig, maar je wint ook nooit "
                "een grote pot. Waar zit die rem in je code?"))
        elif aandeel > 25:
            vragen.append((
                f"Van je {preflop} preflop-beslissingen kwamen er <b>{river}</b> "
                f"tot de river ({aandeel:.0f}%).",
                "Je betaalt vaak door tot het einde. Kijkt je bot onderweg nog of "
                "zijn hand nog goed is, of alleen bij het begin?"))

        # wat kostte callen?
        calls = [b for b in beslissingen
                 if b["gekozen"] == "call" and b["inzet_om_te_callen"] > 0]
        if len(calls) >= 10:
            odds = [b["inzet_om_te_callen"] / (b["pot"] + b["inzet_om_te_callen"])
                    for b in calls]
            vragen.append((
                f"Over alle straten samen callde je {len(calls)} keer tegen een inzet, "
                f"en betaalde je daarbij gemiddeld "
                f"<b>{100*statistics.fmean(odds):.0f}%</b> van de pot om mee te mogen doen.",
                "Je hand hoeft dus maar in dat percentage van de gevallen de beste "
                "te zijn om dat lonend te maken. Rekent je bot dat uit, of callt hij "
                "op de kaarten alleen?"))

    # 5 -- altijd: de spreiding
    vragen.append((
        f"Je eindigde op <b>{stand}</b> chips, plek {plek} van {aantal}.",
        "Over twintig simulaties zat daar een flinke spreiding in. Wat zou er "
        "gebeuren als we dit toernooi met een andere kaartverdeling opnieuw "
        "draaiden — en hoeveel van je plek is dan nog van jou?"))
    return vragen


# ---------------------------------------------------------------- het document
STIJL = """
  :root{
    --vilt:#1B4D3E;--inkt:#121E31;--papier:#F7F8F6;--vlak:#FFFFFF;
    --vlak-zacht:#EEF2EF;--gedempt:#59636B;--lijn:#DCE3DE;--oker:#8A6A12;
  }
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --vilt:#5FB894;--inkt:#E6EDE9;--papier:#10171A;--vlak:#161F23;
    --vlak-zacht:#1C282B;--gedempt:#9AA8A4;--lijn:#2A3A3B;--oker:#D8B25A;}}
  :root[data-theme="dark"]{
    --vilt:#5FB894;--inkt:#E6EDE9;--papier:#10171A;--vlak:#161F23;
    --vlak-zacht:#1C282B;--gedempt:#9AA8A4;--lijn:#2A3A3B;--oker:#D8B25A;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--papier);color:var(--inkt);
    font-family:"Public Sans","Segoe UI",system-ui,-apple-system,sans-serif;
    font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased}
  .blad{max-width:52rem;margin:0 auto;padding:2.8rem 1.4rem 5rem}
  h1,h2{font-family:Literata,Georgia,serif;text-wrap:balance;margin:0}
  h1{font-size:2.1rem;font-weight:700;line-height:1.16;letter-spacing:-.015em}
  h2{font-size:1.4rem;font-weight:600;margin:2.8rem 0 .3rem}
  .stempel{font-family:"IBM Plex Mono",monospace;font-size:.72rem;
    text-transform:uppercase;letter-spacing:.12em;color:var(--vilt);
    font-weight:500;display:block;margin-bottom:.8rem}
  header{border-bottom:2px solid var(--vilt);padding-bottom:1.6rem;margin-bottom:1.4rem}
  .kerncijfers{display:flex;flex-wrap:wrap;gap:1.6rem 2.6rem;margin-top:1.2rem}
  .kerncijfer .label{font-family:"IBM Plex Mono",monospace;font-size:.7rem;
    text-transform:uppercase;letter-spacing:.08em;color:var(--gedempt);display:block}
  .kerncijfer .waarde{font-size:1.5rem;font-weight:700;
    font-variant-numeric:tabular-nums;line-height:1.2}
  .sub{color:var(--gedempt);font-size:.88rem;margin:.2rem 0 1rem;max-width:42rem}
  figure{margin:1.4rem 0 0}
  figure img{width:100%;height:auto;display:block;border:1px solid var(--lijn);border-radius:4px}
  .vraag{background:var(--vlak);border-left:3px solid var(--vilt);
    padding:1rem 1.1rem;margin:1rem 0 0;border-radius:0 4px 4px 0}
  .vraag .cijfer{margin:0;font-size:.95rem}
  .vraag .stel{margin:.55rem 0 0;font-weight:600;color:var(--vilt)}
  .nummer{font-family:"IBM Plex Mono",monospace;font-size:.72rem;color:var(--gedempt);
    letter-spacing:.08em;display:block;margin-bottom:.35rem}
  table{border-collapse:collapse;width:100%;font-size:.88rem;margin-top:1rem}
  th,td{text-align:left;padding:.4rem .8rem .4rem 0;border-bottom:1px solid var(--lijn)}
  th{font-family:"IBM Plex Mono",monospace;font-size:.7rem;text-transform:uppercase;
    letter-spacing:.06em;color:var(--gedempt);font-weight:500}
  td.getal{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}
  footer{margin-top:3rem;padding-top:1.2rem;border-top:1px solid var(--lijn);
    color:var(--gedempt);font-size:.82rem}
  code{font-family:"IBM Plex Mono",monospace;font-size:.89em;
    background:var(--vlak-zacht);padding:.08em .34em;border-radius:3px}
"""


def bouw_document(student, bonus, plek, aantal, stand, platen, vragen, handen,
                  week, ronde):
    def figuur(uri, bijschrift):
        if not uri:
            return ""
        return (f'<figure><img src="{uri}" alt="{bijschrift}">'
                f'<figcaption class="sub">{bijschrift}</figcaption></figure>')

    vraagblokken = "".join(
        f'<div class="vraag"><span class="nummer">Vraag {i}</span>'
        f'<p class="cijfer">{cijfer}</p><p class="stel">{stel}</p></div>'
        for i, (cijfer, stel) in enumerate(vragen, 1))

    handrijen = "".join(
        f'<tr><td class="getal">{h["waar"]}</td><td class="getal">{h["hand"]}</td>'
        f'<td>{h["actie"]}</td><td class="getal">{h["winst"]:+d}</td>'
        f'<td>{h["waarom"]}</td></tr>' for h in handen)

    return f"""<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bot {student}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600;7..72,700&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{STIJL}</style></head><body><div class="blad">

<header>
  <span class="stempel">Poker Analytics Challenge &middot; week {week}, toernooi {ronde} &middot; overhoring</span>
  <h1>Bot {student}</h1>
  <div class="kerncijfers">
    <div class="kerncijfer"><span class="label">eindstand</span>
      <span class="waarde">{nl(stand)}</span></div>
    <div class="kerncijfer"><span class="label">plek</span>
      <span class="waarde">{plek} <span style="font-size:.95rem;font-weight:400;color:var(--gedempt)">van {aantal}</span></span></div>
    <div class="kerncijfer"><span class="label">bonus</span>
      <span class="waarde" style="color:var(--vilt)">{bonus}</span></div>
  </div>
</header>

<p class="sub">Alle cijfers hieronder komen uit het logboek van dit toernooi. Die data
heeft deze student nooit gezien: hij kent zijn bot van de code, niet van wat die
honderden handen lang werkelijk deed.</p>

<h2>Wat zijn bot deed</h2>
{figuur(platen.get("handsoorten"), "Per soort hand: welk deel ging weg, welk deel werd gespeeld.")}
{figuur(platen.get("per_ronde"), "Uit de uitgebreide log: op welke straat viel de beslissing, en welke.")}

<h2>Wat het opleverde</h2>
{figuur(platen.get("acties"), "Gemiddelde winst per hand, per actie, naast dezelfde actie bij de rest van de klas.")}
{figuur(platen.get("stackverloop"), "Twintig simulaties met dezelfde code. De spreiding is het punt.")}

<h2>Vragen om te stellen</h2>
<p class="sub">Geen quizvragen. Het goede antwoord is een redenering over zijn eigen
regels — en of hij het verschil ziet tussen wat hij dacht dat zijn bot deed en wat
er staat.</p>
{vraagblokken}

<h2>Handen om op door te vragen</h2>
<table>
  <thead><tr><th>waar</th><th>hand</th><th>deed</th><th>chips</th><th>waarom deze</th></tr></thead>
  <tbody>{handrijen}</tbody>
</table>
<p class="sub">Naspelen kan met
<code>python3 scripts/laat_hand_zien.py --ronde {ronde} --bot {student}</code>.</p>

<footer>
  Gemaakt met <code>scripts/botdocumenten.py</code> uit het logboek van week {week},
  toernooi {ronde}. De plots zijn dezelfde als in Werkcollege 8, maar dan over deze bot.
</footer>

</div></body></html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde", default="2")
    p.add_argument("--student", help="alleen dit studentnummer")
    p.add_argument("--iedereen", action="store_true",
                   help="ook de studenten zonder bonuspunten")
    args = p.parse_args()

    with open(os.path.join(HIER, f"uitslag_week{args.week}_ronde{args.ronde}.json")) as f:
        uitslag = json.load(f)
    uitgebreid = []
    pad = os.path.join(HIER, f"uitgebreid_week{args.week}_ronde{args.ronde}.json")
    if os.path.exists(pad):
        with open(pad) as f:
            uitgebreid = json.load(f)["regels"]

    bonussen = {}
    pad_bonus = os.path.join(HIER, f"bonus_week{args.week}.json")
    if os.path.exists(pad_bonus):
        with open(pad_bonus) as f:
            for s in json.load(f)["studenten"]:
                bonussen[s["student_id"]] = s["bonus"]

    KLAS = set(uitslag["namen_deelnemers"])
    regels = winst_per_regel(uitslag["hand_log"])
    per_bot = defaultdict(list)
    for r in regels:
        per_bot[r["bot_naam"]].append(r)
    profielen = {b: profiel(rs) for b, rs in per_bot.items() if b in KLAS}
    mediaan = klas_medianen(profielen)

    stand = sorted(((v, k) for k, v in uitslag["eindstand_per_bot"].items() if k in KLAS),
                   reverse=True)
    plekken = {k: i for i, (_, k) in enumerate(stand, 1)}

    beslissingen_per_bot = defaultdict(list)
    for b in uitgebreid:
        beslissingen_per_bot[b["bot_naam"]].append(b)

    if args.student:
        doelen = [args.student]
    elif args.iedereen:
        doelen = [k for _, k in stand]
    else:
        doelen = [k for _, k in stand if bonussen.get(k, 0) > 0]
        if not doelen:
            raise SystemExit(
                f"Geen bonusscoorders gevonden in bonus_week{args.week}.json.\n"
                f"Haal hem op met scripts/controleer_opslag.py, of gebruik --iedereen.")

    uitvoer = os.path.join(HIER, "botdocumenten")
    os.makedirs(uitvoer, exist_ok=True)
    print(f"Week {args.week}, toernooi {args.ronde} — {len(doelen)} document(en)\n")

    for student in doelen:
        if student not in profielen:
            print(f"   {student}: niet in dit toernooi")
            continue
        eigen = per_bot[student]
        rest = [r for b, rs in per_bot.items() if b in KLAS and b != student for r in rs]
        prof = profielen[student]
        eigen_log = [r for r in uitslag["hand_log"] if r["bot_naam"] == student]
        beslissingen = beslissingen_per_bot.get(student, [])

        platen = {}
        platen["stackverloop"], _ = plaat_stackverloop(eigen_log)
        platen["acties"] = plaat_acties_tegenover_klas(eigen, rest)
        platen["handsoorten"] = plaat_handsoorten(prof)
        platen["per_ronde"] = plaat_per_ronde(beslissingen)

        vragen = maak_vragen(prof, mediaan, eigen, beslissingen,
                             plekken[student], len(stand),
                             int(uitslag["eindstand_per_bot"][student]))
        # opvallende_handen geeft (regel, waarom) terug, niet een dict.
        handen = [{"waar": f"sim {r['simulatie']}, tafel {r['tafel']}, hand {r['hand_nummer']}",
                   "hand": "-".join(r["hand"]), "actie": r["actie"] or "—",
                   "winst": int(r["winst"]), "waarom": waarom}
                  for r, waarom in opvallende_handen(eigen)]

        bonus = bonussen.get(student)
        html = bouw_document(
            student, f"{bonus:.1f}".replace(".", ",") if bonus else "—",
            plekken[student], len(stand),
            int(uitslag["eindstand_per_bot"][student]),
            platen, vragen, handen, args.week, args.ronde)
        doel = os.path.join(uitvoer, f"{student}.html")
        with open(doel, "w") as f:
            f.write(html)
        print(f"   {student}  plek {plekken[student]:>2d}  bonus {bonus or 0:.1f}  "
              f"{len(vragen)} vragen  ->  botdocumenten/{student}.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
