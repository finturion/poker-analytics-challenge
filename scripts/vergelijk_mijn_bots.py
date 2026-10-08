"""
Laat de bots uit mijn_bots/ tegen elkaar spelen en laat zien HOE ze spelen.

Opgezet als een meting, niet als een wedstrijd. De ruis op de eindstack van één
bot is 500-800 chips over 50 handen (zie scripts/meet_toernooi_variantie.py), en
dat is meer dan het verschil tussen twee redelijke bots. Daarom:

- N_SIMULATIES simulaties per seed, over alle SEEDS heen: dat zijn
  len(SEEDS) * N_SIMULATIES onafhankelijke tafels per bot.
- Het verschil tussen twee bots wordt GEPAARD gemeten. Ze zitten allemaal aan
  dezelfde tafel en chips zijn zero-sum (samen altijd n x 1000), dus als de een
  meer heeft heeft de ander minder. Die correlatie halen we eruit door per tafel
  het verschil te nemen; ongepaard zou de ruis kunstmatig groot lijken.
- Allemaal spelen ze met strategie "balanced", zodat we IDEEEN vergelijken en
  niet archetypes.
- Voor de vraag "wie is er beter" is een volle tafel maar de helft van het
  antwoord; scripts/kop_op_kop_mijn_bots.py speelt alle paren één-tegen-één, en
  die rangorde is aantoonbaar anders.

Uit het hand-log komt daarna het gedrag: actieverdeling, met welke handen een bot
meedeed, en wat elke actie hem opleverde.

Draaien:  python3 scripts/vergelijk_mijn_bots.py
Kost ongeveer een minuut.
"""
import collections
import functools
import os
import random
import statistics
import sys
import time

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(PROJECT, "api"))
sys.path.insert(0, os.path.join(PROJECT, "mijn_bots"))

from bot_validator import TOEGESTANE_ACTIES_MET_SIZING, valideer_bot_code
from poker_adapter import (STANDAARD_INITIAL_STACK, TAFEL_GROOTTE_MAX,
                           speel_toernooi)

import bot_allrounder
import bot_bluffer
import bot_handsterkte
import bot_inzetgrootte
import bot_potodds
import bot_tafellezer
import bot_uitbuiter
import simpel_bluffer
import simpel_caller
import simpel_muntje
import simpel_goeiehanden

# --- de knoppen van dit script ---------------------------------------------
SEEDS = [51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62]
N_SIMULATIES = 20
N_HANDEN = 50
BEWAAR_CSV = True

# bluf_kans staat op dezelfde waarde voor alle bots die kunnen bluffen, zodat
# hoe vaak ze bluffen uit hun IDEE volgt en niet uit de knop. bot_handsterkte
# gebruikt bluf_kans niet -- daar staat hij op 0.0 om dat expliciet te maken.
VELD = {
    "handsterkte":  {"module": bot_handsterkte,  "strategie": "balanced", "bluf_kans": 0.0},
    "potodds":      {"module": bot_potodds,      "strategie": "balanced", "bluf_kans": 0.25},
    "tafellezer":   {"module": bot_tafellezer,   "strategie": "balanced", "bluf_kans": 0.25},
    "inzetgrootte": {"module": bot_inzetgrootte, "strategie": "balanced", "bluf_kans": 0.25},
    "bluffer":      {"module": bot_bluffer,      "strategie": "balanced", "bluf_kans": 0.25},
    "allrounder":   {"module": bot_allrounder,   "strategie": "balanced", "bluf_kans": 0.25},
    "uitbuiter":    {"module": bot_uitbuiter,    "strategie": "balanced", "bluf_kans": 0.25},
    # De vier simpele bots. Eén regel elk, als ijkpunt: wat een bot boven
    # "muntje" uitkomt, is precies wat zijn idee waard is.
    "s_bluffer":    {"module": simpel_bluffer,   "strategie": "balanced", "bluf_kans": 0.25},
    "s_caller":     {"module": simpel_caller,    "strategie": "balanced", "bluf_kans": 0.0},
    "s_goeiehanden":{"module": simpel_goeiehanden, "strategie": "balanced", "bluf_kans": 0.0},
    "s_muntje":     {"module": simpel_muntje,    "strategie": "balanced", "bluf_kans": 0.0},
}

# Winkans-bakken voor "met welke handen deed hij mee". Grenzen in procenten.
HAND_BAKKEN = [0, 45, 55, 65, 100]
HAND_LABELS = ["troep <45", "matig 45-55", "goed 55-65", "top 65+"]
ZWAKKE_HAND = 45.0  # hieronder noemen we een raise een bluf

WINKANS = bot_handsterkte.WINKANS
hand_sleutel = bot_handsterkte.hand_sleutel


def kop(tekst):
    print(f"\n{'=' * 78}\n{tekst}\n{'=' * 78}")


# --- 1. Door de echte validator --------------------------------------------
def valideer_alles():
    kop("1. Door de echte validator (valideer_bot_code, week 5)")
    alles_goed = True
    for naam, info in VELD.items():
        pad = os.path.join(PROJECT, "mijn_bots", info["module"].__name__ + ".py")
        resultaat = valideer_bot_code(
            open(pad).read(), week=5,
            strategie=info["strategie"], bluf_kans=info["bluf_kans"],
        )
        acties = resultaat.get("actie_resultaten") or []
        print(f"  {naam:<14} geldig={str(resultaat['geldig']):<5} "
              f"constante_bot={str(resultaat['constante_bot']):<5} "
              f"{len(acties)} testgevallen -> {sorted(set(acties))}")
        if resultaat["foutmelding"]:
            print(f"      FOUT: {resultaat['foutmelding']}")
            alles_goed = False
    return alles_goed


# --- 2. Een controle-run: crasht er iets stil? ------------------------------
def maak_wachter(functie, naam, dagboek):
    """
    Zelfde functie, maar hij houdt bij of hij crasht, te lang duurt of iets
    onherkenbaars teruggeeft. Dat is precies wat het toernooi NIET laat zien:
    een bot die crasht foldt stil die hand en je merkt alleen slechte cijfers.

    functools.wraps zorgt dat inspect.signature() de signatuur van de ECHTE
    functie blijft zien -- daar kiest poker_adapter zijn argumenten op, en
    daarop hangen ook de gates voor all_in en grote_raise.
    """
    @functools.wraps(functie)
    def wachter(**kwargs):
        start = time.perf_counter()
        try:
            resultaat = functie(**kwargs)
        except Exception as fout:  # noqa: BLE001 - we willen juist alles zien
            dagboek[naam]["crashes"].append(repr(fout))
            return "fold"
        dagboek[naam]["aanroepen"] += 1
        dagboek[naam]["max_duur"] = max(dagboek[naam]["max_duur"],
                                        time.perf_counter() - start)
        dagboek[naam]["acties"][str(resultaat).lower()] += 1
        dagboek[naam]["per_ronde"][(kwargs.get("ronde", "?"), str(resultaat).lower())] += 1
        if not isinstance(resultaat, str) or resultaat.lower() not in TOEGESTANE_ACTIES_MET_SIZING:
            dagboek[naam]["ongeldig"].append(repr(resultaat))
        meet_bluf(functie, kwargs, resultaat, dagboek[naam])
        return resultaat
    return wachter


def meet_bluf(functie, kwargs, resultaat, meting):
    """
    Is de bluf-tak van deze bot dode code?

    Met bluf_kans=0.0 is elke bot deterministisch: er wordt geen random()
    meer gebruikt. Roep dezelfde situatie dus drie keer aan:

    - met bluf_kans 0.0 -> wat hij zonder bluf zou doen
    - met bluf_kans 1.0 EN random() vastgezet op 0.0 -> wat hij doet als hij
      de bluf-tak altijd neemt

    Dat vastzetten is nodig, en dat was eerst fout. bot_bluffer rekent zijn
    kans uit als bluf_kans x STRAAT_FACTOR, en die factor is preflop 0,3. Op
    bluf_kans 1.0 bluft hij daar dus nog steeds maar 30% van de tijd, en dan
    meet je reikbaarheid met een muntje. Met random() op 0.0 is elke
    `random() < kans` waar zolang kans > 0, ongeacht hoe de bot hem opbouwt.

    Verschillen die twee, dan was de bluf-tak in deze situatie BEREIKBAAR.
    Wijkt de echte uitkomst af van de 0.0-variant, dan heeft hij ECHT gebluft.
    Zo zie je het verschil tussen "hij bluft weinig" en "zijn eigen drempels
    laten hem nooit bij die regel komen".
    """
    if "bluf_kans" not in kwargs:
        return
    # Deze extra aanroepen trekken random() leeg, en de bots delen één globale
    # random-generator met de engine. Zonder de toestand terug te zetten meet je
    # dus een ANDER spel dan er zonder diagnose gespeeld zou zijn -- dat scheelde
    # in een eerdere versie een factor 4 in het aantal bereikbare bluf-momenten.
    toestand = random.getstate()
    echte_random = random.random
    try:
        nooit = functie(**{**kwargs, "bluf_kans": 0.0})
        nog_eens = functie(**{**kwargs, "bluf_kans": 0.0})
        random.random = lambda: 0.0
        altijd = functie(**{**kwargs, "bluf_kans": 1.0})
    except Exception:  # noqa: BLE001 - een diagnose mag het toernooi niet slopen
        return
    finally:
        random.random = echte_random
        random.setstate(toestand)
    # Deze hele meting staat of valt bij die aanname: op bluf_kans 0 mag er geen
    # random() meer aan te pas komen. Zo niet, dan is de nul-variant zelf een
    # gok en zijn "bereikbaar" en "gevuurd" onvergelijkbaar -- dan tellen we
    # niets en melden we dat de knop niet uit gaat.
    if nooit != nog_eens:
        meting["niet_deterministisch_op_nul"] += 1
        return
    if nooit != altijd:
        meting["bluf_bereikbaar"] += 1
    if resultaat != nooit:
        meting["bluf_gevuurd"] += 1


def controle_run():
    kop("2. Controle-run: crasht een bot stil, of duurt hij te lang?")
    dagboek = {naam: {"aanroepen": 0, "max_duur": 0.0, "crashes": [], "ongeldig": [],
                      "acties": collections.Counter(), "per_ronde": collections.Counter(),
                      "bluf_bereikbaar": 0, "bluf_gevuurd": 0,
                      "niet_deterministisch_op_nul": 0}
               for naam in VELD}
    bots = {
        naam: {"kies_actie": maak_wachter(info["module"].kies_actie, naam, dagboek),
               "strategie": info["strategie"], "bluf_kans": info["bluf_kans"]}
        for naam, info in VELD.items()
    }
    speel_toernooi(bots, n_simulaties=N_SIMULATIES, n_handen=N_HANDEN, seed=SEEDS[0])
    for naam in VELD:
        meting = dagboek[naam]
        print(f"  {naam:<14} {meting['aanroepen']:>6} beslissingen, "
              f"langzaamste {meting['max_duur'] * 1000:.2f} ms, "
              f"{len(meting['crashes'])} crashes, "
              f"{len(meting['ongeldig'])} onherkenbare returns")
        for boodschap in collections.Counter(meting["crashes"]).most_common(3):
            print(f"      crash: {boodschap[1]}x {boodschap[0]}")
        for boodschap in collections.Counter(meting["ongeldig"]).most_common(3):
            print(f"      return: {boodschap[1]}x {boodschap[0]}")

    print("\n  Is de bluf-tak dode code? (zelfde situatie ook doorgerekend met bluf_kans")
    print("   0.0, en met bluf_kans 1.0 én random() vastgezet op 0)")
    print("   'verwacht' = bereikbaar x bluf_kans. Een bot die bluf_kans intern")
    print("   opschaalt of afzwakt komt daar onder of boven uit, en dat is geen fout:")
    print("   bot_bluffer vermenigvuldigt met STRAAT_FACTOR (preflop 0,3), bot_uitbuiter")
    print("   met STEAL_VERSTERKING (2,5).")
    print(f"\n  {'bot':<14}{'bluf_kans':>11}{'bereikbaar':>12}{'gevuurd':>9}"
          f"{'verwacht':>10}   oordeel")
    for naam, info in VELD.items():
        meting = dagboek[naam]
        kans = info["bluf_kans"]
        bereikbaar = meting["bluf_bereikbaar"]
        verwacht = bereikbaar * kans
        if meting["niet_deterministisch_op_nul"]:
            oordeel = (f"ONMEETBAAR: op bluf_kans 0 nog steeds toevallig, in "
                       f"{meting['niet_deterministisch_op_nul']} gevallen")
        elif kans == 0.0:
            oordeel = "bluft nooit (bluf_kans staat op 0)"
        elif bereikbaar == 0:
            oordeel = "DODE CODE: komt nooit bij die regel"
        elif bereikbaar < 0.01 * meting["aanroepen"]:
            oordeel = "bijna dode code (<1% van zijn beslissingen)"
        else:
            oordeel = f"leeft, in {100 * bereikbaar / meting['aanroepen']:.0f}% van zijn beslissingen"
        print(f"  {naam:<14}{kans:>11.2f}{bereikbaar:>12}{meting['bluf_gevuurd']:>9}"
              f"{verwacht:>10.0f}   {oordeel}")
    return dagboek


# --- 3. Het toernooi --------------------------------------------------------
def speel_alles():
    rest = len(VELD) % TAFEL_GROOTTE_MAX
    if len(VELD) > TAFEL_GROOTTE_MAX:
        print(f"  {len(VELD)} bots bij TAFEL_GROOTTE_MAX {TAFEL_GROOTTE_MAX}: elke simulatie wordt "
              f"verdeeld over {-(-len(VELD) // TAFEL_GROOTTE_MAX)} tafels.")
        if 0 < rest < 2:
            print("  LET OP: er blijft een rest-tafel met 1 bot over, en _verdeel_in_tafels()")
            print("  plakt die bij de vorige in plaats van hem apart te zetten. Je krijgt dan")
            print(f"  een tafel van {TAFEL_GROOTTE_MAX + rest} -- ruimer dan de engine bedoelt. Het draait, maar")
            print("  zo'n tafel is tighter dan de 6-max van het echte toernooi.")
    bots = {naam: {"kies_actie": info["module"].kies_actie,
                   "strategie": info["strategie"], "bluf_kans": info["bluf_kans"]}
            for naam, info in VELD.items()}
    logs = []
    for seed in SEEDS:
        start = time.time()
        uitslag = speel_toernooi(bots, n_simulaties=N_SIMULATIES, n_handen=N_HANDEN, seed=seed)
        frame = pd.DataFrame(uitslag["hand_log"])
        frame["seed"] = seed
        logs.append(frame)
        print(f"  seed {seed} gedraaid in {time.time() - start:.0f}s")
    return pd.concat(logs, ignore_index=True)


def eindstanden_per_tafel(log):
    """
    Eén rij per (seed, simulatie, tafel, bot): de stack na zijn laatste hand.

    Dit is dezelfde grootheid als eindstand_per_bot uit speel_toernooi, maar
    niet meteen uitgemiddeld -- die losse waarnemingen hebben we nodig om de
    ruis te kunnen meten.
    """
    laatste = log.sort_values("hand_nummer").groupby(
        ["seed", "simulatie", "tafel", "bot_naam"], as_index=False).last()
    return laatste[["seed", "simulatie", "tafel", "bot_naam", "stack", "hand_nummer"]]


def rapporteer_uitslag(eindstanden):
    kop(f"3. De uitslag: {len(SEEDS)} seeds x {N_SIMULATIES} simulaties x {N_HANDEN} handen")
    tafels = eindstanden.pivot_table(index=["seed", "simulatie"],
                                     columns="bot_naam", values="stack")
    n = len(tafels)
    print(f"  {n} onafhankelijke tafels per bot "
          f"({n * N_HANDEN} handen per bot)")
    chips = tafels.sum(axis=1)
    print(f"  chip-controle: elke tafel telt op tot {chips.min():.0f}-{chips.max():.0f} "
          f"(verwacht {len(VELD) * STANDAARD_INITIAL_STACK})")

    print(f"\n  {'bot':<14}{'gemiddeld':>11}{'ruis (sd)':>11}{'onzekerheid':>13}"
          f"{'95%-interval':>20}{'% tafels 1e':>13}")
    winnaars = tafels.idxmax(axis=1).value_counts()
    samenvatting = {}
    for naam in tafels.columns:
        kolom = tafels[naam]
        fout = kolom.std() / (n ** 0.5)
        samenvatting[naam] = (kolom.mean(), kolom.std(), fout)
        print(f"  {naam:<14}{kolom.mean():>11.0f}{kolom.std():>11.0f}{fout:>13.0f}"
              f"{f'[{kolom.mean() - 1.96 * fout:.0f}, {kolom.mean() + 1.96 * fout:.0f}]':>20}"
              f"{100 * winnaars.get(naam, 0) / n:>12.0f}%")
    print("\n  'ruis (sd)' is de spreiding van één tafel: dát is de 500-800 chips waar")
    print("  het om gaat. 'onzekerheid' is sd/sqrt(n) -- de fout op het gemiddelde.")

    print(f"\n  Plek per seed (elke seed is een eigen meting over {N_SIMULATIES} simulaties).")
    print("  Een bot wiens plek per seed heen en weer springt, is niet te onderscheiden")
    print("  van de bots waar hij tussen springt:")
    per_seed = eindstanden.pivot_table(index="seed", columns="bot_naam", values="stack")
    plekken = per_seed.rank(axis=1, ascending=False)
    kolommen = list(plekken.mean().sort_values().index)
    print()
    print(f"    {'bot':<14}" + "".join(f"{seed:>5}" for seed in plekken.index) + f"{'gem.':>8}")
    for naam in kolommen:
        rij = "".join(f"{plekken.loc[seed, naam]:>5.0f}" for seed in plekken.index)
        print(f"    {naam:<14}{rij}{plekken[naam].mean():>8.1f}")

    namen = list(tafels.columns)
    n_paren = len(namen) * (len(namen) - 1) // 2
    # We doen n_paren vergelijkingen op dezelfde data. Bij 1,96 (het gewone
    # 95%-interval) is de kans dat er ergens toevallig iets "significant" lijkt
    # dan een stuk groter dan 5%. Bonferroni: deel die 5% door het aantal
    # vergelijkingen. Met 7 bots zijn dat 21 paren en komt de grens op ~3,1.
    ENKEL = 1.96
    STRENG = statistics.NormalDist().inv_cdf(1 - 0.025 / n_paren)
    tafels_per_sim = eindstanden.groupby(["seed", "simulatie"])["tafel"].nunique().max()
    if tafels_per_sim > 1:
        print(f"\n  LET OP: {len(VELD)} bots passen niet aan één tafel, dus elke simulatie wordt")
        print(f"  over {tafels_per_sim} tafels verdeeld en twee bots zitten lang niet altijd bij elkaar.")
        print("  De koppeling hieronder is dan per SIMULATIE en niet per tafel: nog steeds")
        print("  geldig, maar minder scherp dan wanneer ze elkaars chips direct afpakken.")
    print(f"\n  Gepaarde verschillen (per tafel, dus zonder de gedeelde tafelruis).")
    print(f"  t = verschil / onzekerheid. Bij {n_paren} vergelijkingen tegelijk is |t| > "
          f"{STRENG:.1f} pas overtuigend;")
    print(f"  tussen {ENKEL} en {STRENG:.1f} is het een grensgeval.")
    print(f"\n    {'paar':<30}{'verschil':>10}{'onzekerheid':>13}{'t':>7}   {'oordeel':<26}")
    for i, a in enumerate(namen):
        for b in namen[i + 1:]:
            verschil = tafels[a] - tafels[b]
            gemiddeld = verschil.mean()
            fout = verschil.std() / (n ** 0.5)
            t = gemiddeld / fout if fout else 0.0
            beter = a if gemiddeld > 0 else b
            if abs(t) > STRENG:
                oordeel = f"{beter} is beter"
            elif abs(t) > ENKEL:
                oordeel = f"{beter}?  grensgeval"
            else:
                oordeel = "niet te onderscheiden"
            print(f"    {a + ' - ' + b:<30}{gemiddeld:>10.0f}{fout:>13.0f}{t:>7.1f}   {oordeel:<26}")
    return samenvatting


# --- 4. Hoe spelen ze? -----------------------------------------------------
def verrijk_log(log):
    """Winkans per gespeelde hand en winst per hand aan het log toevoegen."""
    log = log.copy()
    log["winkans"] = [WINKANS.get(hand_sleutel(hand), 40.0) for hand in log["hand"]]
    log["handbak"] = pd.cut(log["winkans"], bins=HAND_BAKKEN, labels=HAND_LABELS)

    # Winst per hand = verschil met de stack na de vorige hand. De groupby is
    # essentieel: zonder bot_naam/seed/simulatie/tafel erin rekent diff() door
    # over de grens van een simulatie heen en krijg je bij elke nieuwe simulatie
    # een verzonnen verlies van ~1000 chips.
    log = log.sort_values(["bot_naam", "seed", "simulatie", "tafel", "hand_nummer"])
    groepen = log.groupby(["bot_naam", "seed", "simulatie", "tafel"])
    log["winst"] = groepen["stack"].diff()
    log["stack_voor"] = groepen["stack"].shift().fillna(STANDAARD_INITIAL_STACK)
    # De eerste hand van een simulatie heeft geen vorige hand: dan is de winst
    # het verschil met de startstack.
    eerste_hand = log["winst"].isna()
    log.loc[eerste_hand, "winst"] = log.loc[eerste_hand, "stack"] - STANDAARD_INITIAL_STACK

    # Regels waarin de bot niets heeft gekozen, tellen niet mee. poker_adapter
    # schreef daar eerst `or "fold"` neer en dat was niet te onderscheiden van
    # een echte fold; sinds die `or "fold"` eruit is, staat er gewoon None en
    # kunnen we er direct op filteren. Twee soorten zitten daarin:
    #   - hij was al uitgespeeld (stack 0) en krijgt de uitslag nog wel door
    #   - hij kwam niet aan de beurt omdat iedereen naar zijn blind foldde,
    #     en dan wón hij die hand juist
    log["uitgespeeld"] = log["stack_voor"] <= 0
    log["kwam_niet_aan_beurt"] = log["actie"].isna() & ~log["uitgespeeld"]
    log["echte_beslissing"] = log["actie"].notna() & ~log["uitgespeeld"]
    return log


def rapporteer_spookregels(log):
    kop("4. Eerst opruimen: welke regels zijn geen beslissing?")
    print("  Een regel zonder gekozen actie (actie is None) is geen beslissing.")
    print("  Twee gevallen, en ze zijn groot genoeg om elke actieverdeling te")
    print("  vervalsen als je ze meerekent:")
    print(f"\n  {'bot':<14}{'regels':>9}{'al uitgespeeld':>16}"
          f"{'niet aan de beurt':>19}{'echte beslissingen':>20}")
    for naam in sorted(log["bot_naam"].unique()):
        eigen = log[log["bot_naam"] == naam]
        uitgespeeld = f"{eigen['uitgespeeld'].sum()} ({100 * eigen['uitgespeeld'].mean():.0f}%)"
        niet_aan_beurt = (f"{eigen['kwam_niet_aan_beurt'].sum()} "
                          f"({100 * eigen['kwam_niet_aan_beurt'].mean():.0f}%)")
        print(f"  {naam:<14}{len(eigen):>9}{uitgespeeld:>16}{niet_aan_beurt:>19}"
              f"{eigen['echte_beslissing'].sum():>20}")
    print("\n  Hieronder rekenen we alleen met de echte beslissingen.")


ACTIE_VOLGORDE = ["fold", "check", "call", "raise", "grote_raise", "all_in"]


def rapporteer_acties(log, dagboek):
    kop("5. Actieverdeling: welk woord geeft elke bot terug?")
    print("  Eerst uit het hand-log. Dat bewaart alleen de EERSTE actie van elke")
    print("  hand, dus dit is hoe een bot een hand OPENT -- 'check' en 'all_in'")
    print("  zijn daarin per definitie zeldzaam: bij je eerste beslissing sta je")
    print("  bijna altijd voor een blind, en je stack is dan nog vol.")
    verdeling = (pd.crosstab(log["bot_naam"], log["actie"], normalize="index") * 100)
    verdeling = verdeling.reindex(columns=ACTIE_VOLGORDE, fill_value=0.0)
    print()
    print(verdeling.round(1).to_string())

    print("\n  En nu ALLE beslissingen, ook die halverwege een hand. Dit komt uit de")
    print(f"  controle-run (seed {SEEDS[0]}), waarin elke aanroep is meegeteld:")
    alles = pd.DataFrame(
        {naam: {actie: dagboek[naam]["acties"].get(actie, 0) for actie in ACTIE_VOLGORDE}
         for naam in VELD}
    ).T
    aandeel = (100 * alles.div(alles.sum(axis=1), axis=0)).round(1)
    print()
    print(aandeel.to_string())

    print("\n  Wat een bot NOOIT doet is even interessant:")
    for naam in VELD:
        nooit = sorted(a for a in TOEGESTANE_ACTIES_MET_SIZING
                       if dagboek[naam]["acties"].get(a, 0) == 0)
        print(f"    {naam:<14} gebruikt nooit: {nooit if nooit else '(alle zes komen voor)'}")

    print("\n  Per straat. Let op: de engine geeft `ronde` alleen aan een bot die die")
    print("  parameter zelf in zijn signatuur heeft. Een bot zonder `ronde` KAN preflop")
    print("  niet van river onderscheiden -- die staat hier dus op één regel, en dat is")
    print("  zelf al een uitspraak over hoe hij speelt.")
    for naam in VELD:
        rijen = {}
        for (ronde, actie), aantal in dagboek[naam]["per_ronde"].items():
            rijen.setdefault(ronde, collections.Counter())[actie] += aantal
        print(f"\n    {naam}")
        for ronde in ["preflop", "flop", "turn", "river", "?"]:
            teller = rijen.get(ronde)
            if not teller:
                continue
            totaal = sum(teller.values())
            stukjes = "  ".join(
                f"{actie} {100 * teller[actie] / totaal:.1f}%"
                for actie in ACTIE_VOLGORDE if teller.get(actie)
            )
            label = "geen `ronde`" if ronde == "?" else ronde
            print(f"      {label:<13} ({totaal:>5} beslissingen)  {stukjes}")


def rapporteer_handen(log):
    kop("6. Met welke handen deed hij mee?")
    meedoen = log[log["actie"] != "fold"]
    print(f"  {'bot':<14}{'% meegedaan':>13}{'winkans meegedaan':>19}{'zwakste hand':>20}")
    for naam in sorted(log["bot_naam"].unique()):
        alles = log[log["bot_naam"] == naam]
        mee = meedoen[meedoen["bot_naam"] == naam]
        if len(mee):
            zwakste_rij = mee.loc[mee["winkans"].idxmin()]
            zwakste = "-".join(zwakste_rij["hand"]) + f" ({zwakste_rij['winkans']:.1f})"
        else:
            zwakste = "(deed nooit mee)"
        print(f"  {naam:<14}{100 * len(mee) / len(alles):>12.0f}%"
              f"{mee['winkans'].mean():>19.1f}{zwakste:>20}")

    print("\n  Fold-percentage per handklasse -- hier zie je de drempel:")
    tabel = log.pivot_table(index="bot_naam", columns="handbak",
                            values="actie", aggfunc=lambda s: 100 * (s == "fold").mean(),
                            observed=False)
    print()
    print(tabel.round(0).to_string())

    print(f"\n  Opende hij ooit een hand met een verhoging terwijl zijn winkans onder de")
    print(f"  {ZWAKKE_HAND:.0f} lag? Dat is per definitie een bluf.")
    print(f"\n    {'bot':<14}{'verhogingen':>13}{'waarvan bluf':>14}{'% van verhogingen':>19}")
    verhoogd = log[log["actie"].isin(["raise", "grote_raise", "all_in"])]
    for naam in sorted(log["bot_naam"].unique()):
        eigen = verhoogd[verhoogd["bot_naam"] == naam]
        bluffen = eigen[eigen["winkans"] < ZWAKKE_HAND]
        aandeel = 100 * len(bluffen) / len(eigen) if len(eigen) else 0.0
        print(f"    {naam:<14}{len(eigen):>13}{len(bluffen):>14}{aandeel:>18.1f}%")


def rapporteer_winst(log):
    kop("7. Wat leverde elke actie op? (winst per hand, in chips)")
    print("  Let op: dit is geen oorzaak. Een bot raist met goede handen, dus")
    print("  'raise levert veel op' kan ook betekenen 'hij raist alleen met AA'.")
    tabel = log.groupby(["bot_naam", "actie"])["winst"].agg(["mean", "std", "count"])
    tabel["onzekerheid"] = tabel["std"] / tabel["count"] ** 0.5
    tabel = tabel.rename(columns={"mean": "gemiddeld", "count": "handen"})
    print()
    print(tabel[["gemiddeld", "onzekerheid", "handen"]].round(1).to_string())

    print("\n  En per handklasse, om te zien waar het geld echt vandaan komt:")
    per_bak = log.pivot_table(index="bot_naam", columns="handbak", values="winst",
                              aggfunc="mean", observed=False)
    print()
    print(per_bak.round(1).to_string())


def rapporteer_overleven(log, eindstanden):
    kop(f"8. Overleven ze de {N_HANDEN} handen?")
    print("  Een bot die op 0 staat blijft in het log staan (hij krijgt de uitslag")
    print("  van elke hand nog mee), dus het aantal regels zegt niets. Wat wel iets")
    print("  zegt: wanneer stond zijn stack voor het eerst op 0?")
    print(f"\n  {'bot':<14}{'% tafels op 0':>15}{'zo ja: na hand':>17}"
          f"{'mediane eindstack':>20}{'% tafels > 1000':>18}")
    for naam in sorted(eindstanden["bot_naam"].unique()):
        eigen = log[log["bot_naam"] == naam]
        eind = eindstanden[eindstanden["bot_naam"] == naam]["stack"]
        op_nul = eigen[eigen["stack"] <= 0]
        per_tafel = op_nul.groupby(["seed", "simulatie", "tafel"])["hand_nummer"].min()
        n_tafels = eigen.groupby(["seed", "simulatie", "tafel"]).ngroups
        wanneer = f"{per_tafel.mean():.0f}" if len(per_tafel) else "-"
        print(f"  {naam:<14}{100 * len(per_tafel) / n_tafels:>14.0f}%{wanneer:>17}"
              f"{eind.median():>20.0f}"
              f"{100 * (eind > STANDAARD_INITIAL_STACK).mean():>17.0f}%")


def main():
    if not valideer_alles():
        print("\nEén of meer bots komen niet door de validator. Gestopt.")
        return
    dagboek = controle_run()
    kop("Toernooi draaien")
    log = speel_alles()
    log = verrijk_log(log)
    eindstanden = eindstanden_per_tafel(log)
    rapporteer_uitslag(eindstanden)
    rapporteer_spookregels(log)
    echt = log[log["echte_beslissing"]]
    rapporteer_acties(echt, dagboek)
    rapporteer_handen(echt)
    rapporteer_winst(echt)
    rapporteer_overleven(log, eindstanden)

    if BEWAAR_CSV:
        map_pad = os.path.join(PROJECT, "mijn_bots", "uitkomsten")
        os.makedirs(map_pad, exist_ok=True)
        log.to_csv(os.path.join(map_pad, "hand_log.csv"), index=False)
        eindstanden.to_csv(os.path.join(map_pad, "eindstanden_per_tafel.csv"), index=False)
        print(f"\nHand-log ({len(log):,} regels) en eindstanden weggeschreven naar "
              f"mijn_bots/uitkomsten/ -- klaar om zelf in een notebook op te pakken.")


if __name__ == "__main__":
    main()
