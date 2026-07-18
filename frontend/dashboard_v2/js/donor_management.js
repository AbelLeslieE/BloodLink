// ==========================================================
// 1. IMPORT SHARED API SERVICE
// ==========================================================

import {
    authenticatedFetch
} from "./api.js";
// ==========================================================
// BLOODLINK - DONOR MANAGEMENT
// ==========================================================

const DONOR_API_URL = "/api/donors";

let donorRecords = [];


// ==========================================================
// DONOR MODULE TEMPLATE
// ==========================================================

function getDonorModuleTemplate() {

    return `
        <section class="donor-management">

            <div class="donor-management-content">

                <!-- ==========================================
                     HEADER
                =========================================== -->

                <header class="donor-header">

                    <div class="donor-heading">

                        <div class="donor-title-row">

                            <span class="donor-title-icon">
                                <i data-lucide="heart-pulse"></i>
                            </span>

                            <h1>Donor Management</h1>

                        </div>

                        <p>
                            Manage donor information, search donor records,
                            import and export data, and find matching donors.
                        </p>

                    </div>


                    <div class="donor-actions">

                        <button
                            type="button"
                            class="donor-action-btn"
                            id="findDonorMatchButton"
                        >
                            <i data-lucide="scan-search"></i>
                            Find Match
                        </button>


                        <button
                            type="button"
                            class="donor-action-btn import-btn"
                            id="importDonorsButton"
                        >
                            <i data-lucide="upload"></i>
                            Import Excel
                        </button>


                        <button
                            type="button"
                            class="donor-action-btn export-btn"
                            id="exportDonorsButton"
                        >
                            <i data-lucide="download"></i>
                            Export Excel
                        </button>


                        <button
                            type="button"
                            class="donor-action-btn primary"
                            id="addDonorButton"
                        >
                            <i data-lucide="plus"></i>
                            Add New Donor
                        </button>

                    </div>

                </header>


                <!-- ==========================================
                     KPI CARDS
                =========================================== -->

                <section class="donor-kpi-grid">

                    ${createKpiCard(
                        "users",
                        "Total Donors",
                        "totalDonorCount",
                        "0",
                        "All registered donors",
                        ""
                    )}

                    ${createKpiCard(
                        "droplet",
                        "Available Donors",
                        "availableDonorCount",
                        "0",
                        "Ready / available donors",
                        "available"
                    )}

                    ${createKpiCard(
                        "droplets",
                        "Blood Groups",
                        "bloodGroupCount",
                        "0",
                        "Registered blood groups",
                        "groups"
                    )}

                    ${createKpiCard(
                        "heart-handshake",
                        "Total Donations",
                        "totalDonationCount",
                        "0",
                        "Recorded donor contributions",
                        "donations"
                    )}

                    ${createKpiCard(
                        "user-plus",
                        "New Donors",
                        "newDonorCount",
                        "0",
                        "Added this month",
                        "new-donors"
                    )}

                </section>


                <!-- ==========================================
                     DATA PANEL
                =========================================== -->

                <section class="donor-data-panel">

                    <div class="donor-toolbar">

                        <label class="donor-search">

                            <i data-lucide="search"></i>

                            <input
                                type="search"
                                id="donorSearchInput"
                                placeholder="Search by name, phone, email, donor code..."
                            >

                        </label>


                        <div class="donor-filters">

                            <select
                                class="donor-filter-select"
                                id="donorBloodFilter"
                            >
                                <option value="">
                                    All Blood Groups
                                </option>

                                <option>A+</option>
                                <option>A-</option>
                                <option>B+</option>
                                <option>B-</option>
                                <option>AB+</option>
                                <option>AB-</option>
                                <option>O+</option>
                                <option>O-</option>

                            </select>


                            <select
                                class="donor-filter-select"
                                id="donorGenderFilter"
                            >
                                <option value="">
                                    All Genders
                                </option>

                                <option>Male</option>
                                <option>Female</option>
                                <option>Other</option>

                            </select>


                            <select
                                class="donor-filter-select"
                                id="donorStatusFilter"
                            >
                                <option value="">
                                    All Statuses
                                </option>

                                <option>Available</option>
                                <option>Unavailable</option>

                            </select>

                        </div>

                    </div>


                    <div class="donor-table-wrapper">

                        <table class="donor-table">

                            <thead>

                                <tr>
                                    <th>Donor ID</th>
                                    <th>Name</th>
                                    <th>Blood Group</th>
                                    <th>Gender</th>
                                    <th>Age</th>
                                    <th>Phone Number</th>
                                    <th>Email ID</th>
                                    <th>Last Donation</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>

                            </thead>


                            <tbody id="donorTableBody">

                                <tr>
                                    <td
                                        colspan="10"
                                        class="donor-table-message"
                                    >
                                        Loading donors...
                                    </td>
                                </tr>

                            </tbody>

                        </table>

                    </div>


                    <footer class="donor-table-footer">

                        <span id="donorTableSummary">
                            Showing 0 donors
                        </span>

                    </footer>

                                </section>

                    </div>


                    <!-- ==========================================
                        ADD DONOR MODAL
                    =========================================== -->

                    ${getAddDonorModalTemplate()}
                    <!-- ==========================================
                        VIEW DONOR MODAL
                    =========================================== -->

                    ${getViewDonorModalTemplate()}
                    <!-- ==========================================
                        EDIT DONOR MODAL
                    =========================================== -->

                    ${getEditDonorModalTemplate()}

                </section>
            `;
        }

// ==========================================================
// ADD DONOR MODAL TEMPLATE
// ==========================================================

function getAddDonorModalTemplate() {

    return `
        <div
            class="donor-modal-backdrop"
            id="addDonorModal"
            hidden
        >

            <section
                class="donor-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="addDonorModalTitle"
            >

                <!-- ======================================
                     MODAL HEADER
                ======================================= -->

                <header class="donor-modal-header">

                    <div>

                        <span class="donor-modal-eyebrow">
                            Donor Registration
                        </span>

                        <h2 id="addDonorModalTitle">
                            Add New Donor
                        </h2>

                        <p>
                            Register a new donor in the
                            Pranadan donor database.
                        </p>

                    </div>


                    <button
                        type="button"
                        class="donor-modal-close"
                        id="closeAddDonorModal"
                        aria-label="Close add donor form"
                    >
                        <i data-lucide="x"></i>
                    </button>

                </header>


                <!-- ======================================
                     FORM
                ======================================= -->

                <form
                    id="addDonorForm"
                    class="donor-form"
                    novalidate
                >

                    <div class="donor-modal-body">


                        <!-- ==============================
                             PERSONAL INFORMATION
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="user-round"></i>

                                <div>
                                    <h3>
                                        Personal Information
                                    </h3>

                                    <p>
                                        Basic donor identification
                                        and blood details.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>
                                        Full Name
                                        <strong>*</strong>
                                    </span>

                                    <input
                                        type="text"
                                        id="donorFullName"
                                        name="full_name"
                                        maxlength="200"
                                        autocomplete="name"
                                        required
                                    >

                                </label>


                                <label class="donor-form-field">

                                    <span>
                                        Blood Group
                                        <strong>*</strong>
                                    </span>

                                    <select
                                        id="donorBloodGroup"
                                        name="blood_group"
                                        required
                                    >
                                        <option value="">
                                            Select blood group
                                        </option>

                                        <option value="A+">A+</option>
                                        <option value="A-">A-</option>
                                        <option value="B+">B+</option>
                                        <option value="B-">B-</option>
                                        <option value="AB+">AB+</option>
                                        <option value="AB-">AB-</option>
                                        <option value="O+">O+</option>
                                        <option value="O-">O-</option>
                                    </select>

                                </label>


                                <label class="donor-form-field">

                                    <span>Gender</span>

                                    <select
                                        id="donorGender"
                                        name="gender"
                                    >
                                        <option value="">
                                            Select gender
                                        </option>

                                        <option value="Male">
                                            Male
                                        </option>

                                        <option value="Female">
                                            Female
                                        </option>

                                        <option value="Other">
                                            Other
                                        </option>
                                    </select>

                                </label>


                                <label class="donor-form-field">

                                    <span>Date of Birth</span>

                                    <input
                                        type="date"
                                        id="donorDateOfBirth"
                                        name="date_of_birth"
                                    >

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             CONTACT / COLLEGE
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="contact"></i>

                                <div>
                                    <h3>
                                        Contact & College
                                    </h3>

                                    <p>
                                        Contact information and
                                        academic details.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>Phone Number</span>

                                    <input
                                        type="tel"
                                        id="donorPhone"
                                        name="phone"
                                        maxlength="30"
                                        autocomplete="tel"
                                    >

                                </label>


                                <label class="donor-form-field">

                                    <span>Email ID</span>

                                    <input
                                        type="email"
                                        id="donorEmail"
                                        name="email"
                                        maxlength="255"
                                        autocomplete="email"
                                    >

                                </label>


                                <label
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>
                                        Class / Department
                                    </span>

                                    <input
                                        type="text"
                                        id="donorClassDepartment"
                                        name="class_department"
                                        maxlength="150"
                                    >

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             HEALTH INFORMATION
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="heart-pulse"></i>

                                <div>
                                    <h3>
                                        Health Information
                                    </h3>

                                    <p>
                                        Record the donor's current
                                        eligibility information.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>Weight (kg)</span>

                                    <input
                                        type="number"
                                        id="donorWeight"
                                        name="weight"
                                        min="0"
                                        step="0.01"
                                    >

                                </label>


                                <div
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>
                                        Hb above 12.5?
                                        <strong>*</strong>
                                    </span>

                                    <div class="donor-choice-group">

                                        <label>
                                            <input
                                                type="radio"
                                                name="hb_above_12_5"
                                                value="Yes"
                                                required
                                            >

                                            <span>Yes</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="hb_above_12_5"
                                                value="No"
                                            >

                                            <span>No</span>
                                        </label>

                                    </div>

                                </div>


                                <div class="donor-form-field">

                                    <span>
                                        Regular medication?
                                        <strong>*</strong>
                                    </span>

                                    <div class="donor-choice-group">

                                        <label>
                                            <input
                                                type="radio"
                                                name="regular_medication"
                                                value="Yes"
                                                required
                                            >

                                            <span>Yes</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="regular_medication"
                                                value="No"
                                            >

                                            <span>No</span>
                                        </label>

                                    </div>

                                </div>


                                <div class="donor-form-field">

                                    <span>
                                        BP level normal?
                                        <strong>*</strong>
                                    </span>

                                    <div class="donor-choice-group">

                                        <label>
                                            <input
                                                type="radio"
                                                name="bp_normal"
                                                value="Yes"
                                                required
                                            >

                                            <span>Yes</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="bp_normal"
                                                value="No"
                                            >

                                            <span>No</span>
                                        </label>

                                    </div>

                                </div>


                                <label
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>
                                        Medical Conditions / Notes
                                    </span>

                                    <textarea
                                        id="donorMedicalConditions"
                                        name="medical_conditions"
                                        rows="3"
                                    ></textarea>

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             LOCATION
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="map-pin"></i>

                                <div>
                                    <h3>Location</h3>

                                    <p>
                                        Optional location details
                                        for future donor matching.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>District</span>

                                    <input
                                        type="text"
                                        id="donorDistrict"
                                        name="district"
                                        maxlength="100"
                                    >

                                </label>


                                <label class="donor-form-field">

                                    <span>City</span>

                                    <input
                                        type="text"
                                        id="donorCity"
                                        name="city"
                                        maxlength="100"
                                    >

                                </label>


                                <label
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>Address</span>

                                    <textarea
                                        id="donorAddress"
                                        name="address"
                                        rows="3"
                                    ></textarea>

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             FORM MESSAGE
                        =============================== -->

                        <div
                            class="donor-form-message"
                            id="addDonorFormMessage"
                            role="alert"
                            hidden
                        ></div>

                    </div>


                    <!-- ==================================
                         FOOTER
                    =================================== -->

                    <footer class="donor-modal-footer">

                        <button
                            type="button"
                            class="donor-modal-btn secondary"
                            id="cancelAddDonorButton"
                        >
                            Cancel
                        </button>


                        <button
                            type="submit"
                            class="donor-modal-btn primary"
                            id="submitAddDonorButton"
                        >
                            <i data-lucide="user-plus"></i>

                            <span>
                                Add Donor
                            </span>
                        </button>

                    </footer>

                </form>

            </section>

        </div>
    `;

}
// ==========================================================
// VIEW DONOR MODAL TEMPLATE
// ==========================================================

function getViewDonorModalTemplate() {

    return `
        <div
            class="donor-modal-backdrop"
            id="viewDonorModal"
            hidden
        >

            <section
                class="donor-modal donor-view-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="viewDonorModalTitle"
            >

                <!-- ======================================
                     HEADER
                ======================================= -->

                <header class="donor-modal-header">

                    <div>

                        <span class="donor-modal-eyebrow">
                            Donor Profile
                        </span>

                        <h2 id="viewDonorModalTitle">
                            Donor Details
                        </h2>

                        <p>
                            Complete donor information stored
                            in Pranadan.
                        </p>

                    </div>


                    <button
                        type="button"
                        class="donor-modal-close"
                        id="closeViewDonorModal"
                        aria-label="Close donor details"
                    >
                        <i data-lucide="x"></i>
                    </button>

                </header>


                <!-- ======================================
                     BODY
                ======================================= -->

                <div
                    class="donor-modal-body"
                    id="viewDonorContent"
                >

                    <div class="donor-view-loading">

                        <i data-lucide="loader-circle"></i>

                        <span>
                            Loading donor information...
                        </span>

                    </div>

                </div>


                <!-- ======================================
                     FOOTER
                ======================================= -->

                <footer class="donor-modal-footer">

                    <button
                        type="button"
                        class="donor-modal-btn secondary"
                        id="closeViewDonorFooterButton"
                    >
                        Close
                    </button>

                </footer>

            </section>

        </div>
    `;

}
// ==========================================================
// EDIT DONOR MODAL TEMPLATE
// ==========================================================

function getEditDonorModalTemplate() {

    return `
        <div
            class="donor-modal-backdrop"
            id="editDonorModal"
            hidden
        >

            <section
                class="donor-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="editDonorModalTitle"
            >

                <header class="donor-modal-header">

                    <div>

                        <span class="donor-modal-eyebrow">
                            Donor Management
                        </span>

                        <h2 id="editDonorModalTitle">
                            Edit Donor
                        </h2>

                        <p id="editDonorDescription">
                            Update donor information stored
                            in Pranadan.
                        </p>

                    </div>

                    <button
                        type="button"
                        class="donor-modal-close"
                        id="closeEditDonorModal"
                        aria-label="Close edit donor form"
                    >
                        <i data-lucide="x"></i>
                    </button>

                </header>


                <form
                    id="editDonorForm"
                    class="donor-form"
                    novalidate
                >

                    <input
                        type="hidden"
                        id="editDonorId"
                    >


                    <div class="donor-modal-body">

                        <!-- ==============================
                             PERSONAL INFORMATION
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="user-round"></i>

                                <div>
                                    <h3>
                                        Personal Information
                                    </h3>

                                    <p>
                                        Update identification
                                        and blood details.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>
                                        Full Name
                                        <strong>*</strong>
                                    </span>

                                    <input
                                        type="text"
                                        name="full_name"
                                        maxlength="200"
                                        autocomplete="name"
                                        required
                                    >

                                </label>


                                <label class="donor-form-field">

                                    <span>
                                        Blood Group
                                        <strong>*</strong>
                                    </span>

                                    <select
                                        name="blood_group"
                                        required
                                    >
                                        <option value="">
                                            Select blood group
                                        </option>

                                        <option value="A+">A+</option>
                                        <option value="A-">A-</option>
                                        <option value="B+">B+</option>
                                        <option value="B-">B-</option>
                                        <option value="AB+">AB+</option>
                                        <option value="AB-">AB-</option>
                                        <option value="O+">O+</option>
                                        <option value="O-">O-</option>
                                    </select>

                                </label>


                                <label class="donor-form-field">

                                    <span>Gender</span>

                                    <select name="gender">

                                        <option value="">
                                            Select gender
                                        </option>

                                        <option value="Male">
                                            Male
                                        </option>

                                        <option value="Female">
                                            Female
                                        </option>

                                        <option value="Other">
                                            Other
                                        </option>

                                    </select>

                                </label>


                                <label class="donor-form-field">

                                    <span>Date of Birth</span>

                                    <input
                                        type="date"
                                        name="date_of_birth"
                                    >

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             CONTACT & COLLEGE
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="contact"></i>

                                <div>
                                    <h3>
                                        Contact & College
                                    </h3>

                                    <p>
                                        Update contact and
                                        academic information.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>Phone Number</span>

                                    <input
                                        type="tel"
                                        name="phone"
                                        maxlength="30"
                                        autocomplete="tel"
                                    >

                                </label>


                                <label class="donor-form-field">

                                    <span>Email ID</span>

                                    <input
                                        type="email"
                                        name="email"
                                        maxlength="255"
                                        autocomplete="email"
                                    >

                                </label>


                                <label
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>
                                        Class / Department
                                    </span>

                                    <input
                                        type="text"
                                        name="class_department"
                                        maxlength="150"
                                    >

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             HEALTH INFORMATION
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="heart-pulse"></i>

                                <div>
                                    <h3>
                                        Health Information
                                    </h3>

                                    <p>
                                        Update current donor
                                        eligibility information.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>Weight (kg)</span>

                                    <input
                                        type="number"
                                        name="weight"
                                        min="0"
                                        step="0.01"
                                    >

                                </label>


                                <div
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>
                                        Hb above 12.5?
                                        <strong>*</strong>
                                    </span>

                                    <div class="donor-choice-group">

                                        <label>
                                            <input
                                                type="radio"
                                                name="hb_above_12_5"
                                                value="Yes"
                                                required
                                            >
                                            <span>Yes</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="hb_above_12_5"
                                                value="No"
                                            >
                                            <span>No</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="hb_above_12_5"
                                                value="Not Recorded"
                                            >
                                            <span>
                                                Not Recorded
                                            </span>
                                        </label>

                                    </div>

                                </div>


                                <div class="donor-form-field">

                                    <span>
                                        Regular medication?
                                        <strong>*</strong>
                                    </span>

                                    <div class="donor-choice-group">

                                        <label>
                                            <input
                                                type="radio"
                                                name="regular_medication"
                                                value="Yes"
                                                required
                                            >
                                            <span>Yes</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="regular_medication"
                                                value="No"
                                            >
                                            <span>No</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="regular_medication"
                                                value="Not Recorded"
                                            >
                                            <span>
                                                Not Recorded
                                            </span>
                                        </label>

                                    </div>

                                </div>


                                <div class="donor-form-field">

                                    <span>
                                        BP level normal?
                                        <strong>*</strong>
                                    </span>

                                    <div class="donor-choice-group">

                                        <label>
                                            <input
                                                type="radio"
                                                name="bp_normal"
                                                value="Yes"
                                                required
                                            >
                                            <span>Yes</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="bp_normal"
                                                value="No"
                                            >
                                            <span>No</span>
                                        </label>

                                        <label>
                                            <input
                                                type="radio"
                                                name="bp_normal"
                                                value="Not Recorded"
                                            >
                                            <span>
                                                Not Recorded
                                            </span>
                                        </label>

                                    </div>

                                </div>


                                <label
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>
                                        Medical Conditions / Notes
                                    </span>

                                    <textarea
                                        name="medical_conditions"
                                        rows="3"
                                    ></textarea>

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             LOCATION
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="map-pin"></i>

                                <div>
                                    <h3>Location</h3>

                                    <p>
                                        Update donor location
                                        information.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>District</span>

                                    <input
                                        type="text"
                                        name="district"
                                        maxlength="100"
                                    >

                                </label>


                                <label class="donor-form-field">

                                    <span>City</span>

                                    <input
                                        type="text"
                                        name="city"
                                        maxlength="100"
                                    >

                                </label>


                                <label
                                    class="
                                        donor-form-field
                                        donor-form-field-wide
                                    "
                                >

                                    <span>Address</span>

                                    <textarea
                                        name="address"
                                        rows="3"
                                    ></textarea>

                                </label>

                            </div>

                        </section>


                        <!-- ==============================
                             DONOR STATUS
                        =============================== -->

                        <section class="donor-form-section">

                            <div class="donor-form-section-heading">

                                <i data-lucide="activity"></i>

                                <div>
                                    <h3>Donor Status</h3>

                                    <p>
                                        Update donor availability.
                                    </p>
                                </div>

                            </div>


                            <div class="donor-form-grid">

                                <label class="donor-form-field">

                                    <span>Status</span>

                                    <select name="status">

                                        <option value="Available">
                                            Available
                                        </option>

                                        <option value="Unavailable">
                                            Unavailable
                                        </option>

                                    </select>

                                </label>

                            </div>

                        </section>


                        <div
                            class="donor-form-message"
                            id="editDonorFormMessage"
                            role="alert"
                            hidden
                        ></div>

                    </div>


                    <footer class="donor-modal-footer">

                        <button
                            type="button"
                            class="donor-modal-btn secondary"
                            id="cancelEditDonorButton"
                        >
                            Cancel
                        </button>


                        <button
                            type="submit"
                            class="donor-modal-btn primary"
                            id="submitEditDonorButton"
                        >

                            <i data-lucide="save"></i>

                            <span>
                                Save Changes
                            </span>

                        </button>

                    </footer>

                </form>

            </section>

        </div>
    `;

}
// ==========================================================
// ADD DONOR MODAL
// ==========================================================

function openAddDonorModal() {

    const modal =
        document.getElementById(
            "addDonorModal"
        );

    const form =
        document.getElementById(
            "addDonorForm"
        );

    if (!modal) {
        return;
    }


    if (form) {
        form.reset();
    }


    clearAddDonorMessage();


    modal.hidden = false;

    document.body.classList.add(
        "donor-modal-open"
    );


    if (window.lucide) {
        window.lucide.createIcons();
    }


    window.requestAnimationFrame(
        () => {

            document
                .getElementById(
                    "donorFullName"
                )
                ?.focus();

        }
    );

}


function closeAddDonorModal() {

    const modal =
        document.getElementById(
            "addDonorModal"
        );

    if (!modal) {
        return;
    }


    modal.hidden = true;

    document.body.classList.remove(
        "donor-modal-open"
    );

}


// ==========================================================
// ADD DONOR FORM MESSAGE
// ==========================================================

function showAddDonorMessage(
    message,
    type = "error"
) {

    const messageElement =
        document.getElementById(
            "addDonorFormMessage"
        );

    if (!messageElement) {
        return;
    }


    messageElement.textContent =
        message;

    messageElement.className =
        `donor-form-message ${type}`;

    messageElement.hidden = false;

}


function clearAddDonorMessage() {

    const messageElement =
        document.getElementById(
            "addDonorFormMessage"
        );

    if (!messageElement) {
        return;
    }


    messageElement.textContent = "";

    messageElement.className =
        "donor-form-message";

    messageElement.hidden = true;

}


// ==========================================================
// OPTIONAL STRING NORMALIZATION
// ==========================================================

function optionalString(
    value
) {

    const normalized =
        String(value || "").trim();

    return normalized || null;

}


// ==========================================================
// BUILD DONOR PAYLOAD
// ==========================================================

function buildDonorPayload(
    form
) {

    const formData =
        new FormData(form);


    const weightValue =
        String(
            formData.get("weight") || ""
        ).trim();


    return {

        full_name:
            String(
                formData.get("full_name") || ""
            ).trim(),

        blood_group:
            String(
                formData.get("blood_group") || ""
            ).trim(),

        gender:
            optionalString(
                formData.get("gender")
            ),

        date_of_birth:
            optionalString(
                formData.get("date_of_birth")
            ),

        phone:
            optionalString(
                formData.get("phone")
            ),

        email:
            optionalString(
                formData.get("email")
            ),

        class_department:
            optionalString(
                formData.get(
                    "class_department"
                )
            ),

        district:
            optionalString(
                formData.get("district")
            ),

        city:
            optionalString(
                formData.get("city")
            ),

        address:
            optionalString(
                formData.get("address")
            ),

        weight:
            weightValue
                ? Number(weightValue)
                : null,

        hb_above_12_5:
            String(
                formData.get(
                    "hb_above_12_5"
                ) || ""
            ),

        regular_medication:
            String(
                formData.get(
                    "regular_medication"
                ) || ""
            ),

        bp_normal:
            String(
                formData.get(
                    "bp_normal"
                ) || ""
            ),

        medical_conditions:
            optionalString(
                formData.get(
                    "medical_conditions"
                )
            ),

    };

}


// ==========================================================
// VALIDATE ADD DONOR
// ==========================================================

function validateAddDonorPayload(
    donor
) {

    if (!donor.full_name) {

        return "Please enter the donor's full name.";

    }


    if (!donor.blood_group) {

        return "Please select a blood group.";

    }


    if (!donor.hb_above_12_5) {

        return "Please answer whether Hb is above 12.5.";

    }


    if (!donor.regular_medication) {

        return "Please answer the regular medication question.";

    }


    if (!donor.bp_normal) {

        return "Please answer whether BP level is normal.";

    }


    if (
        donor.weight !== null &&
        (
            !Number.isFinite(donor.weight) ||
            donor.weight <= 0
        )
    ) {

        return "Please enter a valid donor weight.";

    }


    return null;

}


// ==========================================================
// EXTRACT API ERROR
// ==========================================================

async function getApiErrorMessage(
    response
) {

    try {

        const errorData =
            await response.json();


        if (
            typeof errorData.detail ===
            "string"
        ) {

            return errorData.detail;

        }


        if (
            Array.isArray(
                errorData.detail
            )
        ) {

            return errorData.detail
                .map(
                    item =>
                        item.msg ||
                        "Invalid donor information."
                )
                .join(" ");

        }

    }
    catch (error) {

        console.error(
            "Unable to read donor API error:",
            error
        );

    }


    return (
        `Unable to add donor ` +
        `(${response.status}).`
    );

}


// ==========================================================
// SUBMIT ADD DONOR
// ==========================================================

async function handleAddDonorSubmit(
    event
) {

    event.preventDefault();


    const form =
        event.currentTarget;

    const submitButton =
        document.getElementById(
            "submitAddDonorButton"
        );


    clearAddDonorMessage();


    /*
       Run native browser validation first.

       This checks required fields, email format,
       numeric constraints, etc.
    */

    if (!form.checkValidity()) {

        form.reportValidity();

        return;

    }


    const donorPayload =
        buildDonorPayload(
            form
        );


    const validationError =
        validateAddDonorPayload(
            donorPayload
        );


    if (validationError) {

        showAddDonorMessage(
            validationError
        );

        return;

    }


    try {

        if (submitButton) {

            submitButton.disabled = true;

            submitButton.classList.add(
                "is-loading"
            );

            const buttonText =
                submitButton.querySelector(
                    "span"
                );

            if (buttonText) {
                buttonText.textContent =
                    "Adding Donor...";
            }

        }


        const response =
            await authenticatedFetch(
                DONOR_API_URL,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            donorPayload
                        ),
                }
            );


        /*
           A null response means authenticatedFetch()
           received 401 and already handled logout.
        */

        if (!response) {
            return;
        }


        if (!response.ok) {

            const errorMessage =
                await getApiErrorMessage(
                    response
                );


            showAddDonorMessage(
                errorMessage
            );

            return;

        }


        /*
           Consume the created donor response.
        */

        await response.json();


        closeAddDonorModal();


        /*
           Reload from the backend rather than manually
           pushing into donorRecords.

           This keeps the frontend synchronized with the
           database-generated donor code and timestamps.
        */

        await loadDonors();

    }
    catch (error) {

        console.error(
            "Unable to create donor:",
            error
        );


        showAddDonorMessage(
            "Unable to connect to the donor service. Please try again."
        );

    }
    finally {

        if (submitButton) {

            submitButton.disabled = false;

            submitButton.classList.remove(
                "is-loading"
            );


            const buttonText =
                submitButton.querySelector(
                    "span"
                );

            if (buttonText) {
                buttonText.textContent =
                    "Add Donor";
            }

        }

    }

}
// ==========================================================
// KPI TEMPLATE
// ==========================================================

function createKpiCard(
    icon,
    label,
    valueId,
    value,
    description,
    iconClass
) {

    return `
        <article class="donor-kpi-card">

            <div class="donor-kpi-top">

                <div class="donor-kpi-icon ${iconClass}">

                    <i data-lucide="${icon}"></i>

                </div>

                <div>

                    <div class="donor-kpi-label">
                        ${label}
                    </div>

                    <div
                        class="donor-kpi-value"
                        id="${valueId}"
                    >
                        ${value}
                    </div>

                </div>

            </div>

            <p class="donor-kpi-description">
                ${description}
            </p>

        </article>
    `;
}


// ==========================================================
// LOAD DONOR MODULE
// ==========================================================

export async function loadDonorManagement() {

    const moduleView = document.getElementById(
        "moduleView"
    );

    if (!moduleView) {
        return;
    }

    moduleView.innerHTML =
        getDonorModuleTemplate();

    if (window.lucide) {
        window.lucide.createIcons();
    }

    bindDonorEvents();

    await loadDonors();
}


// ==========================================================
// LOAD DONORS FROM API
// ==========================================================

async function loadDonors() {

    const tableBody = document.getElementById(
        "donorTableBody"
    );

    try {

        const response =
            await authenticatedFetch(
                DONOR_API_URL
            );


        // authenticatedFetch() returns null when the
        // backend responds with 401 Unauthorized.
        // It also handles session cleanup and redirects
        // the user back to the login page.
        if (!response) {
            return;
        }


        if (!response.ok) {

            throw new Error(
                `Unable to load donors (${response.status})`
            );

        }

        donorRecords = await response.json();

        updateDonorDashboard(
            donorRecords
        );

        applyDonorFilters();

    }
    catch (error) {

        console.error(
            "Donor loading failed:",
            error
        );

        if (tableBody) {

            tableBody.innerHTML = `
                <tr>
                    <td
                        colspan="10"
                        class="donor-table-message"
                    >
                        Unable to load donor records.
                    </td>
                </tr>
            `;

        }

    }

}


// ==========================================================
// RENDER DONOR TABLE
// ==========================================================

function renderDonorTable(
    donors
) {

    const tableBody = document.getElementById(
        "donorTableBody"
    );

    const summary = document.getElementById(
        "donorTableSummary"
    );

    if (!tableBody) {
        return;
    }


    if (!donors.length) {

        tableBody.innerHTML = `
            <tr>
                <td
                    colspan="10"
                    class="donor-table-message"
                >
                    No donor records found.
                </td>
            </tr>
        `;

        if (summary) {
            summary.textContent =
                "Showing 0 donors";
        }

        return;
    }


    tableBody.innerHTML = donors
        .map(createDonorRow)
        .join("");


    if (summary) {

        summary.textContent =
            `Showing ${donors.length} of ${donorRecords.length} donors`;

    }


    if (window.lucide) {
        window.lucide.createIcons();
    }

}


// ==========================================================
// CREATE DONOR ROW
// ==========================================================

function createDonorRow(
    donor
) {

    const age = calculateAge(
        donor.date_of_birth
    );

    const statusClass = getStatusClass(
        donor.status
    );

    return `
        <tr>

            <td>
                <span class="donor-code">
                    ${escapeHtml(donor.donor_code)}
                </span>
            </td>

            <td>
                <span class="donor-name">
                    ${escapeHtml(donor.full_name)}
                </span>
            </td>

            <td>
                <span class="blood-group-badge">
                    ${escapeHtml(donor.blood_group)}
                </span>
            </td>

            <td>
                ${displayValue(donor.gender)}
            </td>

            <td>
                ${age ?? "—"}
            </td>

            <td>
                ${displayValue(donor.phone)}
            </td>

            <td>
                ${displayValue(donor.email)}
            </td>

            <td>
                ${formatDate(donor.last_donation_date)}
            </td>

            <td>

                <span class="donor-status ${statusClass}">
                    ${escapeHtml(
                        donor.status || "Not Recorded"
                    )}
                </span>

            </td>

            <td>

                <div class="donor-row-actions">

                    <button
                        type="button"
                        class="donor-icon-btn"
                        data-donor-view="${donor.id}"
                        aria-label="View donor"
                    >
                        <i data-lucide="eye"></i>
                    </button>

                    <button
                        type="button"
                        class="donor-icon-btn"
                        data-donor-edit="${donor.id}"
                        aria-label="Edit donor"
                    >
                        <i data-lucide="pencil"></i>
                    </button>

                </div>

            </td>

        </tr>
    `;
}


// ==========================================================
// KPI CALCULATIONS
// ==========================================================

function updateDonorDashboard(
    donors
) {

    const totalDonors =
        donors.length;

    const availableDonors =
        donors.filter(
            donor =>
                String(donor.status)
                    .toLowerCase() ===
                "available"
        ).length;

    const bloodGroups =
        new Set(
            donors
                .map(
                    donor =>
                        donor.blood_group
                )
                .filter(Boolean)
        ).size;

    const totalDonations =
        donors.reduce(
            (total, donor) =>
                total +
                Number(
                    donor.total_donations || 0
                ),
            0
        );

    const currentDate =
        new Date();

    const newDonors =
        donors.filter(
            donor => {

                if (!donor.created_at) {
                    return false;
                }

                const createdDate =
                    new Date(
                        donor.created_at
                    );

                return (
                    createdDate.getMonth() ===
                        currentDate.getMonth()
                    &&
                    createdDate.getFullYear() ===
                        currentDate.getFullYear()
                );

            }
        ).length;


    setText(
        "totalDonorCount",
        totalDonors
    );

    setText(
        "availableDonorCount",
        availableDonors
    );

    setText(
        "bloodGroupCount",
        bloodGroups
    );

    setText(
        "totalDonationCount",
        totalDonations
    );

    setText(
        "newDonorCount",
        newDonors
    );

}


// ==========================================================
// SEARCH + FILTERS
// ==========================================================

function applyDonorFilters() {

    const searchValue =
        document
            .getElementById(
                "donorSearchInput"
            )
            ?.value
            .trim()
            .toLowerCase() || "";

    const bloodGroup =
        document
            .getElementById(
                "donorBloodFilter"
            )
            ?.value || "";

    const gender =
        document
            .getElementById(
                "donorGenderFilter"
            )
            ?.value || "";

    const status =
        document
            .getElementById(
                "donorStatusFilter"
            )
            ?.value || "";


    const filteredDonors =
        donorRecords.filter(
            donor => {

                const searchableText = [
                    donor.donor_code,
                    donor.full_name,
                    donor.phone,
                    donor.email,
                    donor.blood_group,
                    donor.class_department,
                    donor.city,
                    donor.district,
                ]
                    .filter(Boolean)
                    .join(" ")
                    .toLowerCase();


                const matchesSearch =
                    !searchValue ||
                    searchableText.includes(
                        searchValue
                    );


                const matchesBlood =
                    !bloodGroup ||
                    donor.blood_group ===
                        bloodGroup;


                const matchesGender =
                    !gender ||
                    donor.gender ===
                        gender;


                const matchesStatus =
                    !status ||
                    donor.status ===
                        status;


                return (
                    matchesSearch &&
                    matchesBlood &&
                    matchesGender &&
                    matchesStatus
                );

            }
        );


    renderDonorTable(
        filteredDonors
    );

}
// ==========================================================
// VIEW DONOR
// ==========================================================

async function openViewDonorModal(
    donorId
) {

    const modal =
        document.getElementById(
            "viewDonorModal"
        );

    const content =
        document.getElementById(
            "viewDonorContent"
        );


    if (!modal || !content) {
        return;
    }


    /*
       Open the modal immediately so the user receives
       visual feedback while donor information loads.
    */

    modal.hidden = false;

    document.body.classList.add(
        "donor-modal-open"
    );


    content.innerHTML = `
        <div class="donor-view-loading">

            <i data-lucide="loader-circle"></i>

            <span>
                Loading donor information...
            </span>

        </div>
    `;


    if (window.lucide) {
        window.lucide.createIcons();
    }


    try {

        const response =
            await authenticatedFetch(
                `${DONOR_API_URL}/${donorId}`
            );


        if (!response) {
            return;
        }


        if (!response.ok) {

            throw new Error(
                `Unable to load donor (${response.status})`
            );

        }


        const donor =
            await response.json();


        renderViewDonor(
            donor
        );

    }
    catch (error) {

        console.error(
            "Unable to load donor details:",
            error
        );


        content.innerHTML = `
            <div class="donor-view-error">

                <i data-lucide="triangle-alert"></i>

                <strong>
                    Unable to load donor information.
                </strong>

                <span>
                    Please close this window and try again.
                </span>

            </div>
        `;


        if (window.lucide) {
            window.lucide.createIcons();
        }

    }

}


// ==========================================================
// CLOSE VIEW DONOR
// ==========================================================

function closeViewDonorModal() {

    const modal =
        document.getElementById(
            "viewDonorModal"
        );


    if (!modal) {
        return;
    }


    modal.hidden = true;


    /*
       Only remove scroll locking if the Add Donor
       modal is also closed.
    */

    const addModal =
        document.getElementById(
            "addDonorModal"
        );


    if (
        !addModal ||
        addModal.hidden
    ) {

        document.body.classList.remove(
            "donor-modal-open"
        );

    }

}
// ==========================================================
// RENDER VIEW DONOR
// ==========================================================

function renderViewDonor(
    donor
) {

    const content =
        document.getElementById(
            "viewDonorContent"
        );


    if (!content) {
        return;
    }


    const age =
        calculateAge(
            donor.date_of_birth
        );


    const statusClass =
        getStatusClass(
            donor.status
        );


    content.innerHTML = `

        <!-- ==============================================
             DONOR IDENTITY
        =============================================== -->

        <section class="donor-profile-hero">

            <div class="donor-profile-avatar">

                <i data-lucide="user-round"></i>

            </div>


            <div class="donor-profile-main">

                <span class="donor-profile-code">
                    ${displayValue(donor.donor_code)}
                </span>

                <h3>
                    ${displayValue(donor.full_name)}
                </h3>

                <div class="donor-profile-badges">

                    <span class="blood-group-badge">
                        ${displayValue(donor.blood_group)}
                    </span>

                    <span
                        class="
                            donor-status
                            ${statusClass}
                        "
                    >
                        ${displayValue(
                            donor.status
                        )}
                    </span>

                </div>

            </div>

        </section>


        <!-- ==============================================
             PERSONAL INFORMATION
        =============================================== -->

        ${createDonorDetailSection(
            "user-round",
            "Personal Information",
            [
                [
                    "Full Name",
                    displayValue(
                        donor.full_name
                    )
                ],

                [
                    "Gender",
                    displayValue(
                        donor.gender
                    )
                ],

                [
                    "Date of Birth",
                    formatDate(
                        donor.date_of_birth
                    )
                ],

                [
                    "Age",
                    age !== null
                        ? `${age} years`
                        : "—"
                ],

                [
                    "Blood Group",
                    displayValue(
                        donor.blood_group
                    )
                ],

                [
                    "Weight",
                    donor.weight
                        ? `${escapeHtml(
                            donor.weight
                        )} kg`
                        : "—"
                ],
            ]
        )}


        <!-- ==============================================
             CONTACT / COLLEGE
        =============================================== -->

        ${createDonorDetailSection(
            "contact",
            "Contact & College",
            [
                [
                    "Phone Number",
                    displayValue(
                        donor.phone
                    )
                ],

                [
                    "Email ID",
                    displayValue(
                        donor.email
                    )
                ],

                [
                    "Class / Department",
                    displayValue(
                        donor.class_department
                    )
                ],
            ]
        )}


        <!-- ==============================================
             HEALTH INFORMATION
        =============================================== -->

        ${createDonorDetailSection(
            "heart-pulse",
            "Health Information",
            [
                [
                    "Hb Above 12.5",
                    healthDisplayValue(
                        donor.hb_above_12_5
                    )
                ],

                [
                    "Regular Medication",
                    healthDisplayValue(
                        donor.regular_medication
                    )
                ],

                [
                    "BP Level Normal",
                    healthDisplayValue(
                        donor.bp_normal
                    )
                ],

                [
                    "Medical Conditions",
                    displayValue(
                        donor.medical_conditions
                    )
                ],
            ]
        )}


        <!-- ==============================================
             LOCATION
        =============================================== -->

        ${createDonorDetailSection(
            "map-pin",
            "Location",
            [
                [
                    "District",
                    displayValue(
                        donor.district
                    )
                ],

                [
                    "City",
                    displayValue(
                        donor.city
                    )
                ],

                [
                    "Address",
                    displayValue(
                        donor.address
                    )
                ],
            ]
        )}


        <!-- ==============================================
             DONATION INFORMATION
        =============================================== -->

        ${createDonorDetailSection(
            "heart-handshake",
            "Donation Information",
            [
                [
                    "Last Donation",
                    formatDate(
                        donor.last_donation_date
                    )
                ],

                [
                    "Total Donations",
                    escapeHtml(
                        donor.total_donations ?? 0
                    )
                ],

                [
                    "Current Status",
                    displayValue(
                        donor.status
                    )
                ],
            ]
        )}


        <!-- ==============================================
             RECORD INFORMATION
        =============================================== -->

        ${createDonorDetailSection(
            "database",
            "Record Information",
            [
                [
                    "Donor ID",
                    displayValue(
                        donor.donor_code
                    )
                ],

                [
                    "Registered",
                    formatDateTime(
                        donor.created_at
                    )
                ],

                [
                    "Last Updated",
                    formatDateTime(
                        donor.updated_at
                    )
                ],
            ]
        )}

    `;


    if (window.lucide) {
        window.lucide.createIcons();
    }

}
// ==========================================================
// DONOR DETAIL SECTION TEMPLATE
// ==========================================================

function createDonorDetailSection(
    icon,
    title,
    fields
) {

    const fieldMarkup =
        fields
            .map(
                ([label, value]) => `
                    <div class="donor-detail-item">

                        <span class="donor-detail-label">
                            ${escapeHtml(label)}
                        </span>

                        <div class="donor-detail-value">
                            ${value}
                        </div>

                    </div>
                `
            )
            .join("");


    return `
        <section class="donor-detail-section">

            <div class="donor-form-section-heading">

                <i data-lucide="${icon}"></i>

                <div>
                    <h3>
                        ${escapeHtml(title)}
                    </h3>
                </div>

            </div>


            <div class="donor-detail-grid">
                ${fieldMarkup}
            </div>

        </section>
    `;

}


// ==========================================================
// HEALTH DISPLAY VALUE
// ==========================================================

function healthDisplayValue(
    value
) {

    if (!value) {
        return "Not Recorded";
    }


    return escapeHtml(
        String(value)
    );

}


// ==========================================================
// DATE + TIME FORMAT
// ==========================================================

function formatDateTime(
    dateValue
) {

    if (!dateValue) {
        return "—";
    }


    const date =
        new Date(
            dateValue
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "—";

    }


    return date.toLocaleString(
        "en-GB",
        {
            day: "2-digit",
            month: "short",
            year: "numeric",

            hour: "2-digit",
            minute: "2-digit",
        }
    );

}
// ==========================================================
// OPEN EDIT DONOR
// ==========================================================

async function openEditDonorModal(
    donorId
) {

    const modal =
        document.getElementById(
            "editDonorModal"
        );

    const form =
        document.getElementById(
            "editDonorForm"
        );

    if (!modal || !form) {
        return;
    }


    form.reset();

    clearEditDonorMessage();


    modal.hidden = false;

    document.body.classList.add(
        "donor-modal-open"
    );


    try {

        const response =
            await authenticatedFetch(
                `${DONOR_API_URL}/${donorId}`
            );


        if (!response) {
            return;
        }


        if (!response.ok) {

            throw new Error(
                `Unable to load donor (${response.status})`
            );

        }


        const donor =
            await response.json();


        populateEditDonorForm(
            donor
        );


        if (window.lucide) {
            window.lucide.createIcons();
        }

    }
    catch (error) {

        console.error(
            "Unable to load donor for editing:",
            error
        );


        showEditDonorMessage(
            "Unable to load donor information."
        );

    }

}


// ==========================================================
// POPULATE EDIT FORM
// ==========================================================

function populateEditDonorForm(
    donor
) {

    const form =
        document.getElementById(
            "editDonorForm"
        );


    if (!form) {
        return;
    }


    document.getElementById(
        "editDonorId"
    ).value = donor.id;


    const description =
        document.getElementById(
            "editDonorDescription"
        );


    if (description) {

        description.textContent =
            `Editing ${
                donor.donor_code ||
                "donor record"
            }`;

    }


    setFormValue(
        form,
        "full_name",
        donor.full_name
    );

    setFormValue(
        form,
        "blood_group",
        donor.blood_group
    );

    setFormValue(
        form,
        "gender",
        donor.gender
    );

    setFormValue(
        form,
        "date_of_birth",
        donor.date_of_birth
    );

    setFormValue(
        form,
        "phone",
        donor.phone
    );

    setFormValue(
        form,
        "email",
        donor.email
    );

    setFormValue(
        form,
        "class_department",
        donor.class_department
    );

    setFormValue(
        form,
        "weight",
        donor.weight
    );

    setRadioValue(
        form,
        "hb_above_12_5",
        donor.hb_above_12_5
    );

    setRadioValue(
        form,
        "regular_medication",
        donor.regular_medication
    );

    setRadioValue(
        form,
        "bp_normal",
        donor.bp_normal
    );

    setFormValue(
        form,
        "medical_conditions",
        donor.medical_conditions
    );

    setFormValue(
        form,
        "district",
        donor.district
    );

    setFormValue(
        form,
        "city",
        donor.city
    );

    setFormValue(
        form,
        "address",
        donor.address
    );

    setFormValue(
        form,
        "status",
        donor.status || "Available"
    );

}


// ==========================================================
// EDIT FORM HELPERS
// ==========================================================

function setFormValue(
    form,
    fieldName,
    value
) {

    const field =
        form.elements.namedItem(
            fieldName
        );


    if (!field) {
        return;
    }


    field.value =
        value ?? "";

}


function setRadioValue(
    form,
    fieldName,
    value
) {

    const radio =
        form.querySelector(
            `input[name="${fieldName}"][value="${CSS.escape(
                value || "Not Recorded"
            )}"]`
        );


    if (radio) {
        radio.checked = true;
    }

}


// ==========================================================
// CLOSE EDIT DONOR
// ==========================================================

function closeEditDonorModal() {

    const modal =
        document.getElementById(
            "editDonorModal"
        );


    if (!modal) {
        return;
    }


    modal.hidden = true;

    document.body.classList.remove(
        "donor-modal-open"
    );

}


// ==========================================================
// EDIT MESSAGE
// ==========================================================

function showEditDonorMessage(
    message,
    type = "error"
) {

    const element =
        document.getElementById(
            "editDonorFormMessage"
        );


    if (!element) {
        return;
    }


    element.textContent = message;

    element.className =
        `donor-form-message ${type}`;

    element.hidden = false;

}


function clearEditDonorMessage() {

    const element =
        document.getElementById(
            "editDonorFormMessage"
        );


    if (!element) {
        return;
    }


    element.textContent = "";

    element.className =
        "donor-form-message";

    element.hidden = true;

}
// ==========================================================
// EVENT BINDINGS
// ==========================================================

// ==========================================================
// EVENT BINDINGS
// ==========================================================

function bindDonorEvents() {

    // ======================================================
    // SEARCH
    // ======================================================

    document
        .getElementById("donorSearchInput")
        ?.addEventListener(
            "input",
            applyDonorFilters
        );


    // ======================================================
    // FILTERS
    // ======================================================

    [
        "donorBloodFilter",
        "donorGenderFilter",
        "donorStatusFilter",
    ].forEach(filterId => {

        document
            .getElementById(filterId)
            ?.addEventListener(
                "change",
                applyDonorFilters
            );

    });


    // ======================================================
    // DONOR TABLE ACTIONS
    // ======================================================

    document
        .getElementById("donorTableBody")
        ?.addEventListener(
            "click",
            event => {

                // -----------------------------
                // VIEW DONOR
                // -----------------------------

                const viewButton =
                    event.target.closest(
                        "[data-donor-view]"
                    );

                if (viewButton) {

                    const donorId =
                        Number(
                            viewButton.dataset.donorView
                        );

                    if (
                        Number.isInteger(donorId) &&
                        donorId > 0
                    ) {

                        openViewDonorModal(
                            donorId
                        );

                    }

                    return;

                }


                // -----------------------------
                // EDIT DONOR
                // -----------------------------

                const editButton =
                    event.target.closest(
                        "[data-donor-edit]"
                    );

                if (editButton) {

                    const donorId =
                        Number(
                            editButton.dataset.donorEdit
                        );

                    if (
                        Number.isInteger(donorId) &&
                        donorId > 0
                    ) {

                        openEditDonorModal(
                            donorId
                        );

                    }

                }

            }
        );


    // ======================================================
    // VIEW DONOR EVENTS
    // ======================================================

    document
        .getElementById("closeViewDonorModal")
        ?.addEventListener(
            "click",
            closeViewDonorModal
        );


    document
        .getElementById("closeViewDonorFooterButton")
        ?.addEventListener(
            "click",
            closeViewDonorModal
        );


    document
        .getElementById("viewDonorModal")
        ?.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    event.currentTarget
                ) {

                    closeViewDonorModal();

                }

            }
        );


    // ======================================================
    // ADD DONOR EVENTS
    // ======================================================

    document
        .getElementById("addDonorButton")
        ?.addEventListener(
            "click",
            openAddDonorModal
        );


    document
        .getElementById("closeAddDonorModal")
        ?.addEventListener(
            "click",
            closeAddDonorModal
        );


    document
        .getElementById("cancelAddDonorButton")
        ?.addEventListener(
            "click",
            closeAddDonorModal
        );


    document
        .getElementById("addDonorForm")
        ?.addEventListener(
            "submit",
            handleAddDonorSubmit
        );


    document
        .getElementById("addDonorModal")
        ?.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    event.currentTarget
                ) {

                    closeAddDonorModal();

                }

            }
        );


    // ======================================================
    // EDIT DONOR EVENTS
    // ======================================================

    document
        .getElementById("closeEditDonorModal")
        ?.addEventListener(
            "click",
            closeEditDonorModal
        );


    document
        .getElementById("cancelEditDonorButton")
        ?.addEventListener(
            "click",
            closeEditDonorModal
        );


    document
        .getElementById("editDonorForm")
        ?.addEventListener(
            "submit",
            handleEditDonorSubmit
        );


    document
        .getElementById("editDonorModal")
        ?.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    event.currentTarget
                ) {

                    closeEditDonorModal();

                }

            }
        );

}

// ==========================================================
// HELPERS
// ==========================================================

function calculateAge(
    dateOfBirth
) {

    if (!dateOfBirth) {
        return null;
    }

    const birthDate =
        new Date(dateOfBirth);

    const today =
        new Date();

    let age =
        today.getFullYear() -
        birthDate.getFullYear();

    const monthDifference =
        today.getMonth() -
        birthDate.getMonth();

    if (
        monthDifference < 0 ||
        (
            monthDifference === 0 &&
            today.getDate() <
                birthDate.getDate()
        )
    ) {
        age--;
    }

    return age;
}


function formatDate(
    dateValue
) {

    if (!dateValue) {
        return "—";
    }

    const date =
        new Date(dateValue);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {
        return "—";
    }

    return date.toLocaleDateString(
        "en-GB",
        {
            day: "2-digit",
            month: "short",
            year: "numeric",
        }
    );

}


function getStatusClass(
    status
) {

    const normalized =
        String(status || "")
            .toLowerCase();

    if (normalized === "available") {
        return "available";
    }

    if (normalized === "unavailable") {
        return "unavailable";
    }

    return "other";
}


function displayValue(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    return escapeHtml(
        String(value)
    );
}


function setText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );

    if (element) {
        element.textContent = value;
    }

}


function escapeHtml(
    value
) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
// ==========================================================
// DONOR MODULE NAVIGATION
// ==========================================================

window.addEventListener(
    "bloodlink:navigate",
    async (event) => {

        const page = event.detail?.page;

        // Only handle the Donors navigation here.
        if (page !== "donors") {
            return;
        }

        const dashboardView =
            document.getElementById(
                "dashboardView"
            );

        const moduleView =
            document.getElementById(
                "moduleView"
            );


        // Hide the main dashboard.
        if (dashboardView) {
            dashboardView.hidden = true;
        }


        // Show the dynamic module area.
        if (moduleView) {
            moduleView.hidden = false;
        }


        // Render and load real donor data.
        await loadDonorManagement();

    }
);
// ==========================================================
// SUBMIT EDIT DONOR
// ==========================================================

async function handleEditDonorSubmit(
    event
) {

    event.preventDefault();


    const form =
        event.currentTarget;

    const donorId =
        Number(
            document.getElementById(
                "editDonorId"
            )?.value
        );

    const submitButton =
        document.getElementById(
            "submitEditDonorButton"
        );


    clearEditDonorMessage();


    if (
        !Number.isInteger(donorId) ||
        donorId <= 0
    ) {

        showEditDonorMessage(
            "Invalid donor record."
        );

        return;

    }


    if (!form.checkValidity()) {

        form.reportValidity();

        return;

    }


    /*
       Reuse the same payload builder used
       by Add Donor.
    */

    const donorPayload =
        buildDonorPayload(
            form
        );


    /*
       Status exists only in the Edit form,
       so add it separately.
    */

    donorPayload.status =
        form.elements.namedItem(
            "status"
        )?.value || "Available";


    const validationError =
        validateAddDonorPayload(
            donorPayload
        );


    if (validationError) {

        showEditDonorMessage(
            validationError
        );

        return;

    }


    try {

        if (submitButton) {

            submitButton.disabled = true;


            const text =
                submitButton.querySelector(
                    "span"
                );


            if (text) {

                text.textContent =
                    "Saving...";

            }

        }


        const response =
            await authenticatedFetch(
                `${DONOR_API_URL}/${donorId}`,
                {
                    method: "PATCH",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            donorPayload
                        ),
                }
            );


        if (!response) {
            return;
        }


        if (!response.ok) {

            const errorMessage =
                await getApiErrorMessage(
                    response
                );


            showEditDonorMessage(
                errorMessage
            );

            return;

        }


        await response.json();


        closeEditDonorModal();


        /*
           Reload authoritative data from backend.

           This automatically refreshes:
           - donor table
           - status
           - search data
           - filters
           - KPI calculations
        */

        await loadDonors();

    }
    catch (error) {

        console.error(
            "Unable to update donor:",
            error
        );


        showEditDonorMessage(
            "Unable to update donor. Please try again."
        );

    }
    finally {

        if (submitButton) {

            submitButton.disabled = false;


            const text =
                submitButton.querySelector(
                    "span"
                );


            if (text) {

                text.textContent =
                    "Save Changes";

            }

        }

    }

}