import streamlit as st
import pandas as pd
import zipfile
from datetime import date
import io
import csv
import qrcode
from PIL import Image
import base64

GTFS_ZIP = "gtfs.zip"

def load_gtfs_data():
    try:
        with zipfile.ZipFile(GTFS_ZIP, 'r') as z:
            stops = pd.read_csv(z.open("stops.txt"))
            stop_times = pd.read_csv(z.open("stop_times.txt"))
            trips = pd.read_csv(z.open("trips.txt"))
            routes = pd.read_csv(z.open("routes.txt"))
            calendar = pd.read_csv(z.open("calendar.txt"))
        return stops, stop_times, trips, routes, calendar
    except Exception as e:
        st.error(f"Viga GTFS andmete laadimisel: {e}")
        return None, None, None, None, None

def gtfs_view():
    st.title("🖨️ Peatuse ajaplaani postri genereerimine")

    stops, stop_times, trips, routes, calendar = load_gtfs_data()

    if stops is not None:
        peatused = sorted(stops['stop_name'].unique())
        peatus = st.selectbox("Vali peatus:", ["— Vali peatus —"] + peatused)

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

        stop_id = stop_info['stop_id']
        stop_code_url = stop_info.get("stop_code", "").replace(" ", "%20")
        qr_link = f"https://web.peatus.ee/pysakit/estonia%3A{stop_id}#{stop_code_url}"

        cols = st.columns([3, 1])

        with cols[0]:  # Vasakul tekstid
            st.markdown(f"### 📍 Peatus: **{stop_info['stop_name']}**")
            st.markdown(f"### 🔢 Stop Code: **{stop_code}**")
            st.markdown(f"### 📅 Genereeritud: **{date.today().strftime('%d.%m.%Y')}**")

        with cols[1]:  # Paremal QR, link ja download link keskel
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            qr.add_data(qr_link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
            st.image(buffer.getvalue(), width=120)
            st.markdown(f"<div style='margin-top: 8px;'><a href='{qr_link}' target='_blank' style='text-decoration: none;'>↗️ Ava link </a></div>", unsafe_allow_html=True)

            # QR-pildi baasil allalaaditav link
            b64 = base64.b64encode(buffer.getvalue()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="qr_{stop_info["stop_name"]}.png">⬇️ Lae alla QR</a>'
            st.markdown(f"<div style='margin-top: 8px;'>{href}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Väljumised ---
        relevant_times = stop_times[stop_times['stop_id'].isin(stop_ids)]
        enriched = relevant_times.merge(trips, on="trip_id").merge(routes, on="route_id").merge(calendar, on="service_id")

        enriched['departure_time'] = pd.to_datetime(enriched['departure_time'], format='%H:%M:%S', errors='coerce')
        enriched = enriched.sort_values(["route_short_name", "trip_headsign", "departure_time"])
        enriched['departure_time'] = enriched['departure_time'].dt.strftime('%H:%M')

        if enriched.empty:
            st.warning("Selle peatuse jaoks ei leitud väljumisi.")
            return

        weekday_columns = {
            "monday": "E",
            "tuesday": "T",
            "wednesday": "K",
            "thursday": "N",
            "friday": "R",
            "saturday": "L",
            "sunday": "P"
        }

        output_rows = []
        grouped = enriched.groupby(["route_short_name", "trip_long_name", "route_desc"])

        for (route, trip_name, desc), group in grouped:
            weekday_departures = {v: [] for v in weekday_columns.values()}

            for _, row in group.iterrows():
                for day_key, abbrev in weekday_columns.items():
                    if row.get(day_key) == 1:
                        weekday_departures[abbrev].append(row['departure_time'])

            seen = {}
            for weekday, times in weekday_departures.items():
                time_strs = [t.strip() for t in times if t]
                if not time_strs:
                    continue
                time_str = ", ".join(time_strs)
                if time_str in seen:
                    seen[time_str].append(weekday)
                else:
                    seen[time_str] = [weekday]

            for time_str, weekdays in seen.items():
                output_rows.append({
                    "Liini nr": route,
                    "Liini nimetus": trip_name,
                    "Liin on käigus": ", ".join(weekdays),
                    "Väljumised": time_str,
                    "Liini info": desc
                })

        flat_rows = []
        for row in output_rows:
            line = f"'{row['Liini nr']}" if "-" in str(row['Liini nr']) else row['Liini nr']
            weekdays = row["Liin on käigus"].split(", ")
            times = row["Väljumised"].split(", ")

            for time in times:
                flat_rows.append({
                    "Väljumine": time.strip(),
                    "Liini nr": line,
                    "Liini nimetus": row["Liini nimetus"],
                    "Liin on käigus": ", ".join(weekdays),
                    "Liini info": row["Liini info"]
                })

        poster_df = pd.DataFrame(flat_rows)
        poster_df["Väljumine"] = pd.to_datetime(poster_df["Väljumine"], format="%H:%M", errors='coerce')
        poster_df = poster_df.sort_values("Väljumine")
        poster_df["Väljumine"] = poster_df["Väljumine"].dt.strftime("%H:%M")
        poster_df = poster_df[["Väljumine", "Liini nr", "Liini nimetus", "Liin on käigus", "Liini info"]]

        st.subheader("📄 Väljumised")
        st.dataframe(poster_df, use_container_width=True, hide_index=True)

        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL)

        csv_writer.writerow([f"Peatus: {stop_info['stop_name']}"])
        csv_writer.writerow([f"Stop Code: {stop_code}"])
        csv_writer.writerow([f"Genereeritud: {date.today().strftime('%d.%m.%Y')}"])
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
        st.error("GTFS andmete laadimine ebaõnnestus.")
