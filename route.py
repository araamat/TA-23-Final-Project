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

    st.title("🚏 Route ID järgi seoste filtreerimine")

    # Tekstiväli ja Otsi-nupp eraldatud CSS-wrapperiga
    st.text_input("**Sisesta route_id:**", key="route_input", placeholder="nt dc6d5ccae7f41a36dd71c4b569278734 või midagi sarnast")

    st.markdown('<div class="otsi-wrapper">', unsafe_allow_html=True)
    search_clicked = st.button("🔍 Otsi", key="otsi_button")
    st.markdown('</div>', unsafe_allow_html=True)


    if search_clicked and st.session_state.get("route_input"):
        st.session_state["submitted_route"] = st.session_state["route_input"]

    if "submitted_route" in st.session_state and st.session_state["submitted_route"]:
        selected_route_id = st.session_state["submitted_route"]
        filtered_routes = routes_df[routes_df['route_id'].astype(str).str.contains(selected_route_id, na=False)]

        if filtered_routes.empty:
            st.warning(f"Ei leitud liine route_id-ga **{selected_route_id}**.")
            return

        def wrap_text(value):
            if len(value) > 10:
                return value[:10] + "\n" + value[10:]
            return value

        filtered_routes_display = filtered_routes.copy()
        filtered_routes_display['route_short_name'] = filtered_routes_display['route_short_name'].astype(str).apply(wrap_text)

        st.write(f"**Seotud liinid Route ID-ga**: {selected_route_id}")
        st.dataframe(filtered_routes_display[['route_id', 'route_short_name', 'route_long_name']], hide_index=True, use_container_width=True)

        selected_route = st.selectbox("**Vali täpne Route ID**", filtered_routes['route_id'].values)
        filtered_trips = trips_df[trips_df['route_id'] == selected_route]

        if not filtered_trips.empty:
            trips_display = filtered_trips[['trip_id', 'service_id', 'trip_headsign', 'trip_long_name']].copy()
            trips_display = trips_display.astype(str)
            st.write(f"**Seotud reisid liinil:** {selected_route}")
            st.dataframe(trips_display, use_container_width=True, hide_index=True)

        selected_trip = st.selectbox("**Liini Trip ID valik:**", filtered_trips['trip_id'].values)
        stop_times = stop_times_df[stop_times_df['trip_id'] == selected_trip]
        stop_data = stop_times.merge(stops_df, on="stop_id").sort_values("stop_sequence")

        if not stop_data.empty:
            st.write("### Valitud reisiga seotud peatused ja nende andmestik")
            cols = ['stop_sequence', 'stop_id', 'stop_code', 'stop_name', 'arrival_time', 'departure_time']
            existing_cols = [col for col in cols if col in stop_data.columns]
            st.dataframe(stop_data[existing_cols].astype(str), use_container_width=True, hide_index=True)

        st.write("**Teenindusperiood**")
        service_id = filtered_trips[filtered_trips['trip_id'] == selected_trip]['service_id'].values[0]
        service_info = calendar_df[calendar_df['service_id'] == service_id]
        if not service_info.empty:
            row = service_info.iloc[0]
            day_labels = {
                'monday': 'E', 'tuesday': 'T', 'wednesday': 'K', 'thursday': 'N',
                'friday': 'R', 'saturday': 'L', 'sunday': 'P'
            }
            days = ", ".join([label for day, label in day_labels.items() if row[day] == 1])
            st.markdown(
                f"- **Algus**: {row['start_date'].strftime('%d.%m.%Y')}  \n"
                f"- **Lõpp**: {row['end_date'].strftime('%d.%m.%Y')}  \n"
                f"- **Käigus päevadel**: {days}"
            )
        else:
            st.info("Teenindusperioodi andmed puuduvad.")

        st.write("**Teenindusperioodi erandid**")
        exceptions = calendar_dates_df[calendar_dates_df['service_id'] == service_id]
        if exceptions.empty:
            st.info("Erandid puuduvad.")
        else:
            for _, row in exceptions.iterrows():
                muutus = "Muudetud" if row['exception_type'] == 1 else "Tühistatud"
                st.markdown(f"- {row['date'].strftime('%d.%m.%Y')} — **{muutus}**")

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
