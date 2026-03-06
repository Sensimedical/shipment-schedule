#!/usr/bin/env python3
"""
Test script for email automation setup
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test that environment variables are set"""
    required_vars = [
        'EMAIL_USER',
        'EMAIL_PASSWORD',
        'IMAP_SERVER',
        'SMTP_SERVER'
    ]

    missing = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == 'your-email@gmail.com' or os.getenv(var) == 'your-app-password':
            missing.append(var)

    if missing:
        print(f"❌ Missing or placeholder environment variables: {', '.join(missing)}")
        print("Please update your .env file with actual values.")
        return False

    print("✅ Environment variables are configured")
    return True

def test_directories():
    """Test that required directories exist"""
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data"

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False

    print("✅ Data directory exists")
    return True

def test_git():
    """Test git repository"""
    try:
        import git
        base_dir = Path(__file__).parent
        repo = git.Repo(base_dir)
        print("✅ Git repository is valid")
        return True
    except Exception as e:
        print(f"❌ Git repository issue: {e}")
        return False

def main():
    print("Testing Email Automation Setup")
    print("=" * 40)

    tests = [
        test_environment,
        test_directories,
        test_git
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Tests passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("🎉 Setup looks good! You can now run the automation.")
        print("Next steps:")
        print("1. Test the automation manually: python email_automation.py")
        print("2. Set up Windows Task Scheduler with run_automation.bat")
    else:
        print("⚠️  Please fix the issues above before running automation.")

if __name__ == "__main__":
    main()