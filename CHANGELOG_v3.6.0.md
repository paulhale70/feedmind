# FeedMind v3.6.0 - Release Notes

**Release Date:** 2026-02-03
**Version:** 3.6.0

---

## 🎬 New Features

### Video Playback Support

FeedMind now supports **video podcasts**! The app automatically detects video files and provides a dedicated video player interface.

**Features:**
- ✅ Automatic detection of video vs audio files
- ✅ Support for common video formats:
  - MP4, M4V, MKV
  - AVI, MOV, WMV
  - FLV, WebM, MPG/MPEG
  - 3GP, OGV
- ✅ Opens videos in your system's default video player
- ✅ Shows video metadata (format, file size)
- ✅ Quick access to video file location
- ✅ Seamless integration with existing podcast system

**How it works:**
1. Download a video podcast episode
2. FeedMind automatically detects it's a video
3. Video player widget appears instead of audio player
4. Click "Play Video" to watch in your default player
5. Use "Show File" to open the folder containing the video

### Podcast Downloads Location

New menu option to quickly access your downloaded podcast files!

**Features:**
- ✅ File → "📁 Open Podcast Downloads" menu option
- ✅ Opens the `podcast_downloads` folder in your file explorer
- ✅ Cross-platform support (Windows, macOS, Linux)
- ✅ Creates folder automatically if it doesn't exist
- ✅ Fallback dialog shows path if folder opening fails

**Location:**
- Default: `podcast_downloads/` in the same folder as FeedMind
- Access via: File → Open Podcast Downloads
- Or manually navigate to the application directory

---

## 📋 What's Changed

### Updated

- **Version:** 3.5.0 → 3.6.0
- **Description:** Added "Podcast & Video Support" to tagline
- **About Dialog:** Now shows video support status
- **Help Menu:** Added "Video Support ✓" indicator

### Added Files

- `rss_video_player_ui.py` - New video player widget module

### Modified Files

- `feedmind.py` - Core application with video support
  - Added VIDEO_SUPPORT flag
  - Video player widget initialization
  - Auto-detection of video files
  - Podcast downloads folder opener
  - Updated version and feature descriptions

---

## 🔧 Technical Details

### Video Player Architecture

```
VideoPlayerWidget (rss_video_player_ui.py)
    ↓
System Default Video Player
    (VLC, Windows Media Player, QuickTime, etc.)
```

**Why system player?**
- ✅ Maximum compatibility
- ✅ No additional dependencies
- ✅ Lightweight
- ✅ Users already have configured video players
- ✅ Supports all codecs user's player supports

### Video Detection

```python
def is_video_file(filename: str) -> bool:
    """Check if file is a video based on extension."""
    video_extensions = {
        '.mp4', '.m4v', '.mkv', '.avi', '.mov', '.wmv',
        '.flv', '.webm', '.mpg', '.mpeg', '.3gp', '.ogv'
    }
    return os.path.splitext(filename)[1].lower() in video_extensions
```

### Cross-Platform Folder Opening

```python
system = platform.system()

if system == 'Windows':
    os.startfile(path)
elif system == 'Darwin':  # macOS
    subprocess.run(['open', path])
else:  # Linux
    subprocess.run(['xdg-open', path])
```

---

## 🚀 Upgrade Instructions

### From v3.5.0 to v3.6.0

**No database changes required!** Simply update the files.

1. **Backup your data:**
   ```bash
   cp feedmind.db feedmind.db.backup
   ```

2. **Update files:**
   ```bash
   git pull origin claude/rss-reader-app-nlqJe
   ```

3. **New file to include:**
   - `rss_video_player_ui.py`

4. **Run FeedMind:**
   ```bash
   python feedmind.py
   ```

5. **Check video support:**
   - Help → Video Support ✓ should appear
   - Download a video podcast to test

### Rebuilding Windows .exe

If you're distributing as .exe:

```bash
pyinstaller feedmind.spec
```

The spec file automatically includes `rss_video_player_ui.py`.

---

## 📱 Video Podcast Sources

Looking for video podcasts to test? Try these:

**News & Tech:**
- TED Talks Video: https://feeds.feedburner.com/TEDTalks_video
- CNET Video: https://www.cnet.com/rss/news/
- The Verge Video: https://www.theverge.com/rss/index.xml

**YouTube Channels (via RSS):**
- Format: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`
- Note: Downloads may require yt-dlp or similar tools

**Educational:**
- Khan Academy: https://www.khanacademy.org/
- Coursera: Various course RSS feeds

---

## 🐛 Bug Fixes

None in this release - this is a pure feature addition.

---

## 🔮 Future Plans

**Potential v3.7 features:**
- Embedded video player (optional)
- Video thumbnails
- Playback speed control for videos
- Picture-in-picture mode
- Video download queue management
- Subtitle support

**Long-term (v4.0):**
- YouTube integration
- Video transcription
- AI video summaries
- Video bookmarks/chapters

---

## 💬 Feedback

Found a bug or have a feature request?

- GitHub Issues: https://github.com/paulhale70/Wildcat/issues
- Feature requests welcome!

---

## 🙏 Compatibility

**Tested on:**
- ✅ Windows 10/11
- ✅ macOS 12+
- ✅ Ubuntu 22.04 LTS

**Requirements:**
- Python 3.8+
- System video player (VLC, Windows Media Player, etc.)
- All dependencies from v3.5.0

**Optional:**
- yt-dlp for YouTube video downloads

---

## 📦 Distribution

### Python (Source)

Run directly:
```bash
python feedmind.py
```

### Windows Executable

Build with:
```bash
pyinstaller feedmind.spec
```

Output: `dist/FeedMind.exe` (~45-65MB)

---

## 📄 License

Same as FeedMind v3.5.0

---

## 🎉 Summary

FeedMind v3.6.0 adds comprehensive video support, making it a complete multimedia RSS reader. Now you can enjoy both audio and video podcasts in one application, with easy access to your downloaded media files.

**Total Features:**
- ✅ RSS/Atom feeds
- ✅ Audio podcasts
- ✅ **Video podcasts** (NEW)
- ✅ AI summaries
- ✅ Categories & OPML
- ✅ Dark mode
- ✅ PDF export
- ✅ Reading stats
- ✅ **Podcast location** (NEW)

Happy watching! 🎬

---

**Version:** 3.6.0
**Previous Version:** 3.5.0
**Release Date:** 2026-02-03
