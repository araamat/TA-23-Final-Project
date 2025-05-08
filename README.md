# GTFS Viewer & Validator

## 📌 Projekti eesmärk
See tööriist on loodud GTFS-andmestiku visualiseerimiseks, filtreerimiseks ja andmekvaliteedi kontrolliks Eesti ühistranspordi kontekstis. Lahendus võimaldab mugavalt uurida sõiduplaane, liine, peatuseid ning genereerida plakateid koos QR-koodidega.

Tööriist on mõeldud kasutamiseks ühistranspordi osakonna töötajatele, ühistranspordi planeerijatele ning tehniliselt teadlikele kasutajatele, kes soovivad andmeid efektiivselt analüüsida.

## 🔧 Kasutatud tehnoloogiad
- **Python 3.11**
- [Streamlit](https://streamlit.io) – kasutajaliidese loomiseks
- [Pandas](https://pandas.pydata.org) – andmetöötluseks
- [Folium](https://python-visualization.github.io/folium/) – interaktiivsete kaartide loomiseks
- [Google Drive API](https://developers.google.com/drive) – andmefailide halduseks
- [QRCode](https://pypi.org/project/qrcode/) ja [ReportLab](https://www.reportlab.com/) – PDF plakatite genereerimiseks

## 📁 Projekti struktuur
```plaintext
├── index.py                 # Avaleht, juhib vaateid
├── route.py                # Route ID ja liini info
├── trip.py                 # Trip ID ja sõidu peatuste info
├── search_by_line.py       # Liini numbri otsing
├── search_by_stop_pair.py  # Kahe peatuse vaheline ühendus
├── stopPoster.py           # PDF plakati ja QR-koodi genereerija
├── authority.py            # Peatuste filtreerimine haldaja järgi
├── history.py              # Ajalooliste GTFS-andmete haldus
├── requirements.txt        # Vajalikud paketid
```

## 🚀 Funktsionaalsus
- ✅ GTFS ZIP-faili laadimine ja avamine
- ✅ Liinide, sõitude ja peatuste filtreerimine (nt `route_id`, `trip_id`, liininumber)
- ✅ Interaktiivne kaart (Folium)
- ✅ Ajalooliste GTFS-failide sirvimine ja haldus
- ✅ PDF-plakati ja QR-koodi loomine peatusinfo põhjal
- ✅ Andmestiku kontroll (nt stop_area vead)

## 📈 Automatiseeritud töövoog
GitHub Actions töövoog `upload_gtfs.yml`:
- Käivitatakse iga päev kell 03:00 UTC, kuid saab ka manuaalselt vajadusel uuendada
- Laadib värske GTFS-faili Peatus.ee lehelt
- Laeb selle Google Drive’i määratud kausta
- Failile määratakse automaatselt kuupäevaga nimi

## 📄 Kasutus
1. Klona projekt:
```bash
git clone https://github.com/SINU_KASUTAJA/gtfs-viewer.git
```

2. Installi sõltuvused:
```bash
pip install -r requirements.txt
```

3. Käivita Streamlit:
```bash
streamlit run index.py
```

## 🔒 Autentimine
- **Google Drive API võtmed** peavad olema seadistatud failis `secrets.toml`
- Teenusekonto peab omama kirjutusõigust Drive’i kausta

## 📬 Kontakt
Autor: **Andrus Raamat**  
Kuressaare Ametikool – Tarkvaraarendaja lõputöö 2025  
Email: [raamatandrus@gmail.com](mailto:raamatandrus@gmail.com)

## 📃 Litsents
Projekt on avatud lähtekoodiga ja kasutatav MIT-litsentsi alusel.
