# Security hardening and release gate

Updated 2026-09-13. **This is not a penetration-test certificate or production approval.**
The application was reviewed and hardened locally. Remote hosting, real delivery providers,
production PostgreSQL, operating-system controls, and an independent penetration test remain unverified.

## Current database status — important

The configured local database is still `bloodlink.db`, ordinary SQLite. **Its existing data has
not been encrypted yet.** Full-database SQLCipher support and a non-overwriting conversion
command are implemented and tested. Activation is deliberately pending confirmation of the
production database/host and durable recovery-key custody. No encryption key was generated
or stored for the real database, and `.env` was not changed.

The additive `02a_security_rate_limits` migration was applied to the local database. It only
creates the rate-limit table/index and updates Alembic's revision. SHA-256 digests of every
pre-existing application table's rows were equal before and after the migration. Existing
donor/patient records, original database files and older backups were preserved.

## Implemented controls

- Administrator authentication/authorization on the previously open legacy donations APIs,
  with the authenticated administrator recorded instead of a hard-coded user ID.
- Explicit JWT token purposes and mandatory expiration. Password-reset tokens cannot be
  used as login credentials. Role/account-link changes revoke previous sessions.
- Browser sessions use HttpOnly cookies, Secure over HTTPS/in production, SameSite=Strict,
  and origin validation for cookie-authenticated mutations. The old local-storage key now
  contains only the non-secret `cookie-session` marker. API clients can still use Bearer JWTs.
- New hashes use bcrypt-SHA256, avoiding bcrypt's 72-byte truncation. Existing bcrypt hashes
  remain verifiable and are upgraded after a successful login.
- Public registration cannot reclaim disabled or existing pending accounts just by supplying
  known contact details. New direct registrations and emailed setup links remain available.
  Existing pending registrations must use the email setup/resend path.
- Conditional database updates protect single-use password setup/reset and email responses
  against concurrent reuse. New email-response tokens are stored as SHA-256 digests.
  Previously issued plaintext tokens remain compatible until expiry; they were not rewritten.
- Shared, atomic database-backed throttling: 30 public login attempts/IP/15 minutes,
  30 combined public registration/recovery/email-response submissions/IP/15 minutes,
  and 10 login attempts/account/15 minutes. Account/IP identifiers are HMACed in storage.
  Review these limits for campus NATs and registration events. HTTP 429 includes Retry-After.
- Request body bounds, compressed/uncompressed workbook limits, defused XML parsing, and
  spreadsheet formula neutralization for donor/history/campaign/match exports.
- Browser-provider allowlisting for Web Push, outbound timeouts, redirect rejection, and
  rejection of subscription reassignment to another account. Legacy stored endpoints are
  revalidated at send time. Browser account switching may require unsubscribing first.
- Stored-XSS fixes in blood requests, matching, notifications and settings. Enforced
  `script-src 'self'`; inline event handlers/script blocks were removed. Chart.js and Lucide
  are fixed local bundles with licenses and checksums in `frontend/vendor/README.md`.
- No-store for non-static responses, no-referrer, anti-framing, MIME-sniffing protection,
  restricted browser permissions, and validation errors that do not echo submitted secrets.
- Production host allowlisting, HTTPS redirection/HSTS, disabled API documentation,
  minimum JWT-secret length, fixed HS256 algorithm, SQLCipher enforcement for SQLite, and
  certificate-verified TLS (`sslmode=verify-full`) for public PostgreSQL. An explicit
  Render-private-network TLS exception is described in DEPLOYMENT.md.
- SQL parameter values are hidden in exception logging; email addresses and provider error
  bodies are no longer deliberately logged by delivery code. Uvicorn access-log filtering
  strips query strings, email bearer links and client addresses. Configure upstream logs too.
- The previous fake MFA toggle is disabled and labelled accurately; **real MFA is not implemented**.

Existing access tokens issued before the explicit-purpose change require signing in again.
Existing passwords and account data are retained. The browser's existing session marker and
API helpers were preserved to minimize changes to working modules.

## Encryption activation — SQLite

1. Confirm the intended deployment and maintenance window. Stop all writers. Keep a protected,
   recoverable backup and test recovery before changing the active database.
2. Install `requirements-security.txt` using the application's Python environment. The pinned
   cross-platform community SQLCipher wheel is an additional binary supply-chain dependency;
   production owners should review or obtain their approved build.
3. Generate a random 32-byte key in an approved secret manager and maintain a separately
   protected recovery copy. Configure its 64-character hex representation through
   `DATABASE_ENCRYPTION_KEY`, **or** `DATABASE_ENCRYPTION_KEY_FILE` (not both). Keep a key file
   outside the repository, restricted to the application identity. Never paste the key into
   chat, commit it, store it beside the database, or reuse the JWT secret.
4. Create a new file while the original remains untouched:

   ```text
   python -m backend.security.encrypt_database --source bloodlink.db --destination bloodlink.encrypted.db
   ```

   The tool rejects existing destinations and invalid sources, exports through SQLCipher,
   validates encrypted pages/database integrity and every table's row count, and preserves
   the source. Failed destination files must be reviewed; it does not silently delete them.
5. Point `DATABASE_URL` to `sqlite:///./bloodlink.encrypted.db`, keep the key available,
   run `python -m alembic upgrade head`, restart, and exercise real workflows in staging.
   With a configured key the application refuses plaintext or wrong-key files; it never
   silently falls back to an unencrypted driver.
6. Test restoration on a separate machine/identity with the recovery key. Then coordinate
   retirement/encryption of the plaintext original, older `.db` backups, exports and any
   archives. These copies are not protected by encrypting only the new active database.

SQLCipher protects database files/pages at rest, not a compromised running application,
authorized database queries, process memory, downloaded exports or screenshots. Use encrypted
volumes/swap and protected backups as well. An optional SQLCipher heap-wiping setting caused
a Windows community-wheel crash during testing and is not enabled; page encryption and
authentication were tested independently and remain enabled when a key is configured.

## PostgreSQL / hosted deployment

Do not supply a SQLCipher key for PostgreSQL. Require host-managed encrypted database volumes,
snapshots and backups, appropriately controlled KMS keys, and documented restore procedures.
Application code cannot prove or enable those infrastructure guarantees. Use a least-privilege
runtime database role and a separate migration identity; restrict database network access.
Public production connections require `sslmode=verify-full` and the provider's trusted
CA/hostname configuration. Render internal self-signed connections can explicitly use
`DATABASE_TLS_MODE=render-internal`, enforcing encrypted transport without certificate
identity verification, restricted to Render internal dpg-* hosts. See DEPLOYMENT.md.
Render handles HTTPS redirection at its edge; the app retains Secure cookies and HSTS.

Set these before deploying; `.env.example` contains placeholders, not usable secrets:

```text
APP_ENV=production
ALLOWED_HOSTS=your-approved-host.example
BACKEND_URL=https://your-approved-host.example
FRONTEND_URL=https://your-approved-host.example
JWT_ALGORITHM=HS256
SECRET_KEY=<independent, cryptographically random secret>
```

Install `requirements-security.txt` if using SQLite/SQLCipher, otherwise `requirements.txt`.
Apply `python -m alembic upgrade head` before starting Uvicorn. Set `--proxy-headers` and
`--forwarded-allow-ips` only for your actual trusted proxy addresses/CIDRs; never trust
arbitrary client-supplied forwarding headers. Terminate TLS at the approved ingress, redirect
HTTP there, prevent direct backend access and validate that HTTPS detection/rate-limit client
identities are correct. Avoid storing sensitive URLs in proxy/platform logs (`--no-access-log`
is also an option for Uvicorn). Do not use development mode for real sensitive data.

## Verification evidence

Initial security run: **61 tests passed** (one framework deprecation warning), frontend
stored-XSS rendering checks passed, and all nine local page/asset checks plus database
connectivity passed. `pip check` found no broken requirements. No real email/push
messages were sent and no remote deployment was changed.

- `python -m pytest -q tests --junitxml=security-test-results.xml`
- `node tests/frontend-security.cjs`
- `node --check` on changed scripts and vendored bundles
- `python -m compileall -q backend tests`
- `python -m pip check`
- `python -m pip_audit -r requirements-security.txt --format json --output security-dependency-audit-after.json`

Tests use disposable databases, random test keys and no real email/push delivery. Core API
tests run on both plain SQLite and encrypted SQLCipher. Coverage includes authorization,
cookie/CSRF handling, token misuse/replay, limits/concurrency, registration, password recovery,
request creation/matching, donor responses, single rewards, certificate ownership/downloads,
Excel import/export, SQLCipher conversion/wrong-key rejection, migrations and production guards.

The original dependency scan found advisories for cryptography and ecdsa. Cryptography was
patched and python-jose/ecdsa were replaced with PyJWT. Unused fastapi-mail was removed because
it constrained cryptography to the affected major version; delivery uses SMTP/Resend directly.
The final resolved production dependency scan reported no known vulnerabilities at scan time.
This does not audit vendored native libraries, JavaScript, infrastructure or undisclosed issues.

## Release blockers / independent pentest scope

- Activate and prove real database/backup encryption and key recovery; currently NOT complete.
- Configure and test actual production TLS, proxy trust, host allowlists, filesystem permissions,
  encrypted volumes/swap/backups, database roles/network rules, and secret rotation.
- Add real administrator MFA (prefer a maintained identity provider), account lifecycle controls
  and verified ownership/consent policy for public registrations.
- Perform browser/PWA/device regression testing and real provider delivery tests with authorized
  test recipients. API tests and HTML-rendering checks are not full browser acceptance tests.
- Add access-controlled, tamper-resistant security/audit events, monitoring/alerts, retention,
  incident response, export governance and restore drills. Local logs are not an audit system.
- Review remaining third-party font/CSS requests, independently audit native/JS dependencies,
  load-test limits and assess resource exhaustion at ingress/egress (including SSRF network rules).
- Commission an authorized independent deployed-system test with admin/donor test accounts and
  synthetic data: OWASP ASVS Level 2 baseline, access control/IDOR, sessions, injection/XSS,
  CSRF, SSRF, imports/exports, resets, replay/races, privacy, configuration and dependency risks.
  Re-test findings before accepting real sensitive data. Passing the local suite is not a promise
  that every functionality or penetration-test case passes.

## Design references

- [OWASP cryptographic storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [OWASP key management](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [SQLCipher encryption/export API](https://www.zetetic.net/sqlcipher/sqlcipher-api/)
