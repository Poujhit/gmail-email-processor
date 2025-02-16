import unittest
from unittest.mock import patch, MagicMock
from gmail_mail_fetch import fetch_emails_and_store
from db_utils import get_or_initialize_db, Email


class TestFetchEmailsIntegration(unittest.TestCase):
    @patch("gmail_mail_fetch.authenticate_gmail")
    @patch("gmail_mail_fetch.build")
    @patch("gmail_mail_fetch.input", return_value="2")
    def test_fetch_emails_and_store_integration(self, mock_input, mock_build, mock_auth):
        # Initialize test database
        db = get_or_initialize_db(testing=True)

        # Ensure the connection is open
        if db.is_closed():
            db.connect(reuse_if_open=True)
        db.create_tables([Email], safe=True)

        # Mock authentication
        mock_creds = MagicMock()
        mock_auth.return_value = mock_creds

        # Mock Gmail API service
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {
            "messages": [
                {"id": "12345"},
                {"id": "67890"}
            ]
        }

        # Mock individual message response
        mock_service.users().messages().get().execute.side_effect = [
            {
                "id": "12345",
                "internalDate": "1700000000000",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "Sender <sender@example.com>"},
                        {"name": "Subject", "value": "Test Subject"}
                    ],
                    "parts": [{
                        "mimeType": "text/plain",
                        "body": {"data": "VGhpcyBpcyBhIHRlc3QgbWVzc2FnZQ=="}
                    }]
                }
            },
            {
                "id": "67890",
                "internalDate": "1700000000000",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "Another Sender <another@example.com>"},
                        {"name": "Subject", "value": "Another Test"}
                    ],
                    "parts": [{
                        "mimeType": "text/plain",
                        "body": {"data": "QW5vdGhlciB0ZXN0IG1lc3NhZ2U="}
                    }]
                }
            }
        ]

        # Run function
        fetch_emails_and_store(testing=True)

        # Verify database entries
        stored_emails = list(Email.select())
        self.assertEqual(len(stored_emails), 2)
        self.assertEqual(stored_emails[0].sender, "sender@example.com")
        self.assertEqual(stored_emails[0].subject, "Test Subject")
        self.assertEqual(stored_emails[1].sender, "another@example.com")
        self.assertEqual(stored_emails[1].subject, "Another Test")

        # Cleanup test data (without dropping tables)
        Email.delete().execute()
        db.close()


if __name__ == "__main__":
    unittest.main()
