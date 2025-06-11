import streamlit as st
import pandas as pd
import os

@st.cache_data(ttl=86400)
def load_routes_and_agencies():
    base_path = "gtfs_data"
    routes = pd.read_csv(os.path.join(base_path, "routes.txt"))
    agencies = pd.read_csv(os.path.join(base_path, "agency.txt"))
    return routes, agencies

def gtfs_view():
    st.title("🔗 Seosta competent_authority ja agency_name")

    routes, agencies = load_routes_and_agencies()

    if 'competent_authority' not in routes.columns:
        st.error("routes.txt ei sisalda veergu 'competent_authority'")
        return

    competent_options = sorted(routes['competent_authority'].dropna().unique())
    selected_authority = st.selectbox("**Vali competent_authority:**", ["— Vali —"] + competent_options)

    if selected_authority == "— Vali —":
        st.info("Palun vali competent_authority.")
        return

    # Leia vastavad agency_id-d
    related_agencies = routes[routes['competent_authority'] == selected_authority]['agency_id'].dropna().unique()

    # Leia agency_name-d
    matched_agencies = agencies[agencies['agency_id'].isin(related_agencies)]

    if matched_agencies.empty:
        st.warning("Antud authority jaoks ei leitud seotud agency_id vasteid agency.txt failis.")
        return

    st.subheader("🧾 Seotud agency_name väärtused:")
    st.dataframe(matched_agencies[['agency_id', 'agency_name']], use_container_width=True)

    st.download_button(
        label="⬇️ Laadi CSV alla",
        data=matched_agencies[['agency_id', 'agency_name']].to_csv(index=False),
        file_name=f"agency_names_{selected_authority}.csv",
        mime="text/csv"
    )
