"""
Poker Analytics Challenge — Streamlit Peer-Review Hub

Studenten loggen in met hun student_id + token, kiezen een week, en
beoordelen anonieme grafieken/kaarten van klasgenoten op Visual Hierarchy.
Een docent-tabblad toont de voortgang van de hele klas en kan het toernooi
opnieuw draaien — zonder dat er ergens handmatig nagekeken hoeft te worden.
Het DataCamp-tabblad laat elke student zijn eigen roostervoortgang zien
(en de docent die van de hele klas).

Start lokaal met: streamlit run app.py
(zorg dat de FastAPI-backend in ../api al draait: uvicorn main:app --reload)
"""
import base64

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Poker Analytics Peer Review", page_icon="🃏", layout="centered")

DEFAULT_API_URL = "https://poker-analytics-api.onrender.com"
WEKEN_MET_INLEVERING = [1, 3, 5]


# ---------------------------------------------------------------------------
# API-helpers
# ---------------------------------------------------------------------------
def api_get(pad, token, params=None):
    return requests.get(
        f"{st.session_state.api_url}{pad}",
        params=params or {},
        headers={"Authorization": f"Bearer {token}"},
        timeout=15,
    )


def api_post(pad, token, json_body, params=None):
    return requests.post(
        f"{st.session_state.api_url}{pad}",
        params=params or {},
        json=json_body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )


def _foutmelding(response):
    try:
        return response.json().get("detail", response.text)
    except ValueError:
        return response.text


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "api_url": DEFAULT_API_URL,
        "student_id": "",
        "token": "",
        "week": WEKEN_MET_INLEVERING[0],
        "gallery": None,
        "gallery_week": None,
        "gallery_index": 0,
    }
    for key, waarde in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = waarde


def ingelogd():
    return bool(st.session_state.student_id and st.session_state.token)


# ---------------------------------------------------------------------------
# Chart-weergave — moet alle 3 library's aankunnen (matplotlib, plotly, folium)
# ---------------------------------------------------------------------------
def render_chart(chart):
    library = chart.get("library")
    if library == "matplotlib":
        png_bytes = base64.b64decode(chart["figuur_json"])
        st.image(png_bytes)
    elif library == "plotly":
        import plotly.graph_objects as go

        fig = go.Figure(chart["figuur_json"])
        st.plotly_chart(fig, width="stretch")
    elif library == "folium":
        components.html(chart["figuur_json"], height=450, scrolling=False)
    else:
        st.warning(f"Onbekende library: {library}")


# ---------------------------------------------------------------------------
# Sidebar: inloggen
# ---------------------------------------------------------------------------
def login_sidebar():
    with st.sidebar:
        st.header("Inloggen")
        st.session_state.api_url = st.text_input("API-adres", value=st.session_state.api_url)
        st.session_state.student_id = st.text_input("Student ID", value=st.session_state.student_id)
        st.session_state.token = st.text_input("Token", value=st.session_state.token, type="password")

        huidige_index = (
            WEKEN_MET_INLEVERING.index(st.session_state.week)
            if st.session_state.week in WEKEN_MET_INLEVERING
            else 0
        )
        st.session_state.week = st.selectbox("Week", WEKEN_MET_INLEVERING, index=huidige_index)


# ---------------------------------------------------------------------------
# Peer-review tabblad
# ---------------------------------------------------------------------------
def toon_status():
    response = api_get(f"/status/{st.session_state.student_id}/{st.session_state.week}", st.session_state.token)
    if response.status_code != 200:
        st.warning(f"Kon je status niet ophalen ({response.status_code}): {_foutmelding(response)}")
        return

    status = response.json()
    kolommen = st.columns(3)
    kolommen[0].metric("Ingeleverd", "Ja" if status["ingeleverd"] else "Nee")
    kolommen[1].metric("Technisch goedgekeurd", "Ja" if status["technisch_goedgekeurd"] else "Nee")
    kolommen[2].metric("Reviews gegeven", f"{status['reviews_gegeven']}/{status['reviews_nodig']}")
    if status["voldaan"]:
        st.success("Voldaan voor deze week.")


def laad_gallery():
    response = api_get(
        f"/gallery/{st.session_state.week}",
        st.session_state.token,
        params={"student_id": st.session_state.student_id},
    )
    if response.status_code != 200:
        st.error(f"Kon de gallery niet ophalen ({response.status_code}): {_foutmelding(response)}")
        st.session_state.gallery = []
    else:
        st.session_state.gallery = response.json()
    st.session_state.gallery_week = st.session_state.week
    st.session_state.gallery_index = 0


def peer_review_tab():
    st.subheader(f"Peer review — Week {st.session_state.week}")

    if not ingelogd():
        st.info("Vul links je student ID en token in om te beginnen.")
        return

    toon_status()

    if st.session_state.gallery is None or st.session_state.gallery_week != st.session_state.week:
        laad_gallery()

    gallery = st.session_state.gallery or []

    if not gallery:
        st.info(
            "Geen (nieuwe) grafieken om te beoordelen voor deze week. "
            "Dat kan zijn omdat er nog niemand heeft ingeleverd, of omdat je alles al beoordeeld hebt."
        )
        if st.button("Opnieuw ophalen"):
            laad_gallery()
            st.rerun()
        return

    index = st.session_state.gallery_index
    if index >= len(gallery):
        st.success("Je hebt alle opgehaalde grafieken beoordeeld.")
        if st.button("Meer ophalen"):
            laad_gallery()
            st.rerun()
        return

    huidige = gallery[index]
    st.caption(f"Grafiek {index + 1} van {len(gallery)}")
    st.markdown(f"**Titel:** {huidige['chart']['titel']}")
    render_chart(huidige["chart"])

    with st.form(key=f"review_form_{huidige['anon_id']}"):
        focal_point = st.slider(
            "Focal point — is in één oogopslag duidelijk waar je naar moet kijken?", 1, 5, 3
        )
        focal_point_opmerking = st.text_area(
            "Toelichting bij focal point", placeholder="Wat trekt je oog als eerste, en is dat terecht?"
        )
        kleur_contrast = st.slider(
            "Kleur & contrast — is kleur functioneel gebruikt, of zijn het te veel losse kleuren zonder duidelijk doel?", 1, 5, 3
        )
        kleur_contrast_opmerking = st.text_area(
            "Toelichting bij kleur & contrast", placeholder="Welke kleur draagt bij, welke niet?"
        )
        actietitel = st.slider(
            "Actietitel — vertelt de titel het inzicht, of alleen de variabelen?", 1, 5, 3
        )
        actietitel_opmerking = st.text_area(
            "Toelichting bij actietitel", placeholder="Wat zou een sterkere titel zijn?"
        )
        verzonden = st.form_submit_button("Beoordeling versturen")

    if verzonden:
        ontbreekt = [
            naam
            for naam, waarde in [
                ("focal point", focal_point_opmerking),
                ("kleur & contrast", kleur_contrast_opmerking),
                ("actietitel", actietitel_opmerking),
            ]
            if not waarde.strip()
        ]
        if ontbreekt:
            st.error(f"Vul bij elk criterium een toelichting in — nog leeg bij: {', '.join(ontbreekt)}.")
        else:
            body = {
                "week": st.session_state.week,
                "anon_id": huidige["anon_id"],
                "focal_point_score": focal_point,
                "focal_point_opmerking": focal_point_opmerking,
                "kleur_contrast_score": kleur_contrast,
                "kleur_contrast_opmerking": kleur_contrast_opmerking,
                "actietitel_score": actietitel,
                "actietitel_opmerking": actietitel_opmerking,
            }
            response = api_post(f"/peer-review/{st.session_state.student_id}", st.session_state.token, body)
            if response.status_code == 200:
                st.session_state.gallery_index += 1
                st.rerun()
            else:
                st.error(f"Versturen mislukt ({response.status_code}): {_foutmelding(response)}")


# ---------------------------------------------------------------------------
# Docent-tabblad
# ---------------------------------------------------------------------------
def _toon_toernooi_resultaat(resultaat, gedraaid_nu):
    """Rendert eindstand_per_bot als tabel. gedraaid_nu onderscheidt de twee knoppen in het succesbericht."""
    if gedraaid_nu:
        st.success(
            f"Toernooi opnieuw gedraaid: {resultaat['n_bots']} bots "
            f"({resultaat['aangevuld_met_oefenbots']} oefenbot(s) aangevuld)."
        )
    else:
        st.success(f"Laatst bekende uitslag: {resultaat['n_bots']} bots.")

    eindstand = resultaat.get("eindstand_per_bot") or {}
    if eindstand:
        eindstand_df = pd.DataFrame(
            sorted(eindstand.items(), key=lambda kv: -kv[1]), columns=["bot", "eindstand"]
        )
        st.dataframe(eindstand_df, width="stretch")
    else:
        st.info(resultaat.get("boodschap", "Nog geen eindstand beschikbaar."))


def docent_tab():
    st.subheader("Docent-overzicht")
    docent_token = st.text_input("Docent-token", type="password", key="docent_token")
    week = st.number_input("Week", min_value=1, value=st.session_state.week, step=1, key="docent_week")

    if not docent_token:
        st.info("Vul het docent-token in om het overzicht te zien.")
        return

    if st.button("Overzicht ophalen"):
        response = api_get(f"/export/{int(week)}", docent_token)
        if response.status_code != 200:
            st.error(f"Kon overzicht niet ophalen ({response.status_code}): {_foutmelding(response)}")
        elif not response.json():
            st.info("Nog geen inzendingen voor deze week.")
        else:
            st.dataframe(pd.DataFrame(response.json()), width="stretch")

    st.divider()
    _docent_datacamp(docent_token)

    st.divider()
    st.markdown("**Toernooi-uitslag**")
    vergelijk_met = st.text_input("Vergelijk met week (optioneel, bv. 1)", key="vergelijk_met_week")
    params = {}
    if vergelijk_met:
        params["vergelijk_met_week"] = int(vergelijk_met)

    kolom_ophalen, kolom_opnieuw = st.columns(2)

    with kolom_ophalen:
        if st.button("Huidige uitslag ophalen", help="Leest alleen wat er al bekend is -- start geen nieuwe run."):
            response = api_get(f"/toernooi/{int(week)}/resultaat", docent_token, params=params)
            if response.status_code != 200:
                st.error(f"Mislukt ({response.status_code}): {_foutmelding(response)}")
            elif not response.json().get("gedraaid"):
                st.info("Nog geen toernooi gedraaid voor deze (week/vergelijk-met-week)-combinatie.")
            else:
                _toon_toernooi_resultaat(response.json(), gedraaid_nu=False)

    with kolom_opnieuw:
        if st.button("Toernooi opnieuw draaien", help="Start een verse run (bv. na te late inzendingen)."):
            response = api_post(f"/toernooi/{int(week)}/opnieuw", docent_token, json_body=None, params=params)
            if response.status_code != 200:
                st.error(f"Mislukt ({response.status_code}): {_foutmelding(response)}")
            else:
                _toon_toernooi_resultaat(response.json(), gedraaid_nu=True)



# ---------------------------------------------------------------------------
# DataCamp-tabblad (student ziet alleen zijn eigen stand)
# ---------------------------------------------------------------------------
STATUS_ICOON = {"af": "✅", "te laat af": "🟠", "gemist": "❌", "open": "⬜️"}


def _toon_klascijfers(klas):
    """
    Bewust geen namen: de klas mag zien hoe de groep ervoor staat, niet wie
    er achterloopt. Dit blok mag dus gerust op een scherm in het lokaal.
    """
    kolom_gemiddelde, kolom_positie = st.columns(2)
    kolom_gemiddelde.metric("Klasgemiddelde", f"{klas['gemiddeld_af']} courses af")
    if "jij_staat_boven_percentage" in klas:
        kolom_positie.metric("Jij staat boven", f"{klas['jij_staat_boven_percentage']}% van de klas")
    verdeling = klas.get("verdeling_af") or {}
    if verdeling:
        st.caption(f"Verdeling over {klas['aantal_studenten']} studenten met een DataCamp-account:")
        st.bar_chart(pd.DataFrame({"studenten": verdeling.values()}, index=list(verdeling.keys())))
        st.caption("Horizontaal: aantal afgeronde courses. Verticaal: hoeveel studenten daar staan.")


def datacamp_tab():
    st.subheader("Jouw DataCamp-stand")
    if not ingelogd():
        st.info("Vul links je Student ID en token in om je eigen stand te zien.")
        return

    response = api_get(f"/datacamp/stand/{st.session_state.student_id}", st.session_state.token)
    if response.status_code == 404:
        st.info("Er is nog geen DataCamp-stand ingelezen. Vraag je docent om de wekelijkse update.")
        return
    if response.status_code != 200:
        st.warning(f"Kon je DataCamp-stand niet ophalen ({response.status_code}): {_foutmelding(response)}")
        return

    stand = response.json()
    st.caption(f"Stand van {stand['peildatum']} — de docent werkt dit wekelijks bij.")

    if not stand["gevonden"]:
        st.error(stand["boodschap"])
        _toon_klascijfers(stand["klas"])
        return

    kolom_af, kolom_verstreken, kolom_laat, kolom_xp = st.columns(4)
    kolom_af.metric("Verplicht af", f"{stand['af']} / {stand['totaal']}")
    kolom_verstreken.metric("Deadlines verstreken", stand["van_verstreken"])
    kolom_laat.metric("Na de deadline af", stand["te_laat"])
    kolom_xp.metric("XP dit blok", f"{stand['xp']:,}".replace(",", "."))

    if stand["gemist"]:
        st.error(f"Verstreken deadline nog niet af: {', '.join(stand['gemist'])}")
    else:
        st.success("Je hebt alle verstreken deadlines gehaald.")

    # Aanbevolen courses staan bewust apart en zonder waarschuwing: die tellen
    # niet mee voor je eindresultaat, dus een gemiste deadline is er geen.
    if stand.get("aanbevolen_totaal"):
        st.caption(
            f"Daarnaast {stand['aanbevolen_af']} van de {stand['aanbevolen_totaal']} aanbevolen "
            "courses af. Die tellen niet mee voor je eindresultaat — ze verdiepen de stof."
        )

    tabel = pd.DataFrame(
        [
            {
                "": STATUS_ICOON.get(regel["status"], ""),
                "Code": regel["code"],
                "Course": regel["titel"],
                "Soort": "verplicht" if regel.get("verplicht", True) else "aanbevolen",
                "Deadline": regel["deadline"] if regel.get("verplicht", True) else "—",
                "Afgerond op": regel["afgerond_op"] or "—",
                "Status": regel["status"],
            }
            for regel in stand["courses"]
        ]
    )
    st.dataframe(tabel, width="stretch", hide_index=True)

    st.divider()
    _toon_klascijfers(stand["klas"])


# ---------------------------------------------------------------------------
# Docent: DataCamp-voortgang van de hele klas
# ---------------------------------------------------------------------------
def _docent_datacamp(docent_token):
    st.markdown("**DataCamp-voortgang**")
    if not st.button("DataCamp-overzicht ophalen"):
        return

    response = api_get("/datacamp/overzicht", docent_token)
    if response.status_code == 404:
        st.info("Nog geen snapshot opgeslagen. Draai scripts/datacamp_snapshot.py --stuur-naar-hub.")
        return
    if response.status_code != 200:
        st.error(f"Kon overzicht niet ophalen ({response.status_code}): {_foutmelding(response)}")
        return

    overzicht = response.json()
    st.caption(f"Peildatum {overzicht['peildatum']} (opgehaald {overzicht['opgehaald_op']}).")
    st.dataframe(pd.DataFrame(overzicht["studenten"]), width="stretch", hide_index=True)

    achterblijvers = overzicht["achterblijvers"]
    if achterblijvers:
        st.warning(f"{len(achterblijvers)} student(en) met een verstreken deadline nog open.")
        adressen = "; ".join(a["email"] for a in achterblijvers if a.get("email"))
        st.text_area("E-mailadressen achterblijvers (kopieer naar de BCC-regel)", adressen, height=80)
        st.text_area(
            "Concept-herinnering",
            "Hoi,\n\n"
            "Je DataCamp-opdrachten uit het rooster staan nog open. In DataCamp zie je bij "
            "Assignments precies welke; ik zie de stand van de hele klas wekelijks.\n\n"
            "Loop je vast, kom langs in het werkcollege.\n\nGroet, Jerome",
            height=150,
        )
    else:
        st.success("Niemand heeft een verstreken deadline openstaan.")

    if overzicht["zonder_account"]:
        st.error(
            f"Geen DataCamp-account ({len(overzicht['zonder_account'])}): "
            f"{', '.join(overzicht['zonder_account'])}. Zij krijgen geen assignment-mails en "
            "staan in geen enkel overzicht."
        )
    if overzicht["niet_gekoppeld"]:
        st.info(
            "DataCamp-accounts zonder studentnummer in de klaslijst: "
            f"{', '.join(overzicht['niet_gekoppeld'])}."
        )


# ---------------------------------------------------------------------------
def main():
    init_state()
    st.title("🃏 Poker Analytics — Peer Review Hub")
    login_sidebar()

    tab_review, tab_datacamp, tab_docent = st.tabs(["Peer review", "DataCamp", "Docent"])
    with tab_review:
        peer_review_tab()
    with tab_datacamp:
        datacamp_tab()
    with tab_docent:
        docent_tab()


main()
