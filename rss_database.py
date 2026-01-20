"""
RSS Reader Database Module
Handles caching and storage of RSS feeds using SQLite.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSDatabase:
    """Manages SQLite database for caching RSS feeds and subscriptions."""

    def __init__(self, db_path: str = "rss_reader.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()

    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Create feeds table (subscriptions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                added_date TEXT NOT NULL
            )
        """)

        # Create articles table (cached articles)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_url TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL,
                description TEXT,
                published TEXT,
                cached_date TEXT NOT NULL,
                UNIQUE(feed_url, link)
            )
        """)

        self.conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def add_feed(self, url: str, title: Optional[str] = None) -> bool:
        """
        Add a new feed subscription.

        Args:
            url: The RSS feed URL
            title: Optional title for the feed

        Returns:
            True if added successfully, False if already exists
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO feeds (url, title, added_date)
                VALUES (?, ?, ?)
            """, (url, title or url, datetime.now().isoformat()))
            self.conn.commit()
            logger.info(f"Added feed: {url}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Feed already exists: {url}")
            return False

    def remove_feed(self, url: str) -> bool:
        """
        Remove a feed subscription and its cached articles.

        Args:
            url: The RSS feed URL to remove

        Returns:
            True if removed successfully
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM feeds WHERE url = ?", (url,))
        cursor.execute("DELETE FROM articles WHERE feed_url = ?", (url,))
        self.conn.commit()
        logger.info(f"Removed feed and its articles: {url}")
        return cursor.rowcount > 0

    def get_all_feeds(self) -> list[dict]:
        """
        Get all subscribed feeds.

        Returns:
            List of feed dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM feeds ORDER BY added_date DESC")
        return [dict(row) for row in cursor.fetchall()]

    def cache_articles(self, articles: list, feed_url: str):
        """
        Cache articles from a feed.

        Args:
            articles: List of RSSFeed objects
            feed_url: The feed URL these articles belong to
        """
        cursor = self.conn.cursor()
        cached_count = 0

        for article in articles:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO articles
                    (feed_url, title, link, description, published, cached_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    feed_url,
                    article.title,
                    article.link,
                    article.description,
                    article.published,
                    datetime.now().isoformat()
                ))
                cached_count += 1
            except Exception as e:
                logger.warning(f"Failed to cache article: {e}")

        self.conn.commit()
        logger.info(f"Cached {cached_count} articles from {feed_url}")

    def get_cached_articles(self, feed_url: Optional[str] = None,
                           limit: int = 100) -> list[dict]:
        """
        Get cached articles, optionally filtered by feed URL.

        Args:
            feed_url: Optional feed URL to filter by
            limit: Maximum number of articles to return

        Returns:
            List of article dictionaries
        """
        cursor = self.conn.cursor()

        if feed_url:
            cursor.execute("""
                SELECT * FROM articles
                WHERE feed_url = ?
                ORDER BY published DESC, cached_date DESC
                LIMIT ?
            """, (feed_url, limit))
        else:
            cursor.execute("""
                SELECT * FROM articles
                ORDER BY published DESC, cached_date DESC
                LIMIT ?
            """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def clear_old_articles(self, days: int = 30):
        """
        Remove articles older than specified days.

        Args:
            days: Number of days to keep articles
        """
        cursor = self.conn.cursor()
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)

        cursor.execute("""
            DELETE FROM articles
            WHERE cached_date < ?
        """, (cutoff_date.isoformat(),))

        deleted = cursor.rowcount
        self.conn.commit()
        logger.info(f"Deleted {deleted} old articles")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
