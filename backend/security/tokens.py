"""Store only a digest of new one-time email links."""
import hashlib


def email_token_digest(token: str) -> str:
    return "sha256:" + hashlib.sha256(token.encode("utf-8")).hexdigest()
