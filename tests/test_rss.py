"""
Simple test script for RSS Reader functionality.
Tests fetching and parsing an RSS feed without GUI.
"""

# --- bootstrap: make repo-root modules importable and emoji output safe ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass
# --- end bootstrap ---

from rss_core import RSSFetcher
from rss_database import RSSDatabase


def test_rss_fetcher():
    """Test fetching and parsing a real RSS feed."""
    print("Testing RSS Fetcher...")

    # Test with NASA RSS feed (more open to programmatic access)
    test_url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"

    try:
        fetcher = RSSFetcher(timeout=15)
        print(f"\nFetching feed from: {test_url}")

        articles = fetcher.fetch_feed(test_url)
        print(f"Successfully fetched {len(articles)} articles!\n")

        # Display first 3 articles
        for i, article in enumerate(articles[:3], 1):
            print(f"\nArticle {i}:")
            print(f"  Title: {article.title}")
            print(f"  Link: {article.link}")
            print(f"  Published: {article.published}")
            desc = article.description[:100] if len(article.description) > 100 else article.description
            print(f"  Description: {desc}...")

        return True
    except Exception as e:
        print(f"Error fetching feed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database():
    """Test database functionality."""
    print("\n" + "="*60)
    print("Testing Database...")

    try:
        db = RSSDatabase("test_rss.db")

        # Add a test feed
        test_url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
        db.add_feed(test_url, "NASA Breaking News")
        print("Added test feed to database")

        # Get all feeds
        feeds = db.get_all_feeds()
        print(f"Total feeds in database: {len(feeds)}")

        # Close database
        db.close()
        print("Database test successful!")

        return True
    except Exception as e:
        print(f"Error testing database: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("RSS Reader Component Tests")
    print("="*60)

    # Test fetcher
    fetcher_ok = test_rss_fetcher()

    # Test database
    db_ok = test_database()

    print("\n" + "="*60)
    print("Test Results:")
    print(f"  RSS Fetcher: {'PASS' if fetcher_ok else 'FAIL'}")
    print(f"  Database: {'PASS' if db_ok else 'FAIL'}")
    print("="*60)
