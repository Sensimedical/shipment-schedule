#!/usr/bin/env python3
"""
GitHub Secrets Setup Helper
Run this script to generate the commands needed to set up GitHub Actions secrets.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_secret_commands():
    """Generate GitHub CLI commands to set up secrets"""

    secrets = [
        'EMAIL_USER',
        'EMAIL_PASSWORD',
        'IMAP_SERVER',
        'IMAP_PORT',
        'SMTP_SERVER',
        'SMTP_PORT',
        'SEARCH_SUBJECT',
        'SEARCH_SENDER',
        'TARGET_FILENAME',
        'NOTIFY_EMAIL'
    ]

    print("GitHub Secrets Setup Commands")
    print("=" * 50)
    print("Run these commands in your terminal (make sure you have GitHub CLI installed):")
    print()
    print("# First, make sure you're in the right repository:")
    print("gh repo set-default https://github.com/eliasattias/shipment-schedule")
    print()

    for secret in secrets:
        value = os.getenv(secret, '')
        if value and value not in ['your-email@gmail.com', 'your-app-password', '', 'your-email@gmail.com']:
            print(f"gh secret set {secret} --body \"{value}\"")
        else:
            print(f"# TODO: Set {secret}")
            print(f"# gh secret set {secret} --body \"YOUR_{secret}_VALUE\"")

    print()
    print("Alternative: Set secrets manually in GitHub web interface:")
    print("Go to: https://github.com/eliasattias/shipment-schedule/settings/secrets/actions")
    print()
    print("Required secrets:")
    for secret in secrets:
        print(f"- {secret}")

if __name__ == "__main__":
    generate_secret_commands()