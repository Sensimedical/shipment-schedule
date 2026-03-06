# Gmail OAuth2 Automation Setup Guide

## 🔐 Complete Setup Instructions

### Phase 1: Local Setup (One Time)

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable Gmail API:
   - Click "Enable APIs and Services"
   - Search for "Gmail API"
   - Click "Enable"

#### Step 2: Create OAuth2 Credentials

1. Go to "Credentials" in left sidebar
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: **"Desktop application"**
4. Click "Create"
5. Click the download icon (JSON file)
6. **IMPORTANT**: Save as `credentials.json` in your project root

#### Step 3: Authorize the Application

```bash
# From your project directory, with credentials.json in place
python oauth2_setup.py
```

This will:
- Open your browser for authentication
- Ask you to authorize the app
- Save `token.pickle` (keep this private!)

#### Step 4: Test Locally

```bash
python email_automation.py
```

### Phase 2: GitHub Actions Setup

#### Step 1: Create Base64-Encoded Credentials Secret

On your local machine:

```powershell
# Windows PowerShell
$content = [System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("credentials.json"))
Write-Host $content
```

Or on Mac/Linux:

```bash
# Mac/Linux
base64 -i credentials.json
```

Copy the output (very long string)

#### Step 2: Add GitHub Secrets

Go to: **https://github.com/eliasattias/shipment-schedule/settings/secrets/actions**

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `GOOGLE_CREDENTIALS_JSON` | Paste the base64 string from above |
| `SEARCH_SUBJECT` | Sensi Medical Sales Open Order |
| `SEARCH_SENDER` | customercare@optimalmax.com |
| `TARGET_FILENAME` | searchresults.xlsx |
| `EMAIL_USER` | your-personal@gmail.com |
| `EMAIL_PASSWORD` | your-16-char-app-password |
| `NOTIFY_EMAIL` | your-email@gmail.com |
| `SMTP_SERVER` | smtp.gmail.com |
| `SMTP_PORT` | 587 |

#### Step 3: Test GitHub Actions Workflow

1. Go to your repo → **Actions** → **"Daily Email Automation"**
2. Click "Run workflow" → "Run workflow"
3. Watch the logs to verify it works

### How It Works

1. **oauth2_setup.py** - Converts base64 credentials back to credentials.json and generates token.pickle
2. **email_automation.py** - Uses the token.pickle to access Gmail API
3. **GitHub Actions** - Runs daily, creates files, commits to repo
4. **Your Computer** - Pulls changes with `git pull`

### Troubleshooting

**"No valid Gmail credentials found"**
- Solution: Run `python oauth2_setup.py` locally first

**"Authentication failed in GitHub Actions"**
- Verify `GOOGLE_CREDENTIALS_JSON` secret is the full base64 string
- Make sure credentials.json is valid

**"File not updating"**
- Check email filters aren't hiding matching emails
- Verify search criteria matches actual emails

### Security Notes

✅ `credentials.json` - Add to .gitignore (don't share)
✅ `token.pickle` - Add to .gitignore (OAuth token)
✅ GitHub Secrets - Only visible to actions, not in logs
✅ No passwords stored in repo (except GitHub Secrets)

### File Structure

```
shipment-schedule/
├── credentials.json      ← Google OAuth2 (gitignored ✓)
├── token.pickle          ← OAuth token (gitignored ✓)
├── .env                  ← Local env vars (gitignored ✓)
├── email_automation.py   ← Main script
├── oauth2_setup.py       ← Authorization setup
└── .github/
    └── workflows/
        └── email-automation.yml
```

### One-Time Local Verification Checklist

- [ ] Created Google Cloud project
- [ ] Enabled Gmail API
- [ ] Created OAuth2 credentials
- [ ] Downloaded credentials.json
- [ ] Ran `python oauth2_setup.py` (authorized browser)
- [ ] Ran `python email_automation.py` (found token.pickle)
- [ ] Successfully downloaded email attachment

### GitHub Actions Checklist

- [ ] Created base64 encoded credentials
- [ ] Added all 9 GitHub Secrets
- [ ] Tested workflow manually
- [ ] Verified logs show success