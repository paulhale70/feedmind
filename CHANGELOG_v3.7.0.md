# FeedMind v3.7.0 - Release Notes

**Release Date:** 2026-02-16
**Version:** 3.7.0

---

## 🎯 New Features

### Article Sorting

FeedMind now allows you to sort articles in multiple ways for better organization!

**Features:**
- ✅ Sort by Date (Newest First) - Default
- ✅ Sort by Date (Oldest First)
- ✅ Sort by Title (A-Z)
- ✅ Sort by Title (Z-A)
- ✅ Sort by Feed Name
- ✅ Easy-to-use dropdown next to search bar
- ✅ Sorting preserved across view changes

**How it works:**
1. Look for the "Sort:" dropdown below the search bar
2. Select your preferred sort option
3. Articles immediately re-sort
4. Your selection applies to all views (All, Unread, Favorites)

**Use Cases:**
- **Date (Newest)** - See latest news first (default)
- **Date (Oldest)** - Catch up chronologically
- **Title (A-Z)** - Find specific articles alphabetically
- **By Feed** - Group articles by their source

### 7-Day Article Filter

Reduce clutter by showing only recent articles from the last 7 days!

**Features:**
- ✅ "Last 7 Days Only" checkbox below search bar
- ✅ Filters out articles older than 7 days
- ✅ Works with all views and sorts
- ✅ Toggle on/off with one click
- ✅ Helps focus on current news

**How it works:**
1. Check the "Last 7 Days Only" checkbox
2. Only articles from the last 7 days will display
3. Uncheck to see all articles again
4. Combines with sorting and search filters

**Benefits:**
- Keep your article list clean and manageable
- Focus on current events and recent content
- Reduce information overload
- Perfect for daily news consumption

### Feed Bookmarks

Mark your favorite feeds with bookmarks for quick access!

**Features:**
- ✅ Bookmark/unbookmark any feed
- ✅ 📌 Pin icon shows on bookmarked feeds
- ✅ Bookmarked feeds appear at top of feed list
- ✅ Keyboard shortcut: Press **B** to toggle bookmark
- ✅ Button in left panel: "📌 Bookmark Feed"
- ✅ Menu option: Manage → 📌 Bookmark Feed
- ✅ Visual feedback when bookmarking

**How it works:**
1. Select a feed from the feed list
2. Press **B** key, or click "📌 Bookmark Feed" button, or use Manage menu
3. Feed is bookmarked and shows 📌 pin icon
4. Bookmarked feeds automatically sort to the top
5. Press **B** again to unbookmark

**Use Cases:**
- Mark your most important news sources
- Quick access to frequently checked feeds
- Organize feeds by priority
- Distinguish must-read feeds from optional ones

---

## 📋 What's Changed

### Updated

- **Version:** 3.6.0 → 3.7.0
- **UI:** Added sort dropdown and 7-day filter checkbox
- **Database:** Added `is_bookmarked` column to feeds table
- **Keyboard Shortcuts:** Added **B** key for bookmarking feeds

### Added Files

- `CHANGELOG_v3.7.0.md` - This release notes file

### Modified Files

- `feedmind.py` - Core application with sorting, filtering, and bookmarks
  - Added sort controls and 7-day filter UI
  - Added sorting logic for articles (5 sort modes)
  - Added 7-day date filtering
  - Added bookmark toggle methods
  - Updated feed list to show bookmark indicators
  - New keyboard shortcut: B for bookmark
  - Updated version to 3.7.0

- `rss_database_v3.py` - Database with bookmark support
  - Added `is_bookmarked` column to feeds table
  - Added `bookmark_feed()` method
  - Added `is_feed_bookmarked()` method
  - Added `get_bookmarked_feeds()` method

---

## 🔧 Technical Details

### Article Sorting Implementation

```python
# V3.7: Apply sorting
if self.sort_order == "date_new":
    articles.sort(key=lambda a: a.get('published', ''), reverse=True)
elif self.sort_order == "date_old":
    articles.sort(key=lambda a: a.get('published', ''))
elif self.sort_order == "title_az":
    articles.sort(key=lambda a: a.get('title', '').lower())
elif self.sort_order == "title_za":
    articles.sort(key=lambda a: a.get('title', '').lower(), reverse=True)
elif self.sort_order == "feed":
    articles.sort(key=lambda a: a.get('feed_url', ''))
```

### 7-Day Filter Implementation

```python
# V3.7: Apply 7-day filter if enabled
if self.show_7days_only:
    from datetime import datetime, timedelta
    cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    articles = [a for a in articles
               if a.get('published', '') and a['published'][:10] >= cutoff_date]
```

### Feed Bookmark Database Schema

```sql
-- V3.7: Add bookmark column to feeds table
ALTER TABLE feeds ADD COLUMN is_bookmarked INTEGER DEFAULT 0;
```

**Database Methods:**
```python
def bookmark_feed(feed_url: str, is_bookmarked: bool = True)
def is_feed_bookmarked(feed_url: str) -> bool
def get_bookmarked_feeds() -> List[Dict]
```

### UI Controls

**Sort Dropdown Values:**
- "Date (Newest First)"
- "Date (Oldest First)"
- "Title (A-Z)"
- "Title (Z-A)"
- "By Feed Name"

**Feed List Display:**
```python
# V3.7: Sort bookmarked feeds first
feeds.sort(key=lambda f: (not f.get('is_bookmarked', 0), f['title']))

# Add bookmark indicator
bookmark_marker = "📌 " if feed.get('is_bookmarked', 0) else ""
display = f"{bookmark_marker}{feed['title']}"
```

---

## 🚀 Upgrade Instructions

### From v3.6.0 to v3.7.0

**No database changes required!** The app automatically adds the new column.

1. **Backup your data:**
   ```bash
   cp feedmind.db feedmind.db.backup
   ```

2. **Update files:**
   ```bash
   git pull origin claude/rss-reader-app-nlqJe
   ```

3. **No new dependencies** - Uses existing Python libraries

4. **Run FeedMind:**
   ```bash
   python feedmind.py
   ```

5. **Database auto-migration:**
   - On first run, `is_bookmarked` column is automatically added
   - All existing feeds default to unbookmarked
   - No manual migration needed

### Rebuilding Windows .exe

If you're distributing as .exe:

```bash
pyinstaller feedmind.spec
```

The spec file doesn't need updates for v3.7.0 changes.

---

## 🎮 Keyboard Shortcuts

### New in v3.7.0

- **B** - Bookmark/unbookmark selected feed

### All Shortcuts

- **R** - Toggle read/unread on selected article
- **F** - Toggle favorite on selected article
- **B** - Toggle bookmark on selected feed (NEW)
- **1** - Show all articles
- **2** - Show unread articles
- **3** - Show favorite articles
- **Ctrl+R** - Refresh selected feed
- **Ctrl+Shift+R** - Refresh all feeds
- **Ctrl+F** - Focus search box
- **Ctrl+T** - Toggle dark/light mode
- **Ctrl+S** - Show statistics
- **Space** - Scroll article down
- **Shift+Space** - Scroll article up

---

## 💡 Usage Tips

### Efficient Workflow with New Features

**Daily News Routine:**
1. Enable "Last 7 Days Only" filter
2. Sort by "Date (Newest First)"
3. Check bookmarked feeds first (📌 at top)
4. Read articles from most important sources

**Catching Up After Vacation:**
1. Disable 7-day filter (see all articles)
2. Sort by "Date (Oldest First)"
3. Focus on bookmarked feeds
4. Mark all read when done

**Finding Specific Content:**
1. Use search box to find keywords
2. Sort by "Title (A-Z)" for alphabetical browsing
3. Or sort by "By Feed" to group by source

**Organizing Feeds:**
1. Press **B** on must-read feeds to bookmark them
2. Bookmarked feeds auto-sort to top of list
3. Easy to spot with 📌 icon
4. Unbookmark with **B** when priorities change

---

## 🐛 Bug Fixes

None in this release - pure feature addition.

---

## 🔮 Future Plans

**Potential v3.8 features:**
- Custom date range filter (e.g., last 30 days, last year)
- Save sort preferences per feed
- Filter by bookmarked feeds only
- Multiple bookmark categories (Work, Personal, etc.)
- Sort by unread count
- Sort by feed popularity

**Long-term (v4.0):**
- Feed groups/folders
- Smart feed recommendations
- Reading time estimates
- Article read history timeline

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
- All dependencies from v3.6.0

**No new dependencies added in v3.7.0**

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

Same as FeedMind v3.6.0

---

## 🎉 Summary

FeedMind v3.7.0 adds powerful organization features that make managing large numbers of feeds and articles much easier. With flexible sorting, time-based filtering, and feed bookmarks, you can now customize your reading experience to match your workflow.

**Key Improvements:**
- ⚡ **Faster** - Find articles quickly with sorting
- 🎯 **Focused** - Filter to recent content with 7-day toggle
- 📌 **Organized** - Bookmark important feeds for quick access
- 🎨 **Flexible** - Customize view to match your needs

**Total Features:**
- ✅ RSS/Atom feeds
- ✅ Audio podcasts
- ✅ Video podcasts
- ✅ Article sorting (NEW)
- ✅ 7-day filter (NEW)
- ✅ Feed bookmarks (NEW)
- ✅ AI summaries
- ✅ Categories & OPML
- ✅ Dark mode
- ✅ PDF export
- ✅ Reading stats

Happy reading! 📰

---

**Version:** 3.7.0
**Previous Version:** 3.6.0
**Release Date:** 2026-02-16
