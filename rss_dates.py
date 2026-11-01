"""
Date helpers shared by the database layer and the UI.

Feeds publish dates as free-form strings (RFC 822 for RSS, ISO 8601 for Atom).
Sorting those strings directly is wrong -- "Wed, 01 Jan 2020" sorts above
"Tue, 31 Oct 2026" -- so the database stores a normalized sort key alongside
the original string.
"""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

# Fixed-width, lexically sortable format for the published_sort column.
SORT_KEY_FORMAT = "%Y-%m-%dT%H:%M:%S"


def _to_naive_utc(dt: datetime) -> datetime:
    """Convert an aware datetime to naive UTC; leave naive ones unchanged."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_published_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a feed date (RFC 822, ISO 8601, or YYYY-MM-DD).

    Returns a naive UTC datetime, or None if the string can't be parsed.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()

    # RFC 822, common in RSS: "Thu, 15 Feb 2024 10:30:00 GMT"
    try:
        return _to_naive_utc(parsedate_to_datetime(date_str))
    except (TypeError, ValueError, IndexError):
        pass

    # ISO 8601, common in Atom: "2024-02-15T10:30:00Z", "2024-02-15T10:30:00+02:00"
    try:
        return _to_naive_utc(datetime.fromisoformat(date_str.replace("Z", "+00:00")))
    except ValueError:
        pass

    # Bare date prefix: "2024-02-15..."
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except ValueError:
        pass

    return None


def published_sort_key(published: Optional[str],
                       fallback: Optional[datetime] = None) -> str:
    """Return the published_sort value for an article.

    Uses the parsed publish date; if that fails, uses `fallback` (normally the
    time the article was cached) so undated articles still sort sensibly.
    """
    dt = parse_published_date(published)
    if dt is None:
        dt = fallback or datetime.now(timezone.utc).replace(tzinfo=None)
    return dt.strftime(SORT_KEY_FORMAT)
