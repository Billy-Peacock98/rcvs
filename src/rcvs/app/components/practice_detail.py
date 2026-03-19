from __future__ import annotations

import pandas as pd
import streamlit as st


def render_practice_detail(
    row: pd.Series
) -> None:
    """
    Render full details for a single practice.

    Displays address, contact info, animals, accreditation,
    staff list, and opening hours in a two-column layout.

    :param row: A single row from the practices DataFrame
    """
    st.subheader(row["name"])

    col1, col2 = st.columns(2)

    with col1:
        if pd.notna(row.get("distance_miles")):
            st.markdown(f"**Distance:** {row['distance_miles']:.1f} miles from Bookham")
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
