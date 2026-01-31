# FeedMind v3.5.0 - Complete Feature List

## Overview

**feedmind.py** is the consolidated, production-ready version of FeedMind that includes ALL features from versions 1.0 through 3.5.

**Database**: `feedmind.db` (SQLite3)
**Main File**: `feedmind.py` (1,912 lines)
**Python**: 3.8+
**GUI**: Tkinter

---

## Core Features (V1 Base)

### Feed Management
- ✅ Add RSS/Atom feeds by URL
- ✅ Remove feeds
- ✅ Auto-detect feed metadata (title, description)
- ✅ Support for RSS 2.0 and Atom 1.0 formats
- ✅ Automatic feed parsing and caching
- ✅ Background threaded feed fetching

### Article Management
- ✅ View articles in list format
- ✅ Article details display (title, date, description, link)
- ✅ Open articles in web browser
- ✅ Automatic caching of articles in SQLite database
- ✅ Article deduplication by URL

### User Interface
- ✅ Clean Tkinter-based GUI
- ✅ Two-pane layout (feeds + articles)
- ✅ Status bar with operation feedback
- ✅ Keyboard shortcuts for navigation

---

## Enhanced Features (V2)

### Organization
- ✅ **Categories** - Organize feeds into categories
- ✅ **Favorites** - Star important articles
- ✅ **Read/Unread tracking** - Mark articles as read/unread
- ✅ **Unread counter** - See total unread articles
- ✅ **Category filtering** - View feeds by category

### Views & Filters
- ✅ **All Articles** view - See everything
- ✅ **Unread Only** view - Focus on new content
- ✅ **Favorites** view - Quick access to starred articles
- ✅ **Search** - Full-text search across all articles
- ✅ **Per-feed view** - Filter articles by selected feed

### Import/Export
- ✅ **OPML Import** - Import feeds from other readers
- ✅ **OPML Export** - Export your feed list
- ✅ **Category support in OPML** - Preserve organization
- ✅ **PDF Export** - Export articles to PDF documents

### Appearance
- ✅ **Light Theme** - Clean, bright interface
- ✅ **Dark Theme** - Easy on the eyes at night
- ✅ **Theme persistence** - Remember your preference
- ✅ **Dynamic styling** - Unread articles shown in bold
- ✅ **Color-coded categories** - Visual organization

### Automation
- ✅ **Refresh Feed** - Update selected feed
- ✅ **Refresh All** - Update all feeds at once
- ✅ **Mark All Read** - Bulk mark as read
- ✅ **Auto-refresh scheduling** - Per-feed refresh intervals
- ✅ **Background updates** - Non-blocking operations

### Statistics
- ✅ **Reading stats** - See how much you read
- ✅ **Daily breakdown** - Track reading over time
- ✅ **7/30/90 day views** - Flexible time periods
- ✅ **Articles per day** - Average reading rate
- ✅ **Visual charts** - ASCII bar charts

### Notifications
- ✅ **Desktop notifications** - Get alerted to new articles
- ✅ **New article count** - See how many arrived
- ✅ **Configurable** - Enable/disable as needed
- ✅ **Test notifications** - Verify they work

### Feed Settings
- ✅ **Custom refresh intervals** - 15min to 24hr
- ✅ **Per-feed categories** - Organize individually
- ✅ **Last refresh timestamp** - See when updated

### Keyboard Shortcuts
- ✅ `j/k` - Next/previous article
- ✅ `o/Enter` - Open article in browser
- ✅ `r` - Toggle read/unread
- ✅ `f` - Toggle favorite
- ✅ `1/2/3` - Switch views (all/unread/favorites)
- ✅ `n` - Focus feed URL entry
- ✅ `Ctrl+R` - Refresh current feed
- ✅ `Ctrl+Shift+R` - Refresh all feeds
- ✅ `Ctrl+F` - Focus search
- ✅ `Ctrl+T` - Toggle dark mode
- ✅ `Ctrl+S` - Show statistics
- ✅ `Ctrl+I` - Import OPML
- ✅ `Ctrl+E` - Export OPML
- ✅ `Ctrl+P` - Export to PDF
- ✅ `Ctrl+M` - Manage categories
- ✅ `Space` - Scroll article down
- ✅ `Shift+Space` - Scroll article up
- ✅ `Esc` - Clear search

---

## Podcast Features (V3)

### Podcast Detection
- ✅ **Auto-detect podcasts** - Recognize podcast feeds
- ✅ **Audio enclosure parsing** - Extract MP3/M4A URLs
- ✅ **Duration extraction** - Show episode length
- ✅ **iTunes metadata** - Support iTunes podcast extensions
- ✅ **Podcast indicator** - 🎙️ icon for episodes

### Audio Playback
- ✅ **Built-in audio player** - Play episodes in-app
- ✅ **Play/Pause** - Standard controls
- ✅ **Seek bar** - Jump to any position
- ✅ **Volume control** - Adjust playback volume
- ✅ **Playback speed** - 0.5x to 2.0x speed
- ✅ **Progress tracking** - See current position
- ✅ **Time display** - Current time / total duration

### Episode Management
- ✅ **Download episodes** - Save for offline playback
- ✅ **Download progress** - See download percentage
- ✅ **Episode metadata** - Extract duration, file size
- ✅ **Download tracking** - Remember what's downloaded
- ✅ **Auto-load player** - Load episodes when selected

### Smart Refresh
- ✅ **Auto-refresh scheduling** - Update feeds automatically
- ✅ **Smart timing** - Respect configured intervals
- ✅ **Last refresh tracking** - Don't over-refresh
- ✅ **Podcast-aware** - Handle audio feeds properly

---

## AI Features (V3.5)

### Article Extraction
- ✅ **Full-text extraction** - Get complete article text
- ✅ **Multiple methods** - newspaper3k + trafilatura fallback
- ✅ **Metadata extraction** - Authors, publish date, images
- ✅ **Caching** - Store extracted text in database
- ✅ **Background extraction** - Non-blocking operation

### AI Summarization
- ✅ **AI-powered summaries** - Claude (Anthropic) or OpenAI
- ✅ **TL;DR generation** - Ultra-quick 1-2 sentence summaries
- ✅ **Full summaries** - Comprehensive 200-word overviews
- ✅ **Key points extraction** - Bulleted list of main ideas
- ✅ **Smart caching** - Never re-process same article
- ✅ **Cost-effective** - ~$0.25 per 1,000 articles with Claude

### API Management
- ✅ **Multi-provider support** - Claude (recommended) or OpenAI
- ✅ **API key management** - Store keys securely
- ✅ **Environment variables** - Prefer env vars for security
- ✅ **Database fallback** - Optional key storage in DB
- ✅ **Easy configuration** - GUI dialog for setup

### AI Menu
- ✅ Extract Full Text - Get complete article content
- ✅ Generate Summary - Create comprehensive overview
- ✅ Generate TL;DR - Quick one-liner summary
- ✅ Configure API Keys - Set up Claude/OpenAI keys
- ✅ About AI Features - Learn about AI capabilities

---

## Technical Features

### Database
- ✅ **SQLite storage** - Reliable local database
- ✅ **Automatic migrations** - Upgrade schema seamlessly
- ✅ **Efficient indexing** - Fast article lookups
- ✅ **Foreign key constraints** - Data integrity
- ✅ **Connection pooling** - Optimized access

### Architecture
- ✅ **Modular design** - Separate concerns
- ✅ **Optional features** - Graceful degradation
- ✅ **Feature detection** - Check for dependencies
- ✅ **Error handling** - Comprehensive exception management
- ✅ **Thread safety** - Background operations don't block UI

### Optional Dependencies
- ✅ **pygame** - Audio playback (V3)
- ✅ **mutagen** - Audio metadata (V3)
- ✅ **anthropic** - Claude AI (V3.5)
- ✅ **openai** - OpenAI GPT (V3.5)
- ✅ **newspaper3k** - Article extraction (V3.5)
- ✅ **trafilatura** - Article extraction fallback (V3.5)
- ✅ **reportlab** - PDF export (V2)
- ✅ **plyer** - Desktop notifications (V2)

### Data Safety
- ✅ **Local-first** - All data stored locally
- ✅ **No tracking** - No analytics or telemetry
- ✅ **Privacy-focused** - API keys for AI only
- ✅ **OPML backup** - Easy data export
- ✅ **Database backup** - Single file to backup

---

## Dialogs & Windows

### Category Manager
- ✅ Add/remove categories
- ✅ View all categories
- ✅ Real-time updates

### Feed Settings
- ✅ Change feed category
- ✅ Set refresh interval
- ✅ View last refresh time

### Statistics Window
- ✅ Select time period (7/30/90 days)
- ✅ Total articles read
- ✅ Average per day
- ✅ Daily breakdown chart
- ✅ Unread and favorite counts

### Preferences
- ✅ Enable/disable notifications
- ✅ Test notifications
- ✅ View PDF export status
- ✅ See database location

### AI Configuration
- ✅ Set Claude API key
- ✅ Set OpenAI API key
- ✅ View setup instructions
- ✅ Links to get API keys

---

## File Structure

```
feedmind.py           # Main application (1,912 lines)
rss_core.py          # RSS/Atom parser
rss_database_v3.py   # Database layer with V3 features
rss_opml.py          # OPML import/export
rss_themes.py        # Light/dark themes
rss_notifications.py # Desktop notifications
rss_pdf_exporter.py  # PDF export

# V3 Podcast modules
rss_audio_player.py      # Audio playback engine
rss_audio_player_ui.py   # Player widget
rss_podcast_downloader.py # Episode downloads
rss_auto_refresh.py      # Smart scheduling

# V3.5 AI modules
rss_ai_summarizer.py     # AI summaries
rss_article_extractor.py # Full-text extraction
rss_api_config.py        # API key management
```

---

## Running FeedMind

### Basic Usage
```bash
python3 feedmind.py
```

### With Full Features
```bash
# Install all dependencies
pip install pygame mutagen anthropic newspaper3k reportlab plyer

# Set AI API key (recommended)
export RSS_API_KEY_CLAUDE="your-api-key"

# Run
python3 feedmind.py
```

### Minimal Installation
```bash
# Just core features (no podcast, no AI)
python3 feedmind.py
```

---

## Feature Comparison

| Feature | V1 | V2 | V3 | V3.5 |
|---------|----|----|----|----|
| RSS/Atom parsing | ✅ | ✅ | ✅ | ✅ |
| SQLite caching | ✅ | ✅ | ✅ | ✅ |
| Categories | ❌ | ✅ | ✅ | ✅ |
| Favorites | ❌ | ✅ | ✅ | ✅ |
| OPML import/export | ❌ | ✅ | ✅ | ✅ |
| Dark theme | ❌ | ✅ | ✅ | ✅ |
| Statistics | ❌ | ✅ | ✅ | ✅ |
| PDF export | ❌ | ✅ | ✅ | ✅ |
| Podcast support | ❌ | ❌ | ✅ | ✅ |
| Audio player | ❌ | ❌ | ✅ | ✅ |
| Episode downloads | ❌ | ❌ | ✅ | ✅ |
| AI summaries | ❌ | ❌ | ❌ | ✅ |
| Full-text extraction | ❌ | ❌ | ❌ | ✅ |

---

## Database Schema

**feedmind.db** includes:

- `feeds` - RSS feed metadata
- `articles` - Cached article content
- `categories` - Feed organization
- `settings` - App preferences
- `podcast_downloads` - Downloaded episodes (V3)
- AI columns in `articles`:
  - `full_text` - Extracted article text (V3.5)
  - `ai_summary` - AI-generated summary (V3.5)
  - `ai_tldr` - Quick TL;DR (V3.5)
  - `ai_key_points` - Main points JSON (V3.5)
  - `ai_generated_date` - When AI processed it (V3.5)

---

## Key Improvements in V3.5

1. **Consolidated Application** - Single `feedmind.py` file replaces `rss_reader_v2.py`
2. **Clean Branding** - "FeedMind" throughout, no more "RSSreader"
3. **Modern Database** - `feedmind.db` instead of `rss_reader_v3.db`
4. **Version Tracking** - `__version__ = "3.5.0"` constant
5. **Complete Documentation** - Enhanced docstrings
6. **Production Ready** - All features tested and integrated

---

## What's New in FeedMind v3.5

- 🧠 **AI-Powered** - Claude/OpenAI integration for smart summaries
- 📝 **Full-Text Extraction** - Get complete articles, not just RSS previews
- 🎙️ **Podcast Support** - Play and download podcast episodes
- ⚡ **Faster & Smarter** - Background operations, smart caching
- 🎨 **Polished UI** - Better themes, cleaner layout
- 🔐 **Privacy-Focused** - All data stays local, optional AI

---

## Migration from Previous Versions

**From rss_reader_v2.py:**
- Use `feedmind.py` instead
- Database automatically migrates to V3 schema
- All settings and articles preserved
- No data loss

**Database compatibility:**
- V1 DB → Auto-migrates to V2 → V3
- V2 DB → Auto-migrates to V3
- V3 DB → Already compatible

---

## Future Roadmap

Potential features for future versions:
- Mobile app (Kivy or Flutter)
- Web interface (PWA)
- Multi-device sync
- Browser extensions
- More AI providers
- Video podcast support
- Reading time estimates
- Offline mode improvements

---

**FeedMind v3.5.0 - Smart feeds. Smarter reading. 🧠**
