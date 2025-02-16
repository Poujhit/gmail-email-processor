import json
import os
import sys
import logging
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from utils import authenticate_gmail
from db_utils import Email, get_or_initialize_db
from peewee import DateTimeField
from functools import reduce
import operator

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# def load_rules():
#     logging.info("Loading rules from rules.json")
#     with open("rules.json", "r") as file:
#         return json.load(file)

def process_emails_based_on_rules(rules_path, testing=False):
    logging.info(
        f"Starting to process emails based on rules from {rules_path}")
    try:
        db = get_or_initialize_db(testing=testing)
        logging.info("Database connection established")
        with open(rules_path, "r") as rules_file:
            rules = json.load(rules_file)
        logging.info("Rules loaded successfully")

        creds = authenticate_gmail()
        service = build("gmail", "v1", credentials=creds)

        for rule in rules.get("rules", []):
            logging.info(f"Applying rule: {rule}")
            predicate = rule["predicate"]
            conditions = rule["conditions"]
            actions = rule["actions"]

            query = Email.select()
            condition_list = []

            for condition in conditions:
                field, pred, value = condition["field"], condition["predicate"], condition["value"]
                logging.info(f"Processing condition: {condition}")

                if hasattr(Email, field):
                    field_attr = getattr(Email, field)

                    if isinstance(Email._meta.fields[field], DateTimeField):
                        value = int(value)
                        delta = timedelta(
                            days=value *
                            30 if condition.get("unit") == "months" else value
                        )
                        compare_date = datetime.now() - delta

                        if pred == "less_than":
                            condition_list.append(field_attr > compare_date)
                        elif pred == "greater_than":
                            condition_list.append(field_attr < compare_date)

                    else:
                        if pred == "contains":
                            condition_list.append(field_attr.contains(value))
                        elif pred == "equals":
                            condition_list.append(field_attr == value)
                        elif pred == "not_equals":
                            condition_list.append(field_attr != value)
                        elif pred == "not_contains":
                            condition_list.append(~field_attr.contains(value))

            # Apply predicates conditons: All (AND), Any (OR)
            if condition_list:
                if predicate == "All":
                    query = query.where(*condition_list)
                elif predicate == "Any":
                    query = query.where(reduce(operator.or_, condition_list))

            # Apply actions to emails
            for email in query:
                logging.info(
                    f"Processing email {email.id} for rule actions...")
                for action in actions:
                    logging.info(
                        f"Applying action: {action} to email {email.id}")

                    if action == "mark_as_read":
                        service.users().messages().modify(
                            userId="me", id=email.id, body={"removeLabelIds": ["UNREAD"]}
                        ).execute()

                    elif action == "mark_as_unread":
                        service.users().messages().modify(
                            userId="me", id=email.id, body={"addLabelIds": ["UNREAD"]}
                        ).execute()

                    elif action.startswith("move_to_"):
                        label_name = action.replace("move_to_", "")
                        labels = service.users().labels().list(userId="me").execute().get("labels", [])
                        label_id = next(
                            (lbl["id"] for lbl in labels if lbl["name"].lower(
                            ) == label_name.lower()), None
                        )
                        if label_id:
                            service.users().messages().modify(
                                userId="me", id=email.id, body={"addLabelIds": [label_id]}
                            ).execute()

                    elif action == "flag_message":
                        service.users().messages().modify(
                            userId="me", id=email.id, body={"addLabelIds": ["STARRED"]}
                        ).execute()

                    else:
                        logging.warning(f"Unknown action: {action}")

        db.close()
        logging.info("Database connection closed successfully")

    except Exception as e:
        logging.error(f"Error processing emails based on rules: {e}")
        db.close()
        logging.info("Database connection closed due to error")


if __name__ == "__main__":
    rules_path = input("Enter the path to the rules.json file: ")
    if not os.path.isfile(rules_path):
        logging.error("Invalid rules file path. Please provide a valid path.")
        sys.exit(1)

    process_emails_based_on_rules(rules_path)
    logging.info("Emails processed successfully based on rules.")
