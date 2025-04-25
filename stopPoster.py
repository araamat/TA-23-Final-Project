import streamlit as st
import pandas as pd
import zipfile
from datetime import datetime, date
import io
import csv

GTFS_ZIP = "gtfs.zip"

def load_gtfs_data():
    try:
        st.info("Laen GTFS andmeid...")
        with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
            stops = pd.read_csv(z.open("stops.txt"))
            stop_times = pd.read_csv(z.open("stop_times.txt"))
            trips = pd.read_csv(z.open("trips.txt"))
            routes = pd.read_csv(z.open("routes.txt"))
        st.info("Andmed laetud edukalt!")
        return stops, stop_times, trips, routes
    except FileNotFoundError as e:
        st.error(f"GTFS failide leidmine ebaõnnestus: {e}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Tekkinud viga andmete laadimisel: {e}")
        return None, None, None, None

def gtfs_view():
    st.title("🖨️ Peatuse ajaplaani postri genereerimine")

    stops, stop_times, trips, routes = load_gtfs_data()

    if stops is not None:
        peatused = sorted(stops['stop_name'].unique())
        peatus = st.selectbox("Vali peatus:", ["— Vali peatus —"] + peatused)
        kuupäev = st.date_input("Vali kuupäev ajaplaani jaoks:", value=date.today())

        if peatus == "— Vali peatus —":
            st.info("Palun vali peatus.")
            return

        filtered_stops = stops[stops['stop_name'] == peatus]

        if filtered_stops.empty:
            st.warning("Valitud peatus ei leitud andmetest.")
            return

        stop_info = filtered_stops.iloc[0]
        stop_ids = filtered_stops['stop_id'].tolist()
        stop_code = stop_info.get("stop_code", "—")

        st.markdown(f"### 🚌 Eesti Ühistransport")
        st.markdown(f"#### 📍 Peatus: **{stop_info['stop_name']}**")
        st.markdown(f"#### 🔢 Stop Code: **{stop_code}**")
        st.markdown(f"#### 📅 Kuupäev: **{kuupäev.strftime('%d.%m.%Y')}**")

        relevant_times = stop_times[stop_times['stop_id'].isin(stop_ids)]
        enriched = relevant_times.merge(trips, on="trip_id").merge(routes, on="route_id")

        enriched['departure_time'] = pd.to_datetime(enriched['departure_time'], format='%H:%M:%S', errors='coerce')
        enriched = enriched.sort_values(["route_short_name", "trip_headsign", "departure_time"])
        enriched['departure_time'] = enriched['departure_time'].dt.strftime('%H:%M')

        if enriched.empty:
            st.warning(f"Sel kuupäeval ({kuupäev.strftime('%d.%m.%Y')}) ei leitud selle peatuse väljumisi.")
        else:
            grouped = enriched.groupby(["route_short_name", "trip_long_name", "route_desc"])
            output_rows = []

            for (route, trip_name, desc), group in grouped:
                times = ", ".join(group['departure_time'].tolist())
                output_rows.append({
                    "Liini nr": route,
                    "Tripi nimi": trip_name,
                    "Väljumised": times,
                    "Marsruut": desc
                })

            poster_df = pd.DataFrame(output_rows, columns=["Liini nr", "Tripi nimi", "Väljumised", "Marsruut"])

            st.subheader("📄 Väljumised grupeeritult")
            st.dataframe(poster_df, use_container_width=True, hide_index=True)

            # CSV fail koos UTF-8 BOM-iga ja päiseinfoga
            csv_buffer = io.StringIO()
            csv_writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL)

            csv_writer.writerow([f"Peatus: {stop_info['stop_name']}"])
            csv_writer.writerow([f"Stop Code: {stop_code}"])
            csv_writer.writerow([f"Kuupäev: {kuupäev.strftime('%d.%m.%Y')}"])
            csv_writer.writerow([])

            csv_writer.writerow(poster_df.columns.tolist())
            for row in poster_df.itertuples(index=False):
                csv_writer.writerow(list(row))

            csv_data = '\ufeff' + csv_buffer.getvalue()
            csv_bytes = csv_data.encode('utf-8')

            st.download_button(
                "⬇️ Laadi poster CSV-na alla",
                csv_bytes,
                file_name=f"poster_{stop_info['stop_name']}.csv",
                mime="text/csv"
            )
    else:
        st.error("Andmete laadimine ebaõnnestus. Kontrollige, kas `gtfs.zip` fail on olemas ja sisaldab kõiki vajalikke andmeid.")
