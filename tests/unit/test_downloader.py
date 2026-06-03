"""Podcast downloader: safe filename derivation and size cap."""
import pytest

from rss_podcast_downloader import PodcastDownloader


@pytest.fixture
def dl(tmp_path):
    return PodcastDownloader(download_dir=str(tmp_path))


@pytest.mark.parametrize("url", [
    "https://host/path/ep1.mp3?token=abc",
    "https://host/a%2f..%2f..%2fevil.mp3",   # encoded path separators
    "https://host/dir/sub/show%20ep.mp3",
    "https://host/noext",
])
def test_generated_filename_has_no_separators(dl, url):
    name = dl._generate_filename(url)
    assert "/" not in name and "\\" not in name
    assert name  # non-empty


def test_query_string_stripped(dl):
    assert dl._generate_filename("https://host/path/ep1.mp3?x=1") == "ep1.mp3"


def test_missing_extension_gets_mp3(dl):
    assert dl._generate_filename("https://host/noext").endswith(".mp3")


def test_sanitize_filename_replaces_invalid_chars(dl):
    out = dl._sanitize_filename('a<b>c:"d/e\\f|g?h*i.mp3')
    assert not any(c in out for c in '<>:"/\\|?*')


def test_default_size_cap(dl):
    assert dl.max_download_bytes == 2 * 1024 * 1024 * 1024
