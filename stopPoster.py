import streamlit as st
import pandas as pd
import os
import io
import csv
import qrcode
import base64
from PIL import Image
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage,
    Frame, PageTemplate
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm


@st.cache_data(ttl=86400)
def load_gtfs_data(version=None):
    try:
        base_path = "gtfs_data"
        stops = pd.read_csv(os.path.join(base_path, "stops.txt"))
        stop_times = pd.read_csv(os.path.join(base_path, "stop_times.txt"))
        trips = pd.read_csv(os.path.join(base_path, "trips.txt"))
        routes = pd.read_csv(os.path.join(base_path, "routes.txt"))
        calendar = pd.read_csv(os.path.join(base_path, "calendar.txt"))
        return stops, stop_times, trips, routes, calendar
    except Exception as e:
        st.error(f"Viga GTFS andmete laadimisel: {e}")
        return None, None, None, None, None


def smart_wrap_text(text, max_length=30):
    lines = []
    current_line = ""

    for char in text:
        current_line += char
        if len(current_line) >= max_length:
            last_space = current_line.rfind(" ")
            last_dash = current_line.rfind("-")
            split_pos = max(last_space, last_dash)

            if split_pos != -1:
                lines.append(current_line[:split_pos+1].strip())
                current_line = current_line[split_pos+1:].strip()
            else:
                lines.append(current_line.strip())
                current_line = ""

    if current_line:
        lines.append(current_line.strip())

    return "<br/>".join(lines)

def first_page_header(canvas, doc, stop_info, stop_code, qr_img, kuupaev):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawString(20 * mm, A4[1] - 30 * mm, f"Peatus: {stop_info['stop_name']}")
    canvas.setFont('Helvetica', 10)
    canvas.drawString(20 * mm, A4[1] - 40 * mm, f"Stop Code: {stop_code}")
    canvas.drawString(20 * mm, A4[1] - 48 * mm, f"Kehtiv alates: {kuupaev.strftime('%d.%m.%Y')}")
    if qr_img:
        qr_rl = RLImage(qr_img, width=40*mm, height=40*mm)
        qr_rl.drawOn(canvas, A4[0] - 60 * mm, A4[1] - 60 * mm)
    canvas.restoreState()

def later_pages_header(canvas, doc, stop_info, kuupaev):
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(20 * mm, A4[1] - 20 * mm, f"Peatus: {stop_info['stop_name']} — {kuupaev.strftime('%d.%m.%Y')}")
    canvas.restoreState()

def generate_pdf(stop_info, stop_code, qr_img, poster_df, kuupaev):
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()

    qr_buffer = io.BytesIO()
    qr_img.resize((100, 100)).save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    elements = []

    first_frame = Frame(20*mm, 20*mm, A4[0]-40*mm, A4[1]-80*mm, id='first_frame')
    later_frame = Frame(20*mm, 20*mm, A4[0]-40*mm, A4[1]-40*mm, id='later_frame')

    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=20*mm, leftMargin=20*mm,
                             topMargin=20*mm, bottomMargin=20*mm)

    doc.addPageTemplates([
        PageTemplate(id='First', frames=[first_frame],
                     onPage=lambda canvas, doc: first_page_header(canvas, doc, stop_info, stop_code, qr_buffer, kuupaev)),
        PageTemplate(id='Later', frames=[later_frame],
                     onPage=lambda canvas, doc: later_pages_header(canvas, doc, stop_info, kuupaev))
    ])

    table_data = [["Väljumine", "Liini nr", "Liini nimetus", "Liini informatsioon"]]

    para_style = ParagraphStyle(
        name='Normal_wrap',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        wordWrap='CJK',
        splitLongWords=True,
        allowWidows=1,
        allowOrphans=1
    )

    center_style = ParagraphStyle(
        name='Center',
        parent=para_style,
        alignment=1
    )

    for idx, row in poster_df.iterrows():
        liini_info_text = str(row['Liini info']) if pd.notna(row['Liini info']) else ""
        liini_info = f"<b>{row['Liin on käigus']}</b><br/>{liini_info_text.replace('<br>', '<br />')}"
        table_data.append([
            Paragraph(str(row["Väljumine"]), center_style),
            Paragraph(str(row["Liini nr"]), center_style),
            Paragraph(smart_wrap_text(str(row["Liini nimetus"]), max_length=35), para_style),
            Paragraph(liini_info, para_style)
        ])

    table = Table(table_data, repeatRows=1, colWidths=[20*mm, 20*mm, 65*mm, 65*mm])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def gtfs_view():
    st.title("🚏 Ühistranspordi peatuse info")

    stops, stop_times, trips, routes, calendar = load_gtfs_data(version=st.session_state["gtfs_version"])

    if stops is not None:
        def format_peatus(row):
            code = row.get("stop_code", "—")
            desc = row.get("stop_desc", "")
            desc = "" if pd.isna(desc) else desc
            return f"{row['stop_name']} ({code}{', ' + desc if desc else ''})"

        stops['peatus_valik'] = stops.apply(format_peatus, axis=1)
        peatus_dict = dict(zip(stops['peatus_valik'], stops['stop_id']))

        valitud_peatus_valik = st.selectbox("**Vali peatus**:", ["— Vali peatus —"] + list(peatus_dict.keys()))
        if valitud_peatus_valik == "— Vali peatus —":
            st.info("Palun vali peatus.")
            return

        stop_id = peatus_dict[valitud_peatus_valik]
        filtered_stops = stops[stops['stop_id'] == stop_id]

        if filtered_stops.empty:
            st.warning("Valitud peatus ei leitud andmetest.")
            return

        stop_info = filtered_stops.iloc[0]
        stop_code = stop_info.get("stop_code", "—")

        kuupaev = st.date_input("**Vali kuupäev, mis seisuga peatuse infot kuvatakse:**", value=date.today())
        kuupaev = pd.to_datetime(kuupaev)
        kuupaev_kuvana = kuupaev.strftime("%d.%m.%Y")
        nadal_algus = kuupaev - pd.to_timedelta(kuupaev.weekday(), unit='D')
        nadal_lopp = nadal_algus + pd.Timedelta(days=6)

        stop_code_url = stop_info.get("stop_code", "").replace(" ", "%20")
        qr_link = f"https://web.peatus.ee/pysakit/estonia%3A{stop_id}#{stop_code_url}"

        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown(f"### 📍 Peatus: **{stop_info['stop_name']}**")
            st.markdown(f"### 🔢 Stop Code: **{stop_code}**")
            st.markdown(f"### 📅 Kehtiv alates: **{kuupaev_kuvana}**")
        with cols[1]:
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=4, border=2)
            qr.add_data(qr_link)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            st.image(buffer.getvalue(), width=120)
            st.markdown(f"<a href='{qr_link}' target='_blank'>↗️ Ava link</a>", unsafe_allow_html=True)
            b64 = base64.b64encode(buffer.getvalue()).decode()
            href = f'<a href="data:image/png;base64,{b64}" download="qr_{stop_info["stop_name"]}.png">⬇️ Lae alla QR</a>'
            st.markdown(href, unsafe_allow_html=True)

        calendar['start_date'] = pd.to_datetime(calendar['start_date'], format='%Y%m%d')
        calendar['end_date'] = pd.to_datetime(calendar['end_date'], format='%Y%m%d')
        sobivad_teenused = calendar[
            (calendar['start_date'] <= nadal_lopp) &
            (calendar['end_date'] >= nadal_algus) &
            (
                (calendar['monday'] == 1) | (calendar['tuesday'] == 1) |
                (calendar['wednesday'] == 1) | (calendar['thursday'] == 1) |
                (calendar['friday'] == 1) | (calendar['saturday'] == 1) |
                (calendar['sunday'] == 1)
            )
        ]

        if sobivad_teenused.empty:
            st.warning("Sellel nädalal ei ole valitud peatuses väljumisi.")
            return

        sobivad_service_id = sobivad_teenused['service_id'].unique()
        relevant_times = stop_times[stop_times['stop_id'] == stop_id]
        enriched = relevant_times.merge(trips, on="trip_id")
        enriched = enriched[enriched['service_id'].isin(sobivad_service_id)]
        enriched = enriched.merge(routes, on="route_id").merge(calendar, on="service_id")
        enriched['departure_time'] = pd.to_datetime(enriched['departure_time'], format='%H:%M:%S', errors='coerce')
        enriched = enriched.sort_values(["departure_time", "route_short_name", "trip_long_name"])
        enriched['departure_time'] = enriched['departure_time'].dt.strftime('%H:%M')

        if enriched.empty:
            st.warning("Selle peatuse jaoks ei leitud väljumisi valitud nädala jooksul.")
            return

        weekday_columns = {
            "monday": "E", "tuesday": "T", "wednesday": "K",
            "thursday": "N", "friday": "R", "saturday": "L", "sunday": "P"
        }
        weekday_order = ["E", "T", "K", "N", "R", "L", "P"]

        output_rows = []
        for _, row in enriched.iterrows():
            weekdays = [abbr for day, abbr in weekday_columns.items() if row.get(day) == 1]
            liin_info = row['route_desc'] if pd.notna(row['route_desc']) else ""
            output_rows.append({
                "Väljumine": row['departure_time'],
                "Liini nr": f"'{row['route_short_name']}" if "-" in str(row['route_short_name']) else row['route_short_name'],
                "Liini nimetus": row['trip_long_name'],
                "Liin on käigus": weekdays,
                "Liini info": liin_info
            })

        # --- KOONDA SAMAD VÄLJUMISED
        poster_df = (
            pd.DataFrame(output_rows)
            .groupby(["Väljumine", "Liini nr", "Liini nimetus", "Liini info"], as_index=False)
            .agg({"Liin on käigus": lambda days: sorted(set(sum(days, [])), key=weekday_order.index)})
        )
        poster_df["Liin on käigus"] = poster_df["Liin on käigus"].apply(lambda days: ", ".join(days))
        poster_df = poster_df.sort_values(["Väljumine", "Liini nr", "Liini nimetus"]).reset_index(drop=True)
        
        # 🛠 Muuda veergude järjekorda ekraanil
        poster_df = poster_df[["Väljumine", "Liini nr", "Liini nimetus", "Liin on käigus", "Liini info"]]


        # --- Kuvamine
        st.subheader("📄 Väljumised")
        st.dataframe(poster_df, use_container_width=True, hide_index=True)

        # --- PDF allalaadimine
        pdf_buffer = generate_pdf(stop_info, stop_code, img, poster_df, kuupaev)
        st.download_button(
            "⬇️ Laadi poster PDF-na alla",
            data=pdf_buffer,
            file_name=f"poster_{stop_info['stop_name']}.pdf",
            mime="application/pdf"
        )

        # --- CSV allalaadimine UTF-8 kodeeringus
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, quoting=csv.QUOTE_ALL)
        csv_writer.writerow([f"Peatus: {stop_info['stop_name']}"])
        csv_writer.writerow([f"Stop Code: {stop_code}"])
        csv_writer.writerow([f"Kehtiv alates: {kuupaev_kuvana}"])
        csv_writer.writerow([])
        csv_writer.writerow(poster_df.columns.tolist())
        for row in poster_df.itertuples(index=False):
            csv_writer.writerow(list(row))

        st.download_button(
            "⬇️ Laadi poster CSV-na alla",
            data=csv_buffer.getvalue().encode("utf-8-sig"),
            file_name=f"poster_{stop_info['stop_name']}.csv",
            mime="text/csv"
        )

        # --- Kaart
        if 'stop_lat' in stop_info and 'stop_lon' in stop_info:
            st.subheader("🗺️ Peatuse asukoht kaardil")
            import folium
            from streamlit_folium import st_folium

            m = folium.Map(location=[stop_info['stop_lat'], stop_info['stop_lon']], zoom_start=15)
            folium.Marker(
                location=[stop_info['stop_lat'], stop_info['stop_lon']],
                popup=stop_info['stop_name'],
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)
            st_folium(m, height=400, width="100%")

    else:
        st.error("GTFS andmete laadimine ebaõnnestus.")