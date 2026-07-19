/* ==========================================================
   BloodLink Settings Module
   File: settings.js
========================================================== */

export function loadSettings() {

    return `

    <section class="settings-page">

        <!-- ======================================================
             HERO
        ======================================================= -->

        <section class="settings-hero glass-card">

            <div class="settings-hero-left">

                <div class="settings-hero-icon">

                    <i class="fa-solid fa-gear"></i>

                </div>

                <div class="settings-hero-text">

                    <h1>System Settings</h1>

                    <p>

                        Configure your BloodLink account,
                        notifications, security,
                        application preferences
                        and backup options.

                    </p>

                </div>

            </div>

        </section>

        <!-- ======================================================
             SETTINGS GRID
        ======================================================= -->

        <section class="settings-grid">

            <!-- ==================================================
                 PROFILE
            =================================================== -->

            <article
                class="settings-card glass-card">

                <div class="card-header">

                    <div>

                        <h2>My Profile</h2>

                        <p>

                            Personal information
                            and account details.

                        </p>

                    </div>

                    <i class="fa-solid fa-user card-icon"></i>

                </div>

                <div class="profile-wrapper">

                    <div class="profile-avatar-wrapper">

                        <img
                            id="profilePreview"
                            src="../assets/settings/profile.png"
                            alt="Profile">

                        <button
                            id="changePhoto"
                            class="camera-btn">

                            <i class="fa-solid fa-camera"></i>

                        </button>

                        <input
                            id="profileUpload"
                            type="file"
                            hidden>

                    </div>

                    <div class="profile-information">

                        <div class="detail-row">

                            <label>Full Name</label>

                            <span id="settingsFullName">

                                Loading...

                            </span>

                        </div>

                        <div class="detail-row">

                            <label>Email</label>

                            <span id="settingsEmail">

                                Loading...

                            </span>

                        </div>

                        <div class="detail-row">

                            <label>Employee ID</label>

                            <span id="settingsEmployeeId">

                                Loading...

                            </span>

                        </div>

                        <div class="detail-row">

                            <label>Role</label>

                            <span id="settingsRole">

                                Loading...

                            </span>

                        </div>

                        <button
                            id="editProfileBtn"
                            class="btn-primary">

                            <i class="fa-solid fa-pen"></i>

                            Edit Profile

                        </button>

                    </div>

                </div>

            </article>

            <!-- ==================================================
                 NOTIFICATIONS
            =================================================== -->

            <article
                class="settings-card glass-card">

                <div class="card-header">

                    <div>

                        <h2>Notifications</h2>

                        <p>

                            Configure notification
                            preferences.

                        </p>

                    </div>

                    <i class="fa-solid fa-bell card-icon"></i>

                </div>

                <div class="settings-list">

                    <div class="settings-item">

                        <span>Email Notifications</span>

                        <label class="switch">

                            <input
                                id="emailNotification"
                                type="checkbox"
                                checked>

                            <span class="slider"></span>

                        </label>

                    </div>

                    <div class="settings-item">

                        <span>Desktop Notifications</span>

                        <label class="switch">

                            <input
                                id="desktopNotification"
                                type="checkbox"
                                checked>

                            <span class="slider"></span>

                        </label>

                    </div>

                    <div class="settings-item">

                        <span>Blood Request Updates</span>

                        <label class="switch">

                            <input
                                id="requestUpdates"
                                type="checkbox"
                                checked>

                            <span class="slider"></span>

                        </label>

                    </div>

                    <div class="settings-item">

                        <span>Donation Reminder</span>

                        <label class="switch">

                            <input
                                id="pmReminder"
                                type="checkbox">

                            <span class="slider"></span>

                        </label>

                    </div>

                </div>

            </article>

            <!-- ==================================================
                 SECURITY
            =================================================== -->

            <article
                class="settings-card glass-card">

                <div class="card-header">

                    <div>

                        <h2>Security</h2>

                        <p>

                            Password,
                            authentication and
                            login protection.

                        </p>

                    </div>

                    <i class="fa-solid fa-shield-halved card-icon"></i>

                </div>

                <div class="settings-list">

                    <div class="settings-item">

                        <span>Change Password</span>

                        <button
                            id="changePassword"
                            class="btn-secondary">

                            Change

                        </button>

                    </div>

                    <div class="settings-item">

                        <span>Two Factor Authentication</span>

                        <label class="switch">

                            <input
                                id="twoFactor"
                                type="checkbox">

                            <span class="slider"></span>

                        </label>

                    </div>

                    <div class="settings-item">

                        <span>Active Sessions</span>

                        <button
                            id="viewSessions"
                            class="btn-secondary">

                            View

                        </button>

                    </div>

                </div>

            </article>

            <!-- ==================================================
                 PREFERENCES
            =================================================== -->

            <article
                class="settings-card glass-card">

                <div class="card-header">

                    <div>

                        <h2>Preferences</h2>

                        <p>

                            Application preferences.

                        </p>

                    </div>

                    <i class="fa-solid fa-sliders card-icon"></i>

                </div>

                <div class="settings-form">

                    <select id="themeSelect">

                        <option value="light">

                            Light Theme

                        </option>

                        <option value="dark">

                            Dark Theme

                        </option>

                    </select>

                    <select id="languageSelect">

                        <option>

                            English

                        </option>

                        <option>

                            Malayalam

                        </option>

                    </select>

                    <select id="dateFormat">

                        <option>

                            DD/MM/YYYY

                        </option>

                        <option>

                            MM/DD/YYYY

                        </option>

                    </select>

                    <select id="timeFormat">

                        <option>

                            24 Hour

                        </option>

                        <option>

                            12 Hour

                        </option>

                    </select>

                </div>

            </article>

            <!-- ==================================================
                 BACKUP
            =================================================== -->

            <article
                class="settings-card glass-card">

                <div class="card-header">

                    <div>

                        <h2>

                            Backup & Data

                        </h2>

                        <p>

                            Backup and export
                            BloodLink data.

                        </p>

                    </div>

                    <i class="fa-solid fa-database card-icon"></i>

                </div>

                <div class="backup-buttons">

                    <button
                        id="backupNow"
                        class="btn-primary">

                        Create Backup

                    </button>

                    <button
                        id="exportData"
                        class="btn-secondary">

                        Export Data

                    </button>

                </div>

            </article>

        </section>

        <div id="settingsToast"></div>

    </section>

    `;

}
/* ==========================================================
   Initialize Settings
========================================================== */

export function initializeSettings() {

    loadProfileData();

    initializeProfilePhoto();

    initializeNotificationSwitches();

    initializeSecurity();

    initializePreferences();

    initializeTheme();

    initializeBackup();

    loadSavedPreferences();

    initializeSmoothButtons();

    initializeButtonEffects();

    initializeCardEffects();

    initializeKeyboardShortcuts();

    showToast(

        "BloodLink",

        "Settings loaded successfully.",

        "fa-circle-check"

    );

}

/* ==========================================================
   Load Profile Data
========================================================== */

function loadProfileData() {

    const profile = {

        fullName:
            localStorage.getItem("username")
            || "Administrator",

        email:
            localStorage.getItem("email")
            || "admin@bloodlink.com",

        employeeId:
            localStorage.getItem("employee_id")
            || "EMP-001",

        role:
            localStorage.getItem("role")
            || "Administrator"

    };

    const fullName =
        document.getElementById("settingsFullName");

    const email =
        document.getElementById("settingsEmail");

    const employeeId =
        document.getElementById("settingsEmployeeId");

    const role =
        document.getElementById("settingsRole");

    if(fullName){

        fullName.textContent =
            profile.fullName;

    }

    if(email){

        email.textContent =
            profile.email;

    }

    if(employeeId){

        employeeId.textContent =
            profile.employeeId;

    }

    if(role){

        role.textContent =
            profile.role;

    }

}

/* ==========================================================
   Profile Photo
========================================================== */

function initializeProfilePhoto() {

    const upload =
        document.getElementById("profileUpload");

    const preview =
        document.getElementById("profilePreview");

    const camera =
        document.getElementById("changePhoto");

    if(
        !upload ||
        !preview ||
        !camera
    ){

        return;

    }

    camera.addEventListener("click", () => {

        upload.click();

    });

    upload.addEventListener("change", event => {

        const file =
            event.target.files[0];

        if(!file){

            return;

        }

        if(
            !file.type.startsWith("image/")
        ){

            showToast(

                "Invalid Image",

                "Please choose a valid image.",

                "fa-circle-xmark"

            );

            return;

        }

        const reader =
            new FileReader();

        reader.onload = e => {

            preview.src =
                e.target.result;

            localStorage.setItem(

                "settings-profile-photo",

                e.target.result

            );

            showToast(

                "Profile Updated",

                "Profile photo updated successfully.",

                "fa-circle-check"

            );

        };

        reader.readAsDataURL(file);

    });

    const savedPhoto =
        localStorage.getItem(
            "settings-profile-photo"
        );

    if(savedPhoto){

        preview.src =
            savedPhoto;

    }

}
/* ==========================================================
   Notification Switches
========================================================== */

function initializeNotificationSwitches() {

    const switches = [

        "emailNotification",

        "desktopNotification",

        "requestUpdates",

        "pmReminder"

    ];

    switches.forEach(id => {

        const element =
            document.getElementById(id);

        if (!element) return;

        const saved =
            localStorage.getItem(id);

        if (saved !== null) {

            element.checked =
                saved === "true";

        }

        element.addEventListener("change", () => {

            localStorage.setItem(

                id,

                element.checked

            );

            showToast(

                "Notification Updated",

                `${getSettingName(id)} ${element.checked ? "Enabled" : "Disabled"}.`,

                element.checked
                    ? "fa-circle-check"
                    : "fa-circle-minus"

            );

        });

    });

}

/* ==========================================================
   Setting Name
========================================================== */

function getSettingName(id){

    const names={

        emailNotification:
            "Email Notifications",

        desktopNotification:
            "Desktop Notifications",

        requestUpdates:
            "Blood Request Updates",

        pmReminder:
            "Donation Reminder"

    };

    return names[id] || "Setting";

}

/* ==========================================================
   Security
========================================================== */

function initializeSecurity(){

    const changePassword =
        document.getElementById("changePassword");

    const sessions =
        document.getElementById("viewSessions");

    const twoFactor =
        document.getElementById("twoFactor");

    if(changePassword){

        changePassword.addEventListener("click",()=>{

            showToast(

                "Security",

                "Password change feature will be available soon.",

                "fa-key"

            );

        });

    }

    if(sessions){

        sessions.addEventListener("click",()=>{

            showToast(

                "Active Sessions",

                "Loading active sessions...",

                "fa-laptop"

            );

        });

    }

    if(twoFactor){

        const saved =
            localStorage.getItem("twoFactor");

        if(saved!==null){

            twoFactor.checked =
                saved==="true";

        }

        twoFactor.addEventListener("change",()=>{

            localStorage.setItem(

                "twoFactor",

                twoFactor.checked

            );

            showToast(

                "Two Factor Authentication",

                twoFactor.checked

                    ? "Enabled."

                    : "Disabled.",

                twoFactor.checked

                    ? "fa-lock"

                    : "fa-lock-open"

            );

        });

    }

}

/* ==========================================================
   Preferences
========================================================== */

function initializePreferences(){

    saveDropdown("languageSelect");

    saveDropdown("dateFormat");

    saveDropdown("timeFormat");

}

/* ==========================================================
   Theme
========================================================== */

function initializeTheme(){

    const selector =
        document.getElementById("themeSelect");

    if(!selector){

        return;

    }

    const savedTheme =
        localStorage.getItem("bloodlink-theme");

    if(savedTheme){

        selector.value =
            savedTheme;

        applyTheme(savedTheme);

    }

    selector.addEventListener("change",()=>{

        localStorage.setItem(

            "bloodlink-theme",

            selector.value

        );

        applyTheme(

            selector.value

        );

    });

}

/* ==========================================================
   Apply Theme
========================================================== */

function applyTheme(theme){

    document.body.classList.remove(

        "dark-theme"

    );

    if(theme==="dark"){

        document.body.classList.add(

            "dark-theme"

        );

    }

    showToast(

        "Theme Updated",

        `${theme} theme applied.`,

        "fa-palette"

    );

}

/* ==========================================================
   Saved Dropdowns
========================================================== */

function saveDropdown(id){

    const dropdown =
        document.getElementById(id);

    if(!dropdown){

        return;

    }

    const saved =
        localStorage.getItem(id);

    if(saved){

        dropdown.value =
            saved;

    }

    dropdown.addEventListener("change",()=>{

        localStorage.setItem(

            id,

            dropdown.value

        );

        showToast(

            "Preference Saved",

            `${dropdown.value} selected.`,

            "fa-sliders"

        );

    });

}

/* ==========================================================
   Load Saved Preferences
========================================================== */

function loadSavedPreferences(){

    saveDropdown("languageSelect");

    saveDropdown("dateFormat");

    saveDropdown("timeFormat");

}
/* ==========================================================
   Backup & Export
========================================================== */

function initializeBackup(){

    const backupButton =
        document.getElementById("backupNow");

    const exportButton =
        document.getElementById("exportData");

    if(backupButton){

        backupButton.addEventListener("click",function(){

            const originalText =
                this.innerHTML;

            this.disabled = true;

            this.innerHTML = `

                <i class="fa-solid fa-spinner fa-spin"></i>

                Creating Backup...

            `;

            setTimeout(()=>{

                this.disabled = false;

                this.innerHTML =
                    originalText;

                showToast(

                    "Backup Complete",

                    "BloodLink backup created successfully.",

                    "fa-cloud-arrow-up"

                );

            },2500);

        });

    }

    if(exportButton){

        exportButton.addEventListener("click",()=>{

            showToast(

                "Export Started",

                "Preparing BloodLink data for export.",

                "fa-file-export"

            );

        });

    }

}

/* ==========================================================
   Smooth Button Ripple
========================================================== */

function initializeSmoothButtons(){

    document

        .querySelectorAll(

            ".btn-primary,.btn-secondary"

        )

        .forEach(button=>{

            button.addEventListener(

                "click",

                createRipple

            );

        });

}

function createRipple(event){

    const button =
        event.currentTarget;

    const ripple =
        document.createElement("span");

    const size =
        Math.max(

            button.clientWidth,

            button.clientHeight

        );

    const rect =
        button.getBoundingClientRect();

    ripple.className = "ripple";

    ripple.style.width =
        ripple.style.height =
            size + "px";

    ripple.style.left =
        event.clientX -
        rect.left -
        size / 2 + "px";

    ripple.style.top =
        event.clientY -
        rect.top -
        size / 2 + "px";

    button.appendChild(ripple);

    setTimeout(()=>{

        ripple.remove();

    },600);

}

/* ==========================================================
   Button Effects
========================================================== */

function initializeButtonEffects(){

    document.addEventListener(

        "click",

        event=>{

            const button =
                event.target.closest("button");

            if(!button){

                return;

            }

            button.style.transform =
                "scale(.97)";

            setTimeout(()=>{

                button.style.transform = "";

            },120);

        }

    );

}

/* ==========================================================
   Card Effects
========================================================== */

function initializeCardEffects(){

    document

        .querySelectorAll(

            ".settings-card"

        )

        .forEach(card=>{

            card.style.transition =
                ".30s ease";

            card.addEventListener(

                "mouseenter",

                ()=>{

                    card.style.transform =
                        "translateY(-5px)";

                }

            );

            card.addEventListener(

                "mouseleave",

                ()=>{

                    card.style.transform =
                        "translateY(0)";

                }

            );

        });

}

/* ==========================================================
   Keyboard Shortcuts
========================================================== */

function initializeKeyboardShortcuts(){

    document.addEventListener(

        "keydown",

        event=>{

            if(

                event.ctrlKey &&

                event.key.toLowerCase()==="s"

            ){

                event.preventDefault();

                showToast(

                    "Settings Saved",

                    "Your preferences have been saved.",

                    "fa-floppy-disk"

                );

            }

        }

    );

}

/* ==========================================================
   Toast
========================================================== */

function showToast(

    title,

    message,

    icon

){

    let toast =

        document.querySelector(

            ".settings-toast"

        );

    if(!toast){

        toast =

            document.createElement("div");

        toast.className =

            "settings-toast";

        document.body.appendChild(

            toast

        );

    }

    toast.innerHTML = `

        <i class="fa-solid ${icon}"></i>

        <div>

            <h4>${title}</h4>

            <p>${message}</p>

        </div>

    `;

    toast.classList.add(

        "show"

    );

    clearTimeout(

        window.settingsToastTimer

    );

    window.settingsToastTimer =

        setTimeout(()=>{

            toast.classList.remove(

                "show"

            );

        },3000);

}

/* ==========================================================
   BloodLink Settings Module
========================================================== */

console.log(

    "%cBloodLink Settings Module Loaded",

    "color:#2563EB;font-size:16px;font-weight:bold;"

);

console.log("Version : 1.0.0");

console.log("Status  : Ready");