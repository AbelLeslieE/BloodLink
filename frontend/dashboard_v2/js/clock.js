// ==========================================
// BIOTRACK V2 CLOCK
// ==========================================

function updateClock() {

    const now = new Date();

    const date = now.toLocaleDateString("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric"
    });

    const time = now.toLocaleTimeString("en-IN");

    const currentDate = document.getElementById("currentDate");
    const currentTime = document.getElementById("currentTime");

    // Prevent errors on pages that don't have a clock
    if (currentDate) {
        currentDate.textContent = date;
    }

    if (currentTime) {
        currentTime.textContent = time;
    }

}

updateClock();

setInterval(updateClock, 1000);


/* ==========================================
   DATE & TIME FORMATTERS
========================================== */

/**
 * Example:
 * 14 Jul 2026, 07:56 PM
 */
function formatDateTime(dateString) {

    if (!dateString) return "-";

    const date = new Date(dateString);

    return date.toLocaleString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });

}


/**
 * Example:
 * 14 Jul 2026
 */
function formatDate(dateString) {

    if (!dateString) return "-";

    const date = new Date(dateString);

    return date.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });

}


/**
 * Example:
 * 07:56 PM
 */
function formatTime(dateString) {

    if (!dateString) return "-";

    const date = new Date(dateString);

    return date.toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true
    });

}