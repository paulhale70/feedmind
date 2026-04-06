"""
Article Card Widget
Material Design card for displaying article summaries in lists.
"""

from kivymd.uix.card import MDCard
from kivymd.uix.behaviors import RippleBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.properties import StringProperty, BooleanProperty, DictProperty
from kivy.metrics import dp


class ArticleCard(MDCard, RippleBehavior):
    """Material Design card for article display."""

    article_data = DictProperty({})
    title = StringProperty('')
    description = StringProperty('')
    feed_title = StringProperty('')
    published = StringProperty('')
    is_read = BooleanProperty(False)
    is_favorite = BooleanProperty(False)

    def __init__(self, article_data=None, **kwargs):
        super().__init__(**kwargs)

        # Configure card appearance
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(8)
        self.spacing = dp(4)
        self.ripple_behavior = True
        self.radius = [dp(8)]
        self.elevation = 2

        # Load article data
        if article_data:
            self.load_article(article_data)

        # Build card content
        self.build_card()

    def load_article(self, article_data):
        """Load article data into the card."""
        self.article_data = article_data
        self.title = article_data.get('title', 'Untitled')
        self.description = article_data.get('description', '')
        self.feed_title = article_data.get('feed_title', '')
        self.published = article_data.get('published', '')
        self.is_read = bool(article_data.get('is_read', 0))
        self.is_favorite = bool(article_data.get('is_favorite', 0))

    def build_card(self):
        """Build card UI."""
        # Main content layout
        content_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(4),
            padding=dp(4)
        )

        # Title
        title_label = MDLabel(
            text=self.title,
            font_style="H6",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Primary" if not self.is_read else "Hint"
        )
        content_layout.add_widget(title_label)

        # Description (truncated)
        desc_text = self.description[:150] + "..." if len(self.description) > 150 else self.description
        desc_label = MDLabel(
            text=desc_text,
            font_style="Body2",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Secondary"
        )
        content_layout.add_widget(desc_label)

        # Feed title and date
        meta_text = self.feed_title
        if self.published:
            meta_text += f" • {self.published[:10]}"  # Just the date part

        meta_label = MDLabel(
            text=meta_text,
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Hint"
        )
        content_layout.add_widget(meta_label)

        # Status indicators layout
        status_layout = MDBoxLayout(
            size_hint_y=None,
            height=dp(24),
            spacing=dp(8)
        )

        if self.is_favorite:
            from kivymd.uix.label import MDIcon
            fav_icon = MDIcon(
                icon="heart",
                theme_text_color="Custom",
                text_color=[1, 0, 0, 1]  # Red
            )
            status_layout.add_widget(fav_icon)

        if self.is_read:
            read_label = MDLabel(
                text="Read",
                font_style="Caption",
                theme_text_color="Hint"
            )
            status_layout.add_widget(read_label)

        content_layout.add_widget(status_layout)

        self.add_widget(content_layout)

    def on_release(self):
        """Called when card is tapped."""
        # This will be handled by the parent screen
        pass
