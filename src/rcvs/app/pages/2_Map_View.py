import streamlit as st

from rcvs.app.components.auth import require_auth
from rcvs.app.components.data_loader import load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters

st.set_page_config(page_title="Map View", page_icon="🐾", layout="wide")
require_auth()
st.title("Map View")

region = render_region_selector()
if not region:
    st.stop()

df = load_practices(region)
if df.empty:
    st.warning("No practices found for this region.")
    st.stop()

filtered = render_sidebar_filters(df)

map_df = filtered.dropna(subset=["lat", "lon"])

if map_df.empty:
    st.warning("No practices with coordinates to display on the map.")
    st.stop()

st.caption(f"Showing {len(map_df)} practices on map")

st.map(map_df, latitude="lat", longitude="lon", size=40)

st.subheader("Mapped Practices")
st.dataframe(
    map_df[["name", "address", "postcode", "phone", "lat", "lon"]],
    column_config={
        "name": "Practice",
        "address": "Address",
        "postcode": "Postcode",
        "phone": "Phone",
        "lat": st.column_config.NumberColumn("Latitude", format="%.5f"),
        "lon": st.column_config.NumberColumn("Longitude", format="%.5f"),
    },
    use_container_width=True,
    hide_index=True,
)
