"""Regression tests: a podcast download is saved against the article it was
started for, and removing a category refreshes and uncategorizes its feeds."""
import types

import pytest

FEED = "https://example.com/feed"


# --- Bug 5: download attached to the article selected when it finishes ------

def _episode(n):
    return types.SimpleNamespace(
        title=f"Episode {n}", link=f"https://example.com/ep{n}", description="d",
        published=f"Tue, {n:02d} Oct 2026 10:00:00 GMT",
        audio_url=f"https://cdn.example.com/ep{n}.mp3")


def test_download_saved_against_the_article_it_started_for(db, tmp_path, monkeypatch):
    feedmind = pytest.importorskip("feedmind")
    monkeypatch.setattr(feedmind, "PODCAST_SUPPORT", True)
    db.add_feed(FEED, "Show")
    db.cache_articles([_episode(1), _episode(2)], FEED)
    first, second = sorted((a["id"] for a in db.get_cached_articles()))

    started = {}

    class FakeDownloader:
        def download(self, url, progress_callback=None, completion_callback=None):
            started.update(url=url, done=completion_callback)
            return True

    reloads = []
    app = types.SimpleNamespace(
        db=db, selected_article_id=first, podcast_downloader=FakeDownloader(),
        logger=feedmind.logging.getLogger("test"),
        root=types.SimpleNamespace(after=lambda _ms, fn: fn()),
        _set_status=lambda _msg: None,
        _on_article_select=lambda _e: reloads.append(app.selected_article_id),
    )
    app._reload_if_selected = lambda aid: feedmind.FeedMind._reload_if_selected(app, aid)
    monkeypatch.setattr(feedmind.messagebox, "showinfo", lambda *a, **k: None)

    feedmind.FeedMind._download_podcast(app)
    assert started["url"].endswith("/ep1.mp3")

    # The user moves on to another article before the download finishes.
    app.selected_article_id = second
    audio = tmp_path / "ep1.mp3"
    audio.write_bytes(b"x" * 10)
    started["done"](True, str(audio), None)

    assert db.get_download_path(first) == str(audio)
    assert db.get_download_path(second) is None
    assert reloads == []  # the pane showing episode 2 isn't redrawn


# --- Bug 6: removing a category ----------------------------------------------

def test_remove_category_reports_success_and_uncategorizes_feeds(db):
    cat = db.add_category("News")
    db.add_feed(FEED, "Feed", category_id=cat)
    assert db.remove_category(cat) is True
    assert "News" not in [c["name"] for c in db.get_categories()]
    feed = next(f for f in db.get_feeds() if f["url"] == FEED)
    assert feed["category_id"] is None
    assert db.remove_category(cat) is False


def test_remove_category_without_foreign_key_action(db):
    """Upgraded databases got category_id via ALTER TABLE, with no ON DELETE SET NULL."""
    cat = db.add_category("News")
    db.add_feed(FEED, "Feed", category_id=cat)
    db.conn.execute("PRAGMA foreign_keys=OFF")
    db.remove_category(cat)
    feed = next(f for f in db.get_feeds() if f["url"] == FEED)
    assert feed["category_id"] is None


try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None


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


@pytest.mark.gui
def test_category_dialog_refreshes_after_remove(db, tk_root, monkeypatch):
    feedmind = pytest.importorskip("feedmind")
    db.add_category("News")
    db.add_category("Tech")
    calls = []
    dialog = feedmind.CategoryManager(tk_root, db, lambda: calls.append(1))
    names = dialog.listbox.get(0, tk.END)
    assert "News" in names

    monkeypatch.setattr(feedmind.messagebox, "askyesno", lambda *a, **k: True)
    dialog.listbox.selection_set(names.index("News"))
    dialog._remove_category()

    after = dialog.listbox.get(0, tk.END)
    assert "News" not in after and "Tech" in after
    assert calls == [1]
    dialog.dialog.destroy()


@pytest.mark.gui
def test_main_window_leaves_removed_category(db, tk_root):
    feedmind = pytest.importorskip("feedmind")
    cat = db.add_category("News")
    app = types.SimpleNamespace(
        db=db, category_ids=[], current_category_id=cat,
        category_listbox=tk.Listbox(tk_root))
    feedmind.FeedMind._load_categories(app)
    assert app.category_listbox.curselection() == (app.category_ids.index(cat),)

    db.remove_category(cat)
    feedmind.FeedMind._load_categories(app)
    assert app.current_category_id is None
    assert app.category_listbox.curselection() == (0,)
