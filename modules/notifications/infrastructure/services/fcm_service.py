"""Firebase Cloud Messaging service for push notification delivery.

Uses the Firebase Admin SDK ``messaging`` module to send notifications to Expo
push tokens (which are FCM-compatible).
"""

import asyncio
import logging

from firebase_admin import messaging

from modules.notifications.domain.entities.push_result import PushPayload, PushResult
from shared.infrastructure.security.firebase_client import get_firebase_app

logger = logging.getLogger(__name__)


class FcmService:
    """Sends push notifications via Firebase Cloud Messaging (FCM)."""

    def __init__(self) -> None:
        self._app = get_firebase_app()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def send_single(
        self,
        expo_token: str,
        title: str,
        body: str,
        data: dict[str, str],
    ) -> PushResult:
        """Send a single push notification to one Expo token.

        Args:
            expo_token: Expo push token (e.g. ``~ExponentPushToken[...]``).
            title: Notification title.
            body: Notification body text.
            data: Custom key-value fields included in the FCM payload.

        Returns:
            A :class:`PushResult` indicating success or failure.
        """
        try:
            message = self._build_message(expo_token, title, body, data)
            response_id = await self._send_async(message)
            logger.info("FCM push sent to %s (msg_id=%s)", expo_token[:20], response_id)
            return PushResult(token=expo_token, success=True, response_id=response_id)

        except messaging.InvalidArgumentError:
            logger.warning("Invalid Expo token: %s", expo_token[:30])
            return PushResult(
                token=expo_token,
                success=False,
                error="invalid-token",
            )
        except Exception as exc:  # pragma: no cover
            logger.error("FCM send failed for %s: %s", expo_token[:20], exc)
            return PushResult(token=expo_token, success=False, error=str(exc))

    async def send_batch(self, payloads: list[PushPayload]) -> list[PushResult]:
        """Send multiple push notifications (one-at-a-time for error isolation).

        Each message is sent independently so a failure on one token does not
        abort the entire batch.

        Args:
            payloads: List of notification payloads to dispatch.

        Returns:
            A list of :class:`PushResult` (one per input payload, same order).
        """
        results = []
        for payload in payloads:
            result = await self.send_single(
                expo_token=payload.expo_token,
                title=payload.title,
                body=payload.body,
                data=payload.data,
            )
            results.append(result)

            # Clean up invalid tokens immediately
            if result.error in ("invalid-token", "not-registered"):
                logger.warning(
                    "Removing stale token %s (error=%s)",
                    payload.expo_token[:30],
                    result.error,
                )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_message(
        expo_token: str, title: str, body: str, data: dict[str, str]
    ) -> messaging.Message:
        """Construct a Firebase ``Message`` from notification parameters."""
        return messaging.Message(
            token=expo_token,
            notification=messaging.Notification(title=title, body=body),
            data=data,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(
                    color="#1a73e8",
                ),
            ),
            apns=messaging.ApnsConfig(
                headers={"priority": "10"},
                payload=messaging.APNSPayload(
                    sound=messaging.APNSSound("default"),
                ),
            ),
        )

    async def _send_async(self, message: messaging.Message) -> str:
        """Send a FCM message and return the response ID."""
        # Firebase Admin SDK is synchronous; wrap in executor for async compatibility.
        loop = asyncio.get_event_loop()
        response_id = await loop.run_in_executor(None, messaging.send_message, message)
        return str(response_id)
