"""Command-line interface for TrendX."""

import asyncio
import sys
from typing import Optional

import click

from .aggregator import TrendAggregator
from .ai import MockAIGenerator
from .common.config import settings
from .common.database import create_tables, get_session
from .common.logging import configure_logging, get_logger
from .publisher import MockPublisher
from .sources import RedditTrendSource, GoogleTrendsSource, TwitterTrendsSource
from .web import create_app

logger = get_logger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--config", "-c", help="Path to configuration file")
def cli(verbose: bool, config: Optional[str]) -> None:
    """TrendX: Curate top global & Turkey trending news/videos and post bilingual summaries to X (Twitter)."""
    # Configure logging
    if verbose:
        settings.logging.level = "DEBUG"
    
    configure_logging()
    
    # Initialize database
    create_tables()


@cli.command()
@click.option("--limit", "-l", default=5, help="Number of items to fetch")
@click.option("--source", "-s", help="Specific source to fetch from (reddit, google_trends, twitter_trends)")
def fetch(limit: int, source: Optional[str]) -> None:
    """Fetch trending items from sources."""
    logger.info("Starting trend fetch", limit=limit, source=source)

    # Initialize sources
    sources = {
        "reddit": RedditTrendSource(),
        "google_trends": GoogleTrendsSource(),
        "twitter_trends": TwitterTrendsSource(),
    }

    # Filter sources if specified
    if source:
        if source not in sources:
            logger.error("Invalid source", source=source, available=list(sources.keys()))
            sys.exit(1)
        sources = {source: sources[source]}

    # Initialize aggregator
    aggregator = TrendAggregator(sources)

    try:
        # Fetch trends
        trends = asyncio.run(aggregator.aggregate_trends(limit=limit))
        
        if not trends:
            logger.warning("No trends fetched")
            return

        # Display results
        click.echo(f"\n📈 Fetched {len(trends)} trending items:\n")
        
        for i, trend in enumerate(trends, 1):
            click.echo(f"{i}. {trend.title}")
            click.echo(f"   Source: {trend.source.value}")
            click.echo(f"   Score: {trend.score:.2f}")
            click.echo(f"   Turkey Related: {'Yes' if trend.is_turkey_related else 'No'}")
            click.echo(f"   Global: {'Yes' if trend.is_global else 'No'}")
            if trend.url:
                click.echo(f"   URL: {trend.url}")
            click.echo()

    except Exception as e:
        logger.error("Error fetching trends", error=str(e))
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=5, help="Number of items to score")
def score(limit: int) -> None:
    """Score and rank trending items."""
    logger.info("Starting trend scoring", limit=limit)

    # Initialize sources
    sources = {
        "reddit": RedditTrendSource(),
        "google_trends": GoogleTrendsSource(),
        "twitter_trends": TwitterTrendsSource(),
    }

    # Initialize aggregator
    aggregator = TrendAggregator(sources)

    try:
        # Fetch and score trends
        trends = asyncio.run(aggregator.aggregate_trends(limit=limit))
        
        if not trends:
            logger.warning("No trends to score")
            return

        # Display results
        click.echo(f"\n🏆 Top {len(trends)} scored trends:\n")
        
        for i, trend in enumerate(trends, 1):
            click.echo(f"{i}. {trend.title}")
            click.echo(f"   Score: {trend.score:.3f}")
            click.echo(f"   Source: {trend.source.value}")
            click.echo(f"   Social Volume: {trend.social_volume}")
            click.echo(f"   Turkey Related: {'Yes' if trend.is_turkey_related else 'No'}")
            click.echo()

    except Exception as e:
        logger.error("Error scoring trends", error=str(e))
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", "-l", default=10, help="Number of queue items to show")
def queue(limit: int) -> None:
    """Show post queue status."""
    logger.info("Showing post queue", limit=limit)

    try:
        with get_session() as session:
            from .common.models import PostQueue
            
            queue_items = session.query(PostQueue).order_by(
                PostQueue.scheduled_at.desc()
            ).limit(limit).all()

            if not queue_items:
                click.echo("No items in post queue")
                return

            click.echo(f"\n📋 Post Queue ({len(queue_items)} items):\n")
            
            for i, item in enumerate(queue_items, 1):
                status_emoji = {
                    "pending": "⏳",
                    "posted": "✅",
                    "failed": "❌",
                }.get(item.status, "❓")
                
                click.echo(f"{i}. {status_emoji} {item.status.upper()}")
                click.echo(f"   Scheduled: {item.scheduled_at}")
                if item.posted_at:
                    click.echo(f"   Posted: {item.posted_at}")
                if item.twitter_post_id:
                    click.echo(f"   Post ID: {item.twitter_post_id}")
                if item.error_message:
                    click.echo(f"   Error: {item.error_message}")
                click.echo()

    except Exception as e:
        logger.error("Error showing queue", error=str(e))
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--dry-run", is_flag=True, help="Show what would be posted without actually posting")
@click.option("--limit", "-l", default=1, help="Number of items to post")
def post(dry_run: bool, limit: int) -> None:
    """Post trending content to Twitter."""
    logger.info("Starting post operation", dry_run=dry_run, limit=limit)

    # Initialize components - Selenium ile gerçek içerik bulma
    from .sources.selenium_trends import SeleniumTrendsSource
    sources = {
        "selenium_trends": SeleniumTrendsSource(),  # Selenium ile gerçek içerik
    }
    
    aggregator = TrendAggregator(sources)
    
    # Initialize AI generator (OpenAI if configured, otherwise mock)
    from .ai.openai_generator import OpenAIGenerator
    if settings.ai.api_key and settings.ai.api_key != "your_openai_api_key_here":
        ai_generator = OpenAIGenerator()
        logger.info("Using OpenAI AI generator")
    else:
        ai_generator = MockAIGenerator()
        logger.info("Using Mock AI generator (OpenAI API key not configured)")
    
    # Initialize publisher (Twitter if configured, otherwise mock)
    from .publisher.twitter_publisher import TwitterPublisher
    if (settings.twitter.api_key and settings.twitter.api_key != "your_twitter_api_key_here" and
        settings.twitter.access_token and settings.twitter.access_token != "your_twitter_access_token_here"):
        publisher = TwitterPublisher()
        logger.info("Using Twitter publisher")
    else:
        publisher = MockPublisher()
        logger.info("Using Mock publisher (Twitter API keys not configured)")

    try:
        # Fetch trends
        trends = asyncio.run(aggregator.aggregate_trends(limit=limit))
        
        if not trends:
            logger.warning("No trends to post")
            return

        click.echo(f"\n📝 {'Would post' if dry_run else 'Posting'} {len(trends)} items:\n")

        for i, trend in enumerate(trends, 1):
            # Generate content
            content = asyncio.run(ai_generator.generate_tweet_content(trend))
            
            click.echo(f"{i}. {trend.title}")
            click.echo(f"   Turkish: {content.turkish_text}")
            click.echo(f"   English: {content.english_text}")
            click.echo(f"   Hashtags: {' '.join(content.hashtags)}")
            click.echo()

            if not dry_run:
                # Actually post
                result = asyncio.run(publisher.publish_tweet(content))
                
                if result.success:
                    click.echo(f"   ✅ Posted successfully (ID: {result.post_id})")
                else:
                    click.echo(f"   ❌ Failed to post: {result.error_message}")
                click.echo()

    except Exception as e:
        logger.error("Error posting content", error=str(e))
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--host", default=settings.web.host, help="Host to bind to")
@click.option("--port", default=settings.web.port, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def web(host: str, port: int, reload: bool) -> None:
    """Start the web dashboard."""
    import uvicorn
    
    logger.info("Starting web dashboard", host=host, port=port)
    
    app = create_app()
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=settings.logging.level.lower(),
    )


@cli.command()
def start() -> None:
    """Start the hourly tweet scheduler."""
    logger.info("Starting hourly tweet scheduler")
    
    try:
        import asyncio
        from .scheduler.scheduler import TrendScheduler
        
        async def run_scheduler():
            # Create and start scheduler
            scheduler = TrendScheduler()
            scheduler.start()
            
            click.echo("🚀 Saat başı tweet scheduler başlatıldı!")
            click.echo("⏰ Her saat başı 1 tweet atılacak")
            click.echo("🌙 Gece 23:00-07:00 arası tweet atılmayacak")
            click.echo("🛑 Durdurmak için Ctrl+C basın")
            
            try:
                # Keep running
                while True:
                    await asyncio.sleep(60)  # 1 dakika bekle
            except KeyboardInterrupt:
                click.echo("\n🛑 Scheduler durduruluyor...")
                scheduler.stop()
                click.echo("✅ Scheduler durduruldu")
        
        # Run async scheduler
        asyncio.run(run_scheduler())
            
    except Exception as e:
        logger.error("Error starting scheduler", error=str(e))
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def init() -> None:
    """Initialize the TrendX database and configuration."""
    logger.info("Initializing TrendX")
    
    # Create database tables
    create_tables()
    
    click.echo("✅ Database initialized")
    click.echo("✅ Configuration loaded")
    click.echo("\nNext steps:")
    click.echo("1. Copy env.example to .env and configure your API keys")
    click.echo("2. Run 'trendx fetch' to test trend collection")
    click.echo("3. Run 'trendx post --dry-run' to test content generation")
    click.echo("4. Run 'trendx start' to start hourly tweet scheduler")


def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
