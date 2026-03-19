# RCVS VetGDP Practice Finder

A tool to find, filter, and organise UK veterinary practices that offer the [VetGDP](https://www.rcvs.org.uk/lifelong-learning/vetgdp/) (Veterinary Graduate Development Programme) training programme.

Scrapes practice data from the [RCVS Find a Vet](https://findavet.rcvs.org.uk/find-a-vet-practice/) directory and presents it in a friendly web interface for browsing, filtering, and tracking contact progress.

**Live app:** https://rcvs-tracker.streamlit.app/

## Features

- **Scraper** — Extracts practice details (contact info, staff, opening hours, animals treated, accreditations) from the RCVS website with rate limiting and retry logic
- **Interactive Table** — Searchable, filterable list of practices with expandable detail rows
- **Map View** — Pinpoints practices on a map using coordinates from RCVS
- **Contact Tracker** — Track which practices you've contacted, with optional Google Sheets sync
- **Export** — Download filtered results as CSV or Excel

## Quick Start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Launch the web app (uses pre-scraped data)
uv run streamlit run src/rcvs/app/main.py
```

## Scraping New Regions

```bash
# Scrape practices for a region
uv run rcvs-scrape --keyword surrey --output-dir data/practices

# Scrape a different region
uv run rcvs-scrape --keyword hampshire --output-dir data/practices
```

The app auto-discovers all `*_vetgdp.json` files in `data/practices/`, so new regions appear in the region selector immediately.

## Tech Stack

- **Frontend**: [Streamlit](https://streamlit.io/)
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
    ├── main.py
    ├── pages/      # Table, Map, Contact Tracker, Export
    └── components/ # Shared filters and data loading
```

## Data

Pre-scraped data is included in `data/practices/`. Currently available:

- **Surrey** — 71 VetGDP practices (94% with email/phone, 100% with coordinates)
