#!/usr/bin/env python3
"""
Update Gmail App Password in .env file
Run this after you generate your Gmail App Password
"""
import os
from pathlib import Path

def update_app_password():
    """Update the EMAIL_PASSWORD in .env with Gmail App Password"""

    print("🔐 Gmail App Password Setup")
    print("=" * 40)
    print()
    print("You need a Gmail App Password for IMAP access.")
    print("Follow these steps:")
    print()
    print("1. Go to: https://myaccount.google.com/apppasswords")
    print("2. Sign in with: elias.a@sensimedical.com")
    print("3. Select 'Mail' and 'Windows Computer' (or other device)")
    print("4. Copy the 16-character password (no spaces)")
    print()

    app_password = input("Enter your 16-character Gmail App Password: ").strip()

    if len(app_password) != 16:
        print(f"❌ Error: App password must be exactly 16 characters. You entered {len(app_password)} characters.")
        return False

    if ' ' in app_password:
        print("❌ Error: App password should not contain spaces.")
        return False

    # Update .env file
    env_path = Path(__file__).parent / '.env'

    try:
        with open(env_path, 'r') as f:
            content = f.read()

        # Replace the password line
        old_line = 'EMAIL_PASSWORD=Black.orange5786!'
        new_line = f'EMAIL_PASSWORD={app_password}'

        if old_line not in content:
            print("❌ Could not find the password line in .env file")
            return False

        updated_content = content.replace(old_line, new_line)

        with open(env_path, 'w') as f:
            f.write(updated_content)

        print("✅ App password updated successfully!")
        print()
        print("🧪 Testing connection...")

        # Test the connection
        import imaplib
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            mail.login('elias.a@sensimedical.com', app_password)
            mail.logout()
            print("✅ IMAP connection test successful!")
            print()
            print("🎉 Ready for GitHub Actions setup!")
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print("Please double-check your app password.")
            return False

    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

if __name__ == "__main__":
    update_app_password()