"""
Audio Player for RSS Reader V3
Handles podcast episode playback with controls.
Supports pygame and Windows MCI (Media Control Interface) backends.
"""

import logging
import os
import sys
import threading
import time
from typing import Optional, Callable
from enum import Enum

# Determine available audio backend
_BACKEND = None

try:
    import pygame
    pygame.mixer.init()
    _BACKEND = 'pygame'
except Exception:
    pass

if _BACKEND is None and sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.winmm
        _BACKEND = 'mci'
    except Exception:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class _MCIPlayer:
    """Windows MCI backend for audio playback."""

    _alias = "feedmind_audio"

    def __init__(self):
        self._winmm = ctypes.windll.winmm
        self._loaded = False

    def _send(self, command: str) -> tuple:
        """Send MCI command string. Returns (error_code, response_string)."""
        buf = ctypes.create_unicode_buffer(255)
        err = self._winmm.mciSendStringW(command, buf, 254, 0)
        return err, buf.value

    def load(self, file_path: str) -> bool:
        """Open an audio file via MCI."""
        self.close()
        # mpegvideo type supports mp3, wav, wma, and more
        err, _ = self._send(f'open "{file_path}" type mpegvideo alias {self._alias}')
        if err:
            # Retry without explicit type for other formats
            err, _ = self._send(f'open "{file_path}" alias {self._alias}')
        self._loaded = err == 0
        if self._loaded:
            self._send(f'set {self._alias} time format milliseconds')
        return self._loaded

    def play(self, start_ms: int = 0) -> bool:
        if not self._loaded:
            return False
        if start_ms > 0:
            err, _ = self._send(f'play {self._alias} from {start_ms}')
        else:
            err, _ = self._send(f'play {self._alias}')
        return err == 0

    def pause(self) -> bool:
        err, _ = self._send(f'pause {self._alias}')
        return err == 0

    def unpause(self) -> bool:
        err, _ = self._send(f'resume {self._alias}')
        return err == 0

    def stop(self) -> bool:
        err, _ = self._send(f'stop {self._alias}')
        return err == 0

    def close(self):
        if self._loaded:
            self._send(f'close {self._alias}')
            self._loaded = False

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        vol = int(max(0, min(1000, volume * 1000)))
        self._send(f'setaudio {self._alias} volume to {vol}')

    def get_position_ms(self) -> int:
        """Get current position in milliseconds."""
        err, val = self._send(f'status {self._alias} position')
        if err == 0 and val.isdigit():
            return int(val)
        return 0

    def get_length_ms(self) -> int:
        """Get total length in milliseconds."""
        err, val = self._send(f'status {self._alias} length')
        if err == 0 and val.isdigit():
            return int(val)
        return 0

    def is_playing(self) -> bool:
        """Check if currently playing."""
        err, val = self._send(f'status {self._alias} mode')
        if err == 0:
            return val.strip().lower() == "playing"
        return False


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
        self._mci: Optional[_MCIPlayer] = None

        if _BACKEND == 'mci':
            self._mci = _MCIPlayer()

        if _BACKEND is None:
            logger.warning("pygame not available - audio playback disabled")
        else:
            logger.info(f"Audio backend: {_BACKEND}")

    @staticmethod
    def is_available() -> bool:
        """Check if audio playback is available."""
        return _BACKEND is not None

    def load(self, file_path: str) -> bool:
        """
        Load an audio file.

        Args:
            file_path: Path to audio file

        Returns:
            True if loaded successfully
        """
        if _BACKEND is None:
            logger.error("No audio backend available")
            return False

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        try:
            # Stop current playback
            self.stop()

            if _BACKEND == 'pygame':
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.set_volume(self.volume)
            elif _BACKEND == 'mci':
                if not self._mci.load(file_path):
                    logger.error(f"MCI failed to load: {file_path}")
                    return False
                self._mci.set_volume(self.volume)

            self.current_file = file_path
            self.state = PlaybackState.STOPPED
            self.position = 0.0
            self.duration = self._estimate_duration(file_path)

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
        if _BACKEND is None or not self.current_file:
            return False

        try:
            if _BACKEND == 'pygame':
                if self.state == PlaybackState.PAUSED:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.play(start=self.position)
            elif _BACKEND == 'mci':
                if self.state == PlaybackState.PAUSED:
                    self._mci.unpause()
                else:
                    self._mci.play(start_ms=int(self.position * 1000))

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
        if _BACKEND is None or self.state != PlaybackState.PLAYING:
            return False

        try:
            if _BACKEND == 'pygame':
                pygame.mixer.music.pause()
            elif _BACKEND == 'mci':
                self._mci.pause()

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
        if _BACKEND is None:
            return False

        try:
            self._stop_monitoring = True
            if self._monitor_thread:
                self._monitor_thread.join(timeout=1.0)

            if _BACKEND == 'pygame':
                pygame.mixer.music.stop()
            elif _BACKEND == 'mci':
                self._mci.stop()

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
        if _BACKEND is None or not self.current_file:
            return False

        try:
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
        if _BACKEND is None:
            return False

        try:
            self.volume = max(0.0, min(1.0, volume))

            if _BACKEND == 'pygame':
                pygame.mixer.music.set_volume(self.volume)
            elif _BACKEND == 'mci' and self._mci:
                self._mci.set_volume(self.volume)

            return True

        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False

    def set_speed(self, speed: float) -> bool:
        """
        Set playback speed.

        Note: Neither pygame nor MCI support variable speed playback.

        Args:
            speed: Playback speed (0.5 to 2.0)

        Returns:
            False (not implemented)
        """
        self.speed = max(0.5, min(2.0, speed))
        logger.warning("Speed adjustment not supported")
        return False

    def get_position(self) -> float:
        """Get current playback position in seconds."""
        if self.state == PlaybackState.PLAYING and _BACKEND is not None:
            try:
                if _BACKEND == 'pygame':
                    ms = pygame.mixer.music.get_pos()
                    if ms >= 0:
                        return self.position + (ms / 1000.0)
                elif _BACKEND == 'mci' and self._mci:
                    return self._mci.get_position_ms() / 1000.0
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
                busy = False
                if _BACKEND == 'pygame':
                    busy = pygame.mixer.music.get_busy()
                elif _BACKEND == 'mci' and self._mci:
                    busy = self._mci.is_playing()

                if not busy:
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

        Args:
            file_path: Path to audio file

        Returns:
            Duration in seconds (or 0 if unknown)
        """
        # MCI can report duration directly
        if _BACKEND == 'mci' and self._mci:
            length_ms = self._mci.get_length_ms()
            if length_ms > 0:
                return length_ms / 1000.0

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
        if _BACKEND == 'pygame':
            try:
                pygame.mixer.quit()
            except:
                pass
        elif _BACKEND == 'mci' and self._mci:
            self._mci.close()


def check_dependencies():
    """Check if required dependencies are installed."""
    if _BACKEND == 'pygame':
        print("✓ Audio backend: pygame")
    elif _BACKEND == 'mci':
        print("✓ Audio backend: Windows MCI (built-in)")
    else:
        print("✗ No audio backend available")
        print("\nTo install pygame, run:")
        print("  pip install pygame-ce")
        print("\nOptional (for accurate duration info):")
        print("  pip install mutagen")
        return False

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

    if _BACKEND is not None:
        print(f"\nAudio player initialized successfully (backend: {_BACKEND})")
        print("Ready for podcast playback!")
    else:
        print("\nAudio player unavailable - install pygame-ce")
