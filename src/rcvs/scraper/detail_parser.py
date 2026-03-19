from __future__ import annotations

from bs4 import BeautifulSoup, Tag
from loguru import logger

from rcvs.scraper.models import Practice, StaffMember


def decode_cf_email(
    encoded: str
) -> str:
    """
    Decode a CloudFlare-obfuscated email address.

    CloudFlare uses a simple XOR cipher: the first byte is the key,
    each subsequent byte pair is XOR'd with it to produce the character.

    :param encoded: Hex-encoded string from data-cfemail attribute

    :return: Decoded email address
    """
    try:
        key = int(encoded[:2], 16)
        return "".join(
            chr(int(encoded[i:i + 2], 16) ^ key)
            for i in range(2, len(encoded), 2)
        )
    except (ValueError, IndexError):
        logger.warning("Failed to decode CF email: {}", encoded)
        return ""


def parse_detail_page(
    soup: BeautifulSoup,
    stub: dict,
    region: str
) -> Practice:
    """
    Parse a practice detail page into a full Practice model.

    Merges data from the stub (list page) with data from the detail page.

    :param soup: Parsed HTML of the practice detail page
    :param stub: Practice stub from the list page parser
    :param region: Search keyword used to find this practice

    :return: Fully populated Practice model
    """
    email = _parse_email(soup)
    website = _parse_website(soup)
    phone = _parse_phone(soup) or stub.get("phone", "")
    address, postcode = _parse_address(soup, stub)
    vets, nurses = _parse_staff(soup)
    animals = _parse_animals(soup)
    hours = _parse_hours(soup)
    accreditations = _parse_accreditations(soup) or stub.get("accreditations", [])
    facilities = _parse_facilities(soup)
    has_vn_training, has_ems = _parse_training(soup)

    return Practice(
        name=stub.get("name", ""),
        slug=stub.get("slug", ""),
        address=address,
        postcode=postcode,
        phone=phone,
        email=email,
        website=website,
        lat=stub.get("lat"),
        lng=stub.get("lng"),
        vets=vets,
        nurses=nurses,
        animals=animals,
        hours=hours,
        accreditations=accreditations,
        facilities=facilities,
        has_vetgdp=True,
        has_vn_training=has_vn_training or stub.get("has_vn_training", False),
        has_ems=has_ems or stub.get("has_ems", False),
        region=region,
    )


def _parse_email(
    soup: BeautifulSoup
) -> str:
    """
    Extract email from CloudFlare-obfuscated span.

    :param soup: Parsed detail page HTML

    :return: Decoded email address
    """
    contact = soup.find("div", class_="practice-numbers")
    if not contact:
        return ""

    cf_span = contact.find("span", class_="__cf_email__")
    if cf_span and cf_span.get("data-cfemail"):
        return decode_cf_email(cf_span["data-cfemail"])

    return ""


def _parse_website(
    soup: BeautifulSoup
) -> str:
    """
    Extract the practice website URL.

    :param soup: Parsed detail page HTML

    :return: Website URL
    """
    contact = soup.find("div", class_="practice-numbers")
    if not contact:
        return ""

    for div in contact.find_all("div"):
        svg_title = div.find("svg")
        if svg_title:
            title_el = svg_title.find("title")
            if title_el and "Website" in title_el.get_text():
                link = div.find("a", target="_blank")
                if link:
                    return link.get("href", "")

    return ""


def _parse_phone(
    soup: BeautifulSoup
) -> str:
    """
    Extract phone number from the contact section.

    :param soup: Parsed detail page HTML

    :return: Phone number string
    """
    contact = soup.find("div", class_="practice-numbers")
    if not contact:
        return ""

    tel_link = contact.find("a", href=lambda h: h and h.startswith("tel:"))
    if tel_link:
        return tel_link.get_text(strip=True)

    return ""


def _parse_address(
    soup: BeautifulSoup,
    stub: dict
) -> tuple[str, str]:
    """
    Extract the full address and postcode from the detail page sidebar.

    :param soup: Parsed detail page HTML
    :param stub: Practice stub with fallback data

    :return: Tuple of (full address, postcode)
    """
    address_div = soup.find("div", class_="practice-address")
    if not address_div:
        return stub.get("address", ""), stub.get("postcode", "")

    p_tag = address_div.find("p")
    if not p_tag:
        return stub.get("address", ""), stub.get("postcode", "")

    for a_tag in p_tag.find_all("a"):
        a_tag.decompose()
    for svg_tag in p_tag.find_all("svg"):
        svg_tag.decompose()

    lines = []
    for part in p_tag.stripped_strings:
        cleaned = part.strip().rstrip(",")
        if cleaned:
            lines.append(cleaned)

    postcode = stub.get("postcode", "")
    address_lines = []
    for line in lines:
        upper = line.upper().strip()
        if upper == "UNITED KINGDOM":
            continue
        if _looks_like_postcode(upper):
            postcode = upper
            continue
        address_lines.append(line.title())

    full_address = ", ".join(address_lines)
    return full_address, postcode


def _looks_like_postcode(
    text: str
) -> bool:
    """
    Check if a string looks like a UK postcode.

    :param text: String to check

    :return: True if it matches a basic UK postcode pattern
    """
    import re
    return bool(re.match(r"^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$", text.strip()))


def _parse_staff(
    soup: BeautifulSoup
) -> tuple[list[StaffMember], list[StaffMember]]:
    """
    Extract veterinary surgeons and nurses from the staff section.

    :param soup: Parsed detail page HTML

    :return: Tuple of (vets list, nurses list)
    """
    staff_section = soup.find("div", id="practice-staff")
    if not staff_section:
        return [], []

    containers = staff_section.find_all("div", class_="staffList-container")

    vets = []
    nurses = []

    for container in containers:
        heading = container.find("h3")
        if not heading:
            continue

        heading_text = heading.get_text(strip=True).lower()
        is_vet = "surgeon" in heading_text
        staff_list = container.find("ul", class_="staffList")
        if not staff_list:
            continue

        for li in staff_list.find_all("li"):
            member = _parse_staff_member(li)
            if member:
                if is_vet:
                    vets.append(member)
                else:
                    nurses.append(member)

    return vets, nurses


def _parse_staff_member(
    li: Tag
) -> StaffMember | None:
    """
    Parse a single staff member list item.

    :param li: BeautifulSoup Tag for one staff member <li>

    :return: StaffMember model, or None if no name found
    """
    name_span = li.find("span", class_="staffList-name")
    if not name_span:
        return None

    name = name_span.get_text(strip=True)

    quals_span = li.find("span", class_="staffList-qualifications")
    qualifications = quals_span.get_text(strip=True) if quals_span else ""

    role_span = li.find("span", class_="staffList-relationship")
    role = role_span.get_text(strip=True) if role_span else ""

    return StaffMember(name=name, qualifications=qualifications, role=role)


def _parse_animals(
    soup: BeautifulSoup
) -> list[str]:
    """
    Extract the list of animal types treated.

    :param soup: Parsed detail page HTML

    :return: List of animal type names
    """
    species_div = soup.find("div", class_="practice-speciesTreated")
    if not species_div:
        return []

    animals = []
    for fig in species_div.find_all("figcaption"):
        text = fig.get_text(strip=True)
        if text:
            animals.append(text)

    return animals


def _parse_hours(
    soup: BeautifulSoup
) -> dict[str, str]:
    """
    Extract opening hours from the hours table.

    :param soup: Parsed detail page HTML

    :return: Dictionary mapping day name to hours string
    """
    table = soup.find("table", class_="practice-openHours")
    if not table:
        return {}

    hours = {}
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 3:
            day = cells[0].get_text(strip=True)
            open_time = cells[1].get_text(strip=True)
            close_time = cells[2].get_text(strip=True)
            if open_time.lower() == "closed" or close_time.lower() == "closed":
                hours[day] = "Closed"
            else:
                hours[day] = f"{open_time}–{close_time}"
        elif len(cells) == 2:
            day = cells[0].get_text(strip=True)
            hours[day] = cells[1].get_text(strip=True)

    return hours


def _parse_accreditations(
    soup: BeautifulSoup
) -> list[str]:
    """
    Extract RCVS accreditation details.

    :param soup: Parsed detail page HTML

    :return: List of accreditation names
    """
    accred_div = soup.find("div", class_="practice-accreditations")
    if not accred_div:
        return []

    accreditations = []
    for detail in accred_div.find_all("div", class_="practice-accreditationDetail"):
        txt_span = detail.find("span", class_="txt")
        if txt_span:
            text = txt_span.get_text(strip=True)
            if text:
                accreditations.append(text)

    return accreditations


def _parse_facilities(
    soup: BeautifulSoup
) -> list[str]:
    """
    Extract facilities and services.

    :param soup: Parsed detail page HTML

    :return: List of facility names
    """
    facilities_div = soup.find("div", class_="practice-facilitiesAdditional")
    if not facilities_div:
        return []

    facilities = []
    for li in facilities_div.find_all("li"):
        span = li.find("span")
        if span:
            text = span.get_text(strip=True)
            if text:
                facilities.append(text)

    return facilities


def _parse_training(
    soup: BeautifulSoup
) -> tuple[bool, bool]:
    """
    Extract VN Training and EMS flags from the development & training section.

    :param soup: Parsed detail page HTML

    :return: Tuple of (has_vn_training, has_ems)
    """
    training_div = soup.find("div", id="development-and-training")
    if not training_div:
        return False, False

    text = training_div.get_text(strip=True).lower()
    has_vn = "approved veterinary nurse training practice" in text or "vn training" in text
    has_ems = "extra-mural studies" in text or "ems" in text.split()

    return has_vn, has_ems
