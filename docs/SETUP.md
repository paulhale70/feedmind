# Wildcat Photo Search Setup

## Prerequisites
- Python 3.11+
- `pip` or `pipx`

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the web app
```bash
python app.py
```

Open `http://localhost:5000` in your browser.

## Usage notes
- Enter the root folder you want to scan (for example, `~/Pictures`).
- The app scans common photo extensions and returns metadata for up to 200 files.
- Logs are written to `logs/app.log`.

## Troubleshooting
- If metadata is missing, the image likely does not contain EXIF data.
- If you see permission errors, grant your terminal access to the target folder or pick a directory you own.
