# BloodLink implementation status

Last updated: 2026-09-29

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

## Completed in the donor data-quality phase

- The Technical Portal now has an administrator-only cleanup queue covering
  incomplete eligibility fields, missing or invalid contact details, missing
  locations, stale profiles, and possible duplicates.
- Profile completeness is scored consistently, with issue explanations and
  high-priority, review, and informational classifications.
- Duplicate suggestions use normalized exact email, phone, or name-and-date-of-
  birth signals. BloodLink never automatically merges, edits, or deletes the
  records.
- Administrators can search, filter, paginate, change the stale-record window,
  and export the current queue as a spreadsheet-safe CSV.
- Queue exports are recorded in the signed audit log, and donor accounts cannot
  access the dashboard or export.
- Automated data-quality tests run against both normal and encrypted SQLite.

## Completed in the structured-location and distance-matching phase

- Blood requests now store optional hospital district, city, latitude, and
  longitude alongside the existing free-text place, preserving all historical
  requests and integrations.
- Donor registration and editing now accept validated latitude and longitude,
  and request entry prevents incomplete coordinate pairs.
- Matching calculates great-circle distance when both the hospital and donor
  have coordinates, shows the measured kilometres, and rewards donors within
  transparent 5, 15, 30, and 60 km bands.
- When coordinates are unavailable, matching falls back to normalized same-city
  and same-district scoring; legacy free-text request locations remain usable as
  a district hint.
- Equal scores are ordered deterministically, preferring the geographically
  nearer donor when distance is known.
- Automated tests cover distance calculation, nearest-donor ranking, structured
  locality fallback, coordinate validation, and encrypted-database migration.

## Completed in the request-lifecycle automation phase

- Every request now has an exact expiry deadline calculated from its required
  date and the deployment's configured local timezone.
- Open requests automatically escalate through 48-hour, 24-hour, and 6-hour
  bands; urgent and emergency priorities receive minimum escalation levels.
- Overdue requests automatically become `Expired`, retain their outstanding-unit
  count in the closure reason, and are blocked from matching, outreach links,
  donor responses, and donation recording.
- Lifecycle reconciliation runs during application startup and every relevant
  workflow, so a restart or quiet period cannot leave stale requests actionable.
- Automatic escalations and expirations produce tamper-evident system events in
  the Technical Portal audit log without duplicating events on later checks.
- Manual Closed, Cancelled, and Expired transitions require a meaningful closure
  reason. Reopening clears old closure metadata and is blocked after the deadline.
- Fully supplied requests automatically record a fulfilment closure reason and
  timestamp from confirmed donation units.
- Blood Request screens show deadlines, escalation levels and reasons, closure
  reasons, closure times, Expired/Closed states, and the new status filters.
- Automated tests cover deadline creation, priority escalation, one-time signed
  audits, expiry enforcement, closure-reason validation, reopening, fulfilment
  closure metadata, and encrypted-database migration.

## Completed in the staged donor-outreach phase

- Administrators can divide selected donors into ranked outreach batches of 1
  to 25 donors and choose a 0-to-24-hour wait before releasing the next batch.
- The matching engine's donor order is preserved even when donors are selected
  in a different order in the browser; later stages remain queued without an
  email token or delivery attempt.
- Notifications shows the current stage, queued count, acceptance target, and
  next-stage availability, with a guarded action to release exactly one batch.
- Cooldowns are enforced by the server, not only by the browser, and normal
  resend actions contact only already-sent pending or failed recipients.
- Campaigns stop future staged outreach automatically once acceptances meet the
  request's outstanding-unit target. Closing or expiring a request also blocks
  further releases.
- Existing campaigns are migrated as one already-sent stage, preserving their
  prior delivery and response history.
- CSV reports now include stage and outreach order, and queued and failed
  delivery states remain distinct in the administrator response table.
- Automated tests cover ranked batching, unsent queue protection, cooldown
  enforcement, next-stage release, acceptance-target stopping, resend isolation,
  and encrypted-database migration.

## Partially completed

- Audit coverage records every authenticated mutation with its route, actor,
  result, source address, and response status. Rich before/after field-level
  diffs still need to be added to each business service.
- Backup creation, verification, download, retention history, and deletion are
  complete. Scheduled off-site copies and automatic retention policies are not.
- MFA is optional for each account. A production policy requiring MFA for all
  administrators is not yet enforced.
- Database upgrades complete successfully, but the strict schema-drift check
  still reports historical prototype differences: legacy notification-table
  preservation, donor-response nullability on older installations, and several
  equivalent index/constraint definitions. A dedicated reconciliation migration
  is still required before this check is clean across old and fresh databases.

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

- No remaining correctness item from the current roadmap.

### Operations and donor experience

- Donor-controlled temporary availability, travel radius, and contact hours.
- Blood-drive scheduling, appointment capacity, QR check-in, and reminders.
- Operational analytics such as time-to-match and time-to-fulfil.
- Granular communication consent and quiet-hour preferences.

## Verification

- Migration head: `f1a2b3c4d5e6`
- Security-operations test module: passing
- Full regression suite: **202 passed** on 2026-09-29.
- Unit-fulfilment workflow suite: **26 passed** across normal and encrypted SQLite.
- Donor-deferral workflow suite: **10 passed** across normal and encrypted SQLite.
- Eligibility-policy workflow suite: **10 passed** across normal and encrypted SQLite.
- Donor data-quality workflow suite: **10 passed** across normal and encrypted SQLite.
- Structured-location and distance-matching suite: **7 passed** across normal
  and encrypted SQLite where database integration is required.
- Request-lifecycle automation suite: **10 passed** across normal and encrypted SQLite.
- Staged donor-outreach suite: **6 passed** across normal and encrypted SQLite.
- Deployment/security focused rerun after configuration changes: **42 passed**.
- Frontend stored-XSS checks and JavaScript syntax checks: passing.
- Local browser smoke check: updated login page loaded with no console warnings or errors.
