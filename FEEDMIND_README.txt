FeedMind v3.5 - RSS Feed Reader & Podcast Manager
====================================================

QUICK START
-----------
1. Double-click FeedMind.exe to launch the application
2. Add your first RSS feed by entering the feed URL in the input box
3. Click the "Add Feed" button or press Enter
4. Click "Refresh All" to load articles from your feeds
5. Click on any article to read it

FEATURES
--------
RSS & ATOM FEEDS:
- Subscribe to unlimited RSS/Atom feeds
- Automatic feed updates
- Mark articles as read/unread
- Favorite/star important articles
- Organize feeds into categories
- Search across all articles
- OPML import/export for feed management

PODCASTS:
- Subscribe to podcast feeds
- Stream or download episodes
- Built-in audio player with controls
- Episode queue management
- Playback speed control

AI-POWERED FEATURES:
- Automatic article summarization (requires API key)
- TL;DR generation
- Key points extraction
- Content analysis
- Supports Claude (Anthropic) and OpenAI APIs

READING EXPERIENCE:
- Clean, distraction-free reading interface
- Dark mode and light mode themes
- Full-text article extraction
- In-app article viewer
- PDF export for articles
- Desktop notifications for new content

ORGANIZATION:
- Categories and tags
- Favorites system
- Reading history
- Statistics and analytics
- Custom feed refresh intervals

SYSTEM REQUIREMENTS
-------------------
- Windows 10 or Windows 11 (64-bit)
- 100 MB free disk space
- Internet connection (for fetching feeds)
- Optional: AI API keys for summarization features

GETTING STARTED
---------------
ADDING YOUR FIRST FEED:
1. Find an RSS feed URL (e.g., https://techcrunch.com/feed/)
2. Paste it into the URL entry box at the top
3. Click "Add Feed" or press Enter
4. The feed will appear in your feed list on the left

READING ARTICLES:
1. Select a feed from the left panel
2. Browse articles in the center panel
3. Click an article to read it in the right panel
4. Use toolbar buttons to mark as read, favorite, etc.

ORGANIZING FEEDS:
1. Right-click on a feed to access options
2. Create categories from the menu
3. Drag and drop feeds between categories
4. Use the search box to filter articles

AI SUMMARIES (OPTIONAL):
1. Go to Settings → AI Settings
2. Enter your Anthropic or OpenAI API key
3. Enable AI features
4. Click "Summarize" button on any article

DATA STORAGE
------------
Your feeds and data are stored in "feedmind.db" (SQLite database)
Location: Same folder as FeedMind.exe

IMPORTANT:
- Back up feedmind.db regularly to preserve your data
- Keep feedmind.db in the same folder as the executable
- You can copy feedmind.db to another computer to transfer your feeds

KEYBOARD SHORTCUTS
------------------
Ctrl+R     - Refresh selected feed
Ctrl+A     - Refresh all feeds
Ctrl+F     - Focus search box
Ctrl+N     - Mark as read/unread
Ctrl+S     - Favorite/unfavorite
Ctrl+O     - Open article in browser
Ctrl+Q     - Quit application
Space      - Next article
Backspace  - Previous article
Enter      - Open selected article

CONFIGURATION
-------------
Settings can be accessed via the toolbar:
- Feed refresh intervals
- AI API configuration
- Theme selection (dark/light)
- Notification preferences
- Podcast player settings
- Database location

IMPORTING FEEDS
---------------
If you have feeds from another reader:

1. Export your feeds as OPML from your current reader
2. In FeedMind, go to File → Import OPML
3. Select your OPML file
4. All feeds will be imported with their categories

EXPORTING FEEDS
---------------
To backup or share your feed list:

1. Go to File → Export OPML
2. Choose a save location
3. The OPML file contains all your feeds and categories
4. Import this file in any RSS reader

TROUBLESHOOTING
---------------
APPLICATION WON'T START:
- Make sure feedmind.db has write permissions
- Try running as administrator
- Check Windows Defender hasn't blocked it
- Temporarily disable antivirus

FEEDS NOT UPDATING:
- Check your internet connection
- Verify the feed URL is still valid
- Try removing and re-adding the feed
- Check feed URL in a web browser

AI FEATURES NOT WORKING:
- Verify your API key is correct
- Check you have API credits/quota available
- Ensure internet connection is active
- Check AI provider status page

DATABASE ERRORS:
- Close FeedMind completely
- Make a backup copy of feedmind.db
- Restart FeedMind
- If problems persist, delete feedmind.db (you'll lose data)

SUPPORT & FEEDBACK
------------------
GitHub: https://github.com/paulhale70/Wildcat
Issues: Report bugs at the GitHub repository
Email: [Your contact email]

FINDING RSS FEEDS
-----------------
Many websites offer RSS feeds:
- Look for RSS icon on websites
- Add /feed or /rss to blog URLs
- Use FeedMind's built-in feed discovery tool
- Check https://feedspot.com for popular feeds

Popular RSS feeds to get started:
- TechCrunch: https://techcrunch.com/feed/
- BBC News: http://feeds.bbci.co.uk/news/rss.xml
- NASA: https://www.nasa.gov/rss/dyn/breaking_news.rss
- Hacker News: https://news.ycombinator.com/rss

PRIVACY
-------
FeedMind is a local application:
- All data stored locally on your computer
- No telemetry or analytics sent
- No account required
- Internet used only for:
  * Fetching RSS feeds
  * AI API calls (if enabled)
  * Opening links in browser

LICENSE
-------
[Add your license information here]
Copyright (c) 2026
See LICENSE file for full license text

VERSION INFORMATION
-------------------
Version: 3.5.0
Build Date: 2026-01-31
Python Version: 3.8+

CHANGELOG
---------
v3.5.0 (2026-01-31):
- RSS feed auto-discovery feature
- Local logging system
- Search keyboard shortcut fix
- Improved stability
- Performance optimizations

v3.0 (Previous):
- Podcast support with audio player
- AI-powered summaries
- Full-text article extraction
- PDF export
- Category management

v2.0 (Previous):
- Multiple feed support
- OPML import/export
- Dark mode
- Reading statistics

v1.0 (Initial):
- Basic RSS feed reader
- Article viewing
- Favorites system

CREDITS
-------
Developed with:
- Python 3
- Tkinter (GUI framework)
- Feedparser (RSS parsing)
- Pygame (Audio playback)
- Anthropic Claude API (AI features)
- OpenAI API (AI features)
- Newspaper3k (Article extraction)

THANK YOU
---------
Thank you for using FeedMind!
We hope it enhances your RSS reading experience.

If you find FeedMind useful, please:
- Star the project on GitHub
- Share it with others
- Report bugs and suggest features
- Contribute to the project

Happy reading! 📰
