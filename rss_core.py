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
                 published: Optional[str] = None, feed_url: str = ""):
        self.title = title
        self.link = link
        self.description = description
        self.published = published
        self.feed_url = feed_url

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

    def _parse_rss(self, xml_content: bytes, url: str) -> list[RSSFeed]:
        """Parse RSS 2.0 format."""
        try:
            root = ET.fromstring(xml_content)
            articles = []

            # Find all item elements
            for item in root.findall('.//item'):
                title = item.findtext('title', 'No Title')
                link = item.findtext('link', '')
                description = item.findtext('description', '')
                pub_date = item.findtext('pubDate', '')

                # Clean description from HTML
                description = self._clean_html(description)

                articles.append(RSSFeed(
                    title=title,
                    link=link,
                    description=description,
                    published=pub_date,
                    feed_url=url
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

                articles.append(RSSFeed(
                    title=title,
                    link=link,
                    description=description,
                    published=published,
                    feed_url=url
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
