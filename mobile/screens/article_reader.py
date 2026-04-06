"""
Article Reader Screen
Displays full article content with actions (favorite, share, open in browser).
"""

from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivy.properties import DictProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from threading import Thread


class ArticleReaderScreen(MDScreen):
    """Screen for reading full article content."""

    article = DictProperty({})
    article_title = StringProperty('')
    article_content = StringProperty('')
    article_link = StringProperty('')
    is_favorite = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load_article(self, article_data):
        """Load article content."""
        self.article = article_data
        self.article_title = article_data.get('title', 'Untitled')
        self.article_content = article_data.get('description', '')
        self.article_link = article_data.get('link', '')
        self.is_favorite = bool(article_data.get('is_favorite', 0))

        # Update UI
        self.update_ui()

    def update_ui(self):
        """Update UI elements with article data."""
        # Update title label
        title_label = self.ids.get('article_title')
        if title_label:
            title_label.text = self.article_title

        # Update content label
        content_label = self.ids.get('article_content')
        if content_label:
            content_label.text = self.article_content

        # Update favorite button icon
        fav_button = self.ids.get('favorite_button')
        if fav_button:
            fav_button.icon = "heart" if self.is_favorite else "heart-outline"

    def toggle_favorite(self):
        """Toggle favorite status."""
        app = App.get_running_app()
        article_id = self.article.get('id')

        if article_id:
            new_status = not self.is_favorite
            app.db.mark_as_favorite(article_id, new_status)
            self.is_favorite = new_status

            # Update UI
            fav_button = self.ids.get('favorite_button')
            if fav_button:
                fav_button.icon = "heart" if self.is_favorite else "heart-outline"

            # Show feedback
            message = "Added to favorites" if new_status else "Removed from favorites"
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text=message).open()

    def open_in_browser(self):
        """Open article in external browser."""
        if self.article_link:
            import webbrowser
            webbrowser.open(self.article_link)

    def share_article(self):
        """Share article (platform-specific)."""
        try:
            from kivy.utils import platform
            if platform == 'android':
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')

                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.putExtra(Intent.EXTRA_TEXT, String(self.article_link))
                intent.setType("text/plain")

                currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
                currentActivity.startActivity(intent)
            elif platform == 'ios':
                # iOS share implementation
                pass
            else:
                # Desktop: copy to clipboard
                from kivy.core.clipboard import Clipboard
                Clipboard.copy(self.article_link)
                from kivymd.uix.snackbar import Snackbar
                Snackbar(text="Link copied to clipboard").open()
        except Exception as e:
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text=f"Share failed: {e}").open()

    def extract_full_text(self):
        """Extract full text from article URL (if available)."""
        try:
            from rss_article_extractor import ArticleExtractor

            def _extract():
                try:
                    extractor = ArticleExtractor()
                    result = extractor.extract(self.article_link)
                    if result and result.get('text'):
                        Clock.schedule_once(lambda dt: self.on_text_extracted(result['text']), 0)
                    else:
                        Clock.schedule_once(lambda dt: self.on_extraction_failed("No text found"), 0)
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.on_extraction_failed(str(e)), 0)

            Thread(target=_extract, daemon=True).start()

            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="Extracting full text...").open()

        except ImportError:
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="Article extraction not available").open()

    def on_text_extracted(self, full_text):
        """Called when full text is extracted."""
        self.article_content = full_text

        # Update UI
        content_label = self.ids.get('article_content')
        if content_label:
            content_label.text = full_text

        # Save to database
        app = App.get_running_app()
        article_id = self.article.get('id')
        if article_id:
            app.db.store_full_text(article_id, full_text)

        from kivymd.uix.snackbar import Snackbar
        Snackbar(text="Full text extracted!").open()

    def on_extraction_failed(self, error_msg):
        """Called when extraction fails."""
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=f"Extraction failed: {error_msg}").open()

    def go_back(self):
        """Navigate back to article list."""
        app = App.get_running_app()
        app.screen_manager.current = 'articles'
