import streamlit as st

from rcvs.app.components.data_loader import load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters
from rcvs.app.components.practice_detail import render_practice_detail

st.title("Practice Table")

region = render_region_selector()
if not region:
    st.stop()

df = load_practices(region)
if df.empty:
    st.warning("No practices found for this region.")
    st.stop()

filtered = render_sidebar_filters(df)

st.caption(f"Showing {len(filtered)} of {len(df)} practices in {region.title()}")

display_cols = [
    "name", "distance_miles", "address", "postcode", "phone", "email",
    "director", "vet_count", "nurse_count", "animals_str",
    "accreditations_str", "has_vn_training", "has_ems",
]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[display_cols],
    column_config={
        "name": st.column_config.TextColumn("Practice", width="medium"),
        "distance_miles": st.column_config.NumberColumn("Distance (mi)", format="%.1f", width="small"),
        "address": st.column_config.TextColumn("Address", width="medium"),
        "postcode": st.column_config.TextColumn("Postcode", width="small"),
        "phone": st.column_config.TextColumn("Phone", width="small"),
        "email": st.column_config.TextColumn("Email", width="medium"),
        "director": st.column_config.TextColumn("Director/Principal", width="medium"),
        "vet_count": st.column_config.NumberColumn("Vets", width="small"),
        "nurse_count": st.column_config.NumberColumn("Nurses", width="small"),
        "animals_str": st.column_config.TextColumn("Animals", width="medium"),
        "accreditations_str": st.column_config.TextColumn("Accreditation", width="medium"),
        "has_vn_training": st.column_config.CheckboxColumn("VN Training", width="small"),
        "has_ems": st.column_config.CheckboxColumn("EMS", width="small"),
    },
    use_container_width=True,
    hide_index=True,
)

st.subheader("Practice Details")

practice_names = filtered["name"].tolist()
selected = st.selectbox(
    "Select a practice",
    options=practice_names,
    index=None,
    placeholder="Search for a practice...",
)

if selected:
    row = filtered[filtered["name"] == selected].iloc[0]
    render_practice_detail(row)
