from core.email_sender import send_email

def send_domain_alert(results):
    lines = []

    for r in results:
        lines.append(
            f"{r['domain']} "
            f"(Score {r['score']}) "
            f"Target ${r['target_price']}"
        )

    body = "\n".join(lines)

    send_email(
        subject="Domain Merchant Alert",
        body=body
    )