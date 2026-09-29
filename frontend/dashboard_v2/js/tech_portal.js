import { authenticatedFetch, logoutUser } from "./api.js";

const state = { auditPage: 1, auditPageSize: 25, dataQualityPage: 1, dataQualityPageSize: 25 };

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[character]));
}

function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "—" : date.toLocaleString();
}

function formatBytes(value) {
    if (!Number.isFinite(Number(value))) return "—";
    const bytes = Number(value);
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

async function api(url, options = {}) {
    const response = await authenticatedFetch(url, options);
    if (!response) throw new Error("Your session has ended.");
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
        throw new Error(typeof detail === "string" ? detail : detail?.message || "The operation could not be completed.");
    }
    return data;
}

function showNotice(message, type = "success") {
    const notice = document.getElementById("techNotice");
    if (!notice) return;
    notice.textContent = message;
    notice.className = `tech-notice ${type}`;
    notice.hidden = false;
    window.clearTimeout(showNotice.timer);
    showNotice.timer = window.setTimeout(() => { notice.hidden = true; }, 5000);
}

export function loadTechnicalPortal() {
    return `
        <section class="tech-page">
            <header class="tech-hero glass-card">
                <div>
                    <p class="tech-eyebrow">ADMINISTRATOR OPERATIONS &amp; SAFETY</p>
                    <h1>Technical Portal</h1>
                    <p>Monitor access, protect records, manage backups, and control reviewed donor pre-screening.</p>
                </div>
                <button id="refreshTechnicalPortal" class="tech-button secondary" type="button"><i class="fa-solid fa-rotate"></i> Refresh</button>
            </header>

            <div id="techNotice" class="tech-notice" role="status" aria-live="polite" hidden></div>

            <section id="techSummary" class="tech-summary" aria-label="Security summary">
                <article class="tech-metric glass-card"><span>Audit events · 24h</span><strong>—</strong></article>
                <article class="tech-metric glass-card"><span>Failed events · 24h</span><strong>—</strong></article>
                <article class="tech-metric glass-card"><span>Active sessions</span><strong>—</strong></article>
                <article class="tech-metric glass-card"><span>MFA coverage</span><strong>—</strong></article>
                <article class="tech-metric glass-card"><span>Ready backups</span><strong>—</strong></article>
                <article class="tech-metric glass-card"><span>Eligibility policy</span><strong>—</strong></article>
            </section>

            <nav class="tech-tabs" aria-label="Technical portal sections">
                <button class="active" data-tech-tab="audit" type="button">Audit logs</button>
                <button data-tech-tab="backups" type="button">Backups</button>
                <button data-tech-tab="mfa" type="button">MFA</button>
                <button data-tech-tab="sessions" type="button">Sessions</button>
                <button data-tech-tab="eligibility" type="button">Eligibility rules</button>
                <button data-tech-tab="data-quality" type="button">Data quality</button>
            </nav>

            <section id="tech-audit" class="tech-panel glass-card">
                <div class="tech-panel-header">
                    <div><h2>Audit logs</h2><p>Signed records of authentication, security, and data-changing actions.</p></div>
                    <a class="tech-button secondary" href="/api/admin/technical/audit-logs/export" id="exportAudit"><i class="fa-solid fa-file-export"></i> Export CSV</a>
                </div>
                <form id="auditFilters" class="tech-filters">
                    <input id="auditSearch" type="search" maxlength="120" placeholder="Search actor, action, path, or target">
                    <select id="auditCategory"><option value="">All categories</option><option>AUTHENTICATION</option><option>DATA_CHANGE</option><option>DATA_QUALITY</option><option>ELIGIBILITY</option><option>MFA</option><option>SESSION</option><option>BACKUP</option><option>AUDIT</option><option>SECURITY</option></select>
                    <select id="auditResult"><option value="">All results</option><option>SUCCESS</option><option>FAILED</option><option>PENDING</option></select>
                    <button class="tech-button" type="submit">Apply</button>
                </form>
                <div class="tech-table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Category</th><th>Action</th><th>Result</th><th>Source</th><th>Integrity</th></tr></thead><tbody id="auditRows"><tr><td colspan="7">Loading audit activity…</td></tr></tbody></table></div>
                <div class="tech-pagination"><span id="auditCount">—</span><div><button id="auditPrevious" class="tech-button secondary" type="button">Previous</button><button id="auditNext" class="tech-button secondary" type="button">Next</button></div></div>
            </section>

            <section id="tech-backups" class="tech-panel glass-card" hidden>
                <div class="tech-panel-header">
                    <div><h2>Encrypted backups</h2><p>Create, verify, download, and retire checksummed database snapshots.</p></div>
                    <button id="createBackup" class="tech-button" type="button"><i class="fa-solid fa-database"></i> Create backup</button>
                </div>
                <p id="backupConfiguration" class="tech-callout"></p>
                <div class="tech-table-wrap"><table><thead><tr><th>Created</th><th>Owner</th><th>Contents</th><th>Size</th><th>Status</th><th>Actions</th></tr></thead><tbody id="backupRows"><tr><td colspan="6">Loading backups…</td></tr></tbody></table></div>
            </section>

            <section id="tech-mfa" class="tech-panel glass-card" hidden>
                <div class="tech-panel-header"><div><h2>Multi-factor authentication</h2><p>Manage your authenticator and review protection across active accounts.</p></div></div>
                <article class="tech-subpanel">
                    <div><h3>My account</h3><p id="myMfaStatus">Loading MFA status…</p></div>
                    <div id="myMfaActions"></div>
                </article>
                <div id="mfaEnrollment" class="tech-enrollment" hidden></div>
                <div class="tech-table-wrap"><table><thead><tr><th>User</th><th>Role</th><th>Status</th><th>Recovery codes</th><th>Action</th></tr></thead><tbody id="mfaRows"><tr><td colspan="5">Loading MFA coverage…</td></tr></tbody></table></div>
            </section>

            <section id="tech-sessions" class="tech-panel glass-card" hidden>
                <div class="tech-panel-header">
                    <div><h2>Active sessions</h2><p>Review devices and revoke access immediately.</p></div>
                    <button id="revokeOtherSessions" class="tech-button danger" type="button">Revoke my other sessions</button>
                </div>
                <div class="tech-table-wrap"><table><thead><tr><th>User</th><th>Device</th><th>IP address</th><th>Last seen</th><th>Expires</th><th>MFA</th><th>Action</th></tr></thead><tbody id="sessionRows"><tr><td colspan="7">Loading sessions…</td></tr></tbody></table></div>
            </section>

            <section id="tech-eligibility" class="tech-panel glass-card" hidden>
                <div class="tech-panel-header">
                    <div><h2>Donor eligibility rules</h2><p>Configure operational pre-screening without replacing the blood centre's medical decision.</p></div>
                    <span id="eligibilityModeBadge" class="tech-status pending">LOADING</span>
                </div>
                <p class="tech-callout warning">These settings control automated matching and outreach only. Final donor fitness must be decided by a qualified medical officer after the required questionnaire, examination, and tests.</p>
                <div id="eligibilitySummary" class="tech-rule-summary"></div>
                <form id="eligibilityPolicyForm" class="tech-policy-form">
                    <label>Operating mode
                        <select id="eligibilityMode" name="enforcement_mode">
                            <option value="ADVISORY">Advisory — show issues, do not exclude</option>
                            <option value="ENFORCED">Enforced — exclude failed pre-screening</option>
                        </select>
                    </label>
                    <label>Minimum age
                        <input id="minimumAge" name="minimum_age_years" type="number" min="18" max="65" required>
                        <small>Must be 18 or higher.</small>
                    </label>
                    <label>Maximum age
                        <input id="maximumAge" name="maximum_age_years" type="number" min="18" max="65" required>
                        <small>Cannot exceed 65.</small>
                    </label>
                    <label>Minimum weight (kg)
                        <input id="minimumWeight" name="minimum_weight_kg" type="number" min="45" max="150" step="0.1" required>
                        <small>Must be 45 kg or higher.</small>
                    </label>
                    <label class="tech-policy-check"><input id="requireCompleteProfile" name="require_complete_profile" type="checkbox"> Block profiles missing age, weight, Hb, or BP screening when enforced</label>
                    <fieldset id="clinicalReviewFields" class="tech-review-fields">
                        <legend>Medical officer approval for enforcement</legend>
                        <label>Reviewer name<input id="reviewerName" name="reviewer_name" maxlength="200" autocomplete="name"></label>
                        <label>Review notes<textarea id="reviewNotes" name="review_notes" maxlength="2000" rows="4" placeholder="Record the policy review, local SOP, and approval context."></textarea></label>
                        <label class="tech-policy-check"><input id="clinicalReviewConfirmed" name="clinical_review_confirmed" type="checkbox"> I confirm that a qualified medical officer reviewed these enforced settings</label>
                    </fieldset>
                    <div class="tech-policy-footer">
                        <p id="eligibilityReviewMeta">No enforced clinical review is recorded.</p>
                        <button class="tech-button" type="submit">Save eligibility policy</button>
                    </div>
                </form>
                <div class="tech-fixed-rules">
                    <h3>Fixed safety behavior</h3>
                    <ul id="eligibilitySafeguards"></ul>
                    <p>Default baseline: <a id="eligibilitySource" href="#" target="_blank" rel="noopener noreferrer">National Standards for Blood Centres and Blood Transfusion Services</a>.</p>
                </div>
            </section>

            <section id="tech-data-quality" class="tech-panel glass-card" hidden>
                <div class="tech-panel-header">
                    <div><h2>Donor data quality</h2><p>Review incomplete, duplicate, invalid-contact, location, and stale records before enforcing stricter workflows.</p></div>
                    <a id="dataQualityExport" class="tech-button secondary" href="/api/admin/technical/data-quality/export"><i class="fa-solid fa-file-export"></i> Export queue</a>
                </div>
                <p class="tech-callout warning">Duplicate matches are suggestions only. This dashboard never merges, edits, or deletes donor records automatically.</p>
                <div id="dataQualitySummary" class="tech-rule-summary"></div>
                <form id="dataQualityFilters" class="tech-filters tech-quality-filters">
                    <input id="dataQualitySearch" type="search" maxlength="120" placeholder="Search donor, code, email, phone, or blood group">
                    <select id="dataQualityCategory"><option value="">All issue types</option><option value="ELIGIBILITY">Eligibility data</option><option value="CONTACT">Contact details</option><option value="DUPLICATE">Possible duplicates</option><option value="LOCATION">Location</option><option value="STALE">Stale profiles</option></select>
                    <select id="dataQualitySeverity"><option value="">All priorities</option><option value="HIGH">High priority</option><option value="REVIEW">Needs review</option><option value="INFO">Informational</option></select>
                    <select id="dataQualityStaleDays"><option value="180">Stale after 180 days</option><option value="365" selected>Stale after 1 year</option><option value="730">Stale after 2 years</option></select>
                    <button class="tech-button" type="submit">Apply</button>
                </form>
                <div class="tech-table-wrap"><table><thead><tr><th>Donor</th><th>Contact</th><th>Completeness</th><th>Priority</th><th>Issues</th><th>Last updated</th></tr></thead><tbody id="dataQualityRows"><tr><td colspan="6">Loading donor quality checks…</td></tr></tbody></table></div>
                <div class="tech-pagination"><span id="dataQualityCount">—</span><div><button id="dataQualityPrevious" class="tech-button secondary" type="button">Previous</button><button id="dataQualityNext" class="tech-button secondary" type="button">Next</button></div></div>
            </section>
        </section>`;
}

async function loadSummary() {
    const summary = await api("/api/admin/technical/summary");
    const values = [summary.audit_events_24h, summary.failed_events_24h, summary.active_sessions, `${summary.mfa_enabled_users}/${summary.active_users}`, summary.ready_backups, summary.eligibility_policy_mode || "ADVISORY"];
    document.querySelectorAll("#techSummary strong").forEach((element, index) => { element.textContent = values[index]; });
    const configuration = document.getElementById("backupConfiguration");
    const backupsConfigured = summary.backup_key_configured && summary.backup_storage_configured;
    configuration.textContent = backupsConfigured
        ? "Backup encryption is configured. Restore remains deliberately unavailable until a reviewed recovery workflow is added."
        : "Production backups are blocked until BACKUP_ENCRYPTION_KEY and persistent BACKUP_DIRECTORY storage are configured.";
    configuration.classList.toggle("warning", !backupsConfigured);
}

function toggleEligibilityReviewFields() {
    const enforced = document.getElementById("eligibilityMode")?.value === "ENFORCED";
    const fields = document.getElementById("clinicalReviewFields");
    if (!fields) return;
    fields.classList.toggle("required", enforced);
    document.getElementById("reviewerName").required = enforced;
    document.getElementById("reviewNotes").required = enforced;
    document.getElementById("clinicalReviewConfirmed").required = enforced;
}

async function loadEligibility() {
    const policy = await api("/api/admin/technical/eligibility-policy");
    document.getElementById("eligibilityMode").value = policy.enforcement_mode;
    document.getElementById("minimumAge").value = policy.minimum_age_years;
    document.getElementById("maximumAge").value = policy.maximum_age_years;
    document.getElementById("minimumWeight").value = Number(policy.minimum_weight_kg);
    document.getElementById("requireCompleteProfile").checked = Boolean(policy.require_complete_profile);
    document.getElementById("reviewerName").value = policy.reviewer_name || "";
    document.getElementById("reviewNotes").value = policy.review_notes || "";
    document.getElementById("clinicalReviewConfirmed").checked = false;
    const badge = document.getElementById("eligibilityModeBadge");
    badge.textContent = policy.enforcement_mode;
    badge.className = `tech-status ${policy.enforcement_mode === "ENFORCED" ? "success" : "pending"}`;
    const summary = policy.summary;
    document.getElementById("eligibilitySummary").innerHTML = `
        <article><span>Total donors</span><strong>${escapeHtml(summary.total_donors)}</strong></article>
        <article><span>Pass recorded checks</span><strong>${escapeHtml(summary.screening_passed)}</strong></article>
        <article><span>Need review</span><strong>${escapeHtml(summary.review_needed)}</strong></article>
        <article><span>Blocked from matching</span><strong>${escapeHtml(summary.matching_blocked)}</strong></article>`;
    document.getElementById("eligibilityReviewMeta").textContent = policy.reviewed_at
        ? `Version ${policy.version} · reviewed by ${policy.reviewer_name} on ${formatDate(policy.reviewed_at)}`
        : `Version ${policy.version} · no enforced clinical review is recorded`;
    document.getElementById("eligibilitySafeguards").innerHTML = policy.fixed_safeguards.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    document.getElementById("eligibilitySource").href = policy.source_reference;
    toggleEligibilityReviewFields();
}

function dataQualityParameters(includePage = true) {
    const parameters = new URLSearchParams({
        stale_after_days: document.getElementById("dataQualityStaleDays")?.value || "365",
    });
    if (includePage) {
        parameters.set("page", state.dataQualityPage);
        parameters.set("page_size", state.dataQualityPageSize);
    }
    const search = document.getElementById("dataQualitySearch")?.value.trim();
    const category = document.getElementById("dataQualityCategory")?.value;
    const severity = document.getElementById("dataQualitySeverity")?.value;
    if (search) parameters.set("search", search);
    if (category) parameters.set("category", category);
    if (severity) parameters.set("severity", severity);
    return parameters;
}

async function loadDataQuality() {
    const parameters = dataQualityParameters();
    const data = await api(`/api/admin/technical/data-quality?${parameters}`);
    const summary = data.summary;
    document.getElementById("dataQualitySummary").innerHTML = `
        <article><span>Donors with issues</span><strong>${escapeHtml(summary.donors_with_issues)}</strong></article>
        <article><span>High priority</span><strong>${escapeHtml(summary.high_priority)}</strong></article>
        <article><span>Incomplete eligibility</span><strong>${escapeHtml(summary.incomplete_eligibility)}</strong></article>
        <article><span>Possible duplicates</span><strong>${escapeHtml(summary.possible_duplicates)}</strong></article>`;
    const rows = document.getElementById("dataQualityRows");
    rows.innerHTML = data.items.length ? data.items.map((item) => {
        const severityClass = item.highest_severity === "HIGH" ? "failed" : item.highest_severity === "REVIEW" ? "pending" : item.highest_severity === "COMPLETE" ? "success" : "";
        const issues = item.issues.length
            ? item.issues.map((issue) => `<small><strong>${escapeHtml(issue.code.replaceAll("_", " "))}</strong> · ${escapeHtml(issue.message)}</small>`).join("")
            : "<small>No tracked issues.</small>";
        return `<tr>
            <td><strong>${escapeHtml(item.full_name)}</strong><small>${escapeHtml(item.donor_code)} · ${escapeHtml(item.blood_group)} · ${escapeHtml(item.status)}</small></td>
            <td>${escapeHtml(item.email || "—")}<small>${escapeHtml(item.phone || "—")}</small></td>
            <td><div class="tech-quality-score"><span style="width:${Math.max(0, Math.min(100, Number(item.completeness_percent)))}%"></span></div><small>${escapeHtml(item.completeness_percent)}%</small></td>
            <td><span class="tech-status ${severityClass}">${escapeHtml(item.highest_severity)}</span></td>
            <td class="tech-quality-issues">${issues}</td>
            <td>${escapeHtml(formatDate(item.updated_at))}</td>
        </tr>`;
    }).join("") : '<tr><td colspan="6">No donor records match these filters.</td></tr>';
    document.getElementById("dataQualityCount").textContent = `${data.total} donor(s) · page ${data.page}`;
    document.getElementById("dataQualityPrevious").disabled = state.dataQualityPage <= 1;
    document.getElementById("dataQualityNext").disabled = state.dataQualityPage * state.dataQualityPageSize >= data.total;
    document.getElementById("dataQualityExport").href = `/api/admin/technical/data-quality/export?${dataQualityParameters(false)}`;
}

async function loadAudits() {
    const parameters = new URLSearchParams({ page: state.auditPage, page_size: state.auditPageSize });
    const search = document.getElementById("auditSearch")?.value.trim();
    const category = document.getElementById("auditCategory")?.value;
    const result = document.getElementById("auditResult")?.value;
    if (search) parameters.set("search", search);
    if (category) parameters.set("category", category);
    if (result) parameters.set("result", result);
    const data = await api(`/api/admin/technical/audit-logs?${parameters}`);
    const rows = document.getElementById("auditRows");
    rows.innerHTML = data.items.length ? data.items.map((item) => `
        <tr><td>${escapeHtml(formatDate(item.created_at))}</td><td>${escapeHtml(item.actor_username)}</td><td><span class="tech-badge">${escapeHtml(item.category)}</span></td><td><strong>${escapeHtml(item.action)}</strong><small>${escapeHtml(item.request_method || "")} ${escapeHtml(item.request_path || "")}</small></td><td><span class="tech-status ${item.result.toLowerCase()}">${escapeHtml(item.result)}</span></td><td>${escapeHtml(item.ip_address || "—")}</td><td><span class="tech-integrity ${item.integrity_valid ? "valid" : "invalid"}">${item.integrity_valid ? "Verified" : "Mismatch"}</span></td></tr>`).join("") : '<tr><td colspan="7">No audit events match these filters.</td></tr>';
    document.getElementById("auditCount").textContent = `${data.total} events · page ${data.page}`;
    document.getElementById("auditPrevious").disabled = state.auditPage <= 1;
    document.getElementById("auditNext").disabled = state.auditPage * state.auditPageSize >= data.total;
}

async function loadBackups() {
    const records = await api("/api/admin/technical/backups");
    const rows = document.getElementById("backupRows");
    rows.innerHTML = records.length ? records.map((record) => `
        <tr><td>${escapeHtml(formatDate(record.created_at))}</td><td>${escapeHtml(record.created_by)}</td><td>${escapeHtml(record.table_count ?? "—")} tables · ${escapeHtml(record.row_count ?? "—")} rows</td><td>${escapeHtml(formatBytes(record.size_bytes))}</td><td><span class="tech-status ${record.status.toLowerCase()}">${escapeHtml(record.status)}</span></td><td class="tech-actions">${record.status === "READY" ? `<a class="tech-icon-button" title="Download" href="/api/admin/technical/backups/${encodeURIComponent(record.id)}/download"><i class="fa-solid fa-download"></i></a><button class="tech-icon-button" type="button" data-backup-verify="${escapeHtml(record.id)}" title="Verify"><i class="fa-solid fa-shield-check"></i></button><button class="tech-icon-button danger" type="button" data-backup-delete="${escapeHtml(record.id)}" title="Delete"><i class="fa-solid fa-trash"></i></button>` : escapeHtml(record.error_message || "—")}</td></tr>`).join("") : '<tr><td colspan="6">No backups have been created.</td></tr>';
}

async function loadMfa() {
    const [status, users] = await Promise.all([api("/api/security/mfa/status"), api("/api/admin/technical/mfa/users")]);
    document.getElementById("myMfaStatus").textContent = status.enabled
        ? `Enabled · ${status.recovery_codes_remaining} recovery codes remaining`
        : status.setup_pending ? "Enrollment started but not confirmed" : "Not enabled";
    document.getElementById("myMfaActions").innerHTML = status.enabled
        ? '<button id="regenerateRecovery" class="tech-button secondary" type="button">New recovery codes</button> <button id="disableMfa" class="tech-button danger" type="button">Disable MFA</button>'
        : '<button id="startMfa" class="tech-button" type="button">Set up authenticator</button>';
    const currentUsername = localStorage.getItem("username");
    document.getElementById("mfaRows").innerHTML = users.map((user) => `
        <tr><td><strong>${escapeHtml(user.full_name)}</strong><small>${escapeHtml(user.username)}</small></td><td>${escapeHtml(user.role)}</td><td><span class="tech-status ${user.mfa_enabled ? "success" : "pending"}">${user.mfa_enabled ? "ENABLED" : "NOT ENABLED"}</span></td><td>${user.mfa_enabled ? escapeHtml(user.recovery_codes_remaining) : "—"}</td><td>${user.mfa_enabled && user.username !== currentUsername ? `<button class="tech-button danger small" type="button" data-mfa-reset="${user.id}" data-username="${escapeHtml(user.username)}">Reset</button>` : "—"}</td></tr>`).join("");
}

async function loadSessions() {
    const sessions = await api("/api/admin/technical/sessions");
    document.getElementById("sessionRows").innerHTML = sessions.length ? sessions.map((session) => `
        <tr><td><strong>${escapeHtml(session.display_name || session.username)}</strong><small>${escapeHtml(session.username)}${session.current ? " · This session" : ""}</small></td><td>${escapeHtml(session.device)}</td><td>${escapeHtml(session.ip_address || "—")}</td><td>${escapeHtml(formatDate(session.last_seen_at))}</td><td>${escapeHtml(formatDate(session.expires_at))}</td><td>${session.mfa_verified ? "Verified" : "No"}</td><td><button class="tech-button danger small" type="button" data-session-revoke="${escapeHtml(session.id)}" data-current="${session.current}">Revoke</button></td></tr>`).join("") : '<tr><td colspan="7">No active tracked sessions.</td></tr>';
}

async function refreshAll() {
    await Promise.all([loadSummary(), loadAudits(), loadBackups(), loadMfa(), loadSessions(), loadEligibility(), loadDataQuality()]);
    if (window.lucide) window.lucide.createIcons();
}

function showEnrollment(data) {
    const panel = document.getElementById("mfaEnrollment");
    panel.hidden = false;
    panel.innerHTML = `<div><h3>Scan this code</h3><p>Use any TOTP authenticator, then enter the six-digit code to finish.</p><code>${escapeHtml(data.secret)}</code></div><img src="${data.qr_data_uri}" alt="Authenticator enrollment QR code"><form id="confirmMfaForm"><label>Verification code<input name="code" inputmode="numeric" autocomplete="one-time-code" minlength="6" maxlength="6" required></label><button class="tech-button" type="submit">Confirm and enable</button></form>`;
}

function showRecoveryCodes(codes) {
    const panel = document.getElementById("mfaEnrollment");
    panel.hidden = false;
    panel.innerHTML = `<div><h3>Save your recovery codes now</h3><p>Each code works once. They will not be shown again.</p><div class="tech-recovery-codes">${codes.map((code) => `<code>${escapeHtml(code)}</code>`).join("")}</div><button id="downloadRecoveryCodes" class="tech-button secondary" type="button">Download codes</button></div>`;
    document.getElementById("downloadRecoveryCodes").addEventListener("click", () => {
        const blob = new Blob([`BloodLink MFA recovery codes\n\n${codes.join("\n")}\n`], { type: "text/plain" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "bloodlink-recovery-codes.txt";
        link.click();
        URL.revokeObjectURL(link.href);
    });
}

export function initializeTechnicalPortal() {
    document.querySelectorAll("[data-tech-tab]").forEach((button) => button.addEventListener("click", () => {
        document.querySelectorAll("[data-tech-tab]").forEach((item) => item.classList.toggle("active", item === button));
        document.querySelectorAll(".tech-panel").forEach((panel) => { panel.hidden = panel.id !== `tech-${button.dataset.techTab}`; });
    }));
    document.getElementById("refreshTechnicalPortal").addEventListener("click", () => refreshAll().then(() => showNotice("Technical portal refreshed.")).catch((error) => showNotice(error.message, "error")));
    document.getElementById("auditFilters").addEventListener("submit", (event) => { event.preventDefault(); state.auditPage = 1; loadAudits().catch((error) => showNotice(error.message, "error")); });
    document.getElementById("auditPrevious").addEventListener("click", () => { state.auditPage -= 1; loadAudits(); });
    document.getElementById("auditNext").addEventListener("click", () => { state.auditPage += 1; loadAudits(); });
    document.getElementById("dataQualityFilters").addEventListener("submit", (event) => { event.preventDefault(); state.dataQualityPage = 1; loadDataQuality().catch((error) => showNotice(error.message, "error")); });
    document.getElementById("dataQualityPrevious").addEventListener("click", () => { state.dataQualityPage -= 1; loadDataQuality().catch((error) => showNotice(error.message, "error")); });
    document.getElementById("dataQualityNext").addEventListener("click", () => { state.dataQualityPage += 1; loadDataQuality().catch((error) => showNotice(error.message, "error")); });
    document.getElementById("eligibilityMode").addEventListener("change", toggleEligibilityReviewFields);
    document.getElementById("eligibilityPolicyForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        const submit = event.submitter;
        if (submit) submit.disabled = true;
        try {
            const mode = document.getElementById("eligibilityMode").value;
            const result = await api("/api/admin/technical/eligibility-policy", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    enforcement_mode: mode,
                    minimum_age_years: Number(document.getElementById("minimumAge").value),
                    maximum_age_years: Number(document.getElementById("maximumAge").value),
                    minimum_weight_kg: document.getElementById("minimumWeight").value,
                    require_complete_profile: document.getElementById("requireCompleteProfile").checked,
                    reviewer_name: document.getElementById("reviewerName").value,
                    review_notes: document.getElementById("reviewNotes").value,
                    clinical_review_confirmed: mode === "ENFORCED" && document.getElementById("clinicalReviewConfirmed").checked,
                }),
            });
            await Promise.all([loadEligibility(), loadSummary(), loadAudits()]);
            showNotice(`Eligibility policy version ${result.version} saved in ${result.enforcement_mode.toLowerCase()} mode.`);
        } catch (error) { showNotice(error.message, "error"); }
        finally { if (submit) submit.disabled = false; }
    });
    document.getElementById("createBackup").addEventListener("click", async (event) => {
        const button = event.currentTarget; button.disabled = true; button.textContent = "Creating…";
        try { await api("/api/admin/technical/backups", { method: "POST" }); await Promise.all([loadBackups(), loadSummary(), loadAudits()]); showNotice("Encrypted backup created and checksummed."); }
        catch (error) { showNotice(error.message, "error"); }
        finally { button.disabled = false; button.innerHTML = '<i class="fa-solid fa-database"></i> Create backup'; }
    });
    document.getElementById("revokeOtherSessions").addEventListener("click", async () => {
        if (!window.confirm("Revoke every other active session for your account?")) return;
        try { const result = await api("/api/security/sessions/revoke-others", { method: "POST" }); await loadSessions(); showNotice(`${result.revoked_count} other session(s) revoked.`); }
        catch (error) { showNotice(error.message, "error"); }
    });

    document.querySelector(".tech-page").addEventListener("submit", async (event) => {
        if (event.target.id !== "confirmMfaForm") return;
        event.preventDefault();
        try { const result = await api("/api/security/mfa/confirm", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code: event.target.elements.code.value }) }); showRecoveryCodes(result.recovery_codes); await Promise.all([loadMfa(), loadSummary(), loadSessions()]); showNotice("MFA is now enabled."); }
        catch (error) { showNotice(error.message, "error"); }
    });

    document.querySelector(".tech-page").addEventListener("click", async (event) => {
        const target = event.target.closest("button, a");
        if (!target) return;
        try {
            if (target.id === "startMfa") {
                const password = window.prompt("Enter your current password to begin MFA setup:");
                if (!password) return;
                showEnrollment(await api("/api/security/mfa/setup", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ current_password: password }) }));
            } else if (target.id === "disableMfa") {
                const password = window.prompt("Enter your current password:"); if (!password) return;
                const code = window.prompt("Enter an authenticator or recovery code:"); if (!code) return;
                if (!window.confirm("Disable MFA for your account?")) return;
                await api("/api/security/mfa/disable", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ current_password: password, code }) });
                await Promise.all([loadMfa(), loadSummary(), loadSessions()]); showNotice("MFA disabled.");
            } else if (target.id === "regenerateRecovery") {
                const password = window.prompt("Enter your current password:"); if (!password) return;
                const code = window.prompt("Enter a fresh authenticator code:"); if (!code) return;
                const result = await api("/api/security/mfa/recovery-codes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ current_password: password, code }) });
                showRecoveryCodes(result.recovery_codes); await loadMfa(); showNotice("New recovery codes created. Previous codes no longer work.");
            } else if (target.dataset.sessionRevoke) {
                if (!window.confirm("Revoke this session immediately?")) return;
                const result = await api(`/api/admin/technical/sessions/${encodeURIComponent(target.dataset.sessionRevoke)}`, { method: "DELETE" });
                if (result.current_session) { logoutUser(); return; }
                await Promise.all([loadSessions(), loadSummary(), loadAudits()]); showNotice("Session revoked.");
            } else if (target.dataset.backupVerify) {
                const result = await api(`/api/admin/technical/backups/${encodeURIComponent(target.dataset.backupVerify)}/verify`, { method: "POST" });
                await loadAudits(); showNotice(`Backup verified: ${result.table_count} tables and ${result.row_count} rows.`);
            } else if (target.dataset.backupDelete) {
                if (!window.confirm("Permanently delete this backup file? Its audit record will be retained.")) return;
                await api(`/api/admin/technical/backups/${encodeURIComponent(target.dataset.backupDelete)}`, { method: "DELETE" });
                await Promise.all([loadBackups(), loadSummary(), loadAudits()]); showNotice("Backup file deleted; its history was retained.");
            } else if (target.dataset.mfaReset) {
                if (!window.confirm(`Reset MFA for ${target.dataset.username} and revoke all their sessions?`)) return;
                const password = window.prompt("Enter your administrator password:"); if (!password) return;
                const reason = window.prompt("Enter the support or security reason for this reset:"); if (!reason) return;
                await api(`/api/admin/technical/mfa/users/${target.dataset.mfaReset}/reset`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ current_password: password, reason }) });
                await Promise.all([loadMfa(), loadSummary(), loadSessions(), loadAudits()]); showNotice("MFA reset and sessions revoked.");
            }
        } catch (error) { showNotice(error.message, "error"); }
    });

    refreshAll().catch((error) => showNotice(error.message, "error"));
}
