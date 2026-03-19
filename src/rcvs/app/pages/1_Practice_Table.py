import streamlit as st

from rcvs.app.components.data_loader import load_practices
from rcvs.app.components.filters import render_region_selector, render_sidebar_filters

st.set_page_config(page_title="Practice Table", page_icon="🐾", layout="wide")
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
    "name", "address", "postcode", "phone", "email",
    "director", "vet_count", "nurse_count", "animals_str",
    "accreditations_str", "has_vn_training", "has_ems",
]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[display_cols],
    column_config={
        "name": st.column_config.TextColumn("Practice", width="medium"),
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
st.markdown("Click on a practice name to expand details.")

for _, row in filtered.iterrows():
    with st.expander(f"{row['name']} — {row.get('postcode', '')}"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Address:** {row.get('address', 'N/A')}")
            st.markdown(f"**Postcode:** {row.get('postcode', 'N/A')}")
            st.markdown(f"**Phone:** {row.get('phone', 'N/A')}")
            st.markdown(f"**Email:** {row.get('email', 'N/A')}")
            if row.get("website"):
                st.markdown(f"**Website:** [{row['website']}]({row['website']})")

        with col2:
            st.markdown(f"**Animals:** {row.get('animals_str', 'N/A')}")
            st.markdown(f"**Accreditation:** {row.get('accreditations_str', 'N/A')}")
            st.markdown(f"**VN Training:** {'Yes' if row.get('has_vn_training') else 'No'}")
            st.markdown(f"**EMS:** {'Yes' if row.get('has_ems') else 'No'}")

        if row.get("vets"):
            st.markdown("**Veterinary Surgeons:**")
            for vet in row["vets"]:
                role_str = f" ({vet['role']})" if vet.get("role") else ""
                quals_str = f" — {vet['qualifications']}" if vet.get("qualifications") else ""
                st.markdown(f"- {vet['name']}{quals_str}{role_str}")

        if row.get("hours") and isinstance(row["hours"], dict):
            st.markdown("**Opening Hours:**")
            for day, time_str in row["hours"].items():
                st.markdown(f"- {day}: {time_str}")
