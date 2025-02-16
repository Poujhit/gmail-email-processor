import json
import unittest
from unittest.mock import patch, MagicMock
from process_mail import process_emails_based_on_rules
from db_utils import get_or_initialize_db, Email


class TestProcessEmails(unittest.TestCase):

    @patch("process_mail.authenticate_gmail")
    @patch("process_mail.build")
    def test_process_emails_based_on_rules(self, mock_build, mock_authenticate):
        # Initialize test database
        db = get_or_initialize_db(testing=True)

        # Ensure connection is open
        if db.is_closed():
            db.connect(reuse_if_open=True)
        db.create_tables([Email], safe=True)

        # Cleanup any previous test data
        Email.delete().where(Email.id == "123").execute()

        # Mock authentication
        mock_credentials = MagicMock()
        mock_authenticate.return_value = mock_credentials
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Insert mock email into the database safely
        test_email, created = Email.get_or_create(
            id="123",
            defaults={
                "sender": "test@example.com",
                "subject": "Test Email",
                "body": "Test body",
                "received_at": "2025-02-16 12:00:00",
            }
        )

        if not created:
            print("Test email already exists, skipping insertion.")
        else:
            test_email.save()  # 🔥 Force save & commit

        db.commit()  # 🔥 Ensure changes persist

        # Verify email exists
        assert Email.select().where(Email.id == "123").exists(
        ), "Test email was not inserted into the database."

        # Define rules for processing
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

        # Fetch updated email
        updated_email = Email.get_or_none(
            Email.id == "123")  # 🔥 Avoid exceptions

        self.assertIsNotNone(
            updated_email, "Email record was deleted or not found!")
        self.assertEqual(updated_email.subject, "Test Email")

        # Verify Gmail API call to modify labels
        mock_service.users().messages().modify.assert_called_once_with(
            userId="me", id="123", body={"removeLabelIds": ["UNREAD"]}
        )

        # Cleanup database
        Email.delete().execute()
        db.close()


if __name__ == "__main__":
    unittest.main()
