"""
Audio Player for RSS Reader V3
Handles podcast episode playback with controls.
"""

import logging
import os
import threading
import time
from typing import Optional, Callable
from enum import Enum

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class AudioPlayer:
    """Audio player for podcast episodes."""

    def __init__(self):
        """Initialize audio player."""
        self.current_file: Optional[str] = None
        self.state = PlaybackState.STOPPED
        self.speed = 1.0
        self.volume = 0.7
        self.position = 0.0  # Current position in seconds
        self.duration = 0.0  # Total duration in seconds
        self.update_callback: Optional[Callable] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = False

        if not PYGAME_AVAILABLE:
            logger.warning("pygame not available - audio playback disabled")

    @staticmethod
    def is_available() -> bool:
        """Check if audio playback is available."""
        return PYGAME_AVAILABLE

    def load(self, file_path: str) -> bool:
        """
        Load an audio file.

        Args:
            file_path: Path to audio file

        Returns:
            True if loaded successfully
        """
        if not PYGAME_AVAILABLE:
            logger.error("pygame not available")
            return False

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        try:
            # Stop current playback
            self.stop()

            # Load new file
            pygame.mixer.music.load(file_path)
            self.current_file = file_path
            self.state = PlaybackState.STOPPED
            self.position = 0.0

            # Try to get duration (this is approximate with pygame)
            # For more accurate duration, we'd need mutagen or similar
            self.duration = self._estimate_duration(file_path)

            pygame.mixer.music.set_volume(self.volume)

            logger.info(f"Loaded audio file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load audio file: {e}")
            return False

    def play(self) -> bool:
        """
        Start or resume playback.

        Returns:
            True if playback started
        """
        if not PYGAME_AVAILABLE or not self.current_file:
            return False

        try:
            if self.state == PlaybackState.PAUSED:
                pygame.mixer.music.unpause()
            else:
                pygame.mixer.music.play(start=self.position)

            self.state = PlaybackState.PLAYING
            self._start_monitoring()
            logger.info("Playback started")
            return True

        except Exception as e:
            logger.error(f"Failed to start playback: {e}")
            return False

    def pause(self) -> bool:
        """
        Pause playback.

        Returns:
            True if paused
        """
        if not PYGAME_AVAILABLE or self.state != PlaybackState.PLAYING:
            return False

        try:
            pygame.mixer.music.pause()
            self.state = PlaybackState.PAUSED
            logger.info("Playback paused")
            return True

        except Exception as e:
            logger.error(f"Failed to pause: {e}")
            return False

    def stop(self) -> bool:
        """
        Stop playback.

        Returns:
            True if stopped
        """
        if not PYGAME_AVAILABLE:
            return False

        try:
            self._stop_monitoring = True
            if self._monitor_thread:
                self._monitor_thread.join(timeout=1.0)

            pygame.mixer.music.stop()
            self.state = PlaybackState.STOPPED
            self.position = 0.0
            logger.info("Playback stopped")
            return True

        except Exception as e:
            logger.error(f"Failed to stop: {e}")
            return False

    def seek(self, position: float) -> bool:
        """
        Seek to position in seconds.

        Args:
            position: Position in seconds

        Returns:
            True if seek successful
        """
        if not PYGAME_AVAILABLE or not self.current_file:
            return False

        try:
            # pygame doesn't support seeking easily
            # We need to stop and restart from position
            was_playing = self.state == PlaybackState.PLAYING

            self.stop()
            self.position = max(0.0, min(position, self.duration))

            if was_playing:
                self.play()

            logger.info(f"Seeked to {self.position:.1f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to seek: {e}")
            return False

    def set_volume(self, volume: float) -> bool:
        """
        Set volume (0.0 to 1.0).

        Args:
            volume: Volume level

        Returns:
            True if volume set
        """
        if not PYGAME_AVAILABLE:
            return False

        try:
            self.volume = max(0.0, min(1.0, volume))
            pygame.mixer.music.set_volume(self.volume)
            return True

        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

    def set_speed(self, speed: float) -> bool:
        """
        Set playback speed.

        Note: pygame doesn't support variable speed playback.
        This is a placeholder for potential future implementation
        using a different library (like pydub + sounddevice).

        Args:
            speed: Playback speed (0.5 to 2.0)

        Returns:
            False (not implemented in pygame)
        """
        self.speed = max(0.5, min(2.0, speed))
        logger.warning("Speed adjustment not supported with pygame")
        return False

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if self.state == PlaybackState.PLAYING and PYGAME_AVAILABLE:
            # pygame.mixer.music.get_pos() returns milliseconds since start
            # but it's not accurate for total position
            try:
                ms = pygame.mixer.music.get_pos()
                if ms >= 0:
                    return self.position + (ms / 1000.0)
            except:
                pass
        return self.position

    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.duration

    def get_state(self) -> PlaybackState:
        """Get current playback state."""
        return self.state

    def set_update_callback(self, callback: Callable):
        """
        Set callback for position updates.

        Args:
            callback: Function to call with (position, duration)
        """
        self.update_callback = callback

    def _start_monitoring(self):
        """Start monitoring thread for playback position."""
        self._stop_monitoring = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
        self._monitor_thread.start()

    def _monitor_playback(self):
        """Monitor playback and update position."""
        while not self._stop_monitoring and self.state == PlaybackState.PLAYING:
            try:
                if not pygame.mixer.music.get_busy():
                    # Playback finished
                    self.state = PlaybackState.STOPPED
                    self.position = 0.0
                    if self.update_callback:
                        self.update_callback(0.0, self.duration)
                    break

                # Update position
                current_pos = self.get_position()
                if self.update_callback:
                    self.update_callback(current_pos, self.duration)

                time.sleep(0.5)  # Update every 500ms

            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                break

    def _estimate_duration(self, file_path: str) -> float:
        """
        Estimate audio duration.

        For now, returns 0. For actual duration, would need mutagen library.

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds (or 0 if unknown)
        """
        # Try to use mutagen if available
        try:
            from mutagen import File
            audio = File(file_path)
            if audio and hasattr(audio.info, 'length'):
                return audio.info.length
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Could not get duration: {e}")

        return 0.0  # Unknown duration

    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.quit()
            except:
                pass


def check_dependencies():
    """Check if required dependencies are installed."""
    if not PYGAME_AVAILABLE:
        print("❌ pygame is not installed")
        print("\nTo install pygame, run:")
        print("  pip install pygame")
        print("\nOr on some systems:")
        print("  pip3 install pygame")
        print("\nOptional (for accurate duration info):")
        print("  pip install mutagen")
        return False

    print("✓ pygame is installed")

    # Check for mutagen
    try:
        import mutagen
        print("✓ mutagen is installed (for duration info)")
    except ImportError:
        print("⚠️  mutagen not installed (duration info will be limited)")
        print("  To install: pip install mutagen")

    return True


if __name__ == "__main__":
    # Test audio player
    check_dependencies()

    if PYGAME_AVAILABLE:
        print("\nAudio player initialized successfully")
        print("Ready for podcast playback!")
    else:
        print("\nAudio player unavailable - install pygame")
