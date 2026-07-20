from urllib.parse import urlparse


def _company_name(prospect: dict) -> str:
    return (
        prospect.get("company_name")
        or prospect.get("company")
        or prospect.get("name")
        or prospect.get("business_name")
        or ""
    )


def _website(prospect: dict) -> str:
    return prospect.get("website") or prospect.get("url") or prospect.get("domain") or ""


def _domain(prospect: dict) -> str:
    website = _website(prospect)
    parsed = urlparse(website)
    host = parsed.netloc or parsed.path
    return host.lower().removeprefix("www.")


def _contact(prospect: dict) -> dict | None:
    contact = prospect.get("contact")

    if isinstance(contact, dict):
        return {
            "first_name": contact.get("first_name") or contact.get("firstName") or "",
            "last_name": contact.get("last_name") or contact.get("lastName") or "",
            "email": contact.get("email") or prospect.get("email") or "",
            "phone": contact.get("phone") or prospect.get("phone") or "",
            "role": contact.get("role") or contact.get("title") or prospect.get("title") or "",
            "linkedin_url": contact.get("linkedin_url") or "",
        }

    email = prospect.get("email")
    phone = prospect.get("phone")
    title = prospect.get("title")

    if not any([email, phone, title]):
        return None

    return {
        "first_name": prospect.get("first_name") or "",
        "last_name": prospect.get("last_name") or "",
        "email": email or "",
        "phone": phone or "",
        "role": title or "",
        "linkedin_url": prospect.get("linkedin_url") or "",
    }


def _detailed_findings(prospect: dict) -> list[dict]:
    findings = prospect.get("audit", {}).get("findings") or prospect.get("findings") or []

    if not isinstance(findings, list):
        return []

    return [
        finding
        for finding in findings
        if isinstance(finding, dict)
        and finding.get("status", "weakness") == "weakness"
        and finding.get("label")
        and finding.get("evidence")
    ]


def _finding_note(finding: dict) -> str:
    return " | ".join(
        part
        for part in [
            finding.get("label"),
            f"Where: {finding.get('location')}" if finding.get("location") else "",
            f"Evidence: {finding.get('evidence')}" if finding.get("evidence") else "",
            f"Recommended fix: {finding.get('recommendation')}" if finding.get("recommendation") else "",
            f"Business impact: {finding.get('business_impact')}" if finding.get("business_impact") else "",
        ]
        if part
    )


def outreach_audit_to_crm_payload(
    organization_id: str,
    niche_config: dict,
    prospect: dict,
    score: int,
    matched_pain_points: list[dict],
    subject: str,
    body: str,
) -> dict:
    company_name = _company_name(prospect)
    website = _website(prospect)
    domain = _domain(prospect)
    niche_key = niche_config["key"]
    detailed_findings = _detailed_findings(prospect)
    finding_notes = [_finding_note(finding) for finding in detailed_findings]
    pain_labels = [
        finding["label"]
        for finding in detailed_findings
    ]

    return {
        "organization_id": organization_id,
        "source_bot": "devspace_outreach",
        "company": {
            "name": company_name,
            "website": website,
            "domain": domain,
            "industry": niche_key,
        },
        "contact": _contact(prospect),
        "lead": {
            "lead_type": "website_outreach",
            "title": f"{company_name} - {niche_config.get('label', niche_key)} website audit",
            "status": "drafted",
            "score": score,
            "summary": f"Drafted website audit outreach for {company_name}.",
            "notes": "\n".join(finding_notes) if finding_notes else "; ".join(pain_labels),
            "pain_points": pain_labels,
            "findings": detailed_findings,
        },
        "metadata": {
            "niche": niche_key,
            "location": prospect.get("location") or "",
            "website": website,
            "domain": domain,
            "audit": prospect.get("audit"),
            "detailed_findings": detailed_findings,
            "finding_notes": finding_notes,
            "outreach_status": "drafted",
            "outcome": "pending",
            "email_subject": subject,
            "email_body": body,
            "matched_pain_points": matched_pain_points,
            "offer": niche_config.get("offer", {}),
            "raw_prospect": prospect,
        },
    }
