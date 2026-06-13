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

    return {
        "organization_id": organization_id,
        "source_bot": "apollo_outreach",
        "company": {
            "name": company_name,
            "website": website,
            "industry": "loans",
        },
        "contact": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "role": title,
        },
        "lead": {
            "title": f"{company_name} - buyer lead for {domain_offer['domain']}",
            "status": "drafted",
            "score": score,
            "notes": "; ".join(reasons),
            "metadata": {
                "domain": domain_offer["domain"],
                "ask_price": domain_offer.get("ask_price"),
                "email_subject": subject,
                "email_body": body,
                "apollo_score_reasons": reasons,
            },
        },
    }