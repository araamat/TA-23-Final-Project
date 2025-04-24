import streamlit as st
import pandas as pd
import zipfile
import folium

def gtfs_view():
    GTFS_ZIP = "gtfs.zip"

    with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
        z.extractall("gtfs_data")

    stops_df = pd.read_csv("gtfs_data/stops.txt")

    st.title("🚏 Otsi ühistranspordi peatuseid")

    search_type = st.radio("Vali tunnus, mille järgi soovid peatusi grupeerida:", ["Asutus (authority)", "Vald/Linn (stop_area)"])

    if search_type == "Asutus (authority)":
        if 'authority' not in stops_df.columns:
            st.error("Failis 'stops.txt' puudub veerg 'authority'.")
            return

        stops_df['authority'] = stops_df['authority'].astype(str)
        authorities = sorted(stops_df['authority'].dropna().unique())
        selected_authority = st.selectbox("Vali asutus:", [""] + authorities)

        filtered_stops = stops_df[stops_df['authority'] == selected_authority] if selected_authority else pd.DataFrame()

    elif search_type == "Vald/Linn (stop_area)":
        if 'stop_area' not in stops_df.columns:
            st.error("Failis 'stops.txt' puudub veerg 'stop_area'.")
            return

        stops_df['stop_area'] = stops_df['stop_area'].astype(str)
        stop_areas = sorted(stops_df['stop_area'].dropna().unique())
        selected_area = st.selectbox("Vali vald/linn:", [""] + stop_areas)

        filtered_stops = stops_df[stops_df['stop_area'] == selected_area] if selected_area else pd.DataFrame()

    if not filtered_stops.empty:
        st.success(f"Leiti {len(filtered_stops)} peatust.")
        st.dataframe(filtered_stops[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']])

        st.write("Kaart:")
        map_center = [filtered_stops.iloc[0]['stop_lat'], filtered_stops.iloc[0]['stop_lon']]
        m = folium.Map(location=map_center, zoom_start=11)

        for _, row in filtered_stops.iterrows():
            folium.Marker(
                location=[row['stop_lat'], row['stop_lon']],
                popup=f"{row['stop_name']}",
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)

        st.components.v1.html(m._repr_html_(), height=600)
    elif search_type == "Asutus (authority)" and selected_authority:
        st.warning("Selle asutusega ei leitud ühtegi peatust.")
    elif search_type == "Vald/Linn (stop_area)" and selected_area:
        st.warning("Selle stop_area väärtusega ei leitud ühtegi peatust.")