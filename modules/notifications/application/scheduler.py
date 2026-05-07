"""APScheduler integration for the deal checker background task."""

import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from fastapi import FastAPI

from composition.dependencies import (
    get_fcm_service,
    get_itad_client,
    get_settings_repository,
    get_wishlist_repository,
)
from modules.notifications.application.deal_checker_service import DealCheckerService

logger = logging.getLogger(__name__)


def start_scheduler(app: FastAPI) -> AsyncIOScheduler:
    """Create and start the APScheduler with the deal checker job.

    The scheduler runs as an async background task inside the FastAPI process.
    It is configured to run at a fixed interval (default: every 6 hours).

    Args:
        app: The FastAPI application instance (used to store the scheduler ref).

    Returns:
        The started AsyncIOScheduler instance.
    """
    interval_seconds = int(os.getenv("DEAL_CHECKER_INTERVAL", "21600"))

    scheduler = AsyncIOScheduler(timezone="UTC")

    def _run_deal_checker() -> None:
        """Sync wrapper that runs the async deal checker in an event loop."""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            settings_repo = get_settings_repository()
            itad_client = get_itad_client()
            fcm_service = get_fcm_service()
            wishlist_repo = get_wishlist_repository()

            checker = DealCheckerService(
                settings_repo=settings_repo,
                itad_client=itad_client,
                fcm_service=fcm_service,
                wishlist_repo=wishlist_repo,
            )
            loop.run_until_complete(checker.check_all_wishlists())
        except Exception:  # pragma: no cover
            logger.exception("DealChecker job failed")
        finally:
            loop.close()

    scheduler.add_job(
        _run_deal_checker,
        "interval",
        seconds=interval_seconds,
        id="deal_checker",
        max_instances=1,
        replace_existing=True,
    )

    scheduler.start()
    logger.info("DealChecker scheduler started (interval=%ds)", interval_seconds)
    return scheduler
