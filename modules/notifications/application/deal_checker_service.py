"""Deal checker service — scans wishlists for price drops and sends push alerts.

Uses a hybrid trigger strategy:
  - Always notify when current price hits the historical low.
  - Also notify when price drops >=20% from the last alert price, provided at
    least 3 days have passed since that alert.

Rate limits per user:
  - Maximum 3 notifications per hour.
  - Maximum 15 notifications per day.
  - Maximum 1 notification per game every 72 hours.
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

from modules.notifications.domain.entities.push_result import PushPayload
from modules.notifications.infrastructure.services.fcm_service import FcmService
from modules.settings.domain.interfaces.repositories.i_settings_repository import (
    ISettingsRepository,
)
from modules.wishlist.domain.interfaces.repositories.i_wishlist_repository import (
    IWishlistRepository,
)
from shared.domain.interfaces.itad_client import IItadClient

logger = logging.getLogger(__name__)

# Configuration defaults — overridable via environment variables.
_MAX_PER_HOUR: int = int(os.getenv("MAX_NOTIFICATIONS_PER_HOUR", "3"))
_MAX_PER_DAY: int = int(os.getenv("MAX_NOTIFICATIONS_PER_DAY", "15"))
_GAME_COOLDOWN_DAYS: int = int(os.getenv("GAME_ALERT_COOLDOWN_DAYS", "3"))


class DealCheckerService:
    """Periodically checks wishlist prices and sends deal alert push notifications."""

    def __init__(
        self,
        settings_repo: ISettingsRepository,
        itad_client: IItadClient,
        fcm_service: FcmService,
        wishlist_repo: IWishlistRepository | None = None,
    ) -> None:
        self._settings_repo = settings_repo
        self._itad_client = itad_client
        self._fcm_service = fcm_service
        self._wishlist_repo = wishlist_repo

    async def check_all_wishlists(self) -> int:
        """Run a full deal-check cycle across all eligible users.

        Returns:
            Total number of push notifications sent during this run.
        """
        logger.info("DealChecker: starting scan")

        # 1. Get all active tokens for users with deals enabled.
        token_entries = await self._settings_repo.get_all_push_tokens_with_prefs()
        if not token_entries:
            logger.info("DealChecker: no eligible users found")
            return 0

        # Group by uid for per-user rate limiting.
        uid_to_tokens: dict[str, list[dict[str, Any]]] = {}
        for entry in token_entries:
            uid = entry["uid"]
            if uid not in uid_to_tokens:
                uid_to_tokens[uid] = []
            uid_to_tokens[uid].append(entry)

        total_sent = 0
        now = datetime.now(UTC)

        # 2. Process each user's tokens.
        for uid, tokens in uid_to_tokens.items():
            user_result = await self._check_user_deals(uid, tokens, now)
            total_sent += user_result

        logger.info("DealChecker: scan complete — %d notifications sent", total_sent)
        return total_sent

    async def _check_user_deals(
        self,
        uid: str,
        tokens: list[dict[str, Any]],
        now: datetime,
    ) -> int:
        """Check deals for a single user and send notifications.

        Returns:
            Number of notifications sent for this user.
        """
        if self._wishlist_repo is None:
            logger.warning(
                "DealChecker: IWishlistRepository not available — skipping uid=%s",
                uid,
            )
            return 0

        # Per-user rate limit counters (in-memory for this run).
        hour_counts: dict[int, int] = {}
        daily_count = 0
        game_last_alert: dict[str, datetime] = {}
        game_last_price: dict[str, float] = {}

        sent = 0
        payloads_to_send: list[PushPayload] = []

        try:
            wishlist_items = await self._wishlist_repo.get_items(uid)
        except Exception:
            logger.exception("Failed to load wishlist for uid=%s", uid)
            return 0

        if not wishlist_items:
            return 0

        # Process each wishlist item (cap at 50 per user).
        for item in wishlist_items[:50]:
            game_id = item.game_id

            # Rate limit checks.
            if daily_count >= _MAX_PER_DAY:
                break

            hour_key = now.hour
            if hour_counts.get(hour_key, 0) >= _MAX_PER_HOUR:
                continue

            game_key = f"{uid}_{game_id}"
            last_alert = game_last_alert.get(game_key)
            if last_alert and (now - last_alert).days < _GAME_COOLDOWN_DAYS:
                continue

            # Look up ITAD info for this game.
            itad_game_id = await self._itad_client.lookup_game_id(item.title)
            if not itad_game_id:
                continue

            country = "US"  # TODO: Get from user settings.
            current_deals = await self._itad_client.get_prices_for_game(
                itad_game_id,
                country,
            )
            historical_low = await self._itad_client.get_historical_low(
                itad_game_id,
                country,
            )

            if not current_deals and not historical_low:
                continue

            # Find the best (lowest) current deal.
            best_current = min(current_deals, key=lambda d: d.price) if current_deals else None

            # Evaluate hybrid trigger.
            should_notify = False

            if historical_low and best_current and best_current.price <= historical_low.price:
                should_notify = True
            elif (
                best_current
                and last_alert
                and game_last_price.get(game_id, float("inf")) > 0
                and best_current.price <= game_last_price[game_id] * 0.8
            ):
                days_since = (now - last_alert).days
                if days_since >= _GAME_COOLDOWN_DAYS:
                    should_notify = True

            if not should_notify or not best_current:
                continue

            # Build push notification payload for each token.
            discount_pct = self._calc_discount(best_current)

            for token_info in tokens:
                if daily_count >= _MAX_PER_DAY:
                    break

                hour_key = now.hour
                if hour_counts.get(hour_key, 0) >= _MAX_PER_HOUR:
                    break

                payload = PushPayload(
                    expo_token=token_info["expo_token"],
                    title=f"Oferta: {item.title}",
                    body=(
                        f"{best_current.store_name} — "
                        f"${best_current.price:.2f} ({discount_pct}% dto.)"
                    ),
                    data={
                        "game_id": game_id,
                        "game_title": item.title,
                        "store_name": best_current.store_name,
                        "discount_percentage": str(discount_pct),
                        "price": f"{best_current.price:.2f}",
                    },
                )
                payloads_to_send.append(payload)

            # Update tracking.
            game_last_alert[game_key] = now
            game_last_price[game_id] = best_current.price

        # Send batched payloads.
        if payloads_to_send:
            results = await self._fcm_service.send_batch(payloads_to_send)
            for result in results:
                if result.success:
                    sent += 1
                    hour_counts[now.hour] = hour_counts.get(now.hour, 0) + 1
                    daily_count += 1

        # Save deal alert tracking data.
        for item in wishlist_items[:50]:
            game_id = item.game_id
            game_key = f"{uid}_{game_id}"
            if game_key in game_last_alert:
                last_price = game_last_price.get(game_id, 0)
                await self._settings_repo.save_deal_alert(
                    uid,
                    game_id,
                    {
                        "last_alert_price": last_price,
                        "last_alert_at": now.isoformat(),
                    },
                )

        return sent

    @staticmethod
    def _calc_discount(deal: object) -> int:
        """Calculate discount percentage from a deal price."""
        from modules.games.domain.entities.itad import Deal as ItadDeal

        d = deal if isinstance(deal, ItadDeal) else None
        if not d or d.regular_price <= 0:
            return 0
        return int(
            (d.regular_price - d.price) / d.regular_price * 100,
        )
