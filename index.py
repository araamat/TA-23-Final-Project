import streamlit as st
from route import gtfs_view
from trip import gtfs_view

# Lae CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("style.css")

# Navigeerimine
st.sidebar.title("Menüü")

page = st.sidebar.selectbox("Vali leht", ["Avaleht", "Route ID", "Trip ID"])


if page == "Avaleht":
    st.title("Tere tulemast GTFS andmete vaaturisse! 👋")
    st.markdown("""
        🚍 See rakendus võimaldab sul:
        - Otsida transpordiliine `route_id` või `trip_id` järgi  
        - Vaadata seotud peatusi ja ajagraafikuid  
        - Näha visuaalselt kaardil marsruuti  
        - Kontrollida liinide teeninduspäevi ja erandeid  

        👉 Kasutamiseks vali vasakult lehelt **GTFS Liiniandmed**.
    """)

elif page == "Route ID" or page == "Trip ID":
    gtfs_view()
    

