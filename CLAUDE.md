# RCVS VetGDP Practice Finder

## Project Overview

A tool to find, filter, and organise UK veterinary practices that offer the VetGDP (Veterinary Graduate Development Programme) training programme. The goal is to create a pipeline that:

1. **Scrapes** all VetGDP-approved practices from the RCVS Find a Vet directory (UK-wide)
2. **Filters** by distance from Bookham, Surrey (default 25 miles) plus animal type, accreditation, etc.
3. **Processes** practice data (contact details, location, distance calculation, etc.)
4. **Outputs** organised, actionable lists for contacting practices about job opportunities

Source: https://findavet.rcvs.org.uk/find-a-vet-practice/?filter-keyword=&filter-vetgdp=true&filter-searchtype=practice

## Current Status (2026-03-19)

**All 6 build phases are complete. App is deployed to Streamlit Community Cloud.**

- **Live app:** https://rcvs-tracker.streamlit.app/
- **Hosted on:** Streamlit Community Cloud (free tier, deploys from `main` branch)
- Full UK scrape complete (2,439 VetGDP practices)
- 5 Streamlit pages: Home, Practice Table, Map View, Contact Tracker, Export
- Distance filter centred on Bookham, Surrey (default 25 miles, ~257 practices)
- Interactive folium map with single-click practice details
- Searchable practice selectbox replaces expander list (scales to thousands)
- `st.navigation` API for custom sidebar labels
- Authentication via `streamlit-authenticator` with graceful fallback
- Contact Tracker supports `st.secrets` for Cloud credentials and falls back to local-only mode

### Data Quality — UK Scrape

| Metric | Value |
|--------|-------|
| Total practices | 2,439 |
| With email | 2,198 (90%) |
| With phone | 2,306 (94%) |
| With website | 2,103 (86%) |
| With coordinates | 2,411 (98%) |
| Within 25mi of Bookham | ~257 |

### How to Run

```bash
# Scrape all UK VetGDP practices (already done — 2,439 practices)
uv run rcvs-scrape --keyword uk --output-dir data/practices

# Launch the Streamlit app locally
uv run streamlit run src/rcvs/app/main.py
```

### Deployment

The app is deployed to **Streamlit Community Cloud** from the `main` branch.

- **URL:** https://rcvs-tracker.streamlit.app/
- **Main file:** `src/rcvs/app/main.py`
- **Dependencies:** Resolved via `uv.lock` (Community Cloud auto-detects this)
- **Secrets:** Auth and Google Sheets credentials are configured via Streamlit's Secrets Management (`st.secrets["auth"]`, `st.secrets["gcp_service_account"]`), not committed to the repo

## Documentation

Technical documentation lives in `docs/`. **These documents MUST be kept up to date at ALL times** — whenever new information is discovered about the RCVS website, scraping behaviour, data structures, or any other technical detail, update the relevant doc immediately.

- `docs/rcvs_website_technical_reference.md` — detailed breakdown of the RCVS Find a Vet website: URL structure, query parameters, pagination, HTML structure for both list and detail pages, CSS selectors used by parsers, CloudFlare email decoding, data completeness stats, and known quirks

## Architecture

### Folder Structure

```
rcvs/
├── pyproject.toml              # Dependencies, CLI entry point, build config
├── CLAUDE.md                   # This file — project overview and standards
├── .gitignore
├── docs/
│   └── rcvs_website_technical_reference.md
├── data/
│   ├── postcodes/
│   │   └── outcodes.csv        # Outcode-level lat/lng (~533 rows, South East)
│   └── practices/
│       └── uk_vetgdp.json      # Scraped data (2,439 UK practices, committed to repo)
└── src/
    └── rcvs/
        ├── __init__.py
        ├── scraper/
        │   ├── __init__.py
        │   ├── models.py       # Pydantic: Practice, StaffMember
        │   ├── client.py       # RCVSClient: rate-limited HTTP with retry
        │   ├── list_parser.py  # Parse search result pages + map markers
        │   ├── detail_parser.py # Parse practice detail pages + CF email decode
        │   └── run.py          # CLI entry point: orchestrates full scrape
        ├── geo/
        │   ├── __init__.py
        │   └── postcodes.py    # PostcodeLookup: outcode CSV → lat/lng fallback
        ├── sheets/
        │   ├── __init__.py
        │   └── tracker.py      # Google Sheets contact status read/write
        └── app/
            ├── __init__.py
            ├── main.py         # Router: st.navigation, auth gate, page definitions
            ├── pages/
            │   ├── 0_Home.py             # Landing page
            │   ├── 1_Practice_Table.py   # Searchable table + selectbox detail view
            │   ├── 2_Map_View.py         # Interactive folium map with click-to-detail
            │   ├── 3_Contact_Tracker.py  # Status tracking (Sheets or local)
            │   └── 4_Export.py           # CSV/Excel download
            └── components/
                ├── __init__.py
                ├── auth.py         # Authentication (streamlit-authenticator, cached instance)
                ├── filters.py      # Sidebar filters: distance slider, search, animals, etc.
                ├── practice_detail.py # Shared practice detail rendering (used by Table + Map)
                └── data_loader.py  # Load JSON, enrich with geo/distance + computed columns
```

### Key Design Decisions

- **Coordinates from RCVS map markers**: The list page embeds `gmap-marker` divs with exact lat/lng for each practice. This is far more accurate than outcode-level geocoding and costs zero extra requests. The outcode CSV (`data/postcodes/outcodes.csv`) is only a fallback for the rare case where a practice's map marker is missing.
- **Distance-based filtering**: All practices have a pre-computed haversine distance from Bookham, Surrey (51.283, -0.373). The sidebar slider defaults to 25 miles, reducing ~2,400 practices to ~257. Results are sorted nearest-first.
- **CloudFlare email decoding**: All emails on the RCVS site are obfuscated with CF's XOR cipher. The scraper decodes them from the `data-cfemail` hex attribute.
- **Scraper separate from app**: Data is committed to the repo as JSON. The Streamlit app never hits the RCVS website — it reads from local files. This decouples scraping from the user experience.
- **st.navigation for routing**: `main.py` is the single router using `st.Page`/`st.navigation`. This allows custom sidebar labels and centralises auth. Page files contain only their content logic.
- **Cached authenticator**: The `stauth.Authenticate` instance is stored in `st.session_state` to avoid duplicate `CookieManager` components per script run.
- **Google Sheets tracker with graceful fallback**: Credentials are loaded from `st.secrets` (for Cloud) or a local `service-account.json` file. When neither is present, the Contact Tracker falls back to session-only local state.
- **Interactive folium map**: `folium.Marker` with tooltips rendered via `streamlit-folium`. Single-click on a pin shows full practice details below the map. `last_object_clicked_tooltip` identifies the clicked practice by name.
- **Multi-region via convention**: `data/practices/{keyword}_vetgdp.json` files are auto-discovered by the app's region selector.

### Data Flow

```
RCVS Website → scraper/run.py → data/practices/{keyword}_vetgdp.json
                                              ↓
                                    app/components/data_loader.py
                                    (+ geo/postcodes.py fallback)
                                              ↓
                                    Streamlit pages (table, map, tracker, export)
                                              ↓
                                    Google Sheets (optional, for contact tracking)
```

## Target User

The end user is **non-technical** — they will not interact with code, the terminal, or config files. All interaction happens through a Streamlit web UI. Keep the interface simple, clear, and self-explanatory.

## Constraints

- **Zero cost** — no paid infrastructure, APIs, or services. Everything must use free tiers or open-source tools.
- **All dependencies** must be added to `pyproject.toml` (not installed ad-hoc via pip). Use `uv` to manage.

## Tech Stack

- Python 3.11+
- Managed with `uv` (pyproject.toml)
- **Frontend**: Streamlit (free hosting via Streamlit Community Cloud)
- **Authentication**: `streamlit-authenticator` (cookie-based, bcrypt passwords)
- **Scraping**: requests + BeautifulSoup (lxml parser)
- **Data models**: Pydantic
- **Logging**: `loguru`
- **Data handling**: `pandas`
- **Contact tracking**: `gspread` + `google-auth` (optional)
- **Map**: `folium` + `streamlit-folium`

## Dependencies

All in `pyproject.toml`:
```
streamlit, streamlit-authenticator, pandas, loguru, requests, beautifulsoup4, lxml, pydantic, gspread, google-auth, openpyxl, folium, streamlit-folium
```

CLI entry point: `rcvs-scrape = "rcvs.scraper.run:main"`

## Coding Standards

### Function Formatting

All functions must follow this exact style:

```python
def function_name(
    self,
    param1: str,
    param2: int,
    optional_param: bool = True
) -> ReturnType:
    """
    Brief description of what the function does.

    :param param1: Description of parameter 1
    :param param2: Description of parameter 2
    :param optional_param: Description of optional parameter

    :return: Description of what is returned
    """
```

**Rules:**
- Function name and opening parenthesis on same line
- Each parameter on its own line, indented with 4 spaces
- Return type annotation on its own line after closing parenthesis
- Colon on same line as return type
- Docstring starts on next line
- Use `:param` and `:return:` style docstrings (Sphinx/reST)

### Git Commits

- Never include "Co-Authored-By" lines or any Claude/AI attribution in commit messages

### General Style

- Use type annotations on all function signatures
- Use `loguru.logger` for logging (not stdlib `logging`)
- Use `pandas` for tabular data
- Classes follow the same parameter-per-line formatting
- Static methods use `@staticmethod` decorator
