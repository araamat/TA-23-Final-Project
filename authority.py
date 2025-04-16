import streamlit as st
import pandas as pd
import zipfile
import folium

def gtfs_view():
    GTFS_ZIP = "26022025.zip"

    with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
        z.extractall("gtfs_data")

    stops_df = pd.read_csv("gtfs_data/stops.txt")

    st.title("Otsi peatuseid valla (authority) alusel")

    if 'authority' not in stops_df.columns:
        st.error("Failis 'stops.txt' puudub veerg 'authority'.")
        return

    # Loeme unikaalsed valla nimed ja sorteerime need
    authorities = sorted(stops_df['authority'].dropna().unique())

    selected_authority = st.selectbox("Vali vald:", [""] + authorities)

    filtered_stops = stops_df[
        stops_df['authority'] == selected_authority
    ] if selected_authority else pd.DataFrame()

    if not filtered_stops.empty:
        st.success(f"Leiti {len(filtered_stops)} peatust vallast: {selected_authority}")
        st.dataframe(filtered_stops[['stop_id', 'stop_name', 'authority', 'stop_lat', 'stop_lon']])

        st.write("Kaart:")
        map_center = [filtered_stops.iloc[0]['stop_lat'], filtered_stops.iloc[0]['stop_lon']]
        m = folium.Map(location=map_center, zoom_start=11)

        for _, row in filtered_stops.iterrows():
            folium.Marker(
                location=[row['stop_lat'], row['stop_lon']],
                popup=f"{row['stop_name']} ({row['authority']})",
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)

        st.components.v1.html(m._repr_html_(), height=600)
    elif selected_authority:
        st.warning("Selles vallas ei leitud ühtegi peatust.")
# tundub väga oluline