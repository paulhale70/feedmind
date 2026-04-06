"""
Feed List Screen
Displays all RSS feeds organized by categories with add/edit/delete functionality.
"""

from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, ThreeLineAvatarIconListItem, IconLeftWidget, IconRightWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.app import App
from kivy.clock import Clock
from threading import Thread


class FeedListItem(ThreeLineAvatarIconListItem):
    """Custom list item for feed display."""

    def __init__(self, feed_data, **kwargs):
        super().__init__(**kwargs)
        self.feed_data = feed_data

        # Set text from feed data
        self.text = feed_data.get('title', 'Untitled Feed')
        self.secondary_text = feed_data.get('url', '')
        self.tertiary_text = f"Category: {feed_data.get('category_name', 'Uncategorized')}"

        # Add RSS icon
        self.add_widget(IconLeftWidget(icon="rss"))

        # Add chevron for navigation
        self.add_widget(IconRightWidget(icon="chevron-right"))


class FeedListScreen(MDScreen):
    """Screen showing list of all RSS feeds."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dialog = None

    def on_enter(self):
        """Called when screen is displayed."""
        self.refresh_feeds()

    def refresh_feeds(self):
        """Load feeds from database and populate list."""
        app = App.get_running_app()

        # Clear existing list
        feed_list = self.ids.get('feed_list')
        if feed_list:
            feed_list.clear_widgets()

            # Get feeds from database
            feeds = app.db.get_all_feeds()

            if not feeds:
                # Show empty state
                from kivymd.uix.label import MDLabel
                empty_label = MDLabel(
                    text="No feeds yet. Tap + to add one!",
                    halign="center",
                    theme_text_color="Secondary"
                )
                feed_list.add_widget(empty_label)
            else:
                # Add feed items
                for feed in feeds:
                    item = FeedListItem(feed_data=feed)
                    item.bind(on_release=lambda x, f=feed: self.open_feed(f))
                    feed_list.add_widget(item)

    def open_feed(self, feed):
        """Navigate to articles for this feed."""
        app = App.get_running_app()
        article_screen = app.screen_manager.get_screen('articles')
        article_screen.set_feed_filter(feed['url'])
        app.screen_manager.current = 'articles'

    def show_add_feed_dialog(self):
        """Show dialog to add a new feed."""
        if not self.dialog:
            # Create dialog content
            content = MDBoxLayout(
                orientation="vertical",
                spacing="12dp",
                size_hint_y=None,
                height="120dp"
            )

            url_field = MDTextField(
                hint_text="Feed URL",
                helper_text="Enter RSS/Atom feed URL",
                helper_text_mode="on_focus"
            )
            content.add_widget(url_field)

            # Create dialog
            self.dialog = MDDialog(
                title="Add RSS Feed",
                type="custom",
                content_cls=content,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="ADD",
                        on_release=lambda x: self.add_feed(url_field.text)
                    ),
                ],
            )

        self.dialog.open()

    def add_feed(self, url):
        """Add a new RSS feed."""
        if not url:
            return

        app = App.get_running_app()

        # Dismiss dialog
        if self.dialog:
            self.dialog.dismiss()

        # Show loading indicator
        self.show_loading_message("Adding feed...")

        def _add_feed():
            try:
                # Fetch feed to get title
                articles = app.fetcher.fetch_feed(url)
                if articles:
                    title = articles[0].feed_title if articles else url
                    # Add to database
                    app.db.add_feed(url, title)
                    # Cache articles
                    app.db.cache_articles(articles, url)

                    # Update UI on main thread
                    Clock.schedule_once(lambda dt: self.on_feed_added(True), 0)
                else:
                    Clock.schedule_once(lambda dt: self.on_feed_added(False, "No articles found"), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_feed_added(False, str(e)), 0)

        # Run in background thread
        Thread(target=_add_feed, daemon=True).start()

    def on_feed_added(self, success, error_msg=None):
        """Called when feed add operation completes."""
        # Hide loading
        self.hide_loading_message()

        if success:
            # Refresh feed list
            self.refresh_feeds()
            self.show_snackbar("Feed added successfully!")
        else:
            self.show_snackbar(f"Failed to add feed: {error_msg}")

    def show_loading_message(self, message):
        """Show a loading message."""
        # TODO: Implement proper loading indicator
        print(f"Loading: {message}")

    def hide_loading_message(self):
        """Hide loading message."""
        # TODO: Implement proper loading indicator
        pass

    def show_snackbar(self, message):
        """Show a snackbar message."""
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=message).open()
