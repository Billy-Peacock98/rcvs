# RCVS VetGDP Practice Finder

A tool to find, filter, and organise UK veterinary practices that offer the [VetGDP](https://www.rcvs.org.uk/lifelong-learning/vetgdp/) (Veterinary Graduate Development Programme) training programme.

Scrapes practice data from the [RCVS Find a Vet](https://findavet.rcvs.org.uk/find-a-vet-practice/) directory and presents it in a friendly web interface for browsing, filtering, and tracking contact progress.

**Live app:** https://rcvs-tracker.streamlit.app/

## Features

- **Full UK Coverage** — 2,439 VetGDP-approved practices scraped from the RCVS directory
- **Distance Filter** — Practices sorted by distance from Bookham, Surrey (default 25-mile radius, adjustable via slider)
- **Interactive Map** — Folium map with clickable pins; single-click a marker to see full practice details
- **Searchable Table** — Filterable dataframe with type-to-search practice selector for detailed views
- **Contact Tracker** — Single-practice view with auto-saving status and notes to Google Sheets, progress summary table, status counts at a glance
- **Export** — Download filtered results as CSV or Excel, including contact status and notes; filter by status for targeted exports (e.g. "Not Contacted" call lists)
- **Authentication** — Cookie-based login via streamlit-authenticator (optional, for deployed app)

## Quick Start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Launch the web app (uses pre-scraped UK data)
uv run streamlit run src/rcvs/app/main.py
```

## Re-scraping Data

```bash
# Scrape all UK VetGDP practices (~2,400+, takes ~80 minutes)
uv run rcvs-scrape --keyword uk --output-dir data/practices
```

The app auto-discovers all `*_vetgdp.json` files in `data/practices/`, so new regions appear in the region selector immediately.

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/) with [streamlit-folium](https://folium.streamlit.app/) for maps
- **Authentication**: [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator)
- **Scraping**: requests + BeautifulSoup
- **Data models**: Pydantic
- **Contact tracking**: Google Sheets (optional, with local fallback)

## Project Structure

```
src/rcvs/
├── scraper/        # RCVS website scraper (client, parsers, CLI)
├── geo/            # Postcode geocoding fallback
├── sheets/         # Google Sheets contact tracker integration
└── app/            # Streamlit web application
    ├── main.py     # Router (st.navigation + auth gate)
    ├── pages/      # Home, Table, Map, Contact Tracker, Export
    └── components/ # Shared filters, detail panel, data loading, auth
```

## Data

Pre-scraped data is included in `data/practices/`:

- **UK** — 2,439 VetGDP practices (90% with email, 94% with phone, 98% with coordinates)
