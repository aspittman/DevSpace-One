def outreach_result_to_crm_payload(
    organization_id: str,
    lead: dict,
    domain_offer: dict,
    score: int,
    reasons: list[str],
    subject: str,
    body: str,
):
    company_name = lead.get("company") or lead.get("Company") or ""
    website = lead.get("website") or lead.get("Website") or ""
    first_name = lead.get("first_name") or lead.get("First Name") or ""
    last_name = lead.get("last_name") or lead.get("Last Name") or ""
    email = lead.get("email") or lead.get("Email") or ""
    title = lead.get("title") or lead.get("Title") or ""
    domain = domain_offer["domain"]
    ask_price = domain_offer.get("ask_price")

    return {
        "organization_id": organization_id,
        "source_bot": "apollo_outreach",
        "company": {
            "name": company_name,
            "website": website,
            "domain": website,
            "industry": domain_offer.get("niche") or "loans",
        },
        "contact": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role": title,
            "linkedin_url": lead.get("linkedin_url") or "",
        },
        "lead": {
            "lead_type": "domain_buyer_outreach",
            "title": f"{company_name} - buyer lead for {domain}",
            "status": "drafted",
            "score": score,
            "summary": f"Drafted outreach to {company_name} for {domain}",
            "notes": "; ".join(reasons),
            "pain_points": reasons,
        },
        "metadata": {
            "domain": domain,
            "ask_price": ask_price,
            "outreach_status": "drafted",
            "outcome": "pending",
            "purchase_intent": None,
            "response_status": None,
            "email_subject": subject,
            "email_body": body,
            "apollo_score_reasons": reasons,
            "apollo_person_id": lead.get("apollo_person_id"),
            "apollo_organization_id": lead.get("apollo_organization_id"),
            "apollo_email_status": lead.get("email_status"),
            "apollo_raw": lead.get("apollo_raw"),
        },
    }
