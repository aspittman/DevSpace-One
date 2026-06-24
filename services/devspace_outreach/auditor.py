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

    def handle_starttag(self, tag, attrs):
        attr = {key.lower(): value or "" for key, value in attrs}

        if tag == "title":
            self._in_title = True
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

    def handle_data(self, data):
        if self._in_title:
            self.title += data

        if data and data.strip():
            self.text_parts.append(data.strip())

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


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
        "audit_notes": [],
    }

    if not website:
        audit["issues"].append("missing_website")
        audit["audit_notes"].append("No website URL found.")
        return audit

    try:
        final_url, html, elapsed_ms, page_bytes = fetch_homepage(website, config)
    except requests.exceptions.SSLError:
        audit["issues"].append("missing_ssl")
        audit["audit_notes"].append("HTTPS request failed SSL validation.")
        return audit
    except requests.RequestException as exc:
        audit["issues"].append("broken_links")
        audit["audit_notes"].append(f"Homepage request failed: {exc}")
        return audit

    parser = PageParser()
    parser.feed(html)
    text = parser.text
    title = parser.title.strip()
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

    if elapsed_ms >= int(config.get("slow_response_ms", 2500)):
        audit["issues"].append("low_mobile_pagespeed")

    if elapsed_ms >= int(config.get("poor_lcp_ms", 4000)):
        audit["issues"].append("poor_lcp")

    if page_bytes >= int(config.get("large_page_bytes", 1500000)) or len(missing_image_dimensions) >= int(config.get("large_image_count", 12)):
        audit["issues"].append("large_images")

    if len(missing_image_dimensions) >= int(config.get("poor_cls_image_count", 4)):
        audit["issues"].append("poor_cls")

    if len(blocking_scripts) >= int(config.get("render_blocking_script_count", 6)):
        audit["issues"].append("render_blocking_scripts")

    if len(parser.scripts) >= int(config.get("unused_javascript_script_count", 20)):
        audit["issues"].append("unused_javascript")

    if len(images_missing_alt) >= int(config.get("accessibility_missing_alt_count", 3)):
        audit["issues"].append("accessibility_issues")

    if city and city.lower() not in f"{title} {description} {text[:3000]}".lower():
        audit["issues"].append("missing_city_keywords")

    if len(title) < 15 or len(title) > 70:
        audit["issues"].append("weak_title_tag")

    if not description:
        audit["issues"].append("missing_meta_description")

    if not parser.schema:
        audit["issues"].append("missing_schema_markup")
        audit["issues"].append("missing_localbusiness_schema")
        audit["issues"].append("missing_chiropractor_schema")

    if not has_any(html, MAP_TERMS):
        audit["issues"].append("missing_google_map")

    if not has_any(text, LOCATION_TERMS):
        audit["issues"].append("no_location_page")
        audit["issues"].append("no_service_area_terms")

    if not has_any(text, BOOKING_TERMS) and not any("appointment" in link.lower() or "book" in link.lower() for link in parser.links):
        audit["issues"].append("no_online_booking")

    if not phone_number_is_prominent(parser, first_screen):
        audit["issues"].append("phone_number_not_prominent")

    if not parser.phone_links:
        audit["issues"].append("no_click_to_call_on_mobile")

    if not any("tel:" in link.lower() or "appointment" in link.lower() or "book" in link.lower() for link in parser.links[:8]):
        audit["issues"].append("no_sticky_mobile_cta")

    if not has_any(first_screen, BOOKING_TERMS):
        audit["issues"].append("appointment_button_below_fold")

    if not has_any(first_screen, CTA_TERMS):
        audit["issues"].append("weak_call_to_action")

    if parser.forms == 0 and not has_any(text, ("contact form", "send us a message")):
        audit["issues"].append("contact_form_hard_to_find")

    if not has_any(text, ("review", "reviews", "google rating", "stars")):
        audit["issues"].append("missing_reviews")

    if not has_any(text, ("testimonial", "testimonials", "what patients say")):
        audit["issues"].append("no_testimonials")

    if not has_any(text, ("dr.", "doctor", "chiropractor", "meet the team", "about us")):
        audit["issues"].append("no_doctor_bio")

    if not has_any(text, ("success story", "case study", "patient story", "before and after")):
        audit["issues"].append("no_before_after_or_patient_success_content")
        audit["issues"].append("no_patient_success_content")

    if not has_any(text, INSURANCE_TERMS):
        audit["issues"].append("no_insurance_info")

    if not has_any(text, CERTIFICATION_TERMS):
        audit["issues"].append("no_certifications")

    if not has_any(text, CONDITION_TERMS):
        audit["issues"].append("no_conditions_treated_content")

    if "viewport" not in parser.meta:
        audit["issues"].append("mobile_layout_issues")

    if any(marker in html.lower() for marker in CMS_MARKERS) and "generator" in parser.meta:
        audit["issues"].append("outdated_cms_signals")

    if not resource_exists(final_url, "/sitemap.xml", config):
        audit["issues"].append("missing_sitemap")

    if not resource_exists(final_url, "/robots.txt", config):
        audit["issues"].append("missing_robots_txt")

    audit.update({
        "audit_status": "completed",
        "final_url": final_url,
        "response_ms": int(elapsed_ms),
        "page_bytes": page_bytes,
        "title": title,
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
