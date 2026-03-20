from pathlib import Path

import pandas as pd
import streamlit as st

from rcvs.app.components.data_loader import enrich_with_status, load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters
from rcvs.app.components.email_draft import render_email_draft
from rcvs.app.components.practice_detail import render_practice_detail
from rcvs.sheets.tracker import STATUSES, ContactTracker

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
    if "sheet_initialised" not in st.session_state:
        tracker.init_sheet(df["name"].tolist())
        st.session_state.sheet_initialised = True
    statuses = tracker.get_all_statuses()

filtered = render_sidebar_filters(df)
filtered = enrich_with_status(filtered, statuses)

# --- Status summary ---
status_counts = filtered["status"].value_counts()
summary_parts = []
for s in STATUSES:
    count = status_counts.get(s, 0)
    if count > 0 or s == "Not Contacted":
        summary_parts.append(f"**{s}:** {count}")
st.markdown(" / ".join(summary_parts))

# --- Practice selector ---
practice_names = filtered["name"].tolist()
selected = st.selectbox(
    "Select a practice",
    options=practice_names,
    index=None,
    placeholder="Search for a practice...",
)

if selected:
    row = filtered[filtered["name"] == selected].iloc[0]
    current_status = row.get("status", "Not Contacted")
    current_notes = row.get("notes", "")

    render_practice_detail(row)

    st.divider()

    def _save_status() -> None:
        """Auto-save callback for status or notes change."""
        new_status = st.session_state[f"tracker_status_{selected}"]
        new_notes = st.session_state[f"tracker_notes_{selected}"]
        if tracker.is_configured:
            tracker.update_status(selected, new_status, new_notes)
        else:
            st.session_state.local_statuses[selected] = {
                "status": new_status,
                "notes": new_notes,
                "last_updated": "",
            }

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "Status",
            STATUSES,
            index=STATUSES.index(current_status) if current_status in STATUSES else 0,
            key=f"tracker_status_{selected}",
            on_change=_save_status,
        )
    with col2:
        st.text_area(
            "Notes",
            value=current_notes,
            key=f"tracker_notes_{selected}",
            on_change=_save_status,
            placeholder="Add notes...",
            height=100,
        )

    st.divider()
    render_email_draft(row)

# --- Contacted practices summary ---
contacted = filtered[filtered["status"] != "Not Contacted"]
if not contacted.empty:
    st.divider()
    st.subheader(f"Contacted Practices ({len(contacted)})")

    display_cols = ["name", "status", "notes"]
    if "distance_miles" in contacted.columns:
        display_cols.insert(1, "distance_miles")

    st.dataframe(
        contacted[display_cols].sort_values("status"),
        column_config={
            "name": st.column_config.TextColumn("Practice", width="medium"),
            "distance_miles": st.column_config.NumberColumn("Distance (mi)", format="%.1f", width="small"),
            "status": st.column_config.TextColumn("Status", width="small"),
            "notes": st.column_config.TextColumn("Notes", width="large"),
        },
        use_container_width=True,
        hide_index=True,
    )
