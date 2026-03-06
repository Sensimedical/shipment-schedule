# Email Forwarding Setup Guide
# Since your sensimedical.com account is Google Workspace,
# we'll forward emails to a personal Gmail account for automation

## Step 1: Set up Email Forwarding

### In your Google Workspace account (elias.a@sensimedical.com):

1. Go to Gmail → Settings (gear icon) → See all settings
2. Click "Forwarding and POP/IMAP" tab
3. Click "Add a forwarding address"
4. Enter your personal Gmail address (e.g., elias.attias@gmail.com)
5. Gmail will send a verification email to your personal account
6. Click the verification link in the email
7. Back in Workspace Gmail, select "Forward a copy of incoming mail to..."
8. Choose your personal Gmail address
9. Select "keep Gmail's copy in the inbox" (optional)
10. Click "Save Changes"

## Step 2: Create Gmail App Password

### In your personal Gmail account:

1. Enable 2-Factor Authentication (if not already enabled):
   - Go to https://myaccount.google.com/security
   - Under "Signing in to Google", click "2-Step Verification"
   - Follow the setup process

2. Generate App Password:
   - Go to https://myaccount.google.com/apppasswords
   - Sign in if prompted
   - Select "Mail" and "Windows Computer"
   - Copy the 16-character password

## Step 3: Update Configuration

Update your .env file to use the personal Gmail account:

```
EMAIL_USER=your-personal@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
SEARCH_SENDER=customercare@optimalmax.com
NOTIFY_EMAIL=your-personal@gmail.com
```

## Step 4: Test

Run the test script:
```bash
python email_automation.py
```

This approach:
- ✅ Works with Google Workspace accounts
- ✅ Avoids complex OAuth2 setup
- ✅ Uses standard Gmail IMAP
- ✅ Keeps your Workspace email secure