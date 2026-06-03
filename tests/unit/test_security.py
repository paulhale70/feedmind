"""SSRF guard and response-cap tests (rss_core)."""
import io
import ipaddress
import pytest

from rss_core import _validate_url, UnsafeURLError, read_capped, _is_public_ip


@pytest.mark.parametrize("url", [
    "http://127.0.0.1/admin",        # loopback
    "http://localhost/",             # resolves to loopback
    "http://169.254.169.254/latest", # cloud metadata (link-local)
    "http://10.0.0.5/",              # private
    "http://192.168.1.1/",           # private
    "http://0.0.0.0/",               # unspecified
    "file:///etc/passwd",            # disallowed scheme
    "ftp://example.com/x",           # disallowed scheme
    "gopher://evil/",                # disallowed scheme
])
def test_validate_url_blocks_unsafe(url):
    with pytest.raises(UnsafeURLError):
        _validate_url(url)


def test_validate_url_allows_public_literal():
    # A public IP literal needs no DNS and must pass.
    _validate_url("http://93.184.216.34/")  # should not raise


def test_is_public_ip():
    assert _is_public_ip(ipaddress.ip_address("8.8.8.8")) is True
    assert _is_public_ip(ipaddress.ip_address("127.0.0.1")) is False
    assert _is_public_ip(ipaddress.ip_address("10.0.0.1")) is False
    assert _is_public_ip(ipaddress.ip_address("169.254.169.254")) is False


class _FakeResponse:
    def __init__(self, data):
        self._b = io.BytesIO(data)

    def read(self, n=-1):
        return self._b.read(n)


def test_read_capped_under_limit():
    assert read_capped(_FakeResponse(b"x" * 100), max_bytes=1000) == b"x" * 100


def test_read_capped_truncates():
    out = read_capped(_FakeResponse(b"x" * 5000), max_bytes=1000)
    assert len(out) == 1000
