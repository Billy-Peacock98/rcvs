import io
from pathlib import Path

import pandas as pd
import streamlit as st

from rcvs.app.components.data_loader import enrich_with_status, load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters
from rcvs.sheets.tracker import STATUSES, ContactTracker

st.title("Export Practices")

region = render_region_selector()
if not region:
    st.stop()

df = load_practices(region)
if df.empty:
    st.warning("No practices found.")
    st.stop()

# Load contact statuses
creds_dict = None
creds_path = None

try:
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
except Exception:
    pass

if creds_dict is None:
    _path = Path("service-account.json")
    if _path.exists():
        creds_path = _path

tracker = ContactTracker(credentials_path=creds_path, credentials_dict=creds_dict)

if tracker.is_configured:
    statuses = tracker.get_all_statuses()
else:
    statuses = st.session_state.get("local_statuses", {})

df = enrich_with_status(df, statuses)

filtered = render_sidebar_filters(df)

# Status filter
status_filter = st.multiselect("Filter by contact status", STATUSES)
if status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]

st.caption(f"Exporting {len(filtered)} practices")

all_columns = {
    "name": "Practice Name",
    "distance_miles": "Distance (miles)",
    "status": "Contact Status",
    "notes": "Notes",
    "address": "Address",
    "postcode": "Postcode",
    "phone": "Phone",
    "email": "Email",
    "website": "Website",
    "director": "Director/Principal",
    "vet_count": "Number of Vets",
    "nurse_count": "Number of Nurses",
    "vet_names": "Vet Names",
    "animals_str": "Animals Treated",
    "accreditations_str": "Accreditation",
    "has_vn_training": "VN Training",
    "has_ems": "EMS",
    "lat": "Latitude",
    "lon": "Longitude",
}

available = {k: v for k, v in all_columns.items() if k in filtered.columns}

selected = st.multiselect(
    "Select columns to export",
    list(available.keys()),
    default=[
        c for c in [
            "name", "distance_miles", "status", "notes",
            "address", "postcode", "phone", "email", "director",
        ] if c in available
    ],
    format_func=lambda k: available[k],
)

if not selected:
    st.warning("Select at least one column.")
    st.stop()

export_df = filtered[selected].copy()

# Round distance for cleaner export
if "distance_miles" in selected:
    export_df["distance_miles"] = export_df["distance_miles"].round(1)

export_df.columns = [available[c] for c in selected]

st.dataframe(export_df, use_container_width=True, hide_index=True)

col1, col2 = st.columns(2)
with col1:
    csv_data = export_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"{region}_vetgdp_practices.csv",
        mime="text/csv",
    )
with col2:
    buffer = io.BytesIO()
    export_df.to_excel(buffer, index=False, engine="openpyxl")
    st.download_button(
        label="Download Excel",
        data=buffer.getvalue(),
        file_name=f"{region}_vetgdp_practices.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
