"""
Test PDF export and desktop notifications features.
"""

import os
import sys
# --- bootstrap: make repo-root modules importable and emoji output safe ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass
# --- end bootstrap ---
from rss_pdf_exporter import PDFExporter, check_dependencies as check_pdf_deps
from rss_notifications import NotificationManager, check_dependencies as check_notif_deps


def test_pdf_export():
    """Test PDF export functionality."""
    print("\n" + "=" * 60)
    print("Testing PDF Export...")
    print("=" * 60)

    # Check if available
    if not PDFExporter.is_available():
        print("⚠️  reportlab not installed - PDF export unavailable")
        print("To install: pip install reportlab")
        return False

    print("✓ reportlab is available")

    # Test articles
    test_articles = [
        {
            'title': 'First Test Article',
            'description': 'This is a test article with some description content. It should appear in the PDF with proper formatting.',
            'link': 'https://example.com/article1',
            'pub_date': '2026-01-20T10:00:00'
        },
        {
            'title': 'Second Test Article with HTML &amp; entities',
            'description': 'This article tests HTML entity decoding &lt;tag&gt; and special characters.',
            'link': 'https://example.com/article2',
            'pub_date': '2026-01-20T11:00:00'
        },
        {
            'title': 'Third Article',
            'description': 'Short description.',
            'link': 'https://example.com/article3',
            'pub_date': '2026-01-19'
        }
    ]

    # Test full export
    test_file = "test_articles.pdf"
    try:
        if PDFExporter.export_articles(test_articles, test_file, title="Test RSS Export"):
            print(f"✓ Exported {len(test_articles)} articles to {test_file}")

            # Check file exists and has reasonable size
            if os.path.exists(test_file):
                size = os.path.getsize(test_file)
                if size > 1000:  # At least 1KB
                    print(f"✓ PDF file created ({size} bytes)")
                    os.remove(test_file)
                    success = True
                else:
                    print(f"✗ PDF file too small ({size} bytes)")
                    success = False
            else:
                print("✗ PDF file not found")
                success = False
        else:
            print("✗ PDF export failed")
            success = False

    except Exception as e:
        print(f"✗ PDF export error: {e}")
        success = False

    # Test article list export
    test_list_file = "test_article_list.pdf"
    try:
        if PDFExporter.export_article_list(test_articles, test_list_file, title="Test Article List"):
            print(f"✓ Exported article list to {test_list_file}")
            if os.path.exists(test_list_file):
                os.remove(test_list_file)
        else:
            print("✗ Article list export failed")
    except Exception as e:
        print(f"✗ Article list export error: {e}")

    return success


def test_notifications():
    """Test desktop notifications."""
    print("\n" + "=" * 60)
    print("Testing Desktop Notifications...")
    print("=" * 60)

    # Check if available
    if not NotificationManager.is_available():
        print("⚠️  plyer not installed - notifications unavailable")
        print("To install: pip install plyer")
        return False

    print("✓ plyer is available")

    # Create notification manager
    manager = NotificationManager("RSSreader Test")

    # Test basic notification
    print("\nSending test notification...")
    print("(Check your system notifications)")
    try:
        manager.notify_new_articles("Test Feed", 5, timeout=3)
        print("✓ New articles notification sent")
    except Exception as e:
        print(f"✗ Notification failed: {e}")
        return False

    # Test refresh complete notification
    try:
        manager.notify_refresh_complete(10, 3, timeout=3)
        print("✓ Refresh complete notification sent")
    except Exception as e:
        print(f"✗ Refresh notification failed: {e}")

    # Test custom notification
    try:
        manager.notify_custom("Test Title", "Test message content", timeout=3)
        print("✓ Custom notification sent")
    except Exception as e:
        print(f"✗ Custom notification failed: {e}")

    # Test enable/disable
    manager.set_enabled(False)
    if not manager.is_enabled():
        print("✓ Notifications disabled successfully")
    manager.set_enabled(True)
    if manager.is_enabled():
        print("✓ Notifications re-enabled successfully")

    return True


def test_integration():
    """Test integration between modules."""
    print("\n" + "=" * 60)
    print("Testing Integration...")
    print("=" * 60)

    # Test that both modules can be imported together
    try:
        from rss_database_v2 import RSSDatabase
        from rss_pdf_exporter import PDFExporter
        from rss_notifications import NotificationManager
        print("✓ All modules import successfully together")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    # Test availability checks
    pdf_available = PDFExporter.is_available()
    notif_available = NotificationManager.is_available()

    print(f"✓ PDF Export Available: {'Yes' if pdf_available else 'No'}")
    print(f"✓ Notifications Available: {'Yes' if notif_available else 'No'}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("RSSreaderV2 - PDF & Notifications Feature Tests")
    print("=" * 60)

    print("\n📦 Checking Dependencies...")
    print("-" * 60)

    pdf_deps = check_pdf_deps()
    print()
    notif_deps = check_notif_deps()

    print("\n" + "=" * 60)
    print("Running Tests...")
    print("=" * 60)

    results = {
        "Integration": test_integration(),
        "PDF Export": test_pdf_export() if pdf_deps else False,
        "Desktop Notifications": test_notifications() if notif_deps else False
    }

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        if passed:
            status = "✓ PASS"
        elif passed is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP (dependencies missing)"
        print(f"{test_name:30s} {status}")

    print("=" * 60)

    # Overall result
    passed_tests = sum(1 for r in results.values() if r is True)
    failed_tests = sum(1 for r in results.values() if r is False)
    skipped_tests = sum(1 for r in results.values() if r is None)

    if failed_tests == 0 and passed_tests > 0:
        print("\n🎉 All available tests passed!")
    elif skipped_tests > 0 and failed_tests == 0:
        print(f"\n⚠️  Some features unavailable (install dependencies)")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")

    print("\nNote: PDF export and notifications are OPTIONAL features.")
    print("The app works without them, but they enhance functionality.")
    print("\nTo install optional dependencies:")
    print("  pip install reportlab plyer")
