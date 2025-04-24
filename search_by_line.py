
import streamlit as st
import pandas as pd
import zipfile
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_data():
    GTFS_ZIP = "gtfs.zip"
    with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
        routes_df = pd.read_csv(z.open("routes.txt"))
        trips_df = pd.read_csv(z.open("trips.txt"))
        stop_times_df = pd.read_csv(z.open("stop_times.txt"))
        stops_df = pd.read_csv(z.open("stops.txt"))
        calendar_df = pd.read_csv(z.open("calendar.txt"))
        calendar_dates_df = pd.read_csv(z.open("calendar_dates.txt"))

    routes_df['route_short_name'] = routes_df['route_short_name'].astype(str)
    routes_df['valik'] = routes_df['route_short_name'] + " (" + routes_df['route_long_name'] + ")"
    calendar_df['start_date'] = pd.to_datetime(calendar_df['start_date'], format='%Y%m%d')
    calendar_df['end_date'] = pd.to_datetime(calendar_df['end_date'], format='%Y%m%d')
    calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], format='%Y%m%d')

    return routes_df, trips_df, stop_times_df, stops_df, calendar_df, calendar_dates_df

def custom_sort(valikud, otsi):
    otsi = otsi.lower().strip()
    exact_match = []
    letter_extensions = []
    numeric_extensions = []
    others = []

    for valik in valikud:
        prefix = valik.split(" ")[0].lower()
        if prefix == otsi:
            exact_match.append(valik)
        elif prefix.startswith(otsi) and prefix != otsi:
            suffix = prefix[len(otsi):]
            if suffix.isalpha():
                letter_extensions.append((suffix, valik))
            elif suffix.isdigit():
                numeric_extensions.append((int(suffix), valik))
            else:
                others.append(valik)
        else:
            others.append(valik)

    letter_extensions.sort()
    numeric_extensions.sort()
    return (
        exact_match +
        [v for _, v in letter_extensions] +
        [v for _, v in numeric_extensions] +
        others
    )


def gtfs_view():
    routes_df, trips_df, stop_times_df, stops_df, calendar_df, calendar_dates_df = load_data()

    st.title("🚍 Liininumbri järgi otsing")

    otsi = st.text_input("Sisesta liininumber, kui soovid, et järgmises lahtris sorteeritakse tulemuseid")

    # Sort loogika
    otsi_lower = otsi.lower()
    exact, starts, others = [], [], []
    for v in routes_df['valik']:
        v_lower = v.lower()
        if v_lower.startswith(otsi_lower + " "):
            exact.append(v)
        elif v_lower.startswith(otsi_lower):
            starts.append(v)
        else:
            pass
            others.append(v)
    sorted_routes = custom_sort(routes_df['valik'], otsi)

    valik = st.selectbox("**Vali liin**", ["— Vali liin —"] + list(sorted_routes if otsi else routes_df['valik']))


    if valik and valik != "— Vali liin —":
        valik_df = routes_df[routes_df['valik'] == valik]
        if valik_df.empty:
            st.warning("Valitud liini ei leitud.")
            return
        route_id = valik_df['route_id'].iloc[0]
        st.markdown(f"### Valitud liin: **{valik}**  \n**Liini Route ID väärtus:** {route_id}")

        relevant_trips = trips_df[trips_df['route_id'] == route_id]
        if not relevant_trips.empty:
            relevant_trips['trip_label'] = relevant_trips['trip_id'].astype(str) + " (" + relevant_trips['trip_long_name'] + ")"
            trip_valik = st.selectbox("**Liini Trip ID valik:**", relevant_trips['trip_label'], key="trip_select",  placeholder="Vali trip",  label_visibility="visible")
            selected_trip = relevant_trips[relevant_trips['trip_label'] == trip_valik].iloc[0]
            trip_id = selected_trip['trip_id']
            service_id = selected_trip['service_id']

            st.markdown(f"**Valitud Trip ID:** {trip_id} **Trip long name:** {selected_trip['trip_long_name']}")

            stop_seq = stop_times_df[stop_times_df['trip_id'] == trip_id].merge(stops_df, on="stop_id").sort_values("stop_sequence")

            if not stop_seq.empty:
                st.write("### Valitud liini Trip ID-ga seotud peatused ja nende andmestik")
                cols = ['stop_sequence', 'stop_id', 'stop_name', 'stop_code', 'arrival_time', 'departure_time']
                cols = [col for col in cols if col in stop_seq.columns]
                stop_seq[cols] = stop_seq[cols].astype(str)
                st.dataframe(stop_seq[cols], use_container_width=True, hide_index=True)

                st.write("### Peatused kaardil")
                m = folium.Map(location=[stop_seq.iloc[0]['stop_lat'], stop_seq.iloc[0]['stop_lon']], zoom_start=13)
                for _, row in stop_seq.iterrows():
                    folium.Marker(
                        location=[row['stop_lat'], row['stop_lon']],
                        popup=row['stop_name'],
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
                with st.container():
                 st_folium(m, height=400, width="100%")

            st.write("### Teenindusperiood")
            cal = calendar_df[calendar_df['service_id'] == service_id]
            if not cal.empty:
                cal_row = cal.iloc[0]
                day_map = {
                    'monday': 'Esmaspäev',
                    'tuesday': 'Teisipäev',
                    'wednesday': 'Kolmapäev',
                    'thursday': 'Neljapäev',
                    'friday': 'Reede',
                    'saturday': 'Laupäev',
                    'sunday': 'Pühapäev'
                }
                days = ", ".join([day_map[day] for day in day_map if day in cal_row and cal_row[day] == 1])

                
                st.markdown(
    f"- **Algus**: {cal_row['start_date'].date()}  \n"
    f"- **Lõpp**: {cal_row['end_date'].date()}  \n"
    f"- **Liin on käigus**: {days}"
)


            else:
                st.info("**Teeninduspäevad puuduvad.**")

            st.write("### Teenindusperioodi erandid")
            exceptions = calendar_dates_df[calendar_dates_df['service_id'] == service_id]
            if exceptions.empty:
                st.info("**Erandid puuduvad.**")
            else:
                for _, row in exceptions.iterrows():
                    muutus = "Lisatud" if row['exception_type'] == 1 else "Liin ei ole käigus."
                    st.markdown(f"- {row['date'].date()} — **{muutus}**")
        else:
            st.warning("Selle liiniga ei leitud sõite.")
