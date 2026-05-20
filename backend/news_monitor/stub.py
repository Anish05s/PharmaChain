"""
News Monitor — Phase 3 stub.
=========================================
Phase 3 upgrade: wire up NewsAPI.org or GDELT to auto-detect disruption events.

To enable:
  1. Set NEWS_API_KEY in .env
  2. Replace this stub with news_monitor/fetcher.py containing:
     - fetch_pharma_news(query="flood OR earthquake OR outbreak") → List[Article]
     - parse_article_to_event(article) → DisruptionEvent | None
     - schedule_news_poll(db_factory, interval_minutes=30)
  3. Import and start the scheduler in main.py (same pattern as inventory_ai)

Current state: logs a startup notice only.
"""
import logging

logger = logging.getLogger(__name__)


def start_news_monitor(news_api_key: str = "") -> None:
    if not news_api_key:
        logger.info(
            "NewsMonitor: NEWS_API_KEY not set — external news monitoring disabled. "
            "Events can still be submitted manually via POST /crisis/events. "
            "Set NEWS_API_KEY in .env to enable Phase 3 auto-detection."
        )
        return

    # Phase 3: import fetcher and start scheduler here
    logger.info("NewsMonitor: NEWS_API_KEY present — Phase 3 news polling ready to wire up.")
