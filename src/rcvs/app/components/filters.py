from __future__ import annotations

import pandas as pd
import streamlit as st

from rcvs.app.components.data_loader import get_available_regions


def render_sidebar_filters(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Render sidebar filter widgets and return the filtered DataFrame.

    :param df: Full practice DataFrame

    :return: Filtered DataFrame based on user selections
    """
    st.sidebar.header("Filters")

    filtered = df.copy()

    if "distance_miles" in filtered.columns:
        max_distance = st.sidebar.slider(
            "Max distance from Bookham (miles)",
            min_value=5,
            max_value=200,
            value=25,
            step=5,
        )
        filtered = filtered[filtered["distance_miles"] <= max_distance]
        filtered = filtered.sort_values("distance_miles")

    search = st.sidebar.text_input("Search practices", placeholder="Name, address, postcode...")
    if search:
        search_lower = search.lower()
        mask = (
            filtered["name"].str.lower().str.contains(search_lower, na=False)
            | filtered["address"].str.lower().str.contains(search_lower, na=False)
            | filtered["postcode"].str.lower().str.contains(search_lower, na=False)
        )
        filtered = filtered[mask]

    if "animals_str" in filtered.columns:
        all_animals = set()
        for animals in df["animals_str"].dropna():
            for a in animals.split(", "):
                if a.strip():
                    all_animals.add(a.strip())

        if all_animals:
            selected_animals = st.sidebar.multiselect(
                "Animals treated",
                sorted(all_animals),
            )
            if selected_animals:
                mask = filtered["animals_str"].apply(
                    lambda x: all(a in str(x) for a in selected_animals)
                )
                filtered = filtered[mask]

    if "accreditations_str" in filtered.columns:
        all_accred = set()
        for acc in df["accreditations_str"].dropna():
            for a in acc.split(", "):
                if a.strip():
                    all_accred.add(a.strip())

        if all_accred:
            selected_accred = st.sidebar.multiselect(
                "Accreditation",
                sorted(all_accred),
            )
            if selected_accred:
                mask = filtered["accreditations_str"].apply(
                    lambda x: any(a in str(x) for a in selected_accred)
                )
                filtered = filtered[mask]

    col1, col2 = st.sidebar.columns(2)
    with col1:
        vn_only = st.checkbox("VN Training")
    with col2:
        ems_only = st.checkbox("EMS")

    if vn_only:
        filtered = filtered[filtered["has_vn_training"] == True]  # noqa: E712
    if ems_only:
        filtered = filtered[filtered["has_ems"] == True]  # noqa: E712

    return filtered


def render_region_selector() -> str | None:
    """
    Render region selector in the sidebar.

    :return: Selected region keyword, or None if no data available
    """
    regions = get_available_regions()

    if not regions:
        st.sidebar.warning("No practice data found. Run the scraper first.")
        return None

    region = st.sidebar.selectbox(
        "Region",
        regions,
        format_func=lambda r: r.upper() if len(r) <= 2 else r.title(),
    )

    return region
