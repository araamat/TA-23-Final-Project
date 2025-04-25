import streamlit as st
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from history import show_history_view
from route import gtfs_view as route_view
from trip import gtfs_view as trip_view
from search_by_line import gtfs_view as line_view
from authority import gtfs_view as authority_view
from stopPoster import gtfs_view as stop_poster_view

GTFS_ZIP = "gtfs.zip"
GTFS_URL = "https://peatus.ee/gtfs/gtfs.zip"

# --- Andmefaili uuendamine ---
def needs_update(filepath, hours=24):
    if not os.path.exists(filepath):
        return True
    last_modified = os.path.getmtime(filepath)
    return (time.time() - last_modified) > hours * 3600

def download_latest_gtfs():
    st.info("Laadin uusimat GTFS andmestikku...")
    response = requests.get(GTFS_URL)
    with open(GTFS_ZIP, "wb") as f:
        f.write(response.content)
    st.success("GTFS andmestik uuendatud!")

if needs_update(GTFS_ZIP):
    download_latest_gtfs()

# --- CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("style.css ei leitud.")

local_css("style.css")

# --- session_state ---
if "view" not in st.session_state:
    st.session_state.view = "home"
if "filter" not in st.session_state:
    st.session_state.filter = ""

# --- Sidebar ---
# --- Sidebar ---
with st.sidebar:
    st.title("Eesti ühistranspordi avaandmed 🚍")

    if os.path.exists(GTFS_ZIP):
        est_time = datetime.fromtimestamp(os.path.getmtime(GTFS_ZIP), ZoneInfo("Europe/Tallinn"))
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 1rem; margin-top: 0.5rem;">
                📅 <strong>GTFS uuendati:</strong><br>
                {est_time.strftime('%H:%M:%S %d.%m.%Y')}
            </div>
            """,
            unsafe_allow_html=True
        )

    if st.button("🏠 Avaleht"):
        st.session_state.view = "home"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""

    if st.button("📂 GTFS ajalugu"):
        st.session_state.view = "history"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""
        
    if st.button("📂 Peatuse postri genereerimine"):
        st.session_state.view = "poster"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""

    # Filtri valik (pealkiri + selectbox)
    st.markdown('<div class="filter-label">🔍 Vali filtreerimise alus: </div>', unsafe_allow_html=True)
    selected = st.selectbox(
        "",
        ["", "Liininumber", "Route ID", "Trip ID", "Peatuste kuuluvus"],
        key="filter_select"
    )

    if selected:
        st.session_state.view = "filter"
        st.session_state.filter = selected


# --- Vaadete renderdamine ---
view = st.session_state.view
filter_view = st.session_state.filter

if view == "home":
    st.title("Eesti ühistranspordi avaandmete (GTFS) analüüsi tööriist")
    st.markdown("""
        - 📂 **Sirvi GTFS ajaloo faile**  
          Laadib automaatselt failid Google Drive'ist ja kuvab need mugavas ajateljes.
        - 🔍 **Otsi ja analüüsi liine**  
          Leia ühendused **route_id, trip_id, liininumbri** või muude parameetrite alusel.
        - 🔗 **Uuri failide vahelisi seoseid**  
          Analüüsi, kuidas erinevad GTFS **.txt** failid omavahel seotud on (nt trips.txt, routes.txt, stop_times.txt).
        - 🗺️ **Grupeeri peatuseid**  
          Filtreeri ja koonda andmeid vastavalt haldurile või kohaliku omavalitsuse kuuluvusele.
        - 📊 **Tulevane plaan**  
          Peatuste postrite genereerimine.

        See tööriist on mõeldud ühistranspordiosakonna töötajatele, kuid sobib ka nii transpordiplaneerijale, kes soovib kiiresti näha seoseid avaandmetes, ilma käsitsi **.zip** faile avamata.
    """)

elif view == "history":
    show_history_view()
    
elif view == "poster":
    stop_poster_view()

elif view == "filter":
    if filter_view == "Route ID":
        route_view()
    elif filter_view == "Trip ID":
        trip_view()
    elif filter_view == "Liininumber":
        line_view()
    elif filter_view == "Peatuste kuuluvus":
        authority_view()