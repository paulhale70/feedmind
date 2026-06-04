"""Shared fixtures for the deterministic unit suite."""
import types
import pytest

from rss_database_v3 import RSSDatabase


@pytest.fixture
def db(tmp_path):
    """A fresh V3 database backed by a temp file."""
    database = RSSDatabase(str(tmp_path / "test.db"))
    yield database
    database.close()


@pytest.fixture
def make_article():
    """Factory for lightweight article objects accepted by cache_articles."""
    def _make(i, feed="A", audio=None):
        a = types.SimpleNamespace()
        a.title = f"Article {i}"
        a.link = f"https://example.com/{feed}/{i}"
        a.description = "Body text"
        a.published = "2026-06-01"
        if audio:
            a.audio_url = audio
            a.audio_type = "audio/mpeg"
            a.audio_length = 1000
            a.duration_seconds = 60
        return a
    return _make
