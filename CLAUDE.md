# RCVS VetGDP Practice Finder

## Project Overview

A tool to find, filter, and organise UK veterinary practices that offer the VetGDP (Veterinary Graduate Development Programme) training programme. The goal is to create a pipeline that:

1. **Scrapes** VetGDP-approved practices from the RCVS Find a Vet directory
2. **Filters** results to the South East / Surrey area
3. **Processes** practice data (contact details, location, etc.)
4. **Outputs** organised, actionable lists for contacting practices about job opportunities

Source: https://findavet.rcvs.org.uk/find-a-vet-practice/?filter-keyword=&filter-vetgdp=true&filter-searchtype=practice

## Current Status (2026-03-19)

**All 6 build phases are complete. App is deployed to Streamlit Community Cloud.**

- **Live app:** https://rcvs-tracker.streamlit.app/
- **Hosted on:** Streamlit Community Cloud (free tier, deploys from `main` branch)
- Scraper has been run for Surrey (71 practices)
- All 4 Streamlit pages working (Table, Map, Contact Tracker, Export)
- Contact Tracker supports `st.secrets` for Cloud credentials and falls back to local-only mode

### Data Quality — Surrey Scrape

| Metric | Value |
|--------|-------|
| Total practices | 71 |
| With email | 67 (94%) |
| With phone | 67 (94%) |
| With website | 68 (96%) |
| With coordinates | 71 (100% — 70 from RCVS, 1 from outcode fallback) |
| With staff listed | 57 (80%) |
| With opening hours | 46 (65%) |
| With animals list | 69 (97%) |
| VN Training | 63 (89%) |
| EMS placements | 31 (44%) |

### How to Run

```bash
# Scrape practices (already done for surrey)
uv run rcvs-scrape --keyword surrey --output-dir data/practices

# Scrape a different region
uv run rcvs-scrape --keyword hampshire --output-dir data/practices

# Launch the Streamlit app locally
uv run streamlit run src/rcvs/app/Home.py
```

### Deployment

The app is deployed to **Streamlit Community Cloud** from the `main` branch.

- **URL:** https://rcvs-tracker.streamlit.app/
- **Main file:** `src/rcvs/app/Home.py`
- **Dependencies:** Resolved via `uv.lock` (Community Cloud auto-detects this)
- **Secrets:** Google Sheets credentials are configured via Streamlit's Secrets Management (`st.secrets["gcp_service_account"]`), not committed to the repo

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
│       └── surrey_vetgdp.json  # Scraped data (71 practices, committed to repo)
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
            ├── Home.py         # Streamlit landing page
            ├── pages/
            │   ├── 1_Practice_Table.py   # Searchable table + selectbox detail view
            │   ├── 2_Map_View.py         # Interactive folium map with click-to-detail
            │   ├── 3_Contact_Tracker.py  # Status tracking (Sheets or local)
            │   └── 4_Export.py           # CSV/Excel download
            └── components/
                ├── __init__.py
                ├── filters.py      # Sidebar filter widgets (shared across pages)
                ├── practice_detail.py # Shared practice detail rendering (used by Table + Map)
                └── data_loader.py  # Load JSON, enrich with geo + computed columns
```

### Key Design Decisions

- **Coordinates from RCVS map markers**: The list page embeds `gmap-marker` divs with exact lat/lng for each practice. This is far more accurate than outcode-level geocoding and costs zero extra requests. The outcode CSV (`data/postcodes/outcodes.csv`) is only a fallback for the rare case where a practice's map marker is missing.
- **CloudFlare email decoding**: All emails on the RCVS site are obfuscated with CF's XOR cipher. The scraper decodes them from the `data-cfemail` hex attribute.
- **Scraper separate from app**: Data is committed to the repo as JSON. The Streamlit app never hits the RCVS website — it reads from local files. This decouples scraping from the user experience.
- **Google Sheets tracker with graceful fallback**: Credentials are loaded from `st.secrets` (for Cloud) or a local `service-account.json` file. When neither is present, the Contact Tracker falls back to session-only local state.
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
- **Scraping**: requests + BeautifulSoup (lxml parser)
- **Data models**: Pydantic
- **Logging**: `loguru`
- **Data handling**: `pandas`
- **Contact tracking**: `gspread` + `google-auth` (optional)
- **Map**: `folium` + `streamlit-folium`

## Dependencies

All in `pyproject.toml`:
```
streamlit, pandas, loguru, requests, beautifulsoup4, lxml, pydantic, gspread, google-auth, openpyxl, folium, streamlit-folium
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
