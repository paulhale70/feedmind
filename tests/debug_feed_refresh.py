#!/usr/bin/env python3
"""
Debug tool for troubleshooting feed refresh issues.
This will help identify why new episodes aren't appearing.
"""

import sys
import sqlite3
from datetime import datetime
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
from rss_database_v3 import RSSDatabase

def debug_feed_refresh(feed_title_search: str):
    """Debug why a feed isn't showing new articles."""

    print(f"=" * 80)
    print(f"FeedMind Feed Refresh Debugger")
    print(f"=" * 80)

    # Connect to database
    try:
        db = RSSDatabase("feedmind.db")
        print("✓ Connected to feedmind.db\n")
    except Exception as e:
        print(f"✗ Cannot connect to database: {e}")
        print("\nMake sure you're running this from the FeedMind directory")
        print("where feedmind.db is located.")
        return

    # Find the feed
    print(f"Searching for feed: '{feed_title_search}'...")
    feeds = db.get_feeds()
    matching_feeds = [f for f in feeds
                     if feed_title_search.lower() in f['title'].lower()
                     or feed_title_search.lower() in f['url'].lower()]

    if not matching_feeds:
        print(f"✗ No feed found matching '{feed_title_search}'")
        print("\nAvailable feeds:")
        for feed in feeds:
            print(f"  - {feed['title']}")
        return

    feed = matching_feeds[0]
    print(f"✓ Found feed: {feed['title']}\n")

    print(f"Feed Information:")
    print(f"  URL: {feed['url']}")
    print(f"  Last refresh: {feed['last_refresh']}")
    print(f"  Added: {feed['added_date']}")
    print()

    # Get current cached articles
    cached_articles = db.get_cached_articles(feed['url'])
    print(f"Currently cached articles: {len(cached_articles)}")

    if cached_articles:
        print(f"\nMost recent 5 cached episodes:")
        for i, art in enumerate(sorted(cached_articles,
                                       key=lambda a: a.get('published', ''),
                                       reverse=True)[:5], 1):
            print(f"  {i}. {art['title']}")
            print(f"     Published: {art['published']}")
            print(f"     Cached: {art['cached_date'][:19]}")
            print(f"     Link: {art['link'][:60]}...")

    # Fetch fresh articles from feed
    print(f"\n{'=' * 80}")
    print(f"Fetching fresh articles from feed...")
    print(f"{'=' * 80}\n")

    try:
        fetcher = RSSFetcher()
        fresh_articles = fetcher.fetch_feed(feed['url'])
        print(f"✓ Fetched {len(fresh_articles)} articles from feed\n")

        print(f"Most recent 5 episodes in feed:")
        for i, art in enumerate(fresh_articles[:5], 1):
            print(f"  {i}. {art.title}")
            print(f"     Published: {art.published}")
            print(f"     Link: {art.link[:60]}...")

        # Compare what's new
        print(f"\n{'=' * 80}")
        print(f"Comparing cached vs fresh articles...")
        print(f"{'=' * 80}\n")

        cached_links = {art['link'] for art in cached_articles}
        fresh_links = {art.link for art in fresh_articles}

        new_links = fresh_links - cached_links
        removed_links = cached_links - fresh_links

        print(f"Analysis:")
        print(f"  Total in database: {len(cached_links)}")
        print(f"  Total in feed: {len(fresh_links)}")
        print(f"  New episodes (not in DB): {len(new_links)}")
        print(f"  Old episodes (no longer in feed): {len(removed_links)}")

        if new_links:
            print(f"\n✓ NEW EPISODES AVAILABLE ({len(new_links)}):")
            new_articles = [art for art in fresh_articles if art.link in new_links]
            for i, art in enumerate(sorted(new_articles,
                                          key=lambda a: a.published,
                                          reverse=True), 1):
                print(f"  {i}. {art.title}")
                print(f"     Published: {art.published}")

            print(f"\n{'=' * 80}")
            print(f"SOLUTION: Click 'Refresh Feed' button to add these new episodes!")
            print(f"{'=' * 80}")
        else:
            print(f"\n✓ Database is up to date - no new episodes available")
            print(f"\nThis means the podcast hasn't released new episodes,")
            print(f"or the feed only keeps the most recent episodes.")

        # Test caching
        print(f"\n{'=' * 80}")
        print(f"Testing cache mechanism...")
        print(f"{'=' * 80}\n")

        cached_count = db.cache_articles(fresh_articles, feed['url'])
        print(f"Cache test result: {cached_count} new articles added")

        if cached_count > 0:
            print(f"\n✓ SUCCESS! {cached_count} new articles were added to database")
            print(f"  Refresh FeedMind to see them")
        elif new_links:
            print(f"\n✗ WARNING: Expected to add {len(new_links)} articles but added {cached_count}")
            print(f"  This indicates a caching problem")
        else:
            print(f"\n✓ No new articles to cache (database already up to date)")

    except Exception as e:
        print(f"✗ Error fetching feed: {e}")
        import traceback
        traceback.print_exc()

    db.conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_feed_refresh.py <feed_name>")
        print("\nExample:")
        print("  python debug_feed_refresh.py smartless")
        print("  python debug_feed_refresh.py \"NASA Podcast\"")
        sys.exit(1)

    feed_search = " ".join(sys.argv[1:])
    debug_feed_refresh(feed_search)
