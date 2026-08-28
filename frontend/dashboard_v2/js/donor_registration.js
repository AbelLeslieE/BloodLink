const form = document.querySelector("#donorRegistrationForm");
const message = document.querySelector("#formMessage");
const submit = document.querySelector("#submitRegistration");
const password = document.querySelector("#registrationPassword");
const confirmation = document.querySelector("#registrationPasswordConfirm");

const fieldLabels = {
    full_name: "Full name",
    phone: "Phone number",
    email: "Email address",
    blood_group: "Blood group",
    gender: "Gender",
    department: "Class, department, or organisation",
    username: "Username",
    password: "Password",
    confirm_password: "Confirm password",
};

function setMessage(text, type = "error") {
    message.className = type === "success" ? "success" : "";
    message.textContent = text;
}

function inputFor(name) {
    return form.elements.namedItem(name);
}

function clearFieldError(name) {
    const input = inputFor(name);
    if (!input) return;

    input.removeAttribute("aria-invalid");
    input.removeAttribute("aria-errormessage");
    input.setCustomValidity("");
    document.getElementById(`registration-${name}-error`)?.remove();
}

function showFieldError(name, error) {
    const input = inputFor(name);
    if (!input) return;

    clearFieldError(name);
    input.setAttribute("aria-invalid", "true");
    input.setCustomValidity(error);

    const fieldError = document.createElement("small");
    fieldError.id = `registration-${name}-error`;
    fieldError.className = "field-error";
    fieldError.textContent = error;
    input.closest("label")?.append(fieldError);
    input.setAttribute("aria-errormessage", fieldError.id);
}

function clearAllFieldErrors() {
    Object.keys(fieldLabels).forEach(clearFieldError);
}

function normalisePhone(value) {
    let normalised = value.replace(/[\s()-]/g, "");
    if (normalised.startsWith("00")) normalised = `+${normalised.slice(2)}`;
    return normalised;
}

function validateRegistration() {
    clearAllFieldErrors();

    const values = Object.fromEntries(new FormData(form).entries());
    const errors = {};
    const fullName = values.full_name.trim().replace(/\s+/g, " ");
    const username = values.username;
    const passwordValue = values.password;
    const phone = normalisePhone(values.phone);
    const email = values.email.trim();

    if (fullName.length < 2) {
        errors.full_name = "Enter your full name using at least 2 characters.";
    } else if (!/[\p{L}]/u.test(fullName) || /[^\p{L}\s.'-]/u.test(fullName)) {
        errors.full_name = "Use letters, spaces, apostrophes, hyphens, and periods only.";
    }

    if (!/^\+?\d{7,15}$/.test(phone)) {
        errors.phone = "Enter a valid phone number with 7 to 15 digits.";
    }

    if (!email) {
        errors.email = "Enter your email address.";
    } else if (!inputFor("email").validity.valid) {
        errors.email = "Enter a valid email address, for example name@example.com.";
    }

    if (!values.blood_group) {
        errors.blood_group = "Select your blood group.";
    }

    if (username.length < 3) {
        errors.username = "Username must contain at least 3 characters.";
    } else if (/\s/.test(username)) {
        errors.username = "Username cannot contain spaces.";
    } else if (!/^[A-Za-z0-9._-]+$/.test(username)) {
        errors.username = "Use only letters, numbers, periods, underscores, or hyphens.";
    }

    if (passwordValue.length < 8) {
        errors.password = "Password must contain at least 8 characters.";
    } else if (passwordValue !== passwordValue.trim()) {
        errors.password = "Password cannot start or end with a space.";
    } else if (!/[A-Za-z]/.test(passwordValue) || !/\d/.test(passwordValue)) {
        errors.password = "Password must include at least one letter and one number.";
    }

    if (!values.confirm_password) {
        errors.confirm_password = "Confirm your password.";
    } else if (passwordValue !== values.confirm_password) {
        errors.confirm_password = "Passwords do not match.";
    }

    Object.entries(errors).forEach(([name, error]) => showFieldError(name, error));

    return {
        errors,
        payload: {
            full_name: fullName,
            phone: values.phone.trim(),
            email,
            blood_group: values.blood_group,
            gender: values.gender,
            department: values.department.trim(),
            username,
            password: passwordValue,
        },
    };
}

function humaniseApiError(entry) {
    const field = entry.loc?.at(-1);
    const label = fieldLabels[field] || "This field";
    const error = String(entry.msg || "Enter a valid value.")
        .replace(/^Value error,\s*/i, "");

    if (/field required/i.test(error)) return `${label} is required.`;
    if (/string should have at least/i.test(error)) return `${label} is too short.`;
    if (/string should have at most/i.test(error)) return `${label} is too long.`;
    if (/valid email/i.test(error)) return "Enter a valid email address, for example name@example.com.";
    return error;
}

function apiProblem(data) {
    if (typeof data?.detail === "string") {
        const detail = data.detail;
        const field = /username/i.test(detail)
            ? "username"
            : /phone number/i.test(detail)
                ? "phone"
                : /email address/i.test(detail)
                    ? "email"
                    : null;

        return {
            message: detail,
            fieldErrors: field ? { [field]: detail } : {},
        };
    }

    if (Array.isArray(data?.detail)) {
        const fieldErrors = {};

        data.detail.forEach((entry) => {
            const field = entry.loc?.at(-1);
            if (field && fieldLabels[field] && !fieldErrors[field]) {
                fieldErrors[field] = humaniseApiError(entry);
            }
        });

        return {
            message: Object.keys(fieldErrors).length
                ? "Please correct the highlighted fields and try again."
                : "Please review your registration details and try again.",
            fieldErrors,
        };
    }

    return {
        message: "We could not create your account. Please try again.",
        fieldErrors: {},
    };
}

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

form.addEventListener("input", (event) => {
    if (fieldLabels[event.target.name]) clearFieldError(event.target.name);

    if (event.target === password || event.target === confirmation) {
        clearFieldError("confirm_password");
    }
});

password.addEventListener("input", validatePasswordConfirmation);
confirmation.addEventListener("input", validatePasswordConfirmation);

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage("");

    const { errors, payload } = validateRegistration();

    if (Object.keys(errors).length) {
        setMessage("Please correct the highlighted fields and try again.");
        inputFor(Object.keys(errors)[0])?.focus();
        return;
    }

    submit.disabled = true;
    submit.textContent = "Creating account…";

    try {
        const response = await fetch("/api/donor-registration", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            const problem = apiProblem(data);
            throw Object.assign(new Error(problem.message), {
                fieldErrors: problem.fieldErrors,
            });
        }

        setMessage(`${data.message} Redirecting to sign in...`, "success");
        form.reset();
        setTimeout(() => window.location.assign("/login"), 1800);
    } catch (error) {
        const fieldErrors = error?.fieldErrors || {};
        Object.entries(fieldErrors).forEach(([name, fieldError]) => {
            showFieldError(name, fieldError);
        });

        setMessage(
            error instanceof TypeError
                ? "We could not reach BloodLink. Check your connection and try again."
                : (error?.message || "We could not create your account. Please try again.")
        );
    } finally {
        submit.disabled = false;
        submit.textContent = "Create my donor account";
    }
});
