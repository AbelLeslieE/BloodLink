// ==========================================
// LOGOUT
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    console.log("Logout JS Loaded");

    const logoutButton = document.querySelector(".logout-btn");

    console.log(logoutButton);

    logoutButton.addEventListener("click", async () => {

        console.log("Logout clicked");

        try {

            const response = await fetch("/api/logout", {
                method: "POST"
            });

            console.log(response.status);

            window.location.href = "/";

        }

        catch(error){

            console.error(error);

        }

    });

});