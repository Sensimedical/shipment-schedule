@echo off
cd "C:\Users\Usuario\OneDrive\Projects\BIAutomations\shipment-schedule"
call .venv\Scripts\activate.bat
python email_automation.py
echo Automation completed at %date% %time% >> automation_history.log