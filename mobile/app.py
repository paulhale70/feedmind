"""
FeedMind Mobile App
Main application class for Kivy/KivyMD mobile RSS reader.
"""

import os
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivy.core.window import Window
from kivy.utils import platform
from kivy.lang import Builder

# Import backend modules (reuse from desktop app)
from rss_database_v3 import RSSDatabase
from rss_core import RSSFetcher


class FeedMindApp(MDApp):
    """Main Kivy application class for FeedMind mobile."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "FeedMind"

        # Initialize backend components
        self.db = None
        self.fetcher = None
        self.screen_manager = None

        # Load KV file
        kv_file = os.path.join(os.path.dirname(__file__), 'kv', 'feedmind.kv')
        if os.path.exists(kv_file):
            Builder.load_file(kv_file)

    def build(self):
        """Build and return the root widget."""
        # Configure theme
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"  # Light or Dark
        self.theme_cls.material_style = "M3"  # Material Design 3

        # Initialize backend
        self._init_backend()

        # Create screen manager
        self.screen_manager = MDScreenManager()

        # Import and add screens (will be created next)
        try:
            from mobile.screens.feed_list import FeedListScreen
            from mobile.screens.article_list import ArticleListScreen
            from mobile.screens.article_reader import ArticleReaderScreen

            self.screen_manager.add_widget(FeedListScreen(name='feeds'))
            self.screen_manager.add_widget(ArticleListScreen(name='articles'))
            self.screen_manager.add_widget(ArticleReaderScreen(name='reader'))

            # Set initial screen
            self.screen_manager.current = 'feeds'
        except ImportError as e:
            print(f"Warning: Could not import screens: {e}")
            # Continue without screens for now (will add them next)

        # Load theme preference from database
        self._load_theme()

        return self.screen_manager

    def _init_backend(self):
        """Initialize database and RSS fetcher."""
        db_path = self._get_db_path()

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self.db = RSSDatabase(db_path)

        # Initialize RSS fetcher
        self.fetcher = RSSFetcher(timeout=15)

        print(f"Database initialized at: {db_path}")

    def _get_db_path(self):
        """Get platform-specific database path."""
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                base_dir = app_storage_path()
            except:
                base_dir = '/sdcard/FeedMind'
        elif platform == 'ios':
            base_dir = os.path.expanduser('~/Documents/FeedMind')
        else:
            # Desktop testing
            base_dir = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.join(base_dir, '..')

        return os.path.join(base_dir, 'rss_reader_v3_mobile.db')

    def _load_theme(self):
        """Load theme preference from database."""
        try:
            theme = self.db.get_setting('theme')
            if theme == 'dark':
                self.theme_cls.theme_style = "Dark"
            else:
                self.theme_cls.theme_style = "Light"
        except:
            # Default to light theme
            pass

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
            self.db.set_setting('theme', 'dark')
        else:
            self.theme_cls.theme_style = "Light"
            self.db.set_setting('theme', 'light')

    def on_pause(self):
        """Handle app pause (Android/iOS lifecycle)."""
        # Allow the app to pause
        return True

    def on_resume(self):
        """Handle app resume (Android/iOS lifecycle)."""
        # Refresh UI if needed
        pass

    def on_start(self):
        """Called when the app starts."""
        # Window size for desktop testing (mobile phone dimensions)
        if platform not in ('android', 'ios'):
            Window.size = (400, 700)
