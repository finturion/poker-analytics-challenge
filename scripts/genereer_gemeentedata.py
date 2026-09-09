"""
Bouwt de twee databestanden die Werkcollege 9 nodig heeft voor de Nederland-kaart.

    notebooks/data/gemeenten_nl.geojson   342 gemeentegrenzen + inwonertal
    notebooks/data/oefenbots.csv          fictieve bots met een locatie en een resultaat

WAAROM DIT EEN SCRIPT IS EN GEEN CEL IN HET NOTEBOOK
----------------------------------------------------
De bron is de CBS-wijken-en-buurtenkaart via PDOK. Die download is 96 MB en duurt
bijna twee minuten. Dat wil je niet 44 keer tegelijk in een werkcollege doen: dan
hangt je les aan de wifi en aan de beschikbaarheid van PDOK. Dit script haalt het
één keer op, vereenvoudigt de grenzen tot 1,2 MB en zet het resultaat in de repo.
Studenten lezen een lokaal bestand.

Bron: CBS Wijken- en Buurtenkaart 2024 via PDOK (open data, CC BY 4.0 — CBS/Kadaster).

WAAROM ER FICTIEVE BOTS ZIJN
----------------------------
Nederland heeft 342 gemeentes en de klas heeft 44 studenten. Zonder aanvulling is
maximaal 13% van de kaart gekleurd, en dan is een choropleth geen choropleth maar
een puntenwolk met omtrekken. De oefenbots vullen dat op.

Twee dingen zijn daarbij belangrijk:

1. Ze doen NIET mee aan het echte toernooi. Zouden ze dat wel doen, dan speelden
   studenten vooral tegen oefenbots in plaats van tegen elkaar, en dat verpest de
   toernooi-uitslag waar het bonuspunt aan hangt. Ze bestaan alleen op de kaart.

2. Hun prestatie is GEGENEREERD, niet gesimuleerd. Dat is een bewuste keuze na een
   mislukte poging: eerst heb ik ze echt laten spelen, tegen sterke referentiebots,
   zodat de getallen "echt" zouden zijn. Dat werkt niet. De ruis op één bot is
   500 tot 800 chips (zie scripts/meet_toernooi_variantie.py), dus een zwakke bot
   die geluk heeft eindigt boven een goede student. Bij 40 simulaties zaten er nog
   16 van de 342 oefenbots boven de top-5-grens van een representatief
   studentenveld, en hun mediaan lag zelfs hóger dan die van de studenten.

   Een gegenereerde waarde uit een gecontroleerde band doet wat het moet doen: de
   achtergrond varieert genoeg voor een leesbare kaart, en de bovenkant van de
   schaal blijft voor de studenten. Dat is eerlijker dan doen alsof het een
   uitslag is: het notebook zegt gewoon dat het achtergrondbots zijn.

   Daarnaast krijgt de kaart een tweede laag die de gemeentes met een échte
   student markeert. Zo springen die eruit ongeacht hun score -- ook een student
   die slecht speelt hoort vindbaar te zijn op zijn eigen kaart.

Draaien:  python3 scripts/genereer_gemeentedata.py
"""
import os
import random
import sys
import urllib.request

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
sys.path.insert(0, os.path.join(WORTEL, "api"))

DATAMAP = os.path.join(WORTEL, "notebooks", "data")
RUW = os.path.join(DATAMAP, "_gemeenten_ruw.geojson")   # cache, niet in git
GEMEENTEN = os.path.join(DATAMAP, "gemeenten_nl.geojson")
OEFENBOTS = os.path.join(DATAMAP, "oefenbots.csv")

PDOK = ("https://service.pdok.nl/cbs/wijkenbuurten/2024/wfs/v1_0"
        "?request=GetFeature&service=WFS&version=2.0.0"
        "&typeName=wijkenbuurten:gemeenten&outputFormat=application/json&count=500")

# 100 meter: op een kaart van heel Nederland zie je het verschil met de volledige
# grens niet, en het scheelt een factor 50 in bestandsgrootte (61 MB -> 1,2 MB).
VEREENVOUDIGING_METER = 100

AANDEEL_GEMEENTEN_MET_BOTS = 0.5   # de helft van de kaart krijgt kleur
BOTS_PER_GEMEENTE_GEMIDDELD = 2
SEED = 9


def haal_ruwe_grenzen_op():
    os.makedirs(DATAMAP, exist_ok=True)
    if os.path.exists(RUW):
        print(f"  cache gebruikt: {RUW} ({os.path.getsize(RUW) / 1e6:.0f} MB)")
        return
    print("  downloaden van PDOK (96 MB, duurt ~2 minuten)...")
    urllib.request.urlretrieve(PDOK, RUW)
    print(f"  klaar: {os.path.getsize(RUW) / 1e6:.0f} MB")


def bouw_gemeentekaart():
    """De 342 echte gemeentes, vereenvoudigd, met inwonertal, in WGS84 voor Folium."""
    ruw = gpd.read_file(RUW)[["gemeentecode", "gemeentenaam", "aantalInwoners", "geometry"]]

    # CBS gebruikt -99997 e.d. voor "onbekend of geheim". De 82 features die
    # daarop staan zijn water en overig gebied, geen gemeentes.
    kaart = ruw[ruw["aantalInwoners"] > 0].copy()
    kaart = kaart.rename(columns={"gemeentecode": "code", "gemeentenaam": "gemeente",
                                  "aantalInwoners": "inwoners"})

    # Vereenvoudigen gebeurt in meters, dus in RD (EPSG:28992) en niet in graden.
    kaart["geometry"] = kaart.geometry.simplify(VEREENVOUDIGING_METER, preserve_topology=True)
    kaart = kaart.to_crs("EPSG:4326")
    return kaart.sort_values("gemeente").reset_index(drop=True)


def _punt_in(polygoon, rng):
    """Een willekeurig punt binnen het polygoon, zodat bots niet op elkaar liggen."""
    minx, miny, maxx, maxy = polygoon.bounds
    for _ in range(200):
        punt = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if polygoon.contains(punt):
            return punt
    return polygoon.representative_point()


def kies_gemeenten_en_aantallen(kaart, rng):
    """
    Welke gemeentes krijgen oefenbots, en hoeveel.

    Gewogen naar inwonertal: de grote steden komen bijna zeker aan bod, een klein
    dorp soms. Dat is realistischer dan gelijk verdelen, en het maakt de kaart
    ook leesbaarder -- de Randstad wordt dicht, het noorden dun.
    """
    n_gemeenten = round(len(kaart) * AANDEEL_GEMEENTEN_MET_BOTS)
    gewicht = kaart["inwoners"] ** 0.5   # wortel: anders slokt Amsterdam alles op
    gekozen = kaart.sample(n=n_gemeenten, weights=gewicht, random_state=SEED)

    # Elke gekozen gemeente krijgt er minstens één; de rest verdeeld naar gewicht,
    # zodat het gemiddelde op BOTS_PER_GEMEENTE_GEMIDDELD uitkomt.
    extra_totaal = n_gemeenten * (BOTS_PER_GEMEENTE_GEMIDDELD - 1)
    kansen = (gekozen["inwoners"] ** 0.5 / (gekozen["inwoners"] ** 0.5).sum()).tolist()
    aantallen = {code: 1 for code in gekozen["code"]}
    codes = gekozen["code"].tolist()
    for code in rng.choices(codes, weights=kansen, k=extra_totaal):
        aantallen[code] += 1
    return gekozen, aantallen


# De band waarin de achtergrondbots vallen. De bovengrens ligt bewust onder wat een
# redelijke student haalt: in een representatief veld van 44 loopt de eindstand van
# ~300 tot ~1700 met de top 5 vanaf ~1540. Met 1200 als plafond blijft de bovenkant
# van de kleurschaal dus voor de klas.
OEFENBOT_MIN = 380
OEFENBOT_MAX = 1200
OEFENBOT_PIEK = 900   # de meeste achtergrondbots zitten hier in de buurt


def genereer_achtergrondresultaten(namen, rng):
    """
    Een prestatie per achtergrondbot: gegenereerd, niet gespeeld.

    Driehoeksverdeling tussen OEFENBOT_MIN en OEFENBOT_MAX met de piek op
    OEFENBOT_PIEK. Dat geeft een kaart met echte variatie -- niet één vlakke kleur --
    terwijl het plafond gegarandeerd onder de studentenkop blijft. Zie de
    moduledocstring voor waarom dit niet gesimuleerd wordt.
    """
    return {
        naam: round(rng.triangular(OEFENBOT_MIN, OEFENBOT_MAX, OEFENBOT_PIEK), 1)
        for naam in namen
    }


def main():
    rng = random.Random(SEED)
    haal_ruwe_grenzen_op()

    print("\n  Gemeentekaart bouwen")
    kaart = bouw_gemeentekaart()
    kaart.to_file(GEMEENTEN, driver="GeoJSON")
    print(f"    {len(kaart)} gemeentes, {os.path.getsize(GEMEENTEN) / 1e6:.2f} MB")
    print(f"    inwoners: {kaart['inwoners'].sum():,} totaal, "
          f"{kaart['inwoners'].min():,} tot {kaart['inwoners'].max():,}")

    print("\n  Oefenbots verdelen")
    gekozen, aantallen = kies_gemeenten_en_aantallen(kaart, rng)
    rijen = []
    for _, gem in gekozen.iterrows():
        for n in range(aantallen[gem["code"]]):
            punt = _punt_in(gem.geometry, rng)
            rijen.append({"bot_naam": f"oefenbot_{gem['code']}_{n + 1}",
                          "gemeente": gem["gemeente"], "code": gem["code"],
                          "lat": round(punt.y, 5), "lon": round(punt.x, 5)})
    bots = pd.DataFrame(rijen)
    print(f"    {len(bots)} oefenbots over {len(gekozen)} van de {len(kaart)} gemeentes "
          f"({100 * len(gekozen) / len(kaart):.0f}%)")
    print(f"    gemiddeld {len(bots) / len(gekozen):.1f} per gemeente, "
          f"maximaal {max(aantallen.values())}")

    print("\n  Achtergrondprestaties genereren")
    bots["eindstand"] = bots["bot_naam"].map(genereer_achtergrondresultaten(bots["bot_naam"].tolist(), rng))
    bots["is_oefenbot"] = True
    bots.to_csv(OEFENBOTS, index=False)
    print(f"    {len(bots)} bots -> {OEFENBOTS}")
    print(f"    eindstand: {bots['eindstand'].min():.0f} tot {bots['eindstand'].max():.0f}, "
          f"mediaan {bots['eindstand'].median():.0f} (plafond {OEFENBOT_MAX})")


if __name__ == "__main__":
    main()
