// ======================================================
// BLOODLINK LOGIN
// ======================================================

const form = document.getElementById("loginForm");
const message = document.getElementById("message");

const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");
const loginButton = form.querySelector("button[type=submit]");
const loginButtonLabel = loginButton.innerHTML;

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

    loginButton.disabled = true;
    loginButton.setAttribute("aria-busy", "true");
    loginButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> LOGGING IN…';
    message.style.color = "#2F67F6";
    message.textContent = "Logging in…";

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

        if (!profileResponse.ok) {
            throw new Error("Unable to load the signed-in account.");
        }

        const profile = await profileResponse.json();

        localStorage.setItem("username", profile.username);
        localStorage.setItem("role", profile.role);
        localStorage.setItem("full_name", profile.full_name);

        // Redirect
        window.location.href = profile.role === "Administrator"
            ? "/dashboard"
            : "/donor-dashboard";

    }

    catch (error) {

        console.error(error);

        message.style.color = "#dc2626";
        message.textContent =
            "Unable to connect to the server.";

    }

    finally {

        loginButton.disabled = false;
        loginButton.removeAttribute("aria-busy");
        loginButton.innerHTML = loginButtonLabel;

    }

});
