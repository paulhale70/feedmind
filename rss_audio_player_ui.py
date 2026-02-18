"""
Audio Player UI Widget for RSS Reader V3
Provides playback controls for podcast episodes.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from rss_audio_player import AudioPlayer, PlaybackState


class AudioPlayerWidget(tk.Frame):
    """Audio player widget with playback controls."""

    def __init__(self, parent, **kwargs):
        """
        Initialize audio player widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)

        self.player = AudioPlayer()
        self.current_episode_title = ""
        self.update_job = None

        self._create_ui()
        self._update_controls()

        # Set up player callback
        if self.player.is_available():
            self.player.set_update_callback(self._on_player_update)

    def _create_ui(self):
        """Create the UI components."""
        # Title/episode label
        self.episode_label = tk.Label(
            self,
            text="No episode loaded",
            font=("Arial", 10, "bold"),
            anchor=tk.W
        )
        self.episode_label.pack(fill=tk.X, padx=5, pady=(5, 0))

        # Progress bar
        progress_frame = tk.Frame(self)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.time_label = tk.Label(progress_frame, text="0:00", width=6, anchor=tk.E)
        self.time_label.pack(side=tk.LEFT, padx=(0, 5))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            variable=self.progress_var,
            orient=tk.HORIZONTAL,
            command=self._on_seek
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.duration_label = tk.Label(progress_frame, text="0:00", width=6, anchor=tk.W)
        self.duration_label.pack(side=tk.LEFT, padx=(5, 0))

        # Control buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Play/Pause button
        self.play_pause_btn = tk.Button(
            btn_frame,
            text="▶ Play",
            command=self._toggle_play_pause,
            width=10
        )
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)

        # Stop button
        self.stop_btn = tk.Button(
            btn_frame,
            text="■ Stop",
            command=self._stop,
            width=10,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        # Speed selector (placeholder - pygame doesn't support speed)
        tk.Label(btn_frame, text="Speed:").pack(side=tk.LEFT, padx=(10, 2))
        self.speed_var = tk.StringVar(value="1.0x")
        speed_menu = ttk.Combobox(
            btn_frame,
            textvariable=self.speed_var,
            values=["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"],
            width=6,
            state="readonly"
        )
        speed_menu.pack(side=tk.LEFT, padx=2)
        speed_menu.bind('<<ComboboxSelected>>', self._on_speed_change)

        # Volume slider
        tk.Label(btn_frame, text="Volume:").pack(side=tk.LEFT, padx=(10, 2))
        self.volume_var = tk.DoubleVar(value=70)
        volume_slider = ttk.Scale(
            btn_frame,
            from_=0,
            to=100,
            variable=self.volume_var,
            orient=tk.HORIZONTAL,
            command=self._on_volume_change,
            length=100
        )
        volume_slider.pack(side=tk.LEFT, padx=2)
        self.volume_label = tk.Label(btn_frame, text="70%", width=4)
        self.volume_label.pack(side=tk.LEFT)

    def load_episode(self, file_path: str, episode_title: str = ""):
        """
        Load an episode for playback.

        Args:
            file_path: Path to audio file
            episode_title: Title to display

        Returns:
            True if loaded successfully
        """
        if not self.player.is_available():
            return False

        success = self.player.load(file_path)

        if success:
            self.current_episode_title = episode_title or file_path
            self.episode_label.config(text=self.current_episode_title)
            self._update_controls()

            # Update duration
            duration = self.player.get_duration()
            if duration > 0:
                self.duration_label.config(text=self._format_time(duration))

        return success

    def _toggle_play_pause(self):
        """Toggle between play and pause."""
        if not self.player.is_available():
            messagebox.showwarning(
                "Audio Unavailable",
                "Audio playback requires pygame.\n\nInstall it with:\n  pip install pygame",
                parent=self
            )
            return

        if not self.player.current_file:
            return

        state = self.player.get_state()

        if state == PlaybackState.PLAYING:
            self.player.pause()
        else:
            self.player.play()

        self._update_controls()

    def _stop(self):
        """Stop playback."""
        if self.player.is_available():
            self.player.stop()
            self._update_controls()

    def _on_seek(self, value):
        """Handle seek bar movement."""
        if not self.player.is_available() or not self.player.current_file:
            return

        # Only seek when user releases (to avoid constant seeking)
        # For now, we'll skip seeking as pygame doesn't handle it well

    def _on_speed_change(self, event):
        """Handle speed change."""
        speed_text = self.speed_var.get()
        speed = float(speed_text.replace('x', ''))

        if self.player.is_available():
            # pygame doesn't support speed change
            # This is a placeholder for future implementation
            success = self.player.set_speed(speed)
            if not success:
                # Reset to 1.0x
                self.speed_var.set("1.0x")

    def _on_volume_change(self, value):
        """Handle volume change."""
        volume = float(value) / 100.0
        if self.player.is_available():
            self.player.set_volume(volume)

        # Update label
        self.volume_label.config(text=f"{int(float(value))}%")

    def _on_player_update(self, position: float, duration: float):
        """Callback from player with position update."""
        # Update progress bar
        if duration > 0:
            progress = (position / duration) * 100
            self.progress_var.set(progress)

        # Update time label
        self.time_label.config(text=self._format_time(position))

    def _update_controls(self):
        """Update control button states."""
        if not self.player.is_available():
            self.episode_label.config(text="Audio unavailable — run: pip install pygame")
            self.play_pause_btn.config(text="▶ Play", state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            return

        if not self.player.current_file:
            self.play_pause_btn.config(text="▶ Play", state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            return

        state = self.player.get_state()

        if state == PlaybackState.PLAYING:
            self.play_pause_btn.config(text="⏸ Pause", state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
        elif state == PlaybackState.PAUSED:
            self.play_pause_btn.config(text="▶ Resume", state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
        else:  # STOPPED
            self.play_pause_btn.config(text="▶ Play", state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def cleanup(self):
        """Clean up resources."""
        if self.update_job:
            self.after_cancel(self.update_job)
        if self.player:
            self.player.cleanup()


def main():
    """Test the audio player widget."""
    root = tk.Tk()
    root.title("Audio Player Test")
    root.geometry("600x150")

    # Check if audio player is available
    player = AudioPlayer()
    if not player.is_available():
        label = tk.Label(
            root,
            text="Audio playback unavailable\nInstall pygame: pip install pygame",
            font=("Arial", 12)
        )
        label.pack(expand=True)
    else:
        widget = AudioPlayerWidget(root)
        widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add test file selector
        def select_file():
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="Select Audio File",
                filetypes=[
                    ("Audio files", "*.mp3 *.wav *.ogg"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                widget.load_episode(file_path, "Test Episode")

        btn = tk.Button(root, text="Load Audio File", command=select_file)
        btn.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
