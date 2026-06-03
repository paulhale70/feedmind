"""
PDF Exporter for RSS Reader V2
Exports articles to PDF format using reportlab.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from xml.sax.saxutils import escape

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.colors import HexColor
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFExporter:
    """Export RSS articles to PDF format."""

    @staticmethod
    def is_available() -> bool:
        """Check if reportlab is available."""
        return REPORTLAB_AVAILABLE

    @staticmethod
    def export_articles(articles: List[Dict], file_path: str,
                       title: str = "RSS Articles Export",
                       page_size=None) -> bool:
        """
        Export articles to PDF.

        Args:
            articles: List of article dictionaries with title, description, link, published
            file_path: Path to save PDF file
            title: Document title
            page_size: Page size (letter or A4)

        Returns:
            True if successful, False otherwise
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab library not installed. Run: pip install reportlab")
            return False

        try:
            # Set default page size
            if page_size is None:
                page_size = letter

            # Create PDF document
            doc = SimpleDocTemplate(
                file_path,
                pagesize=page_size,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )

            # Get styles
            styles = getSampleStyleSheet()

            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=HexColor('#2196F3'),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            article_title_style = ParagraphStyle(
                'ArticleTitle',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=HexColor('#212121'),
                spaceAfter=6,
                spaceBefore=12
            )

            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=HexColor('#757575'),
                spaceAfter=6
            )

            link_style = ParagraphStyle(
                'LinkStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=HexColor('#2196F3'),
                spaceAfter=12
            )

            body_style = ParagraphStyle(
                'BodyStyle',
                parent=styles['Normal'],
                fontSize=11,
                textColor=HexColor('#212121'),
                spaceAfter=20,
                alignment=TA_LEFT
            )

            # Build PDF content
            story = []

            # Title page
            story.append(Paragraph(title, title_style))
            story.append(Paragraph(
                f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
                date_style
            ))
            story.append(Paragraph(f"Total Articles: {len(articles)}", date_style))
            story.append(Spacer(1, 0.5*inch))

            # Add each article
            for i, article in enumerate(articles):
                # Article title
                article_title = PDFExporter._clean_html(article.get('title', 'Untitled'))
                story.append(Paragraph(f"{i+1}. {article_title}", article_title_style))

                # Publication date
                pub_date = article.get('published', 'Unknown date')
                if pub_date and len(pub_date) > 10:
                    pub_date = pub_date[:10]  # Just the date part
                story.append(Paragraph(f"Published: {pub_date}", date_style))

                # Link — escape so a feed link containing quotes or angle
                # brackets can't break reportlab's mini-markup.
                link = article.get('link', '')
                if link:
                    safe_href = escape(link, {'"': '&quot;'})
                    safe_text = escape(link)
                    story.append(Paragraph(f'<link href="{safe_href}">{safe_text}</link>', link_style))

                # Description/content
                description = PDFExporter._clean_html(
                    article.get('description', 'No description available'),
                    max_length=1000)
                story.append(Paragraph(description, body_style))

                # Add separator between articles (but not after the last one)
                if i < len(articles) - 1:
                    story.append(Spacer(1, 0.2*inch))

            # Build PDF
            doc.build(story)
            logger.info(f"Exported {len(articles)} articles to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export PDF: {e}")
            return False

    @staticmethod
    def export_article_list(articles: List[Dict], file_path: str,
                          title: str = "RSS Articles List") -> bool:
        """
        Export a simple list of articles (titles and links only).

        Args:
            articles: List of article dictionaries
            file_path: Path to save PDF file
            title: Document title

        Returns:
            True if successful
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("reportlab library not installed")
            return False

        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=HexColor('#2196F3'),
                spaceAfter=20,
                alignment=TA_CENTER
            )

            item_style = ParagraphStyle(
                'Item',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=8
            )

            story = []
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3*inch))

            for i, article in enumerate(articles):
                title_text = PDFExporter._clean_html(article.get('title', 'Untitled'))
                link = article.get('link', '')

                if link:
                    story.append(Paragraph(
                        f'{i+1}. <link href="{link}">{title_text}</link>',
                        item_style
                    ))
                else:
                    story.append(Paragraph(f'{i+1}. {title_text}', item_style))

            doc.build(story)
            logger.info(f"Exported {len(articles)} article links to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export PDF list: {e}")
            return False

    @staticmethod
    def _clean_html(text: str, max_length: Optional[int] = None) -> str:
        """Strip HTML to plain text and escape it for reportlab's mini-markup.

        reportlab Paragraph interprets a markup subset, so the result is
        XML-escaped last: a stray & or < in feed content would otherwise break
        or mis-render the PDF. Truncation (max_length) happens on the plain
        text *before* escaping so it can't split an entity like &amp;.
        """
        if not text:
            return ""

        import re
        import html as _html
        # Remove script/style/comments, then all remaining tags.
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)

        # Decode entities to plain text and collapse whitespace.
        text = _html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()

        if max_length and len(text) > max_length:
            text = text[:max_length] + "..."

        # Escape so the plain text is safe inside reportlab markup.
        return escape(text)


def check_dependencies():
    """Check if required dependencies are installed."""
    if not REPORTLAB_AVAILABLE:
        print("❌ reportlab is not installed")
        print("\nTo install reportlab, run:")
        print("  pip install reportlab")
        print("\nOr on some systems:")
        print("  pip3 install reportlab")
        return False

    print("✓ reportlab is installed")
    return True


if __name__ == "__main__":
    # Test if dependencies are available
    check_dependencies()

    if REPORTLAB_AVAILABLE:
        # Test export
        test_articles = [
            {
                'title': 'Test Article 1',
                'description': 'This is a test article description.',
                'link': 'https://example.com/article1',
                'published': '2026-01-20'
            },
            {
                'title': 'Test Article 2',
                'description': 'Another test article with some content.',
                'link': 'https://example.com/article2',
                'published': '2026-01-19'
            }
        ]

        if PDFExporter.export_articles(test_articles, "test_export.pdf"):
            print("✓ Test PDF export successful")
            import os
            if os.path.exists("test_export.pdf"):
                os.remove("test_export.pdf")
        else:
            print("✗ Test PDF export failed")
