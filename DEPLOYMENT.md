# Local and Render deployment

Use the same entry point: `python start.py`. It validates configuration, runs
Alembic migrations, and starts the server. Existing accounts are retained.
Back up your database before deployment. Run only one migration/start operation
at a time; for multiple replicas, run `python start.py --migrate-only` once as a
coordinated pre-deploy step and start replicas with Uvicorn after it succeeds.

## Local Windows / Linux / macOS

From the BloodLink repository, use Python 3.11 and your virtual environment:

```text
python -m pip install -r requirements-security.txt
python start.py
```

For a new installation, copy .env.example to .env and set a random SECRET_KEY
(at least 32 bytes), a non-guessable DEFAULT_VOLUNTEER_USERNAME and a strong
DEFAULT_VOLUNTEER_PASSWORD (production requires 16+ characters and rejects names
such as volunteer or admin). Never reuse the JWT secret as an encryption key.
Existing .env files are not overwritten.
Open http://localhost:8000 (or your PORT). The launcher defaults to loopback only.

Leave BACKEND_URL, FRONTEND_URL and ALLOWED_HOSTS blank for local automatic
defaults. If your existing .env has an old cloud URL, clear those URL values for
local use; otherwise emailed links intentionally keep pointing to that URL.
Set explicit public URLs before sharing registration QR codes with other devices.
The frontend and backend must be served from the same origin.

Relative SQLite and key-file paths resolve against the repository, not the
terminal's current directory. Running the absolute path to start.py also works.
The existing plain database remains usable for development. This is NOT an
encryption migration: activate SQLCipher using the copy-and-verify procedure in
SECURITY.md, preserve the recovery key separately, and point DATABASE_URL at the
verified encrypted copy. Do not simply add a key to an existing plaintext file.
Production SQLite refuses to start without SQLCipher and a key.

## Existing Render service

Set the root directory to the folder containing start.py and requirements.txt.
Keep existing production secrets and database; do not replace SECRET_KEY on each
deploy (that logs everyone out).

| Setting | Value |
| --- | --- |
| Build command | pip install -r requirements.txt |
| Start command | python start.py |
| Health check | /healthz |
| PYTHON_VERSION | 3.11.15 |
| APP_ENV | production |
| JWT_ALGORITHM | HS256 |
| SECRET_KEY | Existing strong random production secret |
| DATABASE_URL | Existing PostgreSQL connection URL |
| DATABASE_TLS_MODE | Leave unset for automatic Render database detection |
| FORWARDED_ALLOW_IPS | Leave unset for the Render private-network default (see proxies below) |
| ALLOWED_HOSTS | Every public hostname, comma-separated |
| DEFAULT_VOLUNTEER_USERNAME | Non-guessable bootstrap admin name (not volunteer/admin) |
| DEFAULT_VOLUNTEER_PASSWORD | 16+ character initial admin password; remove after the first boot |

Render supplies PORT and RENDER_EXTERNAL_URL. With blank BACKEND_URL/FRONTEND_URL,
both use that HTTPS origin. For a custom domain, set both URLs to its HTTPS origin
and include every verified custom domain plus the onrender.com hostname in
ALLOWED_HOSTS. Render can send health checks to any verified custom domain.
Do not copy the local .env into Render; Render ignores it.

postgres://, postgresql:// and postgresql+psycopg:// URLs all select the installed
psycopg 3 driver. Password escaping and existing query parameters are preserved.
Render SQLite is deliberately rejected because its filesystem is ephemeral.

### PostgreSQL encryption

- Render-managed internal and external dpg-* database hosts are detected
  automatically when DATABASE_TLS_MODE is unset. The client enforces
  sslmode=require, matching Render's supported TLS configuration. You can set
  DATABASE_TLS_MODE=render-internal or render-managed explicitly when needed.
- On Render, a third-party provider URL that explicitly includes
  sslmode=require is preserved. Plaintext-capable modes such as disable and
  prefer remain rejected in production.
- For public PostgreSQL URLs, use DATABASE_TLS_MODE=verify-full (default).
  Certificate and hostname verification are required. The CA defaults to certifi;
  set DATABASE_CA_FILE or the URL's sslrootcert to the provider's trusted PEM bundle
  if necessary. Do not fix certificate errors by disabling verification.
- Clear DATABASE_ENCRYPTION_KEY and DATABASE_ENCRYPTION_KEY_FILE for PostgreSQL;
  those settings are exclusively for SQLCipher.
- Render documents AES-256 encryption at rest, including backups. Verify your
  actual instance, backup retention, network restrictions and recovery procedure.
  Code changes cannot attest to a live database's infrastructure configuration.

[Render database TLS/encryption documentation](https://render.com/docs/postgresql-creating-connecting)

### HTTPS, proxies, email and push

Render's edge redirects HTTP to HTTPS and terminates TLS before forwarding HTTP.
The app therefore does not redirect again on Render; secure cookies, HSTS and
host checks remain enabled. Other production hosts retain app HTTPS redirection.
Do not expose Render's internal application port outside trusted infrastructure.

FORWARDED_ALLOW_IPS controls which proxies' X-Forwarded-For headers are trusted.
Locally it defaults to loopback. On Render it defaults to the private/CGNAT ranges
(10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 100.64.0.0/10, 127.0.0.1), because the
app port is reachable only through Render's private network. With an explicit list,
Uvicorn walks the header from the right and stops at the first untrusted hop, so a
visitor cannot spoof their own address; do not use `*`, which trusts the leftmost
(client-supplied) entry. Without correct proxy trust every visitor shares one
throttle bucket and thirty failed attempts would block sign-in for everyone.

Verify after every deploy: sign in as an administrator and call
`GET /api/admin/diagnostics/request` twice from the same machine, once plain and
once with an added header `X-Forwarded-For: 1.2.3.4`. `resolved_client_ip` must be
your real public address both times. If it shows a private address for everyone,
Render's proxy peer is outside the default ranges: set FORWARDED_ALLOW_IPS to that
peer's range. The startup log line beginning `Security posture:` shows the same
values without signing in.

Render free services block SMTP ports: leave SMTP settings blank and configure
RESEND_API_KEY plus EMAIL_FROM with an authorized sender. Paid SMTP-enabled hosts
can use the existing SMTP configuration. Set a stable VAPID key pair/subject for
push delivery, and test browser permission/subscription from the public HTTPS URL.
Localhost supports browser development; arbitrary HTTP LAN addresses do not
provide all secure-context PWA/push features.

[Render HTTPS behavior](https://render.com/docs/web-services)
[Render health checks](https://render.com/docs/health-checks)
[Render free-plan limits](https://render.com/docs/free)

## Pre-hosting checklist

1. Repository visibility is private and `git rev-list --all --objects | grep bloodlink.db`
   prints nothing (no database file anywhere in history).
2. Render environment: APP_ENV=production, random SECRET_KEY, PostgreSQL DATABASE_URL,
   ALLOWED_HOSTS, non-guessable DEFAULT_VOLUNTEER_USERNAME, 16+ character
   DEFAULT_VOLUNTEER_PASSWORD, RESEND_API_KEY and EMAIL_FROM.
3. First boot: the log shows `Security posture: production=True docs_disabled=True`.
4. Sign in as the bootstrap administrator, change the password from Settings →
   Security (this signs every session out), then remove DEFAULT_VOLUNTEER_PASSWORD
   from the environment and redeploy. The posture line must now show
   `bootstrap_password_configured=False`.
5. Run the proxy-trust check with `GET /api/admin/diagnostics/request` described above.
6. Enable two-factor authentication on the Render and GitHub accounts themselves.

## Verification and rollout

Latest local verification: 79 tests passed (one framework deprecation warning).
Frontend XSS checks, Python compilation and dependency consistency checks passed.
Windows runtime tested here: Python 3.11.0; Render's configured 3.11.15/Linux
runtime has not been executed here. Upgrade the old local Python before production use.

Run `python -m pytest -q tests` and `node tests/frontend-security.cjs`.
Deployment tests include actual local process startup, migrations and cookie login
on disposable plaintext and encrypted SQLite databases. PostgreSQL URL/driver/TLS
and Render configuration tests do not substitute for a live PostgreSQL integration
test. No real Render deployment or real email/push is performed by this suite.

Before accepting sensitive data, use a staging PostgreSQL database: migrate,
check /healthz, sign in as admin/donor, test registration/recovery email, matching,
donation confirmation, certificate/download/export, PWA/push, and restore a backup.
Recheck TLS, custom-domain cookies, proxy IPs and network access controls. Review
the remaining production security blockers in SECURITY.md.

render.yaml is optional for a NEW service and can create a billable starter
service if you apply it. It does not create or replace a database. No deployment,
purchase, secret rotation or real database conversion is done merely by adding it.
