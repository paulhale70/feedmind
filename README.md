# Wildcat
This is a learn to code project

## RSSreaderV1 - Desktop App

A feature-rich desktop RSS feed reader application built with Python and Tkinter. This professional-grade RSS reader includes advanced features like read/unread tracking, favorites, search, filtering, and automatic refresh.

### Features Overview

- ✅ **Subscribe to multiple RSS/Atom feeds**
- ✅ **Mark articles as read/unread** with visual indicators
- ✅ **Save favorite articles** for later reading
- ✅ **Search and filter** articles by keyword
- ✅ **Automatic feed refresh** every 15 minutes (optional)
- ✅ **SQLite database** for caching articles offline
- ✅ **Clean, intuitive GUI** with organized views
- ✅ **No external dependencies** (uses Python built-in libraries only)

### Running the RSS Reader

```bash
python3 rss_reader.py
```

### Complete Feature Guide

#### 1. Feed Management
- **Add RSS/Atom feeds by URL** - Simply paste any RSS or Atom feed URL
- **Subscribe to unlimited feeds** - No limit on the number of feeds
- **Remove unwanted feeds** - One-click feed deletion
- **Unread count per feed** - See how many unread articles each feed has
- **Press Enter** to quickly add a feed from the URL field

#### 2. Article Organization & Views
- **Three viewing modes:**
  - **All** - See all cached articles
  - **Unread** - Filter to show only unread articles
  - **Favorites** - Quick access to your starred articles
- **Visual status indicators:**
  - **Bold text** = Unread articles
  - **Gray text** = Read articles
  - **★** symbol = Favorite articles
  - **●** symbol = Unread indicator
- **Unread counter** - Real-time display of total unread articles

#### 3. Reading & Interaction
- **Article details panel** - Full description and metadata display
- **Double-click to open** - Opens articles in your default browser
- **One-click read/unread toggle** - Mark articles with a single button
- **Favorite button** - Star articles you want to save
- **Auto-mark as read** - Opening in browser automatically marks as read
- **Articles cached offline** - Read articles even without internet

#### 4. Search & Filter
- **Full-text search** - Search article titles and descriptions
- **Search respects current view** - Filters work with All/Unread/Favorites
- **Press Enter to search** - Quick keyboard-driven search
- **Clear search button** - Return to normal view instantly
- **Feed-specific search** - Search within a selected feed

#### 5. Refresh & Sync
- **Refresh individual feed** - Update one feed with latest articles
- **Refresh all feeds** - Update all subscribed feeds at once
- **Auto-refresh mode** - Automatically refresh all feeds every 15 minutes
- **Background threading** - Refreshes don't freeze the UI
- **Mark all as read** - Bulk operation for current feed or all feeds

#### 6. Cache Management
- **SQLite database storage** - Efficient local caching
- **30-day automatic cleanup** - Remove articles older than 30 days
- **Database migration** - Automatically updates schema for new features
- **Offline reading** - All cached articles available without internet

### Keyboard Shortcuts

- **Enter** in URL field - Add feed
- **Enter** in search field - Execute search
- **Double-click** article - Open in browser

### Sample RSS Feeds to Try

Popular news and technology feeds:

- **NASA Breaking News:** `https://www.nasa.gov/rss/dyn/breaking_news.rss`
- **TechCrunch:** `https://techcrunch.com/feed/`
- **Hacker News:** `https://news.ycombinator.com/rss`
- **Reddit Front Page:** `https://www.reddit.com/.rss`
- **The Verge:** `https://www.theverge.com/rss/index.xml`
- **BBC News:** `http://feeds.bbci.co.uk/news/rss.xml`
- **New York Times:** `https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml`
- **ArsTechnica:** `https://feeds.arstechnica.com/arstechnica/index`

### Technical Details

**Built with:**
- Python 3.11+
- Tkinter (built-in GUI library)
- SQLite3 (built-in database)
- urllib (built-in HTTP library)
- xml.etree.ElementTree (built-in XML parser)

**No external dependencies required!** The application uses only Python's standard library.

### Testing

Run the test script to verify functionality:

```bash
python3 test_rss.py
```

This tests RSS/Atom feed fetching, parsing, and database operations.

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
