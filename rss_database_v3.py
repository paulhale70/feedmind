"""
RSS Reader Database Module V3
Extends V2 with podcast episode support and auto-refresh scheduling.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict
from rss_database_v2 import RSSDatabase as RSSDatabase_V2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSDatabase(RSSDatabase_V2):
    """Extends V2 database with podcast and scheduling features."""

    def __init__(self, db_path: str = "rss_reader_v3.db"):
        """Initialize V3 database with podcast support."""
        # V2's __init__ sets up the thread-local connection machinery and then
        # calls self._init_database(), which our override below extends with the
        # V3 tables. (The previous code connected twice — once here and again in
        # super().__init__() — leaking the first connection.)
        super().__init__(db_path)

    def _init_database(self):
        """Create the V2 schema, then add V3 podcast/scheduling tables."""
        super()._init_database()

        cursor = self.conn.cursor()

        # Create podcast episodes download table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS podcast_downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                audio_url TEXT NOT NULL,
                local_path TEXT,
                download_date TEXT,
                file_size INTEGER,
                duration_seconds INTEGER,
                download_status TEXT DEFAULT 'pending',
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                UNIQUE(article_id)
            )
        """)

        # Migrate to V3
        self._migrate_to_v3(cursor)

        self.conn.commit()
        logger.info(f"Database V3 initialized at {self.db_path}")

    def _migrate_to_v3(self, cursor):
        """Add V3 columns for podcast support and AI features."""
        # Check articles table for podcast columns
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1] for row in cursor.fetchall()}

        if 'audio_url' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN audio_url TEXT")
        if 'audio_type' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN audio_type TEXT")
        if 'audio_length' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN audio_length INTEGER")
        if 'duration_seconds' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN duration_seconds INTEGER")

        # V3.5: Add full text and AI summary columns
        if 'full_text' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN full_text TEXT")
        if 'full_text_extracted_date' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN full_text_extracted_date TEXT")
        if 'ai_summary' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN ai_summary TEXT")
        if 'ai_tldr' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN ai_tldr TEXT")
        if 'ai_key_points' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN ai_key_points TEXT")  # JSON string
        if 'ai_generated_date' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN ai_generated_date TEXT")

        # Check feeds table for scheduling columns
        cursor.execute("PRAGMA table_info(feeds)")
        feed_columns = {row[1] for row in cursor.fetchall()}

        if 'is_podcast' not in feed_columns:
            cursor.execute("ALTER TABLE feeds ADD COLUMN is_podcast INTEGER DEFAULT 0")
        if 'auto_refresh_enabled' not in feed_columns:
            cursor.execute("ALTER TABLE feeds ADD COLUMN auto_refresh_enabled INTEGER DEFAULT 1")

        # V3.7: Add bookmark column
        if 'is_bookmarked' not in feed_columns:
            cursor.execute("ALTER TABLE feeds ADD COLUMN is_bookmarked INTEGER DEFAULT 0")

        # V3.7.1: One-time cleanup of podcast episodes whose link doesn't match
        # their audio_url (a duplicate-link bug fixed in v3.7.1). They get
        # re-fetched on the next refresh with correct unique links.
        #
        # This DELETE is destructive, so it is gated behind PRAGMA user_version
        # and runs exactly once. Previously it ran on every startup, which could
        # wipe legitimately-stored rows whose link differs from audio_url.
        cursor.execute("PRAGMA user_version")
        schema_version = cursor.fetchone()[0]
        if schema_version < 1:
            cursor.execute("""
                DELETE FROM articles
                WHERE audio_url IS NOT NULL
                  AND audio_url != ''
                  AND link != audio_url
            """)
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info(f"Removed {deleted_count} duplicate podcast episodes. Use 'Refresh All' to restore them with unique links.")
            # user_version only accepts a literal, not a bound parameter; the
            # value here is a hard-coded int, so this is safe.
            cursor.execute("PRAGMA user_version = 1")

    # Podcast Episode Methods

    def get_podcast_episodes(self, feed_url: Optional[str] = None,
                            downloaded_only: bool = False,
                            limit: int = 100) -> List[Dict]:
        """
        Get podcast episodes (articles with audio).

        Args:
            feed_url: Optional feed URL to filter by
            downloaded_only: Only return downloaded episodes
            limit: Maximum episodes to return

        Returns:
            List of episode dictionaries
        """
        cursor = self.conn.cursor()

        if downloaded_only:
            # Get episodes with downloads
            query = """
                SELECT a.*, pd.local_path, pd.download_date, pd.duration_seconds as download_duration
                FROM articles a
                INNER JOIN podcast_downloads pd ON a.id = pd.article_id
                WHERE a.audio_url IS NOT NULL
                  AND pd.download_status = 'completed'
            """
            params = []
        else:
            # Get all episodes (with audio URL)
            query = """
                SELECT a.*, pd.local_path, pd.download_date
                FROM articles a
                LEFT JOIN podcast_downloads pd ON a.id = pd.article_id
                WHERE a.audio_url IS NOT NULL
            """
            params = []

        if feed_url:
            query += " AND a.feed_url = ?"
            params.append(feed_url)

        query += " ORDER BY a.published DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def mark_feed_as_podcast(self, feed_url: str, is_podcast: bool = True):
        """Mark a feed as a podcast feed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE feeds SET is_podcast = ? WHERE url = ?
        """, (1 if is_podcast else 0, feed_url))
        self.conn.commit()

    def is_podcast_feed(self, feed_url: str) -> bool:
        """Check if a feed is marked as a podcast."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT is_podcast FROM feeds WHERE url = ?
        """, (feed_url,))
        row = cursor.fetchone()
        return bool(row and row[0]) if row else False

    # V3.7: Feed Bookmark Methods

    def bookmark_feed(self, feed_url: str, is_bookmarked: bool = True):
        """Bookmark or unbookmark a feed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE feeds SET is_bookmarked = ? WHERE url = ?
        """, (1 if is_bookmarked else 0, feed_url))
        self.conn.commit()
        logger.info(f"Feed {'bookmarked' if is_bookmarked else 'unbookmarked'}: {feed_url}")

    def is_feed_bookmarked(self, feed_url: str) -> bool:
        """Check if a feed is bookmarked."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT is_bookmarked FROM feeds WHERE url = ?
        """, (feed_url,))
        row = cursor.fetchone()
        return bool(row and row[0]) if row else False

    def get_bookmarked_feeds(self) -> List[Dict]:
        """Get all bookmarked feeds."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM feeds WHERE is_bookmarked = 1
            ORDER BY title
        """)
        return [dict(row) for row in cursor.fetchall()]

    def add_podcast_download(self, article_id: int, audio_url: str,
                            local_path: str, file_size: int,
                            duration_seconds: int = 0) -> bool:
        """
        Add or update a podcast download record.

        Args:
            article_id: Article ID
            audio_url: URL of audio file
            local_path: Path where file is saved
            file_size: Size of downloaded file in bytes
            duration_seconds: Duration in seconds

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO podcast_downloads
                (article_id, audio_url, local_path, download_date, file_size,
                 duration_seconds, download_status)
                VALUES (?, ?, ?, ?, ?, ?, 'completed')
            """, (article_id, audio_url, local_path, datetime.now().isoformat(),
                  file_size, duration_seconds))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add podcast download: {e}")
            return False

    def get_download_path(self, article_id: int) -> Optional[str]:
        """Get local download path for an episode."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT local_path FROM podcast_downloads
            WHERE article_id = ? AND download_status = 'completed'
        """, (article_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def delete_download(self, article_id: int) -> bool:
        """Remove download record (does not delete file)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM podcast_downloads WHERE article_id = ?
        """, (article_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def get_all_downloads(self) -> List[Dict]:
        """Get all downloaded episodes."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT pd.*, a.title, a.feed_url
            FROM podcast_downloads pd
            JOIN articles a ON pd.article_id = a.id
            WHERE pd.download_status = 'completed'
            ORDER BY pd.download_date DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    # Auto-refresh Methods

    def set_feed_auto_refresh(self, feed_url: str, enabled: bool):
        """Enable/disable auto-refresh for a feed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE feeds SET auto_refresh_enabled = ? WHERE url = ?
        """, (1 if enabled else 0, feed_url))
        self.conn.commit()

    def get_feeds_for_auto_refresh(self) -> List[Dict]:
        """Get feeds that should be auto-refreshed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM feeds
            WHERE auto_refresh_enabled = 1
            ORDER BY last_refresh ASC
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_podcast_feeds(self) -> List[Dict]:
        """Get all podcast feeds."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM feeds WHERE is_podcast = 1
            ORDER BY title
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_article(self, article_id: int) -> Optional[Dict]:
        """Return a single article (all columns) as a dict, or None if absent.

        Gives the UI a typed accessor instead of reaching into conn.cursor().
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # Override cache_articles to handle audio enclosures
    def cache_articles(self, articles, feed_url: str):
        """Cache articles with podcast audio enclosure support."""
        cursor = self.conn.cursor()
        cached_count = 0
        failed_count = 0
        has_audio = False

        for article in articles:
            try:
                # Extract audio enclosure data if present
                audio_url = getattr(article, 'audio_url', None)
                audio_type = getattr(article, 'audio_type', None)
                audio_length = getattr(article, 'audio_length', None)
                duration_seconds = getattr(article, 'duration_seconds', 0)

                if audio_url:
                    has_audio = True

                # For podcasts with duplicate links, check by audio_url instead
                if audio_url:
                    # Check if this audio episode already exists
                    cursor.execute("""
                        SELECT id FROM articles
                        WHERE feed_url = ? AND audio_url = ?
                    """, (feed_url, audio_url))

                    if cursor.fetchone():
                        # Episode already exists, skip
                        continue

                    # Use audio_url as the link to avoid duplicate link conflicts
                    # This allows each episode to have a unique identifier
                    link_to_use = audio_url
                else:
                    link_to_use = article.link

                cursor.execute("""
                    INSERT OR IGNORE INTO articles
                    (feed_url, title, link, description, published, cached_date,
                     audio_url, audio_type, audio_length, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    feed_url,
                    article.title,
                    link_to_use,
                    article.description,
                    article.published,
                    datetime.now().isoformat(),
                    audio_url,
                    audio_type,
                    audio_length,
                    duration_seconds
                ))

                if cursor.rowcount > 0:
                    cached_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to cache article: {e}")

        self.conn.commit()

        if failed_count:
            logger.warning(
                f"cache_articles: {failed_count}/{len(articles)} articles failed "
                f"to cache for {feed_url}"
            )
            # Every article failing means a systemic problem (schema mismatch,
            # disk full, locked DB) rather than normal deduplication, where
            # cached_count is legitimately 0. Surface it so the caller reports an
            # error instead of a silent "refresh succeeded".
            if cached_count == 0 and failed_count == len(articles):
                raise RuntimeError(
                    f"All {failed_count} articles failed to cache for {feed_url}"
                )

        # Auto-mark feed as podcast if it has audio
        if has_audio:
            self.mark_feed_as_podcast(feed_url, True)

        return cached_count

    # Full-Text Article Methods

    def store_full_text(self, article_id: int, full_text: str) -> bool:
        """
        Store extracted full text for an article.

        Args:
            article_id: Article ID
            full_text: Extracted article text

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE articles
                SET full_text = ?, full_text_extracted_date = ?
                WHERE id = ?
            """, (full_text, datetime.now().isoformat(), article_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to store full text: {e}")
            return False

    def get_full_text(self, article_id: int) -> Optional[str]:
        """Get stored full text for an article."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT full_text FROM articles WHERE id = ?
        """, (article_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] else None

    def has_full_text(self, article_id: int) -> bool:
        """Check if article has full text extracted."""
        full_text = self.get_full_text(article_id)
        return full_text is not None and len(full_text) > 0

    # AI Summary Methods

    def store_ai_summary(self, article_id: int, summary: str,
                        tldr: Optional[str] = None,
                        key_points: Optional[List[str]] = None) -> bool:
        """
        Store AI-generated summary for an article.

        Args:
            article_id: Article ID
            summary: Generated summary
            tldr: TL;DR summary
            key_points: List of key points

        Returns:
            True if successful
        """
        try:
            import json

            cursor = self.conn.cursor()

            # Convert key points to JSON
            key_points_json = json.dumps(key_points) if key_points else None

            cursor.execute("""
                UPDATE articles
                SET ai_summary = ?,
                    ai_tldr = ?,
                    ai_key_points = ?,
                    ai_generated_date = ?
                WHERE id = ?
            """, (summary, tldr, key_points_json,
                  datetime.now().isoformat(), article_id))

            self.conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Failed to store AI summary: {e}")
            return False

    def get_ai_summary(self, article_id: int) -> Optional[Dict]:
        """
        Get AI-generated summary for an article.

        Returns:
            Dictionary with summary, tldr, key_points or None
        """
        try:
            import json

            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ai_summary, ai_tldr, ai_key_points, ai_generated_date
                FROM articles WHERE id = ?
            """, (article_id,))

            row = cursor.fetchone()
            if not row or not row[0]:
                return None

            key_points = None
            if row[2]:
                try:
                    key_points = json.loads(row[2])
                except:
                    key_points = []

            return {
                'summary': row[0],
                'tldr': row[1],
                'key_points': key_points,
                'generated_date': row[3]
            }

        except Exception as e:
            logger.error(f"Failed to get AI summary: {e}")
            return None

    def has_ai_summary(self, article_id: int) -> bool:
        """Check if article has AI summary."""
        summary = self.get_ai_summary(article_id)
        return summary is not None

    def get_articles_needing_extraction(self, limit: int = 10) -> List[Dict]:
        """
        Get articles that don't have full text extracted yet.

        Args:
            limit: Maximum articles to return

        Returns:
            List of article dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM articles
            WHERE full_text IS NULL AND link != ''
            ORDER BY published DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_articles_needing_summary(self, limit: int = 10) -> List[Dict]:
        """
        Get articles that have full text but no AI summary.

        Args:
            limit: Maximum articles to return

        Returns:
            List of article dictionaries
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM articles
            WHERE full_text IS NOT NULL
              AND ai_summary IS NULL
            ORDER BY published DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    # Compatibility wrapper methods
    def update_last_refresh(self, feed_url: str):
        """Alias for update_feed_last_refresh."""
        return self.update_feed_last_refresh(feed_url)

    def remove_category(self, category_id: int):
        """Alias for delete_category."""
        return self.delete_category(category_id)

    def update_feed_settings(self, feed_url: str, category_id=None, refresh_interval=None):
        """Update feed settings."""
        cursor = self.conn.cursor()
        if category_id is not None:
            self.update_feed_category(feed_url, category_id)
        if refresh_interval is not None:
            self.update_feed_refresh_interval(feed_url, refresh_interval)

    def get_all_feeds(self, category_id: Optional[int] = None):
        """Get all feeds, optionally filtered by category."""
        cursor = self.conn.cursor()
        if category_id is not None:
            cursor.execute("SELECT * FROM feeds WHERE category_id = ? ORDER BY title", (category_id,))
        else:
            cursor.execute("SELECT * FROM feeds ORDER BY title")
        return [dict(row) for row in cursor.fetchall()]

    def get_feeds(self, category_id: Optional[int] = None):
        """Alias for get_all_feeds for compatibility."""
        return self.get_all_feeds(category_id)


if __name__ == "__main__":
    # Test V3 database
    print("Testing V3 Database...")

    db = RSSDatabase("test_v3.db")
    print("✓ V3 Database initialized")

    # Check for V3 tables
    cursor = db.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}

    assert 'podcast_downloads' in tables, "podcast_downloads table missing"
    print("✓ podcast_downloads table exists")

    # Check V3 columns in articles
    cursor.execute("PRAGMA table_info(articles)")
    article_columns = {row[1] for row in cursor.fetchall()}

    assert 'audio_url' in article_columns, "audio_url column missing"
    assert 'audio_type' in article_columns, "audio_type column missing"
    assert 'duration_seconds' in article_columns, "duration_seconds column missing"
    print("✓ V3 columns added to articles table")

    # Check V3 columns in feeds
    cursor.execute("PRAGMA table_info(feeds)")
    feed_columns = {row[1] for row in cursor.fetchall()}

    assert 'is_podcast' in feed_columns, "is_podcast column missing"
    assert 'auto_refresh_enabled' in feed_columns, "auto_refresh_enabled column missing"
    print("✓ V3 columns added to feeds table")

    db.close()

    # Clean up
    import os
    if os.path.exists("test_v3.db"):
        os.remove("test_v3.db")

    print("\n🎉 V3 Database tests passed!")
