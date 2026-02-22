# FeedMind Changelog

All notable changes to FeedMind are documented in this file.

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
