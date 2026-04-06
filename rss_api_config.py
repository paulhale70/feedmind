"""
API Configuration Manager for RSS Reader V3
Secure storage of API keys and configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
from rss_database_v3 import RSSDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIConfigManager:
    """Manage API keys and configuration."""

    def __init__(self, db: Optional[RSSDatabase] = None):
        """
        Initialize API config manager.

        Args:
            db: Database instance (will create if not provided)
        """
        self.db = db
        if not self.db:
            self.db = RSSDatabase()

    def set_api_key(self, provider: str, api_key: str) -> bool:
        """
        Store an API key.

        Args:
            provider: Provider name (e.g., 'claude', 'openai')
            api_key: The API key

        Returns:
            True if successful
        """
        key_name = f"api_key_{provider}"
        self.db.set_setting(key_name, api_key)
        logger.info(f"Stored API key for {provider}")
        return True

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Retrieve an API key.

        Args:
            provider: Provider name

        Returns:
            API key or None
        """
        key_name = f"api_key_{provider}"

        # First check environment variable
        env_var = f"RSS_API_KEY_{provider.upper()}"
        env_key = os.environ.get(env_var)
        if env_key:
            return env_key

        # Then check database
        db_key = self.db.get_setting(key_name)
        return db_key

    def remove_api_key(self, provider: str) -> bool:
        """
        Remove a stored API key.

        Args:
            provider: Provider name

        Returns:
            True if successful
        """
        key_name = f"api_key_{provider}"
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key = ?", (key_name,))
            self.db.conn.commit()
            logger.info(f"Removed API key for {provider}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove API key: {e}")
            return False

    def list_configured_providers(self) -> list[str]:
        """
        List providers with configured API keys.

        Returns:
            List of provider names
        """
        providers = []

        # Check database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT key FROM settings WHERE key LIKE 'api_key_%'
        """)

        for row in cursor.fetchall():
            key = row[0]
            provider = key.replace('api_key_', '')
            providers.append(provider)

        # Check environment variables
        for env_var in os.environ:
            if env_var.startswith('RSS_API_KEY_'):
                provider = env_var.replace('RSS_API_KEY_', '').lower()
                if provider not in providers:
                    providers.append(provider)

        return providers

    def is_configured(self, provider: str) -> bool:
        """
        Check if a provider has an API key configured.

        Args:
            provider: Provider name

        Returns:
            True if configured
        """
        return self.get_api_key(provider) is not None

    def get_all_settings(self) -> Dict[str, str]:
        """
        Get all non-sensitive settings.

        Returns:
            Dictionary of settings (excludes API keys)
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT key, value FROM settings WHERE key NOT LIKE 'api_key_%'
        """)

        return {row[0]: row[1] for row in cursor.fetchall()}

    def set_ai_provider(self, provider: str) -> bool:
        """
        Set preferred AI provider.

        Args:
            provider: 'claude', 'openai', or 'auto'

        Returns:
            True if successful
        """
        self.db.set_setting("ai_provider", provider)
        return True

    def get_ai_provider(self) -> str:
        """Get preferred AI provider."""
        return self.db.get_setting("ai_provider", "auto")

    def set_ai_model(self, model: str) -> bool:
        """
        Set AI model to use.

        Args:
            model: Model name

        Returns:
            True if successful
        """
        self.db.set_setting("ai_model", model)
        return True

    def get_ai_model(self) -> Optional[str]:
        """Get AI model setting."""
        return self.db.get_setting("ai_model")

    def enable_auto_extraction(self, enabled: bool = True) -> bool:
        """
        Enable/disable automatic full-text extraction.

        Args:
            enabled: Whether to auto-extract

        Returns:
            True if successful
        """
        self.db.set_setting("auto_extract_full_text", "true" if enabled else "false")
        return True

    def is_auto_extraction_enabled(self) -> bool:
        """Check if auto-extraction is enabled."""
        return self.db.get_setting("auto_extract_full_text", "false") == "true"

    def enable_auto_summarization(self, enabled: bool = True) -> bool:
        """
        Enable/disable automatic AI summarization.

        Args:
            enabled: Whether to auto-summarize

        Returns:
            True if successful
        """
        self.db.set_setting("auto_ai_summary", "true" if enabled else "false")
        return True

    def is_auto_summarization_enabled(self) -> bool:
        """Check if auto-summarization is enabled."""
        return self.db.get_setting("auto_ai_summary", "false") == "true"


def print_config_info():
    """Print configuration information."""
    config = APIConfigManager()

    print("=" * 60)
    print("API Configuration")
    print("=" * 60)

    # Check configured providers
    providers = config.list_configured_providers()
    if providers:
        print(f"\n✓ Configured providers: {', '.join(providers)}")
    else:
        print("\n⚠️  No API keys configured")

    # AI settings
    print(f"\nAI Provider: {config.get_ai_provider()}")

    model = config.get_ai_model()
    if model:
        print(f"AI Model: {model}")

    # Feature flags
    print(f"\nAuto-extract full text: {config.is_auto_extraction_enabled()}")
    print(f"Auto-generate summaries: {config.is_auto_summarization_enabled()}")

    print("\n" + "=" * 60)
    print("API Key Configuration Methods")
    print("=" * 60)

    print("""
1. Environment Variables (Recommended for security):
   export RSS_API_KEY_CLAUDE="your-claude-api-key"
   export RSS_API_KEY_OPENAI="your-openai-api-key"

2. Database Storage (Convenient):
   from rss_api_config import APIConfigManager

   config = APIConfigManager()
   config.set_api_key("claude", "your-api-key")
   config.set_api_key("openai", "your-api-key")

3. Direct in Code (Not recommended):
   # Pass API key directly to summarizer
   summarizer = AISummarizer(api_key="your-key")
""")


if __name__ == "__main__":
    print_config_info()

    # Example usage
    print("\n" + "=" * 60)
    print("Example Usage")
    print("=" * 60)

    config = APIConfigManager()

    # Check if any providers are configured
    providers = config.list_configured_providers()

    if providers:
        print(f"\nConfigured: {', '.join(providers)}")
    else:
        print("\nNo API keys configured yet.")
        print("\nTo configure an API key:")
        print("  config.set_api_key('claude', 'your-api-key')")
        print("  config.set_api_key('openai', 'your-api-key')")
