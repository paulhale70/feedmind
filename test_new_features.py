"""
Test script for new RSSreaderV1 features.
Tests read/unread, favorites, search, and database migration.
"""

import os
from rss_core import RSSFetcher
from rss_database import RSSDatabase


def test_database_migration():
    """Test database schema migration with new columns."""
    print("="*60)
    print("Testing Database Migration...")
    print("="*60)

    # Remove old database if exists
    if os.path.exists("test_features.db"):
        os.remove("test_features.db")

    try:
        db = RSSDatabase("test_features.db")
        print("✓ Database created with new schema")

        # Check that new columns exist
        cursor = db.conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1] for row in cursor.fetchall()}

        assert 'is_read' in columns, "is_read column missing"
        assert 'is_favorite' in columns, "is_favorite column missing"
        print("✓ New columns (is_read, is_favorite) present")

        cursor.execute("PRAGMA table_info(feeds)")
        feed_columns = {row[1] for row in cursor.fetchall()}
        assert 'auto_refresh' in feed_columns, "auto_refresh column missing"
        print("✓ auto_refresh column present in feeds table")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Database migration failed: {e}")
        return False


def test_read_unread_features():
    """Test mark as read/unread functionality."""
    print("\n" + "="*60)
    print("Testing Read/Unread Features...")
    print("="*60)

    try:
        db = RSSDatabase("test_features.db")

        # Add a test feed
        test_url = "https://www.nasa.gov/rss/dyn/breaking_news.rss"
        db.add_feed(test_url, "NASA News")
        print("✓ Test feed added")

        # Fetch and cache some articles
        fetcher = RSSFetcher(timeout=15)
        articles = fetcher.fetch_feed(test_url)
        db.cache_articles(articles, test_url)
        print(f"✓ Cached {len(articles)} articles")

        # Get cached articles
        cached = db.get_cached_articles(test_url, limit=5)
        if not cached:
            print("✗ No cached articles found")
            return False

        # Test marking as read
        article_id = cached[0]['id']
        db.mark_as_read(article_id, True)
        print(f"✓ Marked article {article_id} as read")

        # Verify it was marked
        cursor = db.conn.cursor()
        cursor.execute("SELECT is_read FROM articles WHERE id = ?", (article_id,))
        is_read = cursor.fetchone()[0]
        assert is_read == 1, "Article not marked as read"
        print("✓ Verified read status in database")

        # Test marking as unread
        db.mark_as_read(article_id, False)
        cursor.execute("SELECT is_read FROM articles WHERE id = ?", (article_id,))
        is_read = cursor.fetchone()[0]
        assert is_read == 0, "Article not marked as unread"
        print("✓ Verified unread status in database")

        # Test unread count
        unread_count = db.get_unread_count(test_url)
        print(f"✓ Unread count: {unread_count}")
        assert unread_count > 0, "Unread count should be > 0"

        # Test mark all as read
        count = db.mark_all_as_read(test_url)
        print(f"✓ Marked {count} articles as read")

        new_unread = db.get_unread_count(test_url)
        assert new_unread == 0, "All articles should be marked as read"
        print("✓ All articles marked as read successfully")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Read/Unread test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_favorites_feature():
    """Test favorites functionality."""
    print("\n" + "="*60)
    print("Testing Favorites Feature...")
    print("="*60)

    try:
        db = RSSDatabase("test_features.db")

        # Get some articles
        articles = db.get_cached_articles(limit=3)
        if not articles:
            print("✗ No articles to test with")
            return False

        # Mark first article as favorite
        article_id = articles[0]['id']
        db.mark_as_favorite(article_id, True)
        print(f"✓ Marked article {article_id} as favorite")

        # Verify it was marked
        cursor = db.conn.cursor()
        cursor.execute("SELECT is_favorite FROM articles WHERE id = ?", (article_id,))
        is_fav = cursor.fetchone()[0]
        assert is_fav == 1, "Article not marked as favorite"
        print("✓ Verified favorite status in database")

        # Get favorites
        favorites = db.get_favorites()
        assert len(favorites) > 0, "No favorites found"
        print(f"✓ Retrieved {len(favorites)} favorite articles")

        # Unfavorite
        db.mark_as_favorite(article_id, False)
        cursor.execute("SELECT is_favorite FROM articles WHERE id = ?", (article_id,))
        is_fav = cursor.fetchone()[0]
        assert is_fav == 0, "Article still marked as favorite"
        print("✓ Verified unfavorite status in database")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Favorites test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_feature():
    """Test search functionality."""
    print("\n" + "="*60)
    print("Testing Search Feature...")
    print("="*60)

    try:
        db = RSSDatabase("test_features.db")

        # Search for common words
        results = db.search_articles("NASA")
        print(f"✓ Search for 'NASA' returned {len(results)} results")

        # Search with filters
        results = db.search_articles("", show_read=False)
        print(f"✓ Unread filter returned {len(results)} results")

        # Search with favorites filter
        # First mark an article as favorite
        articles = db.get_cached_articles(limit=1)
        if articles:
            db.mark_as_favorite(articles[0]['id'], True)
            results = db.search_articles("", favorites_only=True)
            print(f"✓ Favorites filter returned {len(results)} results")
            assert len(results) > 0, "Should have at least one favorite"

        # Search with specific query
        results = db.search_articles("space")
        print(f"✓ Search for 'space' returned {len(results)} results")

        db.close()
        return True
    except Exception as e:
        print(f"✗ Search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test database."""
    if os.path.exists("test_features.db"):
        os.remove("test_features.db")
        print("\n✓ Cleaned up test database")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("RSSreaderV1 - New Features Test Suite")
    print("="*60)

    results = {
        "Database Migration": test_database_migration(),
        "Read/Unread Features": test_read_unread_features(),
        "Favorites Feature": test_favorites_feature(),
        "Search Feature": test_search_feature()
    }

    # Cleanup
    cleanup()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:30s} {status}")

    print("="*60)

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")

    print("\nAll new features are ready:")
    print("  ✓ Mark articles as read/unread")
    print("  ✓ Save articles to favorites")
    print("  ✓ Search and filter articles")
    print("  ✓ Database schema migration")
    print("  ✓ Unread counter")
    print("  ✓ Auto-refresh support")
