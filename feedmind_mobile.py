"""
FeedMind Mobile - Entry Point
Mobile RSS reader app for Android and iOS using Kivy/KivyMD.
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mobile.app import FeedMindApp


if __name__ == '__main__':
    FeedMindApp().run()
