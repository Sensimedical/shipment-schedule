import imaplib
import email
import os
from email.header import decode_header
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import git
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()  # Also log to console for GitHub Actions
    ]
)

class EmailAutomation:
    def __init__(self):
        # Email configuration - load from environment variables
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')

        # Search configuration
        self.search_subject = os.getenv('SEARCH_SUBJECT', 'search results')
        self.search_sender = os.getenv('SEARCH_SENDER', '')

        # File configuration
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.target_filename = os.getenv('TARGET_FILENAME', 'searchresults.xlsx')

        # Git configuration (optional)
        try:
            self.git_repo = git.Repo(self.base_dir)
        except:
            self.git_repo = None
            logging.warning("Git repository not available - git operations will be skipped")

        self.git_remote = os.getenv('GIT_REMOTE', 'origin')
        self.git_branch = os.getenv('GIT_BRANCH', 'main')

        # Notification configuration
        self.notify_email = os.getenv('NOTIFY_EMAIL')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

    def connect_imap(self):
        """Connect to IMAP server"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_user, self.email_password)
            return mail
        except Exception as e:
            logging.error(f"Failed to connect to IMAP: {e}")
            raise

    def search_emails(self, mail, days_back=1):
        """Search for emails with XLS attachments"""
        try:
            mail.select('inbox')

            # Calculate date range
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')

            # Build search criteria
            search_criteria = f'SINCE {since_date}'
            if self.search_subject:
                search_criteria += f' SUBJECT "{self.search_subject}"'
            if self.search_sender:
                search_criteria += f' FROM "{self.search_sender}"'

            status, messages = mail.search(None, search_criteria)
            return messages[0].split() if status == 'OK' else []

        except Exception as e:
            logging.error(f"Failed to search emails: {e}")
            raise

    def download_attachment(self, mail, email_id):
        """Download XLS attachment from email"""
        try:
            status, msg_data = mail.fetch(email_id, '(RFC822)')
            if status != 'OK':
                return None

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # Check if email has attachments
            for part in email_message.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename and (filename.lower().endswith('.xls') or filename.lower().endswith('.xlsx') or 'sales open orders' in filename.lower()):
                    # Decode filename if necessary
                    filename, encoding = decode_header(filename)[0]
                    if isinstance(filename, bytes):
                        filename = filename.decode(encoding or 'utf-8')

                    # Save attachment
                    filepath = self.data_dir / self.target_filename
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))

                    logging.info(f"Downloaded attachment: {filename} -> {filepath}")
                    return filepath

            return None

        except Exception as e:
            logging.error(f"Failed to download attachment from email {email_id}: {e}")
            return None

    def validate_excel_file(self, filepath):
        """Validate that the downloaded file is a valid Excel file"""
        try:
            df = pd.read_excel(filepath)
            if df.empty:
                logging.warning(f"Downloaded file {filepath} is empty")
                return False
            logging.info(f"Validated Excel file: {len(df)} rows, {len(df.columns)} columns")
            return True
        except Exception as e:
            logging.error(f"Invalid Excel file {filepath}: {e}")
            return False

    def commit_and_push(self, filepath):
        """Commit and push changes to git (optional - may be handled by CI/CD)"""
        try:
            # Check if we should handle git operations ourselves
            if os.getenv('GITHUB_ACTIONS') == 'true':
                logging.info("Running in GitHub Actions - skipping manual git operations")
                return True

            # Add file to git
            self.git_repo.index.add([str(filepath.relative_to(self.base_dir))])

            # Check if there are changes
            if not self.git_repo.index.diff("HEAD"):
                logging.info("No changes to commit")
                return True

            # Commit changes
            commit_message = f"Auto-update: {self.target_filename} from email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.git_repo.index.commit(commit_message)

            # Push changes
            origin = self.git_repo.remote(self.git_remote)
            origin.push(self.git_branch)

            logging.info(f"Successfully committed and pushed changes: {commit_message}")
            return True

        except Exception as e:
            logging.warning(f"Git operations failed (this may be expected in CI/CD): {e}")
            return True  # Don't fail the automation if git push fails

    def send_notification(self, success, message):
        """Send notification email"""
        if not self.notify_email:
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notify_email
            msg['Subject'] = f"Email Automation {'Success' if success else 'Failed'}"

            body = f"Email automation completed.\n\nStatus: {'Success' if success else 'Failed'}\nMessage: {message}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()

            logging.info("Notification email sent")

        except Exception as e:
            logging.error(f"Failed to send notification: {e}")

    def run_automation(self):
        """Main automation function"""
        logging.info("Starting email automation")

        try:
            # Connect to email
            mail = self.connect_imap()

            # Search for emails
            email_ids = self.search_emails(mail)
            if not email_ids:
                message = "No matching emails found"
                logging.info(message)
                self.send_notification(False, message)
                return

            # Process most recent email
            latest_email_id = email_ids[-1]  # Most recent
            filepath = self.download_attachment(mail, latest_email_id)

            if not filepath:
                message = "No XLS attachment found in emails"
                logging.error(message)
                self.send_notification(False, message)
                return

            # Validate file
            if not self.validate_excel_file(filepath):
                message = "Downloaded file is not a valid Excel file"
                logging.error(message)
                self.send_notification(False, message)
                return

            # Commit and push
            if self.commit_and_push(filepath):
                message = f"Successfully updated {self.target_filename}"
                logging.info(message)
                self.send_notification(True, message)
            else:
                message = "Failed to commit and push changes"
                logging.error(message)
                self.send_notification(False, message)

            mail.logout()

        except Exception as e:
            error_msg = f"Automation failed: {str(e)}"
            logging.error(error_msg)
            self.send_notification(False, error_msg)

if __name__ == "__main__":
    automation = EmailAutomation()
    automation.run_automation()</content>
<parameter name="filePath">c:\Users\Usuario\OneDrive\Projects\BIAutomations\shipment-schedule\email_automation.py