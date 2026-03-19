# RCVS Find a Vet — Technical Reference

> **This document must be kept up to date.** Any time new information is discovered about the RCVS website structure, data availability, or scraping behaviour, update this document immediately.

Last updated: 2026-03-18

---

## 1. Website Overview

The RCVS (Royal College of Veterinary Surgeons) operates a public directory of UK veterinary practices at:

```
https://findavet.rcvs.org.uk/find-a-vet-practice/
```

The site is **server-rendered HTML** (not a JavaScript SPA), making it straightforward to scrape with standard HTTP requests and HTML parsing.

---

## 2. Search & Filtering

### Base Search URL

```
https://findavet.rcvs.org.uk/find-a-vet-practice/?filter-keyword=&filter-vetgdp=true&filter-searchtype=practice
```

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `filter-keyword` | string | Search by practice name or location | `surrey`, `GU`, `Guildford` |
| `filter-vetgdp` | boolean | Filter to VetGDP-approved practices only | `true` |
| `filter-searchtype` | string | Search type | `practice` |
| `filter-animals` | string (repeatable) | Filter by animal type treated | `dogs`, `cats`, `equines` |
| `p` | integer | Page number (1-indexed) | `1`, `2`, `249` |

Multiple `filter-animals` parameters can be stacked:
```
&filter-animals=dogs&filter-animals=cats
```

### Additional Filter Categories (visible in sidebar)

- **Practice type**: Core Standards, Equine, Farm Animal, Small Animal
- **Service awards**: Emergency/Critical Care, Diagnostic, etc.
- **Visiting info**: car park, disabled access, weekends, referrals-only
- **Animals treated**: dogs, cats, equines, cattle, exotics, birds, camelids, deer, pigs, poultry, sheep/goats, small mammals, aquatics
- **Specialist fields**: 80+ options (Cardiology, Dentistry, Neurology, Oncology, etc.)
- **Advanced practitioner credentials**
- **Practice interests**: behavioural therapy, complementary medicine
- **Development & training**: VetGDP, VN Training, EMS

### Result Counts (as of 2026-03-18)

| Search | Results | Pages |
|--------|---------|-------|
| All UK VetGDP practices | 2,488 | 249 |
| `surrey` + VetGDP | 71 | 8 |

---

## 3. Pagination

- **Results per page**: 10
- **Pagination parameter**: `&p=N` (1-indexed)
- **Last page may have fewer than 10 results** (e.g. page 8 of Surrey results has just 1 practice)

### Pagination HTML Structure

```html
<ol class="paging">
  <li class="previous"><span><!-- chevron-left SVG (disabled on page 1) --></span></li>
  <li class="active num"><a href="...&p=1">1</a></li>
  <li class="num"><a href="...&p=2">2</a></li>
  <li class="num"><a href="...&p=3">3</a></li>
  <!-- ... -->
  <li class="dots">...</li>
  <li class="num"><a href="...&p=8">8</a></li>
  <li class="next"><a title="Next" href="...&p=2"><!-- chevron-right SVG --></a></li>
</ol>
<p class="paging-info">Page <b>1</b> of <b>8</b></p>
```

**Our parser** reads `p.paging-info > b` tags to extract the total page count.

---

## 4. Practice List Page — HTML Structure

### Practice Entry

Each practice sits inside:

```html
<div class="item item--fav item--practice accredited-accredited" id="item{id}">
  <div class="practice">
    <h2 class="item-title">
      <a href="/find-a-vet-practice/{slug}/">{Practice Name}</a>
    </h2>
    <div class="item-address">
      {Address}, {Town}, {County} <span class="u-nowrap">{Postcode}</span>
    </div>
    <div class="item-contact">
      <span class="item-contact-tel"><!-- phone SVG --> {phone number}</span>
      <a class="item-contact-email" href="...">
        <span class="__cf_email__" data-cfemail="{hex}">[email protected]</span>
      </a>
    </div>
    <div class="amenities">
      <span title="Client car park"><!-- SVG --></span>
      <span title="Open at weekends"><!-- SVG --></span>
    </div>
    <p class="development-and-training">
      <span class="filter dt-vetgdp"><img alt="VetGDP logo" /></span>
      <span class="filter dt-vn-training">VN Training</span>
      <span class="filter dt-ems">EMS</span>
    </p>
  </div>
  <div class="information">
    <ul class="accreditations">
      <li class="accreditation accreditation--core">
        <a href="...">{Accreditation Level}</a>
      </li>
    </ul>
  </div>
</div>
```

### Map Markers (coordinates embedded in list page)

Each list page also contains `gmap-marker` divs with **exact lat/lng** for every practice on that page:

```html
<div class="gmap-marker" id="marker{id}"
  data-lat="51.11010"
  data-lng="-0.75388"
  data-label="1"
  data-accredited="Core Standards (Small Animal)"
  data-url="/find-a-vet-practice/{slug}/"
  data-title="{Practice Name}"
  data-address="{Street}"
  data-city="{Town}"
  data-county="{County}"
  data-postcode="{Postcode}"
  data-country="United Kingdom"
></div>
```

**This is the primary source of coordinates.** It's more accurate than outcode-level geocoding and costs zero extra requests. Our parser extracts these and matches them to practice stubs by URL slug.

### Data Extracted from List Page

| Field | CSS Selector | Notes |
|-------|-------------|-------|
| Name | `h2.item-title > a` | Text content |
| Slug | `h2.item-title > a[href]` | Last path segment of href |
| Address | `div.item-address` | Text content |
| Phone | `span.item-contact-tel` | Text content (strip SVG text) |
| Postcode | `div.gmap-marker[data-postcode]` | From map marker |
| Lat/Lng | `div.gmap-marker[data-lat/data-lng]` | From map marker |
| VN Training | `span.filter.dt-vn-training` | Present/absent |
| EMS | `span.filter.dt-ems` | Present/absent |
| Accreditations | `ul.accreditations > li > a` | Text content |

---

## 5. Individual Practice Page

### URL Pattern

```
/find-a-vet-practice/{practice-name-slugified}-{town}{postcode-no-space}/
```

**Slug rules:**
- Practice name lowercased, spaces replaced with hyphens
- Town name lowercased, appended directly after practice slug
- Postcode appended with no space between parts
- "Ltd", "LLP" etc. are kept in the slug

**Examples:**
| Practice | Town | Postcode | Slug |
|----------|------|----------|------|
| Aura Veterinary | Guildford | GU2 7AJ | `aura-veterinary-guildfordgu2-7aj` |
| 3 Bridges Vets | Dunfermline | KY11 7HQ | `3-bridges-vets-dunfermlineky11-7hq` |
| Amery Veterinary Group | Grayshott | GU26 6HJ | `amery-veterinary-group-grayshottgu26-6hj` |
| Brookmead Veterinary Surgery Ltd | Cranleigh | GU6 8DL | `brookmead-veterinary-surgery-ltd-cranleighgu6-8dl` |

**Important:** Do not guess slugs — extract them from the list page `<a>` href attributes.

### Detail Page HTML Structure

#### Page Title

```html
<h1 class="page-title">{Practice Name}</h1>
```

#### Address (sidebar)

```html
<div class="practice-contactSection practice-address">
  <p>
    {Street}<br>
    {area}<br>
    {town}<br>
    {county}<br>
    {Postcode}<br>
    united kingdom<br>
  </p>
</div>
```

**Note:** Address lines are `<br>`-separated inside a `<p>` tag. Lines are lowercase except the postcode. An RCVS accreditation logo `<a>` may appear inside the `<p>` and must be stripped before parsing.

#### Contact (sidebar)

```html
<div class="practice-contactSection practice-numbers">
  <div>
    <svg><title>Phone</title>...</svg>
    <a href="tel:{number}">{formatted phone}</a>
  </div>
  <div>
    <svg><title>Email</title>...</svg>
    <a href="..."><span class="__cf_email__" data-cfemail="{hex}">[email protected]</span></a>
  </div>
  <div>
    <svg><title>Website</title>...</svg>
    <a href="{url}" target="_blank">Website</a>
  </div>
</div>
```

#### CloudFlare Email Obfuscation

Emails are obfuscated using CloudFlare's email protection. The `data-cfemail` attribute contains a hex string. **Decoding algorithm:**

```python
def decode_cf_email(encoded: str) -> str:
    key = int(encoded[:2], 16)
    return "".join(
        chr(int(encoded[i:i+2], 16) ^ key)
        for i in range(2, len(encoded), 2)
    )
```

The first byte (2 hex chars) is the XOR key. Each subsequent 2-char pair is XOR'd with the key to produce one ASCII character.

#### Social Media (sidebar)

```html
<div class="practice-contactSection practice-social">
  <a href="//www.facebook.com/{PageName}"><!-- facebook SVG --></a>
</div>
```

Not all practices have social media links. When present, it's typically just Facebook.

#### Opening Hours (sidebar)

```html
<table class="practice-openHours" id="openingHours">
  <tr id="monday">
    <td>Monday</td>
    <td>09:00</td>
    <td>17:00</td>
  </tr>
  <!-- ... one <tr> per day -->
</table>
```

**Note:** Closed days show `<td>Closed</td>` in both time cells. Our parser converts this to just `"Closed"` rather than `"Closed–Closed"`.

#### Facilities & Services (main content)

```html
<div id="practice-facilities" class="practice-detail">
  <div class="practice-facilitiesAdditional">
    <h3>Facilities</h3>
    <ul>
      <li>
        <!-- SVG icon -->
        <span>Client car park</span>
      </li>
    </ul>
  </div>
</div>
```

#### Animals Treated (main content)

```html
<div class="practice-speciesTreated">
  <h3>Animals treated</h3>
  <ul>
    <li>
      <figure>
        <!-- animal SVG/image -->
        <figcaption>Dogs</figcaption>
      </figure>
    </li>
    <!-- ... -->
  </ul>
</div>
```

Our parser extracts text from `figcaption` elements.

#### Accreditations (main content)

```html
<div id="practice-accreditations" class="practice-detail">
  <div class="practice-accreditations">
    <h3>Accreditations</h3>
    <!-- many empty conditionals, then: -->
    <div class="practice-accreditationDetail">
      <a href="...">
        <!-- SVG icon -->
        <span class="txt">Core Standards (Small Animal)</span>
      </a>
    </div>
  </div>
</div>
```

Our parser extracts text from `span.txt` inside `div.practice-accreditationDetail`.

#### Development & Training (main content)

```html
<div id="development-and-training" class="practice-detail">
  <div class="wysiwyg">
    <img src="...vetgdp.png" alt="VetGDP logo" />
    <p>This practice is an RCVS Approved Graduate Development Practice...</p>
    <!-- Optional: VN Training, EMS sections -->
  </div>
</div>
```

VN Training and EMS are detected by text content matching within this section.

#### Staff (main content)

```html
<div id="practice-staff" class="practice-detail">
  <div class="staffList-container">
    <h3>Veterinary surgeons</h3>
    <ul class="staffList">
      <li>
        <!-- profile SVG -->
        <span class="staffList-name">Miss Annedine Conradie</span>
        <span class="staffList-qualifications">BVSc  MRCVS</span>
        <span class="staffList-relationship">Director</span>
      </li>
      <!-- ... -->
    </ul>
  </div>

  <div class="staffList-container">
    <h3>Veterinary nurses</h3>
    <ul class="staffList">
      <li>
        <span class="staffList-name">Miss Sarah Clay</span>
        <span class="staffList-qualifications">RVN</span>
        <span class="staffList-relationship">Practice Manager</span>
      </li>
    </ul>
  </div>
</div>
```

**Notes:**
- The `staffList-qualifications` span may contain extra spaces (e.g. `"BVSc  MRCVS"`)
- The `staffList-relationship` span is optional — many staff don't have a listed role
- Vet vs nurse is determined by the `<h3>` heading text: "Veterinary surgeons" vs "Veterinary nurses"

#### Sidebar Map Marker (detail page)

The detail page sidebar also has a map marker with exact coordinates:

```html
<div class="gmap-marker" id="marker{id}"
  data-lat="51.11010"
  data-lng="-0.75388"
  data-title="{Practice Name}"
  data-postcode="{Postcode}"
  ...
></div>
```

This can serve as a fallback coordinate source, but our scraper gets coordinates from the list page markers.

---

## 6. Scraping Strategy

### Scope for Surrey VetGDP Practices

| Step | Requests | Description |
|------|----------|-------------|
| List pages | 8 | Pages 1–8 of `filter-keyword=surrey&filter-vetgdp=true` |
| Detail pages | 71 | One per practice, URL extracted from list page links |
| **Total** | **79** | Very manageable volume |

### Implemented Approach

1. **Scrape list pages** (pages 1–N): extract practice stubs (name, slug, address, phone, lat/lng from map markers, training flags, accreditations)
2. **Scrape detail pages** (one per practice): extract full contact info (email via CF decode, website, phone), staff (vets + nurses with qualifications and roles), animals treated, opening hours, accreditations, facilities, training flags
3. **Rate limiting**: 1.5-second delay between requests
4. **User-Agent**: `RCVS-VetGDP-Finder/0.1 (educational project; polite scraper)`
5. **Retry**: Single retry on failure with 2-second backoff
6. **Output**: JSON file per region at `data/practices/{keyword}_vetgdp.json`

### Libraries

- `requests` — HTTP client (wrapped in `RCVSClient` class)
- `beautifulsoup4` + `lxml` — HTML parsing
- `pydantic` — Data models with validation

### Data Extracted Per Practice

| Field | Source | Extraction Method | Completeness (Surrey) |
|-------|--------|-------------------|----------------------|
| Practice name | List page | `h2.item-title > a` text | 71/71 (100%) |
| URL slug | List page | `h2.item-title > a[href]` last segment | 71/71 (100%) |
| Address (full) | Detail page sidebar | `div.practice-address > p` `<br>`-split lines | 71/71 (100%) |
| Postcode | List page | `div.gmap-marker[data-postcode]` | 71/71 (100%) |
| Phone | Detail page sidebar | `a[href^="tel:"]` text | 67/71 (94%) |
| Email | Detail page sidebar | `span.__cf_email__[data-cfemail]` decoded | 67/71 (94%) |
| Website | Detail page sidebar | `a[target="_blank"]` near Website SVG | 68/71 (96%) |
| Lat/Lng | List page | `div.gmap-marker[data-lat/data-lng]` | 70/71 (99%) |
| Vets (staff list) | Detail page | `div.staffList-container` under "surgeons" heading | 57/71 (80%) |
| Nurses (staff list) | Detail page | `div.staffList-container` under "nurses" heading | Varies |
| Animals treated | Detail page | `figcaption` in `div.practice-speciesTreated` | 69/71 (97%) |
| Opening hours | Detail page sidebar | `table.practice-openHours > tr > td` | 46/71 (65%) |
| Accreditations | Detail page | `span.txt` in `div.practice-accreditationDetail` | Most |
| Facilities | Detail page | `span` in `div.practice-facilitiesAdditional li` | Most |
| VN Training flag | List page | `span.filter.dt-vn-training` present/absent | 63/71 (89%) |
| EMS flag | List page | `span.filter.dt-ems` present/absent | 31/71 (44%) |
| VetGDP flag | List page | Always true (filtered search) | 71/71 (100%) |

---

## 7. Known Quirks & Edge Cases

### Discovered During Scraping

- **CloudFlare email protection**: All emails are obfuscated with CF's XOR cipher. Must decode `data-cfemail` attribute — cannot read emails from rendered text.
- **Some practices don't list a phone number** on list or detail pages (e.g. Bagshot Vets4Pets, Epsom Vets4Pets). 4 out of 71 Surrey practices have no phone.
- **4 practices missing email**: Brelades Veterinary Surgeons, Croydon PDSA Pet Hospital, Linnaeus Veterinary Ltd T/A Crofts Veterinary Practice, Medivet ChipsteadWingrave Vets.
- **1 practice missing map coordinates**: Walton on Thames Vets4Pets Ltd — no gmap-marker on its list page. Resolved via outcode-level geocoding fallback (KT12 → approximate coords).
- **Opening hours not always present**: Only 46/71 (65%) practices list opening hours on their detail page.
- **Staff sections sometimes empty**: 14/71 practices don't list individual staff members — they may use generic staff pages or simply haven't entered data.
- **Address lines are lowercase**: The detail page sidebar renders addresses in lowercase (e.g. "grayshott" not "Grayshott"). Our parser applies `.title()` to normalise casing.
- **RCVS accredited logo inside address `<p>`**: The address paragraph may contain an `<a>` with an SVG logo that must be stripped before extracting address lines.
- **Extra whitespace in qualifications**: Staff qualifications often have double spaces (e.g. `"BVSc  MRCVS"`). We preserve as-is.
- **Chain practices**: Multiple entries exist for chains like Companion Care/Vets4Pets and Medivet — each branch is its own listing.
- **Staff count varies hugely**: From 0 listed staff to 18 vets + 26 nurses (Aura Veterinary hospital).
- **`filter-keyword=GU` (postcode prefix) may not return results** — the keyword search works best with place names and county names.
- **Social media links are inconsistent** — some practices have Facebook, most don't list any.

### Pagination Edge Cases

- The `paging-info` paragraph shows "Page **X** of **Y**" where X and Y are in `<b>` tags.
- The `ol.paging` list uses `li.active.num` for the current page, `li.num` for other pages, `li.dots` for ellipsis.
- On page 1, the "previous" arrow is a `<span>` (disabled). On other pages, it's an `<a>`.
- On the last page, the "next" arrow is a `<span>` (disabled).

---

## 8. Sample Practice Data

### Small Practice — Amery Veterinary Group

```
Name:           Amery Veterinary Group
Address:        Ashburnham House, Crossways Road, Grayshott, Surrey
Postcode:       GU26 6HJ
Phone:          01428 604442
Email:          grayshott@ameryvets.co.uk
Website:        https://www.ameryvets.co.uk
Facebook:       AmeryVets
Hours:          Mon–Fri 09:00–17:00, Sat–Sun Closed
Director:       Miss Annedine Conradie BVSc MRCVS
Principal:      Dr Mark Scott BVSc MRCVS
Vets:           10 surgeons
Nurses:         1 (Miss Sarah Clay RVN — Practice Manager)
Animals:        Birds, Cats, Dogs, Exotic/Wild, Small Mammals
Accreditation:  Core Standards (Small Animal)
Lat/Lng:        51.11010, -0.75388
VetGDP:         Yes
```

### Large Hospital — Aura Veterinary

```
Name:           Aura Veterinary
Address:        70 Priestley Road, Surrey Research Park, Guildford, Surrey
Postcode:       GU2 7AJ
Phone:          01483 668100
Email:          hello@auravet.com
Website:        https://auravet.com
Hours:          Mon–Sat 08:00–18:00, Sun Closed (24hr emergency)
Director:       Prof Nicholas Bacon
Vets:           18 surgeons
Nurses:         26
Animals:        Cats, Dogs
Accreditation:  Small Animal Veterinary Hospital (no dentistry)
Lat/Lng:        51.24050, -0.61686
Specialists:    Internal Medicine, Oncology (3), Soft Tissue Surgery, Surgery (4)
VetGDP:         Yes
VN Training:    Yes
EMS:            Yes
```
