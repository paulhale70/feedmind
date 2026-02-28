"""
FeedMind Mobile - Buildozer Entry Point
This file is used by buildozer as the main entry point for Android/iOS builds.
For desktop testing, use feedmind_mobile.py instead.
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mobile.app import FeedMindApp


if __name__ == '__main__':
    FeedMindApp().run()
