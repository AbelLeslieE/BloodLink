/* ==========================================================
   BloodLink - Donor Response Center
   File: notifications.js

   Description
   ----------------------------------------------------------
   Manages the complete donor response workflow after
   compatible donor emails have been sent.

   Workflow

   Blood Request
          │
          ▼
   Compatible Donors
          │
          ▼
   Email Campaign
          │
          ▼
   Donor Responses
          │
          ▼
   Donor Response Center

========================================================== */
import {
    API,
    authenticatedFetch
} from "./api.js";

/* ==========================================================
   1. MODULE STATE
========================================================== */

let notificationFeed = [];

let filteredFeed = [];

let selectedNotification = null;

let selectedRequest = null;

let selectedRecipient = null;


/* ==========================================================
   2. CACHED DOM ELEMENTS
========================================================== */

const elements = {

    /* ======================================================
       HERO
    ====================================================== */

    refreshButton: null,



    /* ======================================================
       KPI CARDS
    ====================================================== */

    totalNotifications: null,

    emailRequests: null,

    totalResponses: null,

    responseRate: null,



    /* ======================================================
       TOOLBAR
    ====================================================== */

    searchInput: null,

    typeFilter: null,

    statusFilter: null,

    dateFilter: null,



    /* ======================================================
       LEFT PANEL
    ====================================================== */

    notificationList: null,



    /* ======================================================
       RIGHT PANEL
    ====================================================== */

    notificationDetails: null,



    /* ======================================================
       REQUEST SUMMARY
    ====================================================== */

    requestSummary: null,

    recipientTable: null,

    timeline: null,



    /* ======================================================
       ACTION BUTTONS
    ====================================================== */

    resendPendingBtn: null,

    exportBtn: null,

    markCompletedBtn: null

};



/* ==========================================================
   3. NOTIFICATION TYPES
========================================================== */

const NOTIFICATION_TYPES = {

    EMAIL_REQUEST: "email_request",

    RESPONSE_ACCEPTED: "accepted",

    RESPONSE_DECLINED: "declined",

    RESPONSE_PENDING: "pending"

};



/* ==========================================================
   4. REQUEST PRIORITY
========================================================== */

const PRIORITY = {

    CRITICAL: "Critical",

    HIGH: "High",

    MEDIUM: "Medium",

    LOW: "Low"

};



/* ==========================================================
   5. STATUS
========================================================== */

const STATUS = {

    PENDING: "Pending",

    ACTIVE: "Active",

    COMPLETED: "Completed"

};



/* ==========================================================
   6. ICONS
========================================================== */

const ICONS = {

    email: "📧",

    accepted: "✅",

    declined: "❌",

    pending: "⏳",

    donor: "❤️",

    hospital: "🏥",

    blood: "🩸",

    timeline: "🕒",

    notification: "🔔"

};



/* ==========================================================
   7. EMPTY OBJECT
========================================================== */

const EMPTY_REQUEST = {

    id: "",

    requestNumber: "",

    patient: "",

    hospital: "",

    bloodGroup: "",

    units: 0,

    district: "",

    priority: "",

    requiredDate: "",

    emailsSent: 0,

    accepted: 0,

    declined: 0,

    pending: 0,

    recipients: []

};



/* ==========================================================
   8. PUBLIC FUNCTIONS
========================================================== */

/* ==========================================================
   9. LOAD DONOR RESPONSE CENTER
========================================================== */
export function loadNotifications() {

    return `

    <!-- ======================================================
         Notifications Page
    ======================================================= -->

    <div class="notifications-page">

        <!-- ======================================================
             Background Overlay
        ======================================================= -->

        <div class="notifications-overlay"></div>

        <!-- ======================================================
             Main Content Container
        ======================================================= -->

        <div class="notifications-container">

            <!-- ======================================================
                 Hero Section
            ======================================================= -->

            <section class="notifications-hero glass-card">

                <div class="hero-left">

                    <div class="hero-icon">

                        ❤️

                    </div>

                    <div class="hero-content">

                        <h1>

                            Donor Response Center

                        </h1>

                        <p>

                            Monitor every blood request, donor response and
                            email campaign from one centralized dashboard.

                        </p>

                    </div>

                </div>

                <div class="hero-right">

                    <button
                        id="refreshResponsesBtn"
                        class="primary-btn">

                        Refresh Responses

                    </button>

                </div>

            </section>


            <!-- ======================================================
                 KPI Cards
            ======================================================= -->

            <section class="notification-kpis">

                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        🔔

                    </div>

                    <div class="kpi-info">

                        <h2 id="totalNotifications">

                            0

                        </h2>

                        <span>

                            Notifications

                        </span>

                    </div>

                </div>


                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        📧

                    </div>

                    <div class="kpi-info">

                        <h2 id="emailRequests">

                            0

                        </h2>

                        <span>

                            Email Requests

                        </span>

                    </div>

                </div>


                <div class="kpi-card glass-card">

                    <div class="kpi-icon">

                        ❤️

                    </div>

                    <div class="kpi-info">

                        <h2 id="totalResponses">

                            0

                        </h2>

                        <span>

                            Responses

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
            <!-- ======================================================
                 Toolbar
            ======================================================= -->

            <section class="notifications-toolbar glass-card">

                <div class="toolbar-left">

                    <input
                        id="notificationSearch"
                        class="search-input"
                        type="text"
                        placeholder="Search notifications...">

                    <select
                        id="typeFilter"
                        class="search-select">

                        <option value="all">
                            All Types
                        </option>

                        <option value="email_request">
                            Email Requests
                        </option>

                        <option value="accepted">
                            Accepted
                        </option>

                        <option value="declined">
                            Declined
                        </option>

                    </select>

                    <select
                        id="statusFilter"
                        class="search-select">

                        <option value="all">
                            All Status
                        </option>

                        <option value="active">
                            Active
                        </option>

                        <option value="completed">
                            Completed
                        </option>

                    </select>

                    <input
                        id="dateFilter"
                        class="search-input"
                        type="date">

                </div>

                <div class="toolbar-right">

                    <button
                        id="markAllReadBtn"
                        class="secondary-btn">

                        Mark All Read

                    </button>

                </div>

            </section>

            <!-- ======================================================
                 Main Content
            ======================================================= -->

            <section class="notifications-layout">

                <!-- ==================================================
                     Left Column
                =================================================== -->

                <div class="left-column">

                    <div class="notification-feed glass-card">

                        <div class="panel-header">

                            <h2>

                                Activity Feed

                            </h2>

                            <span
                                id="notificationCounter"
                                class="badge">

                                0 Items

                            </span>

                        </div>

                        <div
                            id="notificationList"
                            class="notification-list">

                        </div>

                    </div>

                </div>

                <!-- ==================================================
                     Right Column
                =================================================== -->

                <div class="right-column">

                    <div
                        id="notificationDetails"
                        class="notification-details glass-card">
                        <!-- ==================================================
                             Request Details Wrapper
                        =================================================== -->

                        <div class="request-details-wrapper">

                            <!-- ==========================================
                                 Request Header
                            =========================================== -->

                            <div class="request-header">

                                <div>

                                    <span
                                        id="requestBadge"
                                        class="request-badge">

                                        Email Request

                                    </span>

                                    <h2 id="requestTitle">

                                        Select a Blood Request

                                    </h2>

                                    <p id="requestSubtitle">

                                        Select a notification from the
                                        activity feed to view donor
                                        responses and campaign details.

                                    </p>

                                </div>

                                <div>

                                    <span
                                        id="requestTime"
                                        class="priority-badge">

                                        --

                                    </span>

                                </div>

                            </div>


                            <!-- ==========================================
                                 Request Information
                            =========================================== -->

                            <div class="request-info-grid">

                                <div class="info-card glass-inner-card">

                                    <span>

                                        Blood Group

                                    </span>

                                    <strong id="bloodGroup">

                                        --

                                    </strong>

                                </div>

                                <div class="info-card glass-inner-card">

                                    <span>

                                        Units Required

                                    </span>

                                    <strong id="unitsRequired">

                                        --

                                    </strong>

                                </div>

                                <div class="info-card glass-inner-card">

                                    <span>

                                        Required By

                                    </span>

                                    <strong id="requiredDate">

                                        --

                                    </strong>

                                </div>

                                <div class="info-card glass-inner-card">

                                    <span>

                                        District

                                    </span>

                                    <strong id="district">

                                        --

                                    </strong>

                                </div>

                            </div>


                            <!-- ==========================================
                                 Email Campaign Status
                            =========================================== -->

                            <div class="request-message glass-inner-card">

                                <div class="message-icon">

                                    📧

                                </div>

                                <div>

                                    <strong>

                                        Email Campaign

                                    </strong>

                                    <p id="campaignStatus">

                                        Emails have not been sent yet.

                                    </p>

                                </div>

                            </div>


                            <!-- ==========================================
                                 Campaign Statistics
                            =========================================== -->

                            <div class="recipient-overview">

                                <div class="overview-card glass-inner-card">

                                    <h2 id="emailsSentCard">

                                        0

                                    </h2>

                                    <span>

                                        Emails Sent

                                    </span>

                                </div>

                                <div class="overview-card glass-inner-card">

                                    <h2 id="acceptedCard">

                                        0

                                    </h2>

                                    <span>

                                        Accepted

                                    </span>

                                </div>

                                <div class="overview-card glass-inner-card">

                                    <h2 id="declinedCard">

                                        0

                                    </h2>

                                    <span>

                                        Declined

                                    </span>

                                </div>

                                <div class="overview-card glass-inner-card">

                                    <h2 id="pendingCard">

                                        0

                                    </h2>

                                    <span>

                                        Pending

                                    </span>

                                </div>

                            </div>                        
                            <!-- ==========================================
                                 Recipient List
                            =========================================== -->

                            <div class="recipient-section glass-inner-card">

                                <div class="section-header">

                                    <h3>

                                        Recipient List

                                    </h3>

                                    <button
                                        id="viewAllRecipientsBtn"
                                        class="text-btn">

                                        View All

                                    </button>

                                </div>

                                <div class="recipient-table-wrapper">

                                    <table class="recipient-table">

                                        <thead>

                                            <tr>

                                                <th>

                                                    Donor

                                                </th>

                                                <th>

                                                    Distance

                                                </th>

                                                <th>

                                                    Response

                                                </th>

                                                <th>

                                                    Responded At

                                                </th>

                                                <th>

                                                    Action

                                                </th>

                                            </tr>

                                        </thead>

                                        <tbody id="recipientTable">

                                        </tbody>

                                    </table>

                                </div>

                            </div>


                            <!-- ==========================================
                                 Timeline
                            =========================================== -->

                            <div class="timeline-section glass-inner-card">

                                <div class="section-header">

                                    <h3>

                                        Activity Timeline

                                    </h3>

                                </div>

                                <div
                                    id="timelineContainer"
                                    class="timeline-container">

                                </div>

                            </div>


                            <!-- ==========================================
                                 Request Actions
                            =========================================== -->

                            <div class="request-actions">

                                <button
                                    id="resendPendingBtn"
                                    class="secondary-btn">

                                    Resend Pending Emails

                                </button>

                                <button
                                    id="exportBtn"
                                    class="secondary-btn">

                                    Export Report

                                </button>

                                <button
                                    id="markCompletedBtn"
                                    class="primary-btn">

                                    Mark Request Completed

                                </button>

                            </div>

                        </div>

                    </div>

                </div>

            </section>
            <!-- ======================================================
                 Toast Container
            ======================================================= -->

            <div
                id="notificationToastContainer"
                class="toast-container">

            </div>

        </div>

        <!-- End notifications-container -->

    </div>

    <!-- End notifications-page -->

    `;

}            
/* ==========================================================
   10. INITIALIZE DONOR RESPONSE CENTER
========================================================== */

export function initializeNotifications() {

    console.log("Loading Donor Response Center...");

    cacheElements();

    loadNotificationsFromAPI();

    setupEventListeners();

}
/* ==========================================================
   11. CACHE DOM ELEMENTS
========================================================== */

function cacheElements() {

    /* ======================================================
       HERO
    ====================================================== */

    elements.refreshButton =
        document.getElementById("refreshResponsesBtn");



    /* ======================================================
       KPI CARDS
    ====================================================== */

    elements.totalNotifications =
        document.getElementById("totalNotifications");

    elements.emailRequests =
        document.getElementById("emailRequests");

    elements.totalResponses =
        document.getElementById("totalResponses");

    elements.responseRate =
        document.getElementById("responseRate");



    /* ======================================================
       TOOLBAR
    ====================================================== */

    elements.searchInput =
        document.getElementById("notificationSearch");

    elements.typeFilter =
        document.getElementById("typeFilter");

    elements.statusFilter =
        document.getElementById("statusFilter");

    elements.dateFilter =
        document.getElementById("dateFilter");



    /* ======================================================
       LEFT PANEL
    ====================================================== */

    elements.notificationList =
        document.getElementById("notificationList");



    /* ======================================================
       RIGHT PANEL
    ====================================================== */

    elements.notificationDetails =
        document.getElementById("notificationDetails");



    /* ======================================================
       REQUEST SUMMARY
    ====================================================== */

    elements.requestSummary =
        document.querySelector(".request-details-wrapper");



    /* ======================================================
       RECIPIENTS
    ====================================================== */

    elements.recipientTable =
        document.getElementById("recipientTable");



    /* ======================================================
       TIMELINE
    ====================================================== */

    elements.timeline =
        document.getElementById("timelineContainer");



    /* ======================================================
       ACTION BUTTONS
    ====================================================== */

    elements.resendPendingBtn =
        document.getElementById("resendPendingBtn");

    elements.exportBtn =
        document.getElementById("exportBtn");

    elements.markCompletedBtn =
        document.getElementById("markCompletedBtn");

}
/* ==========================================================
   12. LOAD SAMPLE NOTIFICATIONS
========================================================== */

function loadSampleNotifications() {

    notificationFeed = [

        {
            id: 1,

            type: NOTIFICATION_TYPES.EMAIL_REQUEST,

            title: "Blood Request #BR-2026-001",

            subtitle: "City Hospital",

            createdAt: "Today • 09:15 AM",

            request: {

                id: "BR-2026-001",

                patient: "Arun Thomas",

                hospital: "City Hospital",

                bloodGroup: "O+",

                units: 4,

                district: "Thrissur",

                priority: PRIORITY.CRITICAL,

                requiredDate: "Today",

                status: STATUS.ACTIVE,

                emailsSent: 8,

                accepted: 3,

                declined: 2,

                pending: 3

            },

            recipients: [

                {
                    id: 1,

                    donor: "Rahul Kumar",

                    bloodGroup: "O+",

                    distance: "2.1 km",

                    email: "rahul@email.com",

                    phone: "+91 9876543210",

                    response: "Accepted",

                    respondedAt: "09:22 AM"
                },

                {
                    id: 2,

                    donor: "Akash Nair",

                    bloodGroup: "O+",

                    distance: "3.4 km",

                    email: "akash@email.com",

                    phone: "+91 9876543211",

                    response: "Declined",

                    respondedAt: "09:31 AM"
                },

                {
                    id: 3,

                    donor: "Maria Thomas",

                    bloodGroup: "O+",

                    distance: "4.6 km",

                    email: "maria@email.com",

                    phone: "+91 9876543212",

                    response: "Pending",

                    respondedAt: ""
                }

            ],

            timeline: [

                {

                    icon: "📧",

                    title: "Email campaign started",

                    time: "09:15 AM"

                },

                {

                    icon: "✅",

                    title: "Rahul Kumar accepted",

                    time: "09:22 AM"

                },

                {

                    icon: "❌",

                    title: "Akash Nair declined",

                    time: "09:31 AM"

                }

            ]

        },



        {

            id: 2,

            type: NOTIFICATION_TYPES.EMAIL_REQUEST,

            title: "Blood Request #BR-2026-002",

            subtitle: "Medical College",

            createdAt: "Today • 11:05 AM",

            request: {

                id: "BR-2026-002",

                patient: "Joseph Mathew",

                hospital: "Medical College",

                bloodGroup: "A-",

                units: 2,

                district: "Ernakulam",

                priority: PRIORITY.HIGH,

                requiredDate: "Tomorrow",

                status: STATUS.ACTIVE,

                emailsSent: 5,

                accepted: 2,

                declined: 1,

                pending: 2

            },

            recipients: [

                {

                    id: 4,

                    donor: "Nithin Paul",

                    bloodGroup: "A-",

                    distance: "1.9 km",

                    email: "nithin@email.com",

                    phone: "+91 9988776655",

                    response: "Accepted",

                    respondedAt: "11:20 AM"

                },

                {

                    id: 5,

                    donor: "Athira Roy",

                    bloodGroup: "A-",

                    distance: "3.8 km",

                    email: "athira@email.com",

                    phone: "+91 9988776644",

                    response: "Pending",

                    respondedAt: ""

                }

            ],

            timeline: [

                {

                    icon: "📧",

                    title: "Emails sent",

                    time: "11:05 AM"

                },

                {

                    icon: "✅",

                    title: "Nithin Paul accepted",

                    time: "11:20 AM"

                }

            ]

        }

    ];



    filteredFeed = [...notificationFeed];

}
/* ==========================================================
   13. KPI ENGINE
========================================================== */

function updateKPIs() {

    if (!notificationFeed.length) {

        elements.totalNotifications.textContent = "0";

        elements.emailRequests.textContent = "0";

        elements.totalResponses.textContent = "0";

        elements.responseRate.textContent = "0%";

        return;

    }

    /* ======================================================
       Total Notification Count
    ====================================================== */

    const totalNotifications = notificationFeed.length;


    /* ======================================================
       Email Campaign Count
    ====================================================== */

    const emailRequests = notificationFeed.filter(

        item => item.type === NOTIFICATION_TYPES.EMAIL_REQUEST

    ).length;


    /* ======================================================
       Response Statistics
    ====================================================== */

    let accepted = 0;

    let declined = 0;

    let pending = 0;

    let emailsSent = 0;


    notificationFeed.forEach(notification => {

        emailsSent += notification.request.emailsSent;

        accepted += notification.request.accepted;

        declined += notification.request.declined;

        pending += notification.request.pending;

    });


    const totalResponses = accepted + declined;


    const responseRate =

        emailsSent === 0

            ? 0

            : Math.round((totalResponses / emailsSent) * 100);


    /* ======================================================
       Update KPI Cards
    ====================================================== */

    elements.totalNotifications.textContent =

        totalNotifications;


    elements.emailRequests.textContent =

        emailRequests;


    elements.totalResponses.textContent =

        totalResponses;


    elements.responseRate.textContent =

        `${responseRate}%`;

}
/* ==========================================================
   14. RENDER NOTIFICATION FEED
========================================================== */

function renderNotificationFeed() {

    if (!elements.notificationList) return;

    elements.notificationList.innerHTML = "";

    if (filteredFeed.length === 0) {

        elements.notificationList.innerHTML = `

            <div class="empty-notification-feed">

                <div class="empty-icon">

                    📭

                </div>

                <h3>

                    No Notifications

                </h3>

                <p>

                    No notification activities were found.

                </p>

            </div>

        `;

        return;

    }


    filteredFeed.forEach(notification => {

        const card = document.createElement("div");

        card.className = "notification-card";


        if (

            selectedNotification &&
            selectedNotification.id === notification.id

        ) {

            card.classList.add("active");

        }


        const accepted = notification.request.accepted;

        const declined = notification.request.declined;

        const pending = notification.request.pending;


        card.innerHTML = `

            <div class="notification-card-header">

                <div class="notification-icon">

                    📧

                </div>

                <div class="notification-title">

                    <h3>

                        ${notification.title}

                    </h3>

                    <span>

                        ${notification.createdAt}

                    </span>

                </div>

            </div>


            <div class="notification-card-body">

                <div class="notification-info">

                    <strong>

                        ${notification.request.hospital}

                    </strong>

                    <span>

                        ${notification.request.patient}

                    </span>

                </div>


                <div class="notification-tags">

                    <span class="blood-tag">

                        🩸 ${notification.request.bloodGroup}

                    </span>

                    <span class="priority-tag">

                        ${notification.request.priority}

                    </span>

                </div>


                <div class="notification-summary">

                    <div>

                        <strong>

                            ${notification.request.emailsSent}

                        </strong>

                        <span>

                            Emails

                        </span>

                    </div>

                    <div>

                        <strong>

                            ${accepted}

                        </strong>

                        <span>

                            Accepted

                        </span>

                    </div>

                    <div>

                        <strong>

                            ${declined}

                        </strong>

                        <span>

                            Declined

                        </span>

                    </div>

                    <div>

                        <strong>

                            ${pending}

                        </strong>

                        <span>

                            Pending

                        </span>

                    </div>

                </div>

            </div>

        `;


        card.addEventListener("click", async () => {

            selectedNotification = notification;

            selectedRequest = notification.request;

            renderNotificationFeed();

            renderNotificationDetails();

            await loadNotificationRecipients(
                notification.id
            );

        });


        elements.notificationList.appendChild(card);

    });


    const counter = document.getElementById("notificationCounter");

    if (counter) {

        counter.textContent =

            `${filteredFeed.length} Items`;

    }

}
/* ==========================================================
   15. RENDER NOTIFICATION DETAILS
========================================================== */

function renderNotificationDetails() {

    if (!elements.notificationDetails) return;


    /* ======================================================
       Empty State
    ====================================================== */

    if (!selectedNotification) {

        elements.notificationDetails.innerHTML = `

            <div class="empty-details">

                <div class="empty-icon">

                    ❤️

                </div>

                <h2>

                    No Notification Selected

                </h2>

                <p>

                    Select a notification from the
                    activity feed to view the complete
                    blood request information.

                </p>

            </div>

        `;

        return;

    }


    const request = selectedNotification.request;


    /* ======================================================
       Main Layout
    ====================================================== */

    elements.notificationDetails.innerHTML = `

        <div class="request-details-wrapper">

            <!-- ==========================================
                 Header
            =========================================== -->

            <div class="request-header">

                <div>

                    <span class="request-badge">

                        ${request.id}

                    </span>

                    <h2>

                        ${request.patient}

                    </h2>

                    <p>

                        ${request.hospital}

                    </p>

                </div>

                <span class="priority-badge">

                    ${request.priority}

                </span>

            </div>



            <!-- ==========================================
                 Request Information
            =========================================== -->

            <div class="request-info-grid">

                <div class="info-card glass-inner-card">

                    <span>Blood Group</span>

                    <strong>

                        ${request.bloodGroup}

                    </strong>

                </div>


                <div class="info-card glass-inner-card">

                    <span>Units</span>

                    <strong>

                        ${request.units}

                    </strong>

                </div>


                <div class="info-card glass-inner-card">

                    <span>District</span>

                    <strong>

                        ${request.district}

                    </strong>

                </div>


                <div class="info-card glass-inner-card">

                    <span>Required Date</span>

                    <strong>

                        ${request.requiredDate}

                    </strong>

                </div>

            </div>



            <!-- ==========================================
                 Campaign Summary
            =========================================== -->

            <div class="recipient-overview">

                <div class="overview-card glass-inner-card">

                    <h2>

                        ${request.emailsSent}

                    </h2>

                    <span>

                        Emails Sent

                    </span>

                </div>

                <div class="overview-card glass-inner-card">

                    <h2>

                        ${request.accepted}

                    </h2>

                    <span>

                        Accepted

                    </span>

                </div>

                <div class="overview-card glass-inner-card">

                    <h2>

                        ${request.declined}

                    </h2>

                    <span>

                        Declined

                    </span>

                </div>

                <div class="overview-card glass-inner-card">

                    <h2>

                        ${request.pending}

                    </h2>

                    <span>

                        Pending

                    </span>

                </div>

            </div>



            <!-- ==========================================
                 Recipient Table
            =========================================== -->

            <div class="recipient-section">

                <div class="section-header">

                    <h3>

                        Donor Responses

                    </h3>

                </div>

                <div class="recipient-table-wrapper">

                    <table class="recipient-table">

                        <thead>

                            <tr>

                                <th>Donor</th>

                                <th>Blood</th>

                                <th>Distance</th>

                                <th>Status</th>

                                <th>Responded</th>

                                <th>Action</th>

                            </tr>

                        </thead>

                        <tbody id="recipientTableBody">

                        </tbody>

                    </table>

                </div>

            </div>



            <!-- ==========================================
                 Timeline
            =========================================== -->

            <div class="timeline-section">

                <div class="section-header">

                    <h3>

                        Activity Timeline

                    </h3>

                </div>

                <div id="timelineContainer">

                </div>

            </div>



            <!-- ==========================================
                 Actions
            =========================================== -->

            <div class="request-actions">

                <button
                    id="resendPendingBtn"
                    class="secondary-btn">

                    Resend Pending

                </button>

                <button
                    id="exportBtn"
                    class="secondary-btn">

                    Export Report

                </button>

                <button
                    id="markCompletedBtn"
                    class="primary-btn">

                    Mark Completed

                </button>

            </div>

        </div>

    `;


    renderRecipientTable();

    renderTimeline();

}
/* ==========================================================
   16. RENDER RECIPIENT TABLE
========================================================== */

function renderRecipientTable() {

    const tableBody =
        document.getElementById("recipientTableBody");

    if (!tableBody) return;

    tableBody.innerHTML = "";

    if (
        !selectedNotification ||
        !selectedNotification.recipients ||
        selectedNotification.recipients.length === 0
    ) {

        tableBody.innerHTML = `

            <tr>

                <td
                    colspan="5"
                    class="empty-table">

                    No recipients found.

                </td>

            </tr>

        `;

        return;

    }


    selectedNotification.recipients.forEach(recipient => {

        let badgeClass = "pending";
        let badgeIcon = "⏳";

        if (recipient.response === "Accepted") {

            badgeClass = "accepted";
            badgeIcon = "✅";

        }

        else if (recipient.response === "Declined") {

            badgeClass = "declined";
            badgeIcon = "❌";

        }


        const row = document.createElement("tr");

        row.innerHTML = `

            <td>

                <div class="recipient-name">

                    <strong>

                        ${recipient.donor}

                    </strong>

                    <small>

                        ${recipient.email}

                    </small>

                </div>

            </td>

            <td>

                ${recipient.bloodGroup}

            </td>

            <td>

                ${recipient.distance}

            </td>

            <td>

                <span
                    class="status-badge ${badgeClass}">

                    ${badgeIcon}
                    ${recipient.response}

                </span>

            </td>

            <td>

    ${recipient.respondedAt || "--"}

    </td>

    <td>

        <button
            class="view-donor-btn"
            data-donor-id="${recipient.id}">

            View Donor

        </button>

    </td>

        `;

        tableBody.appendChild(row);

    });

}



/* ==========================================================
   17. RENDER ACTIVITY TIMELINE
========================================================== */

function renderTimeline() {

    const container =
        document.getElementById("timelineContainer");

    if (!container) return;

    container.innerHTML = "";


    if (
        !selectedNotification ||
        !selectedNotification.timeline ||
        selectedNotification.timeline.length === 0
    ) {

        container.innerHTML = `

            <div class="empty-timeline">

                No timeline available.

            </div>

        `;

        return;

    }


    selectedNotification.timeline.forEach(event => {

        const item = document.createElement("div");

        item.className = "timeline-item";

        item.innerHTML = `

            <div class="timeline-icon">

                ${event.icon}

            </div>

            <div class="timeline-content">

                <strong>

                    ${event.title}

                </strong>

                <span>

                    ${event.time}

                </span>

            </div>

        `;

        container.appendChild(item);

    });

}
/* ==========================================================
   18. APPLY SEARCH & FILTERS
========================================================== */

function applyFilters() {

    const searchText =
        elements.searchInput.value
            .trim()
            .toLowerCase();

    const selectedType =
        elements.typeFilter.value;

    const selectedStatus =
        elements.statusFilter.value;

    filteredFeed = notificationFeed.filter(notification => {

        /* ==============================================
           Search
        ============================================== */

        const matchesSearch =

            notification.title
                .toLowerCase()
                .includes(searchText)

            ||

            notification.subtitle
                .toLowerCase()
                .includes(searchText)

            ||

            notification.request.patient
                .toLowerCase()
                .includes(searchText)

            ||

            notification.request.hospital
                .toLowerCase()
                .includes(searchText)

            ||

            notification.request.bloodGroup
                .toLowerCase()
                .includes(searchText);



        /* ==============================================
           Type Filter
        ============================================== */

        const matchesType =

            selectedType === "all"

                ? true

                : notification.type === selectedType;



        /* ==============================================
           Status Filter
        ============================================== */

        const matchesStatus =

            selectedStatus === "all"

                ? true

                : notification.request.status
                    .toLowerCase() === selectedStatus;



        return (

            matchesSearch &&

            matchesType &&

            matchesStatus

        );

    });

    renderNotificationFeed();

}



/* ==========================================================
   19. REFRESH MODULE
========================================================== */

function refreshNotifications() {

    console.log(
        "Refreshing Notification Center..."
    );

    loadNotificationsFromAPI();

}



/* ==========================================================
   20. EVENT LISTENERS
========================================================== */

function setupEventListeners() {

    /* ==============================================
       Search
    ============================================== */

    elements.searchInput.addEventListener(

        "input",

        applyFilters

    );



    /* ==============================================
       Type Filter
    ============================================== */

    elements.typeFilter.addEventListener(

        "change",

        applyFilters

    );



    /* ==============================================
       Status Filter
    ============================================== */

    elements.statusFilter.addEventListener(

        "change",

        applyFilters

    );



    /* ==============================================
       Refresh
    ============================================== */

    elements.refreshButton.addEventListener(

        "click",

        refreshNotifications

    );



    /* ==============================================
       Date Filter
       (Backend Integration Later)
    ============================================== */

    if (elements.dateFilter) {

        elements.dateFilter.addEventListener(

            "change",

            () => {

                console.log(

                    "Date Filter:",

                    elements.dateFilter.value

                );

            }

        );

    }

}

/* ==========================================================
   21. LOAD NOTIFICATIONS FROM BACKEND
========================================================== */

/* ==========================================================
   LOAD NOTIFICATIONS FROM DATABASE
========================================================== */

async function loadNotificationsFromAPI() {

    try {

        const response = await authenticatedFetch(
            API.notifications
        );

        if (!response) {
            return;
        }

        if (!response.ok) {

            throw new Error(
                `Unable to load notifications (${response.status})`
            );

        }

        const campaigns = await response.json();

        /*
        ------------------------------------------------------
        Convert backend response into the format expected
        by the existing UI.
        ------------------------------------------------------
        */

        notificationFeed = campaigns.map(campaign => ({

            id: campaign.id,

            type: NOTIFICATION_TYPES.EMAIL_REQUEST,

            title: campaign.title,

            subtitle: campaign.blood_request.hospital_name,

            createdAt: formatDate(campaign.created_at),

            request: {

                id: campaign.blood_request.id,

                patient: campaign.blood_request.patient_name,

                hospital: campaign.blood_request.hospital_name,

                bloodGroup: campaign.blood_request.blood_group,

                units: campaign.blood_request.units_required,

                district: campaign.blood_request.hospital_location,

                priority: campaign.blood_request.priority,

                requiredDate: formatDate(
                    campaign.blood_request.required_date
                ),

                status: campaign.blood_request.status,

                emailsSent: campaign.total_sent,

                accepted: campaign.accepted_count,

                declined: campaign.declined_count,

                pending: campaign.pending_count

            },

            recipients: [],

            timeline: []

        }));

        filteredFeed = [...notificationFeed];

        updateKPIs();

        renderNotificationFeed();

        clearDetailsPanel();

    }

    catch (error) {

        console.error(
            "Unable to load notifications.",
            error
        );

    }

}


/* ==========================================================
   22. LOAD REQUEST DETAILS
========================================================== */

async function loadRequestDetails(requestId) {

    try {

        /*
        =======================================================

        FUTURE

        GET

        /api/notifications/{requestId}

        =======================================================
        */

        console.log(

            "Loading request:",

            requestId

        );

    }

    catch (error) {

        console.error(error);

    }

}



/* ==========================================================
   23. RESEND PENDING EMAILS
========================================================== */

async function resendPendingEmails(requestId) {

    try {

        /*
        =======================================================

        FUTURE

        POST

        /api/find-match/resend

        {

            request_id

        }

        =======================================================
        */

        console.log(

            "Resending pending emails:",

            requestId

        );

    }

    catch (error) {

        console.error(error);

    }

}



/* ==========================================================
   24. EXPORT REQUEST REPORT
========================================================== */

async function exportRequestReport(requestId) {

    try {

        /*
        =======================================================

        FUTURE

        GET

        /api/reports/request/{id}

        =======================================================
        */

        console.log(

            "Export report:",

            requestId

        );

    }

    catch (error) {

        console.error(error);

    }

}



/* ==========================================================
   25. MARK REQUEST COMPLETED
========================================================== */

async function markRequestCompleted(requestId) {

    try {

        /*
        =======================================================

        FUTURE

        PATCH

        /api/blood-requests/{id}

        {

            status:"Completed"

        }

        =======================================================
        */

        console.log(

            "Mark completed:",

            requestId

        );

    }

    catch (error) {

        console.error(error);

    }

}



/* ==========================================================
   26. BACKEND REFRESH
========================================================== */

async function refreshFromBackend() {

    await loadNotificationsFromAPI();

    updateKPIs();

    renderNotificationFeed();

    renderNotificationDetails();

}
/* ==========================================================
   27. STATUS BADGE CLASS
========================================================== */

function getStatusClass(status) {

    switch ((status || "").toLowerCase()) {

        case "accepted":

            return "accepted";

        case "declined":

            return "declined";

        case "pending":

            return "pending";

        default:

            return "default";

    }

}



/* ==========================================================
   28. PRIORITY BADGE CLASS
========================================================== */

function getPriorityClass(priority) {

    switch ((priority || "").toLowerCase()) {

        case "critical":

            return "critical";

        case "high":

            return "high";

        case "medium":

            return "medium";

        case "low":

            return "low";

        default:

            return "default";

    }

}



/* ==========================================================
   29. FORMAT DATE
========================================================== */

function formatDate(date) {

    if (!date) return "--";

    try {

        return new Date(date).toLocaleDateString();

    }

    catch {

        return date;

    }

}



/* ==========================================================
   30. FORMAT TIME
========================================================== */

function formatTime(time) {

    if (!time) return "--";

    return time;

}



/* ==========================================================
   31. SORT NOTIFICATIONS
========================================================== */

function sortNotifications() {

    filteredFeed.sort((a, b) => {

        return new Date(b.createdAt) -

               new Date(a.createdAt);

    });

}



/* ==========================================================
   32. RESET SELECTION
========================================================== */

function resetSelection() {

    selectedNotification = null;

    selectedRequest = null;

    selectedRecipient = null;

}



/* ==========================================================
   33. CLEAR DETAILS PANEL
========================================================== */

function clearDetailsPanel() {

    if (!elements.notificationDetails) return;

    elements.notificationDetails.innerHTML = `

        <div class="empty-details">

            <div class="empty-icon">

                ❤️

            </div>

            <h2>

                No Notification Selected

            </h2>

            <p>

                Select a notification from the
                activity feed to begin.

            </p>

        </div>

    `;

}


/* ==========================================================
   LOAD NOTIFICATION RECIPIENTS
========================================================== */

async function loadNotificationRecipients(notificationId) {

    try {

        const response = await authenticatedFetch(
            `${API.notifications}/${notificationId}/recipients`
        );

        if (!response) {
            return;
        }

        if (!response.ok) {

            throw new Error(
                "Unable to load recipients."
            );

        }

        const recipients = await response.json();

        if (!selectedNotification) {
            return;
        }

        selectedNotification.recipients = recipients.map(recipient => ({

            id: recipient.id,

            donor: recipient.donor.full_name,

            bloodGroup: recipient.donor.blood_group,

            distance: recipient.distance,

            email: recipient.email,

            phone: recipient.donor.phone,

            response: recipient.status,

            respondedAt: formatDate(
                recipient.responded_at
            )

        }));

        renderRecipientTable();

    }

    catch (error) {

        console.error(error);

    }

}
/* ==========================================================
   34. REFRESH COMPLETE MODULE
========================================================== */

function reloadModule() {

    resetSelection();

    loadNotificationsFromAPI();

}


/* ==========================================================
   35. MODULE READY
========================================================== */

console.log(

    "%cBloodLink - Donor Response Center Loaded",

    "color:#38bdf8;font-weight:bold;"

);