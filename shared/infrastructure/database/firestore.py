"""Firestore async client singleton.

Lazily initializes the Firestore client on first call using service account
credentials from application settings.
"""

from google.cloud import firestore_v1
from google.oauth2 import service_account

from shared.config import get_settings

_firestore_client: firestore_v1.AsyncClient | None = None


def get_firestore() -> firestore_v1.AsyncClient:
    """Return the Firestore async client, initializing it on first call."""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    settings = get_settings()
    cred = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
        {
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "private_key": settings.firebase_private_key.replace("\\n", "\n"),
            "client_email": settings.firebase_client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    _firestore_client = firestore_v1.AsyncClient(
        project=settings.firebase_project_id,
        credentials=cred,
    )
    return _firestore_client
