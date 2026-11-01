"""Regression tests for: date sorting, old-article cleanup, uncapped counts,
read/unread row tags, and keyboard shortcuts firing while typing."""
import sqlite3
import types
from datetime import datetime, timedelta

import pytest

from rss_database_v3 import RSSDatabase
from rss_dates import parse_published_date, published_sort_key

FEED = "https://example.com/feed"


def _article(link, published, title=None):
    return types.SimpleNamespace(title=title or link, link=link,
                                 description="d", published=published)


def _age_all_articles(db, days):
    old = (datetime.now() - timedelta(days=days)).isoformat()
    db.conn.execute("UPDATE articles SET cached_date = ?", (old,))
    db.conn.commit()


# --- Date parsing -----------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("Tue, 27 Oct 2026 10:30:00 GMT", datetime(2026, 10, 27, 10, 30)),
    ("Tue, 27 Oct 2026 03:30:00 -0700", datetime(2026, 10, 27, 10, 30)),
    ("2026-10-27T10:30:00Z", datetime(2026, 10, 27, 10, 30)),
    ("2026-10-27T12:30:00+02:00", datetime(2026, 10, 27, 10, 30)),
    ("2026-10-27", datetime(2026, 10, 27)),
])
def test_parse_published_date_formats(text, expected):
    assert parse_published_date(text) == expected


@pytest.mark.parametrize("text", ["", None, "not a date", "Someday soon"])
def test_parse_published_date_garbage(text):
    assert parse_published_date(text) is None


def test_sort_key_falls_back_for_unparseable_dates():
    fallback = datetime(2026, 1, 2, 3, 4, 5)
    assert published_sort_key("garbage", fallback) == "2026-01-02T03:04:05"


# --- Sorting by real date, not by the date string ---------------------------

def test_articles_sorted_by_actual_date(db):
    # As strings, "Wed..." sorts above "Tue..." even though it is 6 years older.
    db.cache_articles([
        _article("https://example.com/old", "Wed, 01 Jan 2020 00:00:00 GMT"),
        _article("https://example.com/new", "Tue, 27 Oct 2026 00:00:00 GMT"),
        _article("https://example.com/mid", "2024-06-01T00:00:00Z"),
    ], FEED)
    links = [a["link"] for a in db.get_cached_articles()]
    assert links == ["https://example.com/new", "https://example.com/mid",
                     "https://example.com/old"]


def test_limit_keeps_the_newest_unread(db):
    db.cache_articles([
        _article(f"https://example.com/{d}", f"Wed, {d:02d} Jan 2020 00:00:00 GMT")
        for d in range(1, 11)
    ] + [_article("https://example.com/newest", "Mon, 26 Oct 2026 00:00:00 GMT")], FEED)
    top = db.get_cached_articles(limit=1, unread_only=True)
    assert top[0]["link"] == "https://example.com/newest"


def test_existing_database_is_backfilled(tmp_path):
    """A database from before published_sort existed gets the column filled."""
    path = str(tmp_path / "old.db")
    raw = sqlite3.connect(path)
    raw.execute("""
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, feed_url TEXT NOT NULL,
            title TEXT NOT NULL, link TEXT NOT NULL, description TEXT,
            published TEXT, cached_date TEXT NOT NULL,
            is_read INTEGER DEFAULT 0, read_date TEXT,
            is_favorite INTEGER DEFAULT 0, UNIQUE(feed_url, link))
    """)
    raw.executemany(
        "INSERT INTO articles (feed_url, title, link, published, cached_date) "
        "VALUES (?, ?, ?, ?, ?)",
        [(FEED, "old", "u1", "Wed, 01 Jan 2020 00:00:00 GMT", "2026-10-01T00:00:00"),
         (FEED, "new", "u2", "Tue, 27 Oct 2026 00:00:00 GMT", "2026-10-01T00:00:00"),
         (FEED, "undated", "u3", "", "2026-10-01T00:00:00")],
    )
    raw.commit()
    raw.close()

    db = RSSDatabase(path)
    try:
        rows = {a["title"]: a["published_sort"] for a in db.get_cached_articles()}
        assert rows == {"new": "2026-10-27T00:00:00", "old": "2020-01-01T00:00:00",
                        "undated": "2026-10-01T00:00:00"}
        assert [a["title"] for a in db.get_cached_articles()][0] == "new"
    finally:
        db.close()


# --- Old-article cleanup ----------------------------------------------------

def test_cleanup_keeps_favorites_and_downloads(db):
    db.cache_articles([_article(f"https://example.com/{i}", "2026-01-01") for i in range(3)],
                      FEED)
    ids = {a["link"]: a["id"] for a in db.get_cached_articles()}
    db.mark_as_favorite(ids["https://example.com/0"])
    db.add_podcast_download(ids["https://example.com/1"], "https://example.com/1.mp3",
                            "C:/fake/1.mp3", 123)
    _age_all_articles(db, 30)

    assert db.clear_old_articles(days=21) == 1
    remaining = {a["link"] for a in db.get_cached_articles()}
    assert remaining == {"https://example.com/0", "https://example.com/1"}
    assert db.get_download_path(ids["https://example.com/1"]) == "C:/fake/1.mp3"


def test_cleared_articles_do_not_return_as_unread(db):
    feed_items = [_article(f"https://example.com/{i}", "2026-01-01") for i in range(3)]
    db.cache_articles(feed_items, FEED)
    _age_all_articles(db, 30)
    db.clear_old_articles(days=21)

    # Next refresh: the feed still lists the same items.
    assert db.cache_articles(feed_items, FEED) == 0
    assert db.get_cached_articles() == []

    # A genuinely new item is still added.
    assert db.cache_articles(feed_items + [_article("https://example.com/new", "2026-10-30")],
                             FEED) == 1


def test_cleared_podcast_episode_does_not_return(db):
    ep = types.SimpleNamespace(title="Ep", link="https://example.com/show",
                               description="d", published="2026-01-01",
                               audio_url="https://example.com/ep1.mp3",
                               audio_type="audio/mpeg", audio_length=1, duration_seconds=1)
    db.cache_articles([ep], FEED)
    _age_all_articles(db, 30)
    db.clear_old_articles(days=21)
    assert db.cache_articles([ep], FEED) == 0


def _cleared_count(db):
    return db.conn.execute("SELECT COUNT(*) FROM cleared_articles").fetchone()[0]


def test_cleared_records_pruned_only_after_feed_stops_listing_them(db):
    db.add_feed(FEED, "Feed")
    db.cache_articles([_article("https://example.com/gone", "2026-01-01")], FEED)
    _age_all_articles(db, 30)
    db.clear_old_articles(days=21)
    long_ago = (datetime.now() - timedelta(days=120)).isoformat()
    db.conn.execute("UPDATE cleared_articles SET last_seen = ?", (long_ago,))

    # App unused for months (feed not refreshed since): record must be kept.
    db.conn.execute("UPDATE feeds SET last_refresh = ?", (long_ago,))
    db.conn.commit()
    db.clear_old_articles(days=21)
    assert _cleared_count(db) == 1

    # Feed refreshed recently without listing the article: record is pruned.
    db.update_feed_last_refresh(FEED)
    db.clear_old_articles(days=21)
    assert _cleared_count(db) == 0


def test_remove_feed_forgets_cleared_records(db):
    db.add_feed(FEED, "Feed")
    db.cache_articles([_article("https://example.com/a", "2026-01-01")], FEED)
    _age_all_articles(db, 30)
    db.clear_old_articles(days=21)
    assert db.remove_feed(FEED) is True  # true even with no articles left
    assert _cleared_count(db) == 0


# --- Counts are not capped by the list limit --------------------------------

def test_article_counts_are_uncapped(db):
    db.cache_articles([_article(f"https://example.com/{i}", "2026-01-01")
                       for i in range(1200)], FEED)
    first = db.get_cached_articles(limit=2)
    db.mark_as_read(first[0]["id"])
    db.mark_as_favorite(first[1]["id"])
    assert db.get_article_counts() == {"total": 1200, "unread": 1199, "favorites": 1}
    assert db.get_feed_article_count(FEED) == 1200


def test_article_counts_empty_database(db):
    assert db.get_article_counts() == {"total": 0, "unread": 0, "favorites": 0}


# --- UI: row tags and shortcut guard ----------------------------------------

try:
    import tkinter as tk
except ImportError:  # pragma: no cover - Tk missing; GUI tests skip below
    tk = None


@pytest.fixture
def feedmind_cls():
    return pytest.importorskip("feedmind").FeedMind


@pytest.fixture
def tk_root():
    if tk is None:
        pytest.skip("tkinter not available")
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no Tk display available")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


def test_article_tags_keep_id_first_and_read_state(feedmind_cls):
    assert feedmind_cls._article_tags({"id": 7, "is_read": 0}) == ("7", "unread")
    assert feedmind_cls._article_tags({"id": 8, "is_read": 1}) == ("8", "read")


@pytest.mark.gui
@pytest.mark.parametrize("widget_kind, typing", [
    ("entry", True),
    ("ttk_entry", True),
    ("text", True),
    ("disabled_text", False),  # like the article details pane
    ("listbox", False),
    ("treeview", False),
    (None, False),             # nothing focused
])
def test_typing_in_field_detection(feedmind_cls, tk_root, widget_kind, typing):
    from tkinter import ttk
    widget = {
        "entry": lambda: tk.Entry(tk_root),
        "ttk_entry": lambda: ttk.Entry(tk_root),
        "text": lambda: tk.Text(tk_root),
        "disabled_text": lambda: tk.Text(tk_root, state=tk.DISABLED),
        "listbox": lambda: tk.Listbox(tk_root),
        "treeview": lambda: ttk.Treeview(tk_root),
        None: lambda: None,
    }[widget_kind]()
    fake = types.SimpleNamespace(
        root=types.SimpleNamespace(focus_get=lambda: widget),
        _TEXT_INPUT_CLASSES=feedmind_cls._TEXT_INPUT_CLASSES,
    )
    assert feedmind_cls._typing_in_field(fake) is typing


@pytest.mark.parametrize("typing, expected_calls", [(True, 0), (False, 1)])
def test_bound_shortcut_skipped_while_typing(feedmind_cls, typing, expected_calls):
    bound, calls = {}, []
    fake = types.SimpleNamespace(
        root=types.SimpleNamespace(bind=lambda seq, handler: bound.update({seq: handler})),
        _typing_in_field=lambda: typing,
    )
    feedmind_cls._bind_key(fake, "r", lambda: calls.append(1))
    bound["r"](None)  # simulate the key press
    assert len(calls) == expected_calls
