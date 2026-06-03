# FeedMind Changelog

All notable changes to FeedMind are documented in this file.

---

## v3.8.0 (2026-06-02)

A security, stability, and UI release. No new feature surface, but
substantial hardening and fixes throughout.

### Security
- **SSRF protection** - feed, article, and download URLs are resolved and
  rejected if they point to private/loopback/link-local/reserved or
  cloud-metadata addresses (e.g. `169.254.169.254`). The http(s) scheme
  allow-list is re-checked on every redirect.
- newspaper3k extraction now passes the SSRF check (it previously fetched
  with its own client, bypassing the guard).
- **Response-size caps** on feed/page reads (10 MiB) and a 2 GiB cap on
  podcast downloads, with partial-file cleanup on failure, to prevent
  memory/disk exhaustion from a hostile or misconfigured server.
- Podcast filenames are derived safely (URL path -> unquote -> basename)
  to block path traversal via encoded separators.
- The Windows MCI audio backend rejects file paths containing quote or
  control characters (command-string injection).
- Article links are validated as http(s) before opening in the browser;
  feed links are escaped in PDF export; untrusted article text is
  delimited in AI prompts; OPML recursion depth is bounded; notification
  titles are length-capped; downloaded video files are validated by
  extension before being handed to the system handler.

### Fixed
- **SQLite thread-safety** - each thread now gets its own connection with
  WAL and a busy timeout, replacing a single shared connection that could
  raise "recursive use of cursors" or corrupt data during "Refresh All".
- The destructive podcast-cleanup migration now runs **once** (gated by
  `PRAGMA user_version`) instead of on every startup.
- `cache_articles` surfaces a hard failure instead of silently dropping
  every article.
- Audio position updates are marshaled to the UI thread (previously
  unsafe cross-thread Tkinter access).
- Graceful shutdown waits for in-flight downloads and stops the audio
  backend cleanly.
- V1 `clear_old_articles` date math; duplicate OPML `xmlUrl` lookup;
  several bare `except:` clauses.

### UI
- Live counts on the **All / Unread / Favorites** filters (were hardcoded
  placeholders) and a clear active-filter highlight.
- Empty-state guidance for the feeds list, article list, and details pane.
- Full-width status bar at the bottom of the window.
- Working audio **seek bar** (seeks on release).

### Performance
- Feed unread counts are fetched in a single grouped query instead of one
  query per feed.

### Project
- Added the MIT **LICENSE** file referenced by the README.
- Test scripts are now runnable directly and under pytest (import-path
  shim + UTF-8 output); `buildozer.spec` no longer bundles `.db` files.

---

## v3.7.0 (2026-02-16)

### Added
- **Article sorting** - Sort by date (newest/oldest), title (A-Z/Z-A), or feed name via dropdown
- **7-day article filter** - "Last 7 Days Only" checkbox to reduce clutter
- **Feed bookmarks** - Pin feeds with `B` key; bookmarked feeds sort to top with pin icon
- `is_bookmarked` column in feeds table (auto-migrated)

### Keyboard Shortcuts
- **B** - Bookmark/unbookmark selected feed

---

## v3.6.0 (2026-02-03)

### Added
- **Video podcast support** - Auto-detects video files (MP4, MKV, AVI, MOV, etc.) and opens in system player
- **Podcast downloads folder** - File menu option to open `podcast_downloads/` directory
- `rss_video_player_ui.py` - Video player widget

---

## v3.5.0 (2026-01-31)

### Added
- **RSS feed auto-discovery** - Find feeds from any website URL
- **Local logging system** - Persistent log file for debugging
- AI-powered article summarization (Claude and OpenAI)
- Full-text article extraction
- TL;DR and key points generation

### Fixed
- Search keyboard shortcut handling
- Stability and performance improvements

---

## v3.0.0

### Added
- Podcast support with built-in audio player
- Episode downloads for offline listening
- Smart auto-refresh scheduling
- Category management
- PDF export
- Desktop notifications

---

## v2.0.0

### Added
- Multiple feed support
- OPML import/export
- Dark mode theme
- Reading statistics

---

## v1.0.0

### Added
- Basic RSS/Atom feed reader
- Article viewing
- Read/unread tracking
- Favorites system
