import io

import pandas as pd
import streamlit as st

from rcvs.app.components.data_loader import load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters

st.set_page_config(page_title="Export", page_icon="🐾", layout="wide")
st.title("Export Practices")

region = render_region_selector()
if not region:
    st.stop()

df = load_practices(region)
if df.empty:
    st.warning("No practices found.")
    st.stop()

filtered = render_sidebar_filters(df)

st.caption(f"Exporting {len(filtered)} practices")

all_columns = {
    "name": "Practice Name",
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
    default=["name", "address", "postcode", "phone", "email", "director", "animals_str"],
    format_func=lambda k: available[k],
)

if not selected:
    st.warning("Select at least one column.")
    st.stop()

export_df = filtered[selected].copy()
export_df.columns = [available[c] for c in selected]

st.dataframe(export_df, use_container_width=True, hide_index=True)

csv_data = export_df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv_data,
    file_name=f"{region}_vetgdp_practices.csv",
    mime="text/csv",
)

buffer = io.BytesIO()
export_df.to_excel(buffer, index=False, engine="openpyxl")
st.download_button(
    label="Download Excel",
    data=buffer.getvalue(),
    file_name=f"{region}_vetgdp_practices.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
