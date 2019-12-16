# Built-In Modules
import ssl, os, secrets
from datetime import datetime
from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText

# Global Variables
HOST = "https://127.0.0.1:5000"
port = 465
PASSWORD = os.environ['MAILER_PASSWORD']
USERNAME = os.environ['MAILER_USERNAME']
EMAIL_ADDRESS = f"{USERNAME}@gmail.com"
SMTPServer = "smtp.gmail.com"
context = ssl.create_default_context()


class Mailer(object):
    """This class represents our mailer object."""

    def __init__(self):
        """Create our connection."""

    def send_mail(self, message, email, subject="Hello from Octolytics!"):
        """
        Send an email using our email account
        :param str message: Message (in HTML) we are trying to send
        :param str email: Receiver of the email
        :param str subject: Subject of the email
        :rtype Bool:
        :return: True/False if we were able to send the message
        """
        # Build our message object
        msg = MIMEText(message, 'html')
        msg['Subject'] = subject
        msg['From'] = USERNAME
        conn = SMTP(SMTPServer)
        conn.set_debuglevel(False)
        conn.login(USERNAME, PASSWORD)
        try:
            conn.sendmail(USERNAME, email, msg.as_string())
        finally:
            conn.quit()

    def send_code(self, email, data):
        """
        This function sends a code to a email address to confirm it is real.

        :param string email: Email we are confirming
        :param dict data: User DB information
        :return: Updated user DB info with timestamp
        """
        # Generate our secure PRG
        code = secrets.SystemRandom().uniform(0, 10000000)

        # Generate callback URL
        callback_url = f"{HOST}/confirm_alias?code={code}&username={data['username']}&email={email}"

        # Send the PRG
        self.send_mail(f"<html><a href={callback_url}><b>Click me!</b></a></html>", email)

        # Always overwrite
        data['sessions']['email_code'] = (code, datetime.now())
        return data

if __name__ == '__main__':
    mail_client = Mailer()
    # mail_client.send_mail("""<html><b>test</b></html>""", 'sid.premkumar@gmail.com')
    # mail_client.send_code('sid.premkumar@gmail.com', 'test')