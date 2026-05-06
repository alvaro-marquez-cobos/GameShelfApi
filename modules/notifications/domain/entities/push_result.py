"""Push notification result entities."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PushResult:
    """Result of sending a single push notification via FCM.

    Attributes:
        token: The Expo/FCM token the message was sent to.
        success: Whether the message was delivered successfully.
        error: Error type if delivery failed (e.g. "invalid-token", "not-registered").
        response_id: Firebase messaging response ID when successful.
    """

    token: str
    success: bool
    error: str | None = None
    response_id: str | None = None


@dataclass(frozen=True)
class PushPayload:
    """Data needed to send a single push notification.

    Attributes:
        expo_token: Expo/FCM token to deliver the message to.
        title: Notification title text.
        body: Notification body text.
        data: Additional payload fields (game_id, store_name, etc.).
    """

    expo_token: str
    title: str
    body: str
    data: dict[str, str]
