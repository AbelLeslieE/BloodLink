/* ==========================================
   SETTINGS VIEW
========================================== */

function renderSettings() {

    pageContent.innerHTML = `

<section class="settings-page">



    <!-- ==========================================
         SETTINGS CONTENT
    =========================================== -->

    <section class="settings-content">

        <!-- Header -->

        <header class="page-header">

            <div>

                <h1>Settings</h1>

                <p>

                    Manage your profile,
                    notifications,
                    security and
                    system preferences.

                </p>

            </div>

            <div class="header-image">

                <img
                    src="/static/dashboard_v2/assets/settings/settings-banner.png"
                    alt="Settings Banner">

            </div>

        </header>

        <!-- Settings Grid -->

        <div class="settings-grid">
        <!-- ====================================
     PROFILE SETTINGS
==================================== -->

<section
    class="settings-card profile-card"
    id="profile">

    <div class="card-header">

        <div>

            <h2>Profile Settings</h2>

            <p>

                Update your personal information
                and account profile.

            </p>

        </div>

        <i data-lucide="user-round"
            class="card-icon"></i>

    </div>

    <div class="profile-content">

        <!-- Profile Image -->

        <div class="settings-profile-avatar">

        <img
            id="profilePreview"
            class="profile-image"
            src="/static/dashboard_v2/assets/settings/profile.png"
            alt="Profile Picture">

        <button
            class="camera-btn"
            id="changePhoto"
            type="button">

            <i data-lucide="camera"></i>

        </button>

        <input
            type="file"
            id="profileUpload"
            accept="image/*"
            hidden>

    </div>

        <!-- Profile Details -->

        <div class="profile-details">

            <div class="detail-row">

                <label>Full Name</label>

                <span id="settingsFullName">
                    Loading...
                </span>

            </div>

            <div class="detail-row">

                <label>Email Address</label>

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
                class="primary-btn edit-profile"
                id="editProfileBtn">

                <i data-lucide="square-pen"></i>

                Edit Profile

            </button>

        </div>

    </div>

</section>
<!-- ====================================
     NOTIFICATIONS
==================================== -->

<section
    class="settings-card notifications-card"
    id="notifications">

    <div class="card-header">

        <div>

            <h2>Notifications</h2>

            <p>

                Manage how you receive
                updates and alerts.

            </p>

        </div>

        <i
            data-lucide="bell"
            class="card-icon"></i>

    </div>

    <div class="notification-list">

        <!-- Email -->

        <div class="notification-item">

            <div class="notification-info">

                <div class="notification-icon">

                    <i data-lucide="mail"></i>

                </div>

                <div>

                    <h4>Email Notifications</h4>

                    <p>

                        Receive maintenance
                        updates through your
                        registered email.

                    </p>

                </div>

            </div>

            <label class="switch">

                <input
                    type="checkbox"
                    id="emailNotification"
                    checked>

                <span class="slider"></span>

            </label>

        </div>

        <!-- Desktop -->

        <div class="notification-item">

            <div class="notification-info">

                <div class="notification-icon">

                    <i data-lucide="monitor"></i>

                </div>

                <div>

                    <h4>Desktop Notifications</h4>

                    <p>

                        Show alerts directly
                        on your desktop.

                    </p>

                </div>

            </div>

            <label class="switch">

                <input
                    type="checkbox"
                    id="desktopNotification"
                    checked>

                <span class="slider"></span>

            </label>

        </div>

        <!-- Request Updates -->

        <div class="notification-item">

            <div class="notification-info">

                <div class="notification-icon">

                    <i data-lucide="send"></i>

                </div>

                <div>

                    <h4>Request Updates</h4>

                    <p>

                        Notify whenever a
                        service request changes
                        its status.

                    </p>

                </div>

            </div>

            <label class="switch">

                <input
                    type="checkbox"
                    id="requestUpdates"
                    checked>

                <span class="slider"></span>

            </label>

        </div>


        <!-- PM Reminder -->

        <div class="notification-item">

            <div class="notification-info">

                <div class="notification-icon">

                    <i data-lucide="calendar-check"></i>

                </div>

                <div>

                    <h4>Preventive Maintenance Reminder</h4>

                    <p>

                        Receive reminders before
                        scheduled preventive
                        maintenance.

                    </p>

                </div>

            </div>

            <label class="switch">

                <input
                    type="checkbox"
                    id="pmReminder">

                <span class="slider"></span>

            </label>

        </div>

    </div>

    <div class="card-footer">

        <button
            class="primary-btn"
            id="saveNotificationSettings">

            <i data-lucide="settings-2"></i>

            Configure Notifications

        </button>

    </div>

</section>
<!-- ====================================
     SECURITY
==================================== -->

<section
    class="settings-card security-card"
    id="security">

    <div class="card-header">

        <div>

            <h2>Security</h2>

            <p>

                Manage your password,
                account security and
                active sessions.

            </p>

        </div>

        <i
            data-lucide="shield-check"
            class="card-icon"></i>

    </div>

    <div class="security-list">

        <!-- Password -->

        <div class="security-item">

            <div>

                <h4>Password</h4>

                <p>••••••••••••</p>

            </div>

            <button
                class="secondary-btn"
                id="changePassword">

                Change

                <i data-lucide="chevron-right"></i>

            </button>

        </div>

        <!-- Two Factor -->

        <div class="security-item">

            <div>

                <h4>Two-Factor Authentication</h4>

                <p>

                    Add an extra layer
                    of security to
                    your BloodLink account.

                </p>

            </div>

            <label class="switch">

                <input
                    type="checkbox"
                    id="twoFactor">

                <span class="slider"></span>

            </label>

        </div>

        <!-- Active Sessions -->

        <div class="security-item">

            <div>

                <h4>Active Sessions</h4>

                <p>

                    Review all devices
                    currently logged into
                    your account.

                </p>

            </div>

            <button
                class="secondary-btn"
                id="viewSessions">

                View

                <i data-lucide="chevron-right"></i>

            </button>

        </div>

    </div>

</section>

<!-- ====================================
     SYSTEM PREFERENCES
==================================== -->

<section
    class="settings-card preferences-card"
    id="preferences">

    <div class="card-header">

        <div>

            <h2>System Preferences</h2>

            <p>

                Customize your
                BloodLink experience.

            </p>

        </div>

        <i
            data-lucide="sliders-horizontal"
            class="card-icon"></i>

    </div>

    <div class="preference-list">

        <!-- Theme -->

        <div class="preference-item">

            <div class="preference-left">

                <i data-lucide="sun-moon"></i>

                <span>Theme</span>

            </div>

            <select id="themeSelect">

                <option value="light" selected>
                    Light
                </option>

                <option value="dark">
                    Dark
                </option>

                <option value="system">
                    System Default
                </option>

            </select>

        </div>

        <!-- Language -->

        <div class="preference-item">

            <div class="preference-left">

                <i data-lucide="languages"></i>

                <span>Language</span>

            </div>

            <select id="languageSelect">

                <option value="english" selected>
                    English
                </option>

                <option value="malayalam">
                    Malayalam
                </option>

                <option value="hindi">
                    Hindi
                </option>

            </select>

        </div>

        <!-- Date Format -->

        <div class="preference-item">

            <div class="preference-left">

                <i data-lucide="calendar-days"></i>

                <span>Date Format</span>

            </div>

            <select id="dateFormat">

                <option selected>
                    DD/MM/YYYY
                </option>

                <option>
                    MM/DD/YYYY
                </option>

                <option>
                    YYYY-MM-DD
                </option>

            </select>

        </div>

        <!-- Time Format -->

        <div class="preference-item">

            <div class="preference-left">

                <i data-lucide="clock-3"></i>

                <span>Time Format</span>

            </div>

            <select id="timeFormat">

                <option selected>
                    24 Hour
                </option>

                <option>
                    12 Hour
                </option>

            </select>

        </div>

    </div>

</section>
<!-- ====================================
     BACKUP & DATA
==================================== -->

<section
    class="settings-card backup-card"
    id="backup">

    <div class="card-header">

        <div>

            <h2>Backup & Data</h2>

            <p>

                Secure your BloodLink information
                by creating backups or exporting
                maintenance data.

            </p>

        </div>

        <i
            data-lucide="database"
            class="card-icon"></i>

    </div>

    <div class="backup-actions">

        <!-- Backup -->

        <div class="backup-box">

            <div class="backup-icon">

                <i data-lucide="cloud-upload"></i>

            </div>

            <h4>Create Backup</h4>

            <p>

                Generate a complete backup
                of your BloodLink system.

            </p>

            <button
                class="primary-btn"
                id="backupNow">

                <i data-lucide="cloud-upload"></i>

                Backup Now

            </button>

        </div>

        <!-- Export -->

        <div class="backup-box">

            <div class="backup-icon">

                <i data-lucide="download"></i>

            </div>

            <h4>Export Data</h4>

            <p>

                Download reports,
                requests and maintenance
                records.

            </p>

            <button
                class="secondary-btn"
                id="exportData">

                <i data-lucide="download"></i>

                Export

            </button>

        </div>

    </div>

</section>

<!-- ====================================
     ABOUT SYSTEM
==================================== -->

<section
    class="settings-card about-card"
    id="about">

    <div class="card-header">

        <div>

            <h2>About System</h2>

            <p>

                Information about
                the BloodLink platform.

            </p>

        </div>

        <i
            data-lucide="info"
            class="card-icon"></i>

    </div>

    <div class="about-grid">

        <div class="about-item">

            <label>System Name</label>

            <span>
                BloodLink Biomedical Maintenance System
            </span>

        </div>

        <div class="about-item">

            <label>Version</label>

            <span id="systemVersion">

                Version 1.0.0

            </span>

        </div>

        <div class="about-item">

            <label>Developed By</label>

            <span>

                LFH Software Solutions

            </span>

        </div>

        <div class="about-item">

            <label>Support</label>

            <span>

                support@biotrack.com

            </span>

        </div>

    </div>

    <div class="about-footer">

        <p>

            © 2026 BloodLink Biomedical Maintenance System.
            All Rights Reserved.

        </p>

    </div>

</section>
        </div>

    </section>

</section>

`;

    // Re-create Lucide icons after injecting HTML
    if (window.lucide) {
        lucide.createIcons();
    }

    // Initialize page logic
    if (typeof initSettings === "function") {
        initSettings();
    }

}