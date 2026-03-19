from __future__ import annotations

import argparse
import json
from pathlib import Path

from bs4 import BeautifulSoup
from loguru import logger

from rcvs.scraper.client import RCVSClient
from rcvs.scraper.detail_parser import parse_detail_page
from rcvs.scraper.list_parser import build_search_url, get_total_pages, parse_list_page


def scrape_practices(
    keyword: str,
    output_dir: Path
) -> Path:
    """
    Scrape all VetGDP practices for a given keyword and save to JSON.

    When *keyword* is empty, all UK VetGDP practices are scraped and each
    practice's region is set from the county provided by the RCVS map
    marker data.

    :param keyword: Search keyword (e.g. 'surrey', 'hampshire'), or empty for all UK
    :param output_dir: Directory to write the output JSON file

    :return: Path to the written JSON file
    """
    client = RCVSClient()
    output_dir.mkdir(parents=True, exist_ok=True)

    label = keyword or "uk"
    logger.info("Scraping VetGDP practices for keyword: '{}'", label)

    first_url = build_search_url(keyword, page=1)
    response = client.get(first_url)
    soup = BeautifulSoup(response.text, "lxml")
    total_pages = get_total_pages(soup)
    logger.info("Found {} pages of results", total_pages)

    all_stubs = parse_list_page(soup)

    for page in range(2, total_pages + 1):
        url = build_search_url(keyword, page=page)
        response = client.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        stubs = parse_list_page(soup)
        all_stubs.extend(stubs)

    logger.info("Collected {} practice stubs from list pages", len(all_stubs))

    practices = []
    skipped = 0
    for i, stub in enumerate(all_stubs, 1):
        slug = stub["slug"]
        logger.info("[{}/{}] Scraping detail: {}", i, len(all_stubs), stub["name"])

        detail_url = f"/find-a-vet-practice/{slug}/"
        try:
            response = client.get(detail_url)
        except Exception as exc:
            logger.warning("Skipping {} — {}", stub["name"], exc)
            skipped += 1
            continue

        detail_soup = BeautifulSoup(response.text, "lxml")

        region = stub.get("county", "") or keyword
        practice = parse_detail_page(detail_soup, stub, region=region)
        practices.append(practice)

    if skipped:
        logger.warning("Skipped {} practices due to errors", skipped)

    output_file = output_dir / f"{label}_vetgdp.json"
    data = [p.model_dump() for p in practices]
    output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    logger.info("Wrote {} practices to {}", len(practices), output_file)

    return output_file


def main() -> None:
    """
    CLI entry point for the scraper.
    """
    parser = argparse.ArgumentParser(description="Scrape VetGDP practices from RCVS")
    parser.add_argument(
        "--keyword",
        default="",
        help="Search keyword (e.g. 'surrey', 'hampshire'). Empty for all UK.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/practices",
        help="Directory to write output JSON",
    )
    args = parser.parse_args()

    scrape_practices(
        keyword=args.keyword,
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
