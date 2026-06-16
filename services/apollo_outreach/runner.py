import os
from pathlib import Path

from core.crm_client import CRMClient
from services.apollo_outreach.csv_loader import read_csv, write_csv
from services.apollo_outreach.email_writer import build_subject, build_email
from services.apollo_outreach.lead_scorer import score_lead
from services.apollo_outreach.adapter import outreach_result_to_crm_payload


DATA_DIR = Path("data/apollo_outreach")
DOMAINS_FILE = DATA_DIR / "domains.csv"
APOLLO_EXPORT_FILE = DATA_DIR / "apollo_export.csv"
SCORED_OUTPUT = DATA_DIR / "scored_leads.csv"
DRAFTS_OUTPUT = DATA_DIR / "email_drafts.csv"


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


def run(organization_id: str, niche: str | None = None, signals=None, config=None):
    organization_id = os.getenv("APOLLO_OUTREACH_ORG_ID")

    if not organization_id:
        raise ValueError("APOLLO_OUTREACH_ORG_ID is missing from .env")

    domains = read_csv(DOMAINS_FILE)

    if not domains:
        print(f"No domains found at {DOMAINS_FILE}")
        print("Add domains exported from Domain Merchant or the CRM.")
        return

    leads = read_csv(APOLLO_EXPORT_FILE)

    if not leads:
        print(f"No Apollo export found at {APOLLO_EXPORT_FILE}")
        print("Export leads from Apollo and save the CSV there.")
        return

    crm = CRMClient()

    scored_rows = []
    draft_rows = []

    for lead in leads:
        domain_offer, score, reasons = best_domain_match(lead, domains)

        if not domain_offer:
            continue

        if score < 50:
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