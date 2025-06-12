#!/usr/bin/env python3
import os
import sys
import imaplib
import email
from email.policy import default
from datetime import datetime
import requests
import json
import socket
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email server credentials
EMAIL_HOST = os.getenv('EMAIL_HOST', 'mail.geekadomicile.com')
EMAIL_USER = os.getenv('EMAIL_USER', 'a.bordessoules@geekadomicile.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'JHygR4P8$1')
EMAIL_FOLDER = os.getenv('EMAIL_FOLDER', 'Sent')

# API endpoint
API_URL = 'http://localhost:8000/api'

def connect_to_email_server():
    """Connect to the email server and login"""
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    mail.login(EMAIL_USER, EMAIL_PASSWORD)
    return mail

def fetch_emails(mail):
    """Fetch emails from the specified folder"""
    mail.select(EMAIL_FOLDER)
    status, messages = mail.search(None, 'ALL')
    return messages[0].split()

def parse_email(raw_email):
    """Parse a raw email into its components"""
    msg = email.message_from_bytes(raw_email, policy=default)
    return {
        'subject': msg['subject'] or 'No Subject',
        'from_address': msg['from'] or 'unknown@domain.com',
        'date': msg['date'],
        'body': '',
        'attachments': []
    }

def get_email_body(msg):
    """Extract the body from the email message"""
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                break
            elif part.get_content_type() == 'text/html':
                # For now, we'll just get the plain text version
                # In a real application, you might want to parse the HTML
                continue
    else:
        body = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8')
    return body if body else 'No body found'

def save_attachment(attachment_data, item_id):
    """Save an attachment directly from memory without writing to disk"""
    url = f"{API_URL}/items/{item_id}/files"
    files = {'file': (attachment_data['filename'], attachment_data['content'], attachment_data['content_type'])}
    
    # Add retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(url, files=files)
            if response.status_code in [200, 201]:
                print(f"Successfully uploaded attachment: {attachment_data['filename']}")
                return True
            else:
                print(f"Attempt {attempt+1}/{max_retries}: Error uploading attachment - {response.status_code}")
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries}: Connection error - {str(e)}")
        
        time.sleep(2)  # Wait before retrying
    
    print(f"Failed to upload attachment after {max_retries} attempts: {attachment_data['filename']}")
    return False

def get_email_attachments(msg):
    """Extract attachments from the email message using walk()"""
    attachments = []

    for part in msg.walk():
        # Skip the container parts
        if part.get_content_maintype() == 'multipart':
            continue

        # Extract attachments
        if part.get_content_maintype() in ['image', 'application']:
            filename = part.get_filename()
            if filename:
                attachments.append({
                    'filename': filename,
                    'content_type': part.get_content_type(),
                    'content': part.get_payload(decode=True)
                })

    return attachments

def fetch_raw_email(mail, email_id):
    """Fetch the raw email content"""
    status, data = mail.fetch(email_id, '(RFC822)')
    return data[0][1]

def create_email_endpoint(item_id, email_data):
    """Call the create email endpoint with email data"""
    url = f"{API_URL}/items/{item_id}/emails"
    try:
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            data=json.dumps(email_data)
        )
        if response.status_code not in [200, 201]:
            print(f"Error creating email: {response.status_code} - {response.text}")
        return response
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server. Make sure the Django server is running.")
        sys.exit(1)

def check_api_server():
    """Check if the API server is running, start it if not"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    if result == 0:
        print("API server is already running")
        return
    
    print("Starting Django server in background...")
    import subprocess
    server_process = subprocess.Popen(
        ["python", "manage.py", "runserver"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    max_retries = 10
    for i in range(max_retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        if result == 0:
            print("API server started successfully")
            return
        time.sleep(1)
    
    print("Error: Failed to start API server after 10 seconds")
    sys.exit(1)


def get_or_create_unprocessed_item():
    """Get or create an 'Unprocessed' item for imported emails"""
    try:
        # Check if unprocessed item exists
        response = requests.get(f"{API_URL}/items?name=Unprocessed")
        if response.status_code == 200 and response.json():
            return response.json()[0]['id']
        
        # Create unprocessed item
        data = {
            'name': 'Unprocessed',
            'description': 'Temporary container for imported emails',
            'parent_id': None
        }
        response = requests.post(f"{API_URL}/items", json=data)
        if response.status_code in [200, 201]:
            return response.json()['id']
        else:
            print(f"Error creating unprocessed item: {response.status_code} - {response.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server. Make sure the Django server is running.")
        sys.exit(1)

def extract_qr_from_subject(subject):
    """Extract QR code from email subject"""
    import re
    match = re.search(r'(?:Re:\s*)?(\w+)$', subject)
    return match.group(1) if match else None

def save_temp_attachment(attachment, email_id):
    """Save attachment to temporary storage"""
    os.makedirs(f"temp_attachments/{email_id}", exist_ok=True)
    file_path = f"temp_attachments/{email_id}/{attachment['filename']}"
    with open(file_path, 'wb') as f:
        f.write(attachment['content'])
    return file_path

def main():
    # Check if API server is running
    check_api_server()

    # Get or create unprocessed item
    unprocessed_id = get_or_create_unprocessed_item()
    print(f"Using unprocessed item ID: {unprocessed_id}")

    # Connect to email server
    mail = connect_to_email_server()

    # Fetch emails
    email_ids = fetch_emails(mail)

    # Limit to first 250 emails for testing
    email_ids = email_ids[:25]

    # Process each email
    total_emails = len(email_ids)
    for i, email_id in enumerate(email_ids):
        raw_email = fetch_raw_email(mail, email_id)
        msg = email.message_from_bytes(raw_email, policy=default)

        # Parse email
        email_data = parse_email(raw_email)
        email_data['body'] = get_email_body(msg)
        email_data['attachments'] = get_email_attachments(msg)

        # Convert date to datetime
        try:
            email_data['received_at'] = datetime.strptime(email_data['date'], '%a, %d %b %Y %H:%M:%S %z')
        except ValueError:
            # Try a different format if needed
            email_data['received_at'] = datetime.now()

        # Extract QR code from subject
        qr_code = extract_qr_from_subject(email_data['subject'])
        print(f"Extracted QR code: {qr_code or 'None'}")

        # Prepare data for API call
        api_data = {
            'item_id': unprocessed_id,
            'subject': email_data['subject'],
            'body': email_data['body'],
            'from_address': email_data['from_address'],
            'received_at': email_data['received_at'].isoformat(),
            'qr_code': qr_code
        }

        # Call the API
        response = create_email_endpoint(unprocessed_id, api_data)
        if response.status_code not in [200, 201]:
            print(f"Error creating email: {response.status_code} - {response.text}")
            continue
            
        email_id = response.json().get('id')
        print(f"Created email with ID: {email_id}")

        # Handle attachments if any
        if email_data['attachments']:
            saved_count = 0
            for attachment in email_data['attachments']:
                # Save to temp location
                file_path = save_temp_attachment(attachment, email_id)
                print(f"  Saved attachment: {file_path}")
                saved_count += 1
            print(f"  Saved {saved_count} attachments to temporary storage")

        # Print progress
        if i % 10 == 0 or i == total_emails - 1:
            print(f"Processed {i+1}/{total_emails} emails")

    # Logout from email server
    mail.logout()

if __name__ == "__main__":
    main()