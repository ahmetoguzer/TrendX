# TrendX

Curate top global & Turkey trending news/videos and post bilingual (TR+EN) summaries to X (Twitter) automatically, several times per day.

## Features

- **Multiple Sources**: Reddit, Google Trends, Twitter/X Trends, YouTube Trending, RSS feeds
- **Smart Aggregation**: Deduplication, scoring, and ranking of trending content
- **Bilingual Content**: AI-generated Turkish and English summaries
- **Automated Posting**: Scheduled posting with rate limiting and quiet hours
- **Web Dashboard**: Monitor trends, queue status, and posting history
- **Safety First**: Content moderation, URL whitelisting, and copyright protection

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -e .
   ```

2. **Initialize Configuration**:
   ```bash
   python -m trendx init
   ```

3. **Configure API Keys** (optional for testing):
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

4. **Test Trend Collection**:
   ```bash
   python -m trendx fetch --limit 5
   # Or test specific sources:
   python -m trendx fetch --source twitter_trends --limit 3
   python -m trendx fetch --source reddit --limit 3
   ```

5. **Test Content Generation**:
   ```bash
   python -m trendx post --dry-run --limit 1
   ```

6. **Start Web Dashboard**:
   ```bash
   python -m trendx web
   ```

## CLI Commands

- `python -m trendx fetch` - Fetch trending items from all sources
- `python -m trendx fetch --source twitter_trends` - Fetch from specific source
- `python -m trendx score` - Score and rank trending items
- `python -m trendx queue` - Show post queue status
- `python -m trendx post --dry-run` - Test content generation
- `python -m trendx web` - Start web dashboard
- `python -m trendx init` - Initialize database and configuration

## Architecture

```
trendx/
├── sources/          # Pluggable trend sources
├── aggregator/       # Deduplication and scoring
├── ai/              # LLM integration for content generation
├── publisher/       # Twitter/X posting
├── scheduler/       # Automated scheduling
├── web/            # FastAPI dashboard
├── common/         # Configuration, logging, models
└── tests/          # Unit tests
```

## Configuration

Key settings in `.env`:

- `SAFE_MODE=true` - Enable safe mode (no media download)
- `ALLOW_MEDIA_DOWNLOAD=false` - Disable media downloads by default
- `POSTING_INTERVAL_MINUTES=60` - How often to post
- `QUIET_HOURS_START=23` - Quiet hours start (24h format)
- `QUIET_HOURS_END=7` - Quiet hours end (24h format)

## Safety Features

- **Copyright Protection**: No full video re-uploads, prefer links and embeds
- **Content Moderation**: Language filtering and banned keywords
- **URL Whitelisting**: Only allow trusted domains
- **Rate Limiting**: Respect platform limits
- **Idempotency**: Prevent duplicate posts

## Development

1. **Install Dev Dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

2. **Run Tests**:
   ```bash
   pytest
   ```

3. **Code Formatting**:
   ```bash
   black trendx/
   ruff check trendx/
   mypy trendx/
   ```

## License

MIT License - see LICENSE file for details.
