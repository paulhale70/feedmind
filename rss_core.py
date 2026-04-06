"""
RSS Reader Core Module
Handles fetching and parsing RSS feeds from URLs using built-in XML parser.
"""

import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RSSFeed:
    """Represents a single RSS feed entry/article."""

    def __init__(self, title: str, link: str, description: str,
                 published: Optional[str] = None, feed_url: str = "",
                 feed_title: str = "", audio_url: Optional[str] = None,
                 audio_type: Optional[str] = None, audio_length: Optional[int] = None,
                 duration_seconds: int = 0):
        self.title = title
        self.link = link
        self.description = description
        self.published = published
        self.feed_url = feed_url
        self.feed_title = feed_title  # Title of the feed itself
        # Podcast/audio enclosure data
        self.audio_url = audio_url
        self.audio_type = audio_type
        self.audio_length = audio_length  # File size in bytes
        self.duration_seconds = duration_seconds  # Duration in seconds

    def __repr__(self):
        return f"RSSFeed(title='{self.title}', link='{self.link}')"


class RSSFetcher:
    """Fetches and parses RSS feeds from URLs using built-in XML parser."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Unescape HTML entities
        text = html.unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse iTunes duration to seconds.

        Supports formats: HH:MM:SS, MM:SS, or just seconds.

        Args:
            duration_str: Duration string

        Returns:
            Duration in seconds
        """
        if not duration_str:
            return 0

        duration_str = duration_str.strip()

        # Try parsing as seconds first
        try:
            return int(duration_str)
        except ValueError:
            pass

        # Try parsing as HH:MM:SS or MM:SS
        try:
            parts = duration_str.split(':')
            if len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
        except ValueError:
            pass

        return 0

    def _parse_rss(self, xml_content: bytes, url: str) -> list[RSSFeed]:
        """Parse RSS 2.0 format."""
        try:
            root = ET.fromstring(xml_content)
            articles = []

            # Extract feed title from channel
            channel = root.find('.//channel')
            feed_title = ""
            if channel is not None:
                feed_title = channel.findtext('title', url)

            # Find all item elements
            for item in root.findall('.//item'):
                title = item.findtext('title', 'No Title')
                link = item.findtext('link', '')
                description = item.findtext('description', '')
                pub_date = item.findtext('pubDate', '')

                # Clean description from HTML
                description = self._clean_html(description)

                # Extract audio enclosure (for podcasts)
                audio_url = None
                audio_type = None
                audio_length = None
                duration_seconds = 0

                enclosure = item.find('enclosure')
                if enclosure is not None:
                    audio_url = enclosure.get('url')
                    audio_type = enclosure.get('type')
                    length_str = enclosure.get('length', '0')
                    try:
                        audio_length = int(length_str) if length_str else 0
                    except ValueError:
                        audio_length = 0

                # Try to extract iTunes duration (format: HH:MM:SS or seconds)
                itunes_ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}
                duration_elem = item.find('itunes:duration', itunes_ns)
                if duration_elem is not None and duration_elem.text:
                    duration_seconds = self._parse_duration(duration_elem.text)

                articles.append(RSSFeed(
                    title=title,
                    link=link,
                    description=description,
                    published=pub_date,
                    feed_url=url,
                    feed_title=feed_title,
                    audio_url=audio_url,
                    audio_type=audio_type,
                    audio_length=audio_length,
                    duration_seconds=duration_seconds
                ))

            return articles
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS XML: {e}")
            raise

    def _parse_atom(self, xml_content: bytes, url: str) -> list[RSSFeed]:
        """Parse Atom format."""
        try:
            root = ET.fromstring(xml_content)
            articles = []

            # Atom uses namespaces
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}

            # Extract feed title
            feed_title_elem = root.find('title')
            if feed_title_elem is None:
                feed_title_elem = root.find('atom:title', namespace)
            feed_title = feed_title_elem.text if feed_title_elem is not None else url

            # Try without namespace first, then with
            entries = root.findall('.//entry')
            if not entries:
                entries = root.findall('.//atom:entry', namespace)

            for entry in entries:
                # Try with and without namespace
                title_elem = entry.find('title')
                if title_elem is None:
                    title_elem = entry.find('atom:title', namespace)
                title = title_elem.text if title_elem is not None else 'No Title'

                link_elem = entry.find('link')
                if link_elem is None:
                    link_elem = entry.find('atom:link', namespace)
                link = link_elem.get('href', '') if link_elem is not None else ''

                # Try content, then summary
                content_elem = entry.find('content')
                if content_elem is None:
                    content_elem = entry.find('atom:content', namespace)
                if content_elem is None:
                    content_elem = entry.find('summary')
                if content_elem is None:
                    content_elem = entry.find('atom:summary', namespace)
                description = content_elem.text if content_elem is not None else ''

                published_elem = entry.find('published')
                if published_elem is None:
                    published_elem = entry.find('atom:published', namespace)
                if published_elem is None:
                    published_elem = entry.find('updated')
                if published_elem is None:
                    published_elem = entry.find('atom:updated', namespace)
                published = published_elem.text if published_elem is not None else ''

                # Clean description from HTML
                description = self._clean_html(description)

                # Extract audio enclosure (for podcasts in Atom)
                audio_url = None
                audio_type = None
                audio_length = None
                duration_seconds = 0

                # Check for enclosure link
                for link_el in entry.findall('link') + entry.findall('atom:link', namespace):
                    rel = link_el.get('rel', '')
                    if rel == 'enclosure':
                        audio_url = link_el.get('href')
                        audio_type = link_el.get('type')
                        length_str = link_el.get('length', '0')
                        try:
                            audio_length = int(length_str) if length_str else 0
                        except ValueError:
                            audio_length = 0
                        break

                articles.append(RSSFeed(
                    title=title,
                    link=link,
                    description=description,
                    published=published,
                    feed_url=url,
                    feed_title=feed_title,
                    audio_url=audio_url,
                    audio_type=audio_type,
                    audio_length=audio_length,
                    duration_seconds=duration_seconds
                ))

            return articles
        except ET.ParseError as e:
            logger.error(f"Failed to parse Atom XML: {e}")
            raise

    def fetch_feed(self, url: str) -> list[RSSFeed]:
        """
        Fetch and parse an RSS or Atom feed from the given URL.

        Args:
            url: The URL of the RSS/Atom feed

        Returns:
            List of RSSFeed objects containing the parsed articles
        """
        try:
            logger.info(f"Fetching RSS feed from: {url}")

            # Fetch the XML content
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=self.timeout) as response:
                xml_content = response.read()

            # Detect feed type and parse accordingly
            try:
                # Try to detect if it's Atom or RSS
                if b'<feed' in xml_content[:500] or b'xmlns="http://www.w3.org/2005/Atom"' in xml_content[:500]:
                    articles = self._parse_atom(xml_content, url)
                else:
                    articles = self._parse_rss(xml_content, url)

                logger.info(f"Successfully fetched {len(articles)} articles from {url}")
                return articles

            except ET.ParseError:
                # If parsing fails, try the other format
                logger.warning(f"First parse attempt failed, trying alternate format")
                try:
                    if b'<feed' in xml_content[:500]:
                        articles = self._parse_rss(xml_content, url)
                    else:
                        articles = self._parse_atom(xml_content, url)
                    logger.info(f"Successfully fetched {len(articles)} articles from {url}")
                    return articles
                except Exception as e:
                    logger.error(f"Both parse attempts failed: {e}")
                    raise

        except (URLError, HTTPError) as e:
            logger.error(f"Failed to fetch feed from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing feed from {url}: {e}")
            raise

    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is accessible.

        Args:
            url: The URL to validate

        Returns:
            True if the URL is accessible, False otherwise
        """
        try:
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=self.timeout) as response:
                return response.status < 400
        except Exception:
            return False
