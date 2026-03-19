from pathlib import Path

import pandas as pd
import streamlit as st

from rcvs.app.components.auth import require_auth
from rcvs.app.components.data_loader import enrich_with_status, load_practices
from rcvs.app.components.filters import render_region_selector
from rcvs.sheets.tracker import STATUSES, ContactTracker

st.set_page_config(page_title="Contact Tracker", page_icon="🐾", layout="wide")
require_auth()
st.title("Contact Tracker")

region = render_region_selector()
if not region:
    st.stop()

df = load_practices(region)
if df.empty:
    st.warning("No practices found.")
    st.stop()

creds_dict = None
creds_path = None

if "gcp_service_account" in st.secrets:
    creds_dict = dict(st.secrets["gcp_service_account"])
else:
    _path = Path("service-account.json")
    if _path.exists():
        creds_path = _path

tracker = ContactTracker(credentials_path=creds_path, credentials_dict=creds_dict)

if not tracker.is_configured:
    st.info("Google Sheets is not configured. Contact tracking is in local-only mode.")
    st.markdown(
        """
        ### Setup Google Sheets Integration

        To enable persistent contact tracking:

        1. Create a Google Cloud project (free)
        2. Enable the Google Sheets API and Google Drive API
        3. Create a service account and download the JSON key
        4. Save the key as `service-account.json` in the project root
        5. Share a Google Sheet named **"VetGDP Contact Tracker"** with the service account email

        Without this, statuses will reset when the app restarts.
        """
    )

    if "local_statuses" not in st.session_state:
        st.session_state.local_statuses = {}

    statuses = st.session_state.local_statuses
else:
    statuses = tracker.get_all_statuses()

df = enrich_with_status(df, statuses)

st.caption(f"{len(df)} practices in {region.title()}")

status_filter = st.multiselect("Filter by status", STATUSES)
if status_filter:
    df = df[df["status"].isin(status_filter)]

for idx, row in df.iterrows():
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])

        with col1:
            st.markdown(f"**{row['name']}**")
            st.caption(f"{row.get('phone', '')} | {row.get('email', '')}")

        with col2:
            current_status = row.get("status", "Not Contacted")
            new_status = st.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(current_status) if current_status in STATUSES else 0,
                key=f"status_{idx}",
                label_visibility="collapsed",
            )

        with col3:
            notes = st.text_input(
                "Notes",
                value=row.get("notes", ""),
                key=f"notes_{idx}",
                label_visibility="collapsed",
                placeholder="Notes...",
            )

        with col4:
            if st.button("Save", key=f"save_{idx}"):
                if tracker.is_configured:
                    tracker.update_status(row["name"], new_status, notes)
                    st.success(f"Saved: {row['name']}")
                else:
                    st.session_state.local_statuses[row["name"]] = {
                        "status": new_status,
                        "notes": notes,
                        "last_updated": "",
                    }
                    st.success(f"Saved locally: {row['name']}")
                st.rerun()

        st.divider()
