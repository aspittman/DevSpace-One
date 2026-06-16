import os

from core.crm_client import CRMClient
from services.domain_merchant.adapter import domain_result_to_crm_payload
from services.domain_merchant.config import MAX_ALERTS_OR_INGESTS
from services.domain_merchant.scorer import score_domain
from services.domain_merchant.sources import generate_domains_for_niche


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

    organization_id = os.getenv("DOMAIN_MERCHANT_ORG_ID")

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

    selected = buy_candidates[:MAX_ALERTS_OR_INGESTS]

    print(f"Domain Merchant niche: {niche}")
    print(f"Candidates scanned: {len(candidates)}")
    print(f"Buy candidates found: {len(buy_candidates)}")
    print(f"Sending to CRM: {len(selected)}")

    for result in selected:
        payload = domain_result_to_crm_payload(
            result=result,
            organization_id=organization_id,
        )

        crm.ingest_lead(payload)

        print(
            f"Sent to CRM: {result['domain']} "
            f"| Score: {result['score']} "
            f"| Target: ${result['target_price']}"
        )