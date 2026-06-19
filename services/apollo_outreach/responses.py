from datetime import datetime
from pathlib import Path

from core.crm_client import CRMClient
from services.apollo_outreach.csv_loader import read_csv


RESPONSES_FILE = Path("data/apollo_outreach/email_responses.csv")


def clean(value):
    return str(value or "").strip()


def lower(value):
    return clean(value).lower()


def parse_date(value):
    value = clean(value)

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d, %Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            pass

    return value


def money_to_float(value):
    value = clean(value).replace("$", "").replace(",", "")

    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def get_field(row: dict, *possible_names):
    for name in possible_names:
        if name in row and row[name]:
            return row[name]

    lower_map = {k.lower().strip(): v for k, v in row.items()}

    for name in possible_names:
        key = name.lower().strip()
        if key in lower_map and lower_map[key]:
            return lower_map[key]

    return ""


def infer_response_status(row: dict) -> str:
    explicit = lower(get_field(row, "response_status", "Response Status", "status", "Status"))

    if explicit:
        return explicit

    body = lower(get_field(row, "response_body", "Response Body", "body", "Body", "message", "Message"))

    positive_terms = ["interested", "how much", "price", "offer", "send", "call", "talk", "available"]
    negative_terms = ["not interested", "unsubscribe", "remove me", "no thanks", "stop"]

    if any(term in body for term in negative_terms):
        return "negative"

    if any(term in body for term in positive_terms):
        return "positive"

    return "replied"


def normalize_response_row(row: dict) -> dict:
    response_status = infer_response_status(row)
    offer_amount = money_to_float(get_field(row, "offer", "Offer", "Offer Amount", "Price"))
    purchase_intent = response_status in {"positive", "interested", "offer", "buy", "buying"}

    if offer_amount is not None:
        purchase_intent = True

    return {
        "domain": lower(get_field(row, "domain", "Domain")),
        "email": lower(get_field(row, "email", "Email", "from_email", "From Email")),
        "company": get_field(row, "company", "Company"),
        "first_name": get_field(row, "first_name", "First Name"),
        "last_name": get_field(row, "last_name", "Last Name"),
        "response_status": response_status,
        "purchase_intent": purchase_intent,
        "offer_amount": offer_amount,
        "responded_at": parse_date(get_field(row, "responded_at", "Responded At", "Date", "Reply Date")),
        "subject": get_field(row, "subject", "Subject"),
        "response_body": get_field(row, "response_body", "Response Body", "body", "Body", "message", "Message"),
        "raw": row,
    }


def response_to_crm_payload(result: dict, organization_id: str) -> dict:
    domain = result.get("domain")
    email = result.get("email")
    response_status = result.get("response_status")

    return {
        "organization_id": organization_id,
        "source_bot": "apollo_outreach",
        "company": {
            "name": result.get("company") or email or domain,
            "domain": domain,
            "website": None,
            "industry": "domain_sales",
        },
        "contact": {
            "first_name": result.get("first_name") or "",
            "last_name": result.get("last_name") or "",
            "email": email,
            "role": "",
        },
        "lead": {
            "lead_type": "domain_buyer_response",
            "status": response_status,
            "score": 90 if result.get("purchase_intent") else 40,
            "summary": f"{email} replied about {domain}: {response_status}",
            "notes": result.get("response_body") or "",
            "pain_points": [],
        },
        "metadata": {
            "domain": domain,
            "outreach_status": "responded",
            "outcome": "response",
            "response_status": response_status,
            "purchase_intent": result.get("purchase_intent"),
            "offer_amount": result.get("offer_amount"),
            "responded_at": result.get("responded_at"),
            "email_subject": result.get("subject"),
            "response_body": result.get("response_body"),
            "raw": result.get("raw"),
        },
    }


def sync_responses(organization_id: str, responses_file=None, crm=None) -> int:
    rows = read_csv(responses_file or RESPONSES_FILE)

    if not rows:
        return 0

    crm = crm or CRMClient()
    synced = 0

    for row in rows:
        result = normalize_response_row(row)

        if not result["email"] and not result["domain"]:
            continue

        crm.ingest_lead(response_to_crm_payload(result, organization_id))
        synced += 1

    return synced
