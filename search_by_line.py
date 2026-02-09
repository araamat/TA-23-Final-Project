import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

@st.cache_data(ttl=86400)
def load_data(version=None):  # ← versioon cache võtmes
    base_path = "gtfs_data"
    routes_df = pd.read_csv(os.path.join(base_path, "routes.txt"))
    trips_df = pd.read_csv(os.path.join(base_path, "trips.txt"))
    stop_times_df = pd.read_csv(os.path.join(base_path, "stop_times.txt"))
    stops_df = pd.read_csv(os.path.join(base_path, "stops.txt"))
    calendar_df = pd.read_csv(os.path.join(base_path, "calendar.txt"))
    calendar_dates_df = pd.read_csv(os.path.join(base_path, "calendar_dates.txt"))

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
    routes_df, trips_df, stop_times_df, stops_df, calendar_df, calendar_dates_df = load_data(version=st.session_state["gtfs_version"])

    st.title("🚍 Liininumbri järgi seoste filtreerimine")

    # Session state algseadistus
    if "otsi_input" not in st.session_state:
        st.session_state.otsi_input = ""
    if "otsi_tehtud" not in st.session_state:
        st.session_state.otsi_tehtud = False
    if "sorted_routes" not in st.session_state:
        st.session_state.sorted_routes = []
    if "valik" not in st.session_state:
        st.session_state.valik = None
    if "automaatne_valik" not in st.session_state:
        st.session_state.automaatne_valik = False

    with st.form("line_search_form"):
        otsi = st.text_input("🔍 Sisesta liininumber:", placeholder="Nt 5 või 198B", key="otsi_input")
        search_clicked = st.form_submit_button("🔍 Otsi")

    if search_clicked and otsi:
        otsi_lower = otsi.lower().strip()

        # VÕTAME ainult need, mille route_short_name algab õigesti
        filtered_routes = routes_df[routes_df['route_short_name'].str.lower().str.startswith(otsi_lower)]

        if filtered_routes.empty:
            # Kui mitte midagi ei leitud
            st.session_state.sorted_routes = []
            st.session_state.valik = None
            st.session_state.otsi_tehtud = False
            st.session_state.automaatne_valik = False
            st.warning("❌ Sellist liini ei leitud. Palun proovi uuesti.")
        else:
            sorted_routes = custom_sort(filtered_routes['valik'], otsi_lower)

            täpsed_vasted = [v for v in sorted_routes if v.split(" ")[0].lower() == otsi_lower]

            if len(täpsed_vasted) == 1:
                st.session_state.valik = täpsed_vasted[0]
                st.session_state.otsi_tehtud = True
                st.session_state.automaatne_valik = True
            else:
                st.session_state.sorted_routes = sorted_routes
                st.session_state.valik = None
                st.session_state.otsi_tehtud = True
                st.session_state.automaatne_valik = False

    # Kuvame õiged teated vastavalt olukorrale
    if not st.session_state.otsi_tehtud and not st.session_state.valik:
        st.info("Sisesta liininumber")
    elif st.session_state.sorted_routes and not st.session_state.valik:
        st.success("✅ Nüüd vali sobiv liin allolevast nimekirjast!")
    elif st.session_state.otsi_tehtud and st.session_state.valik and st.session_state.automaatne_valik:
        st.info(f"Leiti ainult üks vaste: **{st.session_state.valik}**")

    # Kui mitu vastet ja valikut pole veel tehtud
    if st.session_state.sorted_routes and len(st.session_state.sorted_routes) > 0 and not st.session_state.valik:
        valikud = ["— Vali liin —"] + list(st.session_state.sorted_routes)
        selected = st.selectbox(
            "**Vali liin:**",
            valikud,
            index=0,
            key="vali_liin"
        )

        if selected != "— Vali liin —":
            st.session_state.valik = selected
            st.session_state.automaatne_valik = False
            st.rerun()

    # Kui valik on tehtud
    if st.session_state.valik and st.session_state.valik != "— Vali liin —":
        valik_df = routes_df[routes_df['valik'] == st.session_state.valik]
        if not valik_df.empty:
            route_id = valik_df['route_id'].iloc[0]
            st.success(f"Valitud liin: {st.session_state.valik} (Route ID: {route_id})")

            relevant_trips = trips_df[trips_df['route_id'] == route_id]
            if relevant_trips.empty:
                st.warning("Selle liiniga ei leitud sõite.")
                return

            relevant_trips['trip_label'] = relevant_trips['trip_id'].astype(str) + " (" + relevant_trips['trip_short_name'] + ")"
            trip_valik = st.selectbox(
                "**Liini Trip ID valik:**",
                relevant_trips['trip_label'],
                key="trip_select",
                placeholder="Vali Trip ID",
                label_visibility="visible"
            )

            selected_trip = relevant_trips[relevant_trips['trip_label'] == trip_valik].iloc[0]
            trip_id = selected_trip['trip_id']
            service_id = selected_trip['service_id']

            st.markdown(f"**Valitud Trip ID:** {trip_id} — **{selected_trip['trip_short_name']}**")

            stop_seq = stop_times_df[stop_times_df['trip_id'] == trip_id].merge(stops_df, on="stop_id").sort_values("stop_sequence")

            if not stop_seq.empty:
                st.write("### Valitud reisiga seotud peatused ja nende andmestik")
                cols = ['stop_sequence', 'stop_id', 'stop_name', 'stop_code', 'arrival_time', 'departure_time']
                cols = [col for col in cols if col in stop_seq.columns]
                stop_seq[cols] = stop_seq[cols].astype(str)
                st.dataframe(stop_seq[cols], use_container_width=True, hide_index=True)

            st.write("**Teenindusperiood**")
            cal = calendar_df[calendar_df['service_id'] == service_id]
            if not cal.empty:
                cal_row = cal.iloc[0]
                day_map = {
                    'monday': 'E',
                    'tuesday': 'T',
                    'wednesday': 'K',
                    'thursday': 'N',
                    'friday': 'R',
                    'saturday': 'L',
                    'sunday': 'P'
                }
                days = ", ".join([day_map[day] for day in day_map if day in cal_row and cal_row[day] == 1])

                st.markdown(
                    f"- **Algus**: {cal_row['start_date'].strftime('%d.%m.%Y')}  \n"
                    f"- **Lõpp**: {cal_row['end_date'].strftime('%d.%m.%Y')}  \n"
                    f"- **Liin käigus päevadel**: {days}"
                )
            else:
                st.info("Teeninduspäevad puuduvad.")

            st.write("**Teenindusperioodi erandid**")
            exceptions = calendar_dates_df[calendar_dates_df['service_id'] == service_id]
            if exceptions.empty:
                st.info("Erandid puuduvad.")
            else:
                for _, row in exceptions.iterrows():
                    muutus = "Reis erandkorras käigus" if row['exception_type'] == 1 else "Tühistatud"
                    st.markdown(f"- {row['date'].strftime('%d.%m.%Y')} — **{muutus}**")

            if not stop_seq.empty:
                st.write("### Peatused kaardil")
                m = folium.Map(location=[stop_seq.iloc[0]['stop_lat'], stop_seq.iloc[0]['stop_lon']], zoom_start=13)
                for _, row in stop_seq.iterrows():
                    folium.Marker(
                        location=[row['stop_lat'], row['stop_lon']],
                        popup=row['stop_name'],
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(m)
                st_folium(m, height=400, width="100%")
