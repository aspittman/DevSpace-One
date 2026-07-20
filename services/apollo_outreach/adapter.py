from urllib.parse import urlparse


def _clean(value) -> str:
    return str(value or "").strip()


def _email(value) -> str | None:
    email = _clean(value)

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return None

    return email


def _url(value) -> str | None:
    raw = _clean(value)

    if not raw:
        return None

    candidate = raw if "://" in raw else f"https://{raw}"
    parsed = urlparse(candidate)

    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None

    return candidate


def _domain(value) -> str:
    raw = _clean(value)

    if not raw:
        return ""

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    return parsed.netloc or raw


def outreach_result_to_crm_payload(
    organization_id: str,
    lead: dict,
    domain_offer: dict,
    score: int,
    reasons: list[str],
    subject: str,
    body: str,
):
    website = _url(lead.get("website") or lead.get("Website"))
    company_domain = _domain(website)
    email = _email(lead.get("email") or lead.get("Email"))
    first_name = _clean(lead.get("first_name") or lead.get("First Name"))
    last_name = _clean(lead.get("last_name") or lead.get("Last Name"))
    title = _clean(lead.get("title") or lead.get("Title"))
    domain = domain_offer["domain"]
    ask_price = domain_offer.get("ask_price")

    if not email:
        raise ValueError("Apollo outreach lead is missing a valid email")

    company_name = (
        _clean(lead.get("company") or lead.get("Company"))
        or company_domain
        or email
        or domain
    )

    linkedin_url = _url(lead.get("linkedin_url") or lead.get("LinkedIn"))
    contact = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "role": title,
    }

    if linkedin_url:
        contact["linkedin_url"] = linkedin_url

    return {
        "organization_id": organization_id,
        "source_bot": "apollo_outreach",
        "company": {
            "name": company_name,
            "website": website,
            "domain": company_domain or domain,
            "industry": domain_offer.get("niche") or "loans",
        },
        "contact": contact,
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
            "email_to": email,
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
