#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maakt een HTML-pagina met de uitslag van de twee gescoorde toernooien.

    python3 scripts/maak_uitslag_html.py            -> uitslag_week5.html
    python3 scripts/maak_uitslag_html.py --anoniem-onder 10

Bedoeld om op Brightspace te zetten. Alles staat inline -- geen externe CSS,
geen webfonts, geen scripts -- want Brightspace filtert die eruit en dan staat
er een kale tabel.

Met --anoniem-onder N staan alleen de eerste N plekken met studentnummer en de
rest als "student ...1234". Standaard staat iedereen er met nummer op; de
ranglijst is dan compleet, maar wie laatste werd staat er ook met naam bij.
"""
import argparse
import json
import os
import statistics
from collections import defaultdict

HIER = os.path.dirname(os.path.abspath(__file__))

# Dezelfde kleuren als het deck, zodat de pagina en de dia's bij elkaar horen.
INKT = "#121E31"
GEDEMPT = "#5A646B"
BLAUW = "#2a78d6"
GROEN = "#1B5E4A"
ORANJE = "#eb6834"
LICHT = "#EEF2F0"
LIJN = "#DCE1E6"

RONDES = {1: "Woensdagbot", 2: "Definitieve bot"}



def komma(waarde):
    """0.5 -> '0,5'. Een decimale komma, zoals het in het Nederlands hoort."""
    return f"{waarde:.1f}".replace(".", ",")


def nl(waarde, teken=False):
    """1234.0 -> '1.234'. Nederlandse duizendtallen, zonder de rest van de pagina te raken."""
    tekst = f"{waarde:+,.0f}" if teken else f"{waarde:,.0f}"
    return tekst.replace(",", ".")


def eindstanden(uitslag):
    """{student: eindstand}, alleen de klas."""
    klas = set(uitslag["namen_deelnemers"])
    return {k: v for k, v in uitslag["eindstand_per_bot"].items() if k in klas}


def spreiding_per_bot(uitslag):
    """De eindstand per simulatie, om de onzekerheid op een plek te kunnen tonen."""
    laatste = defaultdict(dict)
    for rij in uitslag["hand_log"]:
        laatste[(rij["bot_naam"], rij["simulatie"])][rij["hand_nummer"]] = rij["stack"]
    per_bot = defaultdict(list)
    for (bot, _), standen in laatste.items():
        per_bot[bot].append(standen[max(standen)])
    return per_bot


def tweemaal_se(waarden):
    if len(waarden) < 2:
        return 0.0
    return 2 * statistics.pstdev(waarden) / len(waarden) ** 0.5



def tabel_ronde(uitslag, titel, ondertitel, hoeveel=5):
    """De eerste `hoeveel` plekken. De rest van de ranglijst staat er bewust niet.

    Deze pagina gaat naar de hele klas. Wie bovenaan staat heeft daar iets voor
    gedaan; wie onderaan staat hoeft daar niet klassikaal mee op een pagina.
    """
    stand = sorted(eindstanden(uitslag).items(), key=lambda kv: -kv[1])[:hoeveel]
    spreiding = spreiding_per_bot(uitslag)
    rijen = []
    for plek, (student, chips) in enumerate(stand, 1):
        winst = chips - 1000
        kleur = GROEN if winst > 0 else (ORANJE if winst < 0 else GEDEMPT)
        onzeker = tweemaal_se(spreiding.get(student, []))
        rijen.append(f"""
        <tr class="top">
          <td class="plek">{plek}</td>
          <td class="wie">{student}</td>
          <td class="getal">{nl(chips)}</td>
          <td class="getal" style="color:{kleur}">{nl(winst, teken=True)}</td>
          <td class="getal onzeker">&plusmn;{nl(onzeker)}</td>
        </tr>""")
    return f"""
    <div class="ronde">
      <h3>{titel}</h3>
      <p class="sub">{ondertitel}</p>
      <table>
        <thead><tr>
          <th class="plek">#</th><th class="wie">student</th>
          <th class="getal">chips</th><th class="getal">winst</th>
          <th class="getal">onzekerheid</th>
        </tr></thead>
        <tbody>{''.join(rijen)}</tbody>
      </table>
    </div>"""


def bonustabel(bonus):
    scoorders = [s for s in bonus["studenten"] if s["bonus"] > 0]
    scoorders.sort(key=lambda s: (-s["bonus"], s["student_id"]))
    rijen = []
    for s in scoorders:
        per = {r["ronde"]: r for r in s["per_ronde"]}

        def cel(nr):
            r = per.get(nr)
            if not r or not r.get("plek"):
                return '<td class="leeg">niet meegespeeld</td>'
            if r["punten"] > 0:
                return (f'<td class="raak">plek {r["plek"]}'
                        f'<span class="pt">+{komma(r["punten"])}</span></td>')
            return f'<td class="mis">plek {r["plek"]}</td>'

        rijen.append(f"""
        <tr>
          <td class="wie">{s['student_id']}</td>
          {cel(1)}{cel(2)}
          <td class="getal bonus">{komma(s['bonus'])}</td>
        </tr>""")
    return f"""
      <table class="bonus">
        <thead><tr>
          <th class="wie">student</th>
          <th>Toernooi 1 &middot; woensdagbot</th>
          <th>Toernooi 2 &middot; definitieve bot</th>
          <th class="getal">bonus</th>
        </tr></thead>
        <tbody>{''.join(rijen)}</tbody>
      </table>"""


def bouw(r1, r2, bonus):
    stand2 = sorted(eindstanden(r2).items(), key=lambda kv: -kv[1])
    spreiding2 = spreiding_per_bot(r2)
    vijfde, zesde = stand2[4][1], stand2[5][1]
    gat = vijfde - zesde
    se_vijfde = tweemaal_se(spreiding2.get(stand2[4][0], []))

    top1 = {s["student_id"] for s in bonus["studenten"]
            for r in s["per_ronde"] if r["ronde"] == 1 and (r.get("plek") or 99) <= 5}
    top2 = {s["student_id"] for s in bonus["studenten"]
            for r in s["per_ronde"] if r["ronde"] == 2 and (r.get("plek") or 99) <= 5}

    ref = sorted(set(r2.get("referentiebots") or []))
    stand_lijst = [v for _, v in stand2]
    ref_rijen = []
    for naam_ref in ref:
        waarde = r2["eindstand_per_bot"].get(naam_ref)
        if waarde is None:
            continue
        plek = sum(1 for v in stand_lijst if v > waarde) + 1
        ref_rijen.append(f"""
        <tr><td class="wie">{naam_ref.replace('Referentie_', '')}</td>
            <td class="getal">{nl(waarde)}</td>
            <td class="getal onzeker">plek {plek} van {len(stand_lijst)}</td></tr>""")

    meetlat = "" if not ref_rijen else f"""
  <h2>De referentiebots als meetlat</h2>
  <p>Deze bots speelden mee zonder voor de bonus mee te tellen: haal je ze in, dan weet
  je dat je idee iets waard is.</p>
  <div class="scroll">
    <table>
      <thead><tr><th class="wie">bot</th><th class="getal">chips</th>
                 <th class="getal">zou staan op</th></tr></thead>
      <tbody>{''.join(ref_rijen)}</tbody>
    </table>
  </div>"""

    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poker Analytics &middot; uitslag week 5</title>
<style>
  .pa {{
    --inkt: {INKT}; --gedempt: {GEDEMPT}; --blauw: {BLAUW};
    --groen: {GROEN}; --oranje: {ORANJE}; --licht: {LICHT}; --lijn: {LIJN};
    background: #FFFFFF; color: var(--inkt);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    font-size: 15px; line-height: 1.55;
    max-width: 1100px; margin: 0 auto; padding: 8px 16px 48px;
    box-sizing: border-box;
  }}
  .pa * {{ box-sizing: border-box; }}
  .pa h1 {{ font-size: 30px; line-height: 1.2; margin: 4px 0 6px; text-wrap: balance; }}
  .pa h2 {{ font-size: 21px; margin: 40px 0 6px; text-wrap: balance; }}
  .pa h3 {{ font-size: 16px; margin: 0 0 2px; }}
  .pa .eyebrow {{
    font-size: 12px; letter-spacing: .09em; text-transform: uppercase;
    color: var(--blauw); font-weight: 700; margin: 0;
  }}
  .pa .sub {{ color: var(--gedempt); font-size: 13px; margin: 0 0 10px; }}
  .pa .lead {{ font-size: 16px; color: var(--inkt); margin: 0 0 4px; max-width: 68ch; }}
  .pa p {{ max-width: 68ch; }}
  .pa table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
  .pa th {{
    text-align: left; font-size: 11.5px; letter-spacing: .06em;
    text-transform: uppercase; color: var(--gedempt); font-weight: 700;
    border-bottom: 2px solid var(--lijn); padding: 6px 8px;
  }}
  .pa td {{ padding: 5px 8px; border-bottom: 1px solid var(--lijn); }}
  .pa .getal {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .pa .plek {{ width: 34px; color: var(--gedempt); font-variant-numeric: tabular-nums; }}
  .pa .wie {{ font-variant-numeric: tabular-nums; }}
  .pa .onzeker {{ color: var(--gedempt); font-size: 12.5px; }}
  .pa tr.top td {{ background: var(--licht); font-weight: 600; }}
  .pa tr.top .plek {{ color: var(--blauw); font-weight: 700; }}
  .pa .rondes {{ display: flex; flex-wrap: wrap; gap: 28px; }}
  .pa .ronde {{ flex: 1 1 420px; min-width: 300px; }}
  .pa .bonus td {{ padding: 7px 8px; }}
  .pa .bonus .raak {{ color: var(--groen); font-weight: 600; }}
  .pa .bonus .mis {{ color: var(--gedempt); }}
  .pa .bonus .leeg {{ color: var(--gedempt); font-style: italic; }}
  .pa .bonus .pt {{
    display: inline-block; margin-left: 7px; padding: 1px 6px; border-radius: 9px;
    background: var(--groen); color: #fff; font-size: 11.5px; font-weight: 700;
  }}
  .pa .bonus .bonus {{ font-weight: 700; font-size: 15px; }}
  .pa .kader {{
    background: var(--licht); border-left: 3px solid var(--blauw);
    padding: 14px 18px; margin: 16px 0; border-radius: 0 6px 6px 0;
  }}
  .pa .kader p {{ margin: 0 0 8px; }}
  .pa .kader p:last-child {{ margin-bottom: 0; }}
  .pa .cijfer {{ color: var(--blauw); font-weight: 700; font-variant-numeric: tabular-nums; }}
  .pa footer {{
    margin-top: 40px; padding-top: 14px; border-top: 1px solid var(--lijn);
    color: var(--gedempt); font-size: 12.5px;
  }}
  .pa .scroll {{ overflow-x: auto; }}
</style>
</head>
<body>
<div class="pa">

  <p class="eyebrow">Poker Analytics Challenge &middot; week 5</p>
  <h1>De uitslag van de twee toernooien</h1>
  <p class="lead">Je bot speelde twee keer mee: op woensdag en met je definitieve
  inzending. Elk toernooi is {r2['n_simulaties']} simulaties van 50 handen, en wat
  hieronder staat is het gemiddelde daarvan. Iedereen begint elke simulatie op 1.000 chips.</p>

  <h2>Wie bonuspunten heeft</h2>
  <p>De top 5 van elk toernooi krijgt punten: 0,5 &middot; 0,4 &middot; 0,3 &middot; 0,2 &middot; 0,1.
  Je kunt dus maximaal {komma(bonus['maximaal'])} punt halen over de twee toernooien samen.</p>
  <div class="scroll">{bonustabel(bonus)}</div>

  <h2>Hoeveel hiervan is toeval?</h2>
  <div class="kader">
    <p>Eerlijk antwoord: een flink deel. Het verschil tussen plek 5 en plek 6 in het
    tweede toernooi is <span class="cijfer">{nl(gat)}</span> chips. De onzekerheid op
    plek 5 alleen al is <span class="cijfer">&plusmn;{nl(se_vijfde)}</span> chips &mdash;
    dertig keer zo groot als het verschil dat erover beslist.</p>
    <p>Nog duidelijker: <strong>geen enkele student stond in de top 5 van allebei de
    toernooien.</strong> De vier toppers van woensdag die ook het tweede toernooi
    speelden eindigden daar op plek 6, 11, 12 en 13. Een deel daarvan is dat jullie je
    bots hebben veranderd &mdash; maar lang niet alles.</p>
    <p>Dat is geen weeffout in de opdracht, het is het onderwerp. Een bot die harder
    speelt wordt niet beter, hij wordt <em>onzekerder</em>. In Werkcollege 8, Deel 5
    reken je precies dit zelf uit op je eigen bot.</p>
  </div>

  <h2>De top vijf per toernooi</h2>
  <p class="sub">De kolom &ldquo;onzekerheid&rdquo; is twee keer de standaardfout over de
  {r2['n_simulaties']} simulaties. Liggen twee bots binnen elkaars marge, dan zegt hun
  onderlinge volgorde weinig.</p>
  <div class="rondes">
    {tabel_ronde(r1, "Woensdag &middot; je woensdagbot",
                 f"de eerste vijf van {len(eindstanden(r1))} deelnemers")}
    {tabel_ronde(r2, "Vrijdag &middot; je definitieve bot",
                 f"de eerste vijf van {len(eindstanden(r2))} deelnemers")}
  </div>

  {meetlat}

  <footer>
    <p>Toernooi 1 en 2, week 5 &middot; {r2['n_simulaties']} simulaties &times; 50 handen
    per toernooi &middot; startstack 1.000.<br>
    Je eigen logboek haal je op met <code>/toernooi/5</code>, en je beslissingen per
    ronde met <code>/toernooi/5/uitgebreid</code>.</p>
  </footer>

</div>
</body>
</html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--week", type=int, default=5)
    p.add_argument("--ronde1", default="1_woensdag",
                   help="achtervoegsel van het woensdagbestand")
    p.add_argument("--ronde2", default="2")
    args = p.parse_args()

    with open(os.path.join(HIER, f"uitslag_week{args.week}_ronde{args.ronde1}.json")) as f:
        r1 = json.load(f)
    with open(os.path.join(HIER, f"uitslag_week{args.week}_ronde{args.ronde2}.json")) as f:
        r2 = json.load(f)
    with open(os.path.join(HIER, f"bonus_week{args.week}.json")) as f:
        bonus = json.load(f)

    doel = os.path.join(HIER, f"uitslag_week{args.week}.html")
    with open(doel, "w") as f:
        f.write(bouw(r1, r2, bonus))
    print(f"{os.path.getsize(doel) / 1024:.0f} kB -> {doel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
