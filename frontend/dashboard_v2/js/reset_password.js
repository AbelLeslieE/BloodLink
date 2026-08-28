const requestForm = document.getElementById("passwordResetRequestForm");
const confirmForm = document.getElementById("passwordResetConfirmForm");
const requestMessage = document.getElementById("resetRequestMessage");
const confirmMessage = document.getElementById("resetConfirmMessage");
const resetToken = new URLSearchParams(window.location.search).get("token");
const newPassword = document.getElementById("newPassword");
const confirmPassword = document.getElementById("confirmPassword");

function showMessage(element, text, isError = false) {
    element.classList.toggle("is-error", isError);
    element.textContent = text;
}

function apiMessage(data, fallback) {
    if (typeof data?.detail === "string") return data.detail;

    if (Array.isArray(data?.detail)) {
        const firstError = data.detail[0];
        return String(firstError?.msg || fallback).replace(/^Value error,\s*/i, "");
    }

    return fallback;
}

function setInvalid(input, invalid) {
    input.closest(".input-group")?.classList.toggle("is-invalid", invalid);
    input.setAttribute("aria-invalid", String(invalid));
}

function passwordProblem(password) {
    if (password.length < 8) return "Password must contain at least 8 characters.";
    if (password !== password.trim()) return "Password cannot start or end with a space.";
    if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
        return "Password must include at least one letter and one number.";
    }
    return "";
}

function setResetMode() {
    const hasToken = Boolean(resetToken);
    requestForm.hidden = hasToken;
    confirmForm.hidden = !hasToken;

    if (hasToken) {
        document.getElementById("resetTitle").textContent = "Choose a new password";
        document.getElementById("resetSubtitle").textContent =
            "Use a strong password that you do not use elsewhere.";
    }
}

document.querySelectorAll("[data-password-toggle]").forEach((toggle) => {
    toggle.addEventListener("click", () => {
        const input = document.getElementById(toggle.getAttribute("aria-controls"));
        const isHidden = input.type === "password";
        input.type = isHidden ? "text" : "password";
        toggle.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
        toggle.innerHTML = isHidden
            ? '<i class="fa-regular fa-eye-slash"></i>'
            : '<i class="fa-regular fa-eye"></i>';
    });
});

document.getElementById("resetEmail").addEventListener("input", (event) => {
    setInvalid(event.target, false);
    requestMessage.textContent = "";
});

[newPassword, confirmPassword].forEach((input) => {
    input.addEventListener("input", () => {
        setInvalid(input, false);
        confirmMessage.textContent = "";
    });
});

setResetMode();

requestForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("resetEmail");
    const cleanEmail = email.value.trim();
    requestMessage.textContent = "";

    if (!cleanEmail || !email.validity.valid) {
        setInvalid(email, true);
        showMessage(
            requestMessage,
            "Enter a valid email address, for example name@example.com.",
            true
        );
        email.focus();
        return;
    }

    const submitButton = requestForm.querySelector("button[type=submit]");
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending…';

    try {
        const response = await fetch("/api/auth/password-reset/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: cleanEmail }),
        });
        const data = await response.json().catch(() => ({}));
        showMessage(
            requestMessage,
            apiMessage(data, "If the account exists, a reset link has been sent."),
            !response.ok
        );
    } catch {
        showMessage(
            requestMessage,
            "We could not request a reset link. Check your connection and try again.",
            true
        );
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fa-regular fa-paper-plane"></i> Send reset link';
    }
});

confirmForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    confirmMessage.textContent = "";

    const problem = passwordProblem(newPassword.value);
    if (problem) {
        setInvalid(newPassword, true);
        showMessage(confirmMessage, problem, true);
        newPassword.focus();
        return;
    }

    if (!confirmPassword.value) {
        setInvalid(confirmPassword, true);
        showMessage(confirmMessage, "Confirm your new password.", true);
        confirmPassword.focus();
        return;
    }

    if (newPassword.value !== confirmPassword.value) {
        setInvalid(confirmPassword, true);
        showMessage(confirmMessage, "The passwords do not match.", true);
        confirmPassword.focus();
        return;
    }

    const submitButton = confirmForm.querySelector("button[type=submit]");
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating…';

    try {
        const response = await fetch("/api/auth/password-reset/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: resetToken, new_password: newPassword.value }),
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            showMessage(
                confirmMessage,
                apiMessage(data, "Unable to update your password."),
                true
            );
            return;
        }

        showMessage(confirmMessage, "Password updated. Taking you to sign in…");
        confirmForm.reset();
        setTimeout(() => {
            window.location.assign("/login?reset=success");
        }, 1200);
    } catch {
        showMessage(
            confirmMessage,
            "We could not update your password. Check your connection and try again.",
            true
        );
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fa-solid fa-shield-heart"></i> Update password';
    }
});
