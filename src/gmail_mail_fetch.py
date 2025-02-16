import base64
import logging
from datetime import datetime
import re
from googleapiclient.discovery import build

from utils import authenticate_gmail
from db_utils import get_or_initialize_db, Email


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_emails_and_store(testing=False):
    """
    Fetches the latest emails from Gmail and stores them in a local database efficiently.

    Args:
        testing (bool): If True, uses a test database.

    What this function does:
    - Initialize the database.
    - Prompt the user for the number of emails to fetch.
    - Authenticate with Gmail API.
    - Retrieve email metadata and full email content.
    - Extract relevant details (sender, subject, received timestamp, and body).
    - Store emails in the database using a bulk insert, ignoring duplicates.
    - Handle errors gracefully and log them.
    - Close the database connection.
    """
    try:
        db = get_or_initialize_db(testing=testing)
        num_messages = int(
            input("Enter the number of latest messages to fetch: "))

        logging.info(
            f"Fetching the latest {num_messages} messages from Gmail...")

        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(
            userId="me", maxResults=num_messages).execute()
        messages = results.get("messages", [])

        logging.info("Processing and storing messages...")

        emails_to_insert = []  # Bulk insert list

        for message in messages:
            try:
                logging.info(f"Fetching message ID: {message['id']}")
                msg = service.users().messages().get(
                    userId="me", id=message["id"]).execute()

                # Extract headers
                headers = msg["payload"].get("headers", [])
                subject, sender = "", ""
                received_at = datetime.fromtimestamp(
                    int(msg["internalDate"]) / 1000)

                for header in headers:
                    if header["name"] == "From":
                        sender_match = re.search(r"<(.+?)>", header["value"])
                        sender = sender_match.group(
                            1) if sender_match else header["value"]
                    elif header["name"] == "Subject":
                        subject = header["value"]

                # Extract plain-text email body
                body = ""
                if "parts" in msg["payload"]:
                    for part in msg["payload"]["parts"]:
                        if part.get("mimeType") == "text/plain":
                            try:
                                body = base64.urlsafe_b64decode(
                                    part["body"]["data"]).decode("utf-8")
                                break  # Stop after decoding the first plain-text part
                            except Exception as e:
                                logging.error(
                                    f"Error decoding email body for message {message['id']}: {e}")

                # Collect email data for bulk insert
                emails_to_insert.append({
                    "id": message["id"],
                    "sender": sender,
                    "subject": subject,
                    "body": body,
                    "received_at": received_at
                })

            except Exception as e:
                logging.error(f"Error processing message {message['id']}: {e}")

        # Perform bulk insert if emails were fetched
        if emails_to_insert:
            logging.info("Bulk inserting emails into the database")
            Email.insert_many(emails_to_insert).on_conflict_ignore().execute()
            logging.info(
                f"Inserted {len(emails_to_insert)} emails into the database.")

        db.close()
        logging.info("Emails processed successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    fetch_emails_and_store()
    logging.info("Emails fetched from Gmail and stored locally.")
