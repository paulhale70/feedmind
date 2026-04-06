# RSSreaderV3 - New Features

## Overview

Version 3 adds **Podcast & Audio Support** and **Scheduled Auto-Refresh** to the RSS reader, building on all the V2 features.

## New V3 Features

### 1. Podcast & Audio Support

**Audio Enclosure Detection**
- Automatically detects podcast episodes in RSS feeds
- Extracts audio URLs, file sizes, and duration information
- Supports both RSS and Atom podcast formats
- Reads iTunes podcast metadata (duration, etc.)

**Audio Playback**
- Built-in audio player with playback controls
- Play, pause, and stop controls
- Volume adjustment
- Position tracking and progress display
- Speed control (requires alternative to pygame)

**Episode Downloads**
- Download podcast episodes for offline listening
- Progress tracking during downloads
- Automatic filename generation and sanitization
- Storage usage monitoring
- Episode management (download/delete)

**Database Enhancements**
- New `podcast_downloads` table to track downloaded episodes
- Article columns: `audio_url`, `audio_type`, `audio_length`, `duration_seconds`
- Feed columns: `is_podcast` flag
- Auto-detection and marking of podcast feeds

### 2. Scheduled Feed Updates

**Auto-Refresh Scheduler**
- Automatic background refresh at configurable intervals
- Per-feed refresh interval settings
- System runs while app is open
- Respects feed-specific update frequencies

**Smart Scheduling**
- Adapts refresh intervals based on feed activity
- Frequent updaters get checked more often
- Infrequent feeds get checked less often
- Learns from update patterns over time

**Feed-Level Control**
- Enable/disable auto-refresh per feed
- Custom refresh intervals (15 min to 2 hours)
- View next scheduled refresh time
- Manual refresh still available anytime

## Technical Implementation

### Core Modules

#### rss_audio_player.py
- `AudioPlayer` class for playback control
- Uses pygame for cross-platform audio support
- Position tracking and callbacks
- Volume and speed control (limited by pygame)

#### rss_podcast_downloader.py
- `PodcastDownloader` class for episode downloads
- Background download with progress callbacks
- Automatic file management
- Storage usage tracking

#### rss_auto_refresh.py
- `AutoRefreshScheduler` for basic scheduling
- `SmartRefreshScheduler` for adaptive intervals
- Background worker thread
- Configurable refresh logic

#### rss_database_v3.py
- Extends V2 database with podcast support
- New tables and columns for audio metadata
- Podcast episode queries and management
- Auto-refresh feed queries

#### rss_core.py (Enhanced)
- Updated `RSSFeed` class with audio properties
- Enclosure extraction in RSS parser
- iTunes namespace support for duration
- Duration parsing (HH:MM:SS format)

#### rss_audio_player_ui.py
- Tkinter widget for audio playback UI
- Embedded player controls
- Progress bar and time display
- Volume and speed controls

### Database Schema Changes

**New Table: podcast_downloads**
```sql
CREATE TABLE podcast_downloads (
    id INTEGER PRIMARY KEY,
    article_id INTEGER,
    audio_url TEXT,
    local_path TEXT,
    download_date TEXT,
    file_size INTEGER,
    duration_seconds INTEGER,
    download_status TEXT
)
```

**Articles Table - New Columns**
- `audio_url` - URL of audio file
- `audio_type` - MIME type (audio/mpeg, etc.)
- `audio_length` - File size in bytes
- `duration_seconds` - Duration in seconds

**Feeds Table - New Columns**
- `is_podcast` - Boolean flag
- `auto_refresh_enabled` - Enable auto-refresh

## Installation

### Required Dependencies (Already in V2)
```bash
pip install streamlit pandas sqlalchemy
```

### V3 New Dependencies

**For Podcast Support:**
```bash
pip install pygame
pip install mutagen  # Optional, for accurate duration info
```

**All V2 Optional Dependencies Still Supported:**
```bash
pip install reportlab  # PDF export
pip install plyer      # Desktop notifications
```

### Quick Install All
```bash
pip install -r requirements.txt
```

## Usage Examples

### Testing V3 Features
```bash
python test_v3_features.py
```

This runs comprehensive tests for:
- V3 database schema
- Podcast detection in feeds
- Audio player functionality
- Download system
- Auto-refresh scheduling
- Integration testing

### Using V3 Database Directly

```python
from rss_database_v3 import RSSDatabase

# Create V3 database
db = RSSDatabase("my_rss.db")

# Add a podcast feed
db.add_feed("https://example.com/podcast.rss", "My Podcast")

# Enable auto-refresh
db.set_feed_auto_refresh("https://example.com/podcast.rss", True)

# Get podcast episodes
episodes = db.get_podcast_episodes(limit=10)

# Record a download
db.add_podcast_download(
    article_id=1,
    audio_url="https://example.com/episode.mp3",
    local_path="/downloads/episode.mp3",
    file_size=50000000,
    duration_seconds=3600
)
```

### Using Audio Player

```python
from rss_audio_player import AudioPlayer

player = AudioPlayer()

# Check if available
if player.is_available():
    # Load and play
    player.load("episode.mp3")
    player.play()

    # Control playback
    player.pause()
    player.set_volume(0.8)  # 80%

    # Clean up
    player.cleanup()
```

### Using Auto-Refresh Scheduler

```python
from rss_auto_refresh import SmartRefreshScheduler

def refresh_feed(feed_url):
    print(f"Refreshing {feed_url}")
    # Your refresh logic here

# Create and start scheduler
scheduler = SmartRefreshScheduler(default_interval_minutes=30)
scheduler.start(refresh_feed)

# Stop when done
scheduler.stop()
```

### Using Podcast Downloader

```python
from rss_podcast_downloader import PodcastDownloader

downloader = PodcastDownloader("podcast_downloads")

def on_progress(downloaded, total):
    percent = (downloaded / total) * 100 if total > 0 else 0
    print(f"Progress: {percent:.1f}%")

def on_complete(success, file_path, error):
    if success:
        print(f"Downloaded to: {file_path}")
    else:
        print(f"Failed: {error}")

# Start download
downloader.download(
    "https://example.com/episode.mp3",
    progress_callback=on_progress,
    completion_callback=on_complete
)
```

## Integration with Main App

To integrate V3 features into the main RSS reader app (rss_reader_v2.py), you would need to:

1. **Replace database import:**
   ```python
   from rss_database_v3 import RSSDatabase  # Instead of v2
   ```

2. **Add audio player widget:**
   ```python
   from rss_audio_player_ui import AudioPlayerWidget

   # In UI creation:
   self.audio_player = AudioPlayerWidget(self.root)
   self.audio_player.pack(...)
   ```

3. **Add podcast panel:**
   - New tab or section for podcast episodes
   - List view of episodes with audio indicator
   - Download buttons for each episode
   - Play buttons for downloaded episodes

4. **Add auto-refresh:**
   ```python
   from rss_auto_refresh import SmartRefreshScheduler

   # In initialization:
   self.scheduler = SmartRefreshScheduler()
   self.scheduler.start(self._refresh_feed_callback)
   ```

5. **Update article display:**
   - Show audio icon for podcast episodes
   - Display duration information
   - Add download/play buttons

6. **Update feed management:**
   - Show podcast indicator on feeds
   - Auto-refresh toggle per feed
   - Display next refresh time

## Feature Comparison

| Feature | V1 | V2 | V3 |
|---------|----|----|-----|
| Basic RSS/Atom parsing | ✓ | ✓ | ✓ |
| Feed management | ✓ | ✓ | ✓ |
| Article caching | ✓ | ✓ | ✓ |
| Categories/folders | - | ✓ | ✓ |
| OPML import/export | - | ✓ | ✓ |
| Dark mode | - | ✓ | ✓ |
| Reading statistics | - | ✓ | ✓ |
| PDF export | - | ✓ | ✓ |
| Desktop notifications | - | ✓ | ✓ |
| Smart refresh intervals | - | ✓ | ✓ |
| **Podcast detection** | - | - | **✓** |
| **Audio playback** | - | - | **✓** |
| **Episode downloads** | - | - | **✓** |
| **Auto-refresh scheduler** | - | - | **✓** |

## Known Limitations

### Audio Playback
- pygame doesn't support variable playback speed natively
- Seeking is limited (requires stop/restart)
- For better features, consider alternative libraries:
  - pydub + sounddevice for speed control
  - python-vlc for full media player features

### Auto-Refresh
- Only runs while app is open
- No background service when app is closed
- For always-on refresh, consider system scheduler (cron/Task Scheduler)

### File Formats
- Best support for MP3 files
- Other formats depend on pygame/system codecs

## Future Enhancements (V4 Ideas)

- Video podcast support
- Playlist management
- Cloud sync for subscriptions
- Mobile companion app
- Background refresh service
- Advanced audio features (equalizer, bookmarks)
- Podcast search and discovery
- Chapter markers support
- Transcription integration

## License & Credits

Same as RSS Reader V2 - see main project README.

## Support

For issues or questions about V3 features:
1. Run `python test_v3_features.py` to verify setup
2. Check that pygame and mutagen are installed
3. Review error messages for missing dependencies
4. Ensure audio files are in supported formats
