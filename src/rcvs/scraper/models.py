from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class StaffMember(BaseModel):
    """
    A veterinary staff member (surgeon or nurse).

    :param name: Full name including title
    :param qualifications: Post-nominal qualifications
    :param role: Role at practice (Director, Principal, etc.)
    """

    name: str
    qualifications: str = ""
    role: str = ""


class Practice(BaseModel):
    """
    A veterinary practice scraped from the RCVS directory.

    :param name: Practice name
    :param slug: URL slug from the RCVS directory
    :param address: Full street address
    :param postcode: UK postcode
    :param phone: Phone number
    :param email: Email address
    :param website: Practice website URL
    :param lat: Latitude from RCVS map marker
    :param lng: Longitude from RCVS map marker
    :param vets: List of veterinary surgeons
    :param nurses: List of veterinary nurses
    :param animals: Animals treated
    :param hours: Opening hours as day-to-time mapping
    :param accreditations: RCVS accreditation levels
    :param facilities: Facilities and services
    :param has_vetgdp: VetGDP approved
    :param has_vn_training: VN Training practice
    :param has_ems: EMS placements offered
    :param region: Search keyword used to find this practice
    :param scraped_at: Timestamp of scrape
    """

    name: str
    slug: str = ""
    address: str = ""
    postcode: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    lat: float | None = None
    lng: float | None = None
    vets: list[StaffMember] = Field(default_factory=list)
    nurses: list[StaffMember] = Field(default_factory=list)
    animals: list[str] = Field(default_factory=list)
    hours: dict[str, str] = Field(default_factory=dict)
    accreditations: list[str] = Field(default_factory=list)
    facilities: list[str] = Field(default_factory=list)
    has_vetgdp: bool = True
    has_vn_training: bool = False
    has_ems: bool = False
    region: str = ""
    scraped_at: str = Field(default_factory=lambda: datetime.now().isoformat())
