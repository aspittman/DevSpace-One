from core.crm_client import CRMClient
from core.email_sender import send_email


def run():
    crm = CRMClient()

    lead_payload = {
        "source_bot": "domain_outreach",
        "company": {
            "name": "Example Roofing",
            "website": "https://exampleroofing.com",
            "industry": "Roofing",
            "city": "Provo",
            "state": "UT",
        },
        "contact": {
            "name": "Owner",
            "email": "owner@example.com",
            "title": "Owner",
        },
        "lead": {
            "lead_type": "domain_outreach",
            "score": 75,
            "summary": "Potential domain upgrade opportunity.",
            "pain_points": ["brand_domain_upgrade"],
        },
        "signals": {
            "candidate_domain": "fastroofingpros.com",
            "domain_match_quality": "high",
        },
    }

    result = crm.ingest_lead(lead_payload)
    lead_id = result["lead_id"]

    strategy = crm.get_strategy(lead_id)

    subject = strategy.get("subject", "Quick domain idea")
    body = strategy.get(
        "body",
        "I found a domain that may be a strong fit for your business.",
    )

    email_result = send_email(
        to_email=lead_payload["contact"]["email"],
        subject=subject,
        body=body,
    )

    crm.record_outreach_event({
        "lead_id": lead_id,
        "channel": "email",
        "status": "sent" if email_result.get("sent") else "preview",
        "strategy": strategy,
    })