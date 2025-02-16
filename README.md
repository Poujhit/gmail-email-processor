# Gmail Email Processor

## Overview

This project fetches emails from a Gmail inbox using the Gmail API, stores them in an SQLite database, and processes them based on user-defined rules. It supports marking emails as read/unread, moving them to different labels, and flagging messages.
Have uploaded a demo video on the [HERE]()

## Features

- Authenticate and fetch emails from Gmail
- Store email details (sender, subject, body, received date) in SQLite using Peewee ORM
- Apply rule-based email processing with conditions and actions
- Actions include:
  - Mark as read/unread
  - Move to a specified label
  - Flag messages (star them)

## Prerequisites

- Python 3.9.6
- Google API credentials
- Required Python libraries (listed in `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Poujhit/gmail-email-processor.git
   cd gmail-email-processor
   ```
2. Create a virtual environment for python
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up Google API credentials:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Download `credentials.json` and place it in the project root

## Usage

### 1. Authenticate and Fetch Emails

Run the script to authenticate and fetch the latest emails:

```bash
cd src
python3 gmail_mail_fetch.py
```

Enter the number of messages to be stored in the db.
This will create an `emails.db` SQLite database and store the emails.

### 2. Define Email Processing Rules

Create a `rules.json` file to define processing rules. Example:

### **2.1 Sample `rules.json` File**

```json
{
  "rules": [
    {
      "predicate": "All",
      "conditions": [
        { "field": "sender", "predicate": "contains", "value": "github.com" },
        {
          "field": "received_at",
          "predicate": "less_than",
          "value": "7",
          "unit": "days"
        }
      ],
      "actions": ["mark_as_unread", "move_to_Important"]
    },
    {
      "predicate": "Any",
      "conditions": [
        { "field": "subject", "predicate": "contains", "value": "Invoice" },
        {
          "field": "received_at",
          "predicate": "greater_than",
          "value": "30",
          "unit": "days"
        }
      ],
      "actions": ["flag_message"]
    }
  ]
}
```

### **2.2 Explanation of Fields**

| Key         | Description                                                             | Example            |
| ----------- | ----------------------------------------------------------------------- | ------------------ |
| `predicate` | `"All"` (AND) or `"Any"` (OR) conditions must match                     | `"All"`            |
| `field`     | The email field to filter on (`sender`, `subject`, `received_at`)       | `"sender"`         |
| `predicate` | Comparison operator (`contains`, `equals`, `less_than`, `greater_than`) | `"contains"`       |
| `value`     | The value to compare with                                               | `"github.com"`     |
| `unit`      | Only for date fields (`days` or `months`)                               | `"days"`           |
| `actions`   | Actions to perform (`mark_as_read`, `move_to_<label>`, `flag_message`)  | `["flag_message"]` |

---

### 3. Process Emails

After defining rules, process the emails:

```bash
python process_mail.py
```

## Testing

To run tests:

```bash
pytest
```

## Troubleshooting

- If you face any authorisation problems, delete the `token.json` and re-authenticate by running the script again.
- Check if the `credentials.json` file is in the correct location.
- Verify that the required Python libraries are installed.
- Ensure the SQLite database file (`emails.db`) is not corrupted.
- Check the logs for detailed error messages and stack traces.

## Future improvements

1. Automating the mail fetch and sync to database periodically so that all the latest messages will be polled and stored locally
2. Adding cron to the process mail based on rules so that this job also runs periodically
3. mail fetch and sync should handle large number of messages, currently it can't hold a large number of messages from gmail on memory since I am bulk writing to it.

## Author

Poujhit
