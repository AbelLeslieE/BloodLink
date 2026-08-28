const form = document.querySelector("#donorRegistrationForm");
const message = document.querySelector("#formMessage");
const submit = document.querySelector("#submitRegistration");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    message.className = "";
    message.textContent = "";
    const payload = Object.fromEntries(new FormData(form).entries());
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
