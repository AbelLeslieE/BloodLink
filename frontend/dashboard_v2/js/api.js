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

function logoutUser() {

    /*
       BloodLink currently uses a JWT stored
       in localStorage.

       Removing the JWT terminates the local
       authenticated session.

       We intentionally do NOT use
       localStorage.clear() because unrelated
       BloodLink preferences should remain.
    */

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

    logoutUser

};