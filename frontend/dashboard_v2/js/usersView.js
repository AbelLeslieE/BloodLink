/* ==========================================================
   BloodLink - Users Module
   File: users.js
========================================================== */

import { authenticatedFetch } from "./api.js";

let usersCache = [];

let editingUserId = null;

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[character]));
}

/* ==========================================================
   PAGE TEMPLATE
========================================================== */
/* ==========================================================
   Users Page Template
========================================================== */

export function loadUsers() {

    return `

    <section class="users-page">

        <!-- ======================================================
             HERO
        ======================================================= -->

        <section class="users-hero glass-card">

            <div class="users-hero-left">

                <div class="users-hero-icon">

                    <i class="fa-solid fa-users"></i>

                </div>

                <div class="users-hero-text">

                    <h1>User Management</h1>

                    <p>
                        Manage BloodLink users, volunteers, staff, and administrator access.
                    </p>

                </div>

            </div>

        </section>

        <!-- ======================================================
             KPI CARDS
        ======================================================= -->

        <section class="users-kpi-grid">

            <article class="users-kpi-card glass-card">

                <div class="users-kpi-icon blue">

                    <i class="fa-solid fa-users"></i>

                </div>

                <div class="users-kpi-content">

                    <span>Total Users</span>

                    <h2 id="kpiUsers">

                        0

                    </h2>

                    <small class="positive">

                        <i class="fa-solid fa-arrow-up"></i>

                        Registered users

                    </small>

                </div>

            </article>

            <article class="users-kpi-card glass-card">

                <div class="users-kpi-icon green">

                    <i class="fa-solid fa-user-check"></i>

                </div>

                <div class="users-kpi-content">

                    <span>Active Users</span>

                    <h2 id="kpiActiveUsers">

                        0

                    </h2>

                    <small class="positive">

                        <i class="fa-solid fa-circle-check"></i>

                        Active accounts

                    </small>

                </div>

            </article>

            <article class="users-kpi-card glass-card">

                <div class="users-kpi-icon red">

                    <i class="fa-solid fa-user-shield"></i>

                </div>

                <div class="users-kpi-content">

                    <span>Administrators</span>

                    <h2 id="kpiAdmins">

                        0

                    </h2>

                    <small>

                        System administrators

                    </small>

                </div>

            </article>

            <article class="users-kpi-card glass-card">

                <div class="users-kpi-icon orange">

                    <i class="fa-solid fa-building"></i>

                </div>

                <div class="users-kpi-content">

                    <span>Departments</span>

                    <h2 id="kpiDepartments">

                        0

                    </h2>

                    <small>

                        Registered departments

                    </small>

                </div>

            </article>

        </section>

        <!-- ======================================================
             FILTER BAR
        ======================================================= -->

        <section class="users-filter glass-card">

            <div class="users-search">

                <i class="fa-solid fa-magnifying-glass"></i>

                <input
                    id="userSearch"
                    type="text"
                    placeholder="Search users..."
                >

            </div>

            <select id="roleFilter">

                <option value="">
                    All Roles
                </option>

            </select>

            <button
                id="registerUserButton"
                class="btn-primary">

                <i class="fa-solid fa-plus"></i>

                Add User

            </button>

        </section>

        <!-- ======================================================
             CONTENT GRID
        ======================================================= -->

        <section class="users-layout">

            <!-- LEFT -->

            <div class="users-main glass-card">

                <div class="section-title">

                    <h2>User Directory</h2>

                </div>

                <div class="users-table-wrapper" tabindex="0" role="region" aria-label="User directory table. Scroll horizontally to view all columns.">

                    <table class="users-table">

                        <thead>

                            <tr>

                                <th>Name</th>

                                <th>Department</th>

                                <th>Role</th>

                                <th>Email</th>

                                <th>Phone</th>

                                <th>Actions</th>

                            </tr>

                        </thead>

                        <tbody id="usersBody">

                        </tbody>

                    </table>

                </div>

            </div>

            <!-- RIGHT -->

            <aside class="users-sidebar">

                <div class="glass-card">

                    <div class="sidebar-title">

                        <h3>User Summary</h3>

                    </div>

                    <div id="usersSummary">

                    </div>

                </div>

                <div class="glass-card">

                    <div class="sidebar-title">

                        <h3>Recent Users</h3>

                    </div>

                    <div id="recentUsers">

                    </div>

                </div>

                <div class="glass-card donor-registration-card">

                    <div class="sidebar-title"><h3>Donor registration QR</h3></div>
                    <p>Display this code so donors can register their own portal account.</p>
                    <img id="donorRegistrationQr" alt="QR code for BloodLink donor registration">
                    <a href="/donor-register" target="_blank" rel="noopener">Open registration page</a>

                </div>

            </aside>

        </section>

        <!-- ======================================================
             MODAL
        ======================================================= -->

        <div id="userModal"></div>

    </section>

    `;

}

/* ==========================================================
   INITIALIZER
========================================================== */

export function initializeUsers() {

    document
        .getElementById("registerUserButton")
        ?.addEventListener(
            "click",
            showRegisterUser
        );

    document
        .getElementById("userSearch")
        ?.addEventListener(
            "keyup",
            filterUsers
        );

    document
        .getElementById("roleFilter")
        ?.addEventListener(
            "change",
            filterUsers
        );

    loadUsersData();
    loadDonorRegistrationQr();

}

async function loadDonorRegistrationQr() {
    const image = document.getElementById("donorRegistrationQr");
    if (!image) return;
    const response = await authenticatedFetch("/api/donor-registration/qr");
    if (!response || !response.ok) return;
    image.src = URL.createObjectURL(await response.blob());
}
function loadUsersData(){
authenticatedFetch('/api/users')
.then(r=>r ? r.json() : [])
.then(data=>{
usersCache=data;

let roles=[...new Set(data.map(x=>x.role))];

roleFilter.innerHTML='<option value="">All Roles</option>'+roles.map(x=>`<option value="${escapeHtml(x)}">${escapeHtml(x)}</option>`).join('');

displayUsers(data);
});
}


/* ==========================================================
   Render Users
========================================================== */

function displayUsers(data) {

    const tbody = document.getElementById("usersBody");

    if (!tbody) return;

    tbody.innerHTML = data.map(user => `

        <tr>

            <td>

                <div class="user-info">

                    <div class="user-avatar">

                        ${escapeHtml(user.full_name.charAt(0).toUpperCase())}

                    </div>

                    <div>

                        <strong>${escapeHtml(user.full_name)}</strong>

                    </div>

                </div>

            </td>

            <td>

                ${escapeHtml(user.department)}

            </td>

            <td>

                <span class="role-badge ${escapeHtml(user.role.toLowerCase().replace(/\s+/g,'-'))}">

                    ${escapeHtml(user.role)}

                </span>

            </td>

            <td>

                ${escapeHtml(user.email)}

            </td>

            <td>

                ${escapeHtml(user.phone)}

            </td>

            <td>

                <button
                    class="edit-btn"
                    onclick="editUser(${user.id})">

                    <i class="fa-solid fa-pen"></i>

                </button>

                <button
                    class="delete-btn"
                    onclick="deleteUser(${user.id})">

                    <i class="fa-solid fa-trash"></i>

                </button>

            </td>

        </tr>

    `).join("");

    renderUserKPIs();

    renderUserSummary();

    renderRecentUsers();

}
/* ==========================================================
   KPI Cards
========================================================== */

function renderUserKPIs() {

    document.getElementById("kpiUsers").textContent =
        usersCache.length;

    document.getElementById("kpiActiveUsers").textContent =
        usersCache.length;

    document.getElementById("kpiAdmins").textContent =
        usersCache.filter(user => user.role === "Administrator").length;

    document.getElementById("kpiDepartments").textContent =
        new Set(usersCache.map(user => user.department)).size;

}

/* ==========================================================
   Summary Card
========================================================== */

function renderUserSummary() {

    const container =
        document.getElementById("usersSummary");

    if (!container) return;

    const admins =
        usersCache.filter(user => user.role === "Administrator").length;

    const donors =
        usersCache.filter(user => user.role === "Donor").length;

    container.innerHTML = `

        <div class="summary-row">

            <span>Total Users</span>

            <strong>${usersCache.length}</strong>

        </div>

        <div class="summary-row">

            <span>Administrators</span>

            <strong>${admins}</strong>

        </div>

        <div class="summary-row">

            <span>Donors</span>

            <strong>${donors}</strong>

        </div>

    `;

}

/* ==========================================================
   Recent Users
========================================================== */

function renderRecentUsers() {

    const container =
        document.getElementById("recentUsers");

    if (!container) return;

    container.innerHTML = usersCache

        .slice(0,5)

        .map(user => `

            <div class="recent-user">

                <div class="recent-avatar">

                    ${escapeHtml(user.full_name.charAt(0).toUpperCase())}

                </div>

                <div class="recent-info">

                    <strong>${escapeHtml(user.full_name)}</strong>

                    <small>${escapeHtml(user.department)}</small>

                </div>

            </div>

        `)

        .join("");

}

function filterUsers(){

const searchInput = document.getElementById("userSearch");
const roleSelect = document.getElementById("roleFilter");
const text = searchInput?.value.toLowerCase() || "";
const role = roleSelect?.value || "";

let result=usersCache.filter(u=>
u.full_name.toLowerCase().includes(text) &&
(!role || u.role===role)
);

displayUsers(result);

}

function showRegisterUser() {

    const userModal = document.getElementById("userModal");

    userModal.innerHTML = `

    <div class="modal">

        <h3>${editingUserId ? "Edit User" : "Register User"}</h3>

        <input id="newName" placeholder="Full Name">

        <input id="newDept" placeholder="Department">

        <select id="newRole">

            <option value="">Select Role</option>
            <option value="Administrator">Administrator</option>
            <option value="Donor">Donor</option>

        </select>

        <input id="newEmail" placeholder="Email">

        <input id="newPhone" placeholder="Phone">

        <select id="newBloodGroup">
            <option value="">Blood group (required for a new donor)</option>
            <option>A+</option><option>A-</option><option>B+</option><option>B-</option>
            <option>AB+</option><option>AB-</option><option>O+</option><option>O-</option>
        </select>

        <input id="newUsername" placeholder="Username">

        <input
            id="newPassword"
            type="password"
            placeholder="Password"
        >

        <div class="form-actions">

            <button onclick="registerUser()">

                Save User

            </button>

            <button
                class="cancel-btn"
                onclick="closeUserModal()"
            >

                Cancel

            </button>

        </div>

    </div>

    `;

    userModal.classList.add("show");

}



function validateUserForm(){
 const email=/^[^\s@]+@[^\s@]+\.[^\s@]+$/;
 const phone=/^(?:\+91|91)?[6-9][0-9]{9}$/;
 if(!email.test(newEmail.value)){alert("Enter valid email address"); return false;}
 if(!phone.test(newPhone.value.replace(/\s|-/g,""))){alert("Enter valid Indian mobile number"); return false;}
 return true;
}

function registerUser(){

    if(!validateUserForm()) return;

    if(editingUserId){
        console.log("Updating user:", editingUserId);
    }

    const payload = {

        full_name: newName.value.trim(),
        department: newDept.value.trim(),
        role: newRole.value,
        email: newEmail.value.trim(),
        phone: newPhone.value.trim(),
        username: newUsername.value.trim(),
        password: newPassword.value || null

    };

    if (!editingUserId && !payload.password) {
        alert("A password is required for a new account.");
        return;
    }

    if (!editingUserId && payload.role === "Donor") {
        payload.blood_group = newBloodGroup.value;
        if (!payload.blood_group) {
            alert("Select the donor's blood group.");
            return;
        }
    }

    authenticatedFetch(
        editingUserId
            ? `/api/users/${editingUserId}`
            : payload.role === "Donor" ? "/api/donor-registration/admin" : "/api/users/register",
        {
            method: editingUserId ? "PUT" : "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)
        }
    )
    .then(r => r ? r.json() : { detail: "Session expired." })
    .then(r => {

        if (!r.success) throw new Error(r.detail || "Unable to save user.");
        alert("User saved successfully.");

        loadUsersData();

        closeUserModal();

    })
    .catch(err => {

        console.error(err);

    });

}


function editUser(id){
 const u=usersCache.find(x=>x.id===id);
 editingUserId=id;
 showRegisterUser();
 setTimeout(()=>{
 newName.value=u.full_name;
 newDept.value=u.department;
 newRole.value=u.role;
 newEmail.value=u.email;
 newPhone.value=u.phone;
 newUsername.value=u.username;
 newPassword.value="";
 },100);
}

function deleteUser(id){
 if(!confirm("Delete this user?")) return;
  authenticatedFetch(`/api/users/${id}`,{method:"DELETE"})
  .then(r=>r ? r.json() : { detail: "Session expired." })
 .then(()=>{
   loadUsersData();
 });
}


function closeUserModal(){

    const userModal =
        document.getElementById("userModal");

    userModal.classList.remove("show");

    setTimeout(() => {

        userModal.innerHTML = "";

    }, 200);

    editingUserId = null;

}
/* ==========================================================
   Global Functions for Inline HTML
========================================================== */

window.editUser = editUser;

window.deleteUser = deleteUser;

window.registerUser = registerUser;

window.closeUserModal = closeUserModal;
