/* ============================================================
   BloodLink - Donation History Module
   File: donation_history.js
   Description:
   Renders the Donation History workspace.
============================================================ */

export function loadDonationHistory() {
    return `
    <section class="donation-history-page">

        <!-- ========================================================= -->
        <!-- Hero -->
        <!-- ========================================================= -->
        <section class="dh-hero glass-card">

            <div class="dh-hero-left">

                <div class="dh-hero-icon">
                    <i class="fa-solid fa-calendar-days"></i>
                </div>

                <div class="dh-hero-text">
                    <h1>Donation History</h1>
                    <p>View and manage all blood donation records.</p>
                </div>

            </div>

        </section>

        <!-- ========================================================= -->
        <!-- KPI Cards -->
        <!-- ========================================================= -->
        <section class="dh-kpi-grid">

            <div class="dh-kpi-card glass-card">

                <div class="dh-kpi-icon blue">
                    <i class="fa-solid fa-droplet"></i>
                </div>

                <div class="dh-kpi-content">
                    <span>Total Donations</span>
                    <h2 id="kpiTotalDonations">0</h2>
                    <small class="positive">
                        <i class="fa-solid fa-arrow-up"></i>
                        12% from last year
                    </small>
                </div>

            </div>

            <div class="dh-kpi-card glass-card">

                <div class="dh-kpi-icon green">
                    <i class="fa-solid fa-users"></i>
                </div>

                <div class="dh-kpi-content">
                    <span>Total Donors</span>
                    <h2 id="kpiTotalDonors">0</h2>
                    <small class="positive">
                        <i class="fa-solid fa-arrow-up"></i>
                        8% from last year
                    </small>
                </div>

            </div>

            <div class="dh-kpi-card glass-card">

                <div class="dh-kpi-icon purple">
                    <i class="fa-solid fa-syringe"></i>
                </div>

                <div class="dh-kpi-content">
                    <span>Units Collected</span>
                    <h2 id="kpiUnitsCollected">0</h2>
                    <small class="positive">
                        <i class="fa-solid fa-arrow-up"></i>
                        15% from last year
                    </small>
                </div>

            </div>

            <div class="dh-kpi-card glass-card">

                <div class="dh-kpi-icon orange">
                    <i class="fa-solid fa-calendar"></i>
                </div>

                <div class="dh-kpi-content">
                    <span>This Month</span>
                    <h2 id="kpiThisMonth">0</h2>
                    <small class="positive">
                        <i class="fa-solid fa-arrow-up"></i>
                        10% from last month
                    </small>
                </div>

            </div>

        </section>

        <!-- ========================================================= -->
        <!-- Filter Bar -->
        <!-- ========================================================= -->
        <section class="dh-filter-bar glass-card">

            <div class="dh-search">

                <i class="fa-solid fa-magnifying-glass"></i>

                <input
                    id="dhSearch"
                    type="text"
                    placeholder="Search by donor name, phone, or ID..."
                >

            </div>

            <select id="dhBloodGroup">
                <option>All Blood Groups</option>
            </select>

            <input
                type="date"
                id="dhDate"
            >

            <select id="dhDistrict">
                <option>All Districts</option>
            </select>

            <button id="btnFilter" class="btn-primary">
                <i class="fa-solid fa-filter"></i>
                Filter
            </button>

            <button id="btnReset" class="btn-secondary">
                Reset
            </button>

        </section>

        <!-- ========================================================= -->
        <!-- Main Layout -->
        <!-- ========================================================= -->
        <section class="dh-layout">

            <!-- ========================================= -->
            <!-- Left -->
            <!-- ========================================= -->

            <div class="dh-main">

                <div class="glass-card">

                    <div class="section-title">
                        <h2>Donation Records</h2>
                    </div>

                    <div class="dh-table-wrapper">

                        <table class="dh-table">

                            <thead>

                                <tr>

                                    <th>Donation ID</th>
                                    <th>Donor Name</th>
                                    <th>Blood Group</th>
                                    <th>Donation Date</th>
                                    <th>Units</th>
                                    <th>Location</th>
                                    <th>Donation Type</th>
                                    <th>Action</th>

                                </tr>

                            </thead>

                            <tbody id="donationHistoryTable">

                            </tbody>

                        </table>

                    </div>

                    <div class="dh-pagination">

                        <div class="dh-record-count">
                            Showing 0 records
                        </div>

                        <div id="dhPagination">

                        </div>

                    </div>

                </div>

            </div>

            <!-- ========================================= -->
            <!-- Right Sidebar -->
            <!-- ========================================= -->

            <aside class="dh-sidebar">

                <div class="glass-card">

                    <div class="sidebar-title">

                        <h3>Donation Summary</h3>

                        <select>
                            <option>This Year</option>
                        </select>

                    </div>

                    <div id="donationSummary">

                    </div>

                </div>

                <div class="glass-card">

                    <div class="sidebar-title">

                        <h3>Recent Donors</h3>

                        <button class="link-btn">
                            View All
                        </button>

                    </div>

                    <div id="recentDonors">

                    </div>

                </div>

                <div class="glass-card export-card">

                    <h3>

                        <i class="fa-solid fa-download"></i>

                        Export Records

                    </h3>

                    <p>
                        Download donation history in Excel or PDF format.
                    </p>

                    <div class="export-buttons">

                        <button class="btn-success">

                            <i class="fa-solid fa-file-excel"></i>

                            Export Excel

                        </button>

                        <button class="btn-danger">

                            <i class="fa-solid fa-file-pdf"></i>

                            Export PDF

                        </button>

                    </div>

                </div>

            </aside>

        </section>

    </section>
    `;
}
/* ============================================================
   Donation History State
============================================================ */

const donationHistoryState = {

    donations: [

        {
            id: "DON-2026-1256",
            donor: "Rahul Sharma",
            bloodGroup: "AB+",
            date: "17 Jul 2026",
            units: "1 Unit",
            location: "City Hospital",
            type: "Voluntary"
        },

        {
            id: "DON-2026-1255",
            donor: "Anjali Nair",
            bloodGroup: "O-",
            date: "16 Jul 2026",
            units: "1 Unit",
            location: "Medical College",
            type: "Voluntary"
        },

        {
            id: "DON-2026-1254",
            donor: "John Mathew",
            bloodGroup: "B+",
            date: "15 Jul 2026",
            units: "1 Unit",
            location: "General Hospital",
            type: "Voluntary"
        },

        {
            id: "DON-2026-1253",
            donor: "Priya Menon",
            bloodGroup: "A+",
            date: "14 Jul 2026",
            units: "1 Unit",
            location: "Sunrise Hospital",
            type: "Voluntary"
        },

        {
            id: "DON-2026-1252",
            donor: "Vishnu Das",
            bloodGroup: "O+",
            date: "12 Jul 2026",
            units: "1 Unit",
            location: "City Hospital",
            type: "Replacement"
        },

        {
            id: "DON-2026-1251",
            donor: "Arun Kumar",
            bloodGroup: "A-",
            date: "10 Jul 2026",
            units: "1 Unit",
            location: "Medical College",
            type: "Replacement"
        },

        {
            id: "DON-2026-1250",
            donor: "Neha Roy",
            bloodGroup: "B-",
            date: "09 Jul 2026",
            units: "1 Unit",
            location: "General Hospital",
            type: "Voluntary"
        }

    ],

    summary: {

        totalDonations: 2356,
        totalDonors: 1245,
        unitsCollected: 3842,
        average: "1.63 Units",
        voluntary: "1,856 (78.8%)",
        replacement: "500 (21.2%)"

    },

    recentDonors: [

        {
            name: "Rahul Sharma",
            group: "AB+",
            date: "17 Jul 2026"
        },

        {
            name: "Anjali Nair",
            group: "O-",
            date: "16 Jul 2026"
        },

        {
            name: "John Mathew",
            group: "B+",
            date: "15 Jul 2026"
        },

        {
            name: "Priya Menon",
            group: "A+",
            date: "14 Jul 2026"
        }

    ]

};


/* ============================================================
   Initialize Module
============================================================ */

export function initializeDonationHistory() {

    renderKPIs();

    renderDonationTable();

    renderDonationSummary();

    renderRecentDonors();

}


/* ============================================================
   KPI Rendering
============================================================ */

function renderKPIs() {

    document.getElementById("kpiTotalDonations").textContent = donationHistoryState.summary.totalDonations.toLocaleString();

    document.getElementById("kpiTotalDonors").textContent = donationHistoryState.summary.totalDonors.toLocaleString();

    document.getElementById("kpiUnitsCollected").textContent = donationHistoryState.summary.unitsCollected.toLocaleString();

    document.getElementById("kpiThisMonth").textContent = "156";

}


/* ============================================================
   Donation Table
============================================================ */

function renderDonationTable() {

    const tbody = document.getElementById("donationHistoryTable");

    if (!tbody) return;

    tbody.innerHTML = donationHistoryState.donations.map(donation => `

        <tr>

            <td>${donation.id}</td>

            <td>${donation.donor}</td>

            <td>

                <span class="blood-badge ${donation.bloodGroup.replace("+","plus").replace("-","minus")}">

                    ${donation.bloodGroup}

                </span>

            </td>

            <td>${donation.date}</td>

            <td>${donation.units}</td>

            <td>${donation.location}</td>

            <td>

                <span class="donation-type ${donation.type.toLowerCase()}">

                    ${donation.type}

                </span>

            </td>

            <td>

                <button class="table-view-btn">

                    <i class="fa-solid fa-eye"></i>

                </button>

            </td>

        </tr>

    `).join("");

}
/* ============================================================
   Donation Summary
============================================================ */

function renderDonationSummary() {

    const container = document.getElementById("donationSummary");

    if (!container) return;

    container.innerHTML = `

        <div class="summary-row">

            <span>Total Donations</span>

            <strong>${donationHistoryState.summary.totalDonations.toLocaleString()}</strong>

        </div>

        <div class="summary-row">

            <span>Total Donors</span>

            <strong>${donationHistoryState.summary.totalDonors.toLocaleString()}</strong>

        </div>

        <div class="summary-row">

            <span>Units Collected</span>

            <strong>${donationHistoryState.summary.unitsCollected.toLocaleString()}</strong>

        </div>

        <div class="summary-row">

            <span>Average per Donation</span>

            <strong>${donationHistoryState.summary.average}</strong>

        </div>

        <div class="summary-row">

            <span>Voluntary Donations</span>

            <strong>${donationHistoryState.summary.voluntary}</strong>

        </div>

        <div class="summary-row">

            <span>Replacement Donations</span>

            <strong>${donationHistoryState.summary.replacement}</strong>

        </div>

    `;

}


/* ============================================================
   Recent Donors
============================================================ */

function renderRecentDonors() {

    const container = document.getElementById("recentDonors");

    if (!container) return;

    container.innerHTML = donationHistoryState.recentDonors.map(donor => `

        <div class="recent-donor">

            <div class="recent-avatar">

                ${donor.name.charAt(0)}

            </div>

            <div class="recent-info">

                <strong>${donor.name}</strong>

                <small>${donor.date}</small>

            </div>

            <span class="blood-badge ${donor.group.replace("+","plus").replace("-","minus")}">

                ${donor.group}

            </span>

        </div>

    `).join("");

}