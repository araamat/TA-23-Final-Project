import streamlit as st
import pandas as pd
import zipfile
import folium
from folium import plugins

def gtfs_view():
    GTFS_ZIP = "26022025.zip"

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

    st.title("GTFS Andmete Analüüs ja Kaardil Kuvamine")

    selected_trip_id = st.text_input("Sisesta trip_id")
    filtered_trips = trips_df[trips_df['trip_id'].astype(str).str.contains(str(selected_trip_id), na=False)] if selected_trip_id else pd.DataFrame()

    if not filtered_trips.empty:
        st.write(f"Seotud trips trip_id-ga: {selected_trip_id}")
        st.write(filtered_trips[['trip_id', 'route_id', 'service_id', 'trip_headsign']])

        selected_trip_id = st.selectbox("Vali trip_id", filtered_trips['trip_id'].values)
        filtered_stop_times = stop_times_df[stop_times_df['trip_id'] == selected_trip_id]
        filtered_stops = stops_df[stops_df['stop_id'].isin(filtered_stop_times['stop_id'])]

        if not filtered_stops.empty:
            merged_data = filtered_stop_times.merge(stops_df, on="stop_id")
            st.write("Seotud peatused ja ajad:")
            st.write(merged_data[['trip_id', 'stop_id', 'stop_name', 'arrival_time', 'departure_time']])

            st.write("Kuvame peatused kaardil:")
            map_center = [filtered_stops.iloc[0]['stop_lat'], filtered_stops.iloc[0]['stop_lon']]
            m = folium.Map(location=map_center, zoom_start=12)

            for index, row in filtered_stops.iterrows():
                folium.Marker(
                    location=[row['stop_lat'], row['stop_lon']],
                    popup=row['stop_name'],
                    icon=folium.Icon(color='blue', icon='info-sign')
                ).add_to(m)

            map_html = m._repr_html_()
            st.components.v1.html(map_html, height=600)

            st.write("### Liini teenuse kättesaadavus")
            selected_service_id = filtered_trips['service_id'].values[0]
            service_info = calendar_df[calendar_df['service_id'] == selected_service_id]
            exception_info = calendar_dates_df[calendar_dates_df['service_id'] == selected_service_id]

            st.write("**Tavapärased teenuse päevad:**")
            st.write(service_info[['service_id','monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date']])

            st.write("**Erandid (lisa- või tühistatud teenused):**")
            st.write(exception_info[['service_id','date', 'exception_type']])
        else:
            st.warning("Valitud trip_id jaoks ei leitud ühtegi peatust.")
    else:
        if selected_trip_id and filtered_trips.empty:
         st.warning(f"Ei leitud sõite trip_id-ga {selected_trip_id}. Proovige uuesti.")



# import streamlit as st
# import pandas as pd
# import zipfile
# import folium
# from folium import plugins

# def gtfs_view():
#     GTFS_ZIP = "26022025.zip"

#     with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
#         z.extractall("gtfs_data")

#     agency_df = pd.read_csv("gtfs_data/agency.txt")
#     routes_df = pd.read_csv("gtfs_data/routes.txt")
#     trips_df = pd.read_csv("gtfs_data/trips.txt")
#     stop_times_df = pd.read_csv("gtfs_data/stop_times.txt")
#     stops_df = pd.read_csv("gtfs_data/stops.txt")
#     calendar_df = pd.read_csv("gtfs_data/calendar.txt")
#     calendar_dates_df = pd.read_csv("gtfs_data/calendar_dates.txt")

#     calendar_df['start_date'] = pd.to_datetime(calendar_df['start_date'], format='%Y%m%d')
#     calendar_df['end_date'] = pd.to_datetime(calendar_df['end_date'], format='%Y%m%d')
#     calendar_dates_df['date'] = pd.to_datetime(calendar_dates_df['date'], format='%Y%m%d')

#     st.title("GTFS Andmete Analüüs ja Kaardil Kuvamine")

#     selected_route_id = st.text_input("Sisesta trip_id")
#     filtered_trips = trips_df[trips_df['trip_id'].astype(str).str.contains(str(selected_route_id), na=False)] if selected_route_id else pd.DataFrame()

#     if not filtered_trips.empty:
#             st.write(f"Seotud trips trip_id-ga: {selected_route_id}")
#             st.write(filtered_trips[['trip_id', 'route_id', 'service_id', 'trip_headsign']])

#             selected_trip_id = st.selectbox("Vali trip_id", filtered_trips['trip_id'].values)
#             filtered_stop_times = stop_times_df[stop_times_df['trip_id'] == selected_trip_id]
#             filtered_stops = stops_df[stops_df['stop_id'].isin(filtered_stop_times['stop_id'])]

#             if not filtered_stops.empty:
#                 merged_data = filtered_stop_times.merge(stops_df, on="stop_id")
#                 st.write("Seotud peatused ja ajad:")
#                 st.write(merged_data[['trip_id', 'stop_id', 'stop_name', 'arrival_time', 'departure_time']])

#                 st.write("Kuvame peatused kaardil:")
#                 map_center = [filtered_stops.iloc[0]['stop_lat'], filtered_stops.iloc[0]['stop_lon']]
#                 m = folium.Map(location=map_center, zoom_start=12)

#                 for index, row in filtered_stops.iterrows():
#                     folium.Marker(
#                         location=[row['stop_lat'], row['stop_lon']],
#                         popup=row['stop_name'],
#                         icon=folium.Icon(color='blue', icon='info-sign')
#                     ).add_to(m)

#                 map_html = m._repr_html_()
#                 st.components.v1.html(map_html, height=600)

#                 st.write("### Liini teenuse kättesaadavus")
#                 selected_service_id = filtered_trips['service_id'].values[0]
#                 service_info = calendar_df[calendar_df['service_id'] == selected_service_id]
#                 exception_info = calendar_dates_df[calendar_dates_df['service_id'] == selected_service_id]

#                 st.write("**Tavapärased teenuse päevad:**")
#                 st.write(service_info[['service_id','monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date']])

#                 st.write("**Erandid (lisa- või tühistatud teenused):**")
#                 st.write(exception_info[['service_id','date', 'exception_type']])
#             else:
#                 st.warning("Valitud trip_id jaoks ei leitud ühtegi peatust.")
#     else:
#             st.warning(f"Ei leitud liine route_id või trip_id-ga {selected_route_id}. Proovige uuesti.")