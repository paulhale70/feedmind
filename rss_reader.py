"""
RSS Reader Desktop Application
A feature-rich desktop RSS feed reader with GUI built using Tkinter.
"""

import logging
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, scrolledtext, ttk
from typing import Optional

from rss_core import RSSFetcher
from rss_database import RSSDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSReaderApp:
    """Main RSS Reader Desktop Application with advanced features."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("RSSreaderV1")
        self.root.geometry("1200x750")

        # Initialize components
        self.fetcher = RSSFetcher()
        self.db = RSSDatabase()
        self.current_feed: Optional[str] = None
        self.current_view = "all"  # all, unread, favorites
        self.auto_refresh_enabled = False
        self.refresh_timer = None

        # Setup UI
        self._setup_ui()

        # Load initial data
        self._load_feeds()
        self._update_unread_count()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Feed list
        left_panel = tk.Frame(main_container, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Feed management section
        feed_mgmt_frame = tk.LabelFrame(left_panel, text="Feed Management", padx=5, pady=5)
        feed_mgmt_frame.pack(fill=tk.X, pady=(0, 10))

        # Add feed controls
        tk.Label(feed_mgmt_frame, text="RSS Feed URL:").pack(anchor=tk.W)
        self.feed_url_entry = tk.Entry(feed_mgmt_frame, width=30)
        self.feed_url_entry.pack(fill=tk.X, pady=(0, 5))
        self.feed_url_entry.bind('<Return>', lambda e: self._add_feed())

        btn_frame = tk.Frame(feed_mgmt_frame)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Add Feed", command=self._add_feed,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(btn_frame, text="Remove", command=self._remove_feed,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # View selector
        view_frame = tk.LabelFrame(left_panel, text="View", padx=5, pady=5)
        view_frame.pack(fill=tk.X, pady=(0, 10))

        view_buttons = tk.Frame(view_frame)
        view_buttons.pack(fill=tk.X)

        tk.Button(view_buttons, text="All", command=lambda: self._change_view("all"),
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(view_buttons, text="Unread", command=lambda: self._change_view("unread"),
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 2))
        tk.Button(view_buttons, text="Favorites", command=lambda: self._change_view("favorites"),
                 bg="#E91E63", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # Unread counter
        self.unread_label = tk.Label(view_frame, text="Unread: 0", font=("Arial", 10, "bold"))
        self.unread_label.pack(pady=(5, 0))

        # Feeds list
        feeds_frame = tk.LabelFrame(left_panel, text="Subscribed Feeds", padx=5, pady=5)
        feeds_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollable feeds listbox
        self.feeds_listbox = tk.Listbox(feeds_frame, selectmode=tk.SINGLE)
        self.feeds_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.feeds_listbox.bind('<<ListboxSelect>>', self._on_feed_select)

        feeds_scrollbar = tk.Scrollbar(feeds_frame)
        feeds_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.feeds_listbox.config(yscrollcommand=feeds_scrollbar.set)
        feeds_scrollbar.config(command=self.feeds_listbox.yview)

        # Feed action buttons
        feed_actions = tk.Frame(left_panel)
        feed_actions.pack(fill=tk.X, pady=(10, 0))

        tk.Button(feed_actions, text="Refresh Feed", command=self._refresh_feed,
                 bg="#2196F3", fg="white").pack(fill=tk.X, pady=(0, 2))
        tk.Button(feed_actions, text="Refresh All", command=self._refresh_all_feeds,
                 bg="#00BCD4", fg="white").pack(fill=tk.X, pady=(0, 2))
        tk.Button(feed_actions, text="Mark All Read", command=self._mark_all_as_read,
                 bg="#9C27B0", fg="white").pack(fill=tk.X)

        # Auto-refresh checkbox
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_cb = tk.Checkbutton(left_panel, text="Auto-refresh (15 min)",
                                        variable=self.auto_refresh_var,
                                        command=self._toggle_auto_refresh)
        auto_refresh_cb.pack(pady=(10, 0))

        # Right panel - Articles
        right_panel = tk.Frame(main_container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Search and filter bar
        search_frame = tk.Frame(right_panel)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = tk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind('<Return>', lambda e: self._search_articles())

        tk.Button(search_frame, text="Search", command=self._search_articles,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(search_frame, text="Clear", command=self._clear_search,
                 bg="#9E9E9E", fg="white").pack(side=tk.LEFT)

        # Articles list
        articles_frame = tk.LabelFrame(right_panel, text="Articles", padx=5, pady=5)
        articles_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview for articles with status indicators
        columns = ('status', 'title', 'published')
        self.articles_tree = ttk.Treeview(articles_frame, columns=columns, show='tree headings', height=15)
        self.articles_tree.heading('status', text='')
        self.articles_tree.heading('title', text='Title')
        self.articles_tree.heading('published', text='Published')
        self.articles_tree.column('#0', width=0, stretch=False)
        self.articles_tree.column('status', width=40, stretch=False)
        self.articles_tree.column('title', width=600)
        self.articles_tree.column('published', width=150)

        # Configure tags for styling
        self.articles_tree.tag_configure('unread', font=('Arial', 10, 'bold'))
        self.articles_tree.tag_configure('read', foreground='gray')

        articles_scrollbar = tk.Scrollbar(articles_frame, orient=tk.VERTICAL, command=self.articles_tree.yview)
        self.articles_tree.configure(yscrollcommand=articles_scrollbar.set)

        self.articles_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        articles_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.articles_tree.bind('<Double-Button-1>', self._on_article_double_click)
        self.articles_tree.bind('<<TreeviewSelect>>', self._on_article_select)

        # Article details
        details_frame = tk.LabelFrame(right_panel, text="Article Details", padx=5, pady=5)
        details_frame.pack(fill=tk.BOTH, expand=True)

        self.details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=10)
        self.details_text.pack(fill=tk.BOTH, expand=True)

        # Action buttons
        action_frame = tk.Frame(right_panel)
        action_frame.pack(fill=tk.X, pady=(10, 0))

        tk.Button(action_frame, text="Open in Browser", command=self._open_in_browser,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))
        tk.Button(action_frame, text="Mark Read", command=self._toggle_read_status,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 3))
        tk.Button(action_frame, text="Favorite", command=self._toggle_favorite,
                 bg="#E91E63", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 3))
        tk.Button(action_frame, text="Clear Cache", command=self._clear_cache,
                 bg="#9E9E9E", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 0))

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Store article data
        self.articles_data = {}

    def _update_unread_count(self):
        """Update the unread counter display."""
        count = self.db.get_unread_count()
        self.unread_label.config(text=f"Unread: {count}")

    def _change_view(self, view: str):
        """Change the current view (all/unread/favorites)."""
        self.current_view = view
        if self.current_feed:
            self._load_articles(self.current_feed)
        self.status_var.set(f"Viewing: {view.capitalize()}")

    def _load_feeds(self):
        """Load subscribed feeds from database."""
        self.feeds_listbox.delete(0, tk.END)
        feeds = self.db.get_all_feeds()

        for feed in feeds:
            unread = self.db.get_unread_count(feed['url'])
            display_text = f"{feed['title']} ({unread})" if unread > 0 else feed['title']
            self.feeds_listbox.insert(tk.END, display_text)

        self.status_var.set(f"Loaded {len(feeds)} feeds")

    def _add_feed(self):
        """Add a new RSS feed."""
        url = self.feed_url_entry.get().strip()

        if not url:
            messagebox.showwarning("Invalid Input", "Please enter a feed URL")
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        self.status_var.set(f"Adding feed: {url}")

        def add_in_thread():
            try:
                # Fetch to validate (network operation in background thread)
                articles = self.fetcher.fetch_feed(url)

                # Extract feed title from first article or use URL
                title = url.split('//')[-1].split('/')[0]

                # Schedule database operations on main thread
                self.root.after(0, lambda: self._add_feed_to_db(url, title, articles))

            except Exception as e:
                logger.error(f"Failed to fetch feed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch feed:\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Ready"))

        threading.Thread(target=add_in_thread, daemon=True).start()

    def _add_feed_to_db(self, url: str, title: str, articles: list):
        """Add feed to database (must be called from main thread)."""
        try:
            # Add to database (on main thread)
            if self.db.add_feed(url, title):
                self._on_feed_added(url, articles)
            else:
                messagebox.showinfo("Info", "Feed already exists")
                self.status_var.set("Ready")
        except Exception as e:
            logger.error(f"Failed to add feed to database: {e}")
            messagebox.showerror("Error", f"Failed to add feed to database:\n{str(e)}")
            self.status_var.set("Ready")

    def _on_feed_added(self, url: str, articles: list):
        """Callback when feed is successfully added."""
        self.db.cache_articles(articles, url)
        self._load_feeds()
        self._update_unread_count()
        self.feed_url_entry.delete(0, tk.END)
        self.status_var.set(f"Feed added successfully with {len(articles)} articles")

    def _remove_feed(self):
        """Remove the selected feed."""
        selection = self.feeds_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a feed to remove")
            return

        if messagebox.askyesno("Confirm", "Remove this feed and all cached articles?"):
            feeds = self.db.get_all_feeds()
            feed = feeds[selection[0]]
            self.db.remove_feed(feed['url'])
            self._load_feeds()
            self._update_unread_count()
            self._clear_articles_view()
            self.status_var.set("Feed removed")

    def _on_feed_select(self, event):
        """Handle feed selection."""
        selection = self.feeds_listbox.curselection()
        if not selection:
            return

        feeds = self.db.get_all_feeds()
        feed = feeds[selection[0]]
        self.current_feed = feed['url']

        # Load cached articles
        self._load_articles(feed['url'])

    def _load_articles(self, feed_url: str):
        """Load and display articles for a feed based on current view."""
        self._clear_articles_view()

        # Get articles based on current view
        if self.current_view == "all":
            articles = self.db.get_cached_articles(feed_url)
        elif self.current_view == "unread":
            articles = self.db.search_articles("", feed_url, show_read=False)
        elif self.current_view == "favorites":
            # Get all favorites, then filter by feed
            all_favs = self.db.get_favorites()
            articles = [a for a in all_favs if a['feed_url'] == feed_url]
        else:
            articles = self.db.get_cached_articles(feed_url)

        for article in articles:
            # Create status indicator
            status = ""
            if article.get('is_favorite'):
                status += "★ "
            if not article.get('is_read'):
                status += "●"

            # Determine tag for styling
            tag = 'unread' if not article.get('is_read') else 'read'

            item_id = self.articles_tree.insert('', tk.END, values=(
                status,
                article['title'],
                article['published'] or 'N/A'
            ), tags=(tag,))
            self.articles_data[item_id] = article

        self.status_var.set(f"Loaded {len(articles)} articles")

    def _clear_articles_view(self):
        """Clear the articles view."""
        for item in self.articles_tree.get_children():
            self.articles_tree.delete(item)
        self.articles_data.clear()
        self.details_text.delete('1.0', tk.END)

    def _on_article_select(self, event):
        """Handle article selection and automatically mark as read."""
        selection = self.articles_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        article = self.articles_data.get(item_id)

        if article:
            self.details_text.delete('1.0', tk.END)

            # Show read/favorite status
            status_line = "Status: "
            if article.get('is_read'):
                status_line += "Read "
            else:
                status_line += "Unread "
            if article.get('is_favorite'):
                status_line += "★ Favorite"

            self.details_text.insert('1.0', f"{status_line}\n\n")
            self.details_text.insert(tk.END, f"Title: {article['title']}\n\n")
            self.details_text.insert(tk.END, f"Link: {article['link']}\n\n")
            self.details_text.insert(tk.END, f"Published: {article['published'] or 'N/A'}\n\n")
            self.details_text.insert(tk.END, f"Description:\n{article['description']}")

    def _on_article_double_click(self, event):
        """Handle double-click on article to open in browser."""
        self._open_in_browser()

    def _open_in_browser(self):
        """Open the selected article in a web browser and mark as read."""
        selection = self.articles_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an article")
            return

        item_id = selection[0]
        article = self.articles_data.get(item_id)

        if article and article['link']:
            webbrowser.open(article['link'])
            # Mark as read
            self.db.mark_as_read(article['id'], True)
            self._update_unread_count()
            # Refresh the view
            if self.current_feed:
                self._load_articles(self.current_feed)
            self._load_feeds()
            self.status_var.set(f"Opened: {article['title']}")

    def _toggle_read_status(self):
        """Toggle read/unread status of selected article."""
        selection = self.articles_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an article")
            return

        item_id = selection[0]
        article = self.articles_data.get(item_id)

        if article:
            new_status = not article.get('is_read', False)
            self.db.mark_as_read(article['id'], new_status)
            self._update_unread_count()
            # Refresh the view
            if self.current_feed:
                self._load_articles(self.current_feed)
            self._load_feeds()
            status_text = "read" if new_status else "unread"
            self.status_var.set(f"Marked as {status_text}")

    def _toggle_favorite(self):
        """Toggle favorite status of selected article."""
        selection = self.articles_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an article")
            return

        item_id = selection[0]
        article = self.articles_data.get(item_id)

        if article:
            new_status = not article.get('is_favorite', False)
            self.db.mark_as_favorite(article['id'], new_status)
            # Refresh the view
            if self.current_feed:
                self._load_articles(self.current_feed)
            status_text = "favorited" if new_status else "unfavorited"
            self.status_var.set(f"Article {status_text}")

    def _search_articles(self):
        """Search articles by query."""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Empty Search", "Please enter a search query")
            return

        self._clear_articles_view()

        # Search based on current view
        show_read = self.current_view != "unread"
        favorites_only = self.current_view == "favorites"

        articles = self.db.search_articles(
            query,
            feed_url=self.current_feed,
            show_read=show_read,
            favorites_only=favorites_only
        )

        for article in articles:
            # Create status indicator
            status = ""
            if article.get('is_favorite'):
                status += "★ "
            if not article.get('is_read'):
                status += "●"

            # Determine tag for styling
            tag = 'unread' if not article.get('is_read') else 'read'

            item_id = self.articles_tree.insert('', tk.END, values=(
                status,
                article['title'],
                article['published'] or 'N/A'
            ), tags=(tag,))
            self.articles_data[item_id] = article

        self.status_var.set(f"Found {len(articles)} articles matching '{query}'")

    def _clear_search(self):
        """Clear search and reload current view."""
        self.search_entry.delete(0, tk.END)
        if self.current_feed:
            self._load_articles(self.current_feed)

    def _mark_all_as_read(self):
        """Mark all articles in current feed as read."""
        if self.current_feed:
            count = self.db.mark_all_as_read(self.current_feed)
            self._update_unread_count()
            self._load_articles(self.current_feed)
            self._load_feeds()
            self.status_var.set(f"Marked {count} articles as read")
        else:
            count = self.db.mark_all_as_read()
            self._update_unread_count()
            self._load_feeds()
            self.status_var.set(f"Marked all {count} articles as read")

    def _refresh_feed(self):
        """Refresh the selected feed."""
        if not self.current_feed:
            messagebox.showwarning("No Selection", "Please select a feed to refresh")
            return

        self.status_var.set(f"Refreshing feed...")

        def refresh_in_thread():
            try:
                # Fetch articles (network operation in background thread)
                feed_url = self.current_feed
                articles = self.fetcher.fetch_feed(feed_url)

                # Schedule database operations on main thread
                self.root.after(0, lambda: self._cache_and_refresh_view(feed_url, articles))
            except Exception as e:
                logger.error(f"Failed to refresh feed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh:\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Ready"))

        threading.Thread(target=refresh_in_thread, daemon=True).start()

    def _cache_and_refresh_view(self, feed_url: str, articles: list):
        """Cache articles and refresh view (must be called from main thread)."""
        try:
            self.db.cache_articles(articles, feed_url)
            self._load_articles(feed_url)
            self._update_unread_count()
            self._load_feeds()
            self.status_var.set(f"Refreshed: {len(articles)} articles")
        except Exception as e:
            logger.error(f"Failed to cache articles: {e}")
            messagebox.showerror("Error", f"Failed to cache articles:\n{str(e)}")
            self.status_var.set("Ready")

    def _refresh_all_feeds(self):
        """Refresh all subscribed feeds."""
        feeds = self.db.get_all_feeds()
        if not feeds:
            messagebox.showinfo("No Feeds", "No feeds to refresh")
            return

        self.status_var.set(f"Refreshing {len(feeds)} feeds...")

        def refresh_all_in_thread():
            # Fetch all feeds (network operations in background thread)
            fetched_data = []
            for feed in feeds:
                try:
                    articles = self.fetcher.fetch_feed(feed['url'])
                    fetched_data.append((feed['url'], articles))
                except Exception as e:
                    logger.error(f"Failed to refresh {feed['url']}: {e}")

            # Schedule database operations on main thread
            self.root.after(0, lambda: self._cache_all_feeds(fetched_data))

        threading.Thread(target=refresh_all_in_thread, daemon=True).start()

    def _cache_all_feeds(self, fetched_data: list):
        """Cache all fetched feeds (must be called from main thread)."""
        try:
            total_articles = 0
            for feed_url, articles in fetched_data:
                self.db.cache_articles(articles, feed_url)
                total_articles += len(articles)

            self._update_unread_count()
            self._load_feeds()
            if self.current_feed:
                self._load_articles(self.current_feed)
            self.status_var.set(f"Refreshed all feeds: {total_articles} articles")
        except Exception as e:
            logger.error(f"Failed to cache all feeds: {e}")
            messagebox.showerror("Error", f"Failed to cache feeds:\n{str(e)}")
            self.status_var.set("Ready")

    def _toggle_auto_refresh(self):
        """Toggle automatic feed refresh."""
        self.auto_refresh_enabled = self.auto_refresh_var.get()

        if self.auto_refresh_enabled:
            self._schedule_auto_refresh()
            self.status_var.set("Auto-refresh enabled (every 15 minutes)")
        else:
            if self.refresh_timer:
                self.root.after_cancel(self.refresh_timer)
                self.refresh_timer = None
            self.status_var.set("Auto-refresh disabled")

    def _schedule_auto_refresh(self):
        """Schedule automatic refresh of all feeds."""
        if self.auto_refresh_enabled:
            self._refresh_all_feeds()
            # Schedule next refresh in 15 minutes (900000 ms)
            self.refresh_timer = self.root.after(900000, self._schedule_auto_refresh)

    def _clear_cache(self):
        """Clear old cached articles."""
        if messagebox.askyesno("Clear Cache", "Remove articles older than 30 days?"):
            self.db.clear_old_articles(30)
            self._update_unread_count()
            self._load_feeds()
            if self.current_feed:
                self._load_articles(self.current_feed)
            self.status_var.set("Cache cleared")

    def _on_closing(self):
        """Handle window close event."""
        if self.refresh_timer:
            self.root.after_cancel(self.refresh_timer)
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point for the RSS Reader application."""
    root = tk.Tk()
    app = RSSReaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
