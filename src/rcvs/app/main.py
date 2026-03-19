from pathlib import Path

import streamlit as st

from rcvs.app.components.auth import require_auth

PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(
    page_title="VetGDP Practice Finder",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()

pages = [
    st.Page(PAGES_DIR / "0_Home.py", title="Home", icon="🏠", default=True),
    st.Page(PAGES_DIR / "1_Practice_Table.py", title="Practice Table", icon="📋"),
    st.Page(PAGES_DIR / "2_Map_View.py", title="Map View", icon="🗺️"),
    st.Page(PAGES_DIR / "3_Contact_Tracker.py", title="Contact Tracker", icon="📞"),
    st.Page(PAGES_DIR / "4_Export.py", title="Export", icon="📥"),
]

pg = st.navigation(pages)
pg.run()
