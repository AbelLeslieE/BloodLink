/* ==========================================================
   BloodLink - Users Module
   File: users.js
========================================================== */

let usersCache = [];

let editingUserId = null;

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
                        Manage administrators, biomedical engineers,
                        department users and system access.
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

            <select id="deptFilter">

                <option value="">
                    All Departments
                </option>

            </select>

            <select id="roleFilter">

                <option value="">
                    All Roles
                </option>

            </select>

            <select id="sortUsers">

                <option value="">
                    Sort By
                </option>

                <option value="name">
                    Name
                </option>

                <option value="department">
                    Department
                </option>

                <option value="role">
                    Role
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

                <div class="users-table-wrapper">

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
        .getElementById("deptFilter")
        ?.addEventListener(
            "change",
            filterUsers
        );

    document
        .getElementById("roleFilter")
        ?.addEventListener(
            "change",
            filterUsers
        );

    document
        .getElementById("sortUsers")
        ?.addEventListener(
            "change",
            filterUsers
        );

    loadUsersData();

}
function loadUsersData(){
fetch('/api/users')
.then(r=>r.json())
.then(data=>{
usersCache=data;

let depts=[...new Set(data.map(x=>x.department))];
let roles=[...new Set(data.map(x=>x.role))];

deptFilter.innerHTML='<option value="">All Departments</option>'+depts.map(x=>`<option>${x}</option>`).join('');
roleFilter.innerHTML='<option value="">All Roles</option>'+roles.map(x=>`<option>${x}</option>`).join('');

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

                        ${user.name.charAt(0).toUpperCase()}

                    </div>

                    <div>

                        <strong>${user.name}</strong>

                    </div>

                </div>

            </td>

            <td>

                ${user.department}

            </td>

            <td>

                <span class="role-badge ${user.role.toLowerCase().replace(/\s+/g,'-')}">

                    ${user.role}

                </span>

            </td>

            <td>

                ${user.email}

            </td>

            <td>

                ${user.phone}

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
        usersCache.filter(user => user.role === "Manager").length;

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
        usersCache.filter(user => user.role === "Manager").length;

    const bmes =
        usersCache.filter(user => user.role === "BME").length;

    const users =
        usersCache.filter(user => user.role === "User").length;

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

            <span>Biomedical Engineers</span>

            <strong>${bmes}</strong>

        </div>

        <div class="summary-row">

            <span>Department Users</span>

            <strong>${users}</strong>

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

                    ${user.name.charAt(0).toUpperCase()}

                </div>

                <div class="recent-info">

                    <strong>${user.name}</strong>

                    <small>${user.department}</small>

                </div>

            </div>

        `)

        .join("");

}

function filterUsers(){

let text=userSearch.value.toLowerCase();

let result=usersCache.filter(u=>
u.name.toLowerCase().includes(text) &&
(!deptFilter.value || u.department==deptFilter.value) &&
(!roleFilter.value || u.role==roleFilter.value)
);

if(sortUsers.value)
result.sort((a,b)=>a[sortUsers.value].localeCompare(b[sortUsers.value]));

displayUsers(result);

}

function showRegisterUser(){

    const userModal = document.getElementById("userModal");

    userModal.innerHTML = `

    <div class="modal">

        <h3>${editingUserId ? "Edit User" : "Register User"}</h3>

        <input id="newName" placeholder="Name">

        <input id="newDept" placeholder="Department">

        <select id="newRole">

            <option value="">Select Role</option>

            <option value="Manager">Administrator</option>

            <option value="BME">Biomedical Engineer</option>

            <option value="User">Department User</option>

        </select>

        <input id="newEmail" placeholder="Email">

        <input id="newPhone" placeholder="Phone">

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

        name: newName.value,
        department: newDept.value,
        role: newRole.value,
        email: newEmail.value,
        phone: newPhone.value,
        username: newUsername.value,
        password: newPassword.value

    };

    console.log("Payload being sent:", payload);

    fetch(
        editingUserId
            ? `/api/users/${editingUserId}`
            : "/api/users/register",
        {
            method: editingUserId ? "PUT" : "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify(payload)
        }
    )
    .then(r => r.json())
    .then(r => {

        alert(r.message);

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
 newName.value=u.name;
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
 fetch(`/api/users/${id}`,{method:"DELETE"})
 .then(r=>r.json())
 .then(()=>{
   loadUsersData();
 });
}


function closeUserModal(){

    const userModal =
        document.getElementById("userModal");

    userModal.innerHTML = "";

    editingUserId = null;

}
/* ==========================================================
   Global Functions for Inline HTML
========================================================== */

window.editUser = editUser;

window.deleteUser = deleteUser;

window.registerUser = registerUser;

window.closeUserModal = closeUserModal;