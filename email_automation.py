import os
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging
import git
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)

class EmailAutomation:
    def __init__(self):
        # File configuration
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.target_filename = os.getenv('TARGET_FILENAME', 'searchresults.xlsx')
        self.token_path = self.base_dir / 'token.pickle'

        # Search configuration
        self.search_subject = os.getenv('SEARCH_SUBJECT', 'Sensi Medical Sales Open Order')
        self.search_sender = os.getenv('SEARCH_SENDER', 'customercare@optimalmax.com')

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
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))

    def get_gmail_service(self):
        """Get authenticated Gmail API service"""
        try:
            creds = None

            # Load existing token
            if self.token_path.exists():
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)

            # Refresh token if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            if not creds or not creds.valid:
                logging.error("No valid Gmail credentials found. Run oauth2_setup.py first.")
                return None

            return build('gmail', 'v1', credentials=creds)

        except Exception as e:
            logging.error(f"Failed to get Gmail service: {e}")
            return None

    def search_emails(self, service, days_back=1):
        """Search for emails with XLS attachments"""
        try:
            # Build search query
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            query = f'after:{since_date}'

            if self.search_subject:
                query += f' subject:"{self.search_subject}"'
            if self.search_sender:
                query += f' from:"{self.search_sender}"'

            query += ' has:attachment filename:(xls OR xlsx)'

            logging.info(f"Searching with query: {query}")

            results = service.users().messages().list(
                userId='me',
                q=query,
                orderBy='newest',
                maxResults=5
            ).execute()

            messages = results.get('messages', [])
            logging.info(f"Found {len(messages)} matching emails")
            return messages

        except Exception as e:
            logging.error(f"Failed to search emails: {e}")
            raise

    def download_attachment(self, service, message_id):
        """Download XLS attachment from email"""
        try:
            message = service.users().messages().get(userId='me', id=message_id, format='full').execute()

            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Unknown')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

            logging.info(f"Processing email from {sender}: {subject}")

            # Find and download attachment
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['filename']:
                        filename = part['filename']
                        if filename.lower().endswith(('.xls', '.xlsx')):
                            attachment_id = part['body']['attachmentId']
                            attachment = service.users().messages().attachments().get(
                                userId='me',
                                messageId=message_id,
                                id=attachment_id
                            ).execute()

                            data = base64.urlsafe_b64decode(attachment['data'])
                            filepath = self.data_dir / self.target_filename

                            with open(filepath, 'wb') as f:
                                f.write(data)

                            logging.info(f"Downloaded attachment: {filename} -> {filepath}")
                            return filepath

            return None

        except Exception as e:
            logging.error(f"Failed to download attachment from message {message_id}: {e}")
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
            if not self.git_repo:
                logging.info("Git repository not available - skipping git operations")
                return True

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
            return True

    def send_notification(self, success, message):
        """Send notification email"""
        if not self.notify_email or not self.email_user or not self.email_password:
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.notify_email
            msg['Subject'] = f"Email Automation {'Success' if success else 'Failed'}"

            body = f"Email automation completed.\n\nStatus: {'Success' if success else 'Failed'}\nMessage: {message}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
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
        logging.info("Starting email automation using Gmail API")

        try:
            # Ensure data directory exists
            self.data_dir.mkdir(parents=True, exist_ok=True)

            # Get Gmail service
            service = self.get_gmail_service()
            if not service:
                message = "Failed to authenticate with Gmail API"
                logging.error(message)
                self.send_notification(False, message)
                return

            # Search for emails
            messages = self.search_emails(service)
            if not messages:
                message = "No matching emails found"
                logging.info(message)
                self.send_notification(False, message)
                return

            # Process most recent email
            latest_message_id = messages[0]['id']
            filepath = self.download_attachment(service, latest_message_id)

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

        except Exception as e:
            error_msg = f"Automation failed: {str(e)}"
            logging.error(error_msg)
            self.send_notification(False, error_msg)

if __name__ == "__main__":
    automation = EmailAutomation()
    automation.run_automation()