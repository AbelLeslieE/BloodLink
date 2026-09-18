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

if (new URLSearchParams(window.location.search).get("reset") === "success") {
    message.style.color = "#167950";
    message.textContent = "Password updated. Sign in with your new password.";
}
if (new URLSearchParams(window.location.search).get("registration") === "success") {
    message.style.color = "#167950";
    message.textContent = "Your password has been created. Sign in with your username and password.";
}

// ======================================================
// PASSWORD VISIBILITY
// ======================================================

togglePassword.addEventListener("click", () => {

    const hidden = passwordInput.type === "password";

    passwordInput.type = hidden ? "text" : "password";

    togglePassword.innerHTML = hidden
        ? '<i class="fa-regular fa-eye-slash"></i>'
        : '<i class="fa-regular fa-eye"></i>';

    togglePassword.setAttribute(
        "aria-label",
        hidden ? "Hide password" : "Show password"
    );

});

// ======================================================
// LOGIN
// ======================================================

form.addEventListener("submit", async (event) => {

    event.preventDefault();

    message.textContent = "";

    document.querySelectorAll(".input-group.is-invalid").forEach((group) => {
        group.classList.remove("is-invalid");
    });

    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    loginButton.disabled = true;
    loginButton.setAttribute("aria-busy", "true");
    loginButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin" aria-hidden="true"></i><span>Signing in…</span>';
    message.style.color = "#9f1239";
    message.textContent = "Securely signing you in…";

    // OAuth2PasswordRequestForm requires form data
    const formData = new URLSearchParams();

    formData.append("username", username);
    formData.append("password", password);

    try {

        const response = await fetch("/api/auth/login", {

            method: "POST",

            headers: {

                "Content-Type": "application/x-www-form-urlencoded",
                "X-Session-Mode": "cookie"

            },

            body: formData

        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {

            message.style.color = "#dc2626";
            message.textContent =
                data.detail || "Invalid username or password.";
            if (response.status !== 429) {
                passwordInput.closest(".input-group").classList.add("is-invalid");
                passwordInput.focus();
            }

            return;

        }

        // Store only the non-secret cookie-session marker, never the browser JWT
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
