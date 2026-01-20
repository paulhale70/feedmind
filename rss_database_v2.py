"""
RSS Reader Database Module V2
Enhanced with categories, statistics, and per-feed settings.
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSDatabase:
    """Manages SQLite database for RSS Reader V2 with enhanced features."""

    def __init__(self, db_path: str = "rss_reader_v2.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()

    def _init_database(self):
        """Initialize the database and create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Create categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#2196F3',
                created_date TEXT NOT NULL
            )
        """)

        # Create feeds table (subscriptions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                added_date TEXT NOT NULL,
                category_id INTEGER,
                refresh_interval INTEGER DEFAULT 15,
                last_refresh TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
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
                is_read INTEGER DEFAULT 0,
                read_date TEXT,
                is_favorite INTEGER DEFAULT 0,
                UNIQUE(feed_url, link)
            )
        """)

        # Create settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # Create reading statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reading_stats (
                date TEXT PRIMARY KEY,
                articles_read INTEGER DEFAULT 0,
                time_spent_minutes INTEGER DEFAULT 0
            )
        """)

        # Migrate existing databases
        self._migrate_database(cursor)

        # Initialize default category if needed
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO categories (name, color, created_date)
                VALUES ('Uncategorized', '#9E9E9E', ?)
            """, (datetime.now().isoformat(),))

        self.conn.commit()
        logger.info(f"Database V2 initialized at {self.db_path}")

    def _migrate_database(self, cursor):
        """Add new columns to existing databases if they don't exist."""
        # Check articles table
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1] for row in cursor.fetchall()}

        if 'is_read' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN is_read INTEGER DEFAULT 0")
        if 'read_date' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN read_date TEXT")
        if 'is_favorite' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN is_favorite INTEGER DEFAULT 0")

        # Check feeds table
        cursor.execute("PRAGMA table_info(feeds)")
        feed_columns = {row[1] for row in cursor.fetchall()}

        if 'category_id' not in feed_columns:
            cursor.execute("ALTER TABLE feeds ADD COLUMN category_id INTEGER")
        if 'refresh_interval' not in feed_columns:
            cursor.execute("ALTER TABLE feeds ADD COLUMN refresh_interval INTEGER DEFAULT 15")
        if 'last_refresh' not in feed_columns:
            cursor.execute("ALTER TABLE feeds ADD COLUMN last_refresh TEXT")

    # Category Management
    def add_category(self, name: str, color: str = '#2196F3') -> Optional[int]:
        """Add a new category. Returns category ID on success, None on failure."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO categories (name, color, created_date)
                VALUES (?, ?, ?)
            """, (name, color, datetime.now().isoformat()))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_categories(self) -> list[dict]:
        """Get all categories."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def delete_category(self, category_id: int):
        """Delete a category (feeds will be set to Uncategorized)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        self.conn.commit()

    # Feed Management
    def add_feed(self, url: str, title: Optional[str] = None, category_id: Optional[int] = None,
                 refresh_interval: int = 15) -> bool:
        """Add a new feed subscription."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO feeds (url, title, added_date, category_id, refresh_interval)
                VALUES (?, ?, ?, ?, ?)
            """, (url, title or url, datetime.now().isoformat(), category_id, refresh_interval))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_feed_category(self, feed_url: str, category_id: Optional[int]):
        """Update feed category."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE feeds SET category_id = ? WHERE url = ?
        """, (category_id, feed_url))
        self.conn.commit()

    def update_feed_refresh_interval(self, feed_url: str, interval_minutes: int):
        """Update feed refresh interval."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE feeds SET refresh_interval = ? WHERE url = ?
        """, (interval_minutes, feed_url))
        self.conn.commit()

    def update_feed_last_refresh(self, feed_url: str):
        """Update last refresh timestamp."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE feeds SET last_refresh = ? WHERE url = ?
        """, (datetime.now().isoformat(), feed_url))
        self.conn.commit()

    def remove_feed(self, url: str) -> bool:
        """Remove a feed subscription and its cached articles."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM feeds WHERE url = ?", (url,))
        cursor.execute("DELETE FROM articles WHERE feed_url = ?", (url,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_all_feeds(self, category_id: Optional[int] = None) -> list[dict]:
        """Get all subscribed feeds, optionally filtered by category."""
        cursor = self.conn.cursor()
        if category_id is not None:
            cursor.execute("""
                SELECT * FROM feeds
                WHERE category_id = ? OR (category_id IS NULL AND ? IS NULL)
                ORDER BY title
            """, (category_id, category_id))
        else:
            cursor.execute("SELECT * FROM feeds ORDER BY title")
        return [dict(row) for row in cursor.fetchall()]

    def get_feeds_needing_refresh(self) -> list[dict]:
        """Get feeds that need refreshing based on their interval."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM feeds
            WHERE last_refresh IS NULL
               OR datetime(last_refresh, '+' || refresh_interval || ' minutes') <= datetime('now')
            ORDER BY last_refresh ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    # Article Management
    def cache_articles(self, articles: list, feed_url: str):
        """Cache articles from a feed."""
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

    def get_cached_articles(self, feed_url: Optional[str] = None, limit: int = 100) -> list[dict]:
        """Get cached articles, optionally filtered by feed URL."""
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

    def mark_as_read(self, article_id: int, is_read: bool = True) -> bool:
        """Mark an article as read or unread."""
        cursor = self.conn.cursor()
        read_date = datetime.now().isoformat() if is_read else None
        cursor.execute("""
            UPDATE articles
            SET is_read = ?, read_date = ?
            WHERE id = ?
        """, (1 if is_read else 0, read_date, article_id))
        self.conn.commit()

        # Update statistics
        if is_read:
            self._increment_reading_stat()

        return cursor.rowcount > 0

    def mark_as_favorite(self, article_id: int, is_favorite: bool = True) -> bool:
        """Mark an article as favorite or unfavorite."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE articles
            SET is_favorite = ?
            WHERE id = ?
        """, (1 if is_favorite else 0, article_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_favorites(self, limit: int = 100) -> list[dict]:
        """Get all favorite articles."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM articles
            WHERE is_favorite = 1
            ORDER BY published DESC, cached_date DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_unread_count(self, feed_url: Optional[str] = None) -> int:
        """Get count of unread articles."""
        cursor = self.conn.cursor()
        if feed_url:
            cursor.execute("""
                SELECT COUNT(*) FROM articles
                WHERE is_read = 0 AND feed_url = ?
            """, (feed_url,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM articles
                WHERE is_read = 0
            """)
        return cursor.fetchone()[0]

    def search_articles(self, query: str, feed_url: Optional[str] = None,
                       show_read: bool = True, favorites_only: bool = False,
                       limit: int = 100) -> list[dict]:
        """Search articles by title or description."""
        cursor = self.conn.cursor()

        conditions = []
        params = []

        if query:
            conditions.append("(title LIKE ? OR description LIKE ?)")
            search_pattern = f"%{query}%"
            params.extend([search_pattern, search_pattern])

        if feed_url:
            conditions.append("feed_url = ?")
            params.append(feed_url)

        if not show_read:
            conditions.append("is_read = 0")

        if favorites_only:
            conditions.append("is_favorite = 1")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        cursor.execute(f"""
            SELECT * FROM articles
            WHERE {where_clause}
            ORDER BY published DESC, cached_date DESC
            LIMIT ?
        """, params)

        return [dict(row) for row in cursor.fetchall()]

    def mark_all_as_read(self, feed_url: Optional[str] = None) -> int:
        """Mark all articles as read."""
        cursor = self.conn.cursor()
        read_date = datetime.now().isoformat()

        if feed_url:
            cursor.execute("""
                UPDATE articles
                SET is_read = 1, read_date = ?
                WHERE feed_url = ? AND is_read = 0
            """, (read_date, feed_url))
        else:
            cursor.execute("""
                UPDATE articles
                SET is_read = 1, read_date = ?
                WHERE is_read = 0
            """, (read_date,))

        count = cursor.rowcount
        self.conn.commit()
        return count

    def clear_old_articles(self, days: int = 30):
        """Remove articles older than specified days."""
        cursor = self.conn.cursor()
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

        cursor.execute("""
            DELETE FROM articles
            WHERE cached_date < ?
        """, (cutoff_date,))

        deleted = cursor.rowcount
        self.conn.commit()
        logger.info(f"Deleted {deleted} old articles")

    # Statistics
    def _increment_reading_stat(self):
        """Increment today's reading count."""
        today = datetime.now().date().isoformat()
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO reading_stats (date, articles_read)
            VALUES (?, 1)
            ON CONFLICT(date) DO UPDATE SET articles_read = articles_read + 1
        """, (today,))
        self.conn.commit()

    def get_reading_statistics(self, days: int = 30) -> dict:
        """Get reading statistics for the last N days."""
        cursor = self.conn.cursor()
        since_date = (datetime.now() - timedelta(days=days)).date().isoformat()

        # Total articles read
        cursor.execute("""
            SELECT SUM(articles_read) FROM reading_stats
            WHERE date >= ?
        """, (since_date,))
        total_read = cursor.fetchone()[0] or 0

        # Daily breakdown
        cursor.execute("""
            SELECT date, articles_read FROM reading_stats
            WHERE date >= ?
            ORDER BY date DESC
        """, (since_date,))
        daily_stats = [dict(row) for row in cursor.fetchall()]

        # Total feeds
        cursor.execute("SELECT COUNT(*) FROM feeds")
        total_feeds = cursor.fetchone()[0]

        # Total unread
        unread_count = self.get_unread_count()

        # Total favorites
        cursor.execute("SELECT COUNT(*) FROM articles WHERE is_favorite = 1")
        favorites_count = cursor.fetchone()[0]

        # Calculate average per day
        avg_per_day = total_read / days if days > 0 else 0

        return {
            'total_read': total_read,
            'avg_per_day': avg_per_day,
            'daily_stats': daily_stats,
            'total_feeds': total_feeds,
            'unread_count': unread_count,
            'favorites_count': favorites_count,
            'period_days': days
        }

    # Settings
    def get_setting(self, key: str, default: str = '') -> str:
        """Get a setting value."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key: str, value: str):
        """Set a setting value."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
        self.conn.commit()

    def update_feed_settings(self, feed_url: str, category_id: Optional[int] = None,
                           refresh_interval: Optional[int] = None):
        """Update feed category and/or refresh interval in one call."""
        cursor = self.conn.cursor()
        updates = []
        params = []

        if category_id is not None:
            updates.append("category_id = ?")
            params.append(category_id)

        if refresh_interval is not None:
            updates.append("refresh_interval = ?")
            params.append(refresh_interval)

        if updates:
            params.append(feed_url)
            query = f"UPDATE feeds SET {', '.join(updates)} WHERE url = ?"
            cursor.execute(query, params)
            self.conn.commit()

    # Compatibility methods for consistency with V1 and main app
    def get_feeds(self, category_id: Optional[int] = None) -> list[dict]:
        """Alias for get_all_feeds for compatibility."""
        return self.get_all_feeds(category_id)

    def update_last_refresh(self, feed_url: str):
        """Alias for update_feed_last_refresh for compatibility."""
        self.update_feed_last_refresh(feed_url)

    def remove_category(self, category_id: int):
        """Alias for delete_category for compatibility."""
        self.delete_category(category_id)

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
