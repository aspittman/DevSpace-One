def domain_result_to_crm_payload(result: dict, organization_id: str) -> dict:
    domain = result["domain"]
    niche = result["niche"]

    return {
        "organization_id": organization_id,
        "source_bot": "domain_merchant",
        "company": {
            "name": domain,
            "website": None,
            "industry": niche,
        },
        "contact": None,
        "lead": {
            "title": domain,
            "status": "new",
            "score": result["score"],
            "notes": (
                f"Domain candidate: {domain}\n"
                f"Niche: {niche}\n"
                f"Category: {result.get('category')}\n"
                f"Brand Score: {result.get('brand_score')}\n"
                f"Resale Likelihood: {result.get('resale_likelihood_score')}\n"
                f"Target Price: ${result.get('target_price')}\n"
                f"Buyer Terms: {', '.join(result.get('buyer_terms', []))}\n"
                f"Action Terms: {', '.join(result.get('action_terms', []))}"
            ),
            "metadata": {
                "domain": domain,
                "niche": niche,
                "brand_score": result.get("brand_score"),
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
            },
        },
    }