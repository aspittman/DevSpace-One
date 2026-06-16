import os
from core.email_sender import send_email


def send_domain_alert(results):
    lines = ["Domain Merchant found these candidates:", ""]

    for r in results:
        lines.append(
            f"- {r['domain']} | Score: {r['score']} | Target: ${r['target_price']}"
        )

    body = "\n".join(lines)

    return send_email(
        to_email=os.getenv("ALERT_TO_EMAIL"),
        subject="Domain Merchant Alert",
        body=body,
    )