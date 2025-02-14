import pandas as pd
import zipfile

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

# Kuvame transpordiettevõtted
print("Saadaolevad transpordiettevõtted:")
print(agency_df[['agency_id', 'agency_name']])

# Kasutaja valib agency
selected_agency_id = input("Sisesta agency_id: ")

# Filtreeri liinid valitud agency põhjal
filtered_routes = routes_df[routes_df['agency_id'] == int(selected_agency_id)]

print("\nSeotud liinid:")
print(filtered_routes[['route_id', 'route_short_name', 'route_long_name']])

# Filtreeri trips (sõidud) nende liinide põhjal
filtered_trips = trips_df[trips_df['route_id'].isin(filtered_routes['route_id'])]

print("\nSeotud trips (sõidud):")
print(filtered_trips[['trip_id', 'route_id', 'service_id', 'trip_headsign']])

# Kasutaja valib trip_id
selected_trip_id = input("\nSisesta trip_id, mille kohta soovid peatuste infot: ")

# Filtreeri stop_times tabel trip_id järgi
filtered_stop_times = stop_times_df[stop_times_df['trip_id'] == int(selected_trip_id)]

# Leia peatuste andmed
filtered_stops = stops_df[stops_df['stop_id'].isin(filtered_stop_times['stop_id'])]

print("\nSeotud peatused ja ajad:")
merged_data = filtered_stop_times.merge(stops_df, on="stop_id")

# Kuvame peatused ja ajad
print(merged_data[['trip_id', 'stop_id', 'stop_name', 'arrival_time', 'departure_time']])
