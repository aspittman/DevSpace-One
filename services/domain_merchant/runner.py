import os

from core.crm_client import CRMClient
from services.domain_merchant.adapter import domain_result_to_crm_payload
from services.domain_merchant.config import MAX_ALERTS_OR_INGESTS
from services.domain_merchant.scorer import score_domain
from services.domain_merchant.sources import generate_domains_for_niche
from services.domain_merchant.notifier import send_domain_alert


def decide_action(result: dict) -> str:
    final_score = result["score"]
    brand_score = result["brand_score"]
    resale = result.get("resale_likelihood_score", 0)
    obvious_buyer = result.get("obvious_buyer", False)
    trademark_risk = result.get("trademark_risk", False)

    if trademark_risk:
        return "SKIP"

    if obvious_buyer and final_score >= 75 and brand_score >= 45 and resale >= 55:
        return "BUY_CANDIDATE"

    if obvious_buyer and final_score >= 45 and brand_score >= 35:
        return "REVIEW"

    return "SKIP"


def run(organization_id: str, niche: str | None = None, signals=None, config=None):
    niche = niche or "loans"

    organization_id = organization_id or os.getenv("DOMAIN_MERCHANT_ORG_ID")

    if not organization_id:
        raise ValueError("DOMAIN_MERCHANT_ORG_ID is missing from .env")

    crm = CRMClient()

    candidates = generate_domains_for_niche(niche=niche, limit=250)

    results = []

    for item in candidates:
        domain = item["domain"]

        scored = score_domain(domain=domain, niche=niche)
        scored["source"] = item["source"]
        scored["action"] = decide_action(scored)

        results.append(scored)

    buy_candidates = [
        result for result in results
        if result["action"] == "BUY_CANDIDATE"
    ]

    buy_candidates.sort(key=lambda x: x["score"], reverse=True)

    selected = []

    for result in buy_candidates:
        domain = result["domain"]

        exists_response = crm.domain_exists(
            organization_id=organization_id,
            domain=domain,
        )

        if exists_response.get("exists"):
            print(f"Skipping duplicate domain: {domain}")
            continue

        selected.append(result)

        if len(selected) >= MAX_ALERTS_OR_INGESTS:
            break

    print(f"Domain Merchant niche: {niche}")
    print(f"Candidates scanned: {len(candidates)}")
    print(f"Buy candidates found: {len(buy_candidates)}")
    print(f"Sending to CRM: {len(selected)}")

    sent_to_crm = 0

    for result in selected:
        payload = domain_result_to_crm_payload(
            result=result,
            organization_id=organization_id,
        )

        crm.ingest_lead(payload)
        sent_to_crm += 1

        print(
            f"Sent to CRM: {result['domain']} "
            f"| Score: {result['score']} "
            f"| Target: ${result['target_price']}"
        )

    if selected:
        send_domain_alert(selected)
        print(f"Email alert sent for {len(selected)} domains.")
    else:
        print("No email sent because no domains were selected.")