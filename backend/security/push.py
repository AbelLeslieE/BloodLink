"""Restrict outbound Web Push to browser-provider endpoints, never arbitrary URLs."""
from urllib.parse import urlsplit
import base64
import binascii
import requests


class PushSession(requests.Session):
    def request(self, method, url, **kwargs):
        validate_push_endpoint(url)
        kwargs["allow_redirects"] = False
        kwargs.setdefault("timeout", 10)
        return super().request(method, url, **kwargs)


def validate_push_endpoint(value: str) -> str:
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        allowed = (host in {"fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com"}
                   or host.endswith(".notify.windows.com"))
        if (url.scheme != "https" or not allowed or url.port not in {None, 443}
                or url.username is not None or url.password is not None or url.fragment
                or not url.path or "\\" in value or any(c.isspace() for c in value)):
            raise ValueError("Unsupported browser push endpoint.")
    except (ValueError, TypeError) as error:
        raise ValueError("Unsupported browser push endpoint.") from error
    return value


def validate_push_keys(keys: dict[str, str]) -> dict[str, str]:
    for name, size in (("p256dh", 65), ("auth", 16)):
        value = keys.get(name, "")
        try:
            if len(value) > 128:
                raise ValueError()
            decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
            if len(decoded) != size or (name == "p256dh" and decoded[0] != 4):
                raise ValueError()
        except (ValueError, binascii.Error) as error:
            raise ValueError("Invalid browser push keys.") from error
    return keys
