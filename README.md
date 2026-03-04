## Shipment Schedule App

This is a small Streamlit app that lets your team view the daily **Pending Orders** export and adjust the **Follow up** date for each row using a calendar UI. Changes are stored in a local SQLite database so they persist even when a new CSV is loaded.

### Folder structure

- `app.py` – main Streamlit app
- `requirements.txt` – Python dependencies
- `data/` – place your daily `Pending Orders *.csv` file(s) here
- `orders.db` – created automatically; stores user-edited follow-up dates

### Python & virtual environment setup

From PowerShell:

```powershell
cd "C:\Users\Usuario\OneDrive\Projects\BIAutomations\shipment-schedule"

# Create virtual environment (one time)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

Whenever you come back in a new terminal, just:

```powershell
cd "C:\Users\Usuario\OneDrive\Projects\BIAutomations\shipment-schedule"
.\.venv\Scripts\Activate.ps1
```

### Running the app

With the virtual environment activated:

```powershell
streamlit run app.py
```

Your browser will open to the local URL (usually `http://localhost:8501`). Press `Ctrl+C` in the terminal to stop the app.

### Daily workflow

1. Export/download the latest **Pending Orders** CSV from your source system.
2. Save or copy the file into:
   - `C:\Users\Usuario\OneDrive\Projects\BIAutomations\shipment-schedule\data`
   - The filename should match the pattern `Pending Orders *.csv` (for example: `Pending Orders  March 04, 2026.csv`).
3. Make sure the Streamlit app is running (or restart it if needed).
4. Refresh/reload the browser page if it was already open.
5. Use the table to:
   - Filter by `Customer` (via the filter box).
   - Edit the `Follow up` column using the calendar picker.
6. Click **Save changes** to write all modified follow-up dates into `orders.db`.

The next day, when you drop a new CSV into `data/`, the app will:

- Load the newest `Pending Orders *.csv` file.
- Merge in any existing follow-up overrides from `orders.db` based on the synthetic `order_key`.

