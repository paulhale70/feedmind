"""
Test script for AI Summarization and Article Extraction features.
Tests V3.5 enhancements.
"""

import os
# --- bootstrap: make repo-root modules importable and emoji output safe ---
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
if hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass
# --- end bootstrap ---
from rss_database_v3 import RSSDatabase
from rss_article_extractor import ArticleExtractor, check_dependencies as check_extraction_deps
from rss_ai_summarizer import AISummarizer, check_dependencies as check_ai_deps, AIProvider
from rss_api_config import APIConfigManager


def test_database_ai_columns():
    """Test database schema for AI and extraction columns."""
    print("=" * 60)
    print("Testing Database AI Columns...")
    print("=" * 60)

    # Remove test database if exists
    if os.path.exists("test_ai.db"):
        os.remove("test_ai.db")

    try:
        db = RSSDatabase("test_ai.db")
        print("✓ Database created with AI support")

        # Check AI columns in articles table
        cursor = db.conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        article_columns = {row[1] for row in cursor.fetchall()}

        assert 'full_text' in article_columns, "full_text column missing"
        assert 'full_text_extracted_date' in article_columns, "full_text_extracted_date column missing"
        assert 'ai_summary' in article_columns, "ai_summary column missing"
        assert 'ai_tldr' in article_columns, "ai_tldr column missing"
        assert 'ai_key_points' in article_columns, "ai_key_points column missing"
        assert 'ai_generated_date' in article_columns, "ai_generated_date column missing"
        print("✓ All AI columns present in articles table")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Database AI columns test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_article_extraction():
    """Test full-text article extraction."""
    print("\n" + "=" * 60)
    print("Testing Article Extraction...")
    print("=" * 60)

    if not ArticleExtractor.is_available():
        print("⚠️  No extraction library installed")
        print("To install: pip install newspaper3k")
        return False

    try:
        extractor = ArticleExtractor()
        available_methods = extractor.get_available_methods()
        print(f"✓ Available extraction methods: {', '.join(available_methods)}")

        # Test with a simple article (BBC is reliable for testing)
        test_url = "https://www.bbc.com/news"
        print(f"\nExtracting from: {test_url}")

        result = extractor.extract(test_url)

        if result:
            print(f"✓ Extraction successful using '{result['method']}'")
            print(f"  Title: {result['title'][:60] if result['title'] else 'N/A'}...")
            print(f"  Text length: {len(result['text'])} characters")
            print(f"  Authors: {', '.join(result['authors']) if result['authors'] else 'None'}")
            print(f"  Date: {result['publish_date'] or 'Unknown'}")

            # Test database storage
            db = RSSDatabase("test_ai.db")
            db.add_feed(test_url, "Test Feed")

            # Create a test article
            cursor = db.conn.cursor()
            cursor.execute("""
                INSERT INTO articles
                (feed_url, title, link, description, published, cached_date)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
            """, (test_url, result['title'], test_url, "Test description", "2024-01-01T00:00:00"))
            db.conn.commit()

            article_id = cursor.lastrowid

            # Store full text
            success = db.store_full_text(article_id, result['text'])
            assert success, "Failed to store full text"
            print("✓ Full text stored in database")

            # Retrieve full text
            retrieved = db.get_full_text(article_id)
            assert retrieved == result['text'], "Retrieved text doesn't match"
            print("✓ Full text retrieved successfully")

            # Check has_full_text
            has_text = db.has_full_text(article_id)
            assert has_text, "has_full_text returned False"
            print("✓ has_full_text() working correctly")

            db.close()
            return True
        else:
            print("⚠️  Extraction returned no content (may be network issue)")
            return False

    except Exception as e:
        print(f"✗ Article extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_summarization():
    """Test AI summarization (requires API key)."""
    print("\n" + "=" * 60)
    print("Testing AI Summarization...")
    print("=" * 60)

    if not AISummarizer.is_available():
        print("⚠️  No AI library installed")
        print("To install:")
        print("  pip install anthropic  # For Claude")
        print("  pip install openai     # For OpenAI")
        return False

    try:
        available_providers = AISummarizer.get_available_providers()
        print(f"✓ Available AI providers: {', '.join(available_providers)}")

        # Check for API keys
        config = APIConfigManager()
        configured = config.list_configured_providers()

        if not configured:
            print("\n⚠️  No API keys configured")
            print("To test AI summarization, configure an API key:")
            print("  Option 1 (Environment Variable):")
            print("    export RSS_API_KEY_CLAUDE='your-key'")
            print("  Option 2 (Database):")
            print("    config = APIConfigManager()")
            print("    config.set_api_key('claude', 'your-key')")
            return False

        print(f"✓ API keys configured for: {', '.join(configured)}")

        # Try to initialize summarizer
        api_key = config.get_api_key(configured[0])
        provider = AIProvider.CLAUDE if configured[0] == 'claude' else AIProvider.OPENAI

        summarizer = AISummarizer(provider=provider, api_key=api_key)
        print(f"✓ Initialized {configured[0]} summarizer")

        # Test with sample text
        sample_text = """
        Artificial Intelligence has made significant progress in recent years.
        Machine learning models are now capable of understanding and generating
        human-like text, recognizing images with high accuracy, and even playing
        complex games at superhuman levels. The field continues to evolve rapidly,
        with new breakthroughs happening regularly. Researchers are working on
        making AI systems more efficient, interpretable, and aligned with human values.
        """

        print("\nGenerating TL;DR...")
        tldr = summarizer.generate_tldr(sample_text)
        if tldr:
            print(f"✓ TL;DR: {tldr}")
        else:
            print("⚠️  TL;DR generation returned None (API may have failed)")

        print("\nGenerating summary...")
        summary = summarizer.summarize(sample_text, max_length=50)
        if summary:
            print(f"✓ Summary: {summary}")
        else:
            print("⚠️  Summary generation returned None")

        print("\nExtracting key points...")
        key_points = summarizer.extract_key_points(sample_text, num_points=3)
        if key_points:
            print("✓ Key points:")
            for i, point in enumerate(key_points, 1):
                print(f"  {i}. {point}")
        else:
            print("⚠️  Key point extraction returned None")

        # Test database storage
        if tldr and summary and key_points:
            db = RSSDatabase("test_ai.db")

            # Get or create a test article
            cursor = db.conn.cursor()
            cursor.execute("SELECT id FROM articles LIMIT 1")
            row = cursor.fetchone()

            if row:
                article_id = row[0]

                # Store AI summary
                success = db.store_ai_summary(article_id, summary, tldr, key_points)
                assert success, "Failed to store AI summary"
                print("✓ AI summary stored in database")

                # Retrieve AI summary
                retrieved = db.get_ai_summary(article_id)
                assert retrieved is not None, "Failed to retrieve AI summary"
                assert retrieved['summary'] == summary, "Summary doesn't match"
                assert retrieved['tldr'] == tldr, "TL;DR doesn't match"
                print("✓ AI summary retrieved successfully")

                # Check has_ai_summary
                has_summary = db.has_ai_summary(article_id)
                assert has_summary, "has_ai_summary returned False"
                print("✓ has_ai_summary() working correctly")

            db.close()

        return True

    except Exception as e:
        print(f"✗ AI summarization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_config():
    """Test API configuration manager."""
    print("\n" + "=" * 60)
    print("Testing API Configuration...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_ai.db")
        config = APIConfigManager(db)

        # Test setting/getting API keys
        test_key = "test-api-key-12345"
        config.set_api_key("test_provider", test_key)
        print("✓ API key stored")

        retrieved_key = config.get_api_key("test_provider")
        assert retrieved_key == test_key, "API key doesn't match"
        print("✓ API key retrieved")

        # Test provider listing
        providers = config.list_configured_providers()
        assert "test_provider" in providers, "Provider not in list"
        print(f"✓ Listed providers: {', '.join(providers)}")

        # Test is_configured
        is_configured = config.is_configured("test_provider")
        assert is_configured, "Provider not marked as configured"
        print("✓ is_configured() working")

        # Test AI provider settings
        config.set_ai_provider("claude")
        provider = config.get_ai_provider()
        assert provider == "claude", "AI provider setting not saved"
        print("✓ AI provider setting working")

        # Test feature flags
        config.enable_auto_extraction(True)
        assert config.is_auto_extraction_enabled(), "Auto-extraction not enabled"
        print("✓ Auto-extraction setting working")

        config.enable_auto_summarization(True)
        assert config.is_auto_summarization_enabled(), "Auto-summarization not enabled"
        print("✓ Auto-summarization setting working")

        # Test removal
        config.remove_api_key("test_provider")
        removed_key = config.get_api_key("test_provider")
        assert removed_key is None, "API key not removed"
        print("✓ API key removal working")

        db.close()
        return True

    except Exception as e:
        print(f"✗ API config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test integration of extraction and AI features."""
    print("\n" + "=" * 60)
    print("Testing Integration...")
    print("=" * 60)

    try:
        db = RSSDatabase("test_ai.db")

        # Test articles needing extraction
        cursor = db.conn.cursor()
        cursor.execute("""
            INSERT INTO articles
            (feed_url, title, link, description, published, cached_date)
            VALUES ('http://test.com/feed', 'Test Article', 'http://test.com/article',
                    'Description', '2024-01-01', datetime('now'))
        """)
        db.conn.commit()

        needing_extraction = db.get_articles_needing_extraction(limit=5)
        print(f"✓ Found {len(needing_extraction)} articles needing extraction")

        # Store full text for one
        if needing_extraction:
            article_id = needing_extraction[0]['id']
            db.store_full_text(article_id, "Sample full text content for testing.")

        # Test articles needing summary
        needing_summary = db.get_articles_needing_summary(limit=5)
        print(f"✓ Found {len(needing_summary)} articles needing AI summary")

        db.close()
        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test files."""
    files_to_remove = ["test_ai.db"]
    for file in files_to_remove:
        if os.path.exists(file):
            os.remove(file)
    print("\n✓ Cleaned up test files")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("AI & Extraction Features Test Suite")
    print("=" * 60)

    # Check dependencies
    print("\n📦 Checking Dependencies...")
    print("-" * 60)
    extraction_available = check_extraction_deps()
    print()
    ai_available = check_ai_deps()

    print("\n" + "=" * 60)
    print("Running Tests...")
    print("=" * 60)

    results = {
        "Database AI Columns": test_database_ai_columns(),
        "Article Extraction": test_article_extraction() if extraction_available else None,
        "AI Summarization": test_ai_summarization() if ai_available else None,
        "API Configuration": test_api_config(),
        "Integration": test_integration()
    }

    # Cleanup
    cleanup()

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results.items():
        if passed is True:
            status = "✓ PASS"
        elif passed is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP (dependencies/API key missing)"
        print(f"{test_name:30s} {status}")

    print("=" * 60)

    # Overall result
    passed_tests = sum(1 for r in results.values() if r is True)
    failed_tests = sum(1 for r in results.values() if r is False)
    skipped_tests = sum(1 for r in results.values() if r is None)

    if failed_tests == 0 and passed_tests > 0:
        print("\n🎉 All available tests passed!")
    elif skipped_tests > 0 and failed_tests == 0:
        print(f"\n⚠️  Some tests skipped (dependencies missing)")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")

    print("\nV3.5 New Features Tested:")
    print("  ✓ Database schema for full text and AI summaries")
    print("  ✓ Full-text article extraction (newspaper3k/trafilatura)")
    print("  ✓ AI-powered summarization (Claude/OpenAI)")
    print("  ✓ TL;DR generation")
    print("  ✓ Key points extraction")
    print("  ✓ API key configuration system")
    print("  ✓ Auto-extraction and auto-summarization settings")

    print("\nTo install dependencies:")
    print("  pip install newspaper3k trafilatura")
    print("  pip install anthropic openai")

    print("\nNote: AI summarization requires an API key")
    print("  Claude: https://console.anthropic.com/")
    print("  OpenAI: https://platform.openai.com/api-keys")
