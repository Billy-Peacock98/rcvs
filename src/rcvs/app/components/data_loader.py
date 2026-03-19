from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "practices"


@st.cache_data
def get_available_regions() -> list[str]:
    """
    Discover available regions from JSON files in the data directory.

    Looks for files matching {keyword}_vetgdp.json.

    :return: List of region keywords
    """
    if not DATA_DIR.exists():
        return []

    regions = []
    for f in sorted(DATA_DIR.glob("*_vetgdp.json")):
        keyword = f.stem.replace("_vetgdp", "")
        regions.append(keyword)

    return regions


@st.cache_data
def load_practices(
    region: str
) -> pd.DataFrame:
    """
    Load scraped practice data from JSON into a DataFrame.

    :param region: Region keyword (e.g. 'surrey')

    :return: DataFrame of practices
    """
    json_path = DATA_DIR / f"{region}_vetgdp.json"

    if not json_path.exists():
        logger.warning("No data file found for region: {}", region)
        return pd.DataFrame()

    with open(json_path) as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    if "vets" in df.columns:
        df["vet_count"] = df["vets"].apply(len)
        df["nurse_count"] = df["nurses"].apply(len)
        df["vet_names"] = df["vets"].apply(
            lambda vs: ", ".join(v["name"] for v in vs) if vs else ""
        )
        df["director"] = df["vets"].apply(_find_director)
    else:
        df["vet_count"] = 0
        df["nurse_count"] = 0
        df["vet_names"] = ""
        df["director"] = ""

    if "animals" in df.columns:
        df["animals_str"] = df["animals"].apply(
            lambda a: ", ".join(a) if isinstance(a, list) else str(a)
        )
    else:
        df["animals_str"] = ""

    if "accreditations" in df.columns:
        df["accreditations_str"] = df["accreditations"].apply(
            lambda a: ", ".join(a) if isinstance(a, list) else str(a)
        )
    else:
        df["accreditations_str"] = ""

    if "lat" in df.columns and "lng" in df.columns:
        df["lon"] = df["lng"]

    if df["lat"].isna().any() or df["lon"].isna().any():
        from rcvs.geo.postcodes import PostcodeLookup
        lookup = PostcodeLookup()
        df = lookup.enrich_dataframe(df)

    return df


def _find_director(
    vets: list[dict]
) -> str:
    """
    Find the director or principal from a list of vets.

    :param vets: List of vet dictionaries

    :return: Name and role of the director/principal, or first vet
    """
    if not vets:
        return ""

    for vet in vets:
        role = vet.get("role", "").lower()
        if role in ("director", "principal", "partner"):
            return f"{vet['name']} ({vet.get('role', '')})"

    return vets[0]["name"]


def enrich_with_status(
    df: pd.DataFrame,
    statuses: dict[str, dict]
) -> pd.DataFrame:
    """
    Merge contact tracking statuses into the practice DataFrame.

    :param df: Practice DataFrame
    :param statuses: Status data from ContactTracker.get_all_statuses()

    :return: DataFrame with status and notes columns added
    """
    if not statuses:
        df["status"] = "Not Contacted"
        df["notes"] = ""
        return df

    df["status"] = df["name"].map(
        lambda n: statuses.get(n, {}).get("status", "Not Contacted")
    )
    df["notes"] = df["name"].map(
        lambda n: statuses.get(n, {}).get("notes", "")
    )

    return df
