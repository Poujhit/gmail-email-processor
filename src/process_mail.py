import json
import os
import sys
import logging
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from utils import authenticate_gmail
from db_utils import db, Email
from peewee import DateTimeField


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_rules():
    with open("rules.json", "r") as file:
        return json.load(file)


def process_emails_based_on_rules(rules_path):
    try:
        with open(rules_path, "r") as rules_file:
            rules = json.load(rules_file)

        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)
        db.connect()

        for rule in rules["rules"]:
            logging.info(f"Applying rule: {rule}")
            predicate = rule["predicate"]
            conditions = rule["conditions"]
            actions = rule["actions"]

            query = Email.select()
            condition_list = []
            for condition in conditions:
                field, pred, value = condition["field"], condition["predicate"], condition["value"]

                if hasattr(Email, field):
                    field_attr = getattr(Email, field)

                    if isinstance(field_attr, DateTimeField):
                        value = int(value)
                        delta = timedelta(
                            days=value * 30 if condition.get("unit") == "months" else value)

                        if pred == "less_than":
                            condition_list.append(
                                (datetime.now() - field_attr) < delta)
                        elif pred == "greater_than":
                            condition_list.append(
                                (datetime.now() - field_attr) > delta)
                    else:
                        if pred == "contains":
                            condition_list.append(field_attr.contains(value))
                        elif pred == "equals":
                            condition_list.append(field_attr == value)

            if predicate == "All":
                query = query.where(*condition_list)
            elif predicate == "Any":
                query = query.where(any(condition_list))

            for email in query:
                logging.info(
                    f"Processing email {email.id} for rule actions...")
                for action in actions:
                    logging.info(
                        f"Applying action: {action} to email {email.id}")
                    if action == "mark_as_read":
                        service.users().messages().modify(userId="me", id=email.id,
                                                          body={"removeLabelIds": ["UNREAD"]}).execute()
                    elif action == "mark_as_unread":
                        service.users().messages().modify(userId="me", id=email.id,
                                                          body={"addLabelIds": ["UNREAD"]}).execute()
                    elif action.startswith("move_to_"):
                        label_name = action.replace("move_to_", "")
                        labels = service.users().labels().list(userId="me").execute().get("labels", [])
                        label_id = next(
                            (lbl["id"] for lbl in labels if lbl["name"].lower() == label_name.lower()), None)
                        if label_id:
                            service.users().messages().modify(userId="me", id=email.id,
                                                              body={"addLabelIds": [label_id]}).execute()
                    elif action == "flag_message":
                        service.users().messages().modify(userId="me", id=email.id,
                                                          body={"addLabelIds": ["STARRED"]}).execute()

        db.close()
    except Exception as e:
        logging.error(f"Error processing emails based on rules: {e}")
        db.close()


if __name__ == "__main__":
    rules_path = input("Enter the path to the rules.json file: ")
    if not os.path.isfile(rules_path):
        logging.error("Invalid rules file path. Please provide a valid path.")
        sys.exit(1)

    process_emails_based_on_rules(rules_path)
    logging.info("Emails processed successfully based on rules.")
