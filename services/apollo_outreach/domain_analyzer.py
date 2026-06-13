def clean_domain(domain: str) -> str:
    return (
        str(domain or "")
        .lower()
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .strip()
    )


def domain_base(domain: str) -> str:
    return clean_domain(domain).replace(".com", "")


def detect_domain_angle(domain: str) -> str:
    name = domain_base(domain)

    if "commercial" in name or "bridge" in name:
        return "commercial_loans"

    if "equipment" in name or "truck" in name:
        return "equipment_financing"

    if "business" in name or "funding" in name or "workingcapital" in name:
        return "business_funding"

    if "loanbroker" in name or "loanbrokers" in name:
        return "loan_brokers"

    return "general_lending"