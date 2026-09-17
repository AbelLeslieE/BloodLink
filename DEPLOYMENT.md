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
(at least 32 bytes) and a strong DEFAULT_VOLUNTEER_PASSWORD. Never reuse the JWT
secret as an encryption key. Existing .env files are not overwritten.
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
| DEFAULT_VOLUNTEER_PASSWORD | Strong initial admin password, needed only on a fresh DB |

Render supplies PORT and RENDER_EXTERNAL_URL. With blank BACKEND_URL/FRONTEND_URL,
both use that HTTPS origin. For a custom domain, set both URLs to its HTTPS origin
and include every verified custom domain plus the onrender.com hostname in
ALLOWED_HOSTS. Render can send health checks to any verified custom domain.
Do not copy the local .env into Render; Render ignores it.

postgres://, postgresql:// and postgresql+psycopg:// URLs all select the installed
psycopg 3 driver. Password escaping and existing query parameters are preserved.
Render SQLite is deliberately rejected because its filesystem is ephemeral.

### PostgreSQL encryption

- For the same-account/same-region Render internal URL (single-label dpg-* host),
  explicitly set DATABASE_TLS_MODE=render-internal. This enforces sslmode=require:
  traffic is encrypted but the self-signed server certificate is NOT authenticated.
  This is a documented, limited private-network exception, not public-host policy.
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

FORWARDED_ALLOW_IPS defaults to loopback. Configure actual trusted proxy IPs/CIDRs
when your ingress topology requires them; never blindly set it to *. Without
correct proxy trust, multiple visitors can share an IP throttle bucket. Account
throttling remains active. Verify client IP handling and load-test in staging.

Render free services block SMTP ports: leave SMTP settings blank and configure
RESEND_API_KEY plus EMAIL_FROM with an authorized sender. Paid SMTP-enabled hosts
can use the existing SMTP configuration. Set a stable VAPID key pair/subject for
push delivery, and test browser permission/subscription from the public HTTPS URL.
Localhost supports browser development; arbitrary HTTP LAN addresses do not
provide all secure-context PWA/push features.

[Render HTTPS behavior](https://render.com/docs/web-services)
[Render health checks](https://render.com/docs/health-checks)
[Render free-plan limits](https://render.com/docs/free)

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
