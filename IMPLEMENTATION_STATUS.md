# BloodLink implementation status

Last updated: 2026-09-27

This report is the project-level record of what is complete, what is partially
implemented, and what remains. It should be updated after every implementation
phase.

## Completed in the security operations phase

- Administrator-only Technical Portal with security summary cards and separate
  Audit logs, Backups, MFA, and Sessions workspaces.
- Database-backed individual sessions with device, IP address, last-seen,
  expiry, MFA verification, and independent revocation.
- Existing high-security logout behavior retained: normal logout closes every
  session for the account. The Technical Portal can revoke one session.
- Standards-compatible TOTP MFA enrollment using authenticator apps.
- Encrypted MFA seeds, replay-resistant TOTP verification, one-time hashed
  recovery codes, recovery-code regeneration, self-service disable, and audited
  administrator reset for another user.
- MFA challenge added to the normal sign-in screen.
- Append-only audit records for authentication, MFA, session, backup, and every
  authenticated data-changing API request.
- Per-record HMAC integrity verification and administrator CSV export.
- Real encrypted logical database snapshots for both SQLite and PostgreSQL,
  including compression, SHA-256 checksums, verification, download, metadata,
  and audited deletion.
- Production backups fail safely unless a dedicated encryption key and storage
  directory are configured.
- Render Blueprint includes a persistent backup disk and secret key setting.
- Fake Settings-page backup and session messages removed; those controls now
  open the real Technical Portal.
- Automated tests cover session creation, administrator authorization, MFA
  enrollment and recovery login, audit integrity, and the full backup lifecycle.

## Completed in the unit-based fulfilment phase

- Blood requests now track requested, fulfilled, and remaining units separately.
- A multi-unit request remains `Partially Fulfilled` until confirmed donation
  units reach the requested total.
- Several registered or external donors can contribute to one request, with the
  actual units stored on each donation record.
- Atomic allocation prevents overfilling a request or racing confirmations from
  claiming more units than remain.
- Administrators cannot manually mark a request fulfilled or reopen a fully
  supplied request; fulfilment is derived from confirmed donation records.
- Closing a donor outreach campaign no longer falsely marks its blood request
  as fulfilled, and old email links stop accepting responses after closure.
- Blood Requests, Donor Dashboard, Notifications, matching, and dashboard totals
  now understand partial fulfilment and show unit progress.
- The migration backfills existing unit totals from donation history and repairs
  legacy fulfilled statuses that have no supporting donation record.
- Regression tests cover multiple donors, partial and final fulfilment, overfill
  rejection, manual-status rejection, and outreach closure.

## Completed in the donor-deferral phase

- Administrators can record a temporary donor deferral with a required future
  eligible date and reason, or mark a donor indefinitely unavailable.
- Confirmed whole-blood donations automatically create gender-aware recovery
  deferrals using deployment-configurable 90/120-day defaults.
- Elapsed deferrals automatically restore donors to `Available` without a
  scheduled job being required.
- Deferred donors are excluded from matching, saved selections, availability
  totals, email and push outreach, donor dashboard requests, and acceptance links.
- Resend campaigns reclassify newly deferred recipients as ineligible instead
  of sending them another request.
- Admin donor details, editing, filters, Excel exports, and the donor dashboard
  expose deferral status and next-eligible dates.
- The migration repairs legacy donors left indefinitely unavailable by an older
  confirmed donation and preserves manual unavailability without a donation date.
- Automated deferral tests run against both normal and encrypted SQLite.

## Completed in the eligibility-policy phase

- The Technical Portal now includes configurable donor pre-screening rules for
  age, weight, recorded haemoglobin, recorded blood pressure, and incomplete
  profiles.
- National defaults are age 18–65, minimum weight 45 kg, haemoglobin at least
  12.5 g/dL, and acceptable blood-pressure screening. Enforced configuration
  may make these thresholds stricter but cannot weaken the baseline.
- The initial mode is `ADVISORY`, which explains recorded failures without
  silently removing legacy donors from current operations.
- Switching to `ENFORCED` requires an administrator to record a qualified
  medical officer's name, review notes, and explicit confirmation. Each change
  is versioned and written to the signed audit log.
- Enforced rules are applied consistently to matching, saved selections,
  availability counts, email and push outreach, resends, donor dashboard
  requests, and acceptance links.
- Medication and free-text medical conditions are flagged for human review and
  are never automatically treated as clinical disqualifications.
- Matching cards explain advisory screening issues, while the portal reports
  pass, review-needed, and blocked counts. Every surface states that final donor
  fitness remains the blood centre's medical decision.
- Automated policy tests run against both normal and encrypted SQLite.

## Partially completed

- Audit coverage records every authenticated mutation with its route, actor,
  result, source address, and response status. Rich before/after field-level
  diffs still need to be added to each business service.
- Backup creation, verification, download, retention history, and deletion are
  complete. Scheduled off-site copies and automatic retention policies are not.
- MFA is optional for each account. A production policy requiring MFA for all
  administrators is not yet enforced.

## Not yet completed

### Security operations

- Reviewed, guarded backup restore workflow with dry-run validation and a
  two-administrator approval process.
- Automated off-site backup replication and restore drills.
- Field-level audit diffs and long-term audit export/retention policy.
- Mandatory MFA policy for privileged accounts.
- Email security alerts for new-device login, MFA reset, and mass session
  revocation.

### Core blood-request correctness

- Structured hospital district/city/coordinates and distance-based matching.
- Request expiry, escalation, and closure-reason automation.

### Operations and donor experience

- Staged donor outreach to reduce alert fatigue.
- Donor-controlled temporary availability, travel radius, and contact hours.
- Blood-drive scheduling, appointment capacity, QR check-in, and reminders.
- Data-quality dashboard for duplicate and stale donor records.
- Operational analytics such as time-to-match and time-to-fulfil.
- Granular communication consent and quiet-hour preferences.

## Verification

- Migration head: `c8d9e0f1a2b3`
- Security-operations test module: passing
- Full regression suite: **169 passed** on 2026-09-27.
- Unit-fulfilment workflow suite: **26 passed** across normal and encrypted SQLite.
- Donor-deferral workflow suite: **10 passed** across normal and encrypted SQLite.
- Eligibility-policy workflow suite: **10 passed** across normal and encrypted SQLite.
- Deployment/security focused rerun after configuration changes: **42 passed**.
- Frontend stored-XSS checks and JavaScript syntax checks: passing.
- Local browser smoke check: updated login page loaded with no console warnings or errors.
