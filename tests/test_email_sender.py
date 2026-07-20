import unittest
from unittest.mock import patch

from core.email_sender import send_email


class EmailSenderTests(unittest.TestCase):
    @patch("core.email_sender.smtplib.SMTP")
    @patch.dict(
        "os.environ",
        {
            "EMAIL_ENABLED": "true",
            "SMTP_HOST": "smtp.gmail.com",
            "SMTP_PORT": "587",
            "SMTP_USER": "aaron@devspacetechnologies.com",
            "SMTP_PASSWORD": "app-password",
            "FROM_EMAIL": "domains@devspacetechnologies.com",
            "FROM_NAME": "DevSpace Technologies",
        },
        clear=True,
    )
    def test_authenticates_as_primary_account_and_sends_from_alias(self, smtp):
        result = send_email("buyer@example.com", "Subject", "Body")

        server = smtp.return_value.__enter__.return_value
        server.login.assert_called_once_with(
            "aaron@devspacetechnologies.com", "app-password"
        )
        message = server.send_message.call_args.args[0]
        self.assertEqual(
            message["From"],
            "DevSpace Technologies <domains@devspacetechnologies.com>",
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
