"""
FeedMind Mobile - Entry Point
Mobile RSS reader app for Android and iOS using Kivy/KivyMD.

Usage:
    # Run on desktop (default phone size)
    python feedmind_mobile.py

    # Run with custom window size
    KIVY_WINDOW_SIZE=400,700 python feedmind_mobile.py
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Kivy for desktop testing (before importing Kivy)
if not os.environ.get('KIVY_WINDOW_SIZE'):
    # Default mobile screen size for desktop testing
    os.environ['KIVY_WINDOW_SIZE'] = '400,700'

from mobile.app import FeedMindApp


if __name__ == '__main__':
    FeedMindApp().run()
