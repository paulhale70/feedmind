"""
AI-Powered Article Summarizer for RSS Reader V3
Generates summaries and key points using Claude API or OpenAI.
"""

import logging
from typing import Optional, Dict, List
from enum import Enum

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """AI provider enumeration."""
    CLAUDE = "claude"
    OPENAI = "openai"
    AUTO = "auto"


class AISummarizer:
    """Generate AI-powered article summaries."""

    def __init__(self, provider: AIProvider = AIProvider.AUTO,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None):
        """
        Initialize AI summarizer.

        Args:
            provider: AI provider to use
            api_key: API key (required)
            model: Model name (optional, uses default if not specified)
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model

        # Set default models
        if not self.model:
            if provider == AIProvider.CLAUDE:
                self.model = "claude-3-haiku-20240307"  # Fast and cost-effective
            elif provider == AIProvider.OPENAI:
                self.model = "gpt-3.5-turbo"  # Fast and cost-effective

        # Initialize client
        self.client = None
        if self.api_key:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the AI client."""
        if self.provider == AIProvider.CLAUDE and ANTHROPIC_AVAILABLE:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Initialized Claude client")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")

        elif self.provider == AIProvider.OPENAI and OPENAI_AVAILABLE:
            try:
                openai.api_key = self.api_key
                self.client = openai
                logger.info("Initialized OpenAI client")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

        elif self.provider == AIProvider.AUTO:
            # Try Claude first, then OpenAI
            if ANTHROPIC_AVAILABLE:
                try:
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                    self.provider = AIProvider.CLAUDE
                    if not self.model:
                        self.model = "claude-3-haiku-20240307"
                    logger.info("Auto-selected Claude")
                    return
                except:
                    pass

            if OPENAI_AVAILABLE:
                try:
                    openai.api_key = self.api_key
                    self.client = openai
                    self.provider = AIProvider.OPENAI
                    if not self.model:
                        self.model = "gpt-3.5-turbo"
                    logger.info("Auto-selected OpenAI")
                    return
                except:
                    pass

    @staticmethod
    def is_available() -> bool:
        """Check if any AI library is available."""
        return ANTHROPIC_AVAILABLE or OPENAI_AVAILABLE

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available AI providers."""
        providers = []
        if ANTHROPIC_AVAILABLE:
            providers.append("claude")
        if OPENAI_AVAILABLE:
            providers.append("openai")
        return providers

    def summarize(self, text: str, max_length: int = 200) -> Optional[str]:
        """
        Generate a summary of the article.

        Args:
            text: Article text to summarize
            max_length: Maximum summary length in words

        Returns:
            Summary text or None on failure
        """
        if not self.client or not self.api_key:
            logger.error("AI client not initialized - API key required")
            return None

        if not text or len(text) < 100:
            return text  # Too short to summarize

        prompt = f"""Please provide a concise summary of the following article in approximately {max_length} words. Focus on the main points and key takeaways.

Article:
{text[:8000]}  # Limit to avoid token limits

Summary:"""

        try:
            if self.provider == AIProvider.CLAUDE:
                return self._summarize_claude(prompt)
            elif self.provider == AIProvider.OPENAI:
                return self._summarize_openai(prompt)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None

    def extract_key_points(self, text: str, num_points: int = 5) -> Optional[List[str]]:
        """
        Extract key points from the article.

        Args:
            text: Article text
            num_points: Number of key points to extract

        Returns:
            List of key points or None on failure
        """
        if not self.client or not self.api_key:
            logger.error("AI client not initialized - API key required")
            return None

        if not text or len(text) < 100:
            return [text]

        prompt = f"""Please extract the {num_points} most important key points from the following article. Format as a numbered list.

Article:
{text[:8000]}

Key Points:"""

        try:
            if self.provider == AIProvider.CLAUDE:
                response = self._summarize_claude(prompt)
            elif self.provider == AIProvider.OPENAI:
                response = self._summarize_openai(prompt)
            else:
                return None

            if response:
                # Parse numbered list
                lines = response.strip().split('\n')
                points = []
                for line in lines:
                    line = line.strip()
                    # Remove numbering
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # Remove number, dash, or bullet
                        cleaned = line.lstrip('0123456789.-•) ').strip()
                        if cleaned:
                            points.append(cleaned)

                return points[:num_points]

        except Exception as e:
            logger.error(f"Key point extraction failed: {e}")
            return None

    def generate_tldr(self, text: str) -> Optional[str]:
        """
        Generate a TL;DR (Too Long; Didn't Read) summary.

        Args:
            text: Article text

        Returns:
            TL;DR summary (1-2 sentences) or None
        """
        if not self.client or not self.api_key:
            logger.error("AI client not initialized - API key required")
            return None

        if not text or len(text) < 100:
            return text

        prompt = f"""Please provide a TL;DR (Too Long; Didn't Read) summary of the following article in 1-2 sentences. Be extremely concise.

Article:
{text[:8000]}

TL;DR:"""

        try:
            if self.provider == AIProvider.CLAUDE:
                return self._summarize_claude(prompt)
            elif self.provider == AIProvider.OPENAI:
                return self._summarize_openai(prompt)
        except Exception as e:
            logger.error(f"TL;DR generation failed: {e}")
            return None

    def _summarize_claude(self, prompt: str) -> Optional[str]:
        """
        Generate summary using Claude API.

        Args:
            prompt: Prompt text

        Returns:
            Generated text or None
        """
        if not ANTHROPIC_AVAILABLE or not self.client:
            return None

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return None

    def _summarize_openai(self, prompt: str) -> Optional[str]:
        """
        Generate summary using OpenAI API.

        Args:
            prompt: Prompt text

        Returns:
            Generated text or None
        """
        if not OPENAI_AVAILABLE or not self.client:
            return None

        try:
            response = self.client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes articles concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    def summarize_article(self, text: str) -> Optional[Dict]:
        """
        Generate complete summary with TL;DR and key points.

        Args:
            text: Article text

        Returns:
            Dictionary with summary data:
            {
                'tldr': str,
                'summary': str,
                'key_points': list[str]
            }
        """
        if not self.client or not self.api_key:
            logger.error("AI client not initialized")
            return None

        logger.info("Generating complete article summary...")

        result = {
            'tldr': self.generate_tldr(text),
            'summary': self.summarize(text, max_length=200),
            'key_points': self.extract_key_points(text, num_points=5)
        }

        return result


def check_dependencies():
    """Check if required dependencies are installed."""
    print("AI Summarization Libraries:")
    print("-" * 60)

    if ANTHROPIC_AVAILABLE:
        print("✓ anthropic is installed")
    else:
        print("❌ anthropic is not installed")
        print("  To install: pip install anthropic")

    if OPENAI_AVAILABLE:
        print("✓ openai is installed")
    else:
        print("❌ openai is not installed")
        print("  To install: pip install openai")

    print()

    if not ANTHROPIC_AVAILABLE and not OPENAI_AVAILABLE:
        print("⚠️  No AI library available")
        print("\nTo enable AI summaries, install at least one:")
        print("  pip install anthropic    # Claude API")
        print("  pip install openai       # OpenAI API")
        print("\nNote: You'll also need an API key from the provider")
        return False

    available = AISummarizer.get_available_providers()
    print(f"Available providers: {', '.join(available)}")
    print("\n⚠️  API key required to use AI summarization")
    print("Set your API key:")
    print("  - Claude: https://console.anthropic.com/")
    print("  - OpenAI: https://platform.openai.com/api-keys")
    return True


if __name__ == "__main__":
    # Test AI summarization
    check_dependencies()

    # Example usage (requires API key)
    print("\n" + "=" * 60)
    print("AI Summarizer Usage Example")
    print("=" * 60)

    print("""
# To use the AI summarizer:

from rss_ai_summarizer import AISummarizer, AIProvider

# Initialize with your API key
summarizer = AISummarizer(
    provider=AIProvider.CLAUDE,  # or AIProvider.OPENAI
    api_key="your-api-key-here"
)

# Generate a summary
text = "Your article text here..."
summary = summarizer.summarize(text, max_length=200)

# Extract key points
key_points = summarizer.extract_key_points(text, num_points=5)

# Generate TL;DR
tldr = summarizer.generate_tldr(text)

# Get everything at once
result = summarizer.summarize_article(text)
print(result['tldr'])
print(result['summary'])
for point in result['key_points']:
    print(f"  • {point}")
""")
