// ==========================================================
// BLOODLINK DASHBOARD CONTROLLER
// File: dashboard.js
//
// Responsibilities:
// - Initialize dashboard
// - Load authenticated user information
// - Load dashboard API data
// - Update KPI cards
// - Initialize charts
// - Handle dashboard actions
//
// IMPORTANT:
// Dashboard HTML is already defined in dashboard.html.
// This file must NOT generate or replace dashboard HTML.
// ==========================================================

import {
    getDashboardData
} from "./api.js";

import {
    loadFindMatch
} from "./find_match.js";

import {
    loadDonorManagement
} from "./donor_management.js";

import {
    loadDonationHistory,
    initializeDonationHistory
} from "./donation_history.js";
import {
    loadUsers,
    initializeUsers
} from "./usersView.js";
import {
    loadSettings,
    initializeSettings
} from "./settings.js";
import {
    loadNotifications,
    initializeNotifications
} from "./notifications.js";
// ==========================================================
// 1. DASHBOARD STATE
// ==========================================================

let monthlyDonationChart = null;
let bloodGroupChart = null;


// ==========================================================
// 2. LOAD USER INFORMATION
// ==========================================================

function loadUserInformation() {

    const fullName =
        localStorage.getItem("full_name") ||
        localStorage.getItem("username") ||
        "Administrator";


    const role =
        localStorage.getItem("role") ||
        "Admin";


    const firstLetter =
        fullName
            .trim()
            .charAt(0)
            .toUpperCase() || "A";


    // Hero

    const currentUser =
        document.getElementById("currentUser");

    if (currentUser) {

        currentUser.textContent =
            fullName;

    }


    // Sidebar

    const sidebarUser =
        document.getElementById("sidebarUser");

    const sidebarRole =
        document.getElementById("sidebarRole");

    const sidebarAvatar =
        document.getElementById("sidebarAvatar");


    if (sidebarUser) {

        sidebarUser.textContent =
            fullName;

    }


    if (sidebarRole) {

        sidebarRole.textContent =
            formatRole(role);

    }


    if (sidebarAvatar) {

        sidebarAvatar.textContent =
            firstLetter;

    }


    // Topbar

    const topUser =
        document.getElementById("topUser");

    const topAvatar =
        document.getElementById("topAvatar");


    if (topUser) {

        topUser.textContent =
            fullName;

    }


    if (topAvatar) {

        topAvatar.textContent =
            firstLetter;

    }

}


// ==========================================================
// 3. FORMAT ROLE
// ==========================================================

function formatRole(role) {

    if (!role) {

        return "User";

    }


    return role
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            (letter) =>
                letter.toUpperCase()
        );

}


// ==========================================================
// 4. UPDATE KPI VALUE
// ==========================================================

function updateKpi(
    elementId,
    value,
    fallback = 0
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {

        return;

    }


    element.textContent =
        value ?? fallback;

}


// ==========================================================
// 5. UPDATE DASHBOARD KPIs
// ==========================================================

function updateDashboardKpis(data) {

    if (!data) {

        return;

    }


    /*
       These property names are the expected
       BloodLink dashboard API contract.

       If the backend currently returns different
       property names, only this mapping needs
       to be adjusted.
    */

    updateKpi(
        "totalDonors",
        data.total_donors
    );


    updateKpi(
        "bloodUnits",
        data.blood_units
    );


    updateKpi(
        "activeRequests",
        data.active_requests
    );


    updateKpi(
        "todayDonations",
        data.today_donations
    );


    updateKpi(
        "emergencyCases",
        data.emergency_cases
    );


    const successRate =
        data.success_rate;


    updateKpi(
        "successRate",
        successRate != null
            ? `${successRate}%`
            : "0%",
        "0%"
    );

}


// ==========================================================
// 6. MONTHLY DONATION CHART
// ==========================================================

function initializeMonthlyDonationChart(data = {}) {

    const canvas =
        document.getElementById(
            "monthlyDonationChart"
        );

    if (!canvas) {

        return;

    }

    if (typeof window.Chart === "undefined") {

        console.warn(
            "Chart.js is not available."
        );

        return;

    }

    if (monthlyDonationChart) {

        monthlyDonationChart.destroy();

    }

    const labels = Object.keys(data || {});

    const values = Object.values(data || {});

    monthlyDonationChart =
        new window.Chart(
            canvas,
            {

                type: "line",

                data: {

                    labels,

                    datasets: [

                        {

                            label: "Blood Donations",

                            data: values,

                            borderColor: "#DC2626",

                            backgroundColor:
                                "rgba(220,38,38,0.08)",

                            borderWidth: 2,

                            fill: true,

                            tension: 0.35,

                            pointRadius: 3,

                            pointHoverRadius: 5

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {

                            display: false

                        }

                    },

                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }

        );

}


// ==========================================================
// 7. BLOOD GROUP CHART
// ==========================================================

function initializeBloodGroupChart(data = {}) {

    const canvas =
        document.getElementById(
            "bloodGroupChart"
        );


    if (!canvas) {

        return;

    }


    if (
        typeof window.Chart ===
        "undefined"
    ) {

        return;

    }


    if (bloodGroupChart) {

        bloodGroupChart.destroy();

    }


    const labels =
        Object.keys(data || {});

            "A+",
            "A-",
            "B+",
            "B-",
            "AB+",
            "AB-",
            "O+",
            "O-"

        ;


    const values =
        Object.values(data || {});

            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0

        ;


    bloodGroupChart =
        new window.Chart(
            canvas,
            {

                type: "doughnut",

                data: {

                    labels,

                    datasets: [

                        {

                            data: values,

                            backgroundColor: [

                                "#DC2626",
                                "#EF4444",
                                "#1E3A8A",
                                "#3B82F6",
                                "#16A34A",
                                "#22C55E",
                                "#F59E0B",
                                "#F97316"

                            ],

                            borderWidth: 0

                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    cutout: "68%",

                    plugins: {

                        legend: {

                            position:
                                "bottom",

                            labels: {

                                usePointStyle:
                                    true,

                                padding: 16

                            }

                        }

                    }

                }

            }
        );

}


// ==========================================================
// 8. INITIALIZE CHARTS
// ==========================================================

function initializeCharts(data = {}) {

    initializeMonthlyDonationChart(
        data.monthly_donations
    );


    initializeBloodGroupChart(
        data.blood_group_distribution
    );

}


// ==========================================================
// 9. LOAD DASHBOARD DATA
// ==========================================================

async function loadDashboardData() {

    const data =
        await getDashboardData();


    /*
       Keep the dashboard usable even if the
       backend dashboard endpoint has not yet
       been fully implemented.
    */

    if (!data) {

        initializeCharts();

        return;

    }


    updateDashboardKpis(
        data.statistics || {}
    );


    initializeCharts(
        data
    );

}


// ==========================================================
// 10. HERO ACTIONS
// ==========================================================

function initializeDashboardActions() {

    const newRequestButton =
        document.getElementById(
            "newRequestButton"
        );


    const registerDonorButton =
        document.getElementById(
            "registerDonorButton"
        );


    if (newRequestButton) {

        newRequestButton.addEventListener(
            "click",
            () => {

                window.dispatchEvent(

                    new CustomEvent(
                        "bloodlink:navigate",
                        {

                            detail: {

                                page:
                                    "bloodRequests",

                                action:
                                    "create"

                            }

                        }
                    )

                );

            }
        );

    }


    if (registerDonorButton) {

        registerDonorButton.addEventListener(
            "click",
            () => {

                window.dispatchEvent(

                    new CustomEvent(
                        "bloodlink:navigate",
                        {

                            detail: {

                                page:
                                    "donors",

                                action:
                                    "create"

                            }

                        }
                    )

                );

            }
        );

    }

}

// ==========================================================
// NAVIGATION HANDLER
// ==========================================================

function handleNavigation(event) {

    const page = event.detail.page;

    const dashboardView =
        document.getElementById("dashboardView");

    const moduleView =
        document.getElementById("moduleView");

    if (!dashboardView || !moduleView) {
        return;
    }

    // ---------------- Dashboard ----------------

    if (page === "dashboard") {

        dashboardView.hidden = false;

        moduleView.hidden = true;

        moduleView.innerHTML = "";

        return;

    }

    // ---------------- Other Modules ----------------

    dashboardView.hidden = true;

    moduleView.hidden = false;

    switch (page) {

        /* ======================================================
        Find Match
        ====================================================== */

        case "findMatch":

            loadFindMatch(moduleView);

            break;


        /* ======================================================
        Donor Management
        ====================================================== */

        case "donors":

            loadDonorManagement();

            break;


        /* ======================================================
        Donation History
        ====================================================== */

        case "donationHistory":

            moduleView.innerHTML =
                loadDonationHistory();

            initializeDonationHistory();

            break;
        /* ======================================================
        Users Management
        ====================================================== */
        case "users":

            moduleView.innerHTML = loadUsers();

            initializeUsers();

            break;
        /* ======================================================
        Settings
        ====================================================== */
        case "settings":

            moduleView.innerHTML =  
                loadSettings();

            initializeSettings();   

            break;    
        /* ======================================================
        Notifications
        ====================================================== */

        case "notifications":

            moduleView.innerHTML =
                loadNotifications();

            initializeNotifications();

            break;


        /* ======================================================
        Blood Requests
        ====================================================== */

        case "bloodRequests":

            // This module renders itself from blood-requests.js.
            // Do nothing here to avoid rendering the placeholder.
            break;


        /* ======================================================
        Placeholder Modules
        ====================================================== */

        default:

            moduleView.innerHTML = `
                <div style="
                    display:flex;
                    justify-content:center;
                    align-items:center;
                    height:70vh;
                    color:#0F172A;
                    font-size:22px;
                    font-weight:600;
                ">
                    ${page} module is under development.
                </div>
            `;

            break;

    }
}
// ==========================================================
// 11. INITIALIZE DASHBOARD
// ==========================================================

async function initializeDashboard() {

    // Load logged-in user's information
    loadUserInformation();

    // Activate dashboard buttons
    initializeDashboardActions();

    // Temporary empty charts until backend integration
    // Load dashboard data from backend
    await loadDashboardData();

    // Render Lucide icons
    if (window.lucide) {

        window.lucide.createIcons();

    }
    window.addEventListener(
        "bloodlink:navigate",
        handleNavigation
    );

}

// ==========================================================
// 12. INITIALIZATION
// ==========================================================

if (
    document.readyState ===
    "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeDashboard
    );

}

else {

    initializeDashboard();

}