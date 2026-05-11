"""
Podcast Episode Downloader for RSS Reader V3
Handles downloading podcast episodes with progress tracking.
"""

import logging
import os
import threading
from pathlib import Path
from typing import Optional, Callable
from urllib.request import Request
from urllib.error import URLError, HTTPError

from rss_core import safe_urlopen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PodcastDownloader:
    """Downloads podcast episodes with progress tracking."""

    def __init__(self, download_dir: str = "podcast_downloads"):
        """
        Initialize podcast downloader.

        Args:
            download_dir: Directory to store downloaded episodes
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.active_downloads = {}  # url -> thread

    def download(self, audio_url: str, filename: Optional[str] = None,
                progress_callback: Optional[Callable] = None,
                completion_callback: Optional[Callable] = None) -> bool:
        """
        Download a podcast episode.

        Args:
            audio_url: URL of the audio file
            filename: Optional custom filename (auto-generated if not provided)
            progress_callback: Function to call with (bytes_downloaded, total_bytes)
            completion_callback: Function to call with (success, file_path, error_msg)

        Returns:
            True if download started successfully
        """
        if not audio_url:
            logger.error("No audio URL provided")
            return False

        # Generate filename if not provided
        if not filename:
            filename = self._generate_filename(audio_url)

        file_path = self.download_dir / filename

        # Check if already downloading
        if audio_url in self.active_downloads:
            logger.warning(f"Already downloading: {audio_url}")
            return False

        # Start download in background thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(audio_url, file_path, progress_callback, completion_callback),
            daemon=True
        )
        self.active_downloads[audio_url] = thread
        thread.start()

        return True

    def _download_worker(self, audio_url: str, file_path: Path,
                        progress_callback: Optional[Callable],
                        completion_callback: Optional[Callable]):
        """Worker thread for downloading."""
        try:
            logger.info(f"Starting download: {audio_url}")

            # Open URL (scheme allow-list enforced)
            req = Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
            with safe_urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192

                # Download in chunks
                with open(file_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        # Call progress callback
                        if progress_callback:
                            try:
                                progress_callback(downloaded, total_size)
                            except Exception as e:
                                logger.error(f"Progress callback error: {e}")

            # Download completed successfully
            file_size = file_path.stat().st_size
            logger.info(f"Download completed: {file_path} ({file_size} bytes)")

            if completion_callback:
                try:
                    completion_callback(True, str(file_path), None)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")

        except (URLError, HTTPError) as e:
            error_msg = f"Network error: {e}"
            logger.error(f"Download failed for {audio_url}: {error_msg}")
            if completion_callback:
                try:
                    completion_callback(False, None, error_msg)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"Download failed for {audio_url}: {error_msg}")
            if completion_callback:
                try:
                    completion_callback(False, None, error_msg)
                except Exception as e:
                    logger.error(f"Completion callback error: {e}")

        finally:
            # Remove from active downloads
            if audio_url in self.active_downloads:
                del self.active_downloads[audio_url]

    def _generate_filename(self, audio_url: str) -> str:
        """
        Generate a safe filename from URL.

        Args:
            audio_url: URL of audio file

        Returns:
            Safe filename
        """
        # Extract filename from URL
        parts = audio_url.split('/')
        filename = parts[-1] if parts else 'episode.mp3'

        # Remove query parameters
        if '?' in filename:
            filename = filename.split('?')[0]

        # Ensure it has an extension
        if '.' not in filename:
            filename += '.mp3'

        # Sanitize filename
        filename = self._sanitize_filename(filename)

        # Handle duplicates
        base_path = self.download_dir / filename
        counter = 1
        while base_path.exists():
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{counter}{ext}"
            base_path = self.download_dir / filename
            counter += 1

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        max_length = 200
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            name = name[:max_length - len(ext)]
            filename = name + ext

        return filename

    def is_downloading(self, audio_url: str) -> bool:
        """Check if a URL is currently being downloaded."""
        return audio_url in self.active_downloads

    def get_active_downloads(self) -> list[str]:
        """Get list of currently active download URLs."""
        return list(self.active_downloads.keys())

    def delete_episode(self, file_path: str) -> bool:
        """
        Delete a downloaded episode file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted episode: {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def get_storage_usage(self) -> dict:
        """
        Get storage usage statistics.

        Returns:
            Dictionary with total_size, file_count
        """
        total_size = 0
        file_count = 0

        if self.download_dir.exists():
            for file_path in self.download_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1

        return {
            'total_size': total_size,
            'file_count': file_count,
            'total_size_mb': total_size / (1024 * 1024)
        }


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


if __name__ == "__main__":
    # Test downloader
    print("Podcast downloader initialized")
    downloader = PodcastDownloader()
    print(f"Download directory: {downloader.download_dir}")

    usage = downloader.get_storage_usage()
    print(f"Storage: {format_bytes(usage['total_size'])} in {usage['file_count']} files")
