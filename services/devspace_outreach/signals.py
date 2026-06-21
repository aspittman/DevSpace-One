def as_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def prospect_key(prospect: dict) -> str:
    website = prospect.get("website") or prospect.get("url") or prospect.get("domain")

    if website:
        return f"website:{str(website).lower().strip()}"

    return "|".join([
        str(
            prospect.get("company_name")
            or prospect.get("company")
            or prospect.get("name")
            or prospect.get("business_name")
            or ""
        ).lower().strip(),
        str(prospect.get("location") or "").lower().strip(),
    ])


def _normalize_prospect(row: dict) -> dict | None:
    if not isinstance(row, dict):
        return None

    company_name = (
        row.get("company_name")
        or row.get("company")
        or row.get("name")
        or row.get("business_name")
    )
    website = row.get("website") or row.get("url") or row.get("domain")

    if not company_name and not website:
        return None

    prospect = dict(row)

    if company_name:
        prospect["company_name"] = company_name

    if website:
        prospect["website"] = website

    return prospect


def _rows_from_payload(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload

    if not isinstance(payload, dict):
        return []

    for key in ("prospects", "leads", "companies", "signals", "items", "domains"):
        rows = payload.get(key)

        if isinstance(rows, list):
            return rows

    return []


def load_prospects(signals=None, config=None) -> list[dict]:
    rows = []
    config = config or {}

    rows.extend(_rows_from_payload(config))
    rows.extend(_rows_from_payload(signals))

    prospects = []
    seen = set()

    for row in rows:
        prospect = _normalize_prospect(row)

        if not prospect:
            continue

        key = prospect_key(prospect)

        if key in seen:
            continue

        seen.add(key)
        prospects.append(prospect)

    return prospects


def prospect_issue_keys(prospect: dict) -> set[str]:
    issues = set()

    for key in ("pain_points", "issues", "scan_for", "detected_issues"):
        issues.update(str(item) for item in as_list(prospect.get(key)))

    scan_results = prospect.get("scan_results") or prospect.get("audit") or {}

    if isinstance(scan_results, dict):
        for key, value in scan_results.items():
            if value:
                issues.add(str(key))

    for key, value in prospect.items():
        if isinstance(value, bool) and value:
            issues.add(str(key))

    return {issue.strip() for issue in issues if issue and issue.strip()}
