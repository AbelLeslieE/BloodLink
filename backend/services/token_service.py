"""
==========================================================
Token Service
==========================================================

Generates and validates secure JWT tokens for donor
response links.

Responsibilities
----------------
- Generate response tokens
- Validate tokens
- Handle expiration
- Prevent invalid signatures

No database logic belongs here.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from backend.config.settings import get_settings

# ==========================================================
# Configuration
# ==========================================================

settings = get_settings()


# ==========================================================
# Token Service
# ==========================================================

class TokenService:
    """JWT helper for BloodLink donor response tokens."""

    @staticmethod
    def create_response_token(
        donor_id: int,
        request_id: int,
        action: str,
        expires_hours: int = 24,
    ) -> str:
        """
        Create a signed JWT token.

        Parameters
        ----------
        donor_id : int
            Donor ID.

        request_id : int
            Blood request ID.

        action : str
            accept or decline

        expires_hours : int
            Token validity period.
        """

        now = datetime.now(timezone.utc)

        payload = {

            "donor_id": donor_id,

            "request_id": request_id,

            "action": action,

            "iat": now,

            "exp": now + timedelta(hours=expires_hours),

        }

        return jwt.encode(
            payload,
            settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def verify_token(
        token: str,
    ) -> dict:
        """
        Decode and verify token.
        """

        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )