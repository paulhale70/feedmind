"""
FeedMind 🧠 - AI-Powered RSS Feed Reader with Podcast Support

A modern, feature-rich RSS/Atom feed reader that combines intelligent
content management with podcast support and AI-powered summaries.

Version: 3.5.0
Features:
- RSS/Atom feed parsing and management
- Category organization and OPML import/export
- Podcast playback and episode downloads
- AI-powered article summaries (Claude/OpenAI)
- Full-text article extraction
- Dark/light themes
- Reading statistics
- PDF export
- Desktop notifications
- Keyboard shortcuts
"""

__version__ = "3.5.0"

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import webbrowser
import threading
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from rss_core import RSSFetcher
from rss_database_v3 import RSSDatabase  # V3 database with podcast and AI support
from rss_opml import OPMLHandler
from rss_themes import LightTheme, DarkTheme, Theme
from rss_pdf_exporter import PDFExporter
from rss_notifications import NotificationManager

# Optional V3 features (podcast support)
try:
    from rss_audio_player_ui import AudioPlayerWidget
    from rss_podcast_downloader import PodcastDownloader
    PODCAST_SUPPORT = True
except ImportError:
    PODCAST_SUPPORT = False

# Optional V3.5 features (AI summarization and extraction)
try:
    from rss_ai_summarizer import AISummarizer, AIProvider
    from rss_article_extractor import ArticleExtractor
    from rss_api_config import APIConfigManager
    AI_SUPPORT = True
except ImportError:
    AI_SUPPORT = False


class FeedMind:
    """FeedMind - AI-Powered RSS Reader with Podcast Support."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("FeedMind 🧠")
        self.root.geometry("1280x800")

        # Initialize core components
        self.db = RSSDatabase("feedmind.db")
        self.fetcher = RSSFetcher(timeout=15)
        self.notifier = NotificationManager()

        # Load notification preference
        notifications_enabled = self.db.get_setting("notifications_enabled", "true") == "true"
        self.notifier.set_enabled(notifications_enabled)

        # Theme management
        self.current_theme: Theme = LightTheme()
        self._load_theme_preference()

        # State management
        self.current_view = "all"  # all, unread, favorites
        self.current_feed_url: Optional[str] = None
        self.current_category_id: Optional[int] = None
        self.selected_article_id: Optional[int] = None
        self.auto_refresh_enabled = False
        self.auto_refresh_job = None

        # Data mappings for listboxes (to store metadata)
        self.feed_urls = []  # Maps feed listbox index to URL
        self.category_ids = []  # Maps category listbox index to ID

        # V3 Podcast support
        self.audio_player = None
        self.podcast_downloader = None
        if PODCAST_SUPPORT:
            self.podcast_downloader = PodcastDownloader("podcast_downloads")
            # Audio player widget will be created in _create_ui

        # V3.5 AI support
        self.ai_summarizer = None
        self.article_extractor = None
        self.api_config = None
        if AI_SUPPORT:
            self.api_config = APIConfigManager(self.db)
            self.article_extractor = ArticleExtractor()
            # AI summarizer will be initialized when needed (requires API key)

        # Build UI
        self._create_menu()
        self._create_ui()
        self._apply_theme()

        # Load initial data
        self._load_feeds()
        self._load_categories()
        self._update_view()

        # Set up keyboard shortcuts
        self._setup_keyboard_shortcuts()

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Show feature status in status bar
        self._show_startup_message()

    def _load_theme_preference(self):
        """Load saved theme preference."""
        theme_name = self.db.get_setting("theme", "light")
        if theme_name == "dark":
            self.current_theme = DarkTheme()
        else:
            self.current_theme = LightTheme()

    def _create_menu(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Import OPML...", command=self._import_opml, accelerator="Ctrl+I")
        file_menu.add_command(label="Export OPML...", command=self._export_opml, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Export to PDF...", command=self._export_pdf, accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Dark Mode", command=self._toggle_theme, accelerator="Ctrl+T")
        view_menu.add_separator()
        view_menu.add_command(label="All Articles", command=lambda: self._change_view("all"), accelerator="1")
        view_menu.add_command(label="Unread", command=lambda: self._change_view("unread"), accelerator="2")
        view_menu.add_command(label="Favorites", command=lambda: self._change_view("favorites"), accelerator="3")
        view_menu.add_separator()
        view_menu.add_command(label="Statistics", command=self._show_statistics, accelerator="Ctrl+S")

        # Manage menu
        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Manage", menu=manage_menu)
        manage_menu.add_command(label="Categories...", command=self._manage_categories, accelerator="Ctrl+M")
        manage_menu.add_command(label="Feed Settings...", command=self._feed_settings)
        manage_menu.add_separator()
        manage_menu.add_command(label="Preferences...", command=self._show_preferences)
        manage_menu.add_separator()
        manage_menu.add_command(label="Clear Old Articles", command=self._clear_cache)

        # AI menu (V3.5 features)
        if AI_SUPPORT:
            ai_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="AI ✨", menu=ai_menu)
            ai_menu.add_command(label="Extract Full Text", command=self._extract_full_text)
            ai_menu.add_command(label="Generate Summary", command=self._generate_summary)
            ai_menu.add_command(label="Generate TL;DR", command=self._generate_tldr)
            ai_menu.add_separator()
            ai_menu.add_command(label="Configure API Keys...", command=self._configure_ai)
            ai_menu.add_separator()
            ai_menu.add_command(label="About AI Features", command=self._about_ai_features)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About FeedMind", command=self._show_about)
        if PODCAST_SUPPORT:
            help_menu.add_command(label="Podcast Support ✓", state=tk.DISABLED)
        if AI_SUPPORT:
            help_menu.add_command(label="AI Features ✓", state=tk.DISABLED)

    def _create_ui(self):
        """Create the main user interface."""
        # Main container with two panes
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel (feeds and categories)
        self.left_panel = tk.Frame(self.paned_window, width=300)
        self.paned_window.add(self.left_panel)

        # Right panel (articles and content)
        self.right_panel = tk.Frame(self.paned_window)
        self.paned_window.add(self.right_panel)

        self._create_left_panel()
        self._create_right_panel()

    def _create_left_panel(self):
        """Create left sidebar with feeds and categories."""
        # Add feed section
        add_frame = tk.Frame(self.left_panel)
        add_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(add_frame, text="RSS Feed URL:").pack(anchor=tk.W)

        self.url_entry = tk.Entry(add_frame)
        self.url_entry.pack(fill=tk.X, pady=2)
        self.url_entry.bind('<Return>', lambda e: self._add_feed())

        btn_frame = tk.Frame(add_frame)
        btn_frame.pack(fill=tk.X, pady=2)

        self.add_btn = tk.Button(btn_frame, text="Add Feed", command=self._add_feed, bg="#2E7D32", fg="white")
        self.add_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        self.remove_btn = tk.Button(btn_frame, text="Remove", command=self._remove_feed, bg="#C62828", fg="white")
        self.remove_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # View mode buttons
        view_frame = tk.Frame(self.left_panel)
        view_frame.pack(fill=tk.X, padx=5, pady=5)

        self.all_btn = tk.Button(view_frame, text="All (1)", command=lambda: self._change_view("all"))
        self.all_btn.pack(fill=tk.X, pady=1)

        self.unread_btn = tk.Button(view_frame, text="Unread (2)", command=lambda: self._change_view("unread"))
        self.unread_btn.pack(fill=tk.X, pady=1)

        self.favorites_btn = tk.Button(view_frame, text="Favorites (3)", command=lambda: self._change_view("favorites"))
        self.favorites_btn.pack(fill=tk.X, pady=1)

        # Unread counter
        self.unread_label = tk.Label(self.left_panel, text="Unread: 0", font=("Arial", 12, "bold"))
        self.unread_label.pack(pady=5)

        # Categories section
        tk.Label(self.left_panel, text="Categories:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 2))

        category_frame = tk.Frame(self.left_panel)
        category_frame.pack(fill=tk.BOTH, expand=False, padx=5)

        self.category_listbox = tk.Listbox(category_frame, height=5)
        self.category_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.category_listbox.bind('<<ListboxSelect>>', self._on_category_select)

        cat_scroll = tk.Scrollbar(category_frame, command=self.category_listbox.yview)
        cat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.category_listbox.config(yscrollcommand=cat_scroll.set)

        # Feeds section
        tk.Label(self.left_panel, text="Feeds:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=5, pady=(10, 2))

        feed_frame = tk.Frame(self.left_panel)
        feed_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        self.feed_listbox = tk.Listbox(feed_frame)
        self.feed_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.feed_listbox.bind('<<ListboxSelect>>', self._on_feed_select)

        feed_scroll = tk.Scrollbar(feed_frame, command=self.feed_listbox.yview)
        feed_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.feed_listbox.config(yscrollcommand=feed_scroll.set)

        # Refresh controls
        refresh_frame = tk.Frame(self.left_panel)
        refresh_frame.pack(fill=tk.X, padx=5, pady=5)

        self.refresh_btn = tk.Button(refresh_frame, text="Refresh Feed", command=self._refresh_feed)
        self.refresh_btn.pack(fill=tk.X, pady=1)

        self.refresh_all_btn = tk.Button(refresh_frame, text="Refresh All", command=self._refresh_all)
        self.refresh_all_btn.pack(fill=tk.X, pady=1)

        self.mark_all_btn = tk.Button(refresh_frame, text="Mark All Read", command=self._mark_all_read)
        self.mark_all_btn.pack(fill=tk.X, pady=1)

        # Status label
        self.status_label = tk.Label(self.left_panel, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

    def _create_right_panel(self):
        """Create right panel with article list and content."""
        # Search bar
        search_frame = tk.Frame(self.right_panel)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))

        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self._search())

        self.search_btn = tk.Button(search_frame, text="Search", command=self._search)
        self.search_btn.pack(side=tk.LEFT, padx=(0, 2))

        self.clear_search_btn = tk.Button(search_frame, text="Clear", command=self._clear_search)
        self.clear_search_btn.pack(side=tk.LEFT)

        # Article list
        list_frame = tk.Frame(self.right_panel)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        # Create Treeview for articles
        columns = ("status", "title", "date")
        self.article_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)

        self.article_tree.heading("#0", text="")
        self.article_tree.heading("status", text="★")
        self.article_tree.heading("title", text="Article Title")
        self.article_tree.heading("date", text="Date")

        self.article_tree.column("#0", width=30, stretch=False)
        self.article_tree.column("status", width=30, stretch=False)
        self.article_tree.column("title", width=600)
        self.article_tree.column("date", width=150, stretch=False)

        self.article_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.article_tree.bind('<<TreeviewSelect>>', self._on_article_select)
        self.article_tree.bind('<Double-1>', lambda e: self._open_article())

        tree_scroll = tk.Scrollbar(list_frame, command=self.article_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.article_tree.config(yscrollcommand=tree_scroll.set)

        # Article details
        detail_frame = tk.Frame(self.right_panel)
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tk.Label(detail_frame, text="Article Details:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        text_frame = tk.Frame(detail_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.detail_text = tk.Text(text_frame, wrap=tk.WORD, height=10)
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        detail_scroll = tk.Scrollbar(text_frame, command=self.detail_text.yview)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.config(yscrollcommand=detail_scroll.set, state=tk.DISABLED)

        # Action buttons
        action_frame = tk.Frame(self.right_panel)
        action_frame.pack(fill=tk.X, padx=5, pady=5)

        self.open_btn = tk.Button(action_frame, text="Open in Browser (O)", command=self._open_article)
        self.open_btn.pack(side=tk.LEFT, padx=2)

        self.read_btn = tk.Button(action_frame, text="Mark Read (R)", command=self._toggle_read)
        self.read_btn.pack(side=tk.LEFT, padx=2)

        self.fav_btn = tk.Button(action_frame, text="Favorite (F)", command=self._toggle_favorite)
        self.fav_btn.pack(side=tk.LEFT, padx=2)

        # Podcast buttons (V3 feature)
        if PODCAST_SUPPORT:
            self.podcast_download_btn = tk.Button(action_frame, text="📥 Download Episode", command=self._download_podcast)
            # Initially hidden
            self.podcast_download_btn.pack_forget()

        # Podcast player (V3 feature)
        if PODCAST_SUPPORT:
            self.audio_player = AudioPlayerWidget(self.right_panel)
            self.audio_player.pack(fill=tk.X, padx=5, pady=5)
            # Initially hidden
            self.audio_player.pack_forget()

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Navigation
        self.root.bind('j', lambda e: self._next_article())
        self.root.bind('k', lambda e: self._prev_article())
        self.root.bind('o', lambda e: self._open_article())
        self.root.bind('<Return>', lambda e: self._open_article() if self.selected_article_id else None)

        # Actions
        self.root.bind('r', lambda e: self._toggle_read())
        self.root.bind('f', lambda e: self._toggle_favorite())
        self.root.bind('n', lambda e: self.url_entry.focus())
        self.root.bind('<Control-r>', lambda e: self._refresh_feed())
        self.root.bind('<Control-Shift-R>', lambda e: self._refresh_all())
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<Control-t>', lambda e: self._toggle_theme())
        self.root.bind('<Control-s>', lambda e: self._show_statistics())
        self.root.bind('<Escape>', lambda e: self._clear_search())

        # View switching
        self.root.bind('1', lambda e: self._change_view("all"))
        self.root.bind('2', lambda e: self._change_view("unread"))
        self.root.bind('3', lambda e: self._change_view("favorites"))

        # Menu shortcuts
        self.root.bind('<Control-i>', lambda e: self._import_opml())
        self.root.bind('<Control-e>', lambda e: self._export_opml())
        self.root.bind('<Control-p>', lambda e: self._export_pdf())
        self.root.bind('<Control-m>', lambda e: self._manage_categories())

        # Scrolling
        self.root.bind('<space>', lambda e: self._scroll_article(1))
        self.root.bind('<Shift-space>', lambda e: self._scroll_article(-1))

    def _apply_theme(self):
        """Apply current theme to all widgets."""
        theme = self.current_theme

        # Root window
        self.root.configure(bg=theme.bg_primary)

        # Paned window
        self.paned_window.configure(bg=theme.bg_primary, sashrelief=tk.RAISED)

        # Left panel
        self.left_panel.configure(bg=theme.bg_secondary)
        for widget in self.left_panel.winfo_children():
            self._apply_theme_to_widget(widget, theme)

        # Right panel
        self.right_panel.configure(bg=theme.bg_primary)
        for widget in self.right_panel.winfo_children():
            self._apply_theme_to_widget(widget, theme)

        # Special styling
        self.unread_label.configure(bg=theme.bg_secondary, fg=theme.accent)
        self.status_label.configure(bg=theme.bg_secondary, fg=theme.fg_secondary)

        # Article tree
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
                       background=theme.bg_primary,
                       foreground=theme.fg_primary,
                       fieldbackground=theme.bg_primary,
                       borderwidth=0)
        style.configure("Treeview.Heading",
                       background=theme.bg_secondary,
                       foreground=theme.fg_primary,
                       borderwidth=1)
        style.map('Treeview', background=[('selected', theme.accent)])

    def _apply_theme_to_widget(self, widget, theme: Theme):
        """Recursively apply theme to widget and its children."""
        widget_type = widget.winfo_class()

        if widget_type == 'Frame':
            widget.configure(bg=theme.bg_secondary)
        elif widget_type == 'Label':
            widget.configure(bg=theme.bg_secondary, fg=theme.fg_primary)
        elif widget_type == 'Button':
            # Keep special button colors
            if widget.cget('bg') in ['#2E7D32', '#C62828']:
                pass  # Keep these colors
            else:
                widget.configure(bg=theme.button_bg, fg=theme.button_fg,
                               activebackground=theme.button_active,
                               activeforeground=theme.button_fg)
        elif widget_type == 'Entry':
            widget.configure(bg=theme.bg_primary, fg=theme.fg_primary,
                           insertbackground=theme.fg_primary,
                           selectbackground=theme.accent,
                           selectforeground=theme.bg_primary)
        elif widget_type == 'Text':
            widget.configure(bg=theme.bg_primary, fg=theme.fg_primary,
                           insertbackground=theme.fg_primary,
                           selectbackground=theme.accent,
                           selectforeground=theme.bg_primary)
        elif widget_type == 'Listbox':
            widget.configure(bg=theme.bg_primary, fg=theme.fg_primary,
                           selectbackground=theme.accent,
                           selectforeground=theme.bg_primary)

        # Recursively apply to children
        for child in widget.winfo_children():
            self._apply_theme_to_widget(child, theme)

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        if isinstance(self.current_theme, LightTheme):
            self.current_theme = DarkTheme()
            self.db.set_setting("theme", "dark")
            self._set_status("Dark mode enabled")
        else:
            self.current_theme = LightTheme()
            self.db.set_setting("theme", "light")
            self._set_status("Light mode enabled")

        self._apply_theme()
        self._update_view()  # Refresh to apply colors to articles

    def _load_feeds(self):
        """Load feeds from database."""
        self.feed_listbox.delete(0, tk.END)
        self.feed_urls.clear()
        feeds = self.db.get_feeds()

        # Filter by category if selected
        if self.current_category_id is not None:
            feeds = [f for f in feeds if f['category_id'] == self.current_category_id]

        for feed in feeds:
            unread = self.db.get_unread_count(feed['url'])
            display = f"{feed['title']}"
            if unread > 0:
                display += f" ({unread})"
            self.feed_listbox.insert(tk.END, display)
            self.feed_urls.append(feed['url'])

    def _load_categories(self):
        """Load categories from database."""
        self.category_listbox.delete(0, tk.END)
        self.category_ids.clear()

        # Add "All" option
        self.category_listbox.insert(tk.END, "All Feeds")
        self.category_ids.append(None)

        # Add categories
        categories = self.db.get_categories()
        for cat in categories:
            self.category_listbox.insert(tk.END, cat['name'])
            self.category_ids.append(cat['id'])

        # Select "All" by default
        if self.current_category_id is None:
            self.category_listbox.selection_set(0)

    def _update_view(self):
        """Update article list based on current view and filters."""
        self.article_tree.delete(*self.article_tree.get_children())

        # Get articles based on view
        if self.current_view == "favorites":
            articles = self.db.get_favorites(self.current_feed_url)
        elif self.current_view == "unread":
            if self.current_feed_url:
                articles = self.db.get_cached_articles(self.current_feed_url, unread_only=True)
            else:
                articles = self.db.search_articles("", show_read=False)
        else:  # all
            if self.current_feed_url:
                articles = self.db.get_cached_articles(self.current_feed_url)
            else:
                articles = self.db.get_cached_articles()

        # Display articles
        for article in articles:
            unread_marker = "●" if not article['is_read'] else ""
            fav_marker = "★" if article['is_favorite'] else ""

            date_str = article['published'][:10] if article['published'] else ""

            # Use theme colors for read/unread
            tags = []
            if not article['is_read']:
                tags.append('unread')
            else:
                tags.append('read')

            item_id = self.article_tree.insert("", tk.END, text=unread_marker,
                                               values=(fav_marker, article['title'], date_str),
                                               tags=tags)
            self.article_tree.item(item_id, tags=(str(article['id']),))

        # Configure tags for styling
        self.article_tree.tag_configure('unread', font=("Arial", 10, "bold"))
        self.article_tree.tag_configure('read', foreground=self.current_theme.fg_secondary)

        # Update unread counter
        total_unread = sum(self.db.get_unread_count(f['url']) for f in self.db.get_feeds())
        self.unread_label.config(text=f"Unread: {total_unread}")

        # Update view button states
        self.all_btn.config(relief=tk.SUNKEN if self.current_view == "all" else tk.RAISED)
        self.unread_btn.config(relief=tk.SUNKEN if self.current_view == "unread" else tk.RAISED)
        self.favorites_btn.config(relief=tk.SUNKEN if self.current_view == "favorites" else tk.RAISED)

    def _add_feed(self):
        """Add a new feed."""
        url = self.url_entry.get().strip()
        if not url:
            return

        self._set_status(f"Adding feed: {url}")
        self.url_entry.config(state=tk.DISABLED)
        self.add_btn.config(state=tk.DISABLED)

        def add_in_thread():
            try:
                articles = self.fetcher.fetch_feed(url)
                if articles:
                    title = articles[0].feed_title if articles else url
                    # Schedule database operations on main thread
                    self.root.after(0, lambda: self._add_feed_to_db(url, title, articles))
                else:
                    self.root.after(0, lambda: self._on_feed_add_failed("No articles found"))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self._on_feed_add_failed(error_msg))

        threading.Thread(target=add_in_thread, daemon=True).start()

    def _add_feed_to_db(self, url: str, title: str, articles: list):
        """Add feed to database (must be called from main thread)."""
        try:
            if self.db.add_feed(url, title):
                self.db.cache_articles(articles, url)
                self.url_entry.delete(0, tk.END)
                self._load_feeds()
                self._update_view()
                self._set_status(f"Added: {title}")
            else:
                self._set_status("Feed already exists")
        except Exception as e:
            self._set_status(f"Error: {str(e)}")
        finally:
            self.url_entry.config(state=tk.NORMAL)
            self.add_btn.config(state=tk.NORMAL)

    def _on_feed_add_failed(self, error: str):
        """Handle feed add failure."""
        self._set_status(f"Failed: {error}")
        self.url_entry.config(state=tk.NORMAL)
        self.add_btn.config(state=tk.NORMAL)
        messagebox.showerror("Error", f"Failed to add feed:\n{error}")

    def _remove_feed(self):
        """Remove selected feed."""
        selection = self.feed_listbox.curselection()
        if not selection:
            return

        url = self.feed_urls[selection[0]]
        feed = next((f for f in self.db.get_feeds() if f['url'] == url), None)
        if not feed:
            return

        if messagebox.askyesno("Confirm", f"Remove feed '{feed['title']}'?"):
            self.db.remove_feed(url)
            self._load_feeds()
            self._update_view()
            self._set_status(f"Removed: {feed['title']}")

    def _refresh_feed(self):
        """Refresh currently selected feed."""
        selection = self.feed_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a feed to refresh")
            return

        url = self.feed_urls[selection[0]]
        self._set_status(f"Refreshing feed...")

        def refresh_in_thread():
            try:
                articles = self.fetcher.fetch_feed(url)
                self.root.after(0, lambda: self._cache_and_refresh_view(url, articles))
            except Exception as e:
                error_msg = f"Refresh failed: {str(e)}"
                self.root.after(0, lambda: self._set_status(error_msg))

        threading.Thread(target=refresh_in_thread, daemon=True).start()

    def _refresh_all(self):
        """Refresh all feeds."""
        feeds = self.db.get_feeds()
        if not feeds:
            return

        self._set_status(f"Refreshing {len(feeds)} feeds...")

        def refresh_all_in_thread():
            for i, feed in enumerate(feeds):
                try:
                    articles = self.fetcher.fetch_feed(feed['url'])
                    self.root.after(0, lambda u=feed['url'], a=articles:
                                  self._cache_articles_only(u, a))
                    self.root.after(0, lambda msg=f"Refreshing {i+1}/{len(feeds)}":
                                  self._set_status(msg))
                except Exception as e:
                    self.root.after(0, lambda msg=f"Error on {feed['title']}: {str(e)}":
                                  self._set_status(msg))

            self.root.after(0, lambda: self._finish_refresh_all())

        threading.Thread(target=refresh_all_in_thread, daemon=True).start()

    def _cache_and_refresh_view(self, url: str, articles: list):
        """Cache articles and refresh view (main thread only)."""
        try:
            # Count articles before caching
            old_count = len(self.db.get_cached_articles(url))

            self.db.cache_articles(articles, url)
            self.db.update_last_refresh(url)

            # Count new articles
            new_count = len(self.db.get_cached_articles(url)) - old_count

            # Show notification if there are new articles
            if new_count > 0:
                feed = next((f for f in self.db.get_feeds() if f['url'] == url), None)
                if feed:
                    self.notifier.notify_new_articles(feed['title'], new_count)

            self._load_feeds()
            self._update_view()
            self._set_status("Refresh complete")
        except Exception as e:
            self._set_status(f"Error: {str(e)}")

    def _cache_articles_only(self, url: str, articles: list):
        """Cache articles without refreshing view (for batch operations)."""
        try:
            self.db.cache_articles(articles, url)
            self.db.update_last_refresh(url)
        except Exception as e:
            print(f"Error caching {url}: {e}")

    def _finish_refresh_all(self):
        """Complete refresh all operation."""
        self._load_feeds()
        self._update_view()
        self._set_status("All feeds refreshed")

    def _mark_all_read(self):
        """Mark all articles as read."""
        if self.current_feed_url:
            count = self.db.mark_all_as_read(self.current_feed_url)
            self._set_status(f"Marked {count} articles as read")
        else:
            if messagebox.askyesno("Confirm", "Mark ALL articles from ALL feeds as read?"):
                total = 0
                for feed in self.db.get_feeds():
                    total += self.db.mark_all_as_read(feed['url'])
                self._set_status(f"Marked {total} articles as read")

        self._load_feeds()
        self._update_view()

    def _on_category_select(self, event):
        """Handle category selection."""
        selection = self.category_listbox.curselection()
        if not selection:
            return

        cat_id = self.category_ids[selection[0]]
        self.current_category_id = cat_id
        self.current_feed_url = None
        self._load_feeds()
        self._update_view()

    def _on_feed_select(self, event):
        """Handle feed selection."""
        selection = self.feed_listbox.curselection()
        if not selection:
            return

        url = self.feed_urls[selection[0]]
        self.current_feed_url = url
        self._update_view()

    def _on_article_select(self, event):
        """Handle article selection."""
        selection = self.article_tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.article_tree.item(item, 'tags')
        if not tags:
            return

        article_id = int(tags[0])
        self.selected_article_id = article_id

        # Get article details (including podcast info)
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT title, description, link, published, is_read, is_favorite,
                   audio_url, duration_seconds
            FROM articles WHERE id = ?
        """, (article_id,))

        row = cursor.fetchone()
        if row:
            title, desc, link, date, is_read, is_fav, audio_url, duration = row

            # Update detail view
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(tk.END, f"Title: {title}\n\n")
            self.detail_text.insert(tk.END, f"Date: {date}\n\n")

            # Show podcast info if available
            if audio_url and duration:
                mins = duration // 60
                secs = duration % 60
                self.detail_text.insert(tk.END, f"🎙️ Podcast Episode ({mins}:{secs:02d})\n\n")

            self.detail_text.insert(tk.END, f"Link: {link}\n\n")
            self.detail_text.insert(tk.END, f"Description:\n{desc}\n")
            self.detail_text.config(state=tk.DISABLED)

            # Update button states
            self.read_btn.config(text="Mark Unread (R)" if is_read else "Mark Read (R)")
            self.fav_btn.config(text="Unfavorite (F)" if is_fav else "Favorite (F)")

            # Handle podcast player and download button (V3 feature)
            if PODCAST_SUPPORT and self.audio_player and audio_url:
                # Check if episode is downloaded
                download_path = self.db.get_download_path(article_id)

                if download_path and os.path.exists(download_path):
                    # Load downloaded episode
                    self.audio_player.pack(fill=tk.X, padx=5, pady=5)
                    self.audio_player.load_episode(download_path, title)
                    self.podcast_download_btn.pack_forget()  # Hide download button
                    self._set_status(f"Podcast episode ready: {title}")
                else:
                    # Show player but indicate download needed
                    self.audio_player.pack(fill=tk.X, padx=5, pady=5)
                    self.podcast_download_btn.pack(side=tk.LEFT, padx=2)  # Show download button
                    self._set_status(f"Podcast episode (download to play): {title}")
            elif PODCAST_SUPPORT and self.audio_player:
                # Hide player and download button for non-podcast articles
                self.audio_player.pack_forget()
                self.podcast_download_btn.pack_forget()

    def _open_article(self):
        """Open selected article in browser."""
        if not self.selected_article_id:
            return

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT link FROM articles WHERE id = ?", (self.selected_article_id,))
        row = cursor.fetchone()

        if row:
            webbrowser.open(row[0])
            # Auto-mark as read
            self.db.mark_as_read(self.selected_article_id, True)
            self._update_view()
            self._set_status("Opened in browser")

    def _toggle_read(self):
        """Toggle read/unread status."""
        if not self.selected_article_id:
            return

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT is_read FROM articles WHERE id = ?", (self.selected_article_id,))
        row = cursor.fetchone()

        if row:
            new_status = not row[0]
            self.db.mark_as_read(self.selected_article_id, new_status)
            self._update_view()
            self._on_article_select(None)  # Refresh detail view

    def _toggle_favorite(self):
        """Toggle favorite status."""
        if not self.selected_article_id:
            return

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT is_favorite FROM articles WHERE id = ?", (self.selected_article_id,))
        row = cursor.fetchone()

        if row:
            new_status = not row[0]
            self.db.mark_as_favorite(self.selected_article_id, new_status)
            self._update_view()
            self._on_article_select(None)  # Refresh detail view

    def _download_podcast(self):
        """Download podcast episode for offline playback."""
        if not PODCAST_SUPPORT or not self.selected_article_id:
            return

        # Get article with audio URL
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT audio_url, title FROM articles WHERE id = ?
        """, (self.selected_article_id,))

        row = cursor.fetchone()
        if not row or not row[0]:
            messagebox.showwarning("No Podcast", "This article is not a podcast episode")
            return

        audio_url, title = row

        # Check if already downloaded
        existing_path = self.db.get_download_path(self.selected_article_id)
        if existing_path and os.path.exists(existing_path):
            messagebox.showinfo("Already Downloaded", "This episode is already downloaded")
            return

        self._set_status(f"Downloading: {title}...")

        # Download with progress callback
        def on_progress(downloaded, total):
            if total > 0:
                percent = (downloaded / total) * 100
                self.root.after(0, lambda p=percent: self._set_status(f"Downloading: {p:.1f}%"))

        def on_complete(success, file_path, error):
            if success:
                try:
                    # Get file size
                    file_size = os.path.getsize(file_path)

                    # Try to extract duration with mutagen if available
                    duration = 0
                    try:
                        from mutagen import File as MutagenFile
                        audio = MutagenFile(file_path)
                        if audio and audio.info:
                            duration = int(audio.info.length)
                    except:
                        pass

                    # Store in database
                    self.db.add_podcast_download(
                        self.selected_article_id,
                        audio_url,
                        file_path,
                        file_size,
                        duration
                    )

                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Episode downloaded!\n\n{file_size // 1024 // 1024} MB"))
                    self.root.after(0, lambda: self._set_status("Download complete"))
                    # Reload article to show player with downloaded episode
                    self.root.after(0, lambda: self._on_article_select(None))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to save download info: {e}"))
                    self.root.after(0, lambda: self._set_status("Ready"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Failed", f"Download failed: {error}"))
                self.root.after(0, lambda: self._set_status("Download failed"))

        # Start download
        try:
            self.podcast_downloader.download(
                audio_url,
                progress_callback=on_progress,
                completion_callback=on_complete
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start download: {e}")
            self._set_status("Ready")

    def _change_view(self, view: str):
        """Change view mode (all/unread/favorites)."""
        self.current_view = view
        self._update_view()

    def _search(self):
        """Search articles."""
        query = self.search_entry.get().strip()
        self.article_tree.delete(*self.article_tree.get_children())

        # Search based on current view
        show_read = self.current_view != "unread"
        favorites_only = self.current_view == "favorites"

        articles = self.db.search_articles(query,
                                          feed_url=self.current_feed_url,
                                          show_read=show_read,
                                          favorites_only=favorites_only)

        # Display results
        for article in articles:
            unread_marker = "●" if not article['is_read'] else ""
            fav_marker = "★" if article['is_favorite'] else ""
            date_str = article['published'][:10] if article['published'] else ""

            tags = []
            if not article['is_read']:
                tags.append('unread')
            else:
                tags.append('read')

            item_id = self.article_tree.insert("", tk.END, text=unread_marker,
                                               values=(fav_marker, article['title'], date_str),
                                               tags=tags)
            self.article_tree.item(item_id, tags=(str(article['id']),))

        self.article_tree.tag_configure('unread', font=("Arial", 10, "bold"))
        self.article_tree.tag_configure('read', foreground=self.current_theme.fg_secondary)

        self._set_status(f"Found {len(articles)} articles")

    def _clear_search(self):
        """Clear search and reset view."""
        self.search_entry.delete(0, tk.END)
        self._update_view()

    def _clear_cache(self):
        """Clear old cached articles."""
        if messagebox.askyesno("Confirm", "Clear articles older than 30 days?"):
            count = self.db.clear_old_articles(days=30)
            self._update_view()
            self._set_status(f"Cleared {count} old articles")

    def _next_article(self):
        """Select next article in list."""
        selection = self.article_tree.selection()
        if not selection:
            # Select first item
            children = self.article_tree.get_children()
            if children:
                self.article_tree.selection_set(children[0])
                self.article_tree.focus(children[0])
                self.article_tree.see(children[0])
                self._on_article_select(None)
        else:
            current = selection[0]
            next_item = self.article_tree.next(current)
            if next_item:
                self.article_tree.selection_set(next_item)
                self.article_tree.focus(next_item)
                self.article_tree.see(next_item)
                self._on_article_select(None)

    def _prev_article(self):
        """Select previous article in list."""
        selection = self.article_tree.selection()
        if selection:
            current = selection[0]
            prev_item = self.article_tree.prev(current)
            if prev_item:
                self.article_tree.selection_set(prev_item)
                self.article_tree.focus(prev_item)
                self.article_tree.see(prev_item)
                self._on_article_select(None)

    def _scroll_article(self, direction: int):
        """Scroll article detail view."""
        if direction > 0:
            self.detail_text.yview_scroll(3, "units")
        else:
            self.detail_text.yview_scroll(-3, "units")

    def _import_opml(self):
        """Import feeds from OPML file."""
        file_path = filedialog.askopenfilename(
            title="Import OPML",
            filetypes=[("OPML files", "*.opml *.xml"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            result = OPMLHandler.import_from_opml(file_path)
            feeds = result['feeds']
            categories = result['categories']

            # Import categories first
            cat_map = {}  # old_name -> new_id
            for cat in categories:
                cat_id = self.db.add_category(cat['name'], cat.get('color'))
                if cat_id:
                    cat_map[cat['name']] = cat_id

            # Import feeds
            imported = 0
            for feed in feeds:
                # Map category if exists
                cat_id = None
                if feed.get('category'):
                    cat_id = cat_map.get(feed['category'])

                if self.db.add_feed(feed['url'], feed['title'], category_id=cat_id):
                    imported += 1

            self._load_categories()
            self._load_feeds()
            self._update_view()

            messagebox.showinfo("Success",
                              f"Imported {imported} feeds and {len(cat_map)} categories")
            self._set_status(f"Imported {imported} feeds")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to import OPML:\n{str(e)}")

    def _export_opml(self):
        """Export feeds to OPML file."""
        file_path = filedialog.asksaveasfilename(
            title="Export OPML",
            defaultextension=".opml",
            filetypes=[("OPML files", "*.opml"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            feeds = []
            for feed in self.db.get_feeds():
                feed_dict = {
                    'title': feed['title'],
                    'url': feed['url'],
                    'category_id': feed.get('category_id')
                }
                feeds.append(feed_dict)

            categories = self.db.get_categories()

            if OPMLHandler.export_to_opml(feeds, categories, file_path):
                messagebox.showinfo("Success", f"Exported {len(feeds)} feeds to OPML")
                self._set_status(f"Exported {len(feeds)} feeds")
            else:
                messagebox.showerror("Error", "Failed to export OPML")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export OPML:\n{str(e)}")

    def _export_pdf(self):
        """Export articles to PDF file."""
        # Check if reportlab is available
        if not PDFExporter.is_available():
            messagebox.showerror(
                "PDF Export Unavailable",
                "PDF export requires the reportlab library.\n\n"
                "To install it, run:\n"
                "pip install reportlab\n\n"
                "or:\n"
                "pip3 install reportlab"
            )
            return

        # Get articles to export
        articles = []
        title = "RSS Articles Export"

        if self.current_view == "favorites":
            articles = self.db.get_favorites(limit=1000)
            title = "Favorite RSS Articles"
        elif self.current_view == "unread":
            if self.current_feed_url:
                articles = self.db.get_cached_articles(self.current_feed_url, unread_only=True, limit=1000)
                feed = next((f for f in self.db.get_feeds() if f['url'] == self.current_feed_url), None)
                if feed:
                    title = f"Unread Articles from {feed['title']}"
            else:
                articles = self.db.search_articles("", show_read=False)
                title = "All Unread RSS Articles"
        else:  # all
            if self.current_feed_url:
                articles = self.db.get_cached_articles(self.current_feed_url, limit=1000)
                feed = next((f for f in self.db.get_feeds() if f['url'] == self.current_feed_url), None)
                if feed:
                    title = f"Articles from {feed['title']}"
            else:
                articles = self.db.get_cached_articles(limit=1000)

        if not articles:
            messagebox.showinfo("No Articles", "No articles to export")
            return

        # Ask for file path
        file_path = filedialog.asksaveasfilename(
            title="Export to PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # Export to PDF
        self._set_status(f"Exporting {len(articles)} articles to PDF...")
        try:
            if PDFExporter.export_articles(articles, file_path, title=title):
                messagebox.showinfo("Success", f"Exported {len(articles)} articles to PDF")
                self._set_status(f"Exported {len(articles)} articles to PDF")
            else:
                messagebox.showerror("Error", "Failed to export PDF")
                self._set_status("PDF export failed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF:\n{str(e)}")
            self._set_status("PDF export failed")

    def _manage_categories(self):
        """Open category management dialog."""
        CategoryManager(self.root, self.db, self._on_categories_changed)

    def _on_categories_changed(self):
        """Callback when categories are modified."""
        self._load_categories()
        self._load_feeds()

    def _feed_settings(self):
        """Open feed settings dialog."""
        selection = self.feed_listbox.curselection()
        if not selection:
            messagebox.showinfo("Info", "Please select a feed")
            return

        url = self.feed_urls[selection[0]]
        feed = next((f for f in self.db.get_feeds() if f['url'] == url), None)

        if feed:
            FeedSettingsDialog(self.root, self.db, feed, self._load_feeds)

    def _show_statistics(self):
        """Show reading statistics."""
        StatisticsWindow(self.root, self.db)

    def _show_preferences(self):
        """Show preferences dialog."""
        PreferencesDialog(self.root, self.db, self.notifier, self._on_preferences_changed)

    def _on_preferences_changed(self):
        """Callback when preferences are modified."""
        # Reload notification settings
        notifications_enabled = self.db.get_setting("notifications_enabled", "true") == "true"
        self.notifier.set_enabled(notifications_enabled)

    def _set_status(self, message: str):
        """Update status label."""
        self.status_label.config(text=message)

    # V3.5 AI Features

    def _show_startup_message(self):
        """Show startup message with available features."""
        features = []
        if PODCAST_SUPPORT:
            features.append("Podcasts")
        if AI_SUPPORT:
            features.append("AI")

        if features:
            self._set_status(f"FeedMind ready - {', '.join(features)} available")
        else:
            self._set_status("FeedMind ready - Base features loaded")

    def _extract_full_text(self):
        """Extract full text of selected article."""
        if not AI_SUPPORT:
            messagebox.showinfo("Not Available", "AI features not installed.\n\nInstall with: pip install newspaper3k")
            return

        if not self.selected_article_id:
            messagebox.showwarning("No Article", "Please select an article first")
            return

        # Get article
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT title, link, full_text FROM articles WHERE id = ?", (self.selected_article_id,))
        row = cursor.fetchone()

        if not row:
            return

        title, link, existing_full_text = row[0], row[1], row[2]

        if existing_full_text:
            messagebox.showinfo("Already Extracted", f"Full text already extracted for:\n{title}\n\n{len(existing_full_text)} characters")
            return

        self._set_status(f"Extracting full text from {link}...")

        # Extract in background thread
        def extract():
            try:
                result = self.article_extractor.extract(link)
                if result and result['text']:
                    # Store in database
                    self.db.store_full_text(self.selected_article_id, result['text'])
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Success",
                        f"Extracted {len(result['text'])} characters\nMethod: {result['method']}"
                    ))
                    self.root.after(0, lambda: self._set_status("Full text extracted"))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Failed",
                        "Could not extract full text from this article"
                    ))
                    self.root.after(0, lambda: self._set_status("Extraction failed"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Extraction failed: {e}"))
                self.root.after(0, lambda: self._set_status("Ready"))

        threading.Thread(target=extract, daemon=True).start()

    def _generate_summary(self):
        """Generate AI summary of selected article."""
        if not AI_SUPPORT:
            messagebox.showinfo("Not Available", "AI features not installed.\n\nInstall with: pip install anthropic")
            return

        if not self.selected_article_id:
            messagebox.showwarning("No Article", "Please select an article first")
            return

        # Check for API key
        api_key = self.api_config.get_api_key("claude")
        if not api_key:
            messagebox.showwarning(
                "API Key Required",
                "Claude API key not configured.\n\nSet environment variable:\nexport RSS_API_KEY_CLAUDE='your-key'\n\nOr use AI → Configure API Keys"
            )
            return

        # Get article text
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT title, description, full_text, ai_summary FROM articles WHERE id = ?", (self.selected_article_id,))
        row = cursor.fetchone()

        if not row:
            return

        title, description, full_text, existing_summary = row

        if existing_summary:
            summary_data = self.db.get_ai_summary(self.selected_article_id)
            msg = f"Summary for: {title}\n\n"
            msg += f"TL;DR: {summary_data['tldr']}\n\n"
            msg += f"Summary:\n{summary_data['summary']}\n\n"
            if summary_data['key_points']:
                msg += "Key Points:\n"
                for i, point in enumerate(summary_data['key_points'], 1):
                    msg += f"{i}. {point}\n"
            messagebox.showinfo("AI Summary", msg)
            return

        text = full_text or description
        if not text or len(text) < 100:
            messagebox.showwarning("No Content", "Article text too short to summarize.\n\nTry AI → Extract Full Text first.")
            return

        self._set_status("Generating AI summary...")

        # Generate in background
        def generate():
            try:
                if not self.ai_summarizer:
                    self.ai_summarizer = AISummarizer(provider=AIProvider.CLAUDE, api_key=api_key)

                result = self.ai_summarizer.summarize_article(text)

                if result:
                    # Store in database
                    self.db.store_ai_summary(
                        self.selected_article_id,
                        result['summary'],
                        result['tldr'],
                        result['key_points']
                    )

                    msg = f"Summary for: {title}\n\n"
                    msg += f"TL;DR: {result['tldr']}\n\n"
                    msg += f"Summary:\n{result['summary']}\n\n"
                    if result['key_points']:
                        msg += "Key Points:\n"
                        for i, point in enumerate(result['key_points'], 1):
                            msg += f"{i}. {point}\n"

                    self.root.after(0, lambda: messagebox.showinfo("AI Summary", msg))
                    self.root.after(0, lambda: self._set_status("Summary generated"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Failed", "Could not generate summary"))
                    self.root.after(0, lambda: self._set_status("Ready"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Summary generation failed: {e}"))
                self.root.after(0, lambda: self._set_status("Ready"))

        threading.Thread(target=generate, daemon=True).start()

    def _generate_tldr(self):
        """Generate quick TL;DR of selected article."""
        if not AI_SUPPORT:
            messagebox.showinfo("Not Available", "AI features not installed.\n\nInstall with: pip install anthropic")
            return

        if not self.selected_article_id:
            messagebox.showwarning("No Article", "Please select an article first")
            return

        # Check for existing summary
        summary_data = self.db.get_ai_summary(self.selected_article_id)
        if summary_data and summary_data['tldr']:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT title FROM articles WHERE id = ?", (self.selected_article_id,))
            title = cursor.fetchone()[0]
            messagebox.showinfo("TL;DR", f"{title}\n\n{summary_data['tldr']}")
            return

        # Generate full summary which includes TL;DR
        self._generate_summary()

    def _configure_ai(self):
        """Configure AI API keys."""
        if not AI_SUPPORT:
            messagebox.showinfo("Not Available", "AI features not installed")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Configure AI API Keys")
        dialog.geometry("500x400")

        tk.Label(dialog, text="API Configuration", font=("Arial", 14, "bold")).pack(pady=10)

        # Instructions
        frame = tk.Frame(dialog)
        frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        instructions = """FeedMind supports AI-powered summarization using:

• Claude (Anthropic) - Recommended
• OpenAI GPT

To use AI features, you need an API key.

Get API Keys:
• Claude: https://console.anthropic.com/
• OpenAI: https://platform.openai.com/api-keys

Configure via Environment Variable (recommended):
export RSS_API_KEY_CLAUDE="your-api-key-here"
export RSS_API_KEY_OPENAI="your-openai-key"

Or store in database (less secure):"""

        tk.Label(frame, text=instructions, justify=tk.LEFT).pack(anchor=tk.W)

        # Claude API key
        tk.Label(frame, text="Claude API Key:").pack(anchor=tk.W, pady=(10, 0))
        claude_entry = tk.Entry(frame, width=50, show="*")
        claude_entry.pack(fill=tk.X)

        current_claude = self.api_config.get_api_key("claude")
        if current_claude:
            claude_entry.insert(0, current_claude)

        # OpenAI API key
        tk.Label(frame, text="OpenAI API Key:").pack(anchor=tk.W, pady=(10, 0))
        openai_entry = tk.Entry(frame, width=50, show="*")
        openai_entry.pack(fill=tk.X)

        current_openai = self.api_config.get_api_key("openai")
        if current_openai:
            openai_entry.insert(0, current_openai)

        # Save button
        def save_keys():
            claude_key = claude_entry.get().strip()
            openai_key = openai_entry.get().strip()

            if claude_key:
                self.api_config.set_api_key("claude", claude_key)
            if openai_key:
                self.api_config.set_api_key("openai", openai_key)

            messagebox.showinfo("Success", "API keys saved")
            dialog.destroy()

        tk.Button(frame, text="Save Keys", command=save_keys).pack(pady=10)

    def _about_ai_features(self):
        """Show information about AI features."""
        msg = """FeedMind AI Features (V3.5)

✨ TL;DR Generation
Ultra-quick 1-2 sentence summaries

✨ Smart Summaries
Comprehensive article overviews (200 words)

✨ Key Points Extraction
Bulleted list of main takeaways

✨ Full-Text Extraction
Fetch complete articles from web pages

💰 Cost-Effective
~$0.25 per 1,000 articles with Claude
Summaries are cached - never re-process

🔒 Privacy
API keys stored securely
Only sent to chosen AI provider
Your data stays local

To use AI features:
1. Install: pip install anthropic newspaper3k
2. Get API key from console.anthropic.com
3. Configure in AI → Configure API Keys
4. Select an article and use AI menu!"""

        messagebox.showinfo("About AI Features", msg)

    def _show_about(self):
        """Show about dialog."""
        features = ["Categories & OPML", "Dark Mode", "Reading Stats", "PDF Export"]
        if PODCAST_SUPPORT:
            features.append("🎙️ Podcast Support")
        if AI_SUPPORT:
            features.append("🤖 AI Summaries")

        msg = f"""FeedMind 🧠 v{__version__}

AI-Powered RSS Reader with Podcast Support

Features:
{chr(10).join('• ' + f for f in features)}

Database: feedmind.db
Python: {tk.TkVersion}

Smart feeds. Smarter reading.

Made with 🧠 for better content consumption"""

        messagebox.showinfo("About FeedMind", msg)

    def _on_closing(self):
        """Handle window close event."""
        if self.auto_refresh_job:
            self.root.after_cancel(self.auto_refresh_job)
        self.db.close()
        self.root.destroy()


class CategoryManager:
    """Dialog for managing categories."""

    def __init__(self, parent, db: RSSDatabase, callback):
        self.db = db
        self.callback = callback
        self.category_ids = []  # Maps listbox index to category ID

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Categories")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Category list
        tk.Label(self.dialog, text="Categories:").pack(anchor=tk.W, padx=10, pady=5)

        list_frame = tk.Frame(self.dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        self.listbox = tk.Listbox(list_frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Buttons
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="Add", command=self._add_category, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Remove", command=self._remove_category, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Close", command=self.dialog.destroy, width=10).pack(side=tk.RIGHT, padx=2)

        self._load_categories()

    def _load_categories(self):
        """Load categories into listbox."""
        self.listbox.delete(0, tk.END)
        self.category_ids.clear()
        for cat in self.db.get_categories():
            self.listbox.insert(tk.END, cat['name'])
            self.category_ids.append(cat['id'])

    def _add_category(self):
        """Add new category."""
        name = simpledialog.askstring("Add Category", "Category name:", parent=self.dialog)
        if name:
            if self.db.add_category(name):
                self._load_categories()
                self.callback()
            else:
                messagebox.showerror("Error", "Failed to add category")

    def _remove_category(self):
        """Remove selected category."""
        selection = self.listbox.curselection()
        if not selection:
            return

        cat_id = self.category_ids[selection[0]]
        name = self.listbox.get(selection[0])

        if messagebox.askyesno("Confirm", f"Remove category '{name}'?\nFeeds will be uncategorized."):
            if self.db.remove_category(cat_id):
                self._load_categories()
                self.callback()


class FeedSettingsDialog:
    """Dialog for feed settings."""

    def __init__(self, parent, db: RSSDatabase, feed: dict, callback):
        self.db = db
        self.feed = feed
        self.callback = callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Settings: {feed['title']}")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Category selection
        tk.Label(self.dialog, text="Category:").pack(anchor=tk.W, padx=10, pady=(10, 2))

        self.category_var = tk.StringVar()
        category_frame = tk.Frame(self.dialog)
        category_frame.pack(fill=tk.X, padx=10, pady=2)

        categories = [{"id": None, "name": "Uncategorized"}] + db.get_categories()
        self.category_combo = ttk.Combobox(category_frame, textvariable=self.category_var, state="readonly")
        self.category_combo['values'] = [c['name'] for c in categories]
        self.category_combo.pack(fill=tk.X)

        # Set current category
        if feed.get('category_id'):
            current_cat = next((c for c in categories if c['id'] == feed['category_id']), None)
            if current_cat:
                self.category_combo.set(current_cat['name'])
        else:
            self.category_combo.set("Uncategorized")

        self.category_map = {c['name']: c['id'] for c in categories}

        # Refresh interval
        tk.Label(self.dialog, text="Refresh Interval:").pack(anchor=tk.W, padx=10, pady=(10, 2))

        self.interval_var = tk.StringVar()
        interval_frame = tk.Frame(self.dialog)
        interval_frame.pack(fill=tk.X, padx=10, pady=2)

        intervals = [
            ("15 minutes", 15),
            ("30 minutes", 30),
            ("1 hour", 60),
            ("3 hours", 180),
            ("6 hours", 360),
            ("12 hours", 720),
            ("24 hours", 1440)
        ]

        self.interval_combo = ttk.Combobox(interval_frame, textvariable=self.interval_var, state="readonly")
        self.interval_combo['values'] = [label for label, _ in intervals]
        self.interval_combo.pack(fill=tk.X)

        # Set current interval
        current_interval = feed.get('refresh_interval', 15)
        for label, minutes in intervals:
            if minutes == current_interval:
                self.interval_combo.set(label)
                break

        self.interval_map = {label: minutes for label, minutes in intervals}

        # Last refresh info
        last_refresh = feed.get('last_refresh', 'Never')
        tk.Label(self.dialog, text=f"Last refreshed: {last_refresh}",
                fg="gray").pack(anchor=tk.W, padx=10, pady=10)

        # Buttons
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="Save", command=self._save, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side=tk.RIGHT, padx=2)

    def _save(self):
        """Save feed settings."""
        cat_name = self.category_var.get()
        cat_id = self.category_map.get(cat_name)

        interval_label = self.interval_var.get()
        interval = self.interval_map.get(interval_label, 15)

        self.db.update_feed_settings(self.feed['url'], cat_id, interval)
        self.callback()
        self.dialog.destroy()


class StatisticsWindow:
    """Window for displaying reading statistics."""

    def __init__(self, parent, db: RSSDatabase):
        self.db = db

        self.window = tk.Toplevel(parent)
        self.window.title("Reading Statistics")
        self.window.geometry("600x500")
        self.window.transient(parent)

        # Time period selection
        period_frame = tk.Frame(self.window)
        period_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(period_frame, text="Time Period:").pack(side=tk.LEFT, padx=(0, 5))

        self.period_var = tk.StringVar(value="30 days")
        for days, label in [(7, "7 days"), (30, "30 days"), (90, "90 days")]:
            tk.Radiobutton(period_frame, text=label, variable=self.period_var,
                          value=label, command=self._update_stats).pack(side=tk.LEFT, padx=5)

        # Statistics display
        self.stats_text = tk.Text(self.window, wrap=tk.WORD, height=20)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(self.window, command=self.stats_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.config(yscrollcommand=scrollbar.set)

        # Close button
        tk.Button(self.window, text="Close", command=self.window.destroy, width=10).pack(pady=10)

        self._update_stats()

    def _update_stats(self):
        """Update statistics display."""
        period_label = self.period_var.get()
        days = int(period_label.split()[0])

        stats = self.db.get_reading_statistics(days)

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)

        # Overview
        self.stats_text.insert(tk.END, f"📊 Reading Statistics - Last {days} Days\n", "header")
        self.stats_text.insert(tk.END, "=" * 60 + "\n\n")

        self.stats_text.insert(tk.END, f"Total Articles Read: {stats['total_read']}\n", "bold")
        self.stats_text.insert(tk.END, f"Average per Day: {stats['avg_per_day']:.1f}\n\n")

        self.stats_text.insert(tk.END, f"Total Feeds: {stats['total_feeds']}\n")
        self.stats_text.insert(tk.END, f"Unread Articles: {stats['unread_count']}\n")
        self.stats_text.insert(tk.END, f"Favorite Articles: {stats['favorites_count']}\n\n")

        # Daily breakdown
        if stats['daily_stats']:
            self.stats_text.insert(tk.END, "📅 Daily Breakdown:\n", "header")
            self.stats_text.insert(tk.END, "-" * 60 + "\n")

            for day_stat in stats['daily_stats'][-14:]:  # Show last 14 days
                date = day_stat['date']
                count = day_stat['count']
                bar = "█" * (count // 2) if count > 0 else ""
                self.stats_text.insert(tk.END, f"{date}: {count:3d} {bar}\n")

        # Configure tags
        self.stats_text.tag_config("header", font=("Arial", 12, "bold"))
        self.stats_text.tag_config("bold", font=("Arial", 10, "bold"))

        self.stats_text.config(state=tk.DISABLED)


class PreferencesDialog:
    """Dialog for application preferences."""

    def __init__(self, parent, db: RSSDatabase, notifier: NotificationManager, callback):
        self.db = db
        self.notifier = notifier
        self.callback = callback

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Preferences")
        self.dialog.geometry("450x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Notifications tab
        notif_frame = tk.Frame(notebook)
        notebook.add(notif_frame, text="Notifications")

        self._create_notifications_tab(notif_frame)

        # General tab
        general_frame = tk.Frame(notebook)
        notebook.add(general_frame, text="General")

        self._create_general_tab(general_frame)

        # Buttons
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Button(btn_frame, text="Save", command=self._save, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Cancel", command=self.dialog.destroy, width=10).pack(side=tk.RIGHT, padx=2)

    def _create_notifications_tab(self, parent):
        """Create notifications settings tab."""
        tk.Label(parent, text="Desktop Notifications", font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Check if notifications are available
        if not NotificationManager.is_available():
            warning_frame = tk.Frame(parent, bg="#FFF3CD", borderwidth=2, relief=tk.GROOVE)
            warning_frame.pack(fill=tk.X, padx=10, pady=10)

            tk.Label(
                warning_frame,
                text="⚠️  Desktop notifications are not available",
                bg="#FFF3CD",
                fg="#856404",
                font=("Arial", 10, "bold")
            ).pack(pady=5)

            tk.Label(
                warning_frame,
                text="To enable notifications, install the plyer library:\n"
                     "pip install plyer",
                bg="#FFF3CD",
                fg="#856404",
                font=("Arial", 9)
            ).pack(pady=5)

        # Enable/disable checkbox
        self.notif_enabled_var = tk.BooleanVar()
        current_value = self.db.get_setting("notifications_enabled", "true") == "true"
        self.notif_enabled_var.set(current_value)

        tk.Checkbutton(
            parent,
            text="Enable desktop notifications",
            variable=self.notif_enabled_var,
            state=tk.NORMAL if NotificationManager.is_available() else tk.DISABLED
        ).pack(anchor=tk.W, padx=20, pady=5)

        # Description
        desc_text = (
            "When enabled, you'll receive desktop notifications for:\n"
            "• New articles when refreshing feeds\n"
            "• Completion of bulk refresh operations\n"
        )
        tk.Label(parent, text=desc_text, justify=tk.LEFT, fg="gray").pack(anchor=tk.W, padx=20, pady=10)

        # Test notification button
        if NotificationManager.is_available():
            tk.Button(
                parent,
                text="Test Notification",
                command=self._test_notification
            ).pack(anchor=tk.W, padx=20, pady=10)

    def _create_general_tab(self, parent):
        """Create general settings tab."""
        tk.Label(parent, text="General Settings", font=("Arial", 11, "bold")).pack(anchor=tk.W, padx=10, pady=(10, 5))

        # PDF Export info
        pdf_frame = tk.Frame(parent)
        pdf_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(pdf_frame, text="PDF Export:", font=("Arial", 10, "bold")).pack(anchor=tk.W)

        if PDFExporter.is_available():
            tk.Label(
                pdf_frame,
                text="✓ PDF export is available",
                fg="green"
            ).pack(anchor=tk.W, padx=20)
        else:
            warning_frame = tk.Frame(pdf_frame, bg="#FFF3CD", borderwidth=2, relief=tk.GROOVE)
            warning_frame.pack(fill=tk.X, pady=5)

            tk.Label(
                warning_frame,
                text="⚠️  PDF export is not available",
                bg="#FFF3CD",
                fg="#856404",
                font=("Arial", 10, "bold")
            ).pack(pady=5)

            tk.Label(
                warning_frame,
                text="To enable PDF export, install the reportlab library:\n"
                     "pip install reportlab",
                bg="#FFF3CD",
                fg="#856404",
                font=("Arial", 9)
            ).pack(pady=5)

        # Database info
        tk.Label(parent, text=f"\nDatabase Location:", font=("Arial", 10, "bold")).pack(anchor=tk.W, padx=10)
        tk.Label(parent, text=f"  {self.db.db_path}", fg="gray").pack(anchor=tk.W, padx=10)

    def _test_notification(self):
        """Send a test notification."""
        self.notifier.notify_custom(
            "Test Notification",
            "If you can see this, notifications are working!"
        )

    def _save(self):
        """Save preferences."""
        # Save notification setting
        self.db.set_setting("notifications_enabled", "true" if self.notif_enabled_var.get() else "false")

        # Apply changes
        self.callback()

        messagebox.showinfo("Success", "Preferences saved")
        self.dialog.destroy()


def main():
    """Main entry point for FeedMind."""
    root = tk.Tk()
    app = FeedMind(root)
    root.mainloop()


if __name__ == "__main__":
    main()
