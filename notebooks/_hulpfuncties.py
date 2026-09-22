"""
Gedeelde hulpfuncties voor de Poker Analytics Challenge.

Wordt in elk werkcollege-notebook geimporteerd met:
    from _hulpfuncties import export_chart_info, lever_in

Zo wennen studenten aan hetzelfde inlever-recept vanaf Week 1, of hun
grafiek nu met matplotlib/seaborn (statisch) of plotly (interactief) is
gemaakt.
"""
import base64
import io

import requests

API_URL = "https://poker-analytics-api.onrender.com"


def export_chart_info(fig, titel, x_label="", y_label="", library="matplotlib", n_kleuren=None):
    """
    Bouwt de JSON die de API en de Streamlit peer-review hub verwachten.

    fig: een matplotlib Figure (fig, niet ax!), een plotly Figure, of een folium.Map.
    x_label/y_label: niet verplicht bij library="folium" (een kaart heeft geen assen).
    n_kleuren: als je het weet, geef het aantal onderscheidende kleuren dat je
               bewust gebruikt in de plot (voor je eigen Visual Hierarchy-check).
    """
    if library == "matplotlib":
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
        buffer.seek(0)
        figuur_json = base64.b64encode(buffer.read()).decode("utf-8")
    elif library == "plotly":
        figuur_json = fig.to_dict()
    elif library == "folium":
        figuur_json = fig.get_root().render()
    else:
        raise ValueError("library moet 'matplotlib', 'plotly' of 'folium' zijn")

    return {
        "titel": titel,
        "x_label": x_label,
        "y_label": y_label,
        "library": library,
        "n_kleuren": n_kleuren,
        "figuur_json": figuur_json,
    }


def lever_in(student_id, token, week, bot_code, chart_info, strategie=None, bluf_kans=None, locatie=None, api_url=API_URL):
    """
    Stuurt bot-code + grafiek-info naar de API. bot_code is de string-inhoud
    van je .py bestand (bv. open("mijn_bot.py").read()).

    strategie: verplicht vanaf Week 3 ("tight", "loose", "balanced" of "aggressive").
    bluf_kans: verplicht vanaf Week 5 (een kans tussen 0 en 1).
    locatie: verplicht vanaf Week 5, bv. {"lat": 52.37, "lon": 4.89, "plaatsnaam": "Amsterdam"}.
    """
    payload = {"week": week, "bot_code": bot_code, "chart": chart_info}
    if strategie is not None:
        payload["strategie"] = strategie
    if bluf_kans is not None:
        payload["bluf_kans"] = bluf_kans
    if locatie is not None:
        payload["locatie"] = locatie

    response = requests.post(
        f"{api_url}/submit/{student_id}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    resultaat = response.json()
    toon_testuitslag(resultaat)
    return resultaat


ACTIE_BREEDTE = 12


def toon_testuitslag(resultaat):
    """
    Print wat je bot op de testsituaties koos.

    Waarom dit er is: "technisch goedgekeurd" zegt alleen dat je code draait. In
    week 3 leverde een groot deel van de klas de voorbeeldbot uit het notebook
    in -- die draait prima, en in het toernooi foldde 92% van alle beslissingen.
    Niemand die het merkte, want niemand zag wat zijn bot eigenlijk deed.

    Deze tabel laat het zien op het moment dat je er nog iets aan kunt doen.
    """
    check = (resultaat or {}).get("bot_check") or {}
    uitslag = check.get("testuitslag")
    print(resultaat.get("boodschap", ""))
    if not uitslag:
        if check.get("foutmelding"):
            print("  ", check["foutmelding"])
        return

    keuzes = {rij["actie"] for rij in uitslag}
    print(f"\nWat je bot koos op {len(uitslag)} testsituaties:")

    kolommen = [k for k in ("hand", "stack", "ronde", "pot", "inzet_om_te_callen")
                if k in uitslag[0]]
    titels = {"hand": "hand", "stack": "stack", "ronde": "ronde",
              "pot": "pot", "inzet_om_te_callen": "bijleggen"}
    breedtes = {k: max(len(titels[k]), max(len(_kort(r[k])) for r in uitslag))
                for k in kolommen}
    kop = "  " + "  ".join(titels[k].ljust(breedtes[k]) for k in kolommen)
    print(kop + "   ->  actie")
    print("  " + "-" * (len(kop) + 12))
    for rij in uitslag:
        regel = "  " + "  ".join(_kort(rij[k]).ljust(breedtes[k]) for k in kolommen)
        print(f"{regel}   ->  {rij['actie']}")

    if len(keuzes) == 1:
        actie = keuzes.pop()
        print(f"\n  LET OP: je bot koos {len(uitslag)} keer '{actie}'. Hij kijkt dus niet naar")
        print("  zijn kaarten, zijn stack of de ronde. Dat mag, maar in het toernooi")
        print("  levert het niets op -- zie Deel 7 van het werkcollege.")


def _kort(waarde):
    if isinstance(waarde, list):
        return " ".join(str(x) for x in waarde) or "-"
    return str(waarde)
