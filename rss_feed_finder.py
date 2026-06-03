"""
RSS Feed Finder - Auto-discover RSS/Atom feeds from website URLs

This module helps users find RSS feed URLs from regular website URLs by:
1. Parsing HTML for auto-discovery <link> tags
2. Trying common RSS feed URL patterns
3. Validating discovered feeds
"""

import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from urllib.request import Request
from html.parser import HTMLParser

from rss_core import safe_urlopen, read_capped


class FeedLinkParser(HTMLParser):
    """HTML parser to extract RSS/Atom feed links from <link> tags."""

    def __init__(self):
        super().__init__()
        self.feeds = []

    def handle_starttag(self, tag, attrs):
        """Extract feed links from <link> tags."""
        if tag.lower() == 'link':
            attrs_dict = dict(attrs)
            rel = attrs_dict.get('rel', '').lower()
            type_attr = attrs_dict.get('type', '').lower()
            href = attrs_dict.get('href', '')
            title = attrs_dict.get('title', '')

            # Check if it's an RSS/Atom feed link
            if rel == 'alternate' and href:
                if 'rss' in type_attr or 'atom' in type_attr or 'xml' in type_attr:
                    feed_type = 'RSS' if 'rss' in type_attr else 'Atom' if 'atom' in type_attr else 'XML'
                    self.feeds.append({
                        'url': href,
                        'title': title or 'Untitled Feed',
                        'type': feed_type
                    })


class RSSFeedFinder:
    """Find RSS/Atom feeds from website URLs."""

    # Common RSS feed URL patterns to try
    COMMON_PATTERNS = [
        '/feed/',
        '/feed',
        '/rss/',
        '/rss',
        '/rss.xml',
        '/feed.xml',
        '/atom.xml',
        '/index.xml',
        '/feeds/posts/default',  # Blogger
        '?feed=rss2',  # WordPress
        '?feed=atom',  # WordPress
    ]

    def __init__(self, timeout: int = 10):
        """
        Initialize RSS feed finder.

        Args:
            timeout: Timeout for HTTP requests in seconds
        """
        self.timeout = timeout

    def find_feeds(self, url: str) -> List[Dict[str, str]]:
        """
        Find all RSS/Atom feeds for a given website URL.

        Args:
            url: Website URL to search for feeds

        Returns:
            List of dicts containing feed info: {'url', 'title', 'type'}

        Example:
            finder = RSSFeedFinder()
            feeds = finder.find_feeds('https://techcrunch.com')
            # Returns: [{'url': 'https://techcrunch.com/feed/', 'title': 'TechCrunch', 'type': 'RSS'}]
        """
        feeds = []

        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            # Step 1: Try auto-discovery (parse HTML for <link> tags)
            discovered_feeds = self._discover_feeds_from_html(url)
            if discovered_feeds:
                feeds.extend(discovered_feeds)

            # Step 2: Try common patterns if no feeds found
            if not feeds:
                pattern_feeds = self._try_common_patterns(url)
                feeds.extend(pattern_feeds)

        except Exception as e:
            # If all else fails, return empty list with error info
            return [{'url': '', 'title': f'Error: {str(e)}', 'type': 'Error'}]

        # Remove duplicates
        seen_urls = set()
        unique_feeds = []
        for feed in feeds:
            if feed['url'] not in seen_urls:
                seen_urls.add(feed['url'])
                unique_feeds.append(feed)

        return unique_feeds

    def _discover_feeds_from_html(self, url: str) -> List[Dict[str, str]]:
        """
        Parse HTML page to find auto-discovery feed links.

        Args:
            url: Website URL to parse

        Returns:
            List of discovered feeds
        """
        try:
            # Fetch HTML
            headers = {
                'User-Agent': 'Mozilla/5.0 (FeedMind RSS Reader; +https://github.com/feedmind)'
            }
            req = Request(url, headers=headers)

            with safe_urlopen(req, timeout=self.timeout) as response:
                html = read_capped(response).decode('utf-8', errors='ignore')

            # Parse for feed links
            parser = FeedLinkParser()
            parser.feed(html)

            # Convert relative URLs to absolute
            base_url = url
            feeds = []
            for feed in parser.feeds:
                absolute_url = urljoin(base_url, feed['url'])
                feeds.append({
                    'url': absolute_url,
                    'title': feed['title'],
                    'type': feed['type']
                })

            return feeds

        except Exception as e:
            # Return empty list if HTML parsing fails
            return []

    def _try_common_patterns(self, url: str) -> List[Dict[str, str]]:
        """
        Try common RSS feed URL patterns.

        Args:
            url: Base website URL

        Returns:
            List of valid feeds found
        """
        feeds = []
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        for pattern in self.COMMON_PATTERNS:
            feed_url = urljoin(base_url, pattern)

            # Check if this URL is valid
            if self._validate_feed_url(feed_url):
                # Extract site name from URL
                site_name = parsed_url.netloc.replace('www.', '').split('.')[0].title()
                feeds.append({
                    'url': feed_url,
                    'title': f'{site_name} Feed',
                    'type': 'RSS/Atom'
                })

        return feeds

    def _validate_feed_url(self, url: str) -> bool:
        """
        Check if a URL is a valid RSS/Atom feed.

        Args:
            url: Feed URL to validate

        Returns:
            True if valid feed, False otherwise
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (FeedMind RSS Reader)'
            }
            req = Request(url, headers=headers)

            with safe_urlopen(req, timeout=5) as response:
                # Read first 1000 bytes to check for RSS/Atom markers
                content = response.read(1000).decode('utf-8', errors='ignore')

                # Check for RSS/Atom indicators
                if any(marker in content.lower() for marker in ['<rss', '<feed', '<atom', '<?xml']):
                    return True

        except Exception:
            pass

        return False


def find_feeds_for_url(url: str) -> List[Dict[str, str]]:
    """
    Convenience function to find feeds for a URL.

    Args:
        url: Website URL

    Returns:
        List of found feeds

    Example:
        feeds = find_feeds_for_url('https://nasa.gov')
        for feed in feeds:
            print(f"{feed['title']}: {feed['url']}")
    """
    finder = RSSFeedFinder()
    return finder.find_feeds(url)


if __name__ == "__main__":
    # Test the feed finder
    import sys

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://techcrunch.com"

    print(f"Finding RSS feeds for: {test_url}")
    print("-" * 60)

    finder = RSSFeedFinder()
    feeds = finder.find_feeds(test_url)

    if feeds:
        print(f"Found {len(feeds)} feed(s):\n")
        for i, feed in enumerate(feeds, 1):
            print(f"{i}. {feed['title']} ({feed['type']})")
            print(f"   URL: {feed['url']}\n")
    else:
        print("No feeds found.")
