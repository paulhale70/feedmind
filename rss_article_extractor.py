"""
Full-Text Article Extractor for RSS Reader V3
Extracts complete article content from web pages.
"""

import logging
from typing import Optional, Dict
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

try:
    import trafilatura
    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArticleExtractor:
    """Extract full-text content from article URLs."""

    def __init__(self, timeout: int = 30, preferred_method: str = "auto"):
        """
        Initialize article extractor.

        Args:
            timeout: Request timeout in seconds
            preferred_method: "newspaper", "trafilatura", or "auto"
        """
        self.timeout = timeout
        self.preferred_method = preferred_method

    @staticmethod
    def is_available() -> bool:
        """Check if any extraction library is available."""
        return NEWSPAPER_AVAILABLE or TRAFILATURA_AVAILABLE

    @staticmethod
    def get_available_methods() -> list[str]:
        """Get list of available extraction methods."""
        methods = []
        if NEWSPAPER_AVAILABLE:
            methods.append("newspaper")
        if TRAFILATURA_AVAILABLE:
            methods.append("trafilatura")
        return methods

    def extract(self, url: str, use_cache: bool = True) -> Optional[Dict]:
        """
        Extract full article content from URL.

        Args:
            url: URL of the article
            use_cache: Whether to use cached results (not implemented yet)

        Returns:
            Dictionary with article data or None on failure:
            {
                'title': str,
                'text': str,
                'authors': list,
                'publish_date': str,
                'top_image': str,
                'method': str  # Which method was used
            }
        """
        if not self.is_available():
            logger.error("No extraction library available")
            return None

        # Try preferred method first
        if self.preferred_method == "newspaper" and NEWSPAPER_AVAILABLE:
            result = self._extract_newspaper(url)
            if result:
                return result

        if self.preferred_method == "trafilatura" and TRAFILATURA_AVAILABLE:
            result = self._extract_trafilatura(url)
            if result:
                return result

        # Auto mode - try newspaper first, then trafilatura
        if NEWSPAPER_AVAILABLE:
            result = self._extract_newspaper(url)
            if result:
                return result

        if TRAFILATURA_AVAILABLE:
            result = self._extract_trafilatura(url)
            if result:
                return result

        return None

    def _extract_newspaper(self, url: str) -> Optional[Dict]:
        """
        Extract article using newspaper3k.

        Args:
            url: Article URL

        Returns:
            Extracted article data or None
        """
        if not NEWSPAPER_AVAILABLE:
            return None

        try:
            logger.info(f"Extracting article with newspaper: {url}")

            # Download and parse article
            article = Article(url)
            article.download()
            article.parse()

            # Get publish date
            publish_date = ""
            if article.publish_date:
                publish_date = article.publish_date.isoformat()

            result = {
                'title': article.title or "",
                'text': article.text or "",
                'authors': article.authors or [],
                'publish_date': publish_date,
                'top_image': article.top_image or "",
                'method': 'newspaper'
            }

            logger.info(f"Successfully extracted {len(result['text'])} characters")
            return result

        except Exception as e:
            logger.error(f"Newspaper extraction failed: {e}")
            return None

    def _extract_trafilatura(self, url: str) -> Optional[Dict]:
        """
        Extract article using trafilatura.

        Args:
            url: Article URL

        Returns:
            Extracted article data or None
        """
        if not TRAFILATURA_AVAILABLE:
            return None

        try:
            logger.info(f"Extracting article with trafilatura: {url}")

            # Download page
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=self.timeout) as response:
                html = response.read()

            # Extract text
            text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )

            if not text:
                logger.warning("No text extracted")
                return None

            # Extract metadata
            metadata = trafilatura.extract_metadata(html)

            title = ""
            authors = []
            publish_date = ""

            if metadata:
                title = metadata.title or ""
                if metadata.author:
                    authors = [metadata.author]
                if metadata.date:
                    publish_date = metadata.date

            result = {
                'title': title,
                'text': text,
                'authors': authors,
                'publish_date': publish_date,
                'top_image': "",  # trafilatura doesn't extract images
                'method': 'trafilatura'
            }

            logger.info(f"Successfully extracted {len(result['text'])} characters")
            return result

        except Exception as e:
            logger.error(f"Trafilatura extraction failed: {e}")
            return None

    def extract_batch(self, urls: list[str], max_workers: int = 3) -> Dict[str, Optional[Dict]]:
        """
        Extract multiple articles concurrently.

        Args:
            urls: List of article URLs
            max_workers: Maximum concurrent workers

        Returns:
            Dictionary mapping URLs to extracted data
        """
        import concurrent.futures

        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.extract, url): url
                for url in urls
            }

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as e:
                    logger.error(f"Batch extraction failed for {url}: {e}")
                    results[url] = None

        return results


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Article Extraction Libraries:")
    print("-" * 60)

    if NEWSPAPER_AVAILABLE:
        print("✓ newspaper3k is installed")
    else:
        print("❌ newspaper3k is not installed")
        print("  To install: pip install newspaper3k")

    if TRAFILATURA_AVAILABLE:
        print("✓ trafilatura is installed")
    else:
        print("❌ trafilatura is not installed")
        print("  To install: pip install trafilatura")

    print()

    if not NEWSPAPER_AVAILABLE and not TRAFILATURA_AVAILABLE:
        print("⚠️  No extraction library available")
        print("\nTo enable article extraction, install at least one:")
        print("  pip install newspaper3k    # Recommended")
        print("  pip install trafilatura    # Lightweight alternative")
        return False

    available = ArticleExtractor.get_available_methods()
    print(f"Available methods: {', '.join(available)}")
    return True


if __name__ == "__main__":
    # Test article extraction
    check_dependencies()

    if ArticleExtractor.is_available():
        print("\n" + "=" * 60)
        print("Testing Article Extraction")
        print("=" * 60)

        extractor = ArticleExtractor()

        # Test with a sample article
        test_url = "https://www.bbc.com/news"
        print(f"\nExtracting from: {test_url}")

        result = extractor.extract(test_url)

        if result:
            print(f"\n✓ Extraction successful using {result['method']}")
            print(f"  Title: {result['title'][:60]}...")
            print(f"  Text length: {len(result['text'])} characters")
            print(f"  Authors: {', '.join(result['authors']) if result['authors'] else 'None'}")
            print(f"  Date: {result['publish_date'] or 'Unknown'}")
        else:
            print("\n✗ Extraction failed")

    else:
        print("\n⚠️  Cannot test - no extraction library installed")
