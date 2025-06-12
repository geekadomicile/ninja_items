# Email Database Population Script

This script populates the app database with emails from the specified email account using the create email endpoint.

## Prerequisites

- Python 3.6+
- Django
- Django Ninja
- python-dotenv

## Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file with the following content:
   ```
   EMAIL_HOST=your_email_host
   EMAIL_USER=your_email_user
   EMAIL_PASSWORD=your_email_password
   EMAIL_FOLDER=your_email_folder
   ```

## Usage

1. Make sure the Django server is running:
   ```
   python manage.py runserver
   ```

2. Run the population script:
   ```
   python populate_emails.py
   ```

## Configuration

- The script connects to the email server using the credentials specified in the `.env` file.
- It fetches emails from the specified folder (default: Sent).
- For each email, it calls the create email endpoint with the appropriate data.
- The script handles email attachments by downloading and saving them to the server.

## Troubleshooting

- If you get a "Connection refused" error, make sure the Django server is running.
- If you have issues with email authentication, check your email credentials and server settings.

## Notes

- The script currently uses item_id=1 for all emails. In a real application, you would determine the correct item_id for each email.
- The script handles email attachments and saves them to the server in the 'media/attachments' directory.