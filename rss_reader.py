"""
RSS Reader Desktop Application
A simple desktop RSS feed reader with GUI built using Tkinter.
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
    """Main RSS Reader Desktop Application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("RSS Reader")
        self.root.geometry("1000x700")

        # Initialize components
        self.fetcher = RSSFetcher()
        self.db = RSSDatabase()
        self.current_feed: Optional[str] = None

        # Setup UI
        self._setup_ui()

        # Load initial data
        self._load_feeds()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Feed list
        left_panel = tk.Frame(main_container, width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        # Feed management section
        feed_mgmt_frame = tk.LabelFrame(left_panel, text="Feed Management", padx=5, pady=5)
        feed_mgmt_frame.pack(fill=tk.X, pady=(0, 10))

        # Add feed controls
        tk.Label(feed_mgmt_frame, text="RSS Feed URL:").pack(anchor=tk.W)
        self.feed_url_entry = tk.Entry(feed_mgmt_frame, width=30)
        self.feed_url_entry.pack(fill=tk.X, pady=(0, 5))

        btn_frame = tk.Frame(feed_mgmt_frame)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Add Feed", command=self._add_feed,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(btn_frame, text="Remove", command=self._remove_feed,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

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

        # Refresh button
        tk.Button(left_panel, text="Refresh Selected Feed",
                 command=self._refresh_feed, bg="#2196F3", fg="white").pack(fill=tk.X, pady=(10, 0))

        # Right panel - Articles
        right_panel = tk.Frame(main_container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Articles list
        articles_frame = tk.LabelFrame(right_panel, text="Articles", padx=5, pady=5)
        articles_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview for articles
        columns = ('title', 'published')
        self.articles_tree = ttk.Treeview(articles_frame, columns=columns, show='tree headings', height=15)
        self.articles_tree.heading('title', text='Title')
        self.articles_tree.heading('published', text='Published')
        self.articles_tree.column('#0', width=0, stretch=False)
        self.articles_tree.column('title', width=600)
        self.articles_tree.column('published', width=150)

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
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        tk.Button(action_frame, text="Clear Cache", command=self._clear_cache,
                 bg="#9E9E9E", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Store article data
        self.articles_data = {}

    def _load_feeds(self):
        """Load subscribed feeds from database."""
        self.feeds_listbox.delete(0, tk.END)
        feeds = self.db.get_all_feeds()

        for feed in feeds:
            self.feeds_listbox.insert(tk.END, feed['title'])

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
                # Fetch to validate
                articles = self.fetcher.fetch_feed(url)

                # Extract feed title from first article or use URL
                title = url
                if articles:
                    # Try to get feed title from the parsed data
                    title = url.split('//')[-1].split('/')[0]

                # Add to database
                if self.db.add_feed(url, title):
                    self.root.after(0, self._on_feed_added, url, articles)
                else:
                    self.root.after(0, lambda: messagebox.showinfo("Info", "Feed already exists"))
                    self.root.after(0, lambda: self.status_var.set("Ready"))

            except Exception as e:
                logger.error(f"Failed to add feed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to add feed:\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Ready"))

        threading.Thread(target=add_in_thread, daemon=True).start()

    def _on_feed_added(self, url: str, articles: list):
        """Callback when feed is successfully added."""
        self.db.cache_articles(articles, url)
        self._load_feeds()
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
        """Load and display articles for a feed."""
        self._clear_articles_view()

        articles = self.db.get_cached_articles(feed_url)

        for article in articles:
            item_id = self.articles_tree.insert('', tk.END, values=(
                article['title'],
                article['published'] or 'N/A'
            ))
            self.articles_data[item_id] = article

        self.status_var.set(f"Loaded {len(articles)} articles")

    def _clear_articles_view(self):
        """Clear the articles view."""
        for item in self.articles_tree.get_children():
            self.articles_tree.delete(item)
        self.articles_data.clear()
        self.details_text.delete('1.0', tk.END)

    def _on_article_select(self, event):
        """Handle article selection."""
        selection = self.articles_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        article = self.articles_data.get(item_id)

        if article:
            self.details_text.delete('1.0', tk.END)
            self.details_text.insert('1.0', f"Title: {article['title']}\n\n")
            self.details_text.insert(tk.END, f"Link: {article['link']}\n\n")
            self.details_text.insert(tk.END, f"Published: {article['published'] or 'N/A'}\n\n")
            self.details_text.insert(tk.END, f"Description:\n{article['description']}")

    def _on_article_double_click(self, event):
        """Handle double-click on article to open in browser."""
        self._open_in_browser()

    def _open_in_browser(self):
        """Open the selected article in a web browser."""
        selection = self.articles_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an article")
            return

        item_id = selection[0]
        article = self.articles_data.get(item_id)

        if article and article['link']:
            webbrowser.open(article['link'])
            self.status_var.set(f"Opened: {article['title']}")

    def _refresh_feed(self):
        """Refresh the selected feed."""
        if not self.current_feed:
            messagebox.showwarning("No Selection", "Please select a feed to refresh")
            return

        self.status_var.set(f"Refreshing feed...")

        def refresh_in_thread():
            try:
                articles = self.fetcher.fetch_feed(self.current_feed)
                self.db.cache_articles(articles, self.current_feed)
                self.root.after(0, lambda: self._load_articles(self.current_feed))
                self.root.after(0, lambda: self.status_var.set(f"Refreshed: {len(articles)} articles"))
            except Exception as e:
                logger.error(f"Failed to refresh feed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to refresh:\n{str(e)}"))
                self.root.after(0, lambda: self.status_var.set("Ready"))

        threading.Thread(target=refresh_in_thread, daemon=True).start()

    def _clear_cache(self):
        """Clear old cached articles."""
        if messagebox.askyesno("Clear Cache", "Remove articles older than 30 days?"):
            self.db.clear_old_articles(30)
            if self.current_feed:
                self._load_articles(self.current_feed)
            self.status_var.set("Cache cleared")

    def _on_closing(self):
        """Handle window close event."""
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point for the RSS Reader application."""
    root = tk.Tk()
    app = RSSReaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
