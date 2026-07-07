def _lead_value(lead: dict, *keys: str) -> str:
    for key in keys:
        value = str(lead.get(key) or "").strip()
        if value:
            return value
    return ""


def _domain_url(domain: str) -> str:
    domain = str(domain or "").strip()
    if domain.startswith(("http://", "https://")):
        return domain
    return f"https://{domain}"


def build_subject(domain_offer: dict) -> str:
    domain = domain_offer["domain"]
    return f"Domain opportunity: {domain}"


def build_subject_for_lead(lead: dict, domain_offer: dict) -> str:
    company = _lead_value(lead, "company", "Company")

    if company:
        return f"Domain opportunity for {company}"

    return build_subject(domain_offer)


def build_email(lead: dict, domain_offer: dict) -> str:
    first_name = _lead_value(lead, "first_name", "First Name")
    company = _lead_value(lead, "company", "Company") or "your company"
    domain = domain_offer["domain"]
    url = _domain_url(domain)

    greeting = f"Hi {first_name}," if first_name else "Hi,"

    return f"""{greeting}

I noticed {company} focuses on helping businesses find financing, and I thought {domain} would be a strong fit for your brand.

The name is easy to remember, clearly communicates what you do, and closely matches the kinds of search terms potential customers already use when looking for lending services.

I own the domain, and it's currently listed for sale through Afternic, one of the largest domain marketplaces. You can view the listing by visiting:

{url}

If the domain is a good fit for your plans, the landing page will guide you through the purchase process.

I'm reaching out to a small number of companies that seem like a natural fit before marketing it more broadly.

If you have any questions, or if you'd like to discuss the domain directly, feel free to reply to this email.

Best,

Aaron Pittman
DevSpace Technologies"""
