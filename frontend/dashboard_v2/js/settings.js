/* ==========================================================
   BIOTRACK SETTINGS
   PART 3A
========================================================== */
function initSettings() {

    initializeNavigation();

    initializeProfilePhoto();

    initializeNotificationSwitches();

    initializeSecurity();

    initializePreferences();

    initializeTheme();

    initializeBackup();

    loadProfileData();

    loadSavedPreferences();

    initializeSmoothButtons();

    initializeButtonEffects();

    initializeCardEffects();

    showToast(
        "Settings",
        "Settings page loaded successfully.",
        "fa-circle-check"
    );

}
/* ==========================================================
   LOAD PROFILE DATA
========================================================== */

function loadProfileData() {

    const username =
        localStorage.getItem("username") || "Administrator";

    const role =
        localStorage.getItem("role") || "Administrator";

    const email =
        localStorage.getItem("email") || "admin@BloodLink.com";

    const employeeId =
        localStorage.getItem("employee_id") || "EMP-001";

    const fullName =
        document.getElementById("settingsFullName");

    const emailText =
        document.getElementById("settingsEmail");

    const roleText =
        document.getElementById("settingsRole");

    const employee =
        document.getElementById("settingsEmployeeId");

    if(fullName) fullName.textContent = username;

    if(emailText) emailText.textContent = email;

    if(roleText) roleText.textContent = role;

    if(employee) employee.textContent = employeeId;

}
/* ==========================================================
   SIDEBAR NAVIGATION
========================================================== */

function initializeNavigation() {

    const navItems = document.querySelectorAll(".nav-item");

    navItems.forEach(item => {

        item.addEventListener("click", () => {

            navItems.forEach(nav => nav.classList.remove("active"));

            item.classList.add("active");

            const target = document.getElementById(item.dataset.target);

            if (!target) return;

                            const sections =
                    document.querySelectorAll(".settings-card");

                sections.forEach(section => {

                    section.style.display = "none";

                });

                if (target) {

                    target.style.display = "block";

                }
                const cards =
                    document.querySelectorAll(".settings-card");

                cards.forEach(card => {

                    card.style.display = "none";

                });

                const first =
                    document.getElementById("profile");

                if (first) {

                    first.style.display = "block";

                }

        });

    });

}

/* ==========================================================
   PROFILE IMAGE
========================================================== */

function initializeProfilePhoto() {

    const uploadInput = document.getElementById("profileUpload");

    const preview = document.getElementById("profilePreview");

    const cameraButton = document.getElementById("changePhoto");

    if (!uploadInput || !preview || !cameraButton) return;

    cameraButton.addEventListener("click", () => {

        uploadInput.click();

    });

    uploadInput.addEventListener("change", event => {

        const file = event.target.files[0];

        if (!file) return;

        if (!file.type.startsWith("image/")) {

            showToast(

                "Invalid File",

                "Please select an image.",

                "fa-circle-exclamation"

            );

            return;

        }

        const reader = new FileReader();

        reader.onload = e => {

            preview.src = e.target.result;

            showToast(

                "Profile Updated",

                "Your profile picture has been changed.",

                "fa-circle-check"

            );

        };

        reader.readAsDataURL(file);

    });

}

/* ==========================================================
   BUTTON SCROLL EFFECT
========================================================== */

function initializeSmoothButtons() {

    document.querySelectorAll(".primary-btn, .secondary-btn").forEach(button => {

        button.addEventListener("click", createRipple);

    });

}

/* ==========================================================
   RIPPLE EFFECT
========================================================== */

function createRipple(event) {

    const button = event.currentTarget;

    const ripple = document.createElement("span");

    const size = Math.max(button.clientWidth, button.clientHeight);

    const rect = button.getBoundingClientRect();

    ripple.className = "ripple";

    ripple.style.width = size + "px";

    ripple.style.height = size + "px";

    ripple.style.left = event.clientX - rect.left - size / 2 + "px";

    ripple.style.top = event.clientY - rect.top - size / 2 + "px";

    button.appendChild(ripple);

    setTimeout(() => {

        ripple.remove();

    }, 600);

}
 

/* ==========================================================
   NOTIFICATION SWITCHES
========================================================== */

function initializeNotificationSwitches() {

    const switches = document.querySelectorAll(
        "#emailNotification, #desktopNotification, #requestUpdates, #pmReminder"
    );

    switches.forEach(toggle => {

        toggle.addEventListener("change", function () {

            const title = getSettingName(this.id);

            const status = this.checked ? "Enabled" : "Disabled";

            showToast(
                title,
                `${title} ${status}.`,
                this.checked
                    ? "fa-circle-check"
                    : "fa-circle-minus"
            );

        });

    });

}

function getSettingName(id) {

    switch (id) {

        case "emailNotification":
            return "Email Notifications";

        case "desktopNotification":
            return "Desktop Notifications";

        case "requestUpdates":
            return "Request Updates";

        case "pmReminder":
            return "Preventive Maintenance Reminder";

        default:
            return "Setting";

    }

}

/* ==========================================================
   SYSTEM PREFERENCES
========================================================== */

function initializePreferences() {

    const theme = document.getElementById("themeSelect");
    const language = document.getElementById("languageSelect");
    const date = document.getElementById("dateFormat");
    const time = document.getElementById("timeFormat");

    if (theme) {

        theme.addEventListener("change", () => {

            showToast(
                "Theme",
                `Theme changed to ${theme.value}.`,
                "fa-palette"
            );

        });

    }

    if (language) {

        language.addEventListener("change", () => {

            showToast(
                "Language",
                `Language set to ${language.value}.`,
                "fa-language"
            );

        });

    }

    if (date) {

        date.addEventListener("change", () => {

            showToast(
                "Date Format",
                `${date.value} selected.`,
                "fa-calendar"
            );

        });

    }

    if (time) {

        time.addEventListener("change", () => {

            showToast(
                "Time Format",
                `${time.value} selected.`,
                "fa-clock"
            );

        });

    }

}

/* ==========================================================
   SECURITY
========================================================== */

function initializeSecurity() {

    const changePassword =
        document.getElementById("changePassword");

    const sessions =
        document.getElementById("viewSessions");

    const twoFactor =
        document.getElementById("twoFactor");

    if (changePassword) {

        changePassword.addEventListener("click", () => {

            showToast(
                "Security",
                "Redirecting to Change Password...",
                "fa-key"
            );

        });

    }

    if (sessions) {

        sessions.addEventListener("click", () => {

            showToast(
                "Active Sessions",
                "Loading signed-in devices...",
                "fa-laptop"
            );

        });

    }

    if (twoFactor) {

        twoFactor.addEventListener("change", function () {

            showToast(
                "Two-Factor Authentication",
                this.checked
                    ? "Two-Factor Authentication Enabled."
                    : "Two-Factor Authentication Disabled.",
                this.checked
                    ? "fa-lock"
                    : "fa-lock-open"
            );

        });

    }

}

/* ==========================================================
   TOAST NOTIFICATION
========================================================== */

function showToast(title, message, icon) {

    let toast = document.querySelector(".toast");

    if (!toast) {

        toast = document.createElement("div");

        toast.className = "toast";

        toast.innerHTML = `

            <i class="fa-solid ${icon}"></i>

            <div>

                <h4>${title}</h4>

                <p>${message}</p>

            </div>

        `;

        document.body.appendChild(toast);

    } else {

        toast.innerHTML = `

            <i class="fa-solid ${icon}"></i>

            <div>

                <h4>${title}</h4>

                <p>${message}</p>

            </div>

        `;

    }

    toast.classList.add("show");

    clearTimeout(window.toastTimer);

    window.toastTimer = setTimeout(() => {

        toast.classList.remove("show");

    }, 3000);

}


/* ==========================================================
   BACKUP & EXPORT
========================================================== */

function initializeBackup() {

    const backupBtn = document.getElementById("backupNow");
    const exportBtn = document.getElementById("exportData");

    if (backupBtn) {

        backupBtn.addEventListener("click", function () {

            const original = this.innerHTML;

            this.disabled = true;

            this.innerHTML = `
                <div class="loader"></div>
                Creating Backup...
            `;

            setTimeout(() => {

                this.disabled = false;

                this.innerHTML = original;

                showToast(
                    "Backup Complete",
                    "System backup created successfully.",
                    "fa-cloud-arrow-up"
                );

            }, 2500);

        });

    }

    if (exportBtn) {

        exportBtn.addEventListener("click", () => {

            showToast(
                "Export Started",
                "Preparing maintenance data for download.",
                "fa-file-export"
            );

        });

    }

}

/* ==========================================================
   THEME
========================================================== */

function initializeTheme() {

    const selector = document.getElementById("themeSelect");

    if (!selector) return;

    selector.addEventListener("change", () => {

        localStorage.setItem("bloodlink-theme", selector.value);

        applyTheme(selector.value);

    });

}

function applyTheme(theme) {

    document.body.classList.remove("dark-theme");

    if (theme === "dark") {

        document.body.classList.add("dark-theme");

    }

    showToast(
        "Theme Updated",
        `${theme} theme applied.`,
        "fa-palette"
    );

}

/* ==========================================================
   SAVE PREFERENCES
========================================================== */

function loadSavedPreferences() {

    const theme = localStorage.getItem("bloodlink-theme");

    if (theme) {

        const selector = document.getElementById("themeSelect");

        if (selector) {

            selector.value = theme;

            applyTheme(theme);

        }

    }

    saveDropdown("languageSelect");
    saveDropdown("dateFormat");
    saveDropdown("timeFormat");

}

function saveDropdown(id) {

    const element = document.getElementById(id);

    if (!element) return;

    const saved = localStorage.getItem(id);

    if (saved) {

        element.value = saved;

    }

    element.addEventListener("change", () => {

        localStorage.setItem(id, element.value);

    });

}

/* ==========================================================
   GLOBAL BUTTON EFFECT
========================================================== */

/* ==========================================================
   BUTTON EFFECTS
========================================================== */

function initializeButtonEffects() {

    document.addEventListener("click", function (event) {

        const button = event.target.closest("button");

        if (!button) return;

        button.style.transform = "scale(.97)";

        setTimeout(() => {

            button.style.transform = "";

        }, 120);

    });

}

/* ==========================================================
   CARD HOVER EFFECT
========================================================== */

function initializeCardEffects(){

    document.querySelectorAll(".settings-card")
        .forEach(card=>{

            card.style.transition=".3s ease";

        });

}

/* ==========================================================
   KEYBOARD SHORTCUTS
========================================================== */

function initializeKeyboardShortcuts(){

    document.addEventListener("keydown", event => {

        if(event.ctrlKey &&
           event.key.toLowerCase()==="s"){

            event.preventDefault();

            showToast(
                "Settings Saved",
                "Your preferences have been saved.",
                "fa-floppy-disk"
            );

        }

    });

}

/* ==========================================================
   FINAL INITIALIZATION
========================================================== */

console.log(
    "%cBloodLink Settings Module Loaded",
    "color:#2563eb;font-size:16px;font-weight:bold;"
);

console.log("Version : 1.0.0");

console.log("Status  : Ready");

 