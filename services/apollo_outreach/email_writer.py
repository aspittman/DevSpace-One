from services.apollo_outreach.domain_analyzer import detect_domain_angle


def build_subject(domain_offer: dict) -> str:
    domain = domain_offer["domain"]
    angle = detect_domain_angle(domain)

    if angle == "commercial_loans":
        return f"Commercial finance domain: {domain}"

    if angle == "equipment_financing":
        return f"Equipment financing domain: {domain}"

    if angle == "business_funding":
        return f"Business funding domain: {domain}"

    return f"Domain idea: {domain}"


def build_email(lead: dict, domain_offer: dict) -> str:
    first_name = lead.get("first_name") or lead.get("First Name") or ""
    company = lead.get("company") or lead.get("Company") or "your company"
    domain = domain_offer["domain"]
    price = domain_offer.get("ask_price", "299")

    greeting = f"Hi {first_name}," if first_name else "Hi,"

    return f"""{greeting}

I came across {company} and thought {domain} could be a strong fit for a lending, funding, or commercial finance brand.

The name is direct, easy to understand, and tied to people already searching for funding options.

I currently own {domain} and would be open to selling it for ${price}.

No pressure either way — just thought it could be useful for a future campaign, landing page, or brand asset.

Thanks,
Aaron"""