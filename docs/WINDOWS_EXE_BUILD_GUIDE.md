# FeedMind Windows .exe Build Guide

**Create a standalone Windows executable for FeedMind v3.5**

This guide walks through creating a distributable Windows .exe file that users can run without installing Python or any dependencies.

---

## Overview

**What we'll create:**
- Single-file `FeedMind.exe` (~40-60MB)
- Includes Python interpreter and all dependencies
- No installation required - just run the .exe
- Works on Windows 10/11 (64-bit)

**Tool:** PyInstaller (most reliable for Tkinter apps)

---

## Prerequisites

**System Requirements:**
- Windows 10/11 (64-bit)
- Python 3.8+ installed
- FeedMind desktop app working
- ~500MB free disk space

---

## Step 1: Install PyInstaller

Open Command Prompt or PowerShell:

```bash
pip install pyinstaller
```

Verify installation:
```bash
pyinstaller --version
```

Expected output: `6.x.x` or similar

---

## Step 2: Test Current FeedMind

Before packaging, make sure FeedMind runs correctly:

```bash
cd C:\path\to\Wildcat
python feedmind.py
```

If it works, proceed to packaging.

---

## Step 3: Create Build Specification File

PyInstaller uses a `.spec` file for advanced configuration. Let's create one optimized for FeedMind.

Create `feedmind.spec` in your Wildcat directory:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['feedmind.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include any data files here if needed
        # ('path/to/data', 'destination/folder'),
    ],
    hiddenimports=[
        'anthropic',
        'openai',
        'pygame',
        'newspaper',
        'newspaper3k',
        'feedparser',
        'requests',
        'urllib3',
        'sqlite3',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.font',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Exclude unused large packages
        'numpy',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FeedMind',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress exe (optional, makes it smaller)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='feedmind.ico',  # Add your icon file (optional)
)
```

---

## Step 4: Create Application Icon (Optional)

If you want a custom icon for FeedMind.exe:

1. **Create or find an icon file** (256x256 PNG recommended)
2. **Convert to .ico format:**
   - Online tool: https://convertio.co/png-ico/
   - Or use Pillow:
   ```python
   from PIL import Image
   img = Image.open('feedmind.png')
   img.save('feedmind.ico', format='ICO', sizes=[(256, 256)])
   ```
3. **Place `feedmind.ico`** in your Wildcat directory

**If you don't have an icon:** Remove or comment out the `icon='feedmind.ico'` line in the spec file.

---

## Step 5: Build the Executable

### Method A: Using the Spec File (Recommended)

```bash
cd C:\path\to\Wildcat
pyinstaller feedmind.spec
```

### Method B: Direct Command (Simpler, but less control)

```bash
pyinstaller --onefile --windowed --name "FeedMind" feedmind.py
```

**Build process:**
- Takes 2-5 minutes
- Creates `build/` and `dist/` folders
- Lots of output messages (normal)

**Expected output:**
```
...
Building EXE from EXE-00.toc completed successfully.
```

---

## Step 6: Test the Executable

1. **Navigate to dist folder:**
   ```bash
   cd dist
   ```

2. **Run FeedMind.exe:**
   - Double-click `FeedMind.exe`
   - Or from command prompt: `.\FeedMind.exe`

3. **Test all features:**
   - Add a feed
   - View articles
   - Search
   - AI summaries (if configured)
   - Podcast playback
   - OPML import/export

**Common first-run behavior:**
- Might take 5-10 seconds to start (normal for first launch)
- Windows Defender might scan it (normal)
- Database file `feedmind.db` created in same directory

---

## Step 7: Distribution Package

Create a distributable folder with everything needed:

```
FeedMind-v3.5-Windows/
├── FeedMind.exe           (your executable)
├── README.txt             (usage instructions)
└── LICENSE.txt            (if applicable)
```

**Create README.txt:**
```
FeedMind v3.5 - RSS Feed Reader & Podcast Manager
====================================================

QUICK START:
1. Double-click FeedMind.exe to launch
2. Add your first RSS feed using the URL entry box
3. Click refresh to load articles

FEATURES:
- RSS/Atom feed reader
- Podcast support with audio playback
- AI-powered article summaries
- Search and categories
- Dark/light themes
- OPML import/export

REQUIREMENTS:
- Windows 10/11 (64-bit)
- Internet connection for fetching feeds
- Optional: AI API keys for summarization features

SUPPORT:
- GitHub: https://github.com/paulhale70/Wildcat
- Issues: Report bugs on GitHub

DATABASE:
- Your feeds and data are stored in "feedmind.db"
- Keep this file to preserve your data between sessions
- Back it up regularly!

VERSION: 3.5.0
BUILD DATE: 2026-01-31
```

---

## Troubleshooting

### Issue 1: "Missing module" error when running .exe

**Solution:** Add the module to `hiddenimports` in feedmind.spec:
```python
hiddenimports=[
    'anthropic',
    'missing_module_name',  # Add here
    ...
],
```
Then rebuild: `pyinstaller feedmind.spec`

---

### Issue 2: .exe file is too large (>100MB)

**Solutions:**

1. **Enable UPX compression** (already in spec file):
   ```bash
   # Install UPX first
   # Download from: https://upx.github.io/
   ```

2. **Exclude unused packages** in spec file:
   ```python
   excludes=[
       'matplotlib',
       'numpy',
       'scipy',
       'pandas',
       'jupyter',
       'IPython',
   ],
   ```

3. **Use --exclude-module** in command:
   ```bash
   pyinstaller --onefile --windowed --exclude-module matplotlib feedmind.py
   ```

---

### Issue 3: Console window appears

**Solution:** Make sure `console=False` in spec file, or use `--windowed` flag:
```bash
pyinstaller --onefile --windowed feedmind.py
```

---

### Issue 4: "Failed to execute script" error

**Possible causes:**

1. **Missing dependencies:** Check spec file's `hiddenimports`
2. **Path issues:** Try running from the same directory as feedmind.db
3. **Antivirus blocking:** Temporarily disable antivirus to test

**Debug mode:** Build with console to see errors:
```python
# In feedmind.spec, change:
console=True,  # Temporarily enable to see errors
```

---

### Issue 5: Database not found

**Solution:** The exe looks for `feedmind.db` in the current directory. Either:
- Run .exe from same folder as .db
- Or modify feedmind.py to use absolute path:
  ```python
  import os
  import sys

  # Get directory where exe is located
  if getattr(sys, 'frozen', False):
      # Running as exe
      application_path = os.path.dirname(sys.executable)
  else:
      # Running as script
      application_path = os.path.dirname(__file__)

  db_path = os.path.join(application_path, 'feedmind.db')
  self.db = RSSDatabase(db_path)
  ```

---

### Issue 6: Pygame audio not working

**Solution:** Pygame might need additional DLLs. Add to spec file:
```python
import pygame
import os

pygame_path = os.path.dirname(pygame.__file__)

binaries=[
    (os.path.join(pygame_path, '*.dll'), 'pygame'),
],
```

---

## Advanced: Create Installer (Optional)

If you want a professional installer instead of just .exe:

### Option 1: Inno Setup (Free, Windows)

1. Download: https://jrsoftware.org/isinfo.php
2. Create installer script
3. Generates setup.exe that installs FeedMind

### Option 2: NSIS (Free, Open Source)

1. Download: https://nsis.sourceforge.io/
2. Create .nsi script
3. More complex but very powerful

---

## Build Script (Automated)

Create `build_exe.bat` for easy rebuilding:

```batch
@echo off
echo Building FeedMind.exe...
echo.

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with PyInstaller
pyinstaller feedmind.spec

REM Check if successful
if exist dist\FeedMind.exe (
    echo.
    echo ========================================
    echo Build successful!
    echo Executable: dist\FeedMind.exe
    echo ========================================
    echo.

    REM Optional: Open dist folder
    explorer dist
) else (
    echo.
    echo ========================================
    echo Build FAILED! Check errors above.
    echo ========================================
)

pause
```

Usage: Just double-click `build_exe.bat`

---

## File Size Optimization

**Current size:** ~40-60MB (typical for Tkinter + dependencies)

**Optimization strategies:**

1. **Exclude large unused packages** (already in spec)
2. **Use UPX compression** (already in spec)
3. **Strip debug symbols:** `strip=True` in spec
4. **Remove docstrings:** Not recommended (breaks some packages)

**Typical size breakdown:**
- Python interpreter: ~10MB
- Tkinter: ~5MB
- Dependencies (pygame, requests, etc.): ~15MB
- Your code: ~1MB
- Overhead: ~10-20MB

**Note:** Size <100MB is acceptable for modern systems.

---

## Code Signing (Professional Distribution)

For public distribution, consider code signing to avoid Windows warnings:

1. **Get a code signing certificate** (costs $100-400/year)
   - Providers: DigiCert, Sectigo, GlobalSign
2. **Sign the exe:**
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com FeedMind.exe
   ```

**Benefits:**
- No "Unknown publisher" warning
- Builds trust with users
- Required for some enterprise environments

---

## Distribution Checklist

Before sharing FeedMind.exe:

- [ ] Test on clean Windows machine (no Python installed)
- [ ] Test all major features (feeds, podcasts, AI, OPML)
- [ ] Check exe size is reasonable (<100MB)
- [ ] Include README.txt with instructions
- [ ] Include LICENSE if open source
- [ ] Test on Windows 10 and Windows 11
- [ ] Scan with antivirus to ensure clean
- [ ] Create GitHub release with download link
- [ ] Consider code signing for public distribution

---

## GitHub Release

Create a release on GitHub:

1. **Tag the version:**
   ```bash
   git tag -a v3.5.0 -m "FeedMind v3.5.0 - Windows Release"
   git push origin v3.5.0
   ```

2. **Create release on GitHub:**
   - Go to repository → Releases → New Release
   - Select tag: v3.5.0
   - Title: "FeedMind v3.5.0 - Windows"
   - Upload: `FeedMind.exe` (or zip file)
   - Description: Features, requirements, changelog

3. **Download link format:**
   ```
   https://github.com/paulhale70/Wildcat/releases/download/v3.5.0/FeedMind.exe
   ```

---

## Alternative: Create ZIP Distribution

```bash
# Create dist folder structure
mkdir FeedMind-v3.5-Windows
copy dist\FeedMind.exe FeedMind-v3.5-Windows\
copy README.txt FeedMind-v3.5-Windows\
copy LICENSE.txt FeedMind-v3.5-Windows\

# Create ZIP
# Use 7-Zip or Windows built-in compression
# Right-click → Send to → Compressed folder
```

**Result:** `FeedMind-v3.5-Windows.zip` (~30-40MB compressed)

---

## Summary

**Quick build command:**
```bash
pyinstaller feedmind.spec
```

**Output:**
- `dist/FeedMind.exe` - Ready to distribute!

**Test:**
```bash
cd dist
FeedMind.exe
```

**Distribute:**
- Upload to GitHub Releases
- Share direct download link
- Users just run the .exe - no installation needed!

---

## Next Steps

After creating .exe:

1. **Test thoroughly** on multiple Windows systems
2. **Create release notes** documenting features
3. **Upload to GitHub** as release
4. **Share with users** for feedback
5. **Consider:** Windows Store submission (requires signing)

---

**Document Version:** 1.0
**Last Updated:** 2026-01-31
**Status:** Ready for Windows executable creation
