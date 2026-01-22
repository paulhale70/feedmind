"""
OPML Import/Export Module for RSS Reader
Handles reading and writing OPML subscription files.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OPMLHandler:
    """Handles OPML import and export operations."""

    @staticmethod
    def export_to_opml(feeds: List[Dict], categories: List[Dict], file_path: str) -> bool:
        """
        Export feeds to OPML format.

        Args:
            feeds: List of feed dictionaries with url, title, category_id
            categories: List of category dictionaries with id, name
            file_path: Path to save OPML file

        Returns:
            True if successful
        """
        try:
            # Create OPML structure
            opml = ET.Element('opml', version='2.0')

            # Head section
            head = ET.SubElement(opml, 'head')
            ET.SubElement(head, 'title').text = 'RSS Reader Subscriptions'
            ET.SubElement(head, 'dateCreated').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')
            ET.SubElement(head, 'dateModified').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %Z')

            # Body section
            body = ET.SubElement(opml, 'body')

            # Create category mapping
            category_map = {cat['id']: cat['name'] for cat in categories}
            category_outlines = {}

            # Group feeds by category
            for feed in feeds:
                category_id = feed.get('category_id')
                category_name = category_map.get(category_id, 'Uncategorized')

                # Create category outline if it doesn't exist
                if category_name not in category_outlines:
                    category_outlines[category_name] = ET.SubElement(
                        body, 'outline',
                        text=category_name,
                        title=category_name
                    )

                # Add feed to category
                ET.SubElement(
                    category_outlines[category_name], 'outline',
                    type='rss',
                    text=feed.get('title', feed['url']),
                    title=feed.get('title', feed['url']),
                    xmlUrl=feed['url'],
                    htmlUrl=feed['url']
                )

            # Write to file
            tree = ET.ElementTree(opml)
            ET.indent(tree, space='  ')  # Pretty print
            tree.write(file_path, encoding='utf-8', xml_declaration=True)

            logger.info(f"Exported {len(feeds)} feeds to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export OPML: {e}")
            return False

    @staticmethod
    def import_from_opml(file_path: str) -> Dict[str, List[Dict]]:
        """
        Import feeds from OPML format.

        Args:
            file_path: Path to OPML file

        Returns:
            Dictionary with 'categories' and 'feeds' lists
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            if root.tag != 'opml':
                raise ValueError("Not a valid OPML file")

            categories = []
            feeds = []
            category_map = {}  # Maps category name to internal ID

            # Find body element
            body = root.find('body')
            if body is None:
                raise ValueError("OPML file has no body element")

            def process_outline(outline, parent_category=None):
                """Recursively process outline elements."""
                # Get attributes (case-insensitive)
                attrs = {k.lower(): v for k, v in outline.attrib.items()}

                xml_url = attrs.get('xmlurl') or attrs.get('xmlurl')
                outline_type = attrs.get('type', '').lower()
                title = attrs.get('title') or attrs.get('text', '')

                # If this outline has an xmlUrl, it's a feed
                if xml_url:
                    feeds.append({
                        'url': xml_url,
                        'title': title or xml_url,
                        'category': parent_category
                    })
                    logger.debug(f"Found feed: {title} ({xml_url}) in category: {parent_category}")
                else:
                    # This is a container (category or folder)
                    # Use title or text as category name
                    category_name = title or 'Uncategorized'

                    # Only create category if it has child outlines
                    children = outline.findall('outline')
                    if children:
                        # Add category if not already present
                        if category_name not in category_map:
                            category_map[category_name] = len(categories)
                            categories.append({
                                'name': category_name,
                                'feeds': []
                            })
                            logger.debug(f"Found category: {category_name}")

                        # Process children with this category
                        for child in children:
                            process_outline(child, category_name)

            # Process all top-level outlines
            for outline in body.findall('outline'):
                process_outline(outline)

            logger.info(f"Imported {len(feeds)} feeds and {len(categories)} categories from {file_path}")

            return {
                'categories': categories,
                'feeds': feeds
            }

        except Exception as e:
            logger.error(f"Failed to import OPML: {e}")
            raise


    @staticmethod
    def validate_opml_file(file_path: str) -> bool:
        """
        Validate if a file is a valid OPML file.

        Args:
            file_path: Path to file

        Returns:
            True if valid OPML
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag == 'opml' and root.find('body') is not None
        except Exception:
            return False
