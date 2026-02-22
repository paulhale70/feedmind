# RSSreaderV3.5 - AI & Article Extraction Features

## Overview

Version 3.5 adds **AI-Powered Summarization** and **Full-Text Article Extraction** to the RSS reader, making it easier to quickly process and understand large amounts of content.

## New V3.5 Features

### 1. Full-Text Article Extraction

**Automatic Content Retrieval**
- Fetches complete article content from web pages
- Overcomes truncated RSS feed descriptions
- Stores full text in database for offline reading
- Supports multiple extraction libraries

**Extraction Methods**
- **newspaper3k** - Comprehensive extraction with metadata
- **trafilatura** - Lightweight and fast alternative
- Automatic method selection for best results

**Extracted Data**
- Full article text
- Author names
- Publication date
- Top image URL (newspaper3k only)
- Extraction timestamp

**Database Integration**
- Stores full text in `articles.full_text` column
- Tracks extraction date
- Query articles needing extraction
- Batch extraction support

### 2. AI-Powered Summarization

**Multi-Provider Support**
- **Claude API** (Anthropic) - Recommended for quality
- **OpenAI GPT** - Alternative option
- Automatic provider selection

**Summary Types**

1. **TL;DR** - Ultra-concise 1-2 sentence summary
2. **Standard Summary** - Comprehensive paragraph (customizable length)
3. **Key Points** - Bulleted list of main takeaways (customizable count)

**Features**
- Customizable summary length
- Adjustable number of key points
- Model selection (Haiku, GPT-3.5, etc.)
- Cost-optimized default models
- Batch summarization support

**Database Storage**
- AI summaries stored in articles table
- TL;DR, summary, and key points saved separately
- Generation timestamp tracked
- Query articles needing summaries

### 3. API Configuration System

**Secure Key Storage**
- Environment variable support (recommended)
- Database storage option
- Per-provider configuration
- Easy key management

**Auto-Configuration**
- Auto-detection of available providers
- Fallback provider selection
- Model preference settings
- Feature flags for automation

**Settings**
- Enable/disable auto-extraction
- Enable/disable auto-summarization
- Preferred AI provider
- Preferred AI model

## Technical Implementation

### Core Modules

#### rss_article_extractor.py
- `ArticleExtractor` class for content extraction
- Support for newspaper3k and trafilatura
- Automatic method selection
- Batch extraction with threading
- Error handling and fallbacks

#### rss_ai_summarizer.py
- `AISummarizer` class for AI summarization
- Claude and OpenAI API integration
- Multiple summary types (TL;DR, summary, key points)
- Customizable parameters
- Cost-optimized default models

#### rss_api_config.py
- `APIConfigManager` for key management
- Environment variable support
- Database storage with encryption option
- Feature flag management
- Provider configuration

#### rss_database_v3.py (Enhanced)
- New columns for full text and AI data
- Methods for storing/retrieving full text
- Methods for storing/retrieving AI summaries
- Query methods for articles needing processing
- JSON storage for key points

### Database Schema Enhancements

**Articles Table - New Columns**
```sql
-- Full text extraction
full_text TEXT                     -- Extracted article content
full_text_extracted_date TEXT      -- When text was extracted

-- AI summarization
ai_summary TEXT                    -- Generated summary
ai_tldr TEXT                       -- TL;DR summary
ai_key_points TEXT                 -- JSON array of key points
ai_generated_date TEXT             -- When summary was generated
```

## Installation

### Required Base Dependencies
```bash
pip install streamlit pandas sqlalchemy
```

### V3.5 New Dependencies

**For Article Extraction (choose one or both):**
```bash
pip install newspaper3k    # Recommended - full-featured
pip install trafilatura    # Lightweight alternative
```

**For AI Summarization (choose one or both):**
```bash
pip install anthropic      # Claude API (recommended)
pip install openai         # OpenAI API
```

### Complete Installation
```bash
pip install -r requirements.txt
```

## Configuration

### 1. API Key Setup

**Method 1: Environment Variables (Recommended)**
```bash
# For Claude
export RSS_API_KEY_CLAUDE="sk-ant-api03-xxx..."

# For OpenAI
export RSS_API_KEY_OPENAI="sk-xxx..."
```

**Method 2: Database Storage**
```python
from rss_api_config import APIConfigManager

config = APIConfigManager()
config.set_api_key("claude", "your-api-key")
config.set_api_key("openai", "your-api-key")
```

**Method 3: Direct in Code**
```python
from rss_ai_summarizer import AISummarizer

summarizer = AISummarizer(api_key="your-api-key")
```

### 2. Get API Keys

**Claude API** (Recommended)
- Visit: https://console.anthropic.com/
- Sign up for an account
- Generate an API key
- Default model: claude-3-haiku-20240307 (fast & cheap)

**OpenAI API**
- Visit: https://platform.openai.com/api-keys
- Sign up for an account
- Create an API key
- Default model: gpt-3.5-turbo (fast & affordable)

## Usage Examples

### Article Extraction

```python
from rss_article_extractor import ArticleExtractor
from rss_database_v3 import RSSDatabase

# Initialize extractor
extractor = ArticleExtractor()

# Extract from URL
result = extractor.extract("https://example.com/article")

if result:
    print(f"Title: {result['title']}")
    print(f"Text: {result['text'][:200]}...")
    print(f"Method: {result['method']}")

    # Store in database
    db = RSSDatabase()
    db.store_full_text(article_id, result['text'])
```

### AI Summarization

```python
from rss_ai_summarizer import AISummarizer, AIProvider
from rss_api_config import APIConfigManager

# Get API key from config
config = APIConfigManager()
api_key = config.get_api_key("claude")

# Initialize summarizer
summarizer = AISummarizer(
    provider=AIProvider.CLAUDE,
    api_key=api_key
)

# Generate TL;DR
tldr = summarizer.generate_tldr(article_text)
print(f"TL;DR: {tldr}")

# Generate full summary
summary = summarizer.summarize(article_text, max_length=200)
print(f"Summary: {summary}")

# Extract key points
key_points = summarizer.extract_key_points(article_text, num_points=5)
for i, point in enumerate(key_points, 1):
    print(f"{i}. {point}")

# Or get everything at once
result = summarizer.summarize_article(article_text)
print(result['tldr'])
print(result['summary'])
for point in result['key_points']:
    print(f"  • {point}")
```

### Complete Workflow

```python
from rss_database_v3 import RSSDatabase
from rss_article_extractor import ArticleExtractor
from rss_ai_summarizer import AISummarizer, AIProvider
from rss_api_config import APIConfigManager

# Initialize
db = RSSDatabase()
extractor = ArticleExtractor()
config = APIConfigManager()

# Get articles needing full text
articles = db.get_articles_needing_extraction(limit=10)

for article in articles:
    print(f"Processing: {article['title']}")

    # Extract full text
    result = extractor.extract(article['link'])
    if result:
        # Store full text
        db.store_full_text(article['id'], result['text'])

        # Generate AI summary if configured
        if config.is_auto_summarization_enabled():
            api_key = config.get_api_key("claude")
            if api_key:
                summarizer = AISummarizer(
                    provider=AIProvider.CLAUDE,
                    api_key=api_key
                )

                summary_data = summarizer.summarize_article(result['text'])

                # Store AI summary
                db.store_ai_summary(
                    article['id'],
                    summary_data['summary'],
                    summary_data['tldr'],
                    summary_data['key_points']
                )

                print("  ✓ Extracted and summarized")
            else:
                print("  ✓ Extracted (no API key for summarization)")
        else:
            print("  ✓ Extracted")

db.close()
```

### Configuration Management

```python
from rss_api_config import APIConfigManager

config = APIConfigManager()

# Set up AI provider
config.set_ai_provider("claude")  # or "openai" or "auto"
config.set_ai_model("claude-3-haiku-20240307")

# Enable automatic features
config.enable_auto_extraction(True)
config.enable_auto_summarization(True)

# Check configuration
print(f"Configured providers: {config.list_configured_providers()}")
print(f"AI provider: {config.get_ai_provider()}")
print(f"Auto-extract: {config.is_auto_extraction_enabled()}")
print(f"Auto-summarize: {config.is_auto_summarization_enabled()}")
```

## Testing

### Run All Tests
```bash
python test_ai_extraction.py
```

### Test Components

The test suite includes:
- Database schema validation
- Article extraction (if libraries installed)
- AI summarization (if libraries + API key)
- API configuration management
- Full text storage and retrieval
- AI summary storage and retrieval
- Integration testing

### Expected Output
```
✓ Database AI Columns - PASS
✓ Article Extraction - PASS (or SKIP if not installed)
✓ AI Summarization - PASS (or SKIP if no API key)
✓ API Configuration - PASS
✓ Integration - PASS
```

## Cost Considerations

### AI API Costs

**Claude (Anthropic)**
- Haiku model: ~$0.00025 per 1K input tokens
- Very cost-effective for summaries
- Recommended for high-volume usage
- Example: 1000 articles @ 1000 tokens each ≈ $0.25

**OpenAI**
- GPT-3.5-turbo: ~$0.0005 per 1K input tokens
- Affordable for moderate usage
- Example: 1000 articles @ 1000 tokens each ≈ $0.50

**Tips for Cost Management**
1. Use Haiku or GPT-3.5-turbo (not GPT-4)
2. Limit summary length to what you need
3. Cache summaries in database
4. Only summarize articles you care about
5. Use TL;DR for quick scans (fewer tokens)

### Extraction Costs

Both newspaper3k and trafilatura are **free and open source**. No API costs!

## Feature Comparison

| Feature | V1 | V2 | V3 | V3.5 |
|---------|----|----|-----|------|
| RSS/Atom parsing | ✓ | ✓ | ✓ | ✓ |
| Categories | - | ✓ | ✓ | ✓ |
| OPML import/export | - | ✓ | ✓ | ✓ |
| Dark mode | - | ✓ | ✓ | ✓ |
| PDF export | - | ✓ | ✓ | ✓ |
| Notifications | - | ✓ | ✓ | ✓ |
| Podcast support | - | - | ✓ | ✓ |
| Auto-refresh | - | - | ✓ | ✓ |
| **Full-text extraction** | - | - | - | **✓** |
| **AI summarization** | - | - | - | **✓** |
| **TL;DR generation** | - | - | - | **✓** |
| **Key point extraction** | - | - | - | **✓** |

## Known Limitations

### Article Extraction
- Some sites block scraping (use RSS content in that case)
- JavaScript-heavy sites may not work well
- Paywalled content requires subscription
- Success rate varies by site

### AI Summarization
- Requires API key and internet connection
- Costs money (though very affordable)
- Quality depends on source article
- May miss nuance in complex topics
- Rate limits apply (especially OpenAI free tier)

## Future Enhancements

- Local AI models (no API costs)
- Custom summarization prompts
- Multi-language support
- Summary quality scoring
- Batch processing UI
- Reading list with summaries
- Email digest with TL;DRs
- Smart recommendation based on summaries

## Troubleshooting

### Extraction Not Working
1. Check library is installed: `pip list | grep newspaper`
2. Try alternative method (trafilatura vs newspaper3k)
3. Check article URL is accessible
4. Some sites block automated access

### AI Summarization Fails
1. Verify API key is set correctly
2. Check API key has credits/billing enabled
3. Ensure internet connection
4. Check rate limits (OpenAI has limits on free tier)
5. Try smaller text chunks

### API Key Not Found
1. Check environment variables: `echo $RSS_API_KEY_CLAUDE`
2. Verify database storage: Use APIConfigManager
3. Ensure no typos in provider name

## Support

For issues with V3.5 features:
1. Run `python test_ai_extraction.py` to diagnose
2. Check API key configuration
3. Verify dependencies are installed
4. Review error messages carefully
5. Check provider API status pages

## License

Same as RSS Reader main project.
