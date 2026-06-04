"""Database layer: thread-safety, migration gate, and accessors."""
import sqlite3
import threading

import pytest

from rss_database_v3 import RSSDatabase


def test_wal_and_schema_version(db):
    cur = db.conn.cursor()
    cur.execute("PRAGMA journal_mode")
    assert cur.fetchone()[0].lower() == "wal"
    cur.execute("PRAGMA user_version")
    assert cur.fetchone()[0] == 1  # destructive migration gate marked done


def test_concurrent_writes_no_corruption(db, make_article):
    """8 threads writing at once must not raise or lose rows.

    This is the exact scenario the single-shared-connection bug used to break
    with 'recursive use of cursors'.
    """
    errors = []

    def worker(t):
        try:
            db.cache_articles([make_article(i, feed=f"f{t}") for i in range(20)],
                              f"https://example.com/feed{t}")
        except Exception as e:  # pragma: no cover - failure path
            errors.append(repr(e))

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(8)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    assert errors == []
    cur = db.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM articles")
    assert cur.fetchone()[0] == 8 * 20


def test_get_article(db, make_article):
    db.cache_articles([make_article(1)], "https://example.com/feed")
    aid = db.get_cached_articles("https://example.com/feed")[0]["id"]
    art = db.get_article(aid)
    assert isinstance(art, dict)
    assert art["title"] == "Article 1"
    assert db.get_article(999999) is None


def test_get_all_unread_counts(db, make_article):
    db.cache_articles([make_article(i, feed="A") for i in range(3)], "feedA")
    db.cache_articles([make_article(i, feed="B") for i in range(2)], "feedB")
    counts = db.get_all_unread_counts()
    assert counts == {"feedA": 3, "feedB": 2}


def test_cache_articles_all_fail_raises(db):
    bad = object()  # has no .title etc. -> every insert fails
    with pytest.raises(RuntimeError):
        db.cache_articles([bad], "https://example.com/feed")


def test_migration_delete_runs_once(tmp_path, make_article):
    """The destructive v3.7.1 cleanup must not re-run on subsequent opens."""
    path = str(tmp_path / "m.db")
    db = RSSDatabase(path)
    db.close()

    # Seed a row the OLD (ungated) migration would have deleted.
    raw = sqlite3.connect(path)
    raw.execute(
        "INSERT INTO articles (feed_url, title, link, description, published, "
        "cached_date, audio_url) VALUES (?,?,?,?,?,?,?)",
        ("f", "keepme", "https://example.com/link", "d", "2026", "2026",
         "https://example.com/audio"),
    )
    raw.commit()
    raw.close()

    db2 = RSSDatabase(path)  # migration runs again; user_version already 1
    cur = db2.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM articles WHERE title='keepme'")
    survived = cur.fetchone()[0]
    db2.close()
    assert survived == 1
