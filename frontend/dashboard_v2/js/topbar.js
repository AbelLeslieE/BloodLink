// ==========================================================
// PRANADAN TOPBAR DATE, TIME, AND GREETING
// ==========================================================

(() => {
    const greeting = document.getElementById("greetingText");
    const dateElement = document.getElementById("todayDate");
    const timeElement = document.getElementById("currentTime");
    const timeZoneElement = document.getElementById("timeZoneLabel");

    if (!greeting && !dateElement && !timeElement) {
        return;
    }

    const dateFormatter = new Intl.DateTimeFormat(undefined, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric"
    });

    const timeFormatter = new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });

    const timeZoneFormatter = new Intl.DateTimeFormat(undefined, {
        timeZoneName: "short"
    });

    function getGreeting(hour) {
        if (hour < 12) return "Good morning";
        if (hour < 17) return "Good afternoon";
        return "Good evening";
    }

    function updateTopbarClock() {
        const now = new Date();

        if (greeting) {
            greeting.textContent = getGreeting(now.getHours());
        }

        if (dateElement) {
            dateElement.textContent = dateFormatter.format(now);
            dateElement.setAttribute("datetime", now.toISOString());
        }

        if (timeElement) {
            timeElement.textContent = timeFormatter.format(now);
        }

        if (timeZoneElement) {
            const timeZoneName = timeZoneFormatter
                .formatToParts(now)
                .find((part) => part.type === "timeZoneName")?.value;

            timeZoneElement.textContent = timeZoneName
                ? `Local time · ${timeZoneName}`
                : "Local time";
        }
    }

    updateTopbarClock();
    window.setInterval(updateTopbarClock, 1000);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) updateTopbarClock();
    });
})();
