import os
from urllib.parse import urlparse

from core.crm_client import CRMClient
from services.devspace_outreach.adapter import outreach_audit_to_crm_payload
from services.devspace_outreach.auditor import audit_prospects
from services.devspace_outreach.discovery import discover_prospects
from services.devspace_outreach.niche_config import load_niche_config
from services.devspace_outreach.signals import load_prospects, prospect_issue_keys


def clamp_score(value):
    try:
        return max(0, min(100, int(value)))
    except Exception:
        return 0


def as_bool(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).lower().strip() not in {"0", "false", "no", "off"}


def score_prospect(prospect: dict, niche_config: dict) -> tuple[int, list[dict]]:
    explicit_score = (
        prospect.get("score")
        or prospect.get("audit_score")
        or prospect.get("lead_score")
    )

    issue_keys = prospect_issue_keys(prospect)
    matched = []
    score = 0

    for pain_point in niche_config.get("pain_points", []):
        scan_keys = set(pain_point.get("scan_for") or [])
        keys = {pain_point.get("key"), pain_point.get("label")}
        keys.update(scan_keys)
        keys = {str(key) for key in keys if key}
        matched_scan_keys = sorted(issue_keys.intersection(keys))

        if matched_scan_keys:
            weight = int(pain_point.get("weight", 0))
            score += weight
            findings = [
                finding
                for finding in prospect.get("audit", {}).get("findings", [])
                if finding.get("key") in matched_scan_keys
            ]
            matched.append({
                "key": pain_point.get("key"),
                "label": pain_point.get("label"),
                "weight": weight,
                "matched_signals": matched_scan_keys,
                "findings": findings,
            })

    if explicit_score is not None:
        score = max(score, clamp_score(explicit_score))

    return clamp_score(score), matched


def top_specific_findings(prospect: dict, limit: int = 3) -> list[dict]:
    findings = prospect.get("audit", {}).get("findings") or prospect.get("findings") or []

    if not isinstance(findings, list):
        return []

    priority = {
        "conversion": 0,
        "local_seo": 1,
        "trust": 2,
        "performance": 3,
        "technical": 4,
    }
    evidence_backed = [
        finding
        for finding in findings
        if isinstance(finding, dict)
        and finding.get("status", "weakness") == "weakness"
        and finding.get("evidence")
        and finding.get("label")
    ]

    return sorted(
        evidence_backed,
        key=lambda finding: (
            priority.get(finding.get("category"), 99),
            str(finding.get("label", "")),
        ),
    )[:limit]


def finding_email_phrase(finding: dict) -> str:
    label = str(finding.get("label") or "website issue").lower()
    evidence = str(finding.get("evidence") or "").strip().rstrip(".")

    if evidence:
        return f"{label}: {evidence}"

    return label


def render_email(niche_config: dict, prospect: dict) -> tuple[str, str]:
    email = niche_config.get("email", {})
    company_name = (
        prospect.get("company_name")
        or prospect.get("company")
        or prospect.get("name")
        or prospect.get("business_name")
        or "your business"
    )
    location = prospect.get("location") or "your area"
    values = {
        "company_name": company_name,
        "location": location,
    }

    subject = (email.get("subject") or "Quick website note for {company_name}").format(**values)
    findings = top_specific_findings(prospect, limit=3)

    if findings:
        examples = [finding_email_phrase(finding) for finding in findings[:2]]
        finding_sentence = "; and ".join(examples)
        body_parts = [
            (
                f"I noticed a couple of fixable website issues on {company_name}'s site "
                f"that may be costing appointment requests. For example, {finding_sentence}."
            ),
            (
                "These are the kinds of local SEO and appointment-conversion gaps "
                "that can make it harder for nearby patients to find the clinic and book."
            ),
            email.get("call_to_action", "").format(**values),
        ]
    else:
        body_parts = [
            email.get("opening", "").format(**values),
            email.get("value_prop", "").format(**values),
            email.get("call_to_action", "").format(**values),
        ]
    body = "\n\n".join(part.strip() for part in body_parts if part and part.strip())

    return subject, body


def website_domain(prospect: dict) -> str:
    website = prospect.get("website") or prospect.get("url") or prospect.get("domain") or ""
    parsed = urlparse(website)
    host = parsed.netloc or parsed.path
    return host.lower().removeprefix("www.")


def should_auto_discover(config: dict, prospects: list[dict]) -> bool:
    if "auto_discover" in config:
        return as_bool(config.get("auto_discover"), default=True)

    return not prospects


def should_audit(config: dict) -> bool:
    return as_bool(config.get("audit_websites"), default=True)


def dedupe_prospects(prospects: list[dict]) -> list[dict]:
    deduped = []
    seen = set()

    for prospect in prospects:
        key = website_domain(prospect) or (
            prospect.get("company_name")
            or prospect.get("company")
            or prospect.get("name")
            or ""
        ).lower().strip()

        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(prospect)

    return deduped


def run(organization_id: str, niche: str | None = None, signals=None, config=None):
    config = config or {}
    niche = niche or config.get("niche") or "chiropractors"
    organization_id = organization_id or os.getenv("DEVSPACE_OUTREACH_ORG_ID")

    if not organization_id:
        raise ValueError("DEVSPACE_OUTREACH_ORG_ID is missing from .env")

    niche_config = load_niche_config(niche)
    prospects = load_prospects(signals=signals, config=config)

    if should_auto_discover(config, prospects):
        discovered = discover_prospects(niche_config=niche_config, config=config)
        prospects.extend(discovered)
        prospects = dedupe_prospects(prospects)
        print(f"Discovered prospects: {len(discovered)}")

    if not prospects:
        print(f"No Devspace Outreach prospects found for niche: {niche}")
        print("Add search provider credentials, service config prospects, or CRM domain signals before running.")
        return

    if should_audit(config):
        prospects = audit_prospects(prospects, config=config)

    scoring = niche_config.get("scoring", {})
    min_score_to_save = int(config.get("min_score_to_save", scoring.get("min_score_to_save", 60)))
    max_ingests = int(config.get("max_ingests", 50))
    dry_run = as_bool(config.get("dry_run"), default=False)

    selected = []

    for prospect in prospects:
        score, matched_pain_points = score_prospect(prospect, niche_config)

        if score < min_score_to_save:
            continue

        subject, body = render_email(niche_config, prospect)
        selected.append({
            "prospect": prospect,
            "score": score,
            "matched_pain_points": matched_pain_points,
            "subject": subject,
            "body": body,
        })

        if len(selected) >= max_ingests:
            break

    print(f"Devspace Outreach niche: {niche}")
    print(f"Prospects loaded: {len(prospects)}")
    print(f"Prospects selected: {len(selected)}")

    if dry_run:
        print("Dry run enabled; no leads sent to CRM.")
        return

    if not selected:
        print("No leads sent to CRM.")
        return

    crm = CRMClient()
    sent_to_crm = 0
    existing_updated = 0
    update_existing_clients = as_bool(config.get("update_existing_clients"), default=True)

    for result in selected:
        domain = website_domain(result["prospect"])
        exists_response = {}

        if domain:
            exists_response = crm.domain_exists(
                organization_id=organization_id,
                domain=domain,
            )

            if exists_response.get("exists") and not update_existing_clients:
                print(f"Skipping duplicate website: {domain}")
                continue

        payload = outreach_audit_to_crm_payload(
            organization_id=organization_id,
            niche_config=niche_config,
            prospect=result["prospect"],
            score=result["score"],
            matched_pain_points=result["matched_pain_points"],
            subject=result["subject"],
            body=result["body"],
        )

        if exists_response.get("exists"):
            payload["ingest_mode"] = "update_existing"
            payload["metadata"]["ingest_mode"] = "update_existing"
            payload["metadata"]["existing_client"] = True
            payload["metadata"]["existing_match"] = exists_response

        crm.ingest_lead(payload)
        sent_to_crm += 1

        company_name = payload["company"]["name"] or payload["company"]["website"]
        if exists_response.get("exists"):
            existing_updated += 1
            print(f"Updated CRM: {company_name} | Score: {result['score']}")
        else:
            print(f"Sent to CRM: {company_name} | Score: {result['score']}")

    print(f"Sent {sent_to_crm} Devspace Outreach leads to CRM")
    if existing_updated:
        print(f"Existing CRM clients refreshed: {existing_updated}")
