"""
API Configuration Manager for RSS Reader V3
Secure storage of API keys and configuration.

API keys are stored in the OS credential store via the `keyring` library
(Windows Credential Manager on Windows, Keychain on macOS, Secret Service on
Linux). If `keyring` is unavailable, falls back to the SQLite settings table
with a loud warning — earlier versions stored keys in plaintext SQLite, so
on first read we migrate any plaintext keys into the keyring and scrub the DB.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
from rss_database_v3 import RSSDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keyring service name used to namespace our entries in the OS credential store.
_KEYRING_SERVICE = "feedmind"

try:
    import keyring as _keyring  # type: ignore
    # Probe: if no usable backend is present (e.g. headless Linux without
    # SecretService), keyring raises on first use rather than import. We defer
    # the check to actual get/set calls.
    _KEYRING_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _keyring = None
    _KEYRING_AVAILABLE = False
    logger.warning(
        "'keyring' is not installed; API keys will fall back to SQLite "
        "(less secure, especially in synced folders like OneDrive). "
        "Install with: pip install keyring"
    )


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

    # ------------------------------------------------------------------
    # Storage backend helpers
    # ------------------------------------------------------------------
    def _keyring_set(self, provider: str, api_key: str) -> bool:
        """Store a key in the OS credential store. Returns True on success."""
        if not _KEYRING_AVAILABLE:
            return False
        try:
            _keyring.set_password(_KEYRING_SERVICE, provider, api_key)
            return True
        except Exception as e:
            logger.exception(f"keyring.set_password failed for {provider}: {e}")
            return False

    def _keyring_get(self, provider: str) -> Optional[str]:
        if not _KEYRING_AVAILABLE:
            return None
        try:
            return _keyring.get_password(_KEYRING_SERVICE, provider)
        except Exception as e:
            logger.exception(f"keyring.get_password failed for {provider}: {e}")
            return None

    def _keyring_delete(self, provider: str) -> bool:
        if not _KEYRING_AVAILABLE:
            return False
        try:
            _keyring.delete_password(_KEYRING_SERVICE, provider)
            return True
        except _keyring.errors.PasswordDeleteError:  # type: ignore[attr-defined]
            return False
        except Exception as e:
            logger.exception(f"keyring.delete_password failed for {provider}: {e}")
            return False

    def _db_delete_key(self, provider: str) -> None:
        """Scrub a legacy plaintext key from the settings table."""
        key_name = f"api_key_{provider}"
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM settings WHERE key = ?", (key_name,))
            self.db.conn.commit()
        except Exception as e:
            logger.exception(f"Failed to scrub legacy key for {provider}: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_api_key(self, provider: str, api_key: str) -> bool:
        """
        Store an API key.

        Prefers the OS credential store via `keyring`. Falls back to the
        SQLite settings table only when keyring is unavailable.

        Args:
            provider: Provider name (e.g., 'claude', 'openai')
            api_key: The API key

        Returns:
            True if successful
        """
        if self._keyring_set(provider, api_key):
            # Belt-and-braces: if a legacy plaintext copy exists, remove it.
            self._db_delete_key(provider)
            logger.info(f"Stored API key for {provider} in OS credential store")
            return True

        # Fallback: SQLite (insecure — warn the user).
        key_name = f"api_key_{provider}"
        self.db.set_setting(key_name, api_key)
        logger.warning(
            f"Stored API key for {provider} in SQLite (insecure fallback). "
            f"Install 'keyring' for secure storage."
        )
        return True

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Retrieve an API key.

        Resolution order: environment variable → OS credential store →
        SQLite settings table (legacy). If a legacy SQLite key is found and
        keyring is available, it is migrated into the credential store and
        scrubbed from the database before being returned.

        Args:
            provider: Provider name

        Returns:
            API key or None
        """
        # 1. Environment variable always wins.
        env_var = f"RSS_API_KEY_{provider.upper()}"
        env_key = os.environ.get(env_var)
        if env_key:
            return env_key

        # 2. OS credential store.
        kr_key = self._keyring_get(provider)
        if kr_key:
            return kr_key

        # 3. Legacy SQLite — migrate on read if possible.
        key_name = f"api_key_{provider}"
        db_key = self.db.get_setting(key_name)
        if db_key:
            if _KEYRING_AVAILABLE and self._keyring_set(provider, db_key):
                self._db_delete_key(provider)
                logger.info(
                    f"Migrated legacy plaintext API key for {provider} "
                    f"from SQLite to OS credential store"
                )
        return db_key

    def remove_api_key(self, provider: str) -> bool:
        """
        Remove a stored API key from both storage backends.

        Args:
            provider: Provider name

        Returns:
            True if at least one backend reported success.
        """
        removed_anywhere = False
        if self._keyring_delete(provider):
            removed_anywhere = True
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "DELETE FROM settings WHERE key = ?", (f"api_key_{provider}",)
            )
            if cursor.rowcount > 0:
                removed_anywhere = True
            self.db.conn.commit()
        except Exception as e:
            logger.exception(f"Failed to remove API key from DB: {e}")
            return removed_anywhere
        if removed_anywhere:
            logger.info(f"Removed API key for {provider}")
        return removed_anywhere

    def list_configured_providers(self) -> list[str]:
        """
        List providers with configured API keys.

        Returns:
            List of provider names
        """
        providers: list[str] = []

        # Legacy SQLite entries (will be migrated lazily on read).
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT key FROM settings WHERE key LIKE 'api_key_%'
        """)
        for row in cursor.fetchall():
            provider = row[0].replace('api_key_', '')
            providers.append(provider)

        # OS credential store entries. keyring has no portable enumeration API,
        # so probe the providers we know about.
        if _KEYRING_AVAILABLE:
            for provider in ("claude", "openai"):
                try:
                    if _keyring.get_password(_KEYRING_SERVICE, provider):
                        if provider not in providers:
                            providers.append(provider)
                except Exception:
                    pass

        # Environment variables.
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
