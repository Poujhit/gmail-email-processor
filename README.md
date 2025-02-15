# Gmail Email Processor

## Overview

This project fetches emails from a Gmail inbox using the Gmail API, stores them in an SQLite database, and processes them based on user-defined rules. It supports marking emails as read/unread, moving them to different labels, and flagging messages.

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
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up Google API credentials:
   - Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the Gmail API
   - Download `credentials.json` and place it in the project root

## Usage

### 1. Authenticate and Fetch Emails

Run the script to authenticate and fetch the latest emails:

```bash
python main.py
```

This will create an `emails.db` SQLite database and store the emails.

### 2. Define Email Processing Rules

Create a `rules.json` file to define processing rules. Example:

```json
{
  "rules": [
    {
      "predicate": "All",
      "conditions": [
        { "field": "from", "predicate": "contains", "value": "example.com" },
        {
          "field": "subject",
          "predicate": "equals",
          "value": "Important Notice"
        }
      ],
      "actions": ["mark_as_read", "move_to_Important"]
    }
  ]
}
```

### 3. Process Emails

After defining rules, process the emails:

```bash
python main.py
```

## Testing

To run tests:

```bash
pytest
```

## Troubleshooting

- If `token.json` is missing, delete and re-authenticate by running the script again.
- Ensure your Google Cloud project is configured correctly and the Gmail API is enabled.

## License

This project is licensed under the MIT License.

## Author

[Your Name]

Poujhit
