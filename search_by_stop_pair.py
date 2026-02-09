import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

@st.cache_data(ttl=86400)
def load_gtfs_data(version=None):
    base_path = "gtfs_data"
    stops = pd.read_csv(os.path.join(base_path, "stops.txt"))
    stop_times = pd.read_csv(os.path.join(base_path, "stop_times.txt"))
    trips = pd.read_csv(os.path.join(base_path, "trips.txt"))
    routes = pd.read_csv(os.path.join(base_path, "routes.txt"))
    calendar = pd.read_csv(os.path.join(base_path, "calendar.txt"))
    
    # Agency võib puududa
    agency_path = os.path.join(base_path, "agency.txt")
    agency = pd.read_csv(agency_path) if os.path.exists(agency_path) else None

    return stops, stop_times, trips, routes, calendar, agency

def parse_gtfs_time(t):
    if pd.isna(t):
        return pd.NaT
    try:
        h, m, s = map(int, t.split(":"))
        h = h % 24
        return pd.Timestamp(f"2000-01-01 {h:02}:{m:02}:{s:02}")
    except:
        return pd.NaT

def gtfs_view():
    st.title("🔁 Otsing kahe peatuse vahel")

    stops, stop_times, trips, routes, calendar, agency = load_gtfs_data(version=st.session_state.get("gtfs_version"))

    def format_peatus(row):
        code = row.get("stop_code", "—")
        desc = row.get("stop_desc", "")
        desc = "" if pd.isna(desc) else desc
        return f"{row['stop_name']} ({code}{', ' + desc if desc else ''})"

    stops['peatus_valik'] = stops.apply(format_peatus, axis=1)
    peatus_dict = dict(zip(stops['peatus_valik'], stops['stop_id']))

    col1, col2 = st.columns(2)
    with col1:
        alg_valik = st.selectbox("**Algpeatus**", ["— Vali peatus —"] + list(peatus_dict.keys()), key="algpeatus")
    with col2:
        lopp_valik = st.selectbox("**Sihtpeatus**", ["— Vali peatus —"] + list(peatus_dict.keys()), key="lopppeatus")

    if alg_valik == "— Vali peatus —" or lopp_valik == "— Vali peatus —":
        st.info("Palun vali mõlemad peatused.")
        return

    alg_stop_id = str(peatus_dict[alg_valik])
    lopp_stop_id = str(peatus_dict[lopp_valik])

    stop_times['stop_id'] = stop_times['stop_id'].astype(str)
    stop_times['trip_id'] = stop_times['trip_id'].astype(str)
    trips['trip_id'] = trips['trip_id'].astype(str)
    trips['route_id'] = trips['route_id'].astype(str)
    trips['service_id'] = trips['service_id'].astype(str)
    routes['route_id'] = routes['route_id'].astype(str)
    calendar['service_id'] = calendar['service_id'].astype(str)

    # Agency on valikuline
    if 'agency_id' in trips.columns and agency is not None:
        trips['agency_id'] = trips['agency_id'].astype(str)
        agency['agency_id'] = agency['agency_id'].astype(str)
        merge_with_agency = True
    else:
        merge_with_agency = False

    stop_times['stop_sequence'] = stop_times['stop_sequence'].astype(int)
    stop_times['departure_time'] = stop_times['departure_time'].apply(parse_gtfs_time)
    stop_times['arrival_time'] = stop_times['arrival_time'].apply(parse_gtfs_time)

    alg_trips = stop_times[stop_times['stop_id'] == alg_stop_id][['trip_id','departure_time','stop_sequence']].copy()
    lopp_trips = stop_times[stop_times['stop_id'] == lopp_stop_id][['trip_id','arrival_time','stop_sequence']].copy()

    merged = pd.merge(alg_trips, lopp_trips, on='trip_id', suffixes=('_alg','_lopp'))
    sobivad = merged[merged['stop_sequence_alg'] < merged['stop_sequence_lopp']]

    if sobivad.empty:
        st.warning("Ei leitud liine, mis läbivad valitud peatused õiges järjekorras.")
        return

    enriched = sobivad.merge(trips, on='trip_id').merge(routes, on='route_id').merge(calendar, on='service_id')
    
    # Kui agency olemas, lisa merge
    if merge_with_agency:
        enriched = enriched.merge(agency, on='agency_id')
        enriched['Vedaja'] = enriched['agency_name']
    else:
        enriched['Vedaja'] = "—"

    enriched['Väljumine'] = enriched['departure_time'].dt.strftime('%H:%M')
    enriched['Saabumine'] = enriched['arrival_time'].dt.strftime('%H:%M')
    enriched['Trip ID'] = enriched['trip_id'].astype(str)
    enriched['Liini nimetus'] = enriched.get('trip_short_name', '')
    enriched['Liin'] = enriched.get('route_short_name', '')

    for day, abbr in zip(['monday','tuesday','wednesday','thursday','friday','saturday','sunday'], ['E','T','K','N','R','L','P']):
        enriched[abbr] = enriched[day].apply(lambda x: abbr if x == 1 else '')

    final_df = enriched[['Liin','Väljumine','Saabumine','Liini nimetus','Vedaja','E','T','K','N','R','L','P','Trip ID']]
    final_df = final_df.sort_values('Väljumine')
    st.markdown(f"### ✅ Leitud {len(final_df)} sõitu kahe peatuse vahel:")
    st.dataframe(final_df,use_container_width=True,hide_index=True)
