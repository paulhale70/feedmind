# Wildcat
This is a learn to code project

## RSS Reader Desktop App

A simple desktop RSS feed reader application built with Python and Tkinter. Features include:
- Subscribe to multiple RSS/Atom feeds
- Automatic feed fetching and parsing
- SQLite database for caching articles
- Clean, user-friendly GUI
- Open articles in your default browser
- No external dependencies required (uses Python built-in libraries)

### Running the RSS Reader

```bash
python3 rss_reader.py
```

### Features

1. **Feed Management**
   - Add RSS/Atom feeds by URL
   - Remove unwanted feeds
   - View all subscribed feeds in a sidebar

2. **Article Reading**
   - Browse articles from your feeds
   - View article details (title, description, publish date)
   - Double-click or use "Open in Browser" to read full articles
   - Articles are cached locally for offline viewing

3. **Refresh & Cache**
   - Refresh individual feeds to get latest articles
   - Clear old cached articles (older than 30 days)

### Sample RSS Feeds to Try

- NASA Breaking News: `https://www.nasa.gov/rss/dyn/breaking_news.rss`
- TechCrunch: `https://techcrunch.com/feed/`
- Hacker News: `https://news.ycombinator.com/rss`
- Reddit Front Page: `https://www.reddit.com/.rss`
- The Verge: `https://www.theverge.com/rss/index.xml`

### Testing

Run the test script to verify functionality:

```bash
python3 test_rss.py
```

## dash

Run the Streamlit dashboard to ingest Excel data, explore it, connect to a database, and export datasets for other tools:

```bash
pip install -r requirements.txt  # or install streamlit, pandas, sqlalchemy directly
streamlit run dash.py
```

### Send a report
Inside the dashboard, open **Send report**, fill in your SMTP server details, recipients, and click **Send report** to email a CSV snapshot of the active dataset. Credentials are kept in session state only.

## dash

Run the Streamlit dashboard to ingest Excel data, explore it, connect to a database, and export datasets for other tools:

```bash
pip install -r requirements.txt  # or install streamlit, pandas, sqlalchemy directly
streamlit run dash.py
```

### Send a report
Inside the dashboard, open **Send report**, fill in your SMTP server details (STARTTLS, SSL, or none), recipients, and click **Test SMTP connection** to verify settings. Then choose **Send report** to email a CSV snapshot of the active dataset. Credentials are kept in session state only.
