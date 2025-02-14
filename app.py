import streamlit as st
import pandas as pd
import zipfile
import folium
from folium import plugins

GTFS_ZIP = "140225_gtfs.zip"

# Ekstrahi GTFS failid
with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
    z.extractall("gtfs_data")

# Lae andmed
agency_df = pd.read_csv("gtfs_data/agency.txt")
routes_df = pd.read_csv("gtfs_data/routes.txt")
trips_df = pd.read_csv("gtfs_data/trips.txt")
stop_times_df = pd.read_csv("gtfs_data/stop_times.txt")
stops_df = pd.read_csv("gtfs_data/stops.txt")

st.title("GTFS Andmete Analüüs ja Kaardil Kuvamine")

# **1. Kasutaja valib agency**
selected_agency_id = st.selectbox("Vali transpordiettevõte", agency_df['agency_name'].values)

# Filtreeri liinid (routes) valitud agency põhjal
selected_agency = agency_df[agency_df['agency_name'] == selected_agency_id]
filtered_routes = routes_df[routes_df['agency_id'] == selected_agency['agency_id'].values[0]]

st.write(f"Seotud liinid ettevõttele: {selected_agency_id}")
st.write(filtered_routes[['route_id', 'route_short_name', 'route_long_name']])

# **2. Kasutaja valib route_id**
selected_route_id = st.selectbox("Vali route_id", filtered_routes['route_id'].values)

# Filtreeri trips (sõidud) selle `route_id` järgi
filtered_trips = trips_df[trips_df['route_id'] == selected_route_id]

st.write(f"Seotud trips (sõidud) liinil {selected_route_id}")
st.write(filtered_trips[['trip_id', 'service_id', 'trip_headsign']])

# **3. Kasutaja valib trip_id**
selected_trip_id = st.selectbox("Vali trip_id", filtered_trips['trip_id'].values)

# Filtreeri stop_times selle `trip_id` järgi
filtered_stop_times = stop_times_df[stop_times_df['trip_id'] == selected_trip_id]

# Leia seotud peatused (`stops.txt`) vastavalt stop_id-le
filtered_stops = stops_df[stops_df['stop_id'].isin(filtered_stop_times['stop_id'])]

# Kuvame peatused ja ajad
merged_data = filtered_stop_times.merge(stops_df, on="stop_id")
st.write("Seotud peatused ja ajad:")
st.write(merged_data[['trip_id', 'stop_id', 'stop_name', 'arrival_time', 'departure_time']])

# **4. Kuvame peatused kaardil**
st.write("Kuvame peatused kaardil:")

# Alusta kaarti, keskendudes esimesse peatuse asukohta
map_center = [filtered_stops.iloc[0]['stop_lat'], filtered_stops.iloc[0]['stop_lon']]
m = folium.Map(location=map_center, zoom_start=12)

# Lisame markerid kõikidele peatustele
for index, row in filtered_stops.iterrows():
    folium.Marker(
        location=[row['stop_lat'], row['stop_lon']],
        popup=row['stop_name'],
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

# Salvestame kaardi HTML formaati
map_html = m._repr_html_()

# Kuvame kaardi Streamlitis HTML formaadis
st.components.v1.html(map_html, height=600)
