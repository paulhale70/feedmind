# Wildcat
This is a learn to code project

## dash

Run the Streamlit dashboard to ingest Excel data, explore it, connect to a database, and export datasets for other tools:

```bash
pip install -r requirements.txt  # or install streamlit, pandas, sqlalchemy directly
streamlit run dash.py
```

### Send a report
Inside the dashboard, open **Send report**, fill in your SMTP server details, recipients, and click **Send report** to email a CSV snapshot of the active dataset. Credentials are kept in session state only.

Personal blog/bio/fun site built as a single-page experience.

## Running locally

Open `index.html` in your browser or serve the folder with your favorite static server (for example, `python -m http.server 8000`).
