# -*- mode: python ; coding: utf-8 -*-
# FeedMind PyInstaller Specification File
# This file defines how to package feedmind.py into a Windows executable

block_cipher = None

a = Analysis(
    ['feedmind.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Add any data files here if needed in the future
        # Example: ('images/', 'images'),
    ],
    hiddenimports=[
        # Core dependencies
        'anthropic',
        'openai',
        'pygame',
        'newspaper',
        'newspaper3k',
        'feedparser',
        'requests',
        'urllib3',
        'sqlite3',

        # Tkinter modules
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.font',
        'tkinter.messagebox',
        'tkinter.filedialog',

        # Image handling
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',

        # HTML parsing
        'html.parser',
        'urllib.parse',

        # Additional modules that might be missed
        'logging',
        'json',
        'datetime',
        'threading',
        'queue',
        'webbrowser',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude large packages we don't use
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'setuptools',
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
    upx=True,  # Compress executable (reduces size)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='feedmind.ico',  # Uncomment and add icon file if you have one
)
