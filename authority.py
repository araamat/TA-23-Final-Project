import streamlit as st
import pandas as pd
import folium
import os

def load_data(version=None):  # ← lisab cache'i võtme
    base_path = "gtfs_data"
    stops_df = pd.read_csv(os.path.join(base_path, "stops.txt"))
    return stops_df

def gtfs_view():
    stops_df = load_data(version=st.session_state["gtfs_version"])

    st.title("🚏 Peatuste filtreerimine kuuluvuse järgi")

    search_type = st.radio("**Vali tunnus, mille järgi soovid peatusi grupeerida:**", ["Haldaja", "Kohalik omavalitsus"])

    if search_type == "Haldaja":
        if 'authority' not in stops_df.columns:
            st.error("Failis 'stops.txt' puudub veerg 'authority'.")
            return

        stops_df['authority'] = stops_df['authority'].astype(str)
        authorities = sorted(stops_df['authority'].dropna().unique())
        selected_authority = st.selectbox("**Vali haldaja:**", [""] + authorities)

        filtered_stops = stops_df[stops_df['authority'] == selected_authority] if selected_authority else pd.DataFrame()

    elif search_type == "Kohalik omavalitsus":
        if 'stop_area' not in stops_df.columns:
            st.error("Failis 'stops.txt' puudub veerg 'stop_area'.")
            return

        stops_df['stop_area'] = stops_df['stop_area'].astype(str)
        stop_areas = sorted(stops_df['stop_area'].dropna().unique())
        selected_area = st.selectbox("Vali kohalik omavalitsus:", [""] + stop_areas)

        filtered_stops = stops_df[stops_df['stop_area'] == selected_area] if selected_area else pd.DataFrame()

    if not filtered_stops.empty:
        filtered_stops = filtered_stops.fillna('')


        filtered_stops['stop_id'] = filtered_stops['stop_id'].astype(str)
        st.success(f"Leiti {len(filtered_stops)} peatust.")

        COLS = ['stop_id', 'stop_name', 'stop_code', 'stop_desc', 'stop_lat', 'stop_lon']
        st.dataframe(filtered_stops[COLS], hide_index=True, use_container_width=True)

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
    else:
        if search_type == "Asutus (authority)" and selected_authority:
            st.warning("Selle asutusega ei leitud ühtegi peatust.")
        elif search_type == "Vald/Linn (stop_area)" and selected_area:
            st.warning("Selle stop_area väärtusega ei leitud ühtegi peatust.")

# CSS tabeli laiuse ühtlustamiseks valikukastiga
st.markdown("""
<style>
.streamlit-table {
    width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.streamlit-table table {
    width: 100% !important;
    table-layout: fixed;
}
.streamlit-table th, .streamlit-table td {
    text-align: center !important;
    white-space: normal !important;
    word-wrap: break-word !important;
}
</style>
""", unsafe_allow_html=True)
