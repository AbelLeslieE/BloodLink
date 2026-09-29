"""Response protections, bounded bodies, throttling, and mutation auditing."""
import logging

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.datastructures import MutableHeaders
from starlette.concurrency import run_in_threadpool
from backend.security.rate_limit import consume_limit


logger = logging.getLogger(__name__)


class SecurityMiddleware:
    def __init__(self, app, production=False):
        self.app, self.production = app, production

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "")

        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
                headers["Content-Security-Policy"] = (
                    "default-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; "
                    "form-action 'self'; script-src 'self'; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                    "img-src 'self' data: blob:; connect-src 'self'; worker-src 'self'; media-src 'self' blob:"
                )
                if not path.startswith("/static/"):
                    headers["Cache-Control"] = "no-store"
                    headers["Pragma"] = "no-cache"
                if self.production:
                    headers["Strict-Transport-Security"] = "max-age=31536000"
            await send(message)

        public_sensitive = path.startswith(("/api/auth/login", "/api/auth/password-reset", "/api/donor-registration", "/email/"))
        if public_sensitive and scope["method"] == "POST":
            client = (scope.get("client") or ("unknown",))[0]
            # No trust in arbitrary X-Forwarded-For headers. Configure Uvicorn's
            # trusted proxy addresses at deployment so scope.client is genuine.
            bucket = "login" if path.startswith("/api/auth/login") else "public-registration-recovery"
            allowed = await run_in_threadpool(consume_limit, client, bucket, 30, 900)
            if not allowed:
                return await JSONResponse({"detail": "Too many attempts. Please try again later."}, status_code=429,
                                          headers={"Retry-After": "900"})(scope, receive, secure_send)

        if scope["method"] in {"POST", "PUT", "PATCH", "DELETE"}:
            limit = 11 * 1024 * 1024 if path == "/api/donors/import" else 256 * 1024
            parts, size = [], 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                chunk = message.get("body", b"")
                size += len(chunk)
                if size > limit:
                    return await JSONResponse({"detail": "Request body is too large."}, status_code=413)(scope, receive, secure_send)
                parts.append(chunk)
                if not message.get("more_body", False):
                    break
            delivered = False

            async def bounded_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": b"".join(parts), "more_body": False}
                return await receive()
            return await self.app(scope, bounded_receive, secure_send)
        await self.app(scope, receive, secure_send)


class AuditMutationMiddleware:
    """Record authenticated state changes without retaining request bodies."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        status_code = 500

        async def capture_status(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        await self.app(scope, receive, capture_status)
        path = scope.get("path", "")
        if (
            scope.get("method") not in {"POST", "PUT", "PATCH", "DELETE"}
            or not path.startswith("/api/")
            or path.startswith(("/api/auth/", "/api/security/", "/api/admin/technical/"))
        ):
            return
        state = scope.get("state", {})
        user_id = state.get("audit_user_id")
        if not user_id:
            return

        def persist_event():
            from backend.database import database
            from backend.database.models import User
            from backend.services.audit_service import record_audit_event
            with database.SessionLocal() as session:
                actor = session.get(User, user_id)
                record_audit_event(
                    session,
                    category="DATA_CHANGE",
                    action=f"{scope.get('method')} {path}",
                    result="SUCCESS" if status_code < 400 else "FAILED",
                    actor=actor,
                    actor_username=state.get("audit_username"),
                    request=Request(scope),
                    details={"status_code": status_code},
                )
                session.commit()

        try:
            await run_in_threadpool(persist_event)
        except Exception:
            logger.exception("Unable to persist mutation audit event")
