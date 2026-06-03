# FeedMind

**AI-Powered RSS Reader with Podcast & Video Support**

FeedMind is an intelligent RSS/Atom feed reader that goes beyond simple aggregation. It uses AI to help you understand content faster, supports audio and video podcast playback, and keeps you organized with smart features.

## ✨ What Makes FeedMind Special?

Most RSS readers just show you articles. **FeedMind helps you understand them.**

- 🤖 **AI Summaries** - Get TL;DR and key points for any article
- 🎙️ **Podcast Player** - Play audio episodes directly in the app
- 🎬 **Video Support** - Watch video podcasts with system player
- 📄 **Full-Text Extraction** - Fetch complete articles, not just snippets
- 🔄 **Smart Sorting** - Sort by date, title, or feed name
- 📌 **Feed Bookmarks** - Pin your favorite feeds for quick access
- ⏱️ **7-Day Filter** - Focus on recent content
- 📁 **Categories & OPML** - Import from any RSS reader
- 🌙 **Dark Mode** - Easy on the eyes

---

## 🚀 Quick Start

### Installation

```bash
# No pip installs required — just run it!
python feedmind.py

# Or install optional features as needed:
pip install reportlab          # PDF export
pip install plyer              # Desktop notifications
pip install anthropic          # AI summaries (Claude)
pip install newspaper3k        # Full-text extraction
```

### Optional AI Features

```bash
# Set your Claude API key
export RSS_API_KEY_CLAUDE="your-api-key"
```

### Sample Feeds to Try

```
NASA Breaking News: https://www.nasa.gov/rss/dyn/breaking_news.rss
TechCrunch: https://techcrunch.com/feed/
NASA Podcast: https://www.nasa.gov/rss/dyn/Houston-We-Have-a-Podcast.rss
Hacker News: https://news.ycombinator.com/rss
BBC News: http://feeds.bbci.co.uk/news/rss.xml
```

---

## 📦 FeedMind v3.8 - Complete Feature Set

**Main Application:** `feedmind.py` (All features in one file!)

### Core Features (V1)
- ✓ RSS/Atom feed parsing
- ✓ Article caching & offline reading
- ✓ Read/unread tracking
- ✓ Favorites & search
- ✓ Auto-refresh

### Organization & UI (V2)
- ✓ **Categories & folders**
- ✓ **OPML import/export**
- ✓ **Dark mode** with themes
- ✓ **Reading statistics**
- ✓ **PDF export**
- ✓ **Desktop notifications**
- ✓ **Keyboard shortcuts** (Ctrl+T, Ctrl+S, j/k navigation, etc.)

### Podcast Features (V3)
- ✓ **Auto-detect podcast feeds**
- ✓ **Built-in audio player** with controls
- ✓ **Download episodes** for offline listening
- ✓ **Smart auto-refresh** based on feed activity
- ✓ **Background updates**
- ✓ **Playback speed control** (0.5x to 2.0x)

### AI Features (V3.5)
- ✓ **AI-powered summaries** (Claude/OpenAI)
- ✓ **TL;DR generation** (1-2 sentence summaries)
- ✓ **Key points extraction** (bulleted highlights)
- ✓ **Full-text article extraction** (complete articles)
- ✓ **Smart caching** (never re-process articles)

### Video & Organization Features (V3.6-V3.7)
- ✓ **Video podcast support** (v3.6) - MP4, MKV, AVI, MOV, WebM
- ✓ **Podcast downloads location** (v3.6) - Easy file access
- ✓ **Article sorting** (v3.7) - Sort by date, title, or feed name
- ✓ **7-day article filter** (v3.7) - Focus on recent content
- ✓ **Feed bookmarks** (v3.7) - Pin important feeds with 📌 icon

---

## 🧠 AI Features Deep Dive

### What Can FeedMind's AI Do?

1. **TL;DR** - Ultra-quick 1-2 sentence summary
   ```
   "AI research shows significant progress in language models.
   New techniques improve efficiency while maintaining quality."
   ```

2. **Smart Summary** - Comprehensive overview (200 words)
   ```
   Detailed paragraph covering main points, context,
   and key insights from the article...
   ```

3. **Key Points** - Bulleted main takeaways
   ```
   • Language models now 10x more efficient
   • New training technique reduces compute costs
   • Open-source community driving innovation
   ```

### Cost-Effective

- Uses **Claude Haiku** (recommended) or **GPT-3.5-turbo**
- Only **~$0.25 per 1,000 articles** with Claude
- Full-text extraction is **completely FREE**
- Summaries are cached - never re-process

### Get Started with AI

```python
from rss_ai_summarizer import AISummarizer, AIProvider

# Initialize with your API key
summarizer = AISummarizer(
    provider=AIProvider.CLAUDE,
    api_key="your-key"
)

# Get comprehensive summary
result = summarizer.summarize_article(article_text)
print(f"TL;DR: {result['tldr']}")
```

**Get API Keys:**
- Claude: https://console.anthropic.com/ (recommended)
- OpenAI: https://platform.openai.com/api-keys

---

## 🎙️ Podcast Features

### First-Class Podcast Support

Unlike other RSS readers, FeedMind treats podcasts seriously:

- **Auto-Detection** - Identifies podcast feeds instantly
- **Episode Metadata** - Duration, file size, show notes
- **Download Manager** - Save episodes for offline listening
- **Built-in Player** - Play directly in FeedMind
- **Progress Tracking** - Resume where you left off

### Try a Podcast Feed

```
NASA Houston We Have a Podcast:
https://www.nasa.gov/rss/dyn/Houston-We-Have-a-Podcast.rss
```

The player will appear automatically when you select a podcast episode!

---

## Documentation

- **[Setup Guide](SETUP.md)** - Installation and configuration
- **[Changelog](CHANGELOG.md)** - Release history
- **[Podcast Guide](docs/RSS_V3_FEATURES.md)** - Audio player, downloads, auto-refresh
- **[AI Features Guide](docs/RSS_AI_FEATURES.md)** - Summarization, extraction, API setup
- **[Build Guide](docs/WINDOWS_EXE_BUILD_GUIDE.md)** - Windows .exe packaging

---

## 🛠️ Technology Stack

**Core (zero pip installs needed):**
- Python 3.9+ / SQLite / Tkinter
- Windows MCI audio backend (built-in, no installs)

**All optional — install only what you need:**
- reportlab (PDF export)
- plyer (desktop notifications)
- anthropic / openai (AI summaries)
- newspaper3k / trafilatura (full-text extraction)
- pygame-ce (audio on macOS/Linux — Windows uses MCI automatically)

---

## 🎯 Use Cases

### 📰 News Junkies
- Subscribe to dozens of news sources
- Get TL;DR for breaking news
- Organize by topic (Tech, Politics, Sports)
- Export important articles to PDF

### 🎓 Researchers
- Extract full-text for offline reading
- AI summaries of academic articles
- Key points extraction for lit reviews
- PDF export for archival

### 🎙️ Podcast Fans
- All your shows in one place
- Download episodes for commutes
- No app switching needed
- Smart refresh keeps shows updated

### 💼 Professionals
- Stay current in your industry
- Quick TL;DR saves reading time
- Categories for different projects
- Reading stats track your habits

---

## Privacy & Security

**Your Data, Your Machine**
- All data stored in local SQLite database
- No cloud sync or tracking
- API keys only used for AI features
- Environment variable support for security

**Network Usage**
- Only fetches feeds you subscribe to
- AI only when you explicitly request it
- No telemetry or analytics

---

## Roadmap

### Planned Features
- [ ] Mobile companion app
- [ ] Cloud sync (optional)
- [ ] Local AI models (no API costs)
- [ ] Browser extension
- [ ] Email digest feature

---

## 🤝 Contributing

FeedMind is open for contributions!

1. **Report Bugs** - Open an issue
2. **Suggest Features** - Share your ideas
3. **Submit PRs** - Code contributions welcome
4. **Improve Docs** - Help others
5. **Share Feedback** - Tell us what works

---

## 📝 License

MIT License - see LICENSE file for details

---

**Made with 🧠 by the FeedMind community**

*Smart feeds. Smarter reading.*

