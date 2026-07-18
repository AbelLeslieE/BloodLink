// ==========================================================
// BLOODLINK - BLOOD REQUESTS MODULE
// File: blood-requests.js
//
// Responsibilities:
// - Render Blood Requests management page
// - Switch between Dashboard and Blood Requests views
// - Handle Blood Request page interactions
//
// Backend integration will be added later.
// ==========================================================


// ==========================================================
// 1. DOM REFERENCES
// ==========================================================

const dashboardView =
    document.getElementById("dashboardView");

const moduleView =
    document.getElementById("moduleView");


// ==========================================================
// 2. BLOOD REQUEST DATA
//
// Stores blood requests loaded from the FastAPI backend.
// ==========================================================

let bloodRequests = [];
// ==========================================================
// LOAD BLOOD REQUESTS FROM BACKEND
// ==========================================================

async function loadBloodRequests() {

    // ======================================================
    // 1. GET AUTHENTICATION TOKEN
    // ======================================================

    const accessToken =
        localStorage.getItem("access_token") ||
        localStorage.getItem("accessToken") ||
        localStorage.getItem("token");


    if (!accessToken) {

        throw new Error(
            "Authentication token was not found."
        );

    }


    // ======================================================
    // 2. REQUEST BLOOD REQUESTS FROM FASTAPI
    // ======================================================

    const response =
        await fetch(
            "/api/blood-requests",
            {
                method: "GET",

                headers: {

                    "Authorization":
                        `Bearer ${accessToken}`

                }
            }
        );


    // ======================================================
    // 3. HANDLE API ERROR
    // ======================================================

    if (!response.ok) {

        let errorData = null;

        try {

            errorData =
                await response.json();

        }

        catch {

            errorData = null;

        }


        console.error(
            "Pranadan: Failed to load blood requests.",
            response.status,
            errorData
        );


        throw new Error(
            "Unable to load blood requests."
        );

    }


    // ======================================================
    // 4. STORE REAL DATABASE RECORDS
    // ======================================================

    const data =
        await response.json();


    bloodRequests =
        Array.isArray(data)
            ? data
            : [];


    console.log(
        "Pranadan: Blood requests loaded:",
        bloodRequests
    );


    return bloodRequests;

}
// ==========================================================
// 3. SHOW MODULE VIEW
// ==========================================================

function showModuleView() {

    if (!dashboardView || !moduleView) {
        return;
    }

    dashboardView.hidden = true;

    moduleView.hidden = false;

}


// ==========================================================
// 4. SHOW DASHBOARD VIEW
// ==========================================================

function showDashboardView() {

    if (!dashboardView || !moduleView) {
        return;
    }

    moduleView.hidden = true;

    moduleView.innerHTML = "";

    dashboardView.hidden = false;

}


// ==========================================================
// 5. STATUS CLASS
// ==========================================================

function getStatusClass(status) {

    const normalizedStatus =
        status
            .toLowerCase()
            .replaceAll(" ", "-");

    return `status-${normalizedStatus}`;

}


// ==========================================================
// 6. URGENCY CLASS
// ==========================================================

function getUrgencyClass(urgency) {

    return `urgency-${urgency.toLowerCase()}`;

}


// ==========================================================
// 7. BUILD REQUEST ROWS
// ==========================================================

// ==========================================================
// 7. BUILD REQUEST ROWS
// ==========================================================

function buildRequestRows(requests = bloodRequests) {

    // ======================================================
    // EMPTY STATE
    // ======================================================

    if (!requests.length) {

        return `

            <tr>

                <td
                    colspan="8"
                    class="request-empty-state"
                >

                    No blood requests found.

                </td>

            </tr>

        `;

    }


    // ======================================================
    // BUILD DATABASE REQUEST ROWS
    // ======================================================

    return requests
        .map((request) => {

            // ----------------------------------------------
            // Display Request ID
            // Example:
            // Database ID 1 -> BR-0001
            // ----------------------------------------------

            const displayRequestId =
                `BR-${String(request.id).padStart(4, "0")}`;


            // ----------------------------------------------
            // Format Required Date
            // ----------------------------------------------

            let formattedRequiredDate =
                "Not specified";


            if (request.required_date) {

                const [year, month, day] =
                    request.required_date
                        .split("-")
                        .map(Number);


                const requiredDate =
                    new Date(
                        year,
                        month - 1,
                        day
                    );


                formattedRequiredDate =
                    requiredDate.toLocaleDateString(
                        "en-GB",
                        {
                            day: "2-digit",
                            month: "short",
                            year: "numeric"
                        }
                    );

            }


            // ----------------------------------------------
            // Build Row
            // ----------------------------------------------

            return `

                <tr>

                    <td>

                        <strong class="request-id">
                            ${displayRequestId}
                        </strong>

                    </td>


                    <td>

                        <div class="request-patient">

                            <strong>
                                ${request.patient_name}
                            </strong>

                            <span>
                                Required ${formattedRequiredDate}
                            </span>

                        </div>

                    </td>


                    <td>

                        <span class="blood-group-badge">

                            ${request.blood_group}

                        </span>

                    </td>


                    <td>

                        ${request.units_required}

                    </td>


                    <td>

                        ${request.hospital_name}

                    </td>


                    <td>

                        <span
                            class="
                                urgency-badge
                                ${getUrgencyClass(request.priority)}
                            "
                        >

                            ${request.priority}

                        </span>

                    </td>


                    <td>

                        <span
                            class="
                                status-badge
                                ${getStatusClass(request.status)}
                            "
                        >

                            ${request.status}

                        </span>

                    </td>


                    <td>

                        <button
                            type="button"
                            class="table-action-button"
                            data-request-id="${request.id}"
                            aria-label="View ${displayRequestId}"
                        >

                            <i data-lucide="eye"></i>

                        </button>

                    </td>

                </tr>

            `;

        })
        .join("");

}
// ==========================================================
// OPEN BLOOD REQUEST DETAILS
// ==========================================================

function openBloodRequestDetails(requestId) {

    // Convert the HTML data attribute back to a number.

    const numericRequestId =
        Number(requestId);


    // Find the selected request from the records
    // already loaded from the backend.

    const selectedRequest =
        bloodRequests.find(
            (request) =>
                request.id === numericRequestId
        );


    if (!selectedRequest) {

        console.error(
            "BloodLink: Blood request was not found:",
            numericRequestId
        );

        alert(
            "Unable to find this blood request."
        );

        return;

    }


    renderBloodRequestDetails(
        selectedRequest
    );

}
// ==========================================================
// RENDER BLOOD REQUEST DETAILS
// ==========================================================

function renderBloodRequestDetails(request) {

    if (!moduleView) {

        console.error(
            "BloodLink: #moduleView was not found."
        );

        return;

    }


    showModuleView();


    // ======================================================
    // FORMAT REQUEST ID
    // ======================================================

    const displayRequestId =
        `BR-${String(request.id).padStart(4, "0")}`;


    // ======================================================
    // FORMAT REQUIRED DATE
    // ======================================================

    let formattedRequiredDate =
        "Not specified";


    if (request.required_date) {

        const [year, month, day] =
            request.required_date
                .split("-")
                .map(Number);


        formattedRequiredDate =
            new Date(
                year,
                month - 1,
                day
            ).toLocaleDateString(
                "en-GB",
                {
                    day: "2-digit",
                    month: "short",
                    year: "numeric"
                }
            );

    }


    // ======================================================
    // FORMAT CREATED DATE
    // ======================================================

    const formattedCreatedDate =
        request.created_at
            ? new Date(
                request.created_at
            ).toLocaleString(
                "en-GB",
                {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit"
                }
            )
            : "Not available";


    // ======================================================
    // RENDER DETAILS
    // ======================================================

    moduleView.innerHTML = `

        <div class="blood-requests-module">

            <!-- ==========================================
                 HEADER
            =========================================== -->

            <header class="module-header">

                <div class="module-heading">

                    <span class="module-eyebrow">
                        Request Management
                    </span>

                    <h1>
                        ${displayRequestId}
                    </h1>

                    <p>
                        Complete information for this blood request.
                    </p>

                </div>


                <div class="module-header-actions">

                    <button
                        type="button"
                        class="secondary-btn"
                        id="backFromRequestDetailsButton"
                    >

                        <i data-lucide="arrow-left"></i>

                        <span>
                            Back to Requests
                        </span>

                    </button>

                </div>

            </header>


            <!-- ==========================================
                 STATUS OVERVIEW
            =========================================== -->

            <section class="request-details-overview">

                <div>

                    <span class="blood-group-badge">

                        ${request.blood_group}

                    </span>

                    <h2>
                        ${request.patient_name}
                    </h2>

                    <p>
                        ${request.case_details}
                    </p>

                </div>


                <div class="request-details-badges">

                    <span
                        class="
                            urgency-badge
                            ${getUrgencyClass(request.priority)}
                        "
                    >

                        ${request.priority}

                    </span>


                    <span
                        class="
                            status-badge
                            ${getStatusClass(request.status)}
                        "
                    >

                        ${request.status}

                    </span>

                </div>

            </section>


            <!-- ==========================================
                 DETAILS GRID
            =========================================== -->

            <section class="request-details-grid">


                <!-- BLOOD REQUIREMENT -->

                <article class="request-detail-card">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="droplets"></i>

                        </div>

                        <div>

                            <h2>
                                Blood Requirement
                            </h2>

                            <p>
                                Required blood information
                            </p>

                        </div>

                    </div>


                    <div class="request-detail-list">

                        <div>

                            <span>
                                Blood Group
                            </span>

                            <strong>
                                ${request.blood_group}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Number of Units
                            </span>

                            <strong>
                                ${request.units_required}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Required Date
                            </span>

                            <strong>
                                ${formattedRequiredDate}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Urgency
                            </span>

                            <strong>
                                ${request.priority}
                            </strong>

                        </div>

                    </div>

                </article>


                <!-- HOSPITAL -->

                <article class="request-detail-card">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="hospital"></i>

                        </div>

                        <div>

                            <h2>
                                Hospital Details
                            </h2>

                            <p>
                                Destination for the blood requirement
                            </p>

                        </div>

                    </div>


                    <div class="request-detail-list">

                        <div>

                            <span>
                                Hospital
                            </span>

                            <strong>
                                ${request.hospital_name}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Place
                            </span>

                            <strong>
                                ${request.hospital_location}
                            </strong>

                        </div>

                    </div>

                </article>


                <!-- CONTACT -->

                <article class="request-detail-card">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="phone"></i>

                        </div>

                        <div>

                            <h2>
                                Bystander & Contact
                            </h2>

                            <p>
                                Primary contact for this request
                            </p>

                        </div>

                    </div>


                    <div class="request-detail-list">

                        <div>

                            <span>
                                Bystander
                            </span>

                            <strong>
                                ${request.contact_person}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Contact Number
                            </span>

                            <strong>
                                ${request.contact_phone}
                            </strong>

                        </div>

                    </div>

                </article>


                <!-- REQUEST INFORMATION -->

                <article class="request-detail-card">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="clipboard-list"></i>

                        </div>

                        <div>

                            <h2>
                                Request Information
                            </h2>

                            <p>
                                BloodLink record information
                            </p>

                        </div>

                    </div>


                    <div class="request-detail-list">

                        <div>

                            <span>
                                Request ID
                            </span>

                            <strong>
                                ${displayRequestId}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Status
                            </span>

                            <strong>
                                ${request.status}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Created
                            </span>

                            <strong>
                                ${formattedCreatedDate}
                            </strong>

                        </div>

                    </div>

                </article>

            </section>


            <!-- ==========================================
                 ADDITIONAL NOTES
            =========================================== -->

            <section class="request-detail-card request-notes-card">

                <div class="request-form-section-header">

                    <div class="request-form-section-icon">

                        <i data-lucide="notebook-text"></i>

                    </div>

                    <div>

                        <h2>
                            Additional Notes
                        </h2>

                        <p>
                            Other information recorded with the request
                        </p>

                    </div>

                </div>


                <p class="request-notes-content">

                    ${
                        request.additional_notes ||
                        "No additional notes were provided."
                    }

                </p>

            </section>
                        <!-- ==========================================
                            REQUEST STATUS ACTIONS
                        =========================================== -->

                        <section class="request-status-actions-card">

                            <div class="request-status-actions-info">

                                <span>
                                    Request Status
                                </span>

                                <h2>
                                    ${request.status}
                                </h2>

                                <p>
                                    Update this request as it progresses
                                    through the BloodLink workflow.
                                </p>

                            </div>


                            <div class="request-status-actions">

                                ${buildRequestStatusActions(request)}

                            </div>

                        </section>

        </div>

    `;


    // ======================================================
    // RECREATE ICONS
    // ======================================================

    if (window.lucide) {

        window.lucide.createIcons();

    }


    // ======================================================
    // BACK BUTTON
    // ======================================================

    document
        .getElementById(
            "backFromRequestDetailsButton"
        )
        ?.addEventListener(
            "click",
            () => {

                renderBloodRequests();

            }
        );
        // ======================================================
        // STATUS ACTION BUTTONS
        // ======================================================

        document
            .querySelectorAll(
                ".request-status-action[data-request-status]"
            )
            .forEach(
                (button) => {

                    button.addEventListener(
                        "click",
                        async () => {

                            // ----------------------------------
                            // Get requested new status
                            // ----------------------------------

                            const newStatus =
                                button.dataset.requestStatus;


                            if (!newStatus) {
                                return;
                            }


                            // ----------------------------------
                            // Confirm cancellation
                            // ----------------------------------

                            if (newStatus === "Cancelled") {

                                const confirmed =
                                    window.confirm(
                                        "Are you sure you want to cancel this blood request?"
                                    );


                                if (!confirmed) {
                                    return;
                                }

                            }
                            // ----------------------------------
                            // Confirm reopening
                            // ----------------------------------

                            if (
                                newStatus === "Pending" &&
                                (
                                    request.status === "Fulfilled" ||
                                    request.status === "Cancelled"
                                )
                            ) {

                                const confirmed =
                                    window.confirm(
                                        "Are you sure you want to reopen this blood request?"
                                    );

                                if (!confirmed) {
                                    return;
                                }

                            }


                            // ----------------------------------
                            // Prevent repeated clicks
                            // ----------------------------------

                            button.disabled = true;


                            try {

                                await updateBloodRequestStatus(
                                    request.id,
                                    newStatus
                                );

                            }

                            finally {

                                /*
                                    The details page is normally
                                    re-rendered after a successful
                                    update.

                                    This restores the button if
                                    the update fails.
                                */

                                if (button.isConnected) {

                                    button.disabled = false;

                                }

                            }

                        }
                    );

                }
        );    

}
// ==========================================================
// BUILD REQUEST STATUS ACTIONS
// ==========================================================

function buildRequestStatusActions(request) {

    switch (request.status) {

        // ==================================================
        // PENDING
        // ==================================================

        case "Pending":

            return `

                <button
                    type="button"
                    class="secondary-btn request-status-action"
                    data-request-status="Cancelled"
                >

                    <i data-lucide="x"></i>

                    <span>
                        Cancel Request
                    </span>

                </button>


                <button
                    type="button"
                    class="primary-btn request-status-action"
                    data-request-status="In Progress"
                >

                    <i data-lucide="play"></i>

                    <span>
                        Start Processing
                    </span>

                </button>

            `;


        // ==================================================
        // IN PROGRESS
        // ==================================================

        case "In Progress":

            return `

                <button
                    type="button"
                    class="secondary-btn request-status-action"
                    data-request-status="Cancelled"
                >

                    <i data-lucide="x"></i>

                    <span>
                        Cancel Request
                    </span>

                </button>


                <button
                    type="button"
                    class="primary-btn request-status-action"
                    data-request-status="Fulfilled"
                >

                    <i data-lucide="check"></i>

                    <span>
                        Mark Fulfilled
                    </span>

                </button>

            `;


        // ==================================================
        // FULFILLED
        // ==================================================

        case "Fulfilled":

            return `

                <div class="request-status-complete">

                    <i data-lucide="circle-check"></i>

                    <span>
                        This blood request has been fulfilled.
                    </span>

                </div>

                <button
                    type="button"
                    class="secondary-btn request-status-action"
                    data-request-status="Pending"
                >

                    <i data-lucide="rotate-ccw"></i>

                    <span>
                        Reopen Request
                    </span>

                </button>

            `;


        // ==================================================
        // CANCELLED
        // ==================================================

        case "Cancelled":

            return `

                <div class="request-status-complete">

                    <i data-lucide="circle-x"></i>

                    <span>
                        This blood request has been cancelled.
                    </span>

                </div>

                <button
                    type="button"
                    class="secondary-btn request-status-action"
                    data-request-status="Pending"
                >

                    <i data-lucide="rotate-ccw"></i>

                    <span>
                        Reopen Request
                    </span>

                </button>

            `;


        default:

            return "";

    }

}
// ==========================================================
// UPDATE BLOOD REQUEST STATUS
// ==========================================================

async function updateBloodRequestStatus(
    requestId,
    newStatus
) {

    // ======================================================
    // 1. GET AUTHENTICATION TOKEN
    // ======================================================

    const accessToken =
        localStorage.getItem("access_token") ||
        localStorage.getItem("accessToken") ||
        localStorage.getItem("token");


    if (!accessToken) {

        alert(
            "Your login session could not be found. Please log in again."
        );

        return;

    }


    try {

        // ==================================================
        // 2. SEND STATUS UPDATE TO FASTAPI
        // ==================================================

        const response =
            await fetch(
                `/api/blood-requests/${requestId}/status`,
                {
                    method: "PATCH",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${accessToken}`

                    },

                    body:
                        JSON.stringify(
                            {
                                status: newStatus
                            }
                        )
                }
            );


        const responseData =
            await response.json();


        // ==================================================
        // 3. HANDLE API ERROR
        // ==================================================

        if (!response.ok) {

            console.error(
                "BloodLink: Status update failed.",
                response.status,
                responseData
            );

            throw new Error(
                responseData.detail ||
                "Unable to update blood request status."
            );

        }


        // ==================================================
        // 4. UPDATE LOCAL REQUEST DATA
        // ==================================================

        const requestIndex =
            bloodRequests.findIndex(
                (request) =>
                    request.id === requestId
            );


        if (requestIndex !== -1) {

            bloodRequests[requestIndex] =
                responseData;

        }


        // ==================================================
        // 5. RE-RENDER REQUEST DETAILS
        // ==================================================

        renderBloodRequestDetails(
            responseData
        );

    }

    catch (error) {

        console.error(
            "BloodLink: Error updating request status:",
            error
        );

        alert(
            error.message ||
            "Something went wrong while updating the request."
        );

    }

}
// ==========================================================
// 8. RENDER BLOOD REQUESTS
// ==========================================================

async function renderBloodRequests() {
    // ======================================================
    // LOAD REAL BLOOD REQUESTS FROM DATABASE
    // ======================================================

    try {

        await loadBloodRequests();

    }

    catch (error) {

        console.error(
            "BloodLink: Could not load blood requests.",
            error
        );

    }

    if (!moduleView) {

        console.error(
            "BloodLink: #moduleView was not found."
        );

        return;

    }

    showModuleView();

    moduleView.innerHTML = `

        <div class="blood-requests-module">


            <!-- ==============================================
                 PAGE HEADER
            =============================================== -->

            <header class="module-header">

                <div class="module-heading">

                    <span class="module-eyebrow">
                        Request Management
                    </span>

                    <h1>
                        Blood Requests
                    </h1>

                    <p>
                        Manage, track and coordinate blood requirements
                        across hospitals and patients.
                    </p>

                </div>


                <div class="module-header-actions">

                    <button
                        type="button"
                        class="primary-btn"
                        id="createBloodRequestButton"
                    >

                        <i data-lucide="plus"></i>

                        <span>
                            New Blood Request
                        </span>

                    </button>

                </div>

            </header>


            <!-- ==============================================
                 SUMMARY CARDS
            =============================================== -->

            <section
                class="request-summary-grid"
                aria-label="Blood request statistics"
            >

                <article class="request-summary-card">

                    <div class="request-summary-icon">

                        <i data-lucide="clipboard-list"></i>

                    </div>

                    <div>

                        <span>
                            Total Requests
                        </span>

                        <strong>
                            128
                        </strong>

                        <small>
                            All recorded requests
                        </small>

                    </div>

                </article>


                <article class="request-summary-card">

                    <div class="request-summary-icon">

                        <i data-lucide="siren"></i>

                    </div>

                    <div>

                        <span>
                            Emergency
                        </span>

                        <strong>
                            8
                        </strong>

                        <small>
                            Requires immediate action
                        </small>

                    </div>

                </article>


                <article class="request-summary-card">

                    <div class="request-summary-icon">

                        <i data-lucide="clock-3"></i>

                    </div>

                    <div>

                        <span>
                            Pending
                        </span>

                        <strong>
                            24
                        </strong>

                        <small>
                            Awaiting fulfilment
                        </small>

                    </div>

                </article>


                <article class="request-summary-card">

                    <div class="request-summary-icon">

                        <i data-lucide="circle-check-big"></i>

                    </div>

                    <div>

                        <span>
                            Fulfilled
                        </span>

                        <strong>
                            96
                        </strong>

                        <small>
                            Successfully completed
                        </small>

                    </div>

                </article>

            </section>


            <!-- ==============================================
                 REQUEST MANAGEMENT PANEL
            =============================================== -->

            <section class="request-management-card">


                <!-- Toolbar -->

                <div class="request-toolbar">

                    <div class="request-search">

                        <i data-lucide="search"></i>

                        <input
                            type="search"
                            id="requestSearch"
                            placeholder="Search patient, hospital or request ID..."
                            aria-label="Search blood requests"
                        >

                    </div>


                    <div class="request-filters">

                        <select
                            id="bloodGroupFilter"
                            aria-label="Filter by blood group"
                        >

                            <option value="">
                                All Blood Groups
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


                        <select
                            id="urgencyFilter"
                            aria-label="Filter by urgency"
                        >

                            <option value="">
                                All Urgency
                            </option>

                            <option>
                                Emergency
                            </option>

                            <option>
                                Urgent
                            </option>

                            <option>
                                Normal
                            </option>

                        </select>


                        <select
                            id="statusFilter"
                            aria-label="Filter by status"
                        >

                            <option value="">
                                All Statuses
                            </option>

                            <option>
                                Pending
                            </option>

                            <option>
                                In Progress
                            </option>

                            <option>
                                Fulfilled
                            </option>

                            <option>
                                Cancelled
                            </option>

                        </select>

                    </div>

                </div>


                <!-- Table -->

                <div class="request-table-wrapper">

                    <table class="request-table">

                        <thead>

                            <tr>

                                <th>
                                    Request ID
                                </th>

                                <th>
                                    Patient
                                </th>

                                <th>
                                    Blood
                                </th>

                                <th>
                                    Units
                                </th>

                                <th>
                                    Hospital
                                </th>

                                <th>
                                    Urgency
                                </th>

                                <th>
                                    Status
                                </th>

                                <th>
                                    Action
                                </th>

                            </tr>

                        </thead>


                        <tbody id="bloodRequestTableBody">

                            ${buildRequestRows()}

                        </tbody>

                    </table>

                </div>


                <!-- Footer -->

                <div class="request-table-footer">

                    <p>
                        Showing
                        <strong>1–4</strong>
                        of
                        <strong>128</strong>
                        requests
                    </p>


                    <div class="pagination">

                        <button
                            type="button"
                            disabled
                            aria-label="Previous page"
                        >

                            <i data-lucide="chevron-left"></i>

                        </button>


                        <button
                            type="button"
                            class="active"
                        >
                            1
                        </button>


                        <button
                            type="button"
                        >
                            2
                        </button>


                        <button
                            type="button"
                        >
                            3
                        </button>


                        <button
                            type="button"
                            aria-label="Next page"
                        >

                            <i data-lucide="chevron-right"></i>

                        </button>

                    </div>

                </div>

            </section>
                        
        </div>

    `;


    // Re-render Lucide icons after dynamic HTML insertion.

    if (window.lucide) {

        window.lucide.createIcons();

    }


    // ======================================================
    // CONNECT NEW BLOOD REQUEST BUTTON
    // ======================================================

    const createBloodRequestButton =
        document.getElementById(
            "createBloodRequestButton"
        );

    createBloodRequestButton?.addEventListener(
        "click",
        () => {

            renderNewBloodRequestForm();

        }
    );
        // ======================================================
        // CONNECT REQUEST DETAILS BUTTONS
        // ======================================================

        document
            .querySelectorAll(
                ".table-action-button[data-request-id]"
            )
            .forEach(
                (button) => {

                    button.addEventListener(
                        "click",
                        () => {

                            openBloodRequestDetails(
                                button.dataset.requestId
                            );

                        }
                    );

                }
            );

    }


// ==========================================================
// 9. NAVIGATION EVENT
// ==========================================================

window.addEventListener(
    "bloodlink:navigate",
    (event) => {

        const page =
            event.detail?.page;

        if (page === "dashboard") {

            showDashboardView();

            return;

        }

        if (page === "bloodRequests") {

            renderBloodRequests();

        }

    }
);


// ==========================================================
// 10. EXPORTS
// ==========================================================

export {

    renderBloodRequests,

    showDashboardView

};
// ==========================================================
// 9. RENDER NEW BLOOD REQUEST FORM
// ==========================================================

// ==========================================================
// RENDER NEW BLOOD REQUEST FORM
// ==========================================================

function renderNewBloodRequestForm() {

    if (!moduleView) {

        console.error(
            "BloodLink: #moduleView was not found."
        );

        return;
    }

    showModuleView();

    moduleView.innerHTML = `

        <div class="blood-requests-module">

            <!-- ==========================================
                 FORM HEADER
            =========================================== -->

            <header class="module-header">

                <div class="module-heading">

                    <span class="module-eyebrow">
                        Request Management
                    </span>

                    <h1>
                        New Blood Request
                    </h1>

                    <p>
                        Record the blood requirement information
                        received from the requester or bystander.
                    </p>

                </div>

                <div class="module-header-actions">

                    <button
                        type="button"
                        class="secondary-btn"
                        id="backToBloodRequestsButton"
                    >

                        <i data-lucide="arrow-left"></i>

                        <span>
                            Back to Requests
                        </span>

                    </button>

                </div>

            </header>


            <!-- ==========================================
                 BLOOD REQUEST FORM
            =========================================== -->

            <form
                class="blood-request-form"
                id="bloodRequestForm"
            >


                <!-- ======================================
                     PERSON / CASE DETAILS
                ======================================= -->

                <section class="request-form-section">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="user-round"></i>

                        </div>

                        <div>

                            <h2>
                                Person & Case Details
                            </h2>

                            <p>
                                Enter the name of the person requiring
                                blood and the case information provided.
                            </p>

                        </div>

                    </div>


                    <div class="request-form-grid">

                        <div class="form-field">

                            <label for="patientName">

                                Name of Person

                                <span>*</span>

                            </label>

                            <input
                                type="text"
                                id="patientName"
                                name="patientName"
                                maxlength="200"
                                placeholder="Enter name of person"
                                required
                            >

                        </div>


                        <div class="form-field">

                            <label for="caseDetails">

                                Case

                                <span>*</span>

                            </label>

                            <input
                                type="text"
                                id="caseDetails"
                                name="caseDetails"
                                maxlength="255"
                                placeholder="Example: Surgery, accident, treatment"
                                required
                            >

                        </div>

                    </div>

                </section>


                <!-- ======================================
                     BLOOD REQUIREMENT
                ======================================= -->

                <section class="request-form-section">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="droplets"></i>

                        </div>

                        <div>

                            <h2>
                                Blood Requirement
                            </h2>

                            <p>
                                Specify the required blood group,
                                units, date and urgency.
                            </p>

                        </div>

                    </div>


                    <div class="request-form-grid">

                        <div class="form-field">

                            <label for="requiredBloodGroup">

                                Blood Group

                                <span>*</span>

                            </label>

                            <select
                                id="requiredBloodGroup"
                                name="requiredBloodGroup"
                                required
                            >

                                <option value="">
                                    Select blood group
                                </option>

                                <option value="A+">A+</option>
                                <option value="A-">A-</option>

                                <option value="B+">B+</option>
                                <option value="B-">B-</option>

                                <option value="AB+">AB+</option>
                                <option value="AB-">AB-</option>

                                <option value="O+">O+</option>
                                <option value="O-">O-</option>

                            </select>

                        </div>


                        <div class="form-field">

                            <label for="requiredUnits">

                                Number of Units

                                <span>*</span>

                            </label>

                            <input
                                type="number"
                                id="requiredUnits"
                                name="requiredUnits"
                                min="1"
                                max="20"
                                placeholder="Enter number of units"
                                required
                            >

                        </div>


                        <div class="form-field">

                            <label for="requiredDate">

                                Required Date

                                <span>*</span>

                            </label>

                            <input
                                type="date"
                                id="requiredDate"
                                name="requiredDate"
                                required
                            >

                        </div>


                        <div class="form-field">

                            <label for="requestUrgency">

                                Urgency

                                <span>*</span>

                            </label>

                            <select
                                id="requestUrgency"
                                name="requestUrgency"
                                required
                            >

                                <option value="">
                                    Select urgency
                                </option>

                                <option value="Normal">
                                    Normal
                                </option>

                                <option value="Urgent">
                                    Urgent
                                </option>

                                <option value="Emergency">
                                    Emergency
                                </option>

                            </select>

                        </div>

                    </div>

                </section>


                <!-- ======================================
                     HOSPITAL DETAILS
                ======================================= -->

                <section class="request-form-section">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="hospital"></i>

                        </div>

                        <div>

                            <h2>
                                Hospital Details
                            </h2>

                            <p>
                                Enter the hospital and place where
                                the blood is required.
                            </p>

                        </div>

                    </div>


                    <div class="request-form-grid">

                        <div class="form-field">

                            <label for="hospitalName">

                                Hospital

                                <span>*</span>

                            </label>

                            <input
                                type="text"
                                id="hospitalName"
                                name="hospitalName"
                                maxlength="200"
                                placeholder="Enter hospital name"
                                required
                            >

                        </div>


                        <div class="form-field">

                            <label for="hospitalLocation">

                                Place

                                <span>*</span>

                            </label>

                            <input
                                type="text"
                                id="hospitalLocation"
                                name="hospitalLocation"
                                maxlength="255"
                                placeholder="Enter place or location"
                                required
                            >

                        </div>

                    </div>

                </section>


                <!-- ======================================
                     BYSTANDER / CONTACT DETAILS
                ======================================= -->

                <section class="request-form-section">

                    <div class="request-form-section-header">

                        <div class="request-form-section-icon">

                            <i data-lucide="phone"></i>

                        </div>

                        <div>

                            <h2>
                                Bystander & Contact
                            </h2>

                            <p>
                                Enter the person who can be contacted
                                regarding this blood requirement.
                            </p>

                        </div>

                    </div>


                    <div class="request-form-grid">

                        <div class="form-field">

                            <label for="contactPerson">

                                Bystander

                                <span>*</span>

                            </label>

                            <input
                                type="text"
                                id="contactPerson"
                                name="contactPerson"
                                maxlength="200"
                                placeholder="Enter bystander name"
                                required
                            >

                        </div>


                        <div class="form-field">

                            <label for="contactPhone">

                                Contact Number

                                <span>*</span>

                            </label>

                            <input
                                type="tel"
                                id="contactPhone"
                                name="contactPhone"
                                maxlength="30"
                                placeholder="Enter contact number"
                                required
                            >

                        </div>


                        <div class="form-field form-field-full">

                            <label for="requestNotes">

                                Additional Notes

                            </label>

                            <textarea
                                id="requestNotes"
                                name="requestNotes"
                                rows="5"
                                placeholder="Add any other information received with the blood request..."
                            ></textarea>

                        </div>

                    </div>

                </section>


                <!-- ======================================
                     FORM ACTIONS
                ======================================= -->

                <div class="request-form-actions">

                    <button
                        type="button"
                        class="secondary-btn"
                        id="cancelBloodRequestButton"
                    >

                        Cancel

                    </button>


                    <button
                        type="submit"
                        class="primary-btn"
                    >

                        <i data-lucide="plus"></i>

                        <span>
                            Create Blood Request
                        </span>

                    </button>

                </div>

            </form>

        </div>

    `;


    // Re-create Lucide icons after inserting the form.

    if (window.lucide) {

        window.lucide.createIcons();

    }


    // Connect form controls.

    initializeBloodRequestForm();

}
// ==========================================================
// 10. INITIALIZE BLOOD REQUEST FORM
// ==========================================================

// ==========================================================
// INITIALIZE BLOOD REQUEST FORM
// ==========================================================

function initializeBloodRequestForm() {

    // ======================================================
    // 1. DOM REFERENCES
    // ======================================================

    const form =
        document.getElementById("bloodRequestForm");

    const backButton =
        document.getElementById("backToBloodRequestsButton");

    const cancelButton =
        document.getElementById("cancelBloodRequestButton");


    if (!form) {

        console.error(
            "BloodLink: #bloodRequestForm was not found."
        );

        return;

    }


    // ======================================================
    // 2. BACK BUTTON
    // ======================================================

    backButton?.addEventListener(
        "click",
        () => {

            renderBloodRequests();

        }
    );


    // ======================================================
    // 3. CANCEL BUTTON
    // ======================================================

    cancelButton?.addEventListener(
        "click",
        () => {

            renderBloodRequests();

        }
    );


    // ======================================================
    // 4. FORM SUBMISSION
    // ======================================================

    form.addEventListener(
        "submit",
        async (event) => {

            event.preventDefault();


            // --------------------------------------------------
            // Validate HTML form fields
            // --------------------------------------------------

            if (!form.checkValidity()) {

                form.reportValidity();

                return;

            }


            // --------------------------------------------------
            // Get submit button
            // --------------------------------------------------

            const submitButton =
                form.querySelector(
                    'button[type="submit"]'
                );


            // --------------------------------------------------
            // Build API request payload
            // --------------------------------------------------

            const requestData = {

                patient_name:
                    document
                        .getElementById("patientName")
                        .value
                        .trim(),

                case_details:
                    document
                        .getElementById("caseDetails")
                        .value
                        .trim(),

                blood_group:
                    document
                        .getElementById("requiredBloodGroup")
                        .value,

                units_required:
                    Number(
                        document
                            .getElementById("requiredUnits")
                            .value
                    ),

                required_date:
                    document
                        .getElementById("requiredDate")
                        .value,

                priority:
                    document
                        .getElementById("requestUrgency")
                        .value,

                hospital_name:
                    document
                        .getElementById("hospitalName")
                        .value
                        .trim(),

                hospital_location:
                    document
                        .getElementById("hospitalLocation")
                        .value
                        .trim(),

                contact_person:
                    document
                        .getElementById("contactPerson")
                        .value
                        .trim(),

                contact_phone:
                    document
                        .getElementById("contactPhone")
                        .value
                        .trim(),

                additional_notes:
                    document
                        .getElementById("requestNotes")
                        .value
                        .trim() || null,

                status: "Pending"

            };


            // ==================================================
            // 5. GET AUTHENTICATION TOKEN
            // ==================================================

            /*
                BloodLink login stores a JWT access token.

                Check the common token keys used by the frontend.
            */

            const accessToken =
                localStorage.getItem("access_token") ||
                localStorage.getItem("accessToken") ||
                localStorage.getItem("token");


            if (!accessToken) {

                console.error(
                    "BloodLink: Authentication token was not found."
                );

                alert(
                    "Your login session could not be found. Please log in again."
                );

                return;

            }


            // ==================================================
            // 6. PREVENT DOUBLE SUBMISSION
            // ==================================================

            if (submitButton) {

                submitButton.disabled = true;

            }


            try {

                // ==============================================
                // 7. SEND REQUEST TO FASTAPI
                // ==============================================

                const response =
                    await fetch(
                        "/api/blood-requests",
                        {

                            method: "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                "Authorization":
                                    `Bearer ${accessToken}`

                            },

                            body:
                                JSON.stringify(
                                    requestData
                                )

                        }
                    );


                // ==============================================
                // 8. READ SERVER RESPONSE
                // ==============================================

                let responseData = null;


                try {

                    responseData =
                        await response.json();

                }

                catch {

                    responseData = null;

                }


                // ==============================================
                // 9. HANDLE API ERROR
                // ==============================================

                if (!response.ok) {

                    console.error(
                        "BloodLink: Failed to create blood request.",
                        response.status,
                        responseData
                    );


                    let errorMessage =
                        "Unable to create the blood request.";


                    if (
                        responseData &&
                        typeof responseData.detail === "string"
                    ) {

                        errorMessage =
                            responseData.detail;

                    }


                    throw new Error(
                        errorMessage
                    );

                }


                // ==============================================
                // 10. SUCCESS
                // ==============================================

                console.log(
                    "BloodLink: Blood request created successfully.",
                    responseData
                );


                alert(
                    "Blood request created successfully."
                );


                // Return to Blood Requests page.

                renderBloodRequests();

            }

            catch (error) {

                // ==============================================
                // 11. ERROR HANDLING
                // ==============================================

                console.error(
                    "BloodLink: Blood request submission error:",
                    error
                );


                alert(
                    error.message ||
                    "Something went wrong while creating the blood request."
                );

            }

            finally {

                // ==============================================
                // 12. RESTORE SUBMIT BUTTON
                // ==============================================

                if (submitButton) {

                    submitButton.disabled = false;

                }

            }

        }
    );

}