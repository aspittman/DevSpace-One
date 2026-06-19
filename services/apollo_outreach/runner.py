import os
from pathlib import Path

from core.crm_client import CRMClient
from services.apollo_outreach.apollo_client import ApolloClient, normalize_apollo_person
from services.apollo_outreach.buyer_profiles import BUYER_PROFILES
from services.apollo_outreach.csv_loader import read_csv, write_csv
from services.apollo_outreach.domain_analyzer import detect_domain_angle
from services.apollo_outreach.email_writer import build_subject, build_email
from services.apollo_outreach.lead_scorer import score_lead
from services.apollo_outreach.adapter import outreach_result_to_crm_payload
from services.apollo_outreach.responses import RESPONSES_FILE, sync_responses


DATA_DIR = Path("data/apollo_outreach")
DOMAINS_FILE = DATA_DIR / "domains.csv"
APOLLO_EXPORT_FILE = DATA_DIR / "apollo_export.csv"
SCORED_OUTPUT = DATA_DIR / "scored_leads.csv"
DRAFTS_OUTPUT = DATA_DIR / "email_drafts.csv"


DEFAULT_TITLES = [
    "Founder",
    "Owner",
    "CEO",
    "President",
    "Chief Marketing Officer",
    "VP Marketing",
    "Business Development",
    "Growth",
]

DEFAULT_SENIORITIES = ["owner", "founder", "c_suite", "vp", "director", "head"]


def as_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def as_bool(value, default=True):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).lower().strip() not in {"0", "false", "no", "off"}


def best_domain_match(lead: dict, domains: list[dict]):
    best_domain = None
    best_score = -1
    best_reasons = []

    for domain_offer in domains:
        score, reasons = score_lead(lead, domain_offer)

        if score > best_score:
            best_domain = domain_offer
            best_score = score
            best_reasons = reasons

    return best_domain, best_score, best_reasons


def _domain_from_signal(signal: dict) -> dict | None:
    domain = signal.get("domain") or signal.get("name")

    if not domain:
        return None

    return {
        "domain": domain,
        "ask_price": (
            signal.get("ask_price")
            or signal.get("target_price")
            or signal.get("list_price")
            or signal.get("price")
        ),
        "niche": signal.get("niche"),
    }


def load_domain_offers(signals=None, config=None) -> list[dict]:
    config = config or {}

    configured_domains = config.get("domains") or config.get("domain_offers") or []

    if isinstance(configured_domains, str):
        configured_domains = as_list(configured_domains)

    if configured_domains:
        offers = []

        for item in configured_domains:
            if isinstance(item, str):
                offers.append({"domain": item})
            elif isinstance(item, dict) and item.get("domain"):
                offers.append(item)

        return offers

    signal_rows = []

    if isinstance(signals, dict):
        signal_rows = signals.get("domains") or signals.get("signals") or signals.get("items") or []
    elif isinstance(signals, list):
        signal_rows = signals

    offers = []

    for signal in signal_rows:
        if not isinstance(signal, dict):
            continue

        offer = _domain_from_signal(signal)

        if offer:
            offers.append(offer)

    if offers:
        return offers

    return read_csv(DOMAINS_FILE)


def apollo_search_keywords(domains: list[dict], config: dict) -> list[str]:
    configured = as_list(config.get("apollo_keywords") or config.get("keywords"))

    if configured:
        return configured

    terms = []

    for domain_offer in domains:
        angle = detect_domain_angle(domain_offer["domain"])
        terms.extend(BUYER_PROFILES[angle]["good_terms"])
        terms.extend(BUYER_PROFILES[angle]["buyer_types"])

    seen = set()
    unique_terms = []

    for term in terms:
        if term not in seen:
            unique_terms.append(term)
            seen.add(term)

    return unique_terms[:10]


def load_apollo_leads(domains: list[dict], config: dict) -> list[dict]:
    use_api = as_bool(config.get("use_apollo_api"), default=True)

    if use_api and os.getenv("APOLLO_API_KEY"):
        client = ApolloClient(
            base_url=config.get("apollo_base_url"),
        )
        keywords = apollo_search_keywords(domains, config)
        people = client.search_people(
            keywords=keywords,
            titles=as_list(config.get("apollo_titles")) or DEFAULT_TITLES,
            seniorities=as_list(config.get("apollo_seniorities")) or DEFAULT_SENIORITIES,
            organization_locations=as_list(config.get("apollo_locations")),
            per_page=int(config.get("apollo_per_page", 25)),
            max_pages=int(config.get("apollo_max_pages", 1)),
            extra_payload=config.get("apollo_extra_payload"),
        )

        return [
            normalize_apollo_person(person, keyword=person.get("_apollo_keyword"))
            for person in people
        ]

    return read_csv(APOLLO_EXPORT_FILE)


def lead_key(lead: dict) -> str:
    email = lead.get("email") or lead.get("Email")

    if email:
        return f"email:{email.lower()}"

    return "|".join([
        str(lead.get("first_name") or lead.get("First Name") or "").lower(),
        str(lead.get("last_name") or lead.get("Last Name") or "").lower(),
        str(lead.get("company") or lead.get("Company") or "").lower(),
    ])


def run(organization_id: str, niche: str | None = None, signals=None, config=None):
    config = config or {}
    organization_id = organization_id or os.getenv("APOLLO_OUTREACH_ORG_ID")

    if not organization_id:
        raise ValueError("APOLLO_OUTREACH_ORG_ID is missing from .env")

    crm = CRMClient()
    responses_synced = 0

    if as_bool(config.get("sync_responses"), default=True):
        responses_synced = sync_responses(
            organization_id=organization_id,
            responses_file=config.get("responses_file", RESPONSES_FILE),
            crm=crm,
        )

    domains = load_domain_offers(signals=signals, config=config)

    if not domains:
        print(f"No domains found at {DOMAINS_FILE}")
        print("Add domains through service config, CRM domain signals, or data/apollo_outreach/domains.csv.")
        print(f"Synced {responses_synced} Apollo Outreach responses to CRM")
        return

    leads = load_apollo_leads(domains=domains, config=config)

    if not leads:
        print("No Apollo leads found.")
        print("Set APOLLO_API_KEY for API sourcing or save a CSV export at data/apollo_outreach/apollo_export.csv.")
        print(f"Synced {responses_synced} Apollo Outreach responses to CRM")
        return

    scored_rows = []
    draft_rows = []
    seen_leads = set()
    minimum_score = int(config.get("minimum_score", 50))
    max_ingests = int(config.get("max_ingests", 50))

    for lead in leads:
        key = lead_key(lead)

        if key in seen_leads:
            continue

        seen_leads.add(key)
        domain_offer, score, reasons = best_domain_match(lead, domains)

        if not domain_offer:
            continue

        if score < minimum_score:
            continue

        subject = build_subject(domain_offer)
        body = build_email(lead, domain_offer)

        scored_rows.append({
            "score": score,
            "domain": domain_offer["domain"],
            "company": lead.get("company", lead.get("Company", "")),
            "first_name": lead.get("first_name", lead.get("First Name", "")),
            "last_name": lead.get("last_name", lead.get("Last Name", "")),
            "title": lead.get("title", lead.get("Title", "")),
            "email": lead.get("email", lead.get("Email", "")),
            "website": lead.get("website", lead.get("Website", "")),
            "reasons": "; ".join(reasons),
        })

        draft_rows.append({
            "score": score,
            "domain": domain_offer["domain"],
            "to_email": lead.get("email", lead.get("Email", "")),
            "company": lead.get("company", lead.get("Company", "")),
            "subject": subject,
            "body": body,
        })

        payload = outreach_result_to_crm_payload(
            organization_id=organization_id,
            lead=lead,
            domain_offer=domain_offer,
            score=score,
            reasons=reasons,
            subject=subject,
            body=body,
        )

        crm.ingest_lead(payload)

        if len(scored_rows) >= max_ingests:
            break

    scored_rows.sort(key=lambda row: int(row["score"]), reverse=True)
    draft_rows.sort(key=lambda row: int(row["score"]), reverse=True)

    write_csv(
        SCORED_OUTPUT,
        scored_rows,
        [
            "score",
            "domain",
            "company",
            "first_name",
            "last_name",
            "title",
            "email",
            "website",
            "reasons",
        ],
    )

    write_csv(
        DRAFTS_OUTPUT,
        draft_rows,
        [
            "score",
            "domain",
            "to_email",
            "company",
            "subject",
            "body",
        ],
    )

    print(f"Scored leads saved to {SCORED_OUTPUT}")
    print(f"Email drafts saved to {DRAFTS_OUTPUT}")
    print(f"Sent {len(scored_rows)} Apollo Outreach leads to CRM")
    print(f"Synced {responses_synced} Apollo Outreach responses to CRM")
