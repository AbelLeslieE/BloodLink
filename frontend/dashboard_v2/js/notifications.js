/* ==========================================================
   BloodLink - Notifications Module
   File: notifications.js
   Description:
   Donor Response Center for monitoring donor responses
   after donation request emails have been sent.
========================================================== */


/* ==========================================================
   1. Module State
========================================================== */

let donorResponses = [];
let filteredResponses = [];
let selectedResponse = null;


/* ==========================================================
   2. Cached DOM Elements
========================================================== */

const elements = {

    /* KPI Cards */
    pendingCount: null,
    acceptedCount: null,
    declinedCount: null,
    responseRate: null,

    /* Toolbar */
    searchInput: null,
    statusFilter: null,
    refreshButton: null,

    /* Main Layout */
    responseList: null,
    responseDetails: null

};


/* ==========================================================
   3. Load Notifications Page
========================================================== */

export function loadNotifications() {

    return `

        <div class="notifications-page">

            <!-- ==========================================================
                 Hero Section
            ========================================================== -->

            <section class="notifications-hero glass-card">

                <div class="hero-content">

                    <div class="hero-left">

                        <div class="hero-icon">

                            🔔

                        </div>

                        <div class="hero-text">

                            <h1>Donor Response Center</h1>

                            <p>

                                Monitor donor availability,
                                donation confirmations and
                                live responses received from
                                donation request emails.

                            </p>

                        </div>

                    </div>


                    <div class="hero-actions">

                        <button
                            id="refreshResponsesBtn"
                            class="primary-btn">

                            Refresh Responses

                        </button>

                    </div>

                </div>

            </section>


            <!-- ==========================================================
                 KPI Section
            ========================================================== -->

            <section class="notification-kpis">

                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        ⏳

                    </div>

                    <div class="kpi-info">

                        <h2 id="pendingCount">0</h2>

                        <span>

                            Pending Responses

                        </span>

                    </div>

                </div>


                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        ✅

                    </div>

                    <div class="kpi-info">

                        <h2 id="acceptedCount">0</h2>

                        <span>

                            Accepted

                        </span>

                    </div>

                </div>


                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        ❌

                    </div>

                    <div class="kpi-info">

                        <h2 id="declinedCount">0</h2>

                        <span>

                            Declined

                        </span>

                    </div>

                </div>


                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        📊

                    </div>

                    <div class="kpi-info">

                        <h2 id="responseRate">

                            0%

                        </h2>

                        <span>

                            Response Rate

                        </span>

                    </div>

                </div>

            </section>


            <!-- ==========================================================
                 Toolbar
            ========================================================== -->

            <section class="notifications-toolbar glass-card">

                <div class="toolbar-left">

                    <input
                        id="responseSearch"
                        type="text"
                        placeholder="Search donor..."
                    >

                    <select id="responseStatusFilter">

                        <option value="all">

                            All Responses

                        </option>

                        <option value="accepted">

                            Accepted

                        </option>

                        <option value="declined">

                            Declined

                        </option>

                        <option value="pending">

                            Pending

                        </option>

                    </select>

                </div>


                <div class="toolbar-right">

                    <button
                        id="refreshListBtn"
                        class="secondary-btn">

                        Refresh

                    </button>

                </div>

            </section>


            <!-- ==========================================================
                 Main Content
            ========================================================== -->

            <section class="notifications-layout">


                <!-- ======================================================
                     Response List
                ======================================================= -->

                <div class="response-list glass-card">

                    <div class="section-title">

                        <h2>

                            Donor Responses

                        </h2>

                    </div>

                    <div
                        id="responseList"
                        class="response-list-container">

                    </div>

                </div>



                <!-- ======================================================
                     Response Details
                ======================================================= -->

                <aside
                    id="responseDetails"
                    class="response-details glass-card">

                    <div class="empty-details">

                        <div class="empty-icon">

                            ❤️

                        </div>

                        <h2>

                            No Response Selected

                        </h2>

                        <p>

                            Select a donor response from the
                            left panel to view complete details.

                        </p>

                    </div>

                </aside>

            </section>


            <!-- ==========================================================
                 Pagination
            ========================================================== -->

            <section class="pagination-section">

                <button class="pagination-btn">

                    Previous

                </button>

                <span>

                    Page 1 of 1

                </span>

                <button class="pagination-btn">

                    Next

                </button>

            </section>

        </div>

    `;

}


/* ==========================================================
   4. Initialize Notifications
========================================================== */

export function initializeNotifications() {

    cacheElements();

    loadSampleResponses();

    setupEventListeners();

    updateKPIs();

    applyFilters();

    renderResponseDetails();

}


/* ==========================================================
   5. Cache DOM Elements
========================================================== */

function cacheElements() {

    elements.pendingCount =
        document.getElementById("pendingCount");

    elements.acceptedCount =
        document.getElementById("acceptedCount");

    elements.declinedCount =
        document.getElementById("declinedCount");

    elements.responseRate =
        document.getElementById("responseRate");

    elements.searchInput =
        document.getElementById("responseSearch");

    elements.statusFilter =
        document.getElementById("responseStatusFilter");

    elements.refreshButton =
        document.getElementById("refreshListBtn");

    elements.responseList =
        document.getElementById("responseList");

    elements.responseDetails =
        document.getElementById("responseDetails");

}
/* ==========================================================
   6. Load Sample Responses
========================================================== */

function loadSampleResponses() {

    donorResponses = [

        {
            id: 1,
            donorName: "Rahul Kumar",
            bloodGroup: "O+",
            district: "Thrissur",
            hospital: "City Hospital",
            phone: "+91 9876543210",
            units: 2,
            requestTime: "Today • 10:15 AM",
            responseTime: "Today • 10:22 AM",
            status: "accepted",
            email: "rahul@email.com",
            age: 28,
            gender: "Male"
        },

        {
            id: 2,
            donorName: "Akash Nair",
            bloodGroup: "A-",
            district: "Ernakulam",
            hospital: "Medical College",
            phone: "+91 9898989898",
            units: 1,
            requestTime: "Today • 09:48 AM",
            responseTime: "Today • 10:01 AM",
            status: "declined",
            email: "akash@email.com",
            age: 34,
            gender: "Male"
        },

        {
            id: 3,
            donorName: "Anjali Joseph",
            bloodGroup: "AB+",
            district: "Kottayam",
            hospital: "District Hospital",
            phone: "+91 9988776655",
            units: 1,
            requestTime: "Today • 09:30 AM",
            responseTime: "",
            status: "pending",
            email: "anjali@email.com",
            age: 24,
            gender: "Female"
        },

        {
            id: 4,
            donorName: "Vishnu Das",
            bloodGroup: "B+",
            district: "Kochi",
            hospital: "General Hospital",
            phone: "+91 9876000000",
            units: 3,
            requestTime: "Today • 08:55 AM",
            responseTime: "Today • 09:14 AM",
            status: "accepted",
            email: "vishnu@email.com",
            age: 31,
            gender: "Male"
        },

        {
            id: 5,
            donorName: "Maria Thomas",
            bloodGroup: "O-",
            district: "Thrissur",
            hospital: "Mission Hospital",
            phone: "+91 9000000000",
            units: 2,
            requestTime: "Today • 11:00 AM",
            responseTime: "",
            status: "pending",
            email: "maria@email.com",
            age: 26,
            gender: "Female"
        }

    ];

    filteredResponses = [...donorResponses];

}


/* ==========================================================
   7. KPI Engine
========================================================== */

function updateKPIs() {

    const total = donorResponses.length;

    const accepted = donorResponses.filter(
        donor => donor.status === "accepted"
    ).length;

    const declined = donorResponses.filter(
        donor => donor.status === "declined"
    ).length;

    const pending = donorResponses.filter(
        donor => donor.status === "pending"
    ).length;

    const responded = accepted + declined;

    const rate = total === 0
        ? 0
        : Math.round((responded / total) * 100);


    elements.pendingCount.textContent = pending;

    elements.acceptedCount.textContent = accepted;

    elements.declinedCount.textContent = declined;

    elements.responseRate.textContent = `${rate}%`;

}


/* ==========================================================
   8. Render Response Cards
========================================================== */

function renderResponseCards() {

    if (!elements.responseList) return;

    elements.responseList.innerHTML = "";

    if (filteredResponses.length === 0) {

        renderEmptyState();
        return;

    }

    filteredResponses.forEach(response => {

        const card = document.createElement("div");

        card.className = "donor-response-card";

        if (
            selectedResponse &&
            selectedResponse.id === response.id
        ) {
            card.classList.add("active");
        }

        let statusIcon = "⏳";

        if (response.status === "accepted") {

            statusIcon = "✅";

        } else if (response.status === "declined") {

            statusIcon = "❌";

        }

        card.innerHTML = `

            <div class="response-card-top">

                <div class="response-avatar">

                    ❤️

                </div>

                <div class="response-information">

                    <h3>

                        ${response.donorName}

                    </h3>

                    <p>

                        ${response.bloodGroup}
                        •
                        ${response.district}

                    </p>

                </div>

                <div class="response-status">

                    <span class="status-badge ${response.status}">

                        ${statusIcon}
                        ${capitalize(response.status)}

                    </span>

                </div>

            </div>


            <div class="response-card-middle">

                <div>

                    <strong>Hospital</strong>

                    <span>

                        ${response.hospital}

                    </span>

                </div>

                <div>

                    <strong>Units</strong>

                    <span>

                        ${response.units}

                    </span>

                </div>

            </div>


            <div class="response-card-footer">

                <span>

                    ${response.requestTime}

                </span>

                <span>

                    ${response.responseTime || "Awaiting Response"}

                </span>

            </div>

        `;

        card.addEventListener("click", () => {

            selectedResponse = response;

            renderResponseCards();

            renderResponseDetails();

        });

        elements.responseList.appendChild(card);

    });

}


/* ==========================================================
   9. Render Details Panel
========================================================== */

function renderResponseDetails() {

    if (!elements.responseDetails) return;

    if (!selectedResponse) {

        elements.responseDetails.innerHTML = `

            <div class="empty-details">

                <div class="empty-icon">

                    ❤️

                </div>

                <h2>

                    No Response Selected

                </h2>

                <p>

                    Select a donor response
                    to view complete information.

                </p>

            </div>

        `;

        return;

    }

    elements.responseDetails.innerHTML = `

        <div class="response-details-content">

            <div class="details-header">

                <h2>

                    ${selectedResponse.donorName}

                </h2>

                <span class="status-badge ${selectedResponse.status}">

                    ${capitalize(selectedResponse.status)}

                </span>

            </div>


            <div class="details-grid">

                <div>

                    <label>Blood Group</label>

                    <span>

                        ${selectedResponse.bloodGroup}

                    </span>

                </div>

                <div>

                    <label>Age</label>

                    <span>

                        ${selectedResponse.age}

                    </span>

                </div>

                <div>

                    <label>Gender</label>

                    <span>

                        ${selectedResponse.gender}

                    </span>

                </div>

                <div>

                    <label>Hospital</label>

                    <span>

                        ${selectedResponse.hospital}

                    </span>

                </div>

                <div>

                    <label>District</label>

                    <span>

                        ${selectedResponse.district}

                    </span>

                </div>

                <div>

                    <label>Phone</label>

                    <span>

                        ${selectedResponse.phone}

                    </span>

                </div>

                <div>

                    <label>Email</label>

                    <span>

                        ${selectedResponse.email}

                    </span>

                </div>

                <div>

                    <label>Units Needed</label>

                    <span>

                        ${selectedResponse.units}

                    </span>

                </div>

                <div>

                    <label>Request Time</label>

                    <span>

                        ${selectedResponse.requestTime}

                    </span>

                </div>

                <div>

                    <label>Response Time</label>

                    <span>

                        ${selectedResponse.responseTime || "Pending"}

                    </span>

                </div>

            </div>


            <div class="details-actions">

                <button
                    class="primary-btn"
                    id="viewDonorBtn">

                    View Donor

                </button>

                <button
                    class="secondary-btn"
                    id="callDonorBtn">

                    Call Donor

                </button>

            </div>

        </div>

    `;

}

/* ==========================================================
   11. Setup Event Listeners
========================================================== */

function setupEventListeners() {

    /* Search */

    elements.searchInput.addEventListener("input", () => {

        applyFilters();

    });


    /* Status Filter */

    elements.statusFilter.addEventListener("change", () => {

        applyFilters();

    });


    /* Refresh */

    elements.refreshButton.addEventListener("click", () => {

        refreshResponses();

    });

}
/* ==========================================================
   12. Search & Filter Engine
========================================================== */

function applyFilters() {

    const searchText =
        elements.searchInput.value
            .trim()
            .toLowerCase();

    const selectedStatus =
        elements.statusFilter.value;

    filteredResponses = donorResponses.filter(response => {

        const matchesSearch =

            response.donorName.toLowerCase().includes(searchText) ||

            response.bloodGroup.toLowerCase().includes(searchText) ||

            response.district.toLowerCase().includes(searchText) ||

            response.hospital.toLowerCase().includes(searchText);

        const matchesStatus =

            selectedStatus === "all"

                ? true

                : response.status === selectedStatus;

        return matchesSearch && matchesStatus;

    });

    renderResponseCards();

}
/* ==========================================================
   13. Refresh Responses
========================================================== */

function refreshResponses() {

    loadSampleResponses();

    applyFilters();

    updateKPIs();

    renderResponseDetails();

}
/* ==========================================================
   10. Empty State
========================================================== */

function renderEmptyState() {

    elements.responseList.innerHTML = `

        <div class="empty-response-list">

            <div class="empty-icon">

                📭

            </div>

            <h3>

                No Responses Found

            </h3>

            <p>

                There are currently no donor
                responses matching your filters.

            </p>

        </div>

    `;

}
/* ==========================================================
   11. Utility Functions
========================================================== */

function capitalize(text) {

    return text.charAt(0).toUpperCase() + text.slice(1);

}