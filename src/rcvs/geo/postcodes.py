from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd
from loguru import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "postcodes"
OUTCODES_FILE = DATA_DIR / "outcodes.csv"


class PostcodeLookup:
    """
    Maps UK outcode prefixes (e.g. 'GU26') to approximate lat/lng coordinates.

    Uses a small CSV file (~82KB, ~3K rows) committed to the repository.
    """

    def __init__(
        self,
        csv_path: Path = OUTCODES_FILE
    ) -> None:
        """
        Load the outcode lookup table.

        :param csv_path: Path to the outcodes CSV file
        """
        self._lookup: dict[str, tuple[float, float]] = {}

        if not csv_path.exists():
            logger.warning("Outcodes CSV not found at {}", csv_path)
            return

        with open(csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                outcode = row.get("outcode", row.get("postcode", "")).strip().upper()
                try:
                    lat = float(row["latitude"])
                    lng = float(row["longitude"])
                    self._lookup[outcode] = (lat, lng)
                except (ValueError, KeyError):
                    continue

        logger.info("Loaded {} outcode lookups", len(self._lookup))

    @staticmethod
    def _extract_outcode(
        postcode: str
    ) -> str:
        """
        Extract the outcode prefix from a UK postcode.

        E.g. 'GU26 6HJ' -> 'GU26', 'SW1A 1AA' -> 'SW1A'

        :param postcode: Full UK postcode

        :return: Outcode prefix (uppercase)
        """
        parts = postcode.strip().upper().split()
        return parts[0] if parts else ""

    def lookup(
        self,
        postcode: str
    ) -> tuple[float, float] | None:
        """
        Look up approximate coordinates for a postcode.

        :param postcode: Full UK postcode (e.g. 'GU26 6HJ')

        :return: (latitude, longitude) tuple, or None if not found
        """
        outcode = self._extract_outcode(postcode)
        return self._lookup.get(outcode)

    def enrich_dataframe(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Add lat/lon columns to a DataFrame using postcode lookups.

        Only fills in coordinates where they are currently missing.

        :param df: DataFrame with a 'postcode' column

        :return: DataFrame with 'lat' and 'lon' columns added/updated
        """
        if "postcode" not in df.columns:
            return df

        if "lat" not in df.columns:
            df["lat"] = None
        if "lon" not in df.columns:
            df["lon"] = None

        for idx, row in df.iterrows():
            if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
                continue

            coords = self.lookup(str(row.get("postcode", "")))
            if coords:
                df.at[idx, "lat"] = coords[0]
                df.at[idx, "lon"] = coords[1]

        return df
