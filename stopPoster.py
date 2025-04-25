import streamlit as st
import pandas as pd
import zipfile
from datetime import datetime

# GTFS fail (eeldame, et see fail on olemas rakenduses)
GTFS_ZIP = "gtfs.zip"

# GTFS failide laadimine
def load_gtfs_data():
    try:
        st.info("Laen GTFS andmeid...")  # Lisa logimine
        with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
            st.info("GTFS fail avatud.")  # Kontrollige, kas zip-fail avatakse
            stops = pd.read_csv(z.open("stops.txt"))
            stop_times = pd.read_csv(z.open("stop_times.txt"))
            trips = pd.read_csv(z.open("trips.txt"))
            routes = pd.read_csv(z.open("routes.txt"))
        st.info("Andmed laetud edukalt!")  # Logi, et kõik andmed on laetud
        return stops, stop_times, trips, routes
    except FileNotFoundError as e:
        st.error(f"GTFS failide leidmine ebaõnnestus: {e}")
        return None, None, None, None
    except Exception as e:
        st.error(f"Tekkinud viga andmete laadimisel: {e}")
        return None, None, None, None

# Peatuse ajaplaani postri genereerimine
def gtfs_view():
    st.title("🖨️ Peatuse ajaplaani postri genereerimine")

    # Lae GTFS andmed
    stops, stop_times, trips, routes = load_gtfs_data()

    if stops is not None:
        # Kui andmed on laetud, siis edasi:
        # Valiku kuupäev ja peatus
        peatused = sorted(stops['stop_name'].unique())
        peatus = st.selectbox("Vali peatus:", ["— Vali peatus —"] + peatused)

        kuupäev = st.date_input("Vali kuupäev ajaplaani jaoks:", value=datetime.today())

        if peatus and kuupäev:
            stop_info = stops[stops['stop_name'] == peatus].iloc[0]
            stop_ids = stops[stops['stop_name'] == peatus]['stop_id'].tolist()

            st.markdown(f"**📍 Peatus:** {stop_info['stop_name']}")
            st.markdown(f"**🆔 Stop ID:** {', '.join(map(str, stop_ids))}")
            st.markdown(f"**🔢 Stop Code:** {stop_info.get('stop_code', '—')}")

            # Väljumiste leidmine
            relevant_times = stop_times[stop_times['stop_id'].isin(stop_ids)]
            enriched = relevant_times.merge(trips, on="trip_id").merge(routes, on="route_id")

            enriched['departure_time'] = pd.to_datetime(enriched['departure_time'], format='%H:%M:%S', errors='coerce')
            enriched = enriched.sort_values(["route_short_name", "trip_headsign", "departure_time"])
            enriched['departure_time'] = enriched['departure_time'].dt.strftime('%H:%M')

            if enriched.empty:
                st.warning(f"Sel kuupäeval ({kuupäev.strftime('%d.%m.%Y')}) ei leitud selle peatuse väljumisi.")
            else:
                # Gruppide loogika
                grouped = enriched.groupby(["route_short_name", "trip_headsign", "route_desc"])

                output_rows = []
                for (route, headsign, desc), group in grouped:
                    times = ", ".join(group['departure_time'].tolist())
                    output_rows.append({
                        "Liini nr": route,
                        "Sihtkoht": headsign,
                        "Marsruut": desc,
                        "Väljumised": times
                    })

                poster_df = pd.DataFrame(output_rows)

                st.subheader("📄 Väljumised grupeeritult")
                st.dataframe(poster_df, use_container_width=True, hide_index=True)

                csv = poster_df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Laadi poster CSV-na alla", csv, file_name=f"poster_{peatus}.csv", mime="text/csv")
