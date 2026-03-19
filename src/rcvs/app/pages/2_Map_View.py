import folium
import streamlit as st
from streamlit_folium import st_folium

from rcvs.app.components.auth import require_auth
from rcvs.app.components.data_loader import load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters
from rcvs.app.components.practice_detail import render_practice_detail

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

centre_lat = map_df["lat"].mean()
centre_lon = map_df["lon"].mean()

m = folium.Map(location=[centre_lat, centre_lon], zoom_start=10)

for _, row in map_df.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        tooltip=row["name"],
        icon=folium.Icon(color="blue", icon="plus-sign"),
    ).add_to(m)

map_data = st_folium(m, width=None, height=500, returned_objects=["last_object_clicked_tooltip"])

if map_data and map_data.get("last_object_clicked_tooltip"):
    clicked_name = map_data["last_object_clicked_tooltip"]
    match = map_df[map_df["name"] == clicked_name]

    if not match.empty:
        st.divider()
        render_practice_detail(match.iloc[0])
