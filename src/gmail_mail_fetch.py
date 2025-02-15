import base64
import logging
from datetime import datetime

from googleapiclient.discovery import build

from models.email import Email, db
from utils import authenticate_gmail
from database import db, setup_database

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_emails_and_store():
    try:
        num_messages = int(
            input("Enter the number of latest messages to fetch: "))

        logging.info(
            f"Fetching the latest {num_messages} messages from Gmail...")

        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)
        results = service.users().messages().list(
            userId="me", maxResults=num_messages).execute()
        messages = results.get("messages", [])

        db.connect()
        logging.info("Storing messages...")

        for message in messages:
            try:
                logging.info(f"Storing message ID: {message['id']} locally")
                msg = service.users().messages().get(
                    userId="me", id=message["id"]).execute()
                headers = msg["payload"].get("headers", [])
                subject = snippet = sender = ""
                received_at = datetime.fromtimestamp(
                    int(msg["internalDate"]) / 1000)

                for header in headers:
                    if header["name"] == "From":
                        sender = header["value"]
                    if header["name"] == "Subject":
                        subject = header["value"]

                snippet = msg.get("snippet", "")
                body = ""
                if "parts" in msg["payload"]:
                    for part in msg["payload"]["parts"]:
                        if part.get("mimeType") == "text/plain":
                            try:
                                body = base64.urlsafe_b64decode(
                                    part["body"]["data"]).decode("utf-8")
                                break
                            except Exception as e:
                                logging.error(
                                    f"Error decoding email body for message {message['id']}: {e}")

                Email.insert(id=message["id"], sender=sender, subject=subject, snippet=snippet,
                             body=body, received_at=received_at).on_conflict_ignore().execute()
            except Exception as e:
                logging.error(f"Error processing message {message['id']}: {e}")

        db.close()
        logging.info("Messages processed successfully.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    setup_database()
    fetch_emails_and_store()
    logging.info("Emails fetched from Gmail and stored locally.")
