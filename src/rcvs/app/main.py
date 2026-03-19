from pathlib import Path

import streamlit as st

from rcvs.app.components.auth import build_login_page, is_authenticated, render_logout

PAGES_DIR = Path(__file__).parent / "pages"

st.set_page_config(
    page_title="VetGDP Practice Finder",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not is_authenticated():
    login_page = st.Page(build_login_page, title="Login", icon="🔒")
    pg = st.navigation([login_page])
else:
    render_logout()
    pages = [
        st.Page(PAGES_DIR / "0_Home.py", title="Home", icon="🏠", default=True),
        st.Page(PAGES_DIR / "1_Practice_Table.py", title="Practice Table", icon="📋"),
        st.Page(PAGES_DIR / "2_Map_View.py", title="Map View", icon="🗺️"),
        st.Page(PAGES_DIR / "3_Contact_Tracker.py", title="Contact Tracker", icon="📞"),
        st.Page(PAGES_DIR / "4_Export.py", title="Export", icon="📥"),
    ]
    pg = st.navigation(pages)

pg.run()
