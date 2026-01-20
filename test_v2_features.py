"""
Test script for RSSreaderV2 features.
Tests categories, OPML, themes, statistics, and database V2.
"""

import os
from rss_database_v2 import RSSDatabase
from rss_opml import OPMLHandler
from rss_themes import LightTheme, DarkTheme
from rss_core import RSSFetcher


def test_database_v2():
    """Test V2 database features."""
    print("=" * 60)
    print("Testing Database V2...")
    print("=" * 60)

    # Remove test database if exists
    if os.path.exists("test_v2.db"):
        os.remove("test_v2.db")

    try:
        db = RSSDatabase("test_v2.db")
        print("✓ Database created with V2 schema")

        # Check that V2 tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert 'categories' in tables, "categories table missing"
        assert 'reading_stats' in tables, "reading_stats table missing"
        assert 'settings' in tables, "settings table missing"
        print("✓ All V2 tables present")

        # Check V2 columns in feeds table
        cursor.execute("PRAGMA table_info(feeds)")
        feed_columns = {row[1] for row in cursor.fetchall()}
        assert 'category_id' in feed_columns, "category_id column missing"
        assert 'refresh_interval' in feed_columns, "refresh_interval column missing"
        assert 'last_refresh' in feed_columns, "last_refresh column missing"
        print("✓ V2 columns added to feeds table")

        # Check V2 columns in articles table
        cursor.execute("PRAGMA table_info(articles)")
        article_columns = {row[1] for row in cursor.fetchall()}
        assert 'read_date' in article_columns, "read_date column missing"
        print("✓ V2 columns added to articles table")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Database V2 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_categories():
    """Test category management."""
    print("\n" + "=" * 60)
    print("Testing Categories...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_v2.db")

        # Add categories
        tech_id = db.add_category("Tech", "#2196F3")
        news_id = db.add_category("News", "#FF5722")
        print(f"✓ Added categories (Tech: {tech_id}, News: {news_id})")

        # Get categories
        categories = db.get_categories()
        assert len(categories) >= 2, "Categories not retrieved"
        print(f"✓ Retrieved {len(categories)} categories")

        # Add feed with category
        test_url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
        db.add_feed(test_url, "NASA News", category_id=tech_id)
        print("✓ Added feed with category")

        # Get feeds by category
        feeds = db.get_feeds()
        nasa_feed = next((f for f in feeds if f['url'] == test_url), None)
        assert nasa_feed is not None, "Feed not found"
        assert nasa_feed['category_id'] == tech_id, "Category not assigned"
        print("✓ Feed category verified")

        # Update feed category
        db.update_feed_settings(test_url, category_id=news_id, refresh_interval=30)
        feeds = db.get_feeds()
        nasa_feed = next((f for f in feeds if f['url'] == test_url), None)
        assert nasa_feed['category_id'] == news_id, "Category not updated"
        assert nasa_feed['refresh_interval'] == 30, "Refresh interval not updated"
        print("✓ Feed settings updated")

        # Remove category
        db.remove_category(news_id)
        categories = db.get_categories()
        assert not any(c['id'] == news_id for c in categories), "Category not removed"
        print("✓ Category removed")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Categories test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_opml():
    """Test OPML import/export."""
    print("\n" + "=" * 60)
    print("Testing OPML Import/Export...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_v2.db")

        # Prepare test data
        tech_id = db.add_category("Technology", "#2196F3")
        db.add_feed("https://techcrunch.com/feed/", "TechCrunch", category_id=tech_id)
        db.add_feed("https://news.ycombinator.com/rss", "Hacker News", category_id=tech_id)

        # Export to OPML
        feeds = []
        for feed in db.get_feeds():
            feed_dict = {
                'title': feed['title'],
                'url': feed['url'],
                'category_id': feed.get('category_id')
            }
            feeds.append(feed_dict)

        categories = db.get_categories()

        opml_file = "test_export.opml"
        success = OPMLHandler.export_to_opml(feeds, categories, opml_file)
        assert success, "OPML export failed"
        assert os.path.exists(opml_file), "OPML file not created"
        print(f"✓ Exported {len(feeds)} feeds to OPML")

        # Verify OPML content
        with open(opml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '<?xml' in content, "Missing XML declaration"
            assert '<opml' in content and 'version="2.0"' in content, "Invalid OPML version"
            assert 'TechCrunch' in content, "Feed not in OPML"
            assert 'Technology' in content, "Category not in OPML"
        print("✓ OPML format verified")

        # Import OPML (test parsing)
        imported_feeds, imported_cats = OPMLHandler.import_from_opml(opml_file)
        assert len(imported_feeds) > 0, "No feeds imported"
        print(f"✓ Imported {len(imported_feeds)} feeds, {len(imported_cats)} categories")

        # Cleanup
        os.remove(opml_file)

        db.close()
        return True
    except Exception as e:
        print(f"✗ OPML test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_themes():
    """Test theme system."""
    print("\n" + "=" * 60)
    print("Testing Themes...")
    print("=" * 60)

    try:
        # Test Light Theme
        light = LightTheme()
        assert light.bg_primary == '#FFFFFF', "Light theme bg_primary incorrect"
        assert light.fg_primary == '#212121', "Light theme fg_primary incorrect"
        print("✓ Light theme initialized")

        # Test Dark Theme
        dark = DarkTheme()
        assert dark.bg_primary == '#1E1E1E', "Dark theme bg_primary incorrect"
        assert dark.fg_primary == '#E0E0E0', "Dark theme fg_primary incorrect"
        print("✓ Dark theme initialized")

        # Test theme properties
        assert hasattr(light, 'accent'), "Light theme missing accent"
        assert hasattr(dark, 'accent'), "Dark theme missing accent"
        print("✓ Theme properties verified")

        return True
    except Exception as e:
        print(f"✗ Themes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics():
    """Test reading statistics."""
    print("\n" + "=" * 60)
    print("Testing Reading Statistics...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_v2.db")

        # Fetch some real articles for testing
        fetcher = RSSFetcher(timeout=15)
        test_url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"

        # Make sure feed exists
        if not any(f['url'] == test_url for f in db.get_feeds()):
            db.add_feed(test_url, "NASA News")

        articles = fetcher.fetch_feed(test_url)
        db.cache_articles(articles, test_url)
        print(f"✓ Cached {len(articles)} articles")

        # Mark some as read
        cached = db.get_cached_articles(test_url, limit=5)
        for article in cached[:3]:
            db.mark_as_read(article['id'], True)
        print("✓ Marked 3 articles as read")

        # Get statistics
        stats = db.get_reading_statistics(days=30)
        assert 'total_read' in stats, "total_read missing from stats"
        assert 'avg_per_day' in stats, "avg_per_day missing from stats"
        assert 'daily_stats' in stats, "daily_stats missing from stats"
        assert 'total_feeds' in stats, "total_feeds missing from stats"
        assert 'unread_count' in stats, "unread_count missing from stats"
        print(f"✓ Statistics retrieved: {stats['total_read']} read, {stats['unread_count']} unread")

        # Test different time periods
        stats_7 = db.get_reading_statistics(days=7)
        stats_90 = db.get_reading_statistics(days=90)
        print(f"✓ Statistics for 7 days: {stats_7['total_read']} read")
        print(f"✓ Statistics for 90 days: {stats_90['total_read']} read")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_settings():
    """Test settings management."""
    print("\n" + "=" * 60)
    print("Testing Settings...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_v2.db")

        # Set and get settings
        db.set_setting("theme", "dark")
        theme = db.get_setting("theme")
        assert theme == "dark", "Setting not saved"
        print("✓ Setting saved and retrieved")

        # Update setting
        db.set_setting("theme", "light")
        theme = db.get_setting("theme")
        assert theme == "light", "Setting not updated"
        print("✓ Setting updated")

        # Get non-existent setting with default
        value = db.get_setting("nonexistent", "default_value")
        assert value == "default_value", "Default value not returned"
        print("✓ Default value returned for non-existent setting")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Settings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_refresh():
    """Test smart refresh intervals."""
    print("\n" + "=" * 60)
    print("Testing Smart Refresh Intervals...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_v2.db")

        # Add feeds with different refresh intervals
        db.add_feed("https://example.com/feed1", "Feed 1", refresh_interval=15)
        db.add_feed("https://example.com/feed2", "Feed 2", refresh_interval=60)
        db.add_feed("https://example.com/feed3", "Feed 3", refresh_interval=180)
        print("✓ Added feeds with different refresh intervals")

        # Update last refresh for feed1
        from datetime import datetime, timedelta
        old_time = (datetime.now() - timedelta(minutes=20)).isoformat()
        db.conn.execute("UPDATE feeds SET last_refresh = ? WHERE url = ?",
                       (old_time, "https://example.com/feed1"))
        db.conn.commit()

        # Get feeds needing refresh
        needs_refresh = db.get_feeds_needing_refresh()
        print(f"✓ Found {len(needs_refresh)} feeds needing refresh")

        # Feed1 should need refresh (20 minutes old, interval 15 minutes)
        feed1_needs = any(f['url'] == "https://example.com/feed1" for f in needs_refresh)
        assert feed1_needs, "Feed1 should need refresh"
        print("✓ Correctly identified feeds needing refresh")

        # Update last refresh time
        db.update_last_refresh("https://example.com/feed1")
        feeds = db.get_feeds()
        feed1 = next((f for f in feeds if f['url'] == "https://example.com/feed1"), None)
        assert feed1['last_refresh'] is not None, "Last refresh not updated"
        print("✓ Last refresh time updated")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Smart refresh test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test files."""
    files_to_remove = ["test_v2.db", "test_export.opml"]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    print("\n✓ Cleaned up test files")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("RSSreaderV2 - Feature Test Suite")
    print("=" * 60)

    results = {
        "Database V2": test_database_v2(),
        "Categories": test_categories(),
        "OPML Import/Export": test_opml(),
        "Themes": test_themes(),
        "Statistics": test_statistics(),
        "Settings": test_settings(),
        "Smart Refresh": test_smart_refresh()
    }

    # Cleanup
    cleanup()

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:30s} {status}")

    print("=" * 60)

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All V2 tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")

    print("\nRSSreaderV2 Features Tested:")
    print("  ✓ Enhanced database schema with V2 tables")
    print("  ✓ Categories/folders for feed organization")
    print("  ✓ OPML import/export")
    print("  ✓ Light and Dark themes")
    print("  ✓ Reading statistics")
    print("  ✓ Settings management")
    print("  ✓ Smart refresh intervals")
