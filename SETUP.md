# FeedMind 🧠 Setup Guide

Complete setup guide for FeedMind - the AI-powered RSS reader with podcast support.

---

## What You'll Need

- A computer running Windows, Mac, or Linux
- About 10-15 minutes
- An internet connection
- Python 3.9 or higher

---

## Quick Start (Recommended Path)

### Step 1: Install Python

**Windows:**
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click "Download Python 3.11" (or latest version)
3. Run the installer
4. ⚠️ **IMPORTANT:** Check "Add Python to PATH"
5. Click "Install Now"

**Mac:**
1. Open Terminal (⌘ + Space, type "Terminal")
2. Check if Python is installed: `python3 --version`
3. If you see Python 3.9+, skip to Step 2
4. Otherwise, download from [python.org/downloads](https://www.python.org/downloads/)

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-tk

# Fedora
sudo dnf install python3 python3-pip python3-tkinter
```

### Step 2: Download FeedMind

**Option A: Download ZIP** (Easiest)
1. Go to the GitHub repository
2. Click green "Code" button → "Download ZIP"
3. Extract to your Documents or Desktop folder

**Option B: Use Git**
```bash
git clone https://github.com/paulhale70/Wildcat.git
cd Wildcat
```

### Step 3: Install Base Dependencies

Open Terminal/Command Prompt in the Wildcat folder:

**Windows:**
```bash
pip install -r requirements.txt
```

**Mac/Linux:**
```bash
pip3 install -r requirements.txt
```

### Step 4: Run FeedMind

**Windows:**
```bash
python feedmind.py
```

**Mac/Linux:**
```bash
python3 feedmind.py
```

FeedMind should open.

---

## Optional Features Setup

FeedMind has optional features you can enable. Install what you need:

### 🎙️ Podcast Support (V3)

Enable audio playback and podcast downloads:

```bash
# Windows
pip install pygame mutagen

# Mac/Linux
pip3 install pygame mutagen
```

**What this enables:**
- Built-in audio player
- Play podcast episodes in FeedMind
- Download episodes for offline listening
- Duration and metadata extraction

### 🤖 AI-Powered Summaries (V3.5)

Enable article summarization and extraction:

```bash
# Windows
pip install anthropic newspaper3k

# Mac/Linux
pip3 install anthropic newspaper3k
```

**What this enables:**
- TL;DR generation (1-2 sentence summaries)
- AI-powered article summaries
- Key points extraction
- Full-text article extraction from web pages

**You'll also need an API key:**
1. Get free Claude API key: [console.anthropic.com](https://console.anthropic.com/)
2. Set environment variable:

**Windows (PowerShell):**
```powershell
$env:RSS_API_KEY_CLAUDE="your-api-key-here"
```

**Mac/Linux:**
```bash
export RSS_API_KEY_CLAUDE="your-api-key-here"
```

Or set it permanently in your profile (~/.bashrc, ~/.zshrc, etc.)

**Cost:** ~$0.25 per 1,000 articles with Claude Haiku

### 📄 PDF Export & Notifications

Additional optional features:

```bash
# Already included in requirements.txt
pip install reportlab plyer
```

---

## Features

FeedMind includes all features in a single application (`feedmind.py`):

- RSS/Atom feed reading with categories and OPML import/export
- Dark mode, reading statistics, PDF export, desktop notifications
- Podcast support with built-in audio player and episode downloads
- Video podcast support (opens in system player)
- AI-powered article summarization (optional, requires API key)
- Article sorting, 7-day filter, feed bookmarks

---

## First Time Setup

### Adding Your First Feed

1. Look for the "RSS Feed URL" text box
2. Try one of these sample feeds:

**News:**
```
NASA Breaking News: https://www.nasa.gov/rss/dyn/breaking_news.rss
BBC News: http://feeds.bbci.co.uk/news/rss.xml
TechCrunch: https://techcrunch.com/feed/
Hacker News: https://news.ycombinator.com/rss
```

**Podcasts:**
```
NASA Podcast: https://www.nasa.gov/rss/dyn/Houston-We-Have-a-Podcast.rss
```

3. Paste the URL into the text box
4. Click "Add Feed" or press Enter
5. Wait a few seconds for articles to download
6. The feed appears in your list!

### Using Categories (V2+)

1. Click "Manage Categories" (Ctrl+M)
2. Create categories: "News", "Tech", "Podcasts", etc.
3. Right-click a feed → assign to category
4. Filter by category in the sidebar

### Importing from Another RSS Reader (V2+)

1. Export OPML from your current reader (usually in Settings)
2. In FeedMind, press Ctrl+I (Import OPML)
3. Select your OPML file
4. All feeds are imported with categories!

---

## Daily Usage

### Morning Routine

1. Open FeedMind
2. Click "Unread" to see new articles
3. Read summaries (if AI enabled)
4. Star important articles
5. Double-click to open in browser

### Listening to Podcasts (if enabled)

1. Subscribe to a podcast feed
2. FeedMind auto-detects episodes
3. Click an episode to see details
4. Click "Play" to listen in-app
5. Or "Download" for offline listening

### Using AI Features (if enabled)

1. Right-click an article
2. Select "Extract Full Text"
3. Select "Generate Summary"
4. View TL;DR and key points instantly

---

## Keyboard Shortcuts (V2+)

**Essential:**
- `Ctrl+T` - Toggle dark mode
- `Ctrl+R` - Refresh current feed
- `Ctrl+Shift+R` - Refresh all feeds
- `Ctrl+M` - Manage categories
- `Ctrl+I` - Import OPML
- `Ctrl+E` - Export OPML
- `Ctrl+S` - View statistics
- `Ctrl+P` - Export to PDF (if installed)

**Navigation:**
- `Enter` - Add feed (when in URL box)
- `Enter` - Search (when in search box)
- `Double-click` - Open article in browser

---

## Troubleshooting

### "python is not recognized" (Windows)

**Fix:**
1. Uninstall Python
2. Reinstall and check "Add Python to PATH"
3. Restart Command Prompt

### "No module named 'tkinter'" (Linux)

**Fix:**
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

### "pygame not available" for podcasts

**Fix:**
```bash
pip install pygame mutagen
```

### AI features not working

**Check:**
1. Libraries installed: `pip list | grep anthropic`
2. API key set: `echo $RSS_API_KEY_CLAUDE`
3. Internet connection working
4. API key has credits

### Application crashes or blank window

**Fix:**
1. Close FeedMind
2. Delete database file: `feedmind.db`
3. Restart FeedMind
4. Re-add feeds

### Failed to add feed

**Check:**
1. Internet connection
2. URL starts with http:// or https://
3. Try a different feed to test
4. Some sites block automated access

---

## Testing Your Installation

### Test Base Installation
```bash
python feedmind.py
```
Should open without errors.

### Run Tests
```bash
python -m pytest tests/
```

---

## Configuration Tips

### Store API Key Permanently

**Windows:**
1. Search "Environment Variables"
2. Click "Environment Variables" button
3. Add new user variable:
   - Name: `RSS_API_KEY_CLAUDE`
   - Value: your API key
4. Restart terminal

**Mac/Linux:**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export RSS_API_KEY_CLAUDE="your-api-key-here"
```

Then run: `source ~/.bashrc`

### Enable Auto-Refresh (V3)

In V2, enable auto-refresh checkbox for background updates every 15 minutes.

### Change Theme (V2)

Press `Ctrl+T` to toggle between light and dark mode.

---

## Advanced Setup

### Using Alternative AI Providers

FeedMind supports both Claude and OpenAI:

**For OpenAI:**
```bash
pip install openai
export RSS_API_KEY_OPENAI="your-openai-key"
```

**In code:**
```python
from rss_ai_summarizer import AISummarizer, AIProvider
summarizer = AISummarizer(provider=AIProvider.OPENAI)
```

### Using Alternative Extraction Library

For lightweight extraction, use trafilatura instead of newspaper3k:

```bash
pip install trafilatura
```

### Custom Database Location

```bash
# Set environment variable
export RSS_DATABASE_PATH="/path/to/custom/feedmind.db"
```

---

## File Locations

**Database:** `feedmind.db` (SQLite, auto-created on first run)

**Downloaded Podcasts:** `podcast_downloads/` folder

**Configuration:** Stored in database settings table; API keys via environment variables

---

## Updating FeedMind

When new version is released:

1. Download new files
2. Keep your database file (`.db`)
3. Run new version
4. Database auto-migrates!

**Your data is preserved:**
- All feeds
- All articles
- All categories
- All settings
- Reading history
- Downloaded podcasts

---

## Getting Help

**Documentation:**
- [Main README](README.md) - Overview and quick start
- [Podcast Guide](docs/RSS_V3_FEATURES.md) - Audio features
- [AI Features Guide](docs/RSS_AI_FEATURES.md) - Summarization & extraction

**Testing:**
- Run test scripts to verify functionality
- Check error messages for clues
- Try with sample feeds first

**Common Resources:**
- Claude API: https://console.anthropic.com/
- OpenAI API: https://platform.openai.com/
- Python Help: https://www.python.org/about/help/

---

## Privacy & Security

✅ **Your data stays local**
- All feeds and articles in local SQLite database
- No cloud sync (unless you enable it)
- No tracking or telemetry

✅ **API keys are secure**
- Environment variables (recommended)
- Never logged or shared
- Only sent to chosen AI provider

✅ **Network usage**
- Only fetches feeds you subscribe to
- AI only when you explicitly use it
- No background tracking

---

## Summary Checklist

Installation:
- [ ] Python 3.9+ installed
- [ ] FeedMind downloaded
- [ ] Base dependencies installed (`pip install -r requirements.txt`)
- [ ] FeedMind runs successfully (`python feedmind.py`)

Optional Features:
- [ ] Podcast support installed (`pip install pygame mutagen`)
- [ ] AI features installed (`pip install anthropic newspaper3k`)
- [ ] API key configured (for AI features)

First Steps:
- [ ] Added first RSS feed
- [ ] Created categories
- [ ] Enabled dark mode (Ctrl+T)
- [ ] Imported OPML (if migrating)

You're ready! 🎉

---

**Made with 🧠 by the FeedMind community**

*Smart feeds. Smarter reading.*
