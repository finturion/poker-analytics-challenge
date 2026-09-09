"""
Bouwt de achtergronddata die Werkcollege 9 nodig heeft voor de Nederland-kaart.

    notebooks/data/oefenbots.csv                   342 fictieve bots: locatie + prestatie
    notebooks/data/gemeenten_nl_fallback.geojson   noodkopie van de gemeentegrenzen

DE GRENZEN HAALT DE STUDENT ZELF OP -- DAT IS HET LEERDOEL
----------------------------------------------------------
In Werkcollege 9 is dit één regel:

    URL = ("https://api.pdok.nl/kadaster/bestuurlijkegebieden/ogc/v1"
           "/collections/gemeentegebied/items?f=json&limit=400")
    gemeenten = gpd.read_file(URL)      # 342 gemeentes, EPSG:4326

Gemeten: ongeveer 30 seconden, met naam, code en provincie erbij. Alternatieven
die ik heb nagemeten en verworpen: dezelfde laag via WFS is 23 s en 19 MB, en de
CBS-wijken-en-buurtenkaart is 96 MB en bijna twee minuten -- bruikbaar in dit
script, niet in een les met 44 studenten.

Het fallback-bestand komt uit exact dezelfde API, met dezelfde kolommen, alleen
vereenvoudigd tot 100 meter zodat het in de repo past. Het is er voor als PDOK
eruit ligt: dan is het één regel omzetten in plaats van een afgelopen
werkcollege. Het is niet de bedoelde route.

WAAROM ER FICTIEVE BOTS ZIJN
----------------------------
Nederland heeft 342 gemeentes en de klas heeft 44 studenten. Zonder aanvulling is
maximaal 13% van de kaart gekleurd, en dan is een choropleth een puntenwolk met
omtrekken.

Twee dingen zijn daarbij belangrijk.

Ze doen NIET mee aan het echte toernooi. Zouden ze dat wel doen, dan speelden
studenten vooral tegen oefenbots in plaats van tegen elkaar, en dat verpest de
uitslag waar het bonuspunt aan hangt. Ze bestaan alleen op de kaart.

En hun prestatie is GEGENEREERD, niet gesimuleerd. Dat is een keuze na een
mislukte poging: eerst heb ik ze echt laten spelen tegen sterke referentiebots,
zodat de getallen geen verzinsels zouden zijn. Dat werkt niet. De ruis op één bot
is 500 tot 800 chips (zie scripts/meet_toernooi_variantie.py), dus een zwakke bot
met geluk eindigt boven een goede student. Zelfs bij 40 simulaties zaten er 16 van
de 342 boven de top-5-grens van een representatief studentenveld, en hun mediaan
lag hóger dan die van de studenten -- precies wat niet mag. Een waarde uit een
gecontroleerde band doet wél wat ze moet doen: genoeg variatie voor een leesbare
kaart, en de bovenkant van de schaal blijft voor de klas. Het notebook zegt gewoon
dat het achtergrondbots zijn.

Bronnen: PDOK/Kadaster Bestuurlijke Gebieden (grenzen) en CBS Wijken- en
Buurtenkaart 2024 via PDOK (inwonertallen, alleen om de bots te wegen). Open data.

Draaien:  python3 scripts/genereer_gemeentedata.py
"""
import os
import random
import urllib.request

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

HIER = os.path.dirname(os.path.abspath(__file__))
WORTEL = os.path.dirname(HIER)
DATAMAP = os.path.join(WORTEL, "notebooks", "data")

RUW_INWONERS = os.path.join(DATAMAP, "_gemeenten_ruw.geojson")   # cache, niet in git
FALLBACK = os.path.join(DATAMAP, "gemeenten_nl_fallback.geojson")
OEFENBOTS = os.path.join(DATAMAP, "oefenbots.csv")

# Wat de student in het werkcollege aanroept. Ook hier de autoriteit: de punten van
# de oefenbots worden in DEZE polygonen geplaatst, zodat de sjoin in het notebook
# exact dezelfde gemeente teruggeeft als in oefenbots.csv staat.
PDOK_GRENZEN = ("https://api.pdok.nl/kadaster/bestuurlijkegebieden/ogc/v1"
                "/collections/gemeentegebied/items?f=json&limit=400")

# Zwaar, mét inwonertal. Alleen nodig om de bots te wegen.
PDOK_INWONERS = ("https://service.pdok.nl/cbs/wijkenbuurten/2024/wfs/v1_0"
                 "?request=GetFeature&service=WFS&version=2.0.0"
                 "&typeName=wijkenbuurten:gemeenten&outputFormat=application/json&count=500")

VEREENVOUDIGING_METER = 100      # alleen voor het fallback-bestand
AANDEEL_GEMEENTEN_MET_BOTS = 0.5
BOTS_PER_GEMEENTE_GEMIDDELD = 2

# De band waarin de achtergrondbots vallen. Het plafond ligt bewust onder wat een
# redelijke student haalt: in een representatief veld van 44 loopt de eindstand van
# ~300 tot ~1700, met de top 5 vanaf ~1540.
OEFENBOT_MIN, OEFENBOT_PIEK, OEFENBOT_MAX = 380, 900, 1200
SEED = 9


def haal_grenzen_op():
    """De Kadaster-grenzen, onvereenvoudigd. Zelfde aanroep als in het werkcollege."""
    print("  grenzen ophalen via de PDOK-API (~30 s)...")
    grenzen = gpd.read_file(PDOK_GRENZEN)[["code", "naam", "ligt_in_provincie_naam", "geometry"]]
    return grenzen.rename(columns={"naam": "gemeente", "ligt_in_provincie_naam": "provincie"})


def haal_inwonertallen_op():
    """
    Inwoners per gemeentecode, uit de CBS-kaart.

    CBS schrijft codes als "GM0014", Kadaster als "0014" -- daar gaat de join
    stuk als je dat niet gelijktrekt. En CBS gebruikt negatieve sentinelwaarden
    (-99997) voor "onbekend of geheim"; die rijen zijn water en overig gebied.
    """
    os.makedirs(DATAMAP, exist_ok=True)
    if not os.path.exists(RUW_INWONERS):
        print("  inwonertallen downloaden van PDOK (96 MB, ~2 minuten)...")
        urllib.request.urlretrieve(PDOK_INWONERS, RUW_INWONERS)
    cbs = gpd.read_file(RUW_INWONERS)[["gemeentecode", "aantalInwoners"]]
    cbs = cbs[cbs["aantalInwoners"] > 0]
    cbs["code"] = cbs["gemeentecode"].str.removeprefix("GM")
    return cbs.set_index("code")["aantalInwoners"]


def _punt_in(polygoon, rng):
    """Een willekeurig punt binnen het polygoon, zodat bots niet op elkaar liggen."""
    minx, miny, maxx, maxy = polygoon.bounds
    for _ in range(500):
        punt = Point(rng.uniform(minx, maxx), rng.uniform(miny, maxy))
        if polygoon.contains(punt):
            return punt
    return polygoon.representative_point()


def verdeel_bots(grenzen, rng):
    """
    Welke gemeentes krijgen oefenbots, en hoeveel.

    Gewogen naar inwonertal, maar op de wortel: puur naar inwonertal zou Amsterdam
    een vijfde van alle bots geven en het noorden leeg laten. Met de wortel wordt
    de Randstad dichter en het noorden dunner, zonder dat de kaart scheeftrekt.
    """
    n = round(len(grenzen) * AANDEEL_GEMEENTEN_MET_BOTS)
    gekozen = grenzen.sample(n=n, weights=grenzen["inwoners"] ** 0.5, random_state=SEED)

    aantallen = {code: 1 for code in gekozen["code"]}
    gewichten = (gekozen["inwoners"] ** 0.5 / (gekozen["inwoners"] ** 0.5).sum()).tolist()
    for code in rng.choices(gekozen["code"].tolist(), weights=gewichten,
                            k=n * (BOTS_PER_GEMEENTE_GEMIDDELD - 1)):
        aantallen[code] += 1

    rijen = []
    for _, gem in gekozen.iterrows():
        for i in range(aantallen[gem["code"]]):
            punt = _punt_in(gem.geometry, rng)
            rijen.append({
                "bot_naam": f"oefenbot_{gem['code']}_{i + 1}",
                "gemeente": gem["gemeente"], "code": gem["code"],
                "lat": round(punt.y, 5), "lon": round(punt.x, 5),
                "eindstand": round(rng.triangular(OEFENBOT_MIN, OEFENBOT_MAX, OEFENBOT_PIEK), 1),
                "is_oefenbot": True,
            })
    return pd.DataFrame(rijen), gekozen


def controleer(bots, grenzen):
    """
    De sjoin uit het notebook nabouwen: elke bot moet in de gemeente landen die
    in het CSV staat. Zo niet, dan zou een student een tegenspraak vinden.
    """
    punten = gpd.GeoDataFrame(
        bots[["bot_naam", "gemeente"]],
        geometry=[Point(x, y) for x, y in zip(bots["lon"], bots["lat"])],
        crs="EPSG:4326",
    )
    samen = gpd.sjoin(punten, grenzen[["gemeente", "geometry"]].rename(
        columns={"gemeente": "gevonden"}), how="left", predicate="within")
    klopt = (samen["gevonden"] == samen["gemeente"]).sum()
    return klopt, len(bots)


def main():
    rng = random.Random(SEED)

    grenzen = haal_grenzen_op()
    inwoners = haal_inwonertallen_op()
    grenzen["inwoners"] = grenzen["code"].map(inwoners)
    ontbreekt = grenzen["inwoners"].isna().sum()
    print(f"    {len(grenzen)} gemeentes, inwonertal bekend voor {len(grenzen) - ontbreekt}")
    grenzen = grenzen.dropna(subset=["inwoners"])

    print("\n  Oefenbots verdelen")
    bots, gekozen = verdeel_bots(grenzen, rng)
    print(f"    {len(bots)} bots over {len(gekozen)} van de {len(grenzen)} gemeentes "
          f"({100 * len(gekozen) / len(grenzen):.0f}%), gemiddeld "
          f"{len(bots) / len(gekozen):.1f} per gemeente")
    print(f"    eindstand {bots['eindstand'].min():.0f} tot {bots['eindstand'].max():.0f}, "
          f"mediaan {bots['eindstand'].median():.0f} (plafond {OEFENBOT_MAX})")

    klopt, totaal = controleer(bots, grenzen)
    print(f"\n  Controle: {klopt} van {totaal} bots landt in de gemeente uit het CSV")
    assert klopt == totaal, "punten en grenzen lopen uit elkaar — de sjoin zou tegenspreken"

    bots.to_csv(OEFENBOTS, index=False)
    print(f"    -> {os.path.relpath(OEFENBOTS, WORTEL)}")

    print("\n  Fallback-kaart wegschrijven")
    in_rd = grenzen.drop(columns=["inwoners"]).to_crs("EPSG:28992")
    in_rd["geometry"] = in_rd.geometry.simplify(VEREENVOUDIGING_METER, preserve_topology=True)
    fallback = in_rd.to_crs("EPSG:4326").sort_values("gemeente").reset_index(drop=True)
    fallback.to_file(FALLBACK, driver="GeoJSON")
    print(f"    {len(fallback)} gemeentes, {os.path.getsize(FALLBACK) / 1e6:.2f} MB, "
          f"kolommen {[k for k in fallback.columns if k != 'geometry']}")


if __name__ == "__main__":
    main()
