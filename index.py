import streamlit as st
import os
import time
import requests

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

# Menüünavigatsioon
st.sidebar.title("Menüü")
page = st.sidebar.selectbox("Vali leht", [
    "Avaleht", 
    "Route ID", 
    "Trip ID", 
    "Liini number", 
    "Peatused"
])

# Vaate valik
if page == "Avaleht":
    st.title("Tere tulemast GTFS andmete vaaturisse! 👋")
    st.markdown("""
        🚍 See rakendus võimaldab sul:
        - Otsida transpordiliine `route_id`, `trip_id` või liini numbri järgi  
        - Vaadata seotud peatusi ja ajagraafikuid  
        - Näha visuaalselt kaardil marsruuti  
        - Kontrollida liinide teeninduspäevi ja erandeid  

        👉 Kasutamiseks vali vasakult lehelt sobiv valik.
    """)
elif page == "Route ID":
    route_view()
elif page == "Trip ID":
    trip_view()
elif page == "Liini number":
    line_view()
elif page == "Peatused":
    authority_view()



# import streamlit as st
# from route_1 import gtfs_view
# from trip import gtfs_view

# # Lae CSS
# def local_css(file_name):
#     with open(file_name) as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# local_css("style.css")

# # Navigeerimine
# st.sidebar.title("Menüü")

# page = st.sidebar.selectbox("Vali leht", ["Avaleht", "Route ID", "Trip ID"])


# if page == "Avaleht":
#     st.title("Tere tulemast GTFS andmete vaaturisse! 👋")
#     st.markdown("""
#         🚍 See rakendus võimaldab sul:
#         - Otsida transpordiliine `route_id` või `trip_id` järgi  
#         - Vaadata seotud peatusi ja ajagraafikuid  
#         - Näha visuaalselt kaardil marsruuti  
#         - Kontrollida liinide teeninduspäevi ja erandeid  

#         👉 Kasutamiseks vali vasakult lehelt **GTFS Liiniandmed**.
#     """)

# elif page == "Route ID" or page == "Trip ID":
#     gtfs_view()
    

