import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

@st.cache_data(ttl=86400)
def load_gtfs_data():
    base_path = "gtfs_data"
    stops = pd.read_csv(os.path.join(base_path, "stops.txt"))
    stop_times = pd.read_csv(os.path.join(base_path, "stop_times.txt"))
    trips = pd.read_csv(os.path.join(base_path, "trips.txt"))
    routes = pd.read_csv(os.path.join(base_path, "routes.txt"))
    calendar = pd.read_csv(os.path.join(base_path, "calendar.txt"))
    agency = pd.read_csv(os.path.join(base_path, "agency.txt"))
    return stops, stop_times, trips, routes, calendar, agency


def gtfs_view():
    st.title("🔁 Otsing kahe peatuse vahel")

    stops, stop_times, trips, routes, calendar, agency = load_gtfs_data()

    def format_peatus(row):
        code = row.get("stop_code", "—")
        desc = row.get("stop_desc", "")
        desc = "" if pd.isna(desc) else desc
        return f"{row['stop_name']} ({code}{', ' + desc if desc else ''})"

    stops['peatus_valik'] = stops.apply(format_peatus, axis=1)
    peatus_dict = dict(zip(stops['peatus_valik'], stops['stop_id']))

    st.markdown("### 🚏 Vali alg- ja sihtpeatus:")
    col1, col2 = st.columns(2)
    with col1:
        alg_valik = st.selectbox("**Algpeatus**", ["— Vali peatus —"] + list(peatus_dict.keys()), key="algpeatus")
    with col2:
        lopp_valik = st.selectbox("**Sihtpeatus**", ["— Vali peatus —"] + list(peatus_dict.keys()), key="lopppeatus")

    if alg_valik == "— Vali peatus —" or lopp_valik == "— Vali peatus —":
        st.info("Palun vali mõlemad peatused.")
        return

    alg_stop_id = peatus_dict[alg_valik]
    lopp_stop_id = peatus_dict[lopp_valik]

    alg_peatus = stops[stops['stop_id'] == alg_stop_id].iloc[0]
    lopp_peatus = stops[stops['stop_id'] == lopp_stop_id].iloc[0]

    st.markdown(f"**Algpeatus:** {alg_peatus['stop_name']} ({alg_peatus.get('stop_code', '')})")
    st.markdown(f"**Sihtpeatus:** {lopp_peatus['stop_name']} ({lopp_peatus.get('stop_code', '')})")

    alg_trips = stop_times[stop_times['stop_id'] == alg_stop_id][['trip_id', 'departure_time', 'stop_sequence']]
    lopp_trips = stop_times[stop_times['stop_id'] == lopp_stop_id][['trip_id', 'arrival_time', 'stop_sequence']]

    merged = pd.merge(alg_trips, lopp_trips, on='trip_id', suffixes=('_alg', '_lopp'))
    sobivad = merged[merged['stop_sequence_alg'] < merged['stop_sequence_lopp']]

    if sobivad.empty:
        st.warning("Ei leitud liine, mis läbivad valitud peatused õiges järjekorras.")
        return

    enriched = (
        sobivad
        .merge(trips, on='trip_id')
        .merge(routes, on='route_id')
        .merge(calendar, on='service_id')
        .merge(agency, on='agency_id')
    )

    enriched['Väljumine'] = enriched['departure_time']
    enriched['Saabumine'] = enriched['arrival_time']
    enriched['Trip ID'] = enriched['trip_id'].astype(str).str.replace(",", "")
    enriched['Liini nimetus'] = enriched['trip_long_name']
    enriched['Vedaja'] = enriched['agency_name']
    enriched['Liin'] = enriched['route_short_name']

    # Uus veergude formaadis paevade jaotus
    enriched['E'] = enriched['monday'].apply(lambda x: 'E' if x == 1 else '')
    enriched['T'] = enriched['tuesday'].apply(lambda x: 'T' if x == 1 else '')
    enriched['K'] = enriched['wednesday'].apply(lambda x: 'K' if x == 1 else '')
    enriched['N'] = enriched['thursday'].apply(lambda x: 'N' if x == 1 else '')
    enriched['R'] = enriched['friday'].apply(lambda x: 'R' if x == 1 else '')
    enriched['L'] = enriched['saturday'].apply(lambda x: 'L' if x == 1 else '')
    enriched['P'] = enriched['sunday'].apply(lambda x: 'P' if x == 1 else '')

    final_df = enriched[['Väljumine', 'Saabumine','Liini nimetus','Liin','Vedaja', 'E', 'T', 'K', 'N', 'R', 'L', 'P', 'Trip ID']]
    final_df = final_df.sort_values('Väljumine')

    
    st.markdown(f"### ✅ Leitud {len(final_df)} sõitu kahe peatuse vahel:")
    st.dataframe(final_df, use_container_width=True, hide_index=True)

    if st.checkbox("**:arrow_left: avab liini peatuste kuvamise nii tabelis kui ka kaardil**"):
        trip_options = enriched[['trip_id', 'trip_long_name']].drop_duplicates()
        trip_options['valik'] = trip_options['trip_id'].astype(str) + " — " + trip_options['trip_long_name']
        valik_dict = dict(zip(trip_options['valik'], trip_options['trip_id']))
        valitud_valik = st.selectbox("**Vali Trip**", list(valik_dict.keys()))
        trip_valik = valik_dict[valitud_valik]

        stops_for_map = stop_times[stop_times['trip_id'] == trip_valik].merge(stops, on="stop_id").sort_values("stop_sequence")
        valitud_trip_long_name = enriched[enriched['trip_id'] == trip_valik]['trip_long_name'].values[0]

        if not stops_for_map.empty:
            st.markdown("### 📋 Valitud liini peatused järjestuses")
            peatusetabel = stops_for_map[['stop_sequence', 'stop_name', 'stop_code', 'arrival_time', 'departure_time']]
            peatusetabel = peatusetabel.rename(columns={
                'stop_sequence': 'Järjekord',
                'stop_name': 'Peatus nimi',
                'stop_code': 'Stop code',
                'arrival_time': 'Saabumine',
                'departure_time': 'Väljumine'
            })
            st.dataframe(peatusetabel, use_container_width=True, hide_index=True)

            st.subheader("🗌️ Valitud liini peatused kaardil")
            keskpunkt = [stops_for_map.iloc[0]['stop_lat'], stops_for_map.iloc[0]['stop_lon']]
            m = folium.Map(location=keskpunkt, zoom_start=13)
            for idx, row in stops_for_map.iterrows():
                folium.Marker(
                    location=[row['stop_lat'], row['stop_lon']],
                    popup=f"{row['stop_name']} ({valitud_trip_long_name})",
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)
            st_folium(m, height=500, width="100%")
