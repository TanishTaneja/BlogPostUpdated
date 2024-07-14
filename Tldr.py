import imaplib
import email
from datetime import datetime
from main import FetchedEmail
from email.utils import parsedate_to_datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to the mail server
def mails():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(os.environ.get("EMAIL_KEY"),  os.environ.get("PASSWORD_KEY"))
    mail.select('inbox')

    # Get today's date in the required format
    today = datetime.today().strftime("%d-%b-%Y")
    search_criteria = f'(FROM "dan@tldrnewsletter.com" ON "{today}")'
    result, data = mail.search(None, search_criteria)
    body = []

    for num in data[0].split():
        result, data = mail.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
        email_subject = email_message['subject'].split("=")[0]
        email_from = email_message['from']
        email_body = ""
        message_id = email_message['Message-ID']
        date_received = parsedate_to_datetime(email_message['Date'])
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    email_body=part.get_payload(decode=True).decode().split("Love TLDR?")[0]
        existing_email = FetchedEmail.query.filter_by(message_id=message_id).first()
        if existing_email is None and email_subject:
            new_email = FetchedEmail(
                        message_id=message_id,
                        subject=email_subject,
                        sender=email_from,
                        body=email_body,
                        date_received=date_received
                    )
            body.append(new_email)
    mail.logout()
    return body
