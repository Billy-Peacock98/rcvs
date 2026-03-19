import streamlit as st

from rcvs.app.components.auth import require_auth

st.set_page_config(
    page_title="Home",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

require_auth()

st.title("VetGDP Practice Finder")
st.markdown(
    "Find, filter, and track UK veterinary practices offering the "
    "**Veterinary Graduate Development Programme (VetGDP)**."
)
st.markdown("Use the sidebar to navigate between pages.")

st.sidebar.success("Select a page above.")
