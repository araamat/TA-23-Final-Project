import streamlit as st
import pandas as pd
import zipfile
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    GTFS_ZIP = "gtfs.zip"
    with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
        z.extractall("gtfs_data")

    agency_df = pd.read_csv("gtfs_data/agency.txt")
    routes_df = pd.read_csv("gtfs_data/routes.txt")
    trips_df = pd.read_csv("gtfs_data/trips.txt")
    stop_times_df = pd.read_csv("gtfs_data/stop_times.txt")
    stops_df = pd.read_csv("gtfs_data/stops.txt")
    calendar_df = pd.read_csv("gtfs_data/calendar.txt")
    calendar_dates_df = pd.read_csv("gtfs_data/calendar_dates.txt")

    calendar_df['start_date'] = pd.to_datetime(calendar_df['start_date'], format='%Y%m%d')
    calendar_df['end_date'] = pd.to_datetime(calendar_df['end_date'], format='%Y%m%d')
    calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], format='%Y%m%d')

    return routes_df, trips_df, stop_times_df, stops_df, calendar_df, calendar_dates_df

def gtfs_view():
    routes_df, trips_df, stop_times_df, stops_df, calendar_df, calendar_dates_df = load_data()

    st.title("🚏 Liinid route_id järgi")

    selected_route_id = st.text_input("**Sisesta route_id ja vajuta Enter**")

    if selected_route_id:
        filtered_routes = routes_df[routes_df['route_id'].str.contains(selected_route_id, na=False)]
        if filtered_routes.empty:
            st.warning(f"Ei leitud liine route_id-ga **{selected_route_id}**.")
            return

        st.write(f"**Seotud liinid route_id-ga**: {selected_route_id}")
        st.dataframe(filtered_routes[['route_id', 'route_short_name', 'route_long_name']], hide_index=True)

        selected_route = st.selectbox("**Vali täpne route_id**", filtered_routes['route_id'].values)
        filtered_trips = trips_df[trips_df['route_id'] == selected_route]

        st.write(f"### Seotud sõidud liinil **{selected_route}**")
        st.dataframe(filtered_trips[['trip_id', 'service_id', 'trip_headsign']], hide_index=True)

        selected_trip = st.selectbox("**Vali Trip ID**", filtered_trips['trip_id'].values)
        stop_times = stop_times_df[stop_times_df['trip_id'] == selected_trip]
        stop_data = stop_times.merge(stops_df, on="stop_id").sort_values("stop_sequence")

        # 1. Peatused tabelina
        if not stop_data.empty:
            st.write("### Peatused ja väljumisajad")
            cols = ['stop_sequence', 'stop_id', 'stop_name', 'arrival_time', 'departure_time']
            st.dataframe(stop_data[cols], use_container_width=True, hide_index=True)

        # 2. Teenindusperiood
        st.write("### Teenindusperiood")
        service_id = filtered_trips[filtered_trips['trip_id'] == selected_trip]['service_id'].values[0]
        service_info = calendar_df[calendar_df['service_id'] == service_id]
        if not service_info.empty:
            row = service_info.iloc[0]
            day_labels = {
                'monday': 'E', 'tuesday': 'T', 'wednesday': 'K', 'thursday': 'N',
                'friday': 'R', 'saturday': 'L', 'sunday': 'P'
            }
            days = [label for day, label in day_labels.items() if row[day] == 1]
            st.markdown(
                f"- **Algus**: {row['start_date'].date()}  \n"
                f"- **Lõpp**: {row['end_date'].date()}  \n"
                f"- **Käigus päevadel**: {' '.join(days)}"
            )
        else:
            st.info("Teenindusperioodi andmed puuduvad.")

        # 3. Erandid
        st.write("### Teenindusperioodi erandid")
        exceptions = calendar_dates_df[calendar_dates_df['service_id'] == service_id]
        if exceptions.empty:
            st.info("Erandid puuduvad.")
        else:
            for _, row in exceptions.iterrows():
                muutus = "Lisatud" if row['exception_type'] == 1 else "Tühistatud"
                st.markdown(f"- {row['date'].date()} — **{muutus}**")

        # 4. Kaart VIIMASENA
        if not stop_data.empty:
            st.write("### Peatused kaardil")
            m = folium.Map(location=[stop_data.iloc[0]['stop_lat'], stop_data.iloc[0]['stop_lon']], zoom_start=13)
            for _, row in stop_data.iterrows():
                folium.Marker(
                    location=[row['stop_lat'], row['stop_lon']],
                    popup=row['stop_name'],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
            st_folium(m, height=400, width="100%")
