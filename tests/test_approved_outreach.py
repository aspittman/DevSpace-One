import unittest
from unittest.mock import patch

from core.approved_outreach import send_approved_outreach


class FakeCRM:
    def __init__(self, response):
        self.response = response
        self.sent = []

    def get_approved_outreach(self, organization_id=None):
        return self.response

    def mark_outreach_sent(self, outreach_id, organization_id=None):
        self.sent.append((outreach_id, organization_id))


class ApprovedOutreachTests(unittest.TestCase):
    @patch("core.approved_outreach.send_email", return_value=True)
    def test_sends_and_acknowledges_approved_message(self, send_email):
        crm = FakeCRM({
            "outreach": [{
                "id": "outreach-1",
                "to_email": "buyer@example.com",
                "subject": "A domain for you",
                "body": "Hello",
            }]
        })

        result = send_approved_outreach(crm, organization_id="org-1")

        send_email.assert_called_once_with(
            "buyer@example.com", "A domain for you", "Hello"
        )
        self.assertEqual(crm.sent, [("outreach-1", "org-1")])
        self.assertEqual(result, {"polled": 1, "sent": 1, "failed": 0})

    @patch("core.approved_outreach.send_email", return_value=False)
    def test_does_not_acknowledge_when_email_is_disabled(self, send_email):
        crm = FakeCRM({
            "approved_outreach": [{
                "outreach_id": "outreach-2",
                "email": "buyer@example.com",
                "email_subject": "Subject",
                "email_body": "Body",
            }]
        })

        result = send_approved_outreach(crm)

        self.assertEqual(crm.sent, [])
        self.assertEqual(result, {"polled": 1, "sent": 0, "failed": 1})

    @patch("core.approved_outreach.send_email", side_effect=RuntimeError("SMTP down"))
    def test_failure_does_not_prevent_one_later_success(self, send_email):
        crm = FakeCRM({
            "items": [
                {"id": "bad", "to": "a@example.com", "subject": "A", "body": "A"},
                {"id": "good", "to": "b@example.com", "subject": "B", "body": "B"},
            ]
        })
        send_email.side_effect = [RuntimeError("SMTP down"), True]

        result = send_approved_outreach(crm)

        self.assertEqual(crm.sent, [("good", None)])
        self.assertEqual(result, {"polled": 2, "sent": 1, "failed": 1})

    @patch("core.approved_outreach.send_email", return_value=True)
    def test_stops_after_one_successful_delivery(self, send_email):
        crm = FakeCRM({
            "items": [
                {"id": "first", "to": "a@example.com", "subject": "A", "body": "A"},
                {"id": "second", "to": "b@example.com", "subject": "B", "body": "B"},
            ]
        })

        result = send_approved_outreach(crm)

        send_email.assert_called_once_with("a@example.com", "A", "A")
        self.assertEqual(crm.sent, [("first", None)])
        self.assertEqual(result, {"polled": 2, "sent": 1, "failed": 0})

    @patch("core.approved_outreach.send_email", return_value=True)
    def test_sends_highest_scored_approved_message_first(self, send_email):
        crm = FakeCRM({"items": [
            {"id": "lower", "to": "low@example.com", "subject": "Low", "body": "Low", "score": 71},
            {"id": "higher", "to": "high@example.com", "subject": "High", "body": "High", "lead": {"score": 94}},
        ]})

        send_approved_outreach(crm)

        send_email.assert_called_once_with("high@example.com", "High", "High")
        self.assertEqual(crm.sent, [("higher", None)])


if __name__ == "__main__":
    unittest.main()
