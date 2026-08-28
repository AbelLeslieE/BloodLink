const form = document.querySelector("#donorRegistrationForm");
const message = document.querySelector("#formMessage");
const submit = document.querySelector("#submitRegistration");
const password = document.querySelector("#registrationPassword");
const confirmation = document.querySelector("#registrationPasswordConfirm");

function validatePasswordConfirmation() {
    const matches = password.value === confirmation.value;
    confirmation.setCustomValidity(matches ? "" : "Passwords do not match.");
    return matches;
}

document.querySelectorAll("[data-password-toggle]").forEach((toggle) => {
    toggle.addEventListener("click", () => {
        const input = document.getElementById(toggle.getAttribute("aria-controls"));
        const isHidden = input.type === "password";
        input.type = isHidden ? "text" : "password";
        toggle.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
        toggle.classList.toggle("is-visible", isHidden);
    });
});

password.addEventListener("input", validatePasswordConfirmation);
confirmation.addEventListener("input", validatePasswordConfirmation);

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.className = "";
    message.textContent = "";

    if (!validatePasswordConfirmation()) {
        message.textContent = "Passwords do not match.";
        confirmation.focus();
        return;
    }

    const payload = Object.fromEntries(new FormData(form).entries());
    delete payload.confirm_password;
    submit.disabled = true;
    try {
        const response = await fetch("/api/donor-registration", {
            method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || "We could not create your account.");
        message.className = "success";
        message.textContent = `${data.message} Redirecting to sign in...`;
        form.reset();
        setTimeout(() => window.location.assign("/login"), 1800);
    } catch (error) {
        message.textContent = error.message;
    } finally {
        submit.disabled = false;
    }
});
