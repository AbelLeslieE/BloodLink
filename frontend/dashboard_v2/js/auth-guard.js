// ==========================================================
// BLOODLINK AUTHENTICATION GUARD
// File: auth-guard.js
//
// Responsibilities:
// - Protect authenticated pages
// - Check for an access token
// - Validate the JWT with FastAPI
// - Clear invalid/expired sessions
// - Redirect unauthenticated users to login
// ==========================================================


// ==========================================================
// 1. CONFIGURATION
// ==========================================================

const LOGIN_ROUTE = "/login";

const PROFILE_ENDPOINT = "/api/auth/me";


// ==========================================================
// 2. AUTHENTICATION STORAGE KEYS
// ==========================================================

const AUTH_STORAGE_KEYS = [

    "access_token",

    "volunteer_name",

    "username",

    "role",

    "full_name"

];


// ==========================================================
// 3. CLEAR AUTHENTICATION DATA
// ==========================================================

function clearAuthenticationData() {

    AUTH_STORAGE_KEYS.forEach(
        (key) => {

            localStorage.removeItem(key);

        }
    );

}


// ==========================================================
// 4. REDIRECT TO LOGIN
// ==========================================================

function redirectToLogin() {

    clearAuthenticationData();

    window.location.replace(
        LOGIN_ROUTE
    );

}


// ==========================================================
// 5. GET ACCESS TOKEN
// ==========================================================

function getAccessToken() {

    return localStorage.getItem(
        "access_token"
    );

}


// ==========================================================
// 6. VERIFY AUTHENTICATION
// ==========================================================

async function verifyAuthentication() {

    const token =
        getAccessToken();


    // ------------------------------------------------------
    // No token
    // ------------------------------------------------------

    if (!token) {

        redirectToLogin();

        return false;

    }


    try {

        // --------------------------------------------------
        // Validate token using FastAPI
        // --------------------------------------------------

        const response =
            await fetch(
                PROFILE_ENDPOINT,
                {

                    method: "GET",

                    headers: {

                        Authorization:
                            `Bearer ${token}`

                    },

                    cache: "no-store"

                }
            );


        // --------------------------------------------------
        // Invalid / expired token
        // --------------------------------------------------

        if (!response.ok) {

            redirectToLogin();

            return false;

        }


        // --------------------------------------------------
        // Valid authenticated user
        // --------------------------------------------------

        const profile =
            await response.json();


        /*
           Refresh local user information using
           trusted data returned by the backend.
        */

        if (profile.username) {

            localStorage.setItem(
                "username",
                profile.username
            );

        }


        if (profile.role) {

            localStorage.setItem(
                "role",
                profile.role
            );

        }


        if (profile.full_name) {

            localStorage.setItem(
                "full_name",
                profile.full_name
            );

        }


        return true;

    }

    catch (error) {

        console.error(
            "Authentication verification failed:",
            error
        );


        /*
           A network/server failure is treated as
           an unavailable authenticated session.

           This prevents protected dashboard content
           from continuing to operate without verification.
        */

        redirectToLogin();

        return false;

    }

}


// ==========================================================
// 7. RUN AUTHENTICATION GUARD
// ==========================================================
const authenticationVerified =
    await verifyAuthentication();


if (authenticationVerified) {

    document.body.classList.remove(
        "auth-pending"
    );

}

// ==========================================================
// 8. EXPORT RESULT
// ==========================================================

export {

    authenticationVerified

};