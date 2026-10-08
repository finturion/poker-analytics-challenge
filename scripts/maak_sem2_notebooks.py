#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maakt de notebooks voor semester 2: dezelfde stof, maar de API pas in week 3.

    python3 scripts/maak_sem2_notebooks.py

Leest notebooks/ en schrijft notebooks_sem2/. Afgeleid en niet met de hand
bijgehouden, zodat een verbetering in het origineel vanzelf meekomt.

WAAROM
------
De API zat vanaf werkcollege 1 in de stof: inleveren in WC1, en in WC2 een deel
over wat een API is (20 min), het toernooi ophalen (15) en peer review (10).
Dat is 45 van de 85 minuten van WC2, in dezelfde week waarin tien
programmeerconcepten binnenkomen -- en het bracht een categorie fouten mee die
niets met programmeren te maken heeft: tokens, 401's, netwerk.

Week 1 en 2 werken nu uit data/voorbeeldtoernooi.json: een toernooi dat
werkelijk gespeeld is, met namen in plaats van studentnummers. De API komt in
week 3, als er een bot is die het waard is om in te leveren.

HOE EEN WIJZIGING WORDT AANGEWEZEN
----------------------------------
Niet op celnummer -- dat schuift zodra er iets bij komt -- maar op een stuk tekst
dat in precies één cel moet voorkomen. Klopt dat niet meer, dan stopt het script.
Dan is het bronnotebook veranderd en moet deze bewerking mee.
"""
import argparse
import json
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
BRON = os.path.join(WORTEL, "notebooks")
DOEL = os.path.join(WORTEL, "notebooks_sem2")

LAAD_TOERNOOI = '''import json

# Dit toernooi is echt gespeeld, door een eerdere lichting. De namen zijn
# verzonnen, de getallen niet: dezelfde stacks, hetzelfde foldgedrag, dezelfde
# uitschieters. Vanaf week 3 haal je je eigen toernooi op bij de API; tot die
# tijd werk je hiermee, zodat je je op het programmeren kunt richten.
with open("data/voorbeeldtoernooi.json") as f:
    toernooi_resultaat = json.load(f)

# In deze uitslag staat jouw bot nog niet -- vanaf week 3 wel. Kies er zolang
# eentje om te volgen; alles hieronder rekent met deze naam. Ravi staat net onder
# het midden, en dat is een eerlijker startpunt dan de nummer 1: de vraag onderaan
# is of je boven of onder de helft zit.
mijn_bot = "Ravi"

print("deelnemers:", len(toernooi_resultaat["namen_deelnemers"]))
print("logregels: ", len(toernooi_resultaat["hand_log"]))
print("je volgt:  ", mijn_bot)'''


def zoek_cel(nb, stuk, soort="code"):
    """De enige cel die `stuk` bevat. Meer of minder dan één is een fout."""
    treffers = [i for i, c in enumerate(nb["cells"])
                if c["cell_type"] == soort and stuk in "".join(c["source"])]
    if len(treffers) != 1:
        raise SystemExit(f"{stuk!r} komt in {len(treffers)} {soort}-cellen voor, verwacht 1.\n"
                         f"Het bronnotebook is veranderd; werk dit script bij.")
    return treffers[0]


def zet_bron(cel, tekst):
    regels = tekst.rstrip("\n").split("\n")
    cel["source"] = [r + "\n" for r in regels[:-1]] + [regels[-1]]
    cel["outputs"] = []
    cel["execution_count"] = None


def knip(nb, van_stuk, tot_stuk, van_soort="markdown", tot_soort="markdown"):
    """Haalt de cellen weg van `van_stuk` tot en met de cel vóór `tot_stuk`."""
    van = zoek_cel(nb, van_stuk, van_soort)
    tot = zoek_cel(nb, tot_stuk, tot_soort)
    if tot <= van:
        raise SystemExit(f"{tot_stuk!r} staat vóór {van_stuk!r}; knippen zou de verkeerde kant op gaan.")
    weg = tot - van
    del nb["cells"][van:tot]
    return weg


def werkcollege1(nb):
    """Inleveren eruit: de bot blijft deze week op je eigen machine."""
    weg = knip(nb, "### Stap B: de benodigde imports", "## Reflectievragen")
    i = zoek_cel(nb, "### Stap A: maak `mijn_bot_week1.py`", "markdown")
    nb["cells"][i]["source"] = [
        "### Stap A: zet je bot in een los bestand\n", "\n",
        "Je bot staat nu in een cel van dit notebook. Zet hem daarnaast in een eigen "
        "bestand, want vanaf week 3 lever je dat bestand in — en in week 2 laat je "
        "hem ermee tegen een klasgenoot spelen.\n", "\n",
        "De regel `%%writefile` bovenaan een cel schrijft de rest van die cel naar "
        "een bestand in plaats van hem uit te voeren.\n"]
    # de uitleg ná de writefile-cel mag niet meer naar het inleveren verwijzen
    j = zoek_cel(nb, "Writing mijn_bot_week1.py", "markdown")
    nb["cells"][j]["source"] = [
        "Draai je de cel hierboven, dan zie je `Writing mijn_bot_week1.py` verschijnen "
        "en staat het bestand naast je notebook.\n", "\n",
        "**Deze week lever je nog niets in.** Bewaar `mijn_bot_week1.py` op een plek "
        "die je terugvindt: in week 2 heb je hem nodig, en in week 3 gaat hij naar de "
        "server.\n"]
    return weg, 2


def werkcollege2(nb):
    """De API-les eruit, het toernooi uit een bestand, peer review eruit."""
    weg = knip(nb, "## Deel 2 — Hoe werkt een API", "## Deel 3 — Het toernooi bekijken")
    weg += knip(nb, "## Deel 5 — Peer review via de API", "## Reflectievragen")
    i = zoek_cel(nb, 'f"{API_URL}/toernooi/1"')
    zet_bron(nb["cells"][i], LAAD_TOERNOOI)
    k = zoek_cel(nb, "mijn_bot = next(naam for naam in eindstand")
    zet_bron(nb["cells"][k], """eindstand = toernooi_resultaat["eindstand_per_bot"]

op_volgorde = sorted(eindstand, key=eindstand.get, reverse=True)

print("de top 5:")
for naam in op_volgorde[:5]:
    print("   ", naam, eindstand[naam])

print()
print(mijn_bot, "staat op:", eindstand[mijn_bot])
print("plek:", op_volgorde.index(mijn_bot) + 1, "van de", len(op_volgorde))""")

    j = zoek_cel(nb, "De eerste keer dat iemand in de klas dit ophaalt", "markdown")
    nb["cells"][j]["source"] = [
        "Geen internet nodig: het bestand staat naast je notebook in de map `data/`. "
        "Vanaf week 3 haal je hier je eigen toernooi op bij de API, en dan zie je je "
        "eigen bot in deze uitslag staan.\n"]
    return weg, 3


def werkcollege3(nb):
    """Allebei de toernooi-ophalers uit een bestand."""
    aangepast = 0
    for cel in nb["cells"]:
        if cel["cell_type"] != "code":
            continue
        bron = "".join(cel["source"])
        if 'f"{API_URL}/toernooi/1"' not in bron:
            continue
        staart = bron.split("toernooi_resultaat = response.json()", 1)[1]
        zet_bron(cel, LAAD_TOERNOOI.rsplit("\nprint(", 1)[0].rstrip() + "\n" + staart.lstrip("\n"))
        aangepast += 1
    if aangepast != 2:
        raise SystemExit(f"{aangepast} toernooi-ophalers gevonden in WC3, verwacht 2.")
    return 0, aangepast


BEWERKINGEN = {
    "Week1_Werkcollege1.ipynb": werkcollege1,
    "Week1_Werkcollege2.ipynb": werkcollege2,
    "Week2_Werkcollege3.ipynb": werkcollege3,
}


def main():
    import nbformat
    p = argparse.ArgumentParser()
    p.parse_args()

    os.makedirs(DOEL, exist_ok=True)
    for naam, bewerk in BEWERKINGEN.items():
        nb = nbformat.read(os.path.join(BRON, naam), as_version=4)
        voor = len(nb["cells"])
        weg, aangepast = bewerk(nb)
        nbformat.validator.normalize(nb)
        nbformat.validate(nb)
        doel = os.path.join(DOEL, naam)
        with open(doel, "w") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"   {naam:<28s} {voor} -> {len(nb['cells'])} cellen "
              f"({weg} weg, {aangepast} aangepast)")

    # Controle: er mag geen netwerkaanroep meer in staan.
    import re
    for naam in BEWERKINGEN:
        nb = nbformat.read(os.path.join(DOEL, naam), as_version=4)
        code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
        resten = re.findall(r"requests\.(get|post)|lever_in\(|onrender\.com", code)
        vlag = "geen netwerk" if not resten else f"LET OP: nog {len(resten)}x {set(resten)}"
        print(f"   {naam:<28s} {vlag}")
    print(f"\n-> {DOEL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
