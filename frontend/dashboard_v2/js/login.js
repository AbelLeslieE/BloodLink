// ======================================================
// BLOODLINK LOGIN
// ======================================================

const form = document.getElementById("loginForm");
const message = document.getElementById("message");

const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");

// ======================================================
// PASSWORD VISIBILITY
// ======================================================

togglePassword.addEventListener("click", () => {

    const hidden = passwordInput.type === "password";

    passwordInput.type = hidden ? "text" : "password";

    togglePassword.innerHTML = hidden
        ? '<i class="fa-regular fa-eye-slash"></i>'
        : '<i class="fa-regular fa-eye"></i>';

});

// ======================================================
// LOGIN
// ======================================================

form.addEventListener("submit", async (event) => {

    event.preventDefault();

    message.textContent = "";

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    // OAuth2PasswordRequestForm requires form data
    const formData = new URLSearchParams();

    formData.append("username", username);
    formData.append("password", password);

    try {

        const response = await fetch("/api/auth/login", {

            method: "POST",

            headers: {

                "Content-Type": "application/x-www-form-urlencoded"

            },

            body: formData

        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {

            message.style.color = "#dc2626";
            message.textContent =
                data.detail || "Invalid username or password.";

            return;

        }

        // Save JWT
        localStorage.setItem("access_token", data.access_token);

        // Save volunteer information
        localStorage.setItem(
            "volunteer_name",
            data.volunteer_name
        );

        // Load profile to determine role
        const profileResponse = await fetch("/api/auth/me", {

            headers: {

                Authorization: `Bearer ${data.access_token}`

            }

        });

        const profile = await profileResponse.json();

        localStorage.setItem("username", profile.username);
        localStorage.setItem("role", profile.role);
        localStorage.setItem("full_name", profile.full_name);

        // Redirect
        window.location.href = "/dashboard";

    }

    catch (error) {

        console.error(error);

        message.style.color = "#dc2626";
        message.textContent =
            "Unable to connect to the server.";

    }

});