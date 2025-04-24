

import streamlit as st
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from upload import upload_to_drive

# ✅ GTFS allalaadimise seadistus
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

# ✅ Kontroll ja allalaadimine
if needs_update(GTFS_ZIP):
    download_latest_gtfs()

# Vaated eraldi failidest
from route import gtfs_view as route_view
from trip import gtfs_view as trip_view
from search_by_line import gtfs_view as line_view
from authority import gtfs_view as authority_view

# CSS laadimine
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("style.css ei leitud. Kujundus võib olla vaikimisi.")

local_css("style.css")

# Sidebar
with st.sidebar:
    st.title("Eesti ühistranspordi avaandmed 1")
    if os.path.exists(GTFS_ZIP):
        est_time = datetime.fromtimestamp(os.path.getmtime(GTFS_ZIP), ZoneInfo("Europe/Tallinn"))
        st.caption(f"📅 GTFS uuendati: {est_time.strftime('%Y-%m-%d %H:%M:%S')}")
    if st.button("Salvesta GTFS Google Drive’i"):
        file_id, file_name = upload_to_drive("gtfs.zip")
        st.success(f"✅ Fail **{file_name}** salvestati Drive’i!")

    go_home = st.button("🏠 Avaleht")
    page = st.selectbox("📂 Vali otsingu alus", ["", "Liininumber",  "Route ID", "Trip ID", "Peatuste kuuluvus"])

# Avaleht kuvatakse nupu või tühja valiku puhul
if go_home or not page:
    st.title("Eesti ühistranspordiregistri avaandmete (GTFS) analüüsi ja valideerimise rakendus ! 👋")
    st.markdown("""
        🚍 **See rakendus võimaldab lihtsalt ja kiiresti:**
        - leida seoseid GTFS-tekstifailide vahel, otsides ühistranspordiliine erinevate parameetrite järgi (nt route_id, trip_id või liini number);  
        - grupeerida peatuseid nende haldaja või kohaliku omavalitsuse kuuluvuse alusel.

        👉 Kasutamiseks vali vasakult lehelt sobiv andmetüüp.
    """)
elif page == "Route ID":
    route_view()
elif page == "Trip ID":
    trip_view()
elif page == "Liininumber":
    line_view()
elif page == "Peatuste kuuluvus":
    authority_view()
    

