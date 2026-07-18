"""Pydantic schemas used by the authentication API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Access token details returned after a successful login."""

    access_token: str
    token_type: str = "bearer"
    volunteer_name: str


class TokenData(BaseModel):
    """Decoded token data used while resolving the current volunteer."""

    username: str = Field(min_length=1, max_length=100)


class LogoutResponse(BaseModel):
    """Response returned by the temporary logout endpoint."""

    detail: str
