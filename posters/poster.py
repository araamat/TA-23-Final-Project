import zipfile
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from PIL import Image
import qrcode
from io import BytesIO

def load_gtfs(gtfs_zip):
    """Laeb GTFS andmed ZIP-failist ja tagastab vajalikud andmeframid."""
    
    # Laadige ZIP-fail sisse
    with zipfile.ZipFile(gtfs_zip, 'r') as z:
        # Otsige kõiki faile ZIP-arkiivis
        file_names = z.namelist()
        
        # Laadige vajalikud failid pandas DataFrame'idena
        stops = pd.read_csv(z.open('stops.txt'))
        routes = pd.read_csv(z.open('routes.txt'))
        trips = pd.read_csv(z.open('trips.txt'))
        stop_times = pd.read_csv(z.open('stop_times.txt'))
        calendar = pd.read_csv(z.open('calendar.txt'))
        
    return stops, routes, trips, stop_times, calendar

def generate_poster(gtfs_zip, stop_id, date, title, logo_path=None, extra_text=None, qr_url=None):
    """Genereerib peatuse postri."""
    stops, routes, trips, stop_times, calendar = load_gtfs(gtfs_zip)
    
    date = datetime.strptime(date, "%Y-%m-%d").date()
    
    # Leidke aktiivsed teenused sellel kuupäeval
    calendar['start_date'] = pd.to_datetime(calendar['start_date'], format='%Y%m%d').dt.date
    calendar['end_date'] = pd.to_datetime(calendar['end_date'], format='%Y%m%d').dt.date
    valid_services = calendar[(calendar['start_date'] <= date) & (calendar['end_date'] >= date)]['service_id']
    
    # Filtreeri tripid
    valid_trips = trips[trips['service_id'].isin(valid_services)]
    
    # Kontrollige, kas stop_id on olemas 'stops' DataFrame'is
    stop_info = stops[stops['stop_id'] == stop_id]
    
    if stop_info.empty:
        raise ValueError(f"Peatus ID {stop_id} ei leitud.")
    
    stop_info = stop_info.iloc[0]  # Kui peatuse ID on olemas, võtame esimese rea
    
    # Filtreeri peatuse väljumised
    stop_departures = stop_times[stop_times['stop_id'] == stop_id]
    print(f"Leitud väljumised peatuses {stop_id}:")
    print(stop_departures)  # Prindime kõik vastavad väljumised
    
    # Ühendage tripid ja marsuudid
    stop_departures = stop_departures.merge(valid_trips, on='trip_id', how='inner')
    stop_departures = stop_departures.merge(routes, on='route_id', how='inner')
    
    if stop_departures.empty:
        raise ValueError(f"Peatuses {stop_id} ei leitud väljumisi.")
    
    stop_departures.sort_values('departure_time', inplace=True)
    
    # Alustame postri loomist
    fig, ax = plt.subplots(figsize=(8, 12))
    ax.axis('off')
    
    y_pos = 1.0
    
    # Pealkiri
    ax.text(0.5, y_pos, title, fontsize=18, fontweight='bold', ha='center')
    y_pos -= 0.05
    
    # Logo
    if logo_path:
        logo = Image.open(logo_path)
        ax.imshow(logo, extent=[0.1, 0.3, y_pos - 0.1, y_pos], aspect='auto')
    
    y_pos -= 0.1
    
    # Väljumiste tabel
    for _, row in stop_departures.iterrows():
        ax.text(0.1, y_pos, row['departure_time'], fontsize=12)
        ax.text(0.3, y_pos, row['route_short_name'], fontsize=12, fontweight='bold')
        ax.text(0.5, y_pos, row['trip_long_name'], fontsize=12)
        ax.text(0.8, y_pos, row['route_desc'], fontsize=10, color='gray')
        y_pos -= 0.05
    
    # Lisatekst
    if extra_text:
        y_pos -= 0.1
        ax.text(0.5, y_pos, extra_text, fontsize=10, color='gray', ha='center')
    
    # QR kood
    if qr_url:
        y_pos -= 0.15
        qr = qrcode.make(qr_url)
        buf = BytesIO()
        qr.save(buf)
        buf.seek(0)
        qr_img = Image.open(buf)
        ax.imshow(qr_img, extent=[0.35, 0.65, y_pos - 0.1, y_pos], aspect='auto')
    
    plt.show()

# Näide kasutamisest
generate_poster("gtfs_data.zip", "92498", "2025-04-01", "Peatus: Kikati", 
                logo_path="logo.png", extra_text="Uuendatud sõiduplaanid", 
                qr_url="https://www.transport.ee")
