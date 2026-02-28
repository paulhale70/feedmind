"""
Article List Screen
Displays articles from selected feed with filters (all/unread/favorites).
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList
from kivymd.uix.chip import MDChip
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.app import App
from kivy.properties import StringProperty, ListProperty
from kivy.clock import Clock
from threading import Thread


class ArticleListScreen(MDScreen):
    """Screen showing list of articles with filtering."""

    current_feed_url = StringProperty(None, allownone=True)
    view_filter = StringProperty('all')  # 'all', 'unread', 'favorites'
    articles = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_enter(self):
        """Called when screen is displayed."""
        self.load_articles()

    def set_feed_filter(self, feed_url):
        """Set the feed to display articles from."""
        self.current_feed_url = feed_url
        self.view_filter = 'all'

    def set_view_filter(self, filter_type):
        """Set the view filter (all/unread/favorites)."""
        self.view_filter = filter_type
        self.load_articles()

    def load_articles(self):
        """Load articles based on current filters."""
        app = App.get_running_app()

        # Get article list widget
        article_list = self.ids.get('article_list')
        if not article_list:
            return

        # Clear existing articles
        article_list.clear_widgets()

        # Get articles from database
        if self.view_filter == 'unread':
            articles = self._get_unread_articles()
        elif self.view_filter == 'favorites':
            articles = self._get_favorite_articles()
        else:
            articles = self._get_all_articles()

        self.articles = articles

        if not articles:
            # Show empty state
            from kivymd.uix.label import MDLabel
            message = {
                'unread': "No unread articles",
                'favorites': "No favorite articles",
                'all': "No articles yet"
            }.get(self.view_filter, "No articles")

            empty_label = MDLabel(
                text=message,
                halign="center",
                theme_text_color="Secondary"
            )
            article_list.add_widget(empty_label)
        else:
            # Import article card widget
            try:
                from mobile.widgets.article_card import ArticleCard

                # Add article cards
                for article in articles:
                    card = ArticleCard(article_data=article)
                    card.bind(on_release=lambda x, a=article: self.open_article(a))
                    article_list.add_widget(card)
            except ImportError:
                # Fallback to simple list items
                from kivymd.uix.list import TwoLineListItem
                for article in articles:
                    item = TwoLineListItem(
                        text=article.get('title', 'Untitled'),
                        secondary_text=article.get('feed_title', '')
                    )
                    item.bind(on_release=lambda x, a=article: self.open_article(a))
                    article_list.add_widget(item)

    def _get_all_articles(self):
        """Get all articles (optionally filtered by feed)."""
        app = App.get_running_app()
        if self.current_feed_url:
            return app.db.get_cached_articles(self.current_feed_url)
        else:
            # Get all articles from all feeds
            all_articles = []
            feeds = app.db.get_all_feeds()
            for feed in feeds:
                articles = app.db.get_cached_articles(feed['url'])
                all_articles.extend(articles)
            return all_articles

    def _get_unread_articles(self):
        """Get unread articles."""
        all_articles = self._get_all_articles()
        return [a for a in all_articles if not a.get('is_read')]

    def _get_favorite_articles(self):
        """Get favorite articles."""
        app = App.get_running_app()
        return app.db.get_favorites()

    def open_article(self, article):
        """Open article in reader screen."""
        app = App.get_running_app()

        # Mark as read
        app.db.mark_article_read(article['id'], True)

        # Navigate to reader
        reader_screen = app.screen_manager.get_screen('reader')
        reader_screen.load_article(article)
        app.screen_manager.current = 'reader'

    def refresh_articles(self):
        """Pull-to-refresh handler."""
        if self.current_feed_url:
            self.refresh_feed(self.current_feed_url)
        else:
            self.refresh_all_feeds()

    def refresh_feed(self, feed_url):
        """Refresh a single feed."""
        app = App.get_running_app()

        def _refresh():
            try:
                articles = app.fetcher.fetch_feed(feed_url)
                app.db.cache_articles(articles, feed_url)
                Clock.schedule_once(lambda dt: self.on_refresh_complete(True), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_refresh_complete(False, str(e)), 0)

        Thread(target=_refresh, daemon=True).start()

    def refresh_all_feeds(self):
        """Refresh all feeds."""
        app = App.get_running_app()

        def _refresh_all():
            try:
                feeds = app.db.get_all_feeds()
                for feed in feeds:
                    try:
                        articles = app.fetcher.fetch_feed(feed['url'])
                        app.db.cache_articles(articles, feed['url'])
                    except:
                        pass  # Continue with other feeds
                Clock.schedule_once(lambda dt: self.on_refresh_complete(True), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_refresh_complete(False, str(e)), 0)

        Thread(target=_refresh_all, daemon=True).start()

    def on_refresh_complete(self, success, error_msg=None):
        """Called when refresh completes."""
        if success:
            self.load_articles()
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="Refresh complete!").open()
        else:
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text=f"Refresh failed: {error_msg}").open()
