from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from loguru import logger


def build_search_url(
    keyword: str,
    page: int = 1
) -> str:
    """
    Build a search URL for VetGDP practices.

    :param keyword: Search keyword (e.g. 'surrey')
    :param page: Page number (1-indexed)

    :return: URL path for the search
    """
    return (
        f"/find-a-vet-practice/"
        f"?filter-keyword={keyword}"
        f"&filter-vetgdp=true"
        f"&filter-searchtype=practice"
        f"&p={page}"
    )


def get_total_pages(
    soup: BeautifulSoup
) -> int:
    """
    Extract the total number of pages from the search results.

    Looks for 'Page X of Y' in the paging-info paragraph.

    :param soup: Parsed HTML of a search results page

    :return: Total number of pages
    """
    paging_info = soup.find("p", class_="paging-info")
    if paging_info:
        bold_tags = paging_info.find_all("b")
        if len(bold_tags) >= 2:
            return int(bold_tags[1].get_text(strip=True))

    paging = soup.find("ol", class_="paging")
    if paging:
        page_links = paging.find_all("li", class_="num")
        if page_links:
            last = page_links[-1].get_text(strip=True)
            return int(last)

    return 1


def _extract_map_markers(
    soup: BeautifulSoup
) -> dict[str, dict]:
    """
    Extract lat/lng coordinates from gmap-marker divs.

    :param soup: Parsed HTML of a search results page

    :return: Mapping of practice URL slug to coordinate data
    """
    markers = {}
    for marker in soup.find_all("div", class_="gmap-marker"):
        url = marker.get("data-url", "")
        if url:
            markers[url] = {
                "lat": float(marker.get("data-lat", 0)),
                "lng": float(marker.get("data-lng", 0)),
                "city": marker.get("data-city", ""),
                "county": marker.get("data-county", ""),
                "postcode": marker.get("data-postcode", ""),
            }
    return markers


def parse_list_page(
    soup: BeautifulSoup
) -> list[dict]:
    """
    Parse a search results page into practice stubs.

    Each stub contains: name, slug, address, phone, has_vn_training, has_ems,
    lat, lng, city, county, postcode.

    :param soup: Parsed HTML of a search results page

    :return: List of practice stub dictionaries
    """
    markers = _extract_map_markers(soup)
    stubs = []

    items = soup.find_all("div", class_="item--practice")
    for item in items:
        stub = _parse_item(item, markers)
        if stub:
            stubs.append(stub)

    logger.info("Parsed {} practice stubs from list page", len(stubs))
    return stubs


def _parse_item(
    item: Tag,
    markers: dict[str, dict]
) -> dict | None:
    """
    Parse a single practice item from the search results.

    :param item: BeautifulSoup Tag for one practice entry
    :param markers: Map marker data keyed by URL slug

    :return: Practice stub dictionary, or None if parsing fails
    """
    title_tag = item.find("h2", class_="item-title")
    if not title_tag:
        return None

    link = title_tag.find("a")
    if not link:
        return None

    name = link.get_text(strip=True)
    href = link.get("href", "")
    slug = href.strip("/").split("/")[-1] if href else ""

    address_div = item.find("div", class_="item-address")
    address = address_div.get_text(strip=True) if address_div else ""

    phone_span = item.find("span", class_="item-contact-tel")
    phone = ""
    if phone_span:
        phone = phone_span.get_text(strip=True)
        for prefix in ["phone2", "Phone"]:
            phone = phone.replace(prefix, "").strip()

    training = item.find("p", class_="development-and-training")
    has_vn_training = bool(training and training.find("span", class_="dt-vn-training"))
    has_ems = bool(training and training.find("span", class_="dt-ems"))

    accreditations = []
    accred_list = item.find("ul", class_="accreditations")
    if accred_list:
        for li in accred_list.find_all("li"):
            acc_link = li.find("a")
            if acc_link:
                accreditations.append(acc_link.get_text(strip=True))

    marker_data = markers.get(href, {})

    stub = {
        "name": name,
        "slug": slug,
        "address": address,
        "phone": phone,
        "postcode": marker_data.get("postcode", ""),
        "lat": marker_data.get("lat"),
        "lng": marker_data.get("lng"),
        "city": marker_data.get("city", ""),
        "county": marker_data.get("county", ""),
        "has_vn_training": has_vn_training,
        "has_ems": has_ems,
        "accreditations": accreditations,
    }

    return stub
