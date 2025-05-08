import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

@st.cache_data(ttl=86400)
def load_data():
    base_path = "gtfs_data"
    trips_df = pd.read_csv(os.path.join(base_path, "trips.txt"))
    routes_df = pd.read_csv(os.path.join(base_path, "routes.txt"))
    stop_times_df = pd.read_csv(os.path.join(base_path, "stop_times.txt"))
    stops_df = pd.read_csv(os.path.join(base_path, "stops.txt"))
    calendar_df = pd.read_csv(os.path.join(base_path, "calendar.txt"))
    calendar_dates_df = pd.read_csv(os.path.join(base_path, "calendar_dates.txt"))

    calendar_df['start_date'] = pd.to_datetime(calendar_df['start_date'], format='%Y%m%d')
    calendar_df['end_date'] = pd.to_datetime(calendar_df['end_date'], format='%Y%m%d')
    calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], format='%Y%m%d')

    return trips_df, routes_df, stop_times_df, stops_df, calendar_df, calendar_dates_df


def gtfs_view():
    trips_df, routes_df, stop_times_df, stops_df, calendar_df, calendar_dates_df = load_data()

    st.title("🚍 Trip ID järgi seoste filtreerimine")

    with st.form("trip_search_form"):
        trip_input = st.text_input("**Sisesta Trip ID:**", placeholder="nt 1220349 või midagi sarnast")
        otsi_klikitud = st.form_submit_button("🔍 Otsi")

    if otsi_klikitud and trip_input:
     st.session_state["submitted_trip"] = trip_input

    if otsi_klikitud and st.session_state.get("trip_input"):
        st.session_state["submitted_trip"] = st.session_state["trip_input"]

    if "submitted_trip" in st.session_state and st.session_state["submitted_trip"]:
        selected_trip_id = st.session_state["submitted_trip"]
        filtered_trips = trips_df[trips_df['trip_id'].astype(str).str.contains(str(selected_trip_id), na=False)]
        if filtered_trips.empty:
            st.warning(f"Ei leitud sõite trip_id-ga **{selected_trip_id}**.")
            return

        st.write(f"**Seotud sõidud Trip ID-ga**: {selected_trip_id}")
        st.dataframe(filtered_trips[['trip_id', 'route_id', 'service_id', 'trip_headsign', 'trip_long_name']].astype(str), use_container_width=True, hide_index=True)

        trip_ids = filtered_trips['trip_id'].unique()

        if len(trip_ids) == 1:
            selected_trip = trip_ids[0]
            st.success(f"Ainus vaste: **{selected_trip}** valiti automaatselt.")
        else:
            selected_trip = st.selectbox("**Vali täpne Trip ID**", trip_ids)

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
                muutus = "Reis erandkorras käigus" if row['exception_type'] == 1 else "Tühistatud"
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
