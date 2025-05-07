import streamlit as st
import os
import time
import zipfile
import shutil
import hashlib
import filecmp
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from history import show_history_view
from route import gtfs_view as route_view
from trip import gtfs_view as trip_view
from search_by_line import gtfs_view as line_view
from authority import gtfs_view as authority_view
from stopPoster import gtfs_view as stop_poster_view
from search_by_stop_pair import gtfs_view as stop_pair_view

GTFS_ZIP = "gtfs.zip"
GTFS_URL = "https://peatus.ee/gtfs/gtfs.zip"
GTFS_TEMP_DIR = "gtfs_temp"
GTFS_MAIN_DIR = "gtfs_data"

# --- Session state flags ---
if "view" not in st.session_state:
    st.session_state.view = "home"
if "filter" not in st.session_state:
    st.session_state.filter = ""
if "force_reload" not in st.session_state:
    st.cache_data.clear()
    st.session_state.force_reload = False

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

def directories_differ(dir1, dir2):
    cmp = filecmp.dircmp(dir1, dir2)
    if cmp.left_only or cmp.right_only or cmp.diff_files:
        return True
    for subdir in cmp.common_dirs:
        if directories_differ(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            return True
    return False

if needs_update(GTFS_ZIP) or st.session_state.force_reload:
    download_latest_gtfs()
    if os.path.exists(GTFS_TEMP_DIR):
        shutil.rmtree(GTFS_TEMP_DIR)
    with zipfile.ZipFile(GTFS_ZIP, 'r') as zip_ref:
        zip_ref.extractall(GTFS_TEMP_DIR)

    if not os.path.exists(GTFS_MAIN_DIR) or directories_differ(GTFS_TEMP_DIR, GTFS_MAIN_DIR):
        if os.path.exists(GTFS_MAIN_DIR):
            shutil.rmtree(GTFS_MAIN_DIR)
        shutil.move(GTFS_TEMP_DIR, GTFS_MAIN_DIR)
        st.success("✅ GTFS andmed uuendati.")


    st.cache_data.clear()
    st.session_state.force_reload = False

elif not os.path.exists(GTFS_MAIN_DIR):
    with zipfile.ZipFile(GTFS_ZIP, 'r') as zip_ref:
        zip_ref.extractall(GTFS_MAIN_DIR)

# --- CSS ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("style.css ei leitud.")

local_css("style.css")

# --- Sidebar ---
with st.sidebar:
    st.title("Eesti ühistranspordi avaandmed 🚍")
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    
    

    if st.button("🏠 Avaleht"):
        st.session_state.view = "home"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""

    if st.button("📂 GTFS ajalugu"):
        st.session_state.view = "history"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""

    if st.button("🚏 Ühistranspordi peatuse info"):
        st.session_state.view = "poster"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""

    if st.button("🔁 Otsing kahe peatuse vahel"):
        st.session_state.view = "stop_pair"
        st.session_state.filter = ""
        st.session_state["filter_select"] = ""

    st.markdown('<div class="filter-label" style="margin-top: 1.5rem; margin-bottom: 0.2rem;">🔍 Otsi ja analüüsi liine: </div>', unsafe_allow_html=True)

    selected = st.selectbox(
        label_visibility="collapsed",
        label="",
        options=["", "Liininumbri järgi", "Route ID järgi", "Trip ID järgi", "Peatuste kuuluvuse järgi"],
        key="filter_select"
        
)
    if selected:
        st.session_state.view = "filter"
        st.session_state.filter = selected
    
            
    if os.path.exists(GTFS_ZIP):
        est_time = datetime.fromtimestamp(os.path.getmtime(GTFS_ZIP), ZoneInfo("Europe/Tallinn"))
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 0.25rem; margin-top: 0.5rem;">
                📅 <strong>GTFS-i uuendati viimati:</strong><br>
                {est_time.strftime('%H:%M:%S %d.%m.%Y')}
            </div>
            """,
            unsafe_allow_html=True
        )
        
    if st.button(":inbox_tray: Uuenda GTFS-i avaandmestikku"):
            st.session_state.force_reload = True
            st.rerun()

# --- Vaadete renderdamine ---
view = st.session_state.view
filter_view = st.session_state.filter

if view == "home":
    st.title("Eesti ühistranspordi avaandmete (GTFS) analüüsi tööriist")
    st.markdown("""
        - 📂 **Sirvi GTFS ajaloo faile**  
          Laadib automaatselt failid Google Drive'ist ja kuvab need mugavas ajateljes.
        - 📊 **Ühistranspordi peatuse info**  
          Peatuste kohta info koondamine, postri ja QR koodi genereerimise võimalus.
        - 🔍 **Otsi ja analüüsi liine**  
          Leia ühendused **route_id, trip_id, liininumbri** või muude parameetrite alusel.
        - 🔗 **Uuri failide vahelisi seoseid**  
          Analüüsi, kuidas erinevad GTFS **.txt** failid omavahel seotud on (nt trips.txt, routes.txt, stop_times.txt).
        - 🗺️ **Grupeeri peatuseid**  
          Filtreeri ja koonda andmeid vastavalt haldurile või kohaliku omavalitsuse kuuluvusele.

        See tööriist on mõeldud ühistranspordiosakonna töötajatele, kuid sobib ka nii transpordiplaneerijale, kes soovib kiiresti näha seoseid avaandmetes, ilma käsitsi **.zip** faile avamata.
    """)

elif view == "history":
    show_history_view()

elif view == "poster":
    stop_poster_view()

elif view == "stop_pair":
    stop_pair_view()

elif view == "filter":
    if filter_view == "Route ID järgi":
        route_view()
    elif filter_view == "Trip ID järgi":
        trip_view()
    elif filter_view == "Liininumbri järgi":
        line_view()
    elif filter_view == "Peatuste kuuluvuse järgi":
        authority_view()
