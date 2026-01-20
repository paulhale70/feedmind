"""
Desktop Notifications for RSS Reader V2
Provides desktop notifications for new articles using plyer.
"""

import logging
from typing import Optional

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationManager:
    """Manage desktop notifications for RSS Reader."""

    def __init__(self, app_name: str = "RSSreaderV2"):
        self.app_name = app_name
        self.enabled = True

    @staticmethod
    def is_available() -> bool:
        """Check if plyer is available."""
        return PLYER_AVAILABLE

    def notify_new_articles(self, feed_title: str, count: int, timeout: int = 5):
        """
        Show notification for new articles.

        Args:
            feed_title: Name of the feed
            count: Number of new articles
            timeout: Notification timeout in seconds
        """
        if not self.enabled or not PLYER_AVAILABLE:
            return

        try:
            article_word = "article" if count == 1 else "articles"
            notification.notify(
                title=f"{self.app_name} - New Articles",
                message=f"{count} new {article_word} from {feed_title}",
                app_name=self.app_name,
                timeout=timeout
            )
            logger.info(f"Notification sent: {count} articles from {feed_title}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def notify_refresh_complete(self, total_new: int, feed_count: int, timeout: int = 5):
        """
        Show notification when refresh is complete.

        Args:
            total_new: Total number of new articles
            feed_count: Number of feeds refreshed
            timeout: Notification timeout in seconds
        """
        if not self.enabled or not PLYER_AVAILABLE:
            return

        try:
            if total_new > 0:
                feed_word = "feed" if feed_count == 1 else "feeds"
                article_word = "article" if total_new == 1 else "articles"
                notification.notify(
                    title=f"{self.app_name} - Refresh Complete",
                    message=f"{total_new} new {article_word} from {feed_count} {feed_word}",
                    app_name=self.app_name,
                    timeout=timeout
                )
                logger.info(f"Refresh notification sent: {total_new} new articles")
        except Exception as e:
            logger.error(f"Failed to send refresh notification: {e}")

    def notify_custom(self, title: str, message: str, timeout: int = 5):
        """
        Show custom notification.

        Args:
            title: Notification title
            message: Notification message
            timeout: Notification timeout in seconds
        """
        if not self.enabled or not PLYER_AVAILABLE:
            return

        try:
            notification.notify(
                title=f"{self.app_name} - {title}",
                message=message,
                app_name=self.app_name,
                timeout=timeout
            )
            logger.info(f"Custom notification sent: {title}")
        except Exception as e:
            logger.error(f"Failed to send custom notification: {e}")

    def notify_error(self, error_message: str, timeout: int = 5):
        """
        Show error notification.

        Args:
            error_message: Error message to display
            timeout: Notification timeout in seconds
        """
        if not self.enabled or not PLYER_AVAILABLE:
            return

        try:
            notification.notify(
                title=f"{self.app_name} - Error",
                message=error_message,
                app_name=self.app_name,
                timeout=timeout
            )
            logger.info(f"Error notification sent")
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    def set_enabled(self, enabled: bool):
        """Enable or disable notifications."""
        self.enabled = enabled
        logger.info(f"Notifications {'enabled' if enabled else 'disabled'}")

    def is_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.enabled and PLYER_AVAILABLE


def check_dependencies():
    """Check if required dependencies are installed."""
    if not PLYER_AVAILABLE:
        print("❌ plyer is not installed")
        print("\nTo install plyer, run:")
        print("  pip install plyer")
        print("\nOr on some systems:")
        print("  pip3 install plyer")
        print("\nNote: On Linux, you may also need to install:")
        print("  sudo apt-get install python3-notify2  # For Debian/Ubuntu")
        print("  sudo yum install notify-python        # For RedHat/CentOS")
        return False

    print("✓ plyer is installed")
    return True


if __name__ == "__main__":
    # Test if dependencies are available
    check_dependencies()

    if PLYER_AVAILABLE:
        # Test notification
        manager = NotificationManager()
        print("\nSending test notification...")
        manager.notify_new_articles("Test Feed", 5)
        print("✓ If you saw a notification, it's working!")
    else:
        print("\n❌ Cannot test notifications without plyer installed")
