"""
Video Player Widget for FeedMind
Supports video podcast playback using system's default player or embedded player.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VideoPlayerWidget(ttk.Frame):
    """
    Simple video player widget that can either:
    1. Launch videos in system default player (simple, always works)
    2. Show video metadata and controls

    For embedded playback, would require python-vlc or similar,
    but system player is more reliable and lightweight.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_video = None
        self.current_title = None
        self._create_ui()

    def _create_ui(self):
        """Create the video player UI."""
        # Title label
        self.title_label = ttk.Label(
            self,
            text="No video loaded",
            font=('Arial', 10, 'bold'),
            wraplength=300
        )
        self.title_label.pack(pady=5)

        # Video info frame
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        self.info_label = ttk.Label(
            info_frame,
            text="",
            wraplength=300
        )
        self.info_label.pack()

        # Control buttons frame
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)

        # Play button (launches in system player)
        self.play_btn = ttk.Button(
            button_frame,
            text="▶ Play Video",
            command=self._play_video,
            state=tk.DISABLED
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        # Open location button
        self.location_btn = ttk.Button(
            button_frame,
            text="📁 Show File",
            command=self._open_file_location,
            state=tk.DISABLED
        )
        self.location_btn.pack(side=tk.LEFT, padx=5)

    def load_video(self, file_path: str, video_title: str = ""):
        """
        Load a video file for playback.

        Args:
            file_path: Path to video file
            video_title: Optional title to display
        """
        if not file_path or not os.path.exists(file_path):
            self._reset()
            return

        self.current_video = file_path
        self.current_title = video_title or os.path.basename(file_path)

        # Update UI
        self.title_label.config(text=self.current_title)

        # Get file info
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        file_ext = os.path.splitext(file_path)[1].upper()

        info_text = f"Format: {file_ext}\nSize: {size_mb:.1f} MB"
        self.info_label.config(text=info_text)

        # Enable buttons
        self.play_btn.config(state=tk.NORMAL)
        self.location_btn.config(state=tk.NORMAL)

        logger.info(f"Loaded video: {video_title} ({file_path})")

    def _play_video(self):
        """Open video in system's default video player."""
        if not self.current_video:
            return

        try:
            self._open_file(self.current_video)
            logger.info(f"Opened video in system player: {self.current_video}")
        except Exception as e:
            logger.error(f"Failed to open video: {e}")
            messagebox.showerror(
                "Video Player Error",
                f"Failed to open video:\n{str(e)}\n\n"
                "Make sure you have a video player installed."
            )

    def _open_file_location(self):
        """Open the folder containing the video file."""
        if not self.current_video:
            return

        try:
            folder = os.path.dirname(os.path.abspath(self.current_video))
            self._open_file(folder)
            logger.info(f"Opened video location: {folder}")
        except Exception as e:
            logger.error(f"Failed to open location: {e}")
            messagebox.showerror(
                "Error",
                f"Failed to open file location:\n{str(e)}"
            )

    def _open_file(self, path: str):
        """
        Open a file or folder using the system's default application.
        Works cross-platform (Windows, macOS, Linux).
        """
        system = platform.system()

        if system == 'Windows':
            os.startfile(path)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', path], check=True)
        else:  # Linux and others
            subprocess.run(['xdg-open', path], check=True)

    def _reset(self):
        """Reset the player to initial state."""
        self.current_video = None
        self.current_title = None
        self.title_label.config(text="No video loaded")
        self.info_label.config(text="")
        self.play_btn.config(state=tk.DISABLED)
        self.location_btn.config(state=tk.DISABLED)

    def clear(self):
        """Clear the current video."""
        self._reset()


def is_video_file(filename: str) -> bool:
    """
    Check if a file is a video based on extension.

    Args:
        filename: File name or path

    Returns:
        True if file appears to be a video
    """
    video_extensions = {
        '.mp4', '.m4v', '.mkv', '.avi', '.mov', '.wmv',
        '.flv', '.webm', '.mpg', '.mpeg', '.3gp', '.ogv'
    }
    ext = os.path.splitext(filename)[1].lower()
    return ext in video_extensions


# Test the widget
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Video Player Widget Test")
    root.geometry("400x300")

    player = VideoPlayerWidget(root)
    player.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Test with a dummy path (won't actually play)
    test_btn = ttk.Button(
        root,
        text="Load Test Video",
        command=lambda: player.load_video(
            "/path/to/test/video.mp4",
            "Test Video Episode"
        )
    )
    test_btn.pack(pady=5)

    root.mainloop()
