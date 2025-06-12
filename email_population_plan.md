# Email Database Population Script Plan

## Objective
Create a script that populates the app database using the create email endpoint with emails from the provided email account.

## Components

### 1. Email Model
The `Email` model in `itemsapi/models.py` has the following fields:
- `item`: ForeignKey to Item
- `subject`: CharField
- `body`: TextField
- `from_address`: EmailField
- `received_at`: DateTimeField
- `created_at`: DateTimeField (auto_now_add=True)

### 2. Email Endpoint
We need to create an endpoint to handle email creation. This endpoint should:
- Accept email data (subject, body, from_address, received_at, item_id)
- Create an Email object in the database
- Return the created email

### 3. Email Fetching Script
The script should:
- Connect to the email server using the provided credentials
- Fetch emails from the Sent folder
- For each email, call the create email endpoint with the appropriate data
- Handle email attachments, particularly images:
  - Download and save attachments to the server
  - Store the file paths in the database

## Implementation Steps

1. **Create Email Endpoint**
   - Add a new route in `itemsapi/routers.py` for creating emails
   - Implement the handler function that creates an Email object

2. **Create Email Schema**
   - Define an `EmailCreate` schema in `itemsapi/schemas.py` for request validation

3. **Create the Population Script**
   - Write a Python script that:
     - Connects to the email server
     - Fetches emails from the Sent folder
     - Calls the create email endpoint for each email
     - Handles email attachments:
       - Downloads attachments
       - Saves them to a designated directory
       - Updates the email record with attachment information

## Security Considerations
- Store email credentials securely
- Validate and sanitize all input data
- Handle errors gracefully
- Securely handle and store email attachments

## Testing
- Test the endpoint with sample data
- Test the script with the provided credentials (in a secure environment)
- Verify that emails and their attachments are correctly populated in the database
- Test with emails that have various types of attachments