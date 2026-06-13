def afternic_result_to_crm_payload(result: dict, organization_id: str) -> dict:
    domain = result["domain"]

    score = 100 if result["outcome"] == "sold" else 50

    return {
        "organization_id": organization_id,
        "source_bot": "afternic_sync",
        "company": {
            "name": domain,
            "domain": domain,
            "website": None,
            "industry": "domain_sales",
        },
        "contact": None,
        "lead": {
            "lead_type": "domain_marketplace_update",
            "score": score,
            "summary": f"Afternic marketplace update for {domain}",
            "pain_points": [],
        },
        "metadata": {
            "domain": domain,
            "marketplace": "afternic",
            "status": result.get("status"),
            "outcome": result.get("outcome"),
            "sale_price": result.get("sale_price"),
            "list_price": result.get("list_price"),
            "floor_price": result.get("floor_price"),
            "sale_date": result.get("sale_date"),
            "listed_date": result.get("listed_date"),
            "views": result.get("views"),
            "raw": result.get("raw"),
        },
    }