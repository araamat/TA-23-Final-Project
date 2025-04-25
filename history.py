
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime
import toml

# Lokaalses serveris pean kasutama seda:
# secrets = toml.load("secrets.toml")

#Streamlit impordi puhul:
secrets = st.secrets

def show_history_view():
    st.title("📂 Avaandmete (GTFS) ajalugu")

    filter_text = st.text_input("🔍**Filtreeri failinime järgi** (gtfs_DDMMYYYY, kus  DD on päev, MM kuu ja YYYY aasta.)")

    with st.spinner("Laen GTFS-faile Google Drive'ist..."):
        files = list_gtfs_files_from_drive()
        if not files:
            st.warning("Ühtegi GTFS ajaloo faili ei leitud.")
            return

        # Filtreeri failid
        filtered_files = [f for f in sorted(files, key=lambda x: x['createdTime'], reverse=True)
                          if filter_text.lower() in f['name'].lower()]

        if not filtered_files:
            st.info("Filtreerimisele vastavaid faile ei leitud.")
            return

        # Leheküljestamine
        files_per_page = 10
        total_pages = (len(filtered_files) - 1) // files_per_page + 1

        page = st.number_input("Ühel leheküljel kuvatakse 10 faili", min_value=1, max_value=total_pages, step=1)

        start = (page - 1) * files_per_page
        end = start + files_per_page

        for f in filtered_files[start:end]:
            created = datetime.strptime(f['createdTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_date = created.strftime("%d.%m.%y")
            download_url = f"https://drive.google.com/uc?id={f['id']}&export=download"

            with st.expander(f"📁 {f['name']}"):
                st.markdown(f"""
**Loodud:** {formatted_date}  
[⬇️ Laadi alla]({download_url})
""", unsafe_allow_html=True)

def list_gtfs_files_from_drive():
    key_data = dict(secrets["gcp_service_account"])  # tee koopia!
    key_data["private_key"] = key_data["private_key"].replace("\\n", "\n")

    creds = service_account.Credentials.from_service_account_info(key_data)
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        q=f"'{secrets['folder_id']}' in parents and name contains 'gtfs_' and mimeType='application/zip'",
        pageSize=100,
        fields="files(id, name, createdTime)"
    ).execute()

    return results.get('files', [])

