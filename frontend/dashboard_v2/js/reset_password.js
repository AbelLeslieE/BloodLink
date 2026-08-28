const requestForm = document.getElementById("passwordResetRequestForm");
const confirmForm = document.getElementById("passwordResetConfirmForm");
const requestMessage = document.getElementById("resetRequestMessage");
const confirmMessage = document.getElementById("resetConfirmMessage");
const resetToken = new URLSearchParams(window.location.search).get("token");

function showMessage(element, text, isError = false) {
    element.style.color = isError ? "#dc2626" : "#167950";
    element.textContent = text;
}

function apiMessage(data, fallback) {
    return typeof data?.detail === "string" ? data.detail : fallback;
}

if (resetToken) {
    document.getElementById("resetTitle").textContent = "Choose a new password";
    document.getElementById("resetSubtitle").textContent = "Use a strong password that you do not use elsewhere.";
    requestForm.hidden = true;
    confirmForm.hidden = false;
}

requestForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    requestMessage.textContent = "";
    const submitButton = requestForm.querySelector("button[type=submit]");
    submitButton.disabled = true;
    submitButton.textContent = "Sending…";

    try {
        const response = await fetch("/api/auth/password-reset/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: document.getElementById("resetEmail").value.trim() }),
        });
        const data = await response.json().catch(() => ({}));
        showMessage(requestMessage, apiMessage(data, "If the account exists, a reset link has been sent."), !response.ok);
    } catch {
        showMessage(requestMessage, "Unable to request a reset link. Please try again.", true);
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fa-regular fa-paper-plane"></i> Send reset link';
    }
});

confirmForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    confirmMessage.textContent = "";
    const password = document.getElementById("newPassword").value;
    const confirmation = document.getElementById("confirmPassword").value;
    if (password !== confirmation) {
        showMessage(confirmMessage, "The passwords do not match.", true);
        return;
    }

    const submitButton = confirmForm.querySelector("button[type=submit]");
    submitButton.disabled = true;
    submitButton.textContent = "Updating…";
    try {
        const response = await fetch("/api/auth/password-reset/confirm", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: resetToken, new_password: password }),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            showMessage(confirmMessage, apiMessage(data, "Unable to update your password."), true);
            return;
        }
        showMessage(confirmMessage, apiMessage(data, "Password updated. Redirecting to sign in…"));
        confirmForm.reset();
        setTimeout(() => { window.location.href = "/login"; }, 1800);
    } catch {
        showMessage(confirmMessage, "Unable to update your password. Please try again.", true);
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="fa-solid fa-shield-heart"></i> Update password';
    }
});
