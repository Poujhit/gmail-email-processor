import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime
from process_mail import process_emails_based_on_rules
from db_utils import Email, get_or_initialize_db


class TestProcessEmailsIntegration(unittest.TestCase):

    @patch("process_mail.authenticate_gmail")
    @patch("process_mail.build")
    def test_process_emails_based_on_rules_integration(self, mock_build, mock_authenticate):
        # Initialize test database
        db = get_or_initialize_db(testing=True)

        # Ensure connection is open
        if db.is_closed():
            db.connect(reuse_if_open=True)
        db.create_tables([Email], safe=True)

        # Mock authentication
        mock_credentials = MagicMock()
        mock_authenticate.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Insert test email
        Email.create(
            id="123",
            sender="test@example.com",
            subject="Test Email",
            body="Test body",
            received_at=datetime.now()
        )

        # Define rules
        rules = {
            "rules": [
                {
                    "predicate": "All",
                    "conditions": [
                        {"field": "subject", "predicate": "contains", "value": "Test"}
                    ],
                    "actions": ["mark_as_read"]
                }
            ]
        }

        # Mock file reading
        with patch("builtins.open", unittest.mock.mock_open(read_data=json.dumps(rules))):
            process_emails_based_on_rules("rules.json", testing=True)

        # Validate email is unchanged
        updated_email = Email.get(Email.id == "123")
        self.assertEqual(updated_email.subject, "Test Email")

        # Verify API call for marking email as read
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me", id="123", body={"removeLabelIds": ["UNREAD"]}
        )

        # Cleanup
        Email.delete().execute()
        db.close()


if __name__ == "__main__":
    unittest.main()
