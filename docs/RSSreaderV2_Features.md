# RSSreaderV2 - Feature Documentation

## New Features in V2

### 1. Dark Mode ✨
**Status:** Implemented

- **Light Theme** - Clean, bright interface
- **Dark Theme** - Easy on the eyes for night reading
- **Theme Toggle** - Switch themes with one click (or Ctrl+T)
- **Persistent** - Theme choice saved between sessions
- **System Colors** - Consistent across all UI elements

**Usage:**
- Menu → View → Toggle Dark Mode
- Keyboard: `Ctrl+T`

---

### 2. OPML Import/Export 📁
**Status:** Implemented

- **Export Subscriptions** - Save all your feeds to OPML file
- **Import Subscriptions** - Bulk import from other RSS readers
- **Category Preservation** - Maintains folder structure
- **Standard Format** - Compatible with all major RSS readers

**Usage:**
- Menu → File → Import OPML
- Menu → File → Export OPML
- Supports Feedly, Inoreader, NewsBlur, and other OPML exports

---

### 3. Categories/Folders 📂
**Status:** Implemented

- **Organize Feeds** - Group feeds by topic
- **Create Categories** - Tech, News, Sports, etc.
- **Drag & Drop** - Easy reorganization
- **Color Coding** - Visual identification
- **Filter by Category** - Focus on specific topics

**Features:**
- Unlimited categories
- Move feeds between categories
- Uncategorized default folder
- Category-based feed counts

**Usage:**
- Right-click feed → Move to Category
- Menu → Manage → Categories
- Categories shown in sidebar

---

### 4. Keyboard Shortcuts ⌨️
**Status:** Implemented

**Navigation:**
- `J` - Next article
- `K` - Previous article
- `O` / `Enter` - Open article in browser
- `R` - Mark as read/unread
- `F` - Toggle favorite
- `Space` - Scroll article down
- `Shift+Space` - Scroll article up

**Actions:**
- `N` - New feed
- `Ctrl+R` - Refresh current feed
- `Ctrl+Shift+R` - Refresh all feeds
- `Ctrl+F` - Focus search
- `Ctrl+T` - Toggle dark mode
- `Ctrl+S` - View statistics
- `Esc` - Clear search / Deselect

**Views:**
- `1` - All articles
- `2` - Unread articles
- `3` - Favorites

**Menu:**
- `Ctrl+I` - Import OPML
- `Ctrl+E` - Export OPML
- `Ctrl+M` - Manage categories
- `Ctrl+,` - Settings (future)

---

### 5. Reading Statistics 📊
**Status:** Implemented

- **Articles Read** - Total count over time
- **Daily Breakdown** - See your reading patterns
- **Reading Streak** - Track consecutive days
- **Feed Statistics** - Most/least active feeds
- **Time Period Selection** - 7, 30, or 90 days

**Metrics:**
- Total articles read
- Average per day
- Unread backlog
- Total feeds subscribed
- Favorite count

**Usage:**
- Menu → View → Statistics
- Keyboard: `Ctrl+S`
- Visual charts and graphs

---

### 6. Smart Refresh Intervals ⏰
**Status:** Implemented

- **Per-Feed Settings** - Different interval for each feed
- **Preset Options:**
  - 15 minutes (default)
  - 30 minutes
  - 1 hour
  - 3 hours
  - 6 hours
  - 12 hours
  - 24 hours
- **Auto-Refresh** - Background updates based on schedule
- **Last Refresh Time** - See when feed was last updated
- **Smart Queue** - Refreshes oldest feeds first

**Usage:**
- Right-click feed → Refresh Settings
- Set interval per feed
- Global auto-refresh toggle still available

---

## Database Schema Changes

### New Tables:

**categories**
- id (PRIMARY KEY)
- name (UNIQUE)
- color
- created_date

**reading_stats**
- date (PRIMARY KEY)
- articles_read
- time_spent_minutes

**settings**
- key (PRIMARY KEY)
- value

### Modified Tables:

**feeds** - Added:
- category_id (FOREIGN KEY)
- refresh_interval (INTEGER)
- last_refresh (TEXT)

**articles** - Added:
- read_date (TEXT) - Timestamp when marked as read

---

## Migration from V1

Your V1 database is fully compatible! V2 will:
1. Auto-detect V1 database
2. Add new columns automatically
3. Create new tables
4. Preserve all existing data
5. Keep all read/unread states
6. Maintain favorites

**Steps:**
1. Close V1 if running
2. Start V2 - it will auto-migrate
3. Your feeds and articles are preserved
4. New features available immediately

---

## Keyboard Shortcut Quick Reference Card

```
Navigation          Actions                 Views
-----------         --------               ------
J - Next            R - Mark read           1 - All
K - Previous        F - Favorite            2 - Unread
O - Open            N - New feed            3 - Favorites
Space - Scroll      Ctrl+R - Refresh
Shift+Space - Up    Ctrl+S - Stats
                    Ctrl+T - Dark mode
                    Ctrl+F - Search
```

---

## Future Features (V3)

Coming soon:
- **Podcast Support** - RSS podcasts with audio player
- **Full-text extraction** - Complete articles
- **Export to PDF** - Save articles as PDF
- **Desktop notifications** - New article alerts
- **Email digests** - Daily/weekly summaries
- **Reading mode** - Distraction-free view
- **Tags** - Multi-dimensional organization
- **Cloud sync** - Multi-device support

---

## Technical Details

**New Dependencies:** None! Still uses only Python stdlib

**New Files:**
- `rss_database_v2.py` - Enhanced database with categories
- `rss_opml.py` - OPML import/export
- `rss_themes.py` - Theme definitions
- `rss_reader_v2.py` - Main application V2

**Backward Compatibility:** Full

**Database:** SQLite (auto-migrating)

**Platform:** Windows, Mac, Linux

---

## Performance Improvements

- Faster search with better indexing
- Optimized category queries
- Background refresh doesn't block UI
- Efficient statistics calculation
- Smart cache management

---

## Accessibility

- Full keyboard navigation
- Screen reader compatible
- High contrast themes
- Adjustable layouts
- Clear visual indicators

---

## Changelog

### Version 2.0.0
- ✨ Added dark mode with theme toggle
- ✨ Added OPML import/export
- ✨ Added categories/folders for feed organization
- ✨ Added comprehensive keyboard shortcuts
- ✨ Added reading statistics dashboard
- ✨ Added per-feed refresh intervals
- ⚡ Improved performance for large feed lists
- ⚡ Enhanced search functionality
- 🐛 Fixed threading issues from V1
- 🎨 Refined UI layout and spacing
- 📚 Added complete documentation

### Version 1.0.0
- Initial release with core features

---

## Getting Started with V2

1. **Launch V2:**
   ```bash
   python3 rss_reader_v2.py
   ```

2. **Import your feeds (if new user):**
   - File → Import OPML
   - Or add feeds manually

3. **Create categories:**
   - Manage → Categories
   - Add: Tech, News, Sports, etc.

4. **Organize feeds:**
   - Right-click feed
   - Move to Category

5. **Try keyboard shortcuts:**
   - Press `J`/`K` to navigate
   - Press `R` to mark read
   - Press `F` to favorite

6. **Enable dark mode:**
   - View → Toggle Dark Mode
   - Or press `Ctrl+T`

7. **View your statistics:**
   - View → Statistics
   - Or press `Ctrl+S`

---

## Support & Feedback

- Check `SETUP.md` for installation help
- See `FEATURES.md` for complete V2 feature list
- Review `README.md` for quick start guide

---

**Enjoy RSSreaderV2!** 📰✨
