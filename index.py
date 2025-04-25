import streamlit as st
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

from history import show_history_view

GTFS_ZIP = "gtfs.zip"
GTFS_URL = "https://peatus.ee/gtfs/gtfs.zip"


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

from route import gtfs_view as route_view
from trip import gtfs_view as trip_view
from search_by_line import gtfs_view as line_view
from authority import gtfs_view as authority_view

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("style.css ei leitud. Kujundus võib olla vaikimisi.")

local_css("style.css")

with st.sidebar:
    st.title("Eesti ühistranspordi avaandmed 🚍")
    if os.path.exists(GTFS_ZIP):
        est_time = datetime.fromtimestamp(os.path.getmtime(GTFS_ZIP), ZoneInfo("Europe/Tallinn"))
        st.caption(f"📅 Avaandmete faili GTFS-i uuendati: {est_time.strftime('**%H:%M:%S %d-%m-%Y**')}")

    if st.button("🏠 Avaleht"):
        st.session_state["view"] = "home"
    if st.button("📂 GTFS ajalugu"):
        st.session_state["view"] = "history"

    page = st.selectbox("📂 Vali otsingu alus", ["", "Liininumber",  "Route ID", "Trip ID", "Peatuste kuuluvus"])

if "view" not in st.session_state:
    st.session_state["view"] = "home"

view = st.session_state["view"]

if view == "home" and not page:
    st.title("Eesti ühistranspordiregistri avaandmete (GTFS) analüüsi ja valideerimise rakendus")
    st.markdown("""
        🚍 **See rakendus võimaldab lihtsalt ja kiiresti:**
        - leida seoseid GTFS-tekstifailide vahel, otsides ühistranspordiliine erinevate parameetrite järgi (nt route_id, trip_id või liini number);  
        - grupeerida peatuseid nende haldaja või kohaliku omavalitsuse kuuluvuse alusel.
        👉 Kasutamiseks vali vasakult lehelt sobiv andmetüüp.
    """)

elif view == "history":
    show_history_view()
elif page == "Route ID":
    route_view()
elif page == "Trip ID":
    trip_view()
elif page == "Liininumber":
    line_view()
elif page == "Peatuste kuuluvus":
    authority_view()
