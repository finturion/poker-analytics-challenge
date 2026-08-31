"""
Technische validatie van de geolocatie die vanaf Week 5 bij een inzending hoort.

Verwacht schema:
{
    "lat": float,          # -90 .. 90
    "lon": float,          # -180 .. 180
    "plaatsnaam": str,     # bv. "Amsterdam", puur ter info bij het tonen op de kaart
}
"""

LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


def valideer_locatie(locatie: dict | None) -> dict:
    """Retourneert {"geldig": bool, "problemen": [str, ...]}."""
    if locatie is None:
        return {
            "geldig": False,
            "problemen": [
                "Deze week hoort er een 'locatie' bij je inzending "
                "({'lat': ..., 'lon': ..., 'plaatsnaam': ...}), maar die ontbreekt."
            ],
        }

    if not isinstance(locatie, dict):
        return {"geldig": False, "problemen": ["locatie moet een JSON-object zijn."]}

    problemen = []
    lat = locatie.get("lat")
    lon = locatie.get("lon")
    plaatsnaam = str(locatie.get("plaatsnaam", "")).strip()

    for naam, waarde, ondergrens, bovengrens in (("lat", lat, LAT_MIN, LAT_MAX), ("lon", lon, LON_MIN, LON_MAX)):
        if waarde is None:
            problemen.append(f"'{naam}' ontbreekt in je locatie.")
        elif not isinstance(waarde, (int, float)) or isinstance(waarde, bool):
            problemen.append(f"'{naam}' moet een getal zijn, geen {type(waarde).__name__}.")
        elif not (ondergrens <= waarde <= bovengrens):
            problemen.append(f"'{naam}' moet tussen {ondergrens} en {bovengrens} liggen, jij gaf {waarde}.")

    if not plaatsnaam:
        problemen.append("'plaatsnaam' ontbreekt — puur ter info bij het tonen op de kaart, maar wel verplicht.")

    return {"geldig": len(problemen) == 0, "problemen": problemen}
