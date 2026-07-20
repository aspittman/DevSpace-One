from core.email_sender import send_email


def _outreach_items(response) -> list[dict]:
    if isinstance(response, list):
        return response

    if not isinstance(response, dict):
        raise ValueError("Approved outreach response must be an object or list")

    for key in ("outreach", "approved_outreach", "messages", "items", "data"):
        items = response.get(key)

        if isinstance(items, list):
            return items

    return []


def _required(item: dict, *keys: str):
    for key in keys:
        value = item.get(key)

        if value is not None and str(value).strip():
            return value

    raise ValueError(f"Approved outreach is missing {keys[0]}")


def _score(item: dict) -> float:
    candidates = [
        item.get("score"),
        item.get("lead_score"),
        (item.get("lead") or {}).get("score") if isinstance(item.get("lead"), dict) else None,
        (item.get("metadata") or {}).get("score") if isinstance(item.get("metadata"), dict) else None,
        (item.get("metadata") or {}).get("apollo_score") if isinstance(item.get("metadata"), dict) else None,
    ]
    for value in candidates:
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def send_approved_outreach(crm, organization_id=None, max_sent=1) -> dict[str, int]:
    """Send at most ``max_sent`` approved messages and acknowledge SMTP successes.

    Failed or malformed queue entries do not consume the limit, so the sender can
    skip bad entries while still delivering one valid message per service run.
    """
    if max_sent is not None and max_sent < 1:
        raise ValueError("max_sent must be at least 1 or None")

    response = crm.get_approved_outreach(organization_id=organization_id)
    items = sorted(_outreach_items(response), key=_score, reverse=True)
    sent = 0
    failed = 0

    for item in items:
        try:
            outreach_id = _required(item, "outreach_id", "id")
            to_email = _required(item, "to_email", "email", "recipient_email", "to")
            subject = _required(item, "subject", "email_subject")
            body = _required(item, "body", "email_body")

            if not send_email(str(to_email), str(subject), str(body)):
                failed += 1
                continue

            crm.mark_outreach_sent(
                outreach_id=outreach_id,
                organization_id=organization_id or item.get("organization_id"),
            )
            sent += 1

            if max_sent is not None and sent >= max_sent:
                break
        except Exception as exc:
            failed += 1
            item_id = item.get("outreach_id") or item.get("id") or "unknown"
            print(f"Failed to send approved outreach {item_id}: {exc}")

    print(f"Approved outreach: {sent} sent, {failed} failed, {len(items)} polled")
    return {"polled": len(items), "sent": sent, "failed": failed}
