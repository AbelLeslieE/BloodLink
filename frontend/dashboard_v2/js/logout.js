"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const logoutButton = document.querySelector(".logout-btn");
    if (!logoutButton) return;

    logoutButton.addEventListener("click", async () => {
        const token = localStorage.getItem("access_token");
        try {
            await fetch("/api/auth/logout", {
                method: "POST",
                headers: token ? { Authorization: `Bearer ${token}` } : {},
            });
        } finally {
            ["access_token", "volunteer_name", "username", "role", "full_name"].forEach(
                (key) => localStorage.removeItem(key),
            );
            window.location.replace("/login");
        }
    });
});
