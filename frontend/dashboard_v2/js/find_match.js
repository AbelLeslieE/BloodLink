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

const REQUEST_API = "/api/blood-requests";
const MATCH_API = "/api/find-match";
const MATCH_SAVE_API = "/api/matches";
const EMAIL_API = "/api/send-match-email";

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
   DEMO DATA
   -------------------------------------------------------------------
   Temporary data.
   Replace with backend API later.
=================================================================== */

const DEMO_REQUESTS = [

    {
        id: 1,
        patient: "Anand Joseph",
        hospital: "City Medical Centre",
        district: "Ernakulam",
        bloodGroup: "O+",
        units: 2,
        priority: "Critical",
        requiredDate: "Today"
    },

    {
        id: 2,
        patient: "Maria Thomas",
        hospital: "Lakeside Hospital",
        district: "Thrissur",
        bloodGroup: "A-",
        units: 1,
        priority: "High",
        requiredDate: "Tomorrow"
    },

    {
        id: 3,
        patient: "Rahul Menon",
        hospital: "Medical Trust",
        district: "Kochi",
        bloodGroup: "B+",
        units: 3,
        priority: "Medium",
        requiredDate: "Today"
    }

];

const DEMO_DONORS = [

    {
        id: 101,
        name: "John Thomas",
        phone: "+91 9876543210",
        bloodGroup: "O+",
        district: "Ernakulam",
        distance: "2.4 km",
        availability: "Available",
        compatibility: 98,
        lastDonation: "4 months ago"
    },

    {
        id: 102,
        name: "Kevin Joseph",
        phone: "+91 9876543211",
        bloodGroup: "O+",
        district: "Ernakulam",
        distance: "4.1 km",
        availability: "Available",
        compatibility: 94,
        lastDonation: "5 months ago"
    },

    {
        id: 103,
        name: "Alan George",
        phone: "+91 9876543212",
        bloodGroup: "O+",
        district: "Ernakulam",
        distance: "6.9 km",
        availability: "Available",
        compatibility: 91,
        lastDonation: "6 months ago"
    }

];

/* ===================================================================
   INITIALIZE MODULE
=================================================================== */

export function loadFindMatch(container) {

    if (!container) return;

    initializeState();

    container.innerHTML = getFindMatchTemplate();

    bindEvents();

    loadBloodRequests();

    loadBloodAvailability();

    loadDashboardStatistics();

}

/* ===================================================================
   INITIALIZE STATE
=================================================================== */

function initializeState() {

    state.bloodRequests = [...DEMO_REQUESTS];

    state.filteredRequests = [...DEMO_REQUESTS];

    state.matchingDonors = [];

    state.filteredDonors = [];

    state.selectedRequest = null;

    state.selectedDonors.clear();

    state.statistics.pending = state.bloodRequests.length;

    state.statistics.matches = 0;

    state.statistics.emails = 0;

    state.statistics.responses = 0;

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

                    <button
                        id="refreshDashboardBtn"
                        class="primary-btn">

                        Refresh Dashboard

                    </button>

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

                    <!-- Blood Availability -->

                    <div class="glass-card section-card">

                        <div class="section-header">

                            <h2>

                                Blood Availability

                            </h2>

                        </div>

                        <div
                            id="bloodAvailabilityPanel"
                            class="availability-grid">

                        </div>

                    </div>

                    <!-- Quick Actions -->

                    <div class="glass-card section-card">

                        <div class="section-header">

                            <h2>

                                Quick Actions

                            </h2>

                        </div>

                        <div class="quick-action-grid">

                            <button
                                id="findBestMatchBtn"
                                class="secondary-btn">

                                Find Best Match

                            </button>

                            <button
                                id="refreshMatchesBtn"
                                class="secondary-btn">

                                Refresh Matches

                            </button>

                            <button
                                id="exportMatchesBtn"
                                class="secondary-btn">

                                Export

                            </button>

                        </div>

                    </div>

                    <!-- Compatible Donors -->

                    <div class="glass-card section-card">

                        <div class="section-header">

                            <h2>

                                Compatible Donors

                            </h2>

                            <span
                                id="donorCountBadge"
                                class="badge">

                                0

                            </span>

                        </div>

                        <div
                            id="donorCardsContainer"
                            class="donor-list">

                            <div class="empty-state">

                                Select a request to view
                                compatible donors.

                            </div>

                        </div>

                    </div>

                </div>

            </section>

            <!-- =======================================================
                 FOOTER ACTION BAR
            ======================================================== -->

            <section class="bottom-action-bar glass-card">

                <div class="selected-info">

                    Selected Donors :

                    <strong
                        id="selectedDonorCount">

                        0

                    </strong>

                </div>

                <div class="bottom-actions">

                    <button
                        id="saveMatchBtn"
                        class="secondary-btn">

                        Save Match

                    </button>

                    <button
                        id="sendEmailBtn"
                        class="primary-btn">

                        Send Email

                    </button>

                </div>

            </section>

        </div>

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
    const donorBadge = document.getElementById("donorCountBadge");

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

    if (donorBadge)
        donorBadge.textContent = state.filteredDonors.length;

}

/* ===================================================================
   BLOOD AVAILABILITY PANEL
=================================================================== */

function renderBloodAvailability() {

    const container = document.getElementById(
        "bloodAvailabilityPanel"
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

    /* ---------------- Request Selection ---------------- */

    document.addEventListener("click", handleRequestSelection);

    /* ---------------- Donor Selection ---------------- */

    document.addEventListener("click", handleDonorSelection);

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

function refreshDashboard() {

    refreshModule();

    showToast(
        "Dashboard refreshed successfully."
    );

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
   LOAD MATCHING DONORS
=================================================================== */

function loadMatchingDonors(request) {

    state.matchingDonors = DEMO_DONORS.filter(donor => {

        return donor.bloodGroup === request.bloodGroup;

    });

    state.matchingDonors.sort((a, b) => {

        return b.compatibility - a.compatibility;

    });

    state.filteredDonors = [...state.matchingDonors];

    renderKPICards();

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

/* ===================================================================
   SELECTED COUNTER
=================================================================== */

function updateSelectedCounter() {

    const counter =
        document.getElementById(
            "selectedDonorCount"
        );

    if (!counter) return;

    counter.textContent =
        state.selectedDonors.size;

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

    updateSelectedCounter();

    renderKPICards();

    renderRequestCards();

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

        /*
        Future Backend

        const response = await authenticatedFetch(REQUEST_API);

        const data = await response.json();

        state.bloodRequests = data;

        */

        state.bloodRequests = [...DEMO_REQUESTS];

        state.filteredRequests = [...state.bloodRequests];

        state.statistics.pending = state.filteredRequests.length;

        renderDashboard();

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to load blood requests.",
            "error"
        );

    }

}

/* ===================================================================
   LOAD MATCHING DONORS
=================================================================== */

async function loadMatchingDonorsFromAPI(requestId) {

    try {

        /*
        Future Backend

        const response = await authenticatedFetch(

            `${MATCH_API}/${requestId}`

        );

        const donors = await response.json();

        state.matchingDonors = donors;

        */

        state.matchingDonors = DEMO_DONORS.filter(

            donor => donor.bloodGroup === state.selectedRequest.bloodGroup

        );

        state.matchingDonors.sort(

            (a, b) => b.compatibility - a.compatibility

        );

        state.filteredDonors = [...state.matchingDonors];

        renderDonorCards();

        renderKPICards();

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to load compatible donors.",
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

            requestId: state.selectedRequest.id,

            donorIds: [...state.selectedDonors]

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

async function sendEmailsToSelectedDonors() {

    try {

        if (state.selectedDonors.size === 0)
            return;

        const payload = {

            request: state.selectedRequest,

            donorIds: [...state.selectedDonors]

        };

        /*
        Future Backend

        await authenticatedFetch(

            EMAIL_API,

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify(payload)

            }

        );

        */

        console.log(payload);

        state.statistics.emails += state.selectedDonors.size;

        renderKPICards();

        showToast(
            "Email notifications sent."
        );

    } catch (error) {

        console.error(error);

        showToast(
            "Unable to send emails.",
            "error"
        );

    }

}

/* ===================================================================
   LOAD DASHBOARD STATISTICS
=================================================================== */

async function loadDashboardStatistics() {

    try {

        /*
        Future Backend

        const response =
            await authenticatedFetch("/api/dashboard/find-match");

        const statistics =
            await response.json();

        state.statistics = statistics;

        */

        state.statistics.pending =
            state.filteredRequests.length;

        state.statistics.matches =
            state.filteredDonors.length;

        renderKPICards();

    } catch (error) {

        console.error(error);

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
   CALCULATE COMPATIBILITY
   (Temporary Frontend Version)

   Backend will eventually calculate this score.
=================================================================== */

function calculateCompatibility(donor, request) {

    let score = 0;

    if (donor.bloodGroup === request.bloodGroup)
        score += 50;

    if (donor.availability === "Available")
        score += 20;

    score += Math.max(

        0,

        20 - parseFloat(donor.distance)

    );

    score += 10;

    return Math.min(

        100,

        Math.round(score)

    );

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

}

/* ===================================================================
   REFRESH MODULE
=================================================================== */

function refreshModule() {

    clearSearchFields();

    resetSelections();

    initializeState();

    renderDashboard();

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

        renderDashboard();

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