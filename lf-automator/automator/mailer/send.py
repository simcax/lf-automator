"""Class to send mail via sendgrid."""

import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


class Mailer:
    def __init__(self, sender=None, subject=None):
        """Initialize the class."""
        self.sender = sender
        self.subject = subject

    def send_email(self, message_string, to_email):
        """Send an email."""

        message = Mail(
            from_email=self.sender,
            to_emails=to_email,
            subject=self.subject,
            html_content=f"<strong>{message_string}</strong>",
        )

        try:
            sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)
        return 0
