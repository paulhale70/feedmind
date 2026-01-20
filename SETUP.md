# RSSreaderV1 Setup Guide for Beginners

This guide will help you install and run the RSSreaderV1 application on your computer, even if you've never used Python before.

## What You'll Need

- A computer running Windows, Mac, or Linux
- About 5-10 minutes
- An internet connection

## Step 1: Install Python

RSSreaderV1 is built with Python, so you need to install it first.

### For Windows:

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click the big yellow "Download Python" button
3. Run the downloaded file
4. **IMPORTANT:** Check the box that says "Add Python to PATH" at the bottom
5. Click "Install Now"
6. Wait for the installation to complete

### For Mac:

1. Open Terminal (press Command + Space, type "Terminal", press Enter)
2. Type this command and press Enter:
   ```bash
   python3 --version
   ```
3. If you see a version number like "Python 3.11.x", you're ready! Skip to Step 2.
4. If not, go to [python.org/downloads](https://www.python.org/downloads/) and download Python for Mac
5. Run the downloaded file and follow the installation steps

### For Linux:

Python is usually already installed. Open Terminal and type:
```bash
python3 --version
```

If you see a version number, you're ready! If not, use your package manager:
- Ubuntu/Debian: `sudo apt install python3`
- Fedora: `sudo dnf install python3`

## Step 2: Download the RSSreaderV1 Files

You have two options:

### Option A: Download as ZIP (Easier)

1. Go to the GitHub repository page
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract the ZIP file to a location you'll remember (like your Desktop or Documents folder)

### Option B: Use Git (If you have it installed)

Open Terminal/Command Prompt and type:
```bash
git clone https://github.com/paulhale70/Wildcat.git
cd Wildcat
```

## Step 3: Navigate to the Folder

### For Windows:

1. Open File Explorer
2. Navigate to where you extracted the files
3. Hold Shift and right-click in the folder
4. Click "Open PowerShell window here" or "Open Command Prompt here"

### For Mac/Linux:

1. Open Terminal
2. Type `cd` followed by a space
3. Drag the Wildcat folder into the Terminal window
4. Press Enter

## Step 4: Run the Application

In the Terminal or Command Prompt window, type:

### For Windows:
```bash
python rss_reader.py
```

### For Mac/Linux:
```bash
python3 rss_reader.py
```

Press Enter and the application should open!

## Step 5: First Time Using RSSreaderV1

When the application opens for the first time:

### Adding Your First Feed

1. Look for the "RSS Feed URL" text box in the left panel
2. Copy one of these sample feed URLs:
   - NASA News: `https://www.nasa.gov/rss/dyn/breaking_news.rss`
   - TechCrunch: `https://techcrunch.com/feed/`
   - Hacker News: `https://news.ycombinator.com/rss`

3. Paste the URL into the text box
4. Click the green "Add Feed" button (or press Enter)
5. Wait a few seconds while it downloads the articles
6. You'll see the feed appear in the "Subscribed Feeds" list

### Reading Articles

1. Click on a feed in the left sidebar to see its articles
2. Click on any article in the list to read its description
3. Double-click an article to open it in your web browser

### Organizing Your Reading

- Click **"All"** to see all articles
- Click **"Unread"** to see only unread articles
- Click **"Favorites"** to see articles you've starred
- Use the **search box** at the top to find specific topics

## Common Problems and Solutions

### Problem: "python is not recognized" (Windows)

**Solution:** You didn't check "Add Python to PATH" during installation.
1. Uninstall Python from Windows Settings
2. Reinstall Python and make sure to check the "Add Python to PATH" box

### Problem: "No module named 'tkinter'" (Linux)

**Solution:** Install tkinter separately:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter
```

### Problem: Window opens but is blank or crashes

**Solution:**
1. Close the application
2. Delete the file `rss_reader.db` in the Wildcat folder
3. Run the application again

### Problem: "Failed to add feed"

**Solution:**
1. Check your internet connection
2. Make sure the URL starts with `http://` or `https://`
3. Try a different feed URL to see if the problem is with that specific feed
4. Some feeds may block automated access - try a different feed

### Problem: Application won't start on Mac

**Solution:** You might need to allow the app to run:
1. Go to System Preferences → Security & Privacy
2. Click "Open Anyway" if you see a message about the app

## Tips for New Users

### Finding RSS Feeds

Many websites offer RSS feeds. Look for:
- Orange RSS icons on websites
- Links that say "RSS", "Feed", or "Subscribe"
- Add `/feed` or `/rss` to the end of website URLs (e.g., `example.com/feed`)

### Organizing Your Feeds

1. **Use the Unread view** to focus on new content
2. **Star important articles** by clicking the "Favorite" button
3. **Search** for specific topics across all your feeds
4. **Enable Auto-refresh** to automatically get new articles every 15 minutes

### Keyboard Shortcuts

- Press **Enter** in the URL box to quickly add a feed
- Press **Enter** in the search box to search
- **Double-click** any article to open it in your browser

## Understanding the Interface

```
┌─────────────────────────────────────────────────────────┐
│                    RSSreaderV1                          │
├──────────────┬──────────────────────────────────────────┤
│              │  Search: [type here] [Search] [Clear]    │
│ Add Feed:    │  ┌───────────────────────────────────┐  │
│ [URL here]   │  │ ● Article 1 (unread)              │  │
│ [Add][Remove]│  │ ★ Article 2 (favorite)            │  │
│              │  │ Article 3 (read - gray text)      │  │
│ [All]        │  └───────────────────────────────────┘  │
│ [Unread]     │                                          │
│ [Favorites]  │  Article Details:                        │
│              │  ┌───────────────────────────────────┐  │
│ Unread: 12   │  │ Full article description shows    │  │
│              │  │ here when you click an article    │  │
│ Feeds:       │  └───────────────────────────────────┘  │
│ • NASA (5)   │  [Open][Mark Read][Favorite][Cache]    │
│ • Tech (7)   │                                          │
│ • News       │                                          │
│              │                                          │
│ [Refresh]    │                                          │
│ [Refresh All]│                                          │
│ [Mark All ✓] │                                          │
│ ☑ Auto-ref.  │                                          │
└──────────────┴──────────────────────────────────────────┘
```

### What the Symbols Mean

- **●** = Unread article
- **★** = Favorite article
- **(number)** = Unread count next to feed names
- **Bold text** = Unread article
- **Gray text** = Read article

## Getting More Help

### If you're stuck:

1. **Check this guide again** - make sure you followed all steps
2. **Try the basic test** - run `python3 test_rss.py` to check if everything works
3. **Look at the error message** - it often tells you what's wrong
4. **Delete and reinstall** - sometimes starting fresh helps

### Want to learn more?

- Read `README.md` for detailed features
- Read `FEATURES.md` for a complete feature list
- Explore the application - you can't break anything!

## Updating the Application

When a new version is released:

1. Download the new files
2. Copy your `rss_reader.db` file from the old folder to the new folder
   (This saves your feeds and articles!)
3. Run the new version

The database will automatically upgrade to support new features.

## Daily Use Workflow

Here's how to use RSSreaderV1 every day:

### Morning Routine:
1. Open RSSreaderV1
2. Click "Unread" to see new articles
3. Read articles that interest you
4. Star important ones with the "Favorite" button
5. Articles you open in browser are automatically marked as read

### Weekly Maintenance:
1. Click "Clear Cache" to remove old articles
2. Remove feeds you no longer read
3. Add new feeds you discovered

### Quick Checks:
- The unread counter shows how many new articles you have
- Enable auto-refresh to get updates automatically
- Use search to find specific topics

## Uninstalling

If you want to remove RSSreaderV1:

1. Delete the Wildcat folder
2. That's it! No registry entries or system files to clean up

Your feeds and articles are stored in `rss_reader.db` in the Wildcat folder, so if you keep that file, you can always come back later.

## Privacy and Data

- **All your data stays on your computer** - nothing is sent to any servers
- **No account needed** - no registration, no email, no tracking
- **Your feeds are private** - only you know what you subscribe to
- **Works offline** - read cached articles without internet

## Summary

1. ✅ Install Python
2. ✅ Download RSSreaderV1 files
3. ✅ Open Terminal in the folder
4. ✅ Run `python3 rss_reader.py`
5. ✅ Add your first feed
6. ✅ Start reading!

**You're all set! Enjoy staying updated with RSSreaderV1!** 📰✨
