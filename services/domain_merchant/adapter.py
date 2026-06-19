def clamp_score(value):
    try:
        return max(0, min(100, int(value)))
    except Exception:
        return 0


def domain_result_to_crm_payload(result: dict, organization_id: str) -> dict:
    domain = result["domain"]
    niche = result["niche"]

    crm_score = clamp_score(result.get("resale_likelihood_score") or result.get("score"))

    return {
        "organization_id": organization_id,
        "source_bot": "domain_merchant",
        "company": {
            "name": domain,
            "domain": domain,
            "website": None,
            "industry": niche,
        },
        "contact": None,
        "lead": {
            "lead_type": "domain_candidate",
            "score": crm_score,
            "summary": (
                f"{domain} scored as a Domain Merchant buy candidate. "
                f"Category: {result.get('category')}. "
                f"Target resale price: ${result.get('target_price')}."
            ),
            "pain_points": [
                f"niche: {niche}",
                f"category: {result.get('category')}",
                f"resale likelihood: {result.get('resale_likelihood_score')}",
            ],
        },
        "metadata": {
            "domain": domain,
            "niche": niche,
            "brand_score": result.get("brand_score"),
            "raw_score": result.get("score"),
            "base_score": result.get("base_score"),
            "performance_score_adjustment": result.get("performance_score_adjustment"),
            "performance_reasons": result.get("performance_reasons"),
            "seo_score": result.get("seo_score"),
            "resale_likelihood_score": result.get("resale_likelihood_score"),
            "low_price": result.get("low_price"),
            "target_price": result.get("target_price"),
            "stretch_price": result.get("stretch_price"),
            "trademark_risk": result.get("trademark_risk"),
            "obvious_buyer": result.get("obvious_buyer"),
            "buyer_terms": result.get("buyer_terms"),
            "action_terms": result.get("action_terms"),
            "category": result.get("category"),
            "source": result.get("source"),
            "action": result.get("action"),
        },
    }
