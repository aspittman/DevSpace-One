import re

from services.apollo_outreach.domain_analyzer import detect_domain_angle
from services.apollo_outreach.buyer_profiles import BUYER_PROFILES


TITLE_LEVELS = (
    (22, ("founder", "co-founder", "owner", "chief executive officer", "ceo", "president")),
    (18, ("chief marketing officer", "cmo", "chief revenue officer", "cro")),
    (15, ("vice president", "vp", "head of", "director")),
    (10, ("business development", "marketing", "growth")),
)

BAD_TERMS = (
    "payday",
    "student loan forgiveness",
    "student lending",
    "debt settlement",
    "credit repair",
    "consumer lending",
    "personal loans",
    "university",
    "college",
)

GENERIC_TERMS = {"capital", "funding", "lending", "business financing"}
VERIFIED_EMAIL_STATUSES = {"verified", "valid", "deliverable"}
RISKY_EMAIL_STATUSES = {"catch_all", "catch-all", "unknown", "unverified"}
INVALID_EMAIL_STATUSES = {"invalid", "undeliverable", "bounced", "unavailable"}


def clean(value):
    return " ".join(str(value or "").lower().split())


def get_field(row, *names):
    for name in names:
        if name in row and row[name] not in (None, ""):
            return row[name]
    return ""


def contains_phrase(text: str, phrase: str) -> bool:
    """Match complete words/phrases so terms such as VP do not match developer."""
    pattern = r"(?<![a-z0-9])" + re.escape(clean(phrase)) + r"(?![a-z0-9])"
    return bool(re.search(pattern, clean(text)))


def _industry_score(blob: str, terms: list[str]) -> tuple[int, list[str]]:
    matches = [term for term in terms if contains_phrase(blob, term)]
    specific = sorted(
        (term for term in matches if term not in GENERIC_TERMS),
        key=lambda value: (-len(value), value),
    )
    generic = sorted(term for term in matches if term in GENERIC_TERMS)

    # Closely related phrases are supporting evidence, not independent bonuses.
    score = min(45, (35 if specific else 0) + min(10, 5 * max(0, len(specific) - 1)))
    if not specific and generic:
        score = min(24, 12 + 6 * (len(generic) - 1))

    reasons = [f"industry match: {term}" for term in (specific[:2] or generic[:2])]
    return score, reasons


def _title_score(title: str) -> tuple[int, str | None]:
    for points, titles in TITLE_LEVELS:
        for candidate in titles:
            if contains_phrase(title, candidate):
                return points, f"decision-maker title: {candidate}"
    return 0, None


def _employee_count(lead: dict) -> int | None:
    raw = get_field(lead, "employee_count", "estimated_num_employees", "employees")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def score_lead(lead: dict, domain_offer: dict):
    """Return a fit score, not a probability of conversion."""
    angle = detect_domain_angle(domain_offer["domain"])
    profile = BUYER_PROFILES[angle]
    company = get_field(lead, "company", "Company", "organization_name", "Organization")
    title = get_field(lead, "title", "Title", "job_title")
    email = get_field(lead, "email", "Email")
    website = get_field(lead, "website", "Website", "company_website")
    industry = get_field(lead, "industry", "Industry")
    description = get_field(lead, "keywords", "Keywords", "description", "Description")
    email_status = clean(get_field(lead, "email_status", "Email Status"))
    blob = " ".join(map(clean, (company, website, industry, description)))

    score, reasons = _industry_score(blob, profile["good_terms"])

    title_points, title_reason = _title_score(clean(title))
    score += title_points
    if title_reason:
        reasons.append(title_reason)

    bad_matches = [term for term in BAD_TERMS if contains_phrase(blob, term)]
    if bad_matches:
        score -= 45
        reasons.append(f"bad fit: {bad_matches[0]}")

    if email_status in INVALID_EMAIL_STATUSES:
        score -= 50
        reasons.append(f"invalid email status: {email_status}")
    elif email and email_status in VERIFIED_EMAIL_STATUSES:
        score += 20
        reasons.append("verified email")
    elif email and email_status in RISKY_EMAIL_STATUSES:
        score += 5
        reasons.append(f"risky email status: {email_status}")
    elif email:
        score += 10
        reasons.append("email available; verification unknown")

    if website:
        score += 8
        reasons.append("has website")

    employees = _employee_count(lead)
    if employees is not None:
        if 2 <= employees <= 500:
            score += 5
            reasons.append("company size fits outreach")
        elif employees > 5000:
            score -= 5
            reasons.append("very large company")

    target_countries = {
        clean(value) for value in domain_offer.get("target_countries", []) if value
    }
    country = clean(get_field(lead, "country", "Country"))
    if target_countries and country:
        if country in target_countries:
            score += 5
            reasons.append("target geography")
        else:
            score -= 15
            reasons.append(f"outside target geography: {country}")

    return max(0, min(100, score)), reasons
