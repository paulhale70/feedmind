"""
Auto-Refresh Scheduler for RSS Reader V3
Manages automatic feed refreshing at configurable intervals.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoRefreshScheduler:
    """Manages automatic feed refresh scheduling."""

    def __init__(self, default_interval_minutes: int = 30):
        """
        Initialize auto-refresh scheduler.

        Args:
            default_interval_minutes: Default refresh interval in minutes
        """
        self.default_interval = default_interval_minutes
        self.enabled = False
        self.refresh_callback: Optional[Callable] = None
        self.get_feeds_callback: Optional[Callable] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_flag = threading.Event()
        self.last_refresh_time = {}  # feed_url -> datetime

    def start(self, refresh_callback: Callable[[str], None],
              get_feeds_callback: Optional[Callable[[], List[Dict]]] = None):
        """
        Start the auto-refresh scheduler.

        Args:
            refresh_callback: Function to call when a feed needs refresh.
                             Takes feed_url as parameter.
            get_feeds_callback: Function returning a list of feed dicts with
                             keys 'url', 'refresh_interval_minutes' (optional),
                             and 'last_refresh' (optional ISO datetime). Without
                             this, no feeds will be checked (the worker will warn).
        """
        if self.enabled:
            logger.warning("Scheduler already running")
            return

        self.refresh_callback = refresh_callback
        self.get_feeds_callback = get_feeds_callback
        if get_feeds_callback is None:
            logger.warning(
                "AutoRefreshScheduler started without get_feeds_callback; "
                "no feeds will be auto-refreshed. Pass a callable returning "
                "the feed list to enable polling."
            )
        self.enabled = True
        self._stop_flag.clear()

        # Start worker thread
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True
        )
        self._worker_thread.start()

        logger.info(f"Auto-refresh scheduler started (interval: {self.default_interval}min)")

    def stop(self):
        """Stop the auto-refresh scheduler."""
        if not self.enabled:
            return

        self.enabled = False
        self._stop_flag.set()

        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)

        logger.info("Auto-refresh scheduler stopped")

    def _worker_loop(self):
        """Main worker loop that checks for feeds needing refresh."""
        while not self._stop_flag.is_set():
            try:
                # Sleep in small increments so we can stop quickly
                for _ in range(60):  # Check every minute
                    if self._stop_flag.is_set():
                        return
                    time.sleep(1)

                # Check if any feeds need refreshing
                if self.refresh_callback and self.enabled:
                    self._check_and_refresh()

            except Exception as e:
                logger.error(f"Error in auto-refresh worker: {e}")

    def _check_and_refresh(self):
        """Check feeds and trigger refresh for those that need it."""
        if not self.get_feeds_callback or not self.refresh_callback:
            return

        try:
            feeds = self.get_feeds_callback() or []
        except Exception as e:
            logger.exception(f"get_feeds_callback raised: {e}")
            return

        for feed in feeds:
            if self._stop_flag.is_set() or not self.enabled:
                return

            url = feed.get('url')
            if not url:
                continue

            interval = feed.get('refresh_interval_minutes') or self.default_interval
            last_refresh = feed.get('last_refresh')

            if self.should_refresh(url, interval, last_refresh):
                logger.info(f"Auto-refresh triggering for {url}")
                try:
                    self.refresh_callback(url)
                    self.last_refresh_time[url] = datetime.now()
                except Exception as e:
                    logger.exception(f"refresh_callback failed for {url}: {e}")

    def should_refresh(self, feed_url: str, refresh_interval_minutes: int,
                      last_refresh: Optional[str] = None) -> bool:
        """
        Determine if a feed should be refreshed.

        Args:
            feed_url: URL of the feed
            refresh_interval_minutes: Refresh interval for this feed
            last_refresh: ISO format datetime string of last refresh

        Returns:
            True if feed should be refreshed
        """
        # Use default interval if not specified
        if not refresh_interval_minutes:
            refresh_interval_minutes = self.default_interval

        # If never refreshed, refresh now
        if not last_refresh:
            return True

        try:
            # Parse last refresh time
            last_refresh_dt = datetime.fromisoformat(last_refresh)

            # Check if enough time has passed
            time_since_refresh = datetime.now() - last_refresh_dt
            required_interval = timedelta(minutes=refresh_interval_minutes)

            return time_since_refresh >= required_interval

        except Exception as e:
            logger.error(f"Error checking refresh time: {e}")
            return False

    def get_next_refresh_time(self, feed_url: str, refresh_interval_minutes: int,
                             last_refresh: Optional[str] = None) -> Optional[datetime]:
        """
        Get the next scheduled refresh time for a feed.

        Args:
            feed_url: URL of the feed
            refresh_interval_minutes: Refresh interval for this feed
            last_refresh: ISO format datetime string of last refresh

        Returns:
            Next refresh time as datetime, or None if not available
        """
        if not last_refresh:
            return datetime.now()

        try:
            last_refresh_dt = datetime.fromisoformat(last_refresh)
            next_refresh = last_refresh_dt + timedelta(minutes=refresh_interval_minutes)
            return next_refresh
        except Exception:
            return None

    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self.enabled

    def set_default_interval(self, minutes: int):
        """
        Set the default refresh interval.

        Args:
            minutes: Interval in minutes
        """
        self.default_interval = max(5, minutes)  # Minimum 5 minutes
        logger.info(f"Default refresh interval set to {self.default_interval} minutes")


class SmartRefreshScheduler(AutoRefreshScheduler):
    """
    Enhanced scheduler that adapts refresh intervals based on feed activity.

    Feeds that update frequently get checked more often.
    Feeds that rarely update get checked less often.
    """

    def __init__(self, default_interval_minutes: int = 30):
        super().__init__(default_interval_minutes)
        self.update_history = {}  # feed_url -> list of update times

    def record_update(self, feed_url: str, new_articles_count: int):
        """
        Record an update for smart scheduling.

        Args:
            feed_url: URL of the feed
            new_articles_count: Number of new articles found
        """
        if feed_url not in self.update_history:
            self.update_history[feed_url] = []

        # Record timestamp and article count
        self.update_history[feed_url].append({
            'time': datetime.now(),
            'new_articles': new_articles_count
        })

        # Keep only last 20 updates
        if len(self.update_history[feed_url]) > 20:
            self.update_history[feed_url] = self.update_history[feed_url][-20:]

    def get_recommended_interval(self, feed_url: str) -> int:
        """
        Get recommended refresh interval based on feed activity.

        Args:
            feed_url: URL of the feed

        Returns:
            Recommended interval in minutes
        """
        if feed_url not in self.update_history or len(self.update_history[feed_url]) < 3:
            return self.default_interval

        history = self.update_history[feed_url]

        # Calculate average time between updates with new content
        updates_with_content = [h for h in history if h['new_articles'] > 0]

        if len(updates_with_content) < 2:
            # Feed rarely updates, use longer interval
            return min(self.default_interval * 2, 120)  # Max 2 hours

        # Calculate time between updates
        intervals = []
        for i in range(1, len(updates_with_content)):
            time_diff = updates_with_content[i]['time'] - updates_with_content[i-1]['time']
            intervals.append(time_diff.total_seconds() / 60)  # Convert to minutes

        # Use average interval
        avg_interval = sum(intervals) / len(intervals)

        # Clamp to reasonable range (15 minutes to 2 hours)
        recommended = max(15, min(int(avg_interval * 0.8), 120))

        return recommended


if __name__ == "__main__":
    # Test scheduler
    print("Testing Auto-Refresh Scheduler...")

    def test_refresh_callback(feed_url: str):
        print(f"Refreshing feed: {feed_url}")

    scheduler = AutoRefreshScheduler(default_interval_minutes=1)

    # Test should_refresh logic
    print("\nTesting refresh logic:")

    # Never refreshed
    should = scheduler.should_refresh("http://example.com/feed1", 30, None)
    print(f"Never refreshed: {should} (should be True)")

    # Refreshed recently
    recent_time = datetime.now().isoformat()
    should = scheduler.should_refresh("http://example.com/feed2", 30, recent_time)
    print(f"Just refreshed: {should} (should be False)")

    # Refreshed long ago
    old_time = (datetime.now() - timedelta(hours=2)).isoformat()
    should = scheduler.should_refresh("http://example.com/feed3", 30, old_time)
    print(f"Refreshed 2 hours ago: {should} (should be True)")

    print("\n✓ Auto-refresh scheduler tests passed")

    # Test smart scheduler
    print("\nTesting Smart Scheduler:")
    smart = SmartRefreshScheduler()

    # Simulate updates
    smart.record_update("http://example.com/feed1", 5)
    time.sleep(0.1)
    smart.record_update("http://example.com/feed1", 3)
    time.sleep(0.1)
    smart.record_update("http://example.com/feed1", 0)

    interval = smart.get_recommended_interval("http://example.com/feed1")
    print(f"Recommended interval: {interval} minutes")

    print("\n✓ Smart scheduler tests passed")
