// ==========================================================
// BLOODLINK API SERVICE
// File: api.js
//
// Responsibilities:
// - API configuration
// - Authentication token access
// - Authenticated API requests
// - Dashboard API
// - Logout / session cleanup
// ==========================================================

// ==========================================================
// 1. API ENDPOINTS
// ==========================================================

const API = {

    dashboard: "/api/dashboard",

    profile: "/api/auth/me",

    notifications: "/api/notifications",

    notificationStats: "/api/notifications/stats/summary",

    donors: "/api/donors",

    bloodRequests: "/api/blood-requests",

    donations: "/api/donations",

    donationSummary: "/api/donations/summary",

    donationRecent: "/api/donations/recent",

    matchFind: "/api/match/find",

    matchSend: "/api/match/send"

};

// ==========================================================
// 2. STORAGE KEYS
// ==========================================================

const AUTH_STORAGE_KEYS = [

    "access_token",

    "volunteer_name",

    "username",

    "role",

    "full_name"

];


// ==========================================================
// 3. GET ACCESS TOKEN
// ==========================================================

function getAccessToken() {

    return localStorage.getItem(
        "access_token"
    );

}


// ==========================================================
// 4. AUTHENTICATED FETCH
// ==========================================================

async function authenticatedFetch(
    url,
    options = {}
) {

    const token = getAccessToken();


    const headers = new Headers(
        options.headers || {}
    );


    if (token) {

        headers.set(
            "Authorization",
            `Bearer ${token}`
        );

    }


    const response = await fetch(
        url,
        {
            ...options,
            headers
        }
    );


    /*
       If the JWT is invalid or expired,
       terminate the local session.
    */

    if (response.status === 401) {

        logoutUser();

        return null;

    }


    return response;

}


// ==========================================================
// 5. FETCH DASHBOARD DATA
// ==========================================================

async function getDashboardData() {

    try {

        const response =
            await authenticatedFetch(
                API.dashboard
            );


        if (!response) {
            return null;
        }


        if (!response.ok) {

            throw new Error(
                `Dashboard request failed: ${response.status}`
            );

        }


        return await response.json();

    }

    catch (error) {

        console.error(
            "Unable to load dashboard data:",
            error
        );

        return null;

    }

}

// ==========================================================
// 5A. FETCH DONATION HISTORY
// ==========================================================

async function getDonationHistory() {

    try {

        const response =
            await authenticatedFetch(
                API.donations
            );

        if (!response) {
            return [];
        }

        if (!response.ok) {

            throw new Error(
                `Donation history request failed: ${response.status}`
            );

        }

        return await response.json();

    }

    catch (error) {

        console.error(
            "Unable to load donation history:",
            error
        );

        return [];

    }

}


// ==========================================================
// 5B. FETCH DONATION SUMMARY
// ==========================================================

async function getDonationSummary() {

    try {

        const response =
            await authenticatedFetch(
                API.donationSummary
            );

        if (!response) {
            return {};
        }

        if (!response.ok) {

            throw new Error(
                `Donation summary request failed: ${response.status}`
            );

        }

        return await response.json();

    }

    catch (error) {

        console.error(
            "Unable to load donation summary:",
            error
        );

        return {};

    }

}


// ==========================================================
// 5C. FETCH RECENT DONATIONS
// ==========================================================

async function getRecentDonations() {

    try {

        const response =
            await authenticatedFetch(
                API.donationRecent
            );

        if (!response) {
            return [];
        }

        if (!response.ok) {

            throw new Error(
                `Recent donations request failed: ${response.status}`
            );

        }

        return await response.json();

    }

    catch (error) {

        console.error(
            "Unable to load recent donations:",
            error
        );

        return [];

    }

}
// ==========================================================
// 5D. FETCH DONORS
// ==========================================================

async function getDonors() {

    try {

        const response =
            await authenticatedFetch(
                API.donors
            );

        if (!response) {
            return [];
        }

        if (!response.ok) {

            throw new Error(
                `Donor request failed: ${response.status}`
            );

        }

        return await response.json();

    }

    catch (error) {

        console.error(
            "Unable to load donors:",
            error
        );

        return [];

    }

}
// ==========================================================
// 6. CLEAR AUTHENTICATION DATA
// ==========================================================

function clearAuthenticationData() {

    AUTH_STORAGE_KEYS.forEach(
        (key) => {

            localStorage.removeItem(
                key
            );

        }
    );

}


// ==========================================================
// 7. LOGOUT
// ==========================================================

async function logoutUser({ revoke = false } = {}) {

    /*
       BloodLink currently uses a JWT stored
       in localStorage.

       Removing the JWT terminates the local
       authenticated session.

       We intentionally do NOT use
       localStorage.clear() because unrelated
       BloodLink preferences should remain.
    */

    const token = getAccessToken();

    if (revoke && token) {
        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            });
        } catch (error) {
            // Local cleanup still protects the current browser session when
            // the network is unavailable.
            console.warn("Server logout could not be completed.", error);
        }
    }

    clearAuthenticationData();


    /*
       replace() prevents the dashboard page
       from remaining as the previous browser
       history entry.
    */

    window.location.replace(
        "/login"
    );

}


// ==========================================================
// 8. EXPORT API
// ==========================================================

export {

    API,

    getAccessToken,

    authenticatedFetch,

    getDashboardData,

    getDonationHistory,

    getDonationSummary,

    getRecentDonations,

    getDonors,

    logoutUser

};
