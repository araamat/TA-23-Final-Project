import streamlit as st
import pandas as pd
import zipfile
import re
from gtfs_dropdown_component.gtfs_dropdown import gtfs_dropdown  # 👈 Custom komponent

def gtfs_view():
    st.title("Otsi liini numbri järgi")

    # Lae GTFS ZIP
    GTFS_ZIP = "26022025.zip"
    with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
        z.extractall("gtfs_data")

    # Lae andmefailid
    routes_df = pd.read_csv("gtfs_data/routes.txt")
    trips_df = pd.read_csv("gtfs_data/trips.txt")
    stop_times_df = pd.read_csv("gtfs_data/stop_times.txt")
    stops_df = pd.read_csv("gtfs_data/stops.txt")
    calendar_df = pd.read_csv("gtfs_data/calendar.txt")
    calendar_dates_df = pd.read_csv("gtfs_data/calendar_dates.txt")

    # Kuupäevade parsimine
    calendar_df['start_date'] = pd.to_datetime(calendar_df['start_date'], format='%Y%m%d')
    calendar_df['end_date'] = pd.to_datetime(calendar_df['end_date'], format='%Y%m%d')
    calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], format='%Y%m%d')

    # Valiku tekst kujul: 5 (Lasnamäe – Mustamäe)
    routes_df['valik'] = routes_df['route_short_name'].astype(str) + " (" + routes_df['route_long_name'] + ")"
    route_map = dict(zip(routes_df['valik'], routes_df['route_id']))

    # Sorteeri nagu 5, 5A, 55, 6 jne
    def sort_key(name):
        match = re.match(r'^(\d+)([A-Z]*)', name)
        if match:
            number = int(match.group(1))
            letter = match.group(2) or ''
            return (number, letter)
        return (float('inf'), name)

    sorted_options = sorted(route_map.keys(), key=sort_key)

    # Kasuta oma custom dropdown komponenti
    selected_valik = gtfs_dropdown(sorted_options)

    if selected_valik:
        st.success(f"Valitud liin: {selected_valik}")
        selected_route_id = route_map[selected_valik]
        st.markdown(f"**Route ID**: `{selected_route_id}`")

        # Filtreeri seotud tripid
        filtered_trips = trips_df[trips_df['route_id'] == selected_route_id]
        if not filtered_trips.empty:
            st.subheader("Sõidud (Trips)")
            st.dataframe(filtered_trips[['trip_id', 'service_id', 'trip_headsign']])

            selected_trip_id = st.selectbox("Vali trip_id", filtered_trips['trip_id'].values)
            filtered_stop_times = stop_times_df[stop_times_df['trip_id'] == selected_trip_id]
            filtered_stops = stops_df[stops_df['stop_id'].isin(filtered_stop_times['stop_id'])]

            if not filtered_stops.empty:
                st.subheader("Peatused ja ajad")
                merged = filtered_stop_times.merge(stops_df, on="stop_id")
                st.dataframe(merged[['trip_id', 'stop_id', 'stop_name', 'arrival_time', 'departure_time']])

                st.subheader("Peatused kaardil")
                import folium
                map_center = [filtered_stops.iloc[0]['stop_lat'], filtered_stops.iloc[0]['stop_lon']]
                m = folium.Map(location=map_center, zoom_start=12)
                for _, row in filtered_stops.iterrows():
                    folium.Marker(
                        [row['stop_lat'], row['stop_lon']],
                        popup=row['stop_name'],
                        icon=folium.Icon(color='blue')
                    ).add_to(m)
                st.components.v1.html(m._repr_html_(), height=600)

                st.subheader("Teenuse kättesaadavus")
                service_id = filtered_trips.iloc[0]['service_id']
                st.markdown("**Tavalised päevad**")
                st.dataframe(calendar_df[calendar_df['service_id'] == service_id])
                st.markdown("**Erandid**")
                st.dataframe(calendar_dates_df[calendar_dates_df['service_id'] == service_id])
        else:
            st.warning("Selle liiniga ei leitud seotud sõite.")
    else:
        st.info("Palun vali liin ülaltoodud loendist.")
