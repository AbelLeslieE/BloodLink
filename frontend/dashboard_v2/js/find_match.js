/* ===================================================================
   BloodLink - Find Match Module
   -------------------------------------------------------------------
   Module:
       Find Compatible Blood Donors

   Workflow:
       Blood Request
            ↓
       Find Compatible Donors
            ↓
       Select Donors
            ↓
       Save Match
            ↓
       Send Email
            ↓
       Notification Response

   NOTE:
   This module is built using card-based rendering.
   No table rendering is used anywhere.
=================================================================== */

import { authenticatedFetch } from "./api.js";

/* ===================================================================
   API ENDPOINTS
=================================================================== */

/* ===================================================================
   API ENDPOINTS
=================================================================== */

const REQUEST_API = "/api/blood-requests";

const MATCH_API = "/api/match/find";

const SEND_NOTIFICATION_API = "/api/match/send";

const NOTIFICATION_STATS_API =
    "/api/notifications/stats/summary";
/* ===================================================================
   MODULE STATE
=================================================================== */

const state = {

    bloodRequests: [],

    matchingDonors: [],

    filteredRequests: [],

    filteredDonors: [],

    selectedRequest: null,

    selectedDonors: new Set(),

    statistics: {

        pending: 0,

        matches: 0,

        emails: 0,

        responses: 0

    }

};


/* ===================================================================
   INITIALIZE MODULE
=================================================================== */

export function loadFindMatch(container) {

    if (!container) return;

    initializeState();

    container.innerHTML = getFindMatchTemplate();

    bindEvents();

    initializeModule();

}

/* ===================================================================
   INITIALIZE STATE
=================================================================== */

function initializeState() {

    state.bloodRequests = [];

    state.filteredRequests = [];

    state.matchingDonors = [];

    state.filteredDonors = [];

    state.selectedRequest = null;

    state.selectedDonors.clear();

    state.statistics = {

        pending: 0,

        matches: 0,

        emails: 0,

        responses: 0

    };

}
/* ===================================================================
   MAIN TEMPLATE
=================================================================== */

function getFindMatchTemplate() {

    return `

    <div class="find-match-page">

        <!-- Background Overlay -->
        <div class="find-match-overlay"></div>

        <!-- Main Content -->
        <div class="find-match-container">

            <!-- =======================================================
                 HEADER
            ======================================================== -->

            <section class="fm-header glass-card">

            <div class="fm-header-left">

                <span class="fm-page-tag">
                    BLOODLINK MATCHING
                </span>

                <h1 class="fm-title">
                    Find Compatible Donors
                </h1>

                <p class="fm-subtitle">
                    Search compatible donors, manage pending blood requests,
                    contact donors and monitor responses from one dashboard.
                </p>

            </div>

            <div class="fm-header-right">

                <div class="quick-actions-card">

                    <h3>Quick Actions</h3>

                    <div class="hero-action-grid">

                        <button
                            id="sendEmailHeroBtn"
                            class="primary-btn">

                            Send Email

                        </button>

                        <button
                            id="exportMatchesBtn"
                            class="secondary-btn">

                            Export List

                        </button>

                        <button
                            id="refreshDashboardBtn"
                            class="secondary-btn">

                            Refresh

                        </button>

                    </div>

                </div>

            </div>

        </section>

            <!-- =======================================================
                 KPI SECTION
            ======================================================== -->

            <section class="kpi-grid">

                <div class="kpi-card glass-card">

                    <span class="kpi-title">

                        Pending Requests

                    </span>

                    <h2 id="pendingRequestsCount">

                        0

                    </h2>

                </div>

                <div class="kpi-card glass-card">

                    <span class="kpi-title">

                        Compatible Donors

                    </span>

                    <h2 id="matchingDonorsCount">

                        0

                    </h2>

                </div>

                <div class="kpi-card glass-card">

                    <span class="kpi-title">

                        Emails Sent

                    </span>

                    <h2 id="emailsSentCount">

                        0

                    </h2>

                </div>

                <div class="kpi-card glass-card">

                    <span class="kpi-title">

                        Responses

                    </span>

                    <h2 id="responsesCount">

                        0

                    </h2>

                </div>

            </section>

            <!-- =======================================================
                 SEARCH PANEL
            ======================================================== -->

            <section class="search-panel glass-card">

                <div class="search-grid">

                    <input
                        id="patientSearch"
                        class="search-input"
                        type="text"
                        placeholder="Search Patient">

                    <select
                        id="bloodGroupFilter"
                        class="search-select">

                        <option value="">
                            Blood Group
                        </option>

                        <option>A+</option>
                        <option>A-</option>
                        <option>B+</option>
                        <option>B-</option>
                        <option>AB+</option>
                        <option>AB-</option>
                        <option>O+</option>
                        <option>O-</option>

                    </select>

                    <input
                        id="districtSearch"
                        class="search-input"
                        type="text"
                        placeholder="District">

                    <input
                        id="hospitalSearch"
                        class="search-input"
                        type="text"
                        placeholder="Hospital">

                    <button
                        id="searchButton"
                        class="primary-btn">

                        Search

                    </button>

                </div>

            </section>

            <!-- =======================================================
                 CONTENT GRID
            ======================================================== -->

            <section class="fm-main-grid">

                <!-- LEFT COLUMN -->

                <div class="left-column">

                    <div class="glass-card section-card">

                        <div class="section-header">

                            <h2>

                                Pending Blood Requests

                            </h2>

                            <span id="requestCountBadge"
                                  class="badge">

                                0

                            </span>

                        </div>

                        <div
                            id="requestCardsContainer"
                            class="request-list">

                        </div>

                    </div>

                </div>

                <!-- RIGHT COLUMN -->

                <div class="right-column">

                <div class="glass-card section-card">

                    <div class="section-header">

                    <h2>
                        Compatible Donors
                    </h2>

                    <div class="section-actions">

                        <input
                            type="text"
                            id="compatibleDonorSearch"
                            class="search-input donor-search-input"
                            placeholder="Search donor name...">

                        <label class="select-all-wrapper">

                            <input
                                type="checkbox"
                                id="selectAllDonors">

                            <span>
                                Select All Compatible
                            </span>

                        </label>

                    </div>

                </div>

                    <div class="donor-panel">

                    <div
                        id="donorCardsContainer"
                        class="donor-list">

                        <div class="empty-state">

                            Select a blood request to view
                            compatible donors.

                        </div>

                    </div>

                    <div class="donor-panel-footer">

                        <div class="selected-info">

                            Selected Donors :

                            <strong id="selectedDonorCount">

                                0

                            </strong>

                        </div>

                        <div class="panel-actions">

                            <button
                                id="saveMatchBtn"
                                class="secondary-btn"
                                disabled>

                                Save Match

                            </button>

                            <button
                                id="sendEmailBtn"
                                class="primary-btn"
                                disabled>

                                Send Email

                            </button>

                        </div>

                    </div>

                </div>

                </div>

            </div>
            </section>
            <!-- =======================================================
                BLOOD AVAILABILITY
            ======================================================= -->

            <section class="glass-card blood-availability-section">

                <div class="section-header">

                    <h2>Blood Availability</h2>

                    <button
                        class="secondary-btn"
                        id="refreshAvailabilityBtn">

                        Refresh Availability

                    </button>

                </div>

                <div
                    class="availability-grid"
                    id="bloodAvailabilityGrid">

                    ${renderBloodAvailability()}

                </div>

            </section>
            <!-- =======================================================
                 FOOTER ACTION BAR
            ======================================================== -->





        <!-- Toast -->

        <div
            id="toastContainer"
            class="toast-container">

        </div>

    </div>

    `;

}
/* ===================================================================
   DASHBOARD RENDERING
=================================================================== */

function renderDashboard() {

    renderKPICards();

    renderBloodAvailability();

    renderRequestCards();

    renderDonorCards();

}

/* ===================================================================
   KPI CARDS
=================================================================== */

function renderKPICards() {

    const pendingElement = document.getElementById("pendingRequestsCount");
    const matchingElement = document.getElementById("matchingDonorsCount");
    const emailElement = document.getElementById("emailsSentCount");
    const responseElement = document.getElementById("responsesCount");

    const requestBadge = document.getElementById("requestCountBadge");


    state.statistics.pending = state.filteredRequests.length;
    state.statistics.matches = state.filteredDonors.length;

    if (pendingElement)
        pendingElement.textContent = state.statistics.pending;

    if (matchingElement)
        matchingElement.textContent = state.statistics.matches;

    if (emailElement)
        emailElement.textContent = state.statistics.emails;

    if (responseElement)
        responseElement.textContent = state.statistics.responses;

    if (requestBadge)
        requestBadge.textContent = state.filteredRequests.length;



}

/* ===================================================================
   BLOOD AVAILABILITY PANEL
=================================================================== */

function renderBloodAvailability() {

    const container = document.getElementById(
        "bloodAvailabilityGrid"
    );
    if (!container) return;

    const availability = [

        { group: "A+", units: 15 },
        { group: "A-", units: 4 },
        { group: "B+", units: 12 },
        { group: "B-", units: 3 },
        { group: "AB+", units: 6 },
        { group: "AB-", units: 2 },
        { group: "O+", units: 20 },
        { group: "O-", units: 5 }

    ];

    container.innerHTML = availability
        .map(item => `
            <div class="availability-card">

                <span class="availability-group">

                    ${item.group}

                </span>

                <span class="availability-count">

                    ${item.units}

                </span>

            </div>
        `)
        .join("");

}

/* ===================================================================
   REQUEST CARDS
=================================================================== */

function renderRequestCards() {

    const container = document.getElementById(
        "requestCardsContainer"
    );

    if (!container) return;

    container.innerHTML = "";

    if (state.filteredRequests.length === 0) {

        container.innerHTML = `
            <div class="empty-state">

                No pending requests found.

            </div>
        `;

        return;

    }

    state.filteredRequests.forEach(request => {

        container.insertAdjacentHTML(

            "beforeend",

            createRequestCard(request)

        );

    });

}

/* ===================================================================
   DONOR CARDS
=================================================================== */

function renderDonorCards() {

    const container = document.getElementById(
        "donorCardsContainer"
    );

    if (!container) return;

    container.innerHTML = "";

    if (!state.selectedRequest) {

        container.innerHTML = `
            <div class="empty-state">

                Select a blood request to
                view compatible donors.

            </div>
        `;

        renderKPICards();

        return;

    }

    if (state.filteredDonors.length === 0) {

        container.innerHTML = `
            <div class="empty-state">

                No compatible donors available.

            </div>
        `;

        renderKPICards();

        return;

    }

    state.filteredDonors.forEach(donor => {

        container.insertAdjacentHTML(

            "beforeend",

            createDonorCard(donor)

        );

    });

    renderKPICards();

}
/* ===================================================================
   REQUEST CARD COMPONENT
=================================================================== */

function createRequestCard(request) {

    const selected =
        state.selectedRequest &&
        state.selectedRequest.id === request.id;

    return `

        <article
            class="request-card ${selected ? "active" : ""}"
            data-request-id="${request.id}">

            <div class="request-top">

                <div class="request-avatar">

                    ${request.patient.charAt(0).toUpperCase()}

                </div>

                <div class="request-header">

                    <h3>

                        ${request.patient}

                    </h3>

                    <p>

                        ${request.hospital}

                    </p>

                </div>

                <span class="priority-badge priority-${request.priority.toLowerCase()}">

                    ${request.priority}

                </span>

            </div>

            <div class="request-information">

                <div class="info-item">

                    <span class="info-label">

                        Blood Group

                    </span>

                    <span class="blood-group">

                        ${request.bloodGroup}

                    </span>

                </div>

                <div class="info-item">

                    <span class="info-label">

                        Units

                    </span>

                    <strong>

                        ${request.units}

                    </strong>

                </div>

                <div class="info-item">

                    <span class="info-label">

                        District

                    </span>

                    <strong>

                        ${request.district}

                    </strong>

                </div>

                <div class="info-item">

                    <span class="info-label">

                        Required

                    </span>

                    <strong>

                        ${request.requiredDate}

                    </strong>

                </div>

            </div>

            <div class="request-footer">

                <button
                    class="primary-btn request-select-btn"
                    data-request-id="${request.id}">

                    Find Compatible Donors

                </button>

            </div>

        </article>

    `;

}

/* ===================================================================
   DONOR CARD COMPONENT
=================================================================== */

function createDonorCard(donor) {

    const selected =
        state.selectedDonors.has(donor.id);

    return `

        <article
            class="donor-card ${selected ? "selected" : ""}"
            data-donor-id="${donor.id}">

            <div class="donor-top">

                <div class="donor-avatar">

                    ${donor.name.charAt(0).toUpperCase()}

                </div>

                <div class="donor-header">

                    <h3>

                        ${donor.name}

                    </h3>

                    <p>

                        ${donor.phone}

                    </p>

                </div>

            </div>

            <div class="donor-information">

                <div class="info-item">

                    <span class="info-label">

                        Blood Group

                    </span>

                    <span class="blood-group">

                        ${donor.bloodGroup}

                    </span>

                </div>

                <div class="info-item">

                    <span class="info-label">

                        Distance

                    </span>

                    <strong>

                        ${donor.distance}

                    </strong>

                </div>

                <div class="info-item">

                    <span class="info-label">

                        Availability

                    </span>

                    <strong class="available">

                        ${donor.availability}

                    </strong>

                </div>

                <div class="info-item">

                    <span class="info-label">

                        Last Donation

                    </span>

                    <strong>

                        ${donor.lastDonation}

                    </strong>

                </div>

            </div>

            <div class="compatibility-section">

                <div class="compatibility-header">

                    <span>

                        Compatibility Score

                    </span>

                    <strong>

                        ${donor.compatibility}%

                    </strong>

                </div>

                <div class="compatibility-bar">

                    <div
                        class="compatibility-fill"
                        style="width:${donor.compatibility}%">

                    </div>

                </div>

            </div>

            <div class="donor-footer">

                <button
                    class="select-donor-btn ${selected ? "selected" : ""}"
                    data-donor-id="${donor.id}">

                    ${selected ? "Selected" : "Select Donor"}

                </button>

            </div>

        </article>

    `;

}

/* ===================================================================
   TOAST COMPONENT
=================================================================== */

function showToast(message, type = "success") {

    const container =
        document.getElementById("toastContainer");

    if (!container) return;

    const toast = document.createElement("div");

    toast.className = `toast ${type}`;

    toast.textContent = message;

    container.appendChild(toast);

    requestAnimationFrame(() => {

        toast.classList.add("show");

    });

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => {

            toast.remove();

        }, 300);

    }, 3000);

}
/* ===================================================================
   EVENT BINDING
=================================================================== */

function bindEvents() {

    /* ---------------- Refresh ---------------- */

    document
        .getElementById("refreshDashboardBtn")
        ?.addEventListener("click", refreshDashboard);

    document
        .getElementById("sendEmailHeroBtn")
        ?.addEventListener(
            "click",
            sendSelectedEmails
        );

    document
        .getElementById("exportMatchesBtn")
        ?.addEventListener(
            "click",
            exportMatches
        );
    document
        .getElementById("refreshMatchesBtn")
        ?.addEventListener("click", refreshDashboard);

    /* ---------------- Search ---------------- */

    document
        .getElementById("searchButton")
        ?.addEventListener("click", filterRequests);

    document
        .getElementById("patientSearch")
        ?.addEventListener("input", filterRequests);

    document
        .getElementById("bloodGroupFilter")
        ?.addEventListener("change", filterRequests);

    document
        .getElementById("districtSearch")
        ?.addEventListener("input", filterRequests);

    document
        .getElementById("hospitalSearch")
        ?.addEventListener("input", filterRequests);
    document
        .getElementById("compatibleDonorSearch")
        ?.addEventListener(
            "input",
            filterCompatibleDonors
        );    

    /* ---------------- Request Selection ---------------- */

    document.addEventListener("click", handleRequestSelection);

    /* ---------------- Donor Selection ---------------- */

    document.addEventListener("click", handleDonorSelection);
    document
        .getElementById("selectAllDonors")
        ?.addEventListener("change", handleSelectAllDonors);
    /* ---------------- Footer Buttons ---------------- */

    document
        .getElementById("saveMatchBtn")
        ?.addEventListener("click", saveSelectedMatch);

    document
        .getElementById("sendEmailBtn")
        ?.addEventListener("click", sendSelectedEmails);

}

/* ===================================================================
   REFRESH DASHBOARD
=================================================================== */

async function refreshDashboard() {

    await refreshModule();

}

/* ===================================================================
   REQUEST SELECTION
=================================================================== */

function handleRequestSelection(event) {

    const button =
        event.target.closest(".request-select-btn");

    if (!button) return;

    const requestId =
        Number(button.dataset.requestId);

    const request =
        state.bloodRequests.find(item =>
            item.id === requestId
        );

    if (!request) return;

    state.selectedRequest = request;

    loadMatchingDonorsFromAPI(request.id);

    renderRequestCards();

}



/* ===================================================================
   DONOR SELECTION
=================================================================== */

function handleDonorSelection(event) {

    const button =
        event.target.closest(".select-donor-btn");

    if (!button) return;

    const donorId =
        Number(button.dataset.donorId);

    if (state.selectedDonors.has(donorId)) {

        state.selectedDonors.delete(donorId);

    } else {

        state.selectedDonors.add(donorId);

    }

    updateSelectedCounter();

    renderDonorCards();

}
function handleSelectAllDonors(event) {

    if (event.target.checked) {

        state.filteredDonors.forEach(donor => {

            state.selectedDonors.add(donor.id);

        });

    } else {

        state.selectedDonors.clear();

    }

    updateSelectedCounter();

    renderDonorCards();

}
/* ===================================================================
   SELECTED COUNTER
=================================================================== */

function updateSelectedCounter() {

    const counter = document.getElementById("selectedDonorCount");

    const saveButton = document.getElementById("saveMatchBtn");

    const emailButton = document.getElementById("sendEmailBtn");

    const heroEmailButton = document.getElementById("sendEmailHeroBtn");

    const selectedCount = state.selectedDonors.size;

    if (counter) {
        counter.textContent = selectedCount;
    }

    const hasSelection = selectedCount > 0;

    if (saveButton) {
        saveButton.disabled = !hasSelection;
    }

    if (emailButton) {
        emailButton.disabled = !hasSelection;
    }

    if (heroEmailButton) {
        heroEmailButton.disabled = !hasSelection;
    }

}

/* ===================================================================
   SAVE MATCH
=================================================================== */

function saveSelectedMatch() {

    if (!state.selectedRequest) {

        showToast(
            "Select a blood request first.",
            "warning"
        );

        return;

    }

    if (state.selectedDonors.size === 0) {

        showToast(
            "Please select at least one donor.",
            "warning"
        );

        return;

    }

    saveMatchToDatabase();

}

/* ===================================================================
   SEND EMAIL
=================================================================== */

function sendSelectedEmails() {

    if (state.selectedDonors.size === 0) {

        showToast(
            "No donors selected.",
            "warning"
        );

        return;

    }

    sendEmailsToSelectedDonors();

}
/* ===================================================================
   SEARCH & FILTERING ENGINE
=================================================================== */

function filterRequests() {

    const patient =
        document
            .getElementById("patientSearch")
            ?.value
            .trim()
            .toLowerCase() || "";

    const bloodGroup =
        document
            .getElementById("bloodGroupFilter")
            ?.value
            .trim()
            .toLowerCase() || "";

    const district =
        document
            .getElementById("districtSearch")
            ?.value
            .trim()
            .toLowerCase() || "";

    const hospital =
        document
            .getElementById("hospitalSearch")
            ?.value
            .trim()
            .toLowerCase() || "";

    state.filteredRequests = state.bloodRequests.filter(request => {

        const matchesPatient =
            !patient ||
            request.patient.toLowerCase().includes(patient);

        const matchesBloodGroup =
            !bloodGroup ||
            request.bloodGroup.toLowerCase() === bloodGroup;

        const matchesDistrict =
            !district ||
            request.district.toLowerCase().includes(district);

        const matchesHospital =
            !hospital ||
            request.hospital.toLowerCase().includes(hospital);

        return (
            matchesPatient &&
            matchesBloodGroup &&
            matchesDistrict &&
            matchesHospital
        );

    });

    /* -------------------------------------------------------
       If the selected request disappears after filtering,
       clear the donor panel.
    -------------------------------------------------------- */

    if (
        state.selectedRequest &&
        !state.filteredRequests.some(
            request => request.id === state.selectedRequest.id
        )
    ) {

        state.selectedRequest = null;

        state.matchingDonors = [];

        state.filteredDonors = [];

        state.selectedDonors.clear();

    }
    const selectAllCheckbox =
        document.getElementById("selectAllDonors");

    if (selectAllCheckbox) {

        selectAllCheckbox.checked =
            state.filteredDonors.length > 0 &&
            state.selectedDonors.size === state.filteredDonors.length;

    }
    updateSelectedCounter();

    renderKPICards();

    renderRequestCards();

    renderDonorCards();

}
/* ===================================================================
   FILTER COMPATIBLE DONORS
=================================================================== */

function filterCompatibleDonors() {

    const keyword =
        document
            .getElementById("compatibleDonorSearch")
            ?.value
            .trim()
            .toLowerCase() || "";

    state.filteredDonors =
        state.matchingDonors.filter(donor => {

            return donor.name
                .toLowerCase()
                .includes(keyword);

        });

    renderDonorCards();

}
/* ===================================================================
   CLEAR SEARCH FILTERS
=================================================================== */

function clearFilters() {

    document.getElementById("patientSearch").value = "";

    document.getElementById("bloodGroupFilter").value = "";

    document.getElementById("districtSearch").value = "";

    document.getElementById("hospitalSearch").value = "";

    state.filteredRequests = [...state.bloodRequests];

    state.selectedRequest = null;

    state.matchingDonors = [];

    state.filteredDonors = [];

    state.selectedDonors.clear();

    updateSelectedCounter();

    renderDashboard();

}

/* ===================================================================
   EXPORT PLACEHOLDER
=================================================================== */

function exportMatches() {

    if (!state.selectedRequest) {

        showToast(
            "Select a blood request before exporting.",
            "warning"
        );

        return;

    }

    console.table({

        request: state.selectedRequest,

        donors: [...state.selectedDonors]

    });

    showToast(
        "Export feature will be connected to the backend."
    );

}

/* ===================================================================
   BEST MATCH PLACEHOLDER
=================================================================== */

function findBestMatch() {

    if (!state.selectedRequest) {

        showToast(
            "Please select a blood request first.",
            "warning"
        );

        return;

    }

    if (state.filteredDonors.length === 0) {

        showToast(
            "No compatible donors found.",
            "warning"
        );

        return;

    }

    state.selectedDonors.clear();

    state.selectedDonors.add(
        state.filteredDonors[0].id
    );

    updateSelectedCounter();

    renderDonorCards();

    showToast(
        `${state.filteredDonors[0].name} selected as the best match.`
    );

}
/* ===================================================================
   BACKEND SERVICE LAYER
   -------------------------------------------------------------------
   These functions act as the communication layer between the
   Find Match UI and the backend API.

   Currently they use demo data.

   Later they will call authenticatedFetch().
=================================================================== */


/* ===================================================================
   LOAD BLOOD REQUESTS
=================================================================== */

async function loadBloodRequests() {

    try {

        showLoading("requestCardsContainer");

        const response = await authenticatedFetch(
            REQUEST_API
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load blood requests."
            );

        }

        const requests = await response.json();

        /*
        ----------------------------------------------------------
        Convert backend response into the existing UI format.
        ----------------------------------------------------------
        */

        state.bloodRequests = requests.map(request => ({

            id: request.id,

            patient: request.patient_name,

            hospital: request.hospital_name,

            district: request.hospital_location,

            bloodGroup: request.blood_group,

            units: request.units_required,

            priority: request.priority,

            requiredDate: formatDate(
                request.required_date
            ),

            status: request.status

        }));

        /*
        ----------------------------------------------------------
        Only show pending and in-progress requests.
        ----------------------------------------------------------
        */

        state.filteredRequests = state.bloodRequests.filter(

            request =>

                request.status === "Pending" ||

                request.status === "In Progress"

        );

        state.statistics.pending =
            state.filteredRequests.length;

        renderDashboard();

    }

    catch (error) {

        console.error(error);

        renderEmptyState(

            "requestCardsContainer",

            "Unable to load blood requests."

        );

        showToast(

            error.message,

            "error"

        );

    }

}

/* ===================================================================
   LOAD MATCHING DONORS
=================================================================== */

/* ===================================================================
   LOAD MATCHING DONORS
=================================================================== */

async function loadMatchingDonorsFromAPI(requestId) {

    try {

        showLoading("donorCardsContainer");

        const response = await authenticatedFetch(
            MATCH_API,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    blood_request_id: requestId
                })
            }
        );

        if (!response.ok) {

            throw new Error(
                "Unable to retrieve compatible donors."
            );

        }

        const result = await response.json();

        /*
        ----------------------------------------------------------
        Convert backend response into the UI format expected by
        the existing donor cards.
        ----------------------------------------------------------
        */

        state.matchingDonors = result.matches.map(match => ({

            id: match.donor.id,

            name: match.donor.name,

            phone: match.donor.phone,

            email: match.donor.email,

            bloodGroup: match.donor.blood_group,

            district: match.donor.district,

            availability: match.donor.status,

            compatibility: match.score,

            rank: match.rank,

            distance: "-",

            lastDonation: "-"

        }));

        state.filteredDonors = [...state.matchingDonors];

        state.selectedDonors.clear();

        updateSelectedCounter();

        renderDonorCards();

        renderKPICards();

        showToast(
            `${result.total_matches} compatible donors found.`,
            "success"
        );

    } catch (error) {

        console.error(error);

        renderEmptyState(
            "donorCardsContainer",
            "Unable to load compatible donors."
        );

        showToast(
            error.message,
            "error"
        );

    }

}
/* ===================================================================
   SAVE MATCH
=================================================================== */

async function saveMatchToDatabase() {

    try {

        if (!state.selectedRequest)
            return;

        const payload = {

            blood_request_id: state.selectedRequest.id,

            donor_ids: [...state.selectedDonors]

        };

        /*
        Future Backend

        await authenticatedFetch(

            MATCH_SAVE_API,

            {

                method: "POST",

                headers: {

                    "Content-Type":"application/json"

                },

                body: JSON.stringify(payload)

            }

        );

        */

        console.log(payload);

        showToast(
            "Match saved successfully."
        );

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to save match.",
            "error"
        );

    }

}

/* ===================================================================
   SEND EMAILS
=================================================================== */

/* ===================================================================
   SEND EMAILS
=================================================================== */

async function sendEmailsToSelectedDonors() {

    try {

        if (!state.selectedRequest) {

            showToast(
                "Please select a blood request.",
                "warning"
            );

            return;

        }

        if (state.selectedDonors.size === 0) {

            showToast(
                "Please select at least one donor.",
                "warning"
            );

            return;

        }

        const response = await authenticatedFetch(

            SEND_NOTIFICATION_API,

            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify({

                    blood_request_id: state.selectedRequest.id,

                    donor_ids: [...state.selectedDonors]

                })

            }

        );

        if (!response.ok) {

            throw new Error(
                "Failed to send notification emails."
            );

        }

        const result = await response.json();

        state.statistics.emails += result.emails_sent;

        renderKPICards();

        showToast(

            `${result.emails_sent} notification emails sent successfully.`,

            "success"

        );

    }

    catch (error) {

        console.error(error);

        showToast(

            error.message,

            "error"

        );

    }

}

/* ===================================================================
   LOAD DASHBOARD STATISTICS
=================================================================== */

/* ===================================================================
   LOAD DASHBOARD STATISTICS
=================================================================== */

async function loadDashboardStatistics() {

    try {

        const response = await authenticatedFetch(
            NOTIFICATION_STATS_API
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load dashboard statistics."
            );

        }

        const statistics = await response.json();

        /*
        ----------------------------------------------------------
        Merge backend statistics with UI statistics.
        Pending Requests and Compatible Donors are still driven
        by the currently loaded page state.
        ----------------------------------------------------------
        */

        state.statistics.pending =
            state.filteredRequests.length;

        state.statistics.matches =
            state.filteredDonors.length;

        state.statistics.emails =
            statistics.emails_sent;

        state.statistics.responses =
            statistics.accepted +
            statistics.declined;

        renderKPICards();

    }

    catch (error) {

        console.error(error);

        showToast(
            error.message,
            "error"
        );

    }

}

/* ===================================================================
   LOAD BLOOD AVAILABILITY
=================================================================== */

async function loadBloodAvailability() {

    try {

        /*
        Future Backend

        const response =
            await authenticatedFetch("/api/inventory/summary");

        const inventory =
            await response.json();

        */

        renderBloodAvailability();

    } catch (error) {

        console.error(error);

    }

}
/* ===================================================================
   UTILITY FUNCTIONS
=================================================================== */

/* ===================================================================
   GET PRIORITY CLASS
=================================================================== */

function getPriorityClass(priority) {

    if (!priority) return "priority-medium";

    switch (priority.toLowerCase()) {

        case "critical":
            return "priority-critical";

        case "high":
            return "priority-high";

        case "medium":
            return "priority-medium";

        case "low":
            return "priority-low";

        default:
            return "priority-medium";
    }

}

/* ===================================================================
   FORMAT DATE
=================================================================== */

function formatDate(date) {

    if (!date) return "-";

    const value = new Date(date);

    return value.toLocaleDateString("en-IN", {

        day: "2-digit",

        month: "short",

        year: "numeric"

    });

}

/* ===================================================================
   SORT DONORS
=================================================================== */

function sortDonors() {

    state.filteredDonors.sort((a, b) => {

        if (b.compatibility !== a.compatibility)
            return b.compatibility - a.compatibility;

        const distanceA =
            parseFloat(a.distance);

        const distanceB =
            parseFloat(b.distance);

        return distanceA - distanceB;

    });

}



/* ===================================================================
   RESET SELECTIONS
=================================================================== */

function resetSelections() {

    state.selectedRequest = null;

    state.selectedDonors.clear();

    state.matchingDonors = [];

    state.filteredDonors = [];

    updateSelectedCounter();

}

/* ===================================================================
   LOADING STATE
=================================================================== */

function showLoading(containerId) {

    const container =
        document.getElementById(containerId);

    if (!container) return;

    container.innerHTML = `

        <div class="loading-state">

            <div class="loading-spinner"></div>

            <span>

                Loading...

            </span>

        </div>

    `;

}

/* ===================================================================
   EMPTY STATE
=================================================================== */

function renderEmptyState(

    containerId,

    message

) {

    const container =
        document.getElementById(containerId);

    if (!container) return;

    container.innerHTML = `

        <div class="empty-state">

            ${message}

        </div>

    `;

}

/* ===================================================================
   UPDATE DASHBOARD STATISTICS
=================================================================== */

function updateStatistics() {

    state.statistics.pending =
        state.filteredRequests.length;

    state.statistics.matches =
        state.filteredDonors.length;

    renderKPICards();

}

/* ===================================================================
   GET SELECTED DONORS
=================================================================== */

function getSelectedDonorObjects() {

    return state.filteredDonors.filter(

        donor =>

        state.selectedDonors.has(donor.id)

    );

}

/* ===================================================================
   CLEAR SEARCH
=================================================================== */

function clearSearchFields() {

    const patient =
        document.getElementById("patientSearch");

    const blood =
        document.getElementById("bloodGroupFilter");

    const district =
        document.getElementById("districtSearch");

    const hospital =
        document.getElementById("hospitalSearch");

    if (patient) patient.value = "";

    if (blood) blood.value = "";

    if (district) district.value = "";

    if (hospital) hospital.value = "";
        const donor =
        document.getElementById(
            "compatibleDonorSearch"
        );

    if (donor)
        donor.value = "";

}

/* ===================================================================
   REFRESH MODULE
=================================================================== */

async function refreshModule() {

    clearSearchFields();

    resetSelections();

    initializeState();

    await loadBloodRequests();

    await loadDashboardStatistics();

    await loadBloodAvailability();

    updateSelectedCounter();


    showToast(

        "Find Match module refreshed."

    );

}
/* ===================================================================
   MODULE INITIALIZATION
=================================================================== */

async function initializeModule() {

    try {

        showLoading("requestCardsContainer");

        await loadBloodRequests();

        await loadBloodAvailability();

        await loadDashboardStatistics();

        updateSelectedCounter();

        

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to initialize Find Match module.",
            "error"
        );

    }

}

/* ===================================================================
   MODULE CLEANUP
=================================================================== */

function destroyModule() {

    state.selectedDonors.clear();

    state.selectedRequest = null;

    state.filteredRequests = [];

    state.filteredDonors = [];

    state.matchingDonors = [];

}

/* ===================================================================
   FUTURE NOTIFICATION PLACEHOLDER

   Will later receive:

   - Accepted
   - Declined
   - Busy
   - No Response

=================================================================== */

function handleDonorResponse(response) {

    console.log("Future Notification:", response);

}

/* ===================================================================
   FUTURE WEBSOCKET PLACEHOLDER

   Real-time updates will later arrive here.

=================================================================== */

function initializeRealtimeUpdates() {

    /*
        Future Example

        const socket = new WebSocket(...);

        socket.onmessage = ...

    */

}

/* ===================================================================
   FUTURE EMAIL STATUS PLACEHOLDER
=================================================================== */

function updateEmailStatus(emailId, status) {

    console.log({

        emailId,

        status

    });

}

/* ===================================================================
   FUTURE MATCH STATUS PLACEHOLDER
=================================================================== */

function updateMatchStatus(matchId, status) {

    console.log({

        matchId,

        status

    });

}

/* ===================================================================
   DEBUG
=================================================================== */

function debugModuleState() {

    console.table({

        Requests: state.bloodRequests.length,

        FilteredRequests: state.filteredRequests.length,

        Donors: state.filteredDonors.length,

        SelectedRequest: state.selectedRequest,

        SelectedDonors: state.selectedDonors.size

    });

}

/* ===================================================================
   PUBLIC EXPORTS
=================================================================== */

export {

    loadBloodRequests,

    loadMatchingDonorsFromAPI,

    saveMatchToDatabase,

    sendEmailsToSelectedDonors,

    refreshModule,

    destroyModule,

    debugModuleState

};