"""
Technische validatie van de ingeleverde grafiek-metadata.

Studenten leveren vanaf Week 1 hetzelfde JSON-formaat aan, ongeacht of de
grafiek met matplotlib/seaborn (statisch) of plotly (interactief) is
gemaakt. Zie notebooks/_hulpfuncties.py -> export_chart_info() voor hoe dit
JSON in het notebook wordt gebouwd.

Verwacht schema:
{
    "titel": str,
    "x_label": str,             # niet verplicht bij library "folium" (een kaart heeft geen assen)
    "y_label": str,             # niet verplicht bij library "folium"
    "library": "matplotlib" | "plotly" | "folium",
    "n_kleuren": int,          # aantal onderscheidende kleuren in de plot
    "figuur_json": dict | str  # plotly fig.to_dict(), base64 PNG-string, of folium-HTML-string
}

Deze module checkt alleen de dingen die geautomatiseerd te checken zijn
(titel aanwezig en niet generiek, assen gelabeld). De echte beoordeling op
Visual Hierarchy (focal point, kleurgebruik, storytelling) gebeurt bewust
niet hier, maar in de peer-review op de Streamlit Hub — dat is precies het
punt van dit vak.
"""

GENERIEKE_TITELS = {
    "", "grafiek", "plot", "figure", "figure 1", "untitled", "chart",
    "plot 1", "titel", "mijn grafiek", "chipstack vs tijd", "kaarten",
    "vul hier een echte actietitel in",
}

# Vangnet naast de exacte-match-lijst hierboven: elke placeholder-tekst in de
# notebooks begint met "vul hier" ("vul hier je student_id in", "vul hier een
# echte actietitel in", ...). Als een titel daarmee begint, is die zo goed als
# zeker nooit aangepast — precies wat er in de praktijk al gebeurde bij 2 van
# de 3 eerste echte inzendingen.
GENERIEKE_TITEL_PREFIXES = ("vul hier",)

MIN_TITEL_LENGTE = 8


def valideer_chart_json(chart: dict) -> dict:
    """Retourneert {"geldig": bool, "problemen": [str, ...]}."""
    problemen = []

    if not isinstance(chart, dict):
        return {"geldig": False, "problemen": ["chart moet een JSON-object zijn."]}

    titel = str(chart.get("titel", "")).strip()
    x_label = str(chart.get("x_label", "")).strip()
    y_label = str(chart.get("y_label", "")).strip()
    library = chart.get("library")
    figuur_json = chart.get("figuur_json")

    titel_lower = titel.lower()
    if not titel or titel_lower in GENERIEKE_TITELS or titel_lower.startswith(GENERIEKE_TITEL_PREFIXES):
        problemen.append(
            "Je titel ontbreekt, is te generiek, of is nog de placeholder-tekst uit het notebook. "
            "Gebruik een actietitel die het inzicht samenvat, geen kolomnamen (bv. niet 'Chipstack vs Tijd')."
        )
    elif len(titel) < MIN_TITEL_LENGTE:
        problemen.append("Je titel is wel aanwezig, maar erg kort — is dit al een echte actietitel?")

    if library != "folium":
        if not x_label:
            problemen.append("x_label ontbreekt: label je assen.")
        if not y_label:
            problemen.append("y_label ontbreekt: label je assen.")

    if library not in ("matplotlib", "plotly", "folium"):
        problemen.append("library moet 'matplotlib', 'plotly' of 'folium' zijn.")

    if not figuur_json:
        problemen.append("figuur_json ontbreekt — zonder dit kan de Streamlit Hub je grafiek niet tonen.")

    return {"geldig": len(problemen) == 0, "problemen": problemen}
