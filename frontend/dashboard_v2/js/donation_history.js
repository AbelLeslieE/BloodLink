/* BloodLink donation-history workspace. */

import { authenticatedFetch } from "./api.js";

const donationHistoryState = { records: [], summary: null, filters: { blood_groups: [], districts: [] } };

export function loadDonationHistory() {
    return `
    <section class="donation-history-page">
        <section class="dh-hero glass-card"><div class="dh-hero-left"><div class="dh-hero-icon"><i class="fa-solid fa-calendar-days"></i></div><div class="dh-hero-text"><h1>Donation History</h1><p>View confirmed donation records from the BloodLink database.</p></div></div></section>
        <section class="dh-kpi-grid">
            <div class="dh-kpi-card glass-card"><div class="dh-kpi-icon blue"><i class="fa-solid fa-droplet"></i></div><div class="dh-kpi-content"><span>Total Donations</span><h2 id="kpiTotalDonations">0</h2><small>Matching records</small></div></div>
            <div class="dh-kpi-card glass-card"><div class="dh-kpi-icon green"><i class="fa-solid fa-users"></i></div><div class="dh-kpi-content"><span>Total Donors</span><h2 id="kpiTotalDonors">0</h2><small>Unique donors</small></div></div>
            <div class="dh-kpi-card glass-card"><div class="dh-kpi-icon purple"><i class="fa-solid fa-award"></i></div><div class="dh-kpi-content"><span>Points Awarded</span><h2 id="kpiTotalPoints">0</h2><small>Confirmed donations</small></div></div>
            <div class="dh-kpi-card glass-card"><div class="dh-kpi-icon orange"><i class="fa-solid fa-hospital"></i></div><div class="dh-kpi-content"><span>Hospitals</span><h2 id="kpiHospitals">0</h2><small>Recorded locations</small></div></div>
        </section>
        <section class="dh-filter-bar glass-card">
            <div class="dh-search"><i class="fa-solid fa-magnifying-glass"></i><input id="dhSearch" type="search" placeholder="Search donor name, phone, donor code, or record ID..."></div>
            <select id="dhBloodGroup"><option value="">All Blood Groups</option></select>
            <input type="date" id="dhDate" aria-label="Donation date">
            <select id="dhDistrict"><option value="">All Districts</option></select>
            <button id="btnFilter" class="btn-primary"><i class="fa-solid fa-filter"></i>Filter</button><button id="btnReset" class="btn-secondary">Reset</button>
        </section>
        <section class="dh-layout">
            <div class="dh-content-stack">
                <div class="dh-main"><div class="glass-card"><div class="section-title"><h2>Donation Records</h2></div><div class="dh-table-wrapper"><table class="dh-table"><thead><tr><th>Donation ID</th><th>Donor Name</th><th>Blood Group</th><th>Donation Date</th><th>Points</th><th>Hospital</th><th>Status</th></tr></thead><tbody id="donationHistoryTable"></tbody></table></div><div class="dh-pagination"><div id="dhRecordCount" class="dh-record-count">Showing 0 records</div></div></div></div>
                <section class="dh-bottom-panels" aria-label="Donation history actions">
                    <div class="glass-card"><div class="sidebar-title"><h3>Recent Donors</h3></div><div id="recentDonors"></div></div>
                    <div class="glass-card export-card"><h3><i class="fa-solid fa-download"></i>Export Records</h3><p>Download the donation records that match the active filters.</p><div class="export-buttons"><button id="exportExcel" class="btn-success"><i class="fa-solid fa-file-excel"></i>Export Excel</button><button id="exportPdf" class="btn-danger"><i class="fa-solid fa-file-pdf"></i>Export PDF</button></div></div>
                </section>
            </div>
            <aside class="dh-sidebar">
                <div class="glass-card"><div class="sidebar-title"><h3>Donation Summary</h3><select id="dhSummaryPeriod" aria-label="Donation history period"><option value="">All records</option><option value="current_year">This year</option></select></div><div id="donationSummary"></div></div>
            </aside>
        </section>
    </section>`;
}

export function initializeDonationHistory() {
    document.getElementById("btnFilter")?.addEventListener("click", loadDonationHistoryData);
    document.getElementById("btnReset")?.addEventListener("click", resetFilters);
    document.getElementById("dhSearch")?.addEventListener("keydown", (event) => { if (event.key === "Enter") loadDonationHistoryData(); });
    document.getElementById("dhSummaryPeriod")?.addEventListener("change", loadDonationHistoryData);
    document.getElementById("exportExcel")?.addEventListener("click", () => exportRecords("excel"));
    document.getElementById("exportPdf")?.addEventListener("click", () => exportRecords("pdf"));
    loadDonationHistoryData();
}

function activeFilters() {
    const value = (id) => document.getElementById(id)?.value.trim() || "";
    return { search: value("dhSearch"), blood_group: value("dhBloodGroup"), donation_date: value("dhDate"), district: value("dhDistrict"), period: value("dhSummaryPeriod") };
}

function queryString(filters = activeFilters()) {
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => { if (value) query.set(key, value); });
    return query.toString();
}

async function loadDonationHistoryData() {
    const response = await authenticatedFetch(`/api/donation-history?${queryString()}`);
    if (!response) return;
    if (!response.ok) return renderError("Unable to load donation history.");
    const data = await response.json();
    donationHistoryState.records = data.records || [];
    donationHistoryState.summary = data.summary || {};
    donationHistoryState.filters = data.filters || donationHistoryState.filters;
    populateFilterOptions();
    renderKPIs();
    renderDonationTable();
    renderDonationSummary();
    renderRecentDonors(data.recent_donors || []);
}

function populateFilterOptions() {
    populateSelect("dhBloodGroup", donationHistoryState.filters.blood_groups, "All Blood Groups");
    populateSelect("dhDistrict", donationHistoryState.filters.districts, "All Districts");
}

function populateSelect(id, options, placeholder) {
    const select = document.getElementById(id);
    if (!select) return;
    const selected = select.value;
    select.innerHTML = `<option value="">${placeholder}</option>${options.map((option) => `<option value="${escapeHtml(option)}">${escapeHtml(option)}</option>`).join("")}`;
    select.value = selected;
}

function renderKPIs() {
    const summary = donationHistoryState.summary || {};
    setText("kpiTotalDonations", number(summary.total_donations));
    setText("kpiTotalDonors", number(summary.total_donors));
    setText("kpiTotalPoints", number(summary.total_points));
    setText("kpiHospitals", number(summary.hospitals));
}

function renderDonationTable() {
    const table = document.getElementById("donationHistoryTable");
    const count = document.getElementById("dhRecordCount");
    if (!table || !count) return;
    count.textContent = `Showing ${donationHistoryState.records.length} record${donationHistoryState.records.length === 1 ? "" : "s"}`;
    if (!donationHistoryState.records.length) {
        table.innerHTML = `<tr><td colspan="7" class="dh-empty-row">No donation records match these filters.</td></tr>`;
        return;
    }
    table.innerHTML = donationHistoryState.records.map((donation) => `<tr><td>${escapeHtml(donation.reference)}</td><td>${escapeHtml(donation.donor_name)}</td><td><span class="blood-badge ${bloodGroupClass(donation.blood_group)}">${escapeHtml(donation.blood_group)}</span></td><td>${formatDate(donation.donation_date)}</td><td>${number(donation.points_awarded)}</td><td>${escapeHtml(donation.hospital_name)}</td><td><span class="donation-type voluntary">${escapeHtml(donation.status)}</span></td></tr>`).join("");
}

function renderDonationSummary() {
    const summary = donationHistoryState.summary || {};
    const container = document.getElementById("donationSummary");
    if (!container) return;
    container.innerHTML = `<div class="summary-row"><span>Total Donations</span><strong>${number(summary.total_donations)}</strong></div><div class="summary-row"><span>Total Donors</span><strong>${number(summary.total_donors)}</strong></div><div class="summary-row"><span>Points Awarded</span><strong>${number(summary.total_points)}</strong></div><div class="summary-row"><span>Average Points</span><strong>${number(summary.average_points)}</strong></div><div class="summary-row"><span>Confirmed</span><strong>${number(summary.confirmed)}</strong></div><div class="summary-row"><span>Hospitals</span><strong>${number(summary.hospitals)}</strong></div>`;
}

function renderRecentDonors(donors) {
    const container = document.getElementById("recentDonors");
    if (!container) return;
    if (!donors.length) {
        container.innerHTML = `<p class="dh-empty-state">No recent donations found.</p>`;
        return;
    }
    container.innerHTML = donors.map((donor) => `<div class="recent-donor"><div class="recent-avatar">${escapeHtml(donor.donor_name.charAt(0).toUpperCase())}</div><div class="recent-info"><strong>${escapeHtml(donor.donor_name)}</strong><small>${formatDate(donor.donation_date)}</small></div><span class="blood-badge ${bloodGroupClass(donor.blood_group)}">${escapeHtml(donor.blood_group)}</span></div>`).join("");
}

function resetFilters() {
    ["dhSearch", "dhBloodGroup", "dhDate", "dhDistrict", "dhSummaryPeriod"].forEach((id) => { const input = document.getElementById(id); if (input) input.value = ""; });
    loadDonationHistoryData();
}

async function exportRecords(format) {
    const button = document.getElementById(format === "excel" ? "exportExcel" : "exportPdf");
    if (button) button.disabled = true;
    try {
        const response = await authenticatedFetch(`/api/donation-history/export/${format}?${queryString()}`);
        if (!response || !response.ok) throw new Error("Export failed");
        const url = URL.createObjectURL(await response.blob());
        const link = Object.assign(document.createElement("a"), { href: url, download: `bloodlink-donation-history.${format === "excel" ? "xlsx" : "pdf"}` });
        document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
    } catch (error) {
        console.error(error);
        window.alert("Unable to export donation history. Please try again.");
    } finally {
        if (button) button.disabled = false;
    }
}

function renderError(message) {
    const table = document.getElementById("donationHistoryTable");
    if (table) table.innerHTML = `<tr><td colspan="7" class="dh-empty-row">${escapeHtml(message)}</td></tr>`;
}

function setText(id, value) { const element = document.getElementById(id); if (element) element.textContent = value; }
function number(value) { return Number(value || 0).toLocaleString(); }
function formatDate(value) { return value ? new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`)) : "Not recorded"; }
function bloodGroupClass(value) { return String(value || "").replace("+", "plus").replace("-", "minus"); }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[character])); }
