import re
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests


BOOKING_TERMS = (
    "book online",
    "schedule online",
    "schedule appointment",
    "request appointment",
    "make an appointment",
    "book appointment",
    "appointments",
)
CTA_TERMS = (
    "call now",
    "contact us",
    "schedule",
    "book",
    "request",
    "get started",
)
CMS_MARKERS = (
    "wp-content",
    "wp-includes",
    "wixstatic",
    "squarespace",
    "weebly",
)
LOCATION_TERMS = (
    "areas served",
    "service area",
    "serving",
    "nearby",
)
MAP_TERMS = (
    "google maps",
    "maps.google.com",
    "google.com/maps",
)
INSURANCE_TERMS = (
    "insurance",
    "insured",
    "coverage",
    "medicare",
)
CERTIFICATION_TERMS = (
    "certified",
    "certification",
    "licensed",
    "license",
)
CONDITION_TERMS = (
    "back pain",
    "neck pain",
    "sports injury",
    "auto accident",
    "sciatica",
    "headache",
)
DOCTOR_BIO_TERMS = (
    "dr.",
    "doctor",
    "meet the doctor",
    "meet the team",
    "about us",
    "our team",
    "provider",
    "credentials",
)
CHIROPRACTIC_TERMS = (
    "chiropractor",
    "chiropractic",
    "chiropractic clinic",
)


FINDING_COPY = {
    "missing_city_keywords": {
        "category": "local_seo",
        "label": "Missing city keyword on homepage",
        "why_it_matters": "Local service businesses need strong city signals to rank for nearby searches.",
        "recommendation": "Add the target city to the title tag, H1, and early homepage copy where it reads naturally.",
        "business_impact": "Could improve local search relevance and help more nearby patients find the clinic.",
    },
    "missing_service_keyword_in_title": {
        "category": "local_seo",
        "label": "Missing chiropractic keyword in title tag",
        "why_it_matters": "Searchers and search engines use the title tag to understand the main service offered by the business.",
        "recommendation": "Update the title tag to include a primary service term such as chiropractor or chiropractic clinic.",
        "business_impact": "Could make the homepage more relevant for high-intent chiropractic searches.",
    },
    "missing_service_keywords": {
        "category": "local_seo",
        "label": "Missing chiropractic service keywords on homepage",
        "why_it_matters": "A homepage that does not clearly describe the service can be harder to match with local treatment searches.",
        "recommendation": "Add concise homepage copy that names chiropractic care and the main services patients search for.",
        "business_impact": "Could help more qualified visitors understand the clinic quickly and continue toward booking.",
    },
    "weak_title_tag": {
        "category": "local_seo",
        "label": "Title tag length is not search friendly",
        "why_it_matters": "Very short or very long title tags can weaken the message shown in search results.",
        "recommendation": "Rewrite the title tag to clearly include the clinic name, main service, and target city.",
        "business_impact": "Could improve search-result clarity and attract more relevant clicks.",
    },
    "missing_meta_description": {
        "category": "local_seo",
        "label": "Missing meta description",
        "why_it_matters": "Meta descriptions often shape the snippet people see before choosing a local provider.",
        "recommendation": "Add a concise meta description that mentions chiropractic care, location, and an appointment action.",
        "business_impact": "Could improve click-through from local search results.",
    },
    "missing_localbusiness_schema": {
        "category": "local_seo",
        "label": "Missing LocalBusiness schema",
        "why_it_matters": "Structured local business data helps search engines understand the clinic's name, location, and contact details.",
        "recommendation": "Add JSON-LD LocalBusiness or MedicalBusiness schema with accurate NAP and website details.",
        "business_impact": "Could strengthen local entity signals in search.",
    },
    "missing_chiropractor_schema": {
        "category": "local_seo",
        "label": "Missing Chiropractor schema",
        "why_it_matters": "A chiropractor-specific schema type can clarify the medical service category for search engines.",
        "recommendation": "Use Chiropractor schema or an appropriate medical local business subtype on the homepage.",
        "business_impact": "Could improve relevance for chiropractic-specific local searches.",
    },
    "missing_schema_markup": {
        "category": "local_seo",
        "label": "Missing schema markup",
        "why_it_matters": "Structured data helps search engines understand the business, services, and website content.",
        "recommendation": "Add JSON-LD schema that accurately describes the business and its primary services.",
        "business_impact": "Could improve search engine understanding and support richer local search visibility.",
    },
    "no_online_booking": {
        "category": "conversion",
        "label": "No online booking link found",
        "why_it_matters": "Patients with immediate pain often choose the provider with the easiest appointment path.",
        "recommendation": "Add a visible online booking or appointment request link in the header and hero area.",
        "business_impact": "Could increase appointment requests from ready-to-book visitors.",
    },
    "phone_number_not_prominent": {
        "category": "conversion",
        "label": "Phone number is not prominent above the fold",
        "why_it_matters": "Mobile visitors often want to call quickly without searching through the page.",
        "recommendation": "Place a clearly visible phone number in the header or first screen of the homepage.",
        "business_impact": "Could increase calls from nearby patients comparing providers.",
    },
    "no_click_to_call_on_mobile": {
        "category": "conversion",
        "label": "Phone number is not click-to-call",
        "why_it_matters": "A non-clickable phone number creates extra friction for mobile visitors.",
        "recommendation": "Wrap the primary phone number in a tel: link and keep it visible on mobile.",
        "business_impact": "Could turn more mobile visits into phone calls.",
    },
    "appointment_button_below_fold": {
        "category": "conversion",
        "label": "No clear appointment button above the fold",
        "why_it_matters": "Visitors should immediately see how to book or request care when they land on the homepage.",
        "recommendation": "Add a prominent appointment button in the first screen, especially on mobile.",
        "business_impact": "Could reduce booking friction and increase appointment requests.",
    },
    "missing_reviews": {
        "category": "trust",
        "label": "No Google reviews or ratings shown",
        "why_it_matters": "Reviews help patients trust a provider before booking care.",
        "recommendation": "Feature recent Google reviews, star rating, or patient testimonials near key conversion areas.",
        "business_impact": "Could improve trust and help more visitors feel comfortable requesting an appointment.",
    },
    "no_testimonials": {
        "category": "trust",
        "label": "No patient testimonials found",
        "why_it_matters": "Testimonials give prospective patients confidence that others had a good experience.",
        "recommendation": "Add patient testimonials or success stories with appropriate permissions.",
        "business_impact": "Could improve conversion from visitors who are comparing clinics.",
    },
    "no_doctor_bio": {
        "category": "trust",
        "label": "No doctor bio or credentials found",
        "why_it_matters": "Patients often want to know who will treat them before booking.",
        "recommendation": "Add a doctor or team bio with credentials, experience, and care approach.",
        "business_impact": "Could build confidence and increase first-visit requests.",
    },
    "no_conditions_treated_content": {
        "category": "local_seo",
        "label": "No condition-specific service content found",
        "why_it_matters": "Patients often search by symptoms or injury type, not only by the word chiropractor.",
        "recommendation": "Create or surface pages for back pain, neck pain, auto accident care, sports injury, and related services.",
        "business_impact": "Could capture more high-intent treatment searches.",
    },
    "large_images": {
        "category": "performance",
        "label": "Large page or image optimization issue",
        "why_it_matters": "Heavy pages can load slowly on mobile connections and cause visitors to leave.",
        "recommendation": "Compress large images, add explicit dimensions, and use modern image formats where possible.",
        "business_impact": "Could improve mobile engagement and appointment conversion.",
    },
    "low_mobile_pagespeed": {
        "category": "performance",
        "label": "Mobile PageSpeed not checked",
        "why_it_matters": "A real mobile Lighthouse score is useful because many patients compare clinics from a phone.",
        "recommendation": "Run PageSpeed Insights or Lighthouse for the homepage before making a mobile speed claim.",
        "business_impact": "Could identify mobile performance fixes that help retain more appointment-ready visitors.",
    },
    "render_blocking_scripts": {
        "category": "performance",
        "label": "Multiple render-blocking scripts found",
        "why_it_matters": "Render-blocking scripts can delay the first usable view of the page.",
        "recommendation": "Defer non-critical scripts and remove scripts that are not needed on the homepage.",
        "business_impact": "Could improve perceived speed for mobile visitors.",
    },
    "missing_ssl": {
        "category": "technical",
        "label": "SSL problem detected",
        "why_it_matters": "Security warnings can reduce trust and block visitors from reaching the website.",
        "recommendation": "Fix the SSL certificate and force the site to load cleanly over HTTPS.",
        "business_impact": "Could prevent lost visits caused by browser security warnings.",
    },
    "missing_sitemap": {
        "category": "technical",
        "label": "Missing sitemap.xml",
        "why_it_matters": "A sitemap helps search engines discover important service and location pages.",
        "recommendation": "Generate and submit a sitemap.xml that includes core service, location, and contact pages.",
        "business_impact": "Could improve discovery of pages that attract local patients.",
    },
    "missing_robots_txt": {
        "category": "technical",
        "label": "Missing robots.txt",
        "why_it_matters": "Robots.txt gives crawlers basic instructions and points them toward the sitemap.",
        "recommendation": "Add a robots.txt file that allows normal crawling and references the sitemap.",
        "business_impact": "Could make technical SEO hygiene stronger and easier to maintain.",
    },
    "broken_links": {
        "category": "technical",
        "label": "Homepage could not be fetched",
        "why_it_matters": "If the homepage fails for the scanner, some visitors or crawlers may also have trouble reaching it.",
        "recommendation": "Check hosting, redirects, DNS, and homepage status codes.",
        "business_impact": "Could prevent lost traffic from access or redirect problems.",
    },
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.text_parts = []
        self.meta = {}
        self.links = []
        self.scripts = []
        self.images = []
        self.schema = False
        self.forms = 0
        self.phone_links = 0
        self.h1 = []
        self._tag_stack = []
        self._script_type = ""
        self._in_script = False
        self.schema_text_parts = []

    def handle_starttag(self, tag, attrs):
        attr = {key.lower(): value or "" for key, value in attrs}

        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._tag_stack.append("h1")
        elif tag == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()

            if name:
                self.meta[name] = attr.get("content", "")
        elif tag == "a":
            href = attr.get("href", "")
            self.links.append(href)

            if href.startswith("tel:"):
                self.phone_links += 1
        elif tag == "script":
            script_type = attr.get("type", "").lower()
            self._script_type = script_type
            self._in_script = True

            if "ld+json" in script_type:
                self.schema = True

            self.scripts.append(attr)
        elif tag == "img":
            self.images.append(attr)
        elif tag == "form":
            self.forms += 1

        if "schema.org" in " ".join(str(value) for value in attr.values()).lower():
            self.schema = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._tag_stack:
            self._tag_stack.pop()
        elif tag == "script":
            self._in_script = False
            self._script_type = ""

    def handle_data(self, data):
        if self._in_title:
            self.title += data

        if self._tag_stack and self._tag_stack[-1] == "h1":
            self.h1.append(data.strip())

        if self._in_script and "ld+json" in self._script_type:
            self.schema_text_parts.append(data.strip())

        if data and data.strip():
            self.text_parts.append(data.strip())

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)

    @property
    def h1_text(self) -> str:
        return " ".join(part for part in self.h1 if part)

    @property
    def schema_text(self) -> str:
        return " ".join(part for part in self.schema_text_parts if part)


def ensure_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.scheme:
        return url

    return f"https://{url}"


def fetch_homepage(url: str, config: dict) -> tuple[str, str, float, int]:
    timeout = int(config.get("audit_timeout", 20))
    headers = {
        "User-Agent": config.get(
            "user_agent",
            "Mozilla/5.0 (compatible; DevspaceOutreachBot/1.0)",
        )
    }
    requested_url = ensure_url(url)
    started = time.monotonic()
    response = requests.get(
        requested_url,
        headers=headers,
        timeout=timeout,
        allow_redirects=True,
    )
    elapsed_ms = (time.monotonic() - started) * 1000
    response.raise_for_status()
    return response.url, response.text, elapsed_ms, len(response.content)


def resource_exists(base_url: str, path: str, config: dict) -> bool:
    parsed = urlparse(base_url)
    url = f"{parsed.scheme}://{parsed.netloc}{path}"
    timeout = int(config.get("resource_check_timeout", 8))

    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": config.get(
                    "user_agent",
                    "Mozilla/5.0 (compatible; DevspaceOutreachBot/1.0)",
                )
            },
            timeout=timeout,
            allow_redirects=True,
        )
    except requests.RequestException:
        return False

    return response.status_code < 400 and bool(response.text.strip())


def city_from_location(location: str) -> str:
    return (location or "").split(",")[0].split(" UT")[0].split(" CO")[0].strip()


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def snippet(value: str, max_length: int = 140) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip()

    if len(cleaned) <= max_length:
        return cleaned

    return f"{cleaned[: max_length - 3].rstrip()}..."


def add_finding(
    audit: dict,
    key: str,
    evidence: str,
    location: str = "Homepage",
    status: str = "weakness",
):
    copy = FINDING_COPY[key]
    finding = {
        "key": key,
        "category": copy["category"],
        "label": copy["label"],
        "location": location,
        "status": status,
        "evidence": evidence,
        "why_it_matters": copy["why_it_matters"],
        "recommendation": copy["recommendation"],
        "business_impact": copy["business_impact"],
    }

    audit.setdefault("checks", []).append(finding)

    if status == "weakness":
        audit.setdefault("findings", []).append(finding)
        audit.setdefault("issues", []).append(key)

    return finding


def add_not_checked(audit: dict, key: str, evidence: str, location: str = "Homepage"):
    return add_finding(
        audit=audit,
        key=key,
        evidence=evidence,
        location=location,
        status="not_checked",
    )


def phone_number_is_prominent(parser: PageParser, text: str) -> bool:
    if parser.phone_links:
        return True

    first_chunk = text[:1200]
    return bool(re.search(r"(\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", first_chunk))


def audit_website(prospect: dict, config: dict) -> dict:
    website = prospect.get("website") or prospect.get("url") or prospect.get("domain")
    audit = {
        "audit_status": "failed",
        "issues": [],
        "findings": [],
        "checks": [],
        "audit_notes": [],
    }

    if not website:
        audit["audit_notes"].append("No website URL found.")
        return audit

    try:
        final_url, html, elapsed_ms, page_bytes = fetch_homepage(website, config)
    except requests.exceptions.SSLError:
        add_finding(
            audit,
            "missing_ssl",
            f"HTTPS request failed SSL validation for {website}.",
            "Homepage request",
        )
        audit["audit_notes"].append("HTTPS request failed SSL validation.")
        return audit
    except requests.RequestException as exc:
        add_finding(
            audit,
            "broken_links",
            f"Homepage request failed for {website}: {snippet(str(exc), 180)}",
            "Homepage request",
        )
        audit["audit_notes"].append(f"Homepage request failed: {exc}")
        return audit

    parser = PageParser()
    parser.feed(html)
    text = parser.text
    title = parser.title.strip()
    h1_text = parser.h1_text.strip()
    description = parser.meta.get("description", "").strip()
    location = prospect.get("location") or ""
    city = city_from_location(location)
    first_screen = text[:1200]
    blocking_scripts = [
        script for script in parser.scripts
        if "src" in script and "async" not in script and "defer" not in script
    ]
    missing_image_dimensions = [
        image for image in parser.images
        if image.get("src") and (not image.get("width") or not image.get("height"))
    ]
    images_missing_alt = [
        image for image in parser.images
        if image.get("src") and not image.get("alt")
    ]

    add_not_checked(
        audit,
        "low_mobile_pagespeed",
        "Mobile PageSpeed/Lighthouse was not run; only homepage HTML response and markup heuristics were checked.",
        "Mobile PageSpeed",
    )

    if elapsed_ms >= int(config.get("poor_lcp_ms", 4000)):
        add_finding(
            audit,
            "large_images",
            f"Homepage HTML response took {int(elapsed_ms)}ms, above the {int(config.get('poor_lcp_ms', 4000))}ms threshold used by the scanner.",
        )

    if page_bytes >= int(config.get("large_page_bytes", 1500000)) or len(missing_image_dimensions) >= int(config.get("large_image_count", 12)):
        add_finding(
            audit,
            "large_images",
            f"Homepage transferred {page_bytes:,} bytes and {len(missing_image_dimensions)} images are missing width or height attributes.",
        )

    if len(blocking_scripts) >= int(config.get("render_blocking_script_count", 6)):
        add_finding(
            audit,
            "render_blocking_scripts",
            f"Found {len(blocking_scripts)} script tags with src attributes that are not marked async or defer.",
        )

    if city and (
        city.lower() not in title.lower()
        or city.lower() not in h1_text.lower()
    ):
        missing_city_locations = []

        if city.lower() not in title.lower():
            missing_city_locations.append("title")

        if city.lower() not in h1_text.lower():
            missing_city_locations.append("H1")

        missing_city_subject = " and ".join(missing_city_locations)
        missing_city_verb = "do" if len(missing_city_locations) > 1 else "does"

        add_finding(
            audit,
            "missing_city_keywords",
            (
                f"Homepage title is '{title or 'missing'}' and H1 is '{h1_text or 'missing'}'; "
                f"{missing_city_subject} {missing_city_verb} not mention {city}."
            ),
            "Homepage title/H1",
        )

    if not has_any(title, CHIROPRACTIC_TERMS):
        add_finding(
            audit,
            "missing_service_keyword_in_title",
            f"Homepage title is '{title or 'missing'}' and does not mention chiropractor or chiropractic.",
            "Homepage title tag",
        )

    if not has_any(f"{title} {h1_text} {text[:3000]}", CHIROPRACTIC_TERMS):
        add_finding(
            audit,
            "missing_service_keywords",
            "The title, H1, and first section of homepage copy do not mention chiropractor or chiropractic.",
            "Homepage title/H1/body",
        )

    if len(title) < 15 or len(title) > 70:
        add_finding(
            audit,
            "weak_title_tag",
            f"Homepage title is '{title or 'missing'}' and is {len(title)} characters long.",
            "Homepage title tag",
        )

    if not description:
        add_finding(
            audit,
            "missing_meta_description",
            "No meta name='description' content was found in the homepage HTML.",
            "Homepage head",
        )

    schema_text = parser.schema_text.lower()

    if not parser.schema:
        add_finding(
            audit,
            "missing_schema_markup",
            "No JSON-LD schema script or schema.org markup was found in the homepage HTML.",
            "Homepage structured data",
        )

    if not parser.schema or "localbusiness" not in schema_text:
        add_finding(
            audit,
            "missing_localbusiness_schema",
            "No JSON-LD LocalBusiness schema type was found in the homepage HTML.",
            "Homepage structured data",
        )

    if not parser.schema or "chiropractor" not in schema_text:
        add_finding(
            audit,
            "missing_chiropractor_schema",
            "No JSON-LD Chiropractor schema type was found in the homepage HTML.",
            "Homepage structured data",
        )

    if not has_any(text, BOOKING_TERMS) and not any("appointment" in link.lower() or "book" in link.lower() for link in parser.links):
        add_finding(
            audit,
            "no_online_booking",
            "Homepage copy and links did not include book online, schedule appointment, request appointment, or similar booking terms.",
            "Homepage body/links",
        )

    if not phone_number_is_prominent(parser, first_screen):
        add_finding(
            audit,
            "phone_number_not_prominent",
            "No tel: link or standard phone number pattern was found in the first 1,200 characters of homepage text.",
            "Above-the-fold homepage text",
        )

    if not parser.phone_links:
        add_finding(
            audit,
            "no_click_to_call_on_mobile",
            "No tel: link was found among homepage links.",
            "Homepage links",
        )

    if not has_any(first_screen, BOOKING_TERMS):
        add_finding(
            audit,
            "appointment_button_below_fold",
            "The first 1,200 characters of homepage text did not include book online, schedule appointment, request appointment, or similar booking language.",
            "Above-the-fold homepage text",
        )

    if not has_any(text, ("review", "reviews", "google rating", "stars")):
        add_finding(
            audit,
            "missing_reviews",
            "Homepage text did not mention reviews, Google rating, or star ratings.",
            "Homepage body",
        )

    if not has_any(text, ("testimonial", "testimonials", "what patients say")):
        add_finding(
            audit,
            "no_testimonials",
            "Homepage text did not mention testimonials or patient feedback.",
            "Homepage body",
        )

    if not has_any(text, DOCTOR_BIO_TERMS):
        add_finding(
            audit,
            "no_doctor_bio",
            "Homepage text did not mention a doctor, provider, credentials, meet the team, or about us section.",
            "Homepage body",
        )

    service_signal_text = " ".join([text, " ".join(parser.links[:50])])

    if not has_any(service_signal_text, CONDITION_TERMS):
        add_finding(
            audit,
            "no_conditions_treated_content",
            "Homepage text and sampled links did not mention back pain, neck pain, auto accident, sports injury, sciatica, or headaches.",
            "Homepage body/links",
        )

    if "viewport" not in parser.meta:
        audit["issues"].append("mobile_layout_issues")

    if not resource_exists(final_url, "/sitemap.xml", config):
        add_finding(
            audit,
            "missing_sitemap",
            f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/sitemap.xml did not return a usable sitemap response.",
            "Sitemap check",
        )

    if not resource_exists(final_url, "/robots.txt", config):
        add_finding(
            audit,
            "missing_robots_txt",
            f"{urlparse(final_url).scheme}://{urlparse(final_url).netloc}/robots.txt did not return a usable robots.txt response.",
            "Robots.txt check",
        )

    audit.update({
        "audit_status": "completed",
        "final_url": final_url,
        "response_ms": int(elapsed_ms),
        "page_bytes": page_bytes,
        "title": title,
        "h1": h1_text,
        "meta_description": description,
        "script_count": len(parser.scripts),
        "blocking_script_count": len(blocking_scripts),
        "image_count": len(parser.images),
        "missing_image_dimension_count": len(missing_image_dimensions),
        "internal_links_sample": [
            urljoin(final_url, link)
            for link in parser.links[:10]
        ],
    })

    return audit


def audit_prospects(prospects: list[dict], config: dict) -> list[dict]:
    audited = []

    for prospect in prospects:
        audit = audit_website(prospect, config)
        merged = dict(prospect)
        merged["audit"] = audit
        merged["issues"] = sorted(set(prospect.get("issues") or []) | set(audit.get("issues") or []))
        audited.append(merged)

    return audited
