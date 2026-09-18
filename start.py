"""Identical local/Render entry point: python start.py (or its absolute path)."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def server_options(settings):
    from backend.config.settings import ConfigurationError, forwarded_allow_ips
    try:
        port = int(os.getenv("PORT", "10000" if settings.on_render else "8000"))
    except ValueError:
        raise ConfigurationError("PORT must be an integer.") from None
    if not 1 <= port <= 65535:
        raise ConfigurationError("PORT must be between 1 and 65535.")
    return dict(
        host="0.0.0.0" if settings.on_render else os.getenv("HOST", "127.0.0.1"),
        port=port,
        proxy_headers=True,
        forwarded_allow_ips=forwarded_allow_ips(settings),
    )


def logging_config():
    """Uvicorn's default config has no root handler, which silently drops the
    application's INFO records such as the startup security posture line."""
    import copy
    from uvicorn.config import LOGGING_CONFIG
    config = copy.deepcopy(LOGGING_CONFIG)
    config["root"] = {"handlers": ["default"], "level": "INFO"}
    return config


def main():
    os.chdir(ROOT)
    from backend.config.settings import get_settings
    from alembic import command
    from alembic.config import Config
    import uvicorn

    options = server_options(get_settings())
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    if "--migrate-only" not in sys.argv:
        uvicorn.run("backend.main:app", log_config=logging_config(), **options)


if __name__ == "__main__":
    main()
