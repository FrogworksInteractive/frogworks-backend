import smtplib
from loguru import logger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailManager:
    def __init__(self, email_address: str, password: str, display_name: str):
        self.email_address = email_address
        self.password = password
        self.display_name = display_name

    def send_text_email(self, subject: str, body: str, recipients: list):
        message = MIMEText(body)
        message['Subject'] = subject
        message['From'] = self.display_name
        message['To'] = ', '.join(recipients)

        logger.info(f'Sending text email to: {recipients} - subject: {subject}, body: {body}')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(self.email_address, self.password)
            server.sendmail(self.email_address, recipients, message.as_string())
            server.quit()

    def send_email(self, subject: str, text_body: str, html_body: str, recipients: list):
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.display_name
        message['To'] = ', '.join(recipients)

        logger.info(f'Sending regular email to: {recipients} - subject: {subject}, text body: {text_body}, '
                    f'html body: {html_body}')

        # Add the text and HTML bodies.
        message.attach(MIMEText(text_body, 'plain'))
        message.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(self.email_address, self.password)
            server.sendmail(self.email_address, recipients, message.as_string())
            server.quit()
