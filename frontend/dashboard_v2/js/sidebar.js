// ==========================================================
// BLOODLINK SIDEBAR
// File: sidebar.js
//
// Responsibilities:
// - Role-based navigation
// - Navigation groups
// - Active page state
// - Desktop collapse / expand
// - Mobile drawer
// - Sidebar state persistence
// - Profile navigation
// - Logout handling preparation
// - Lucide icon initialization
// ==========================================================
import {
    logoutUser
} from "./api.js";

// ==========================================================
// 1. CONFIGURATION
// ==========================================================

const MOBILE_BREAKPOINT = 1024;

const STORAGE_KEYS = {
    ROLE: "role",
    SIDEBAR_COLLAPSED: "bloodlink_sidebar_collapsed"
};


// ==========================================================
// 2. DOM ELEMENTS
// ==========================================================

const dashboard = document.querySelector(".dashboard");

const sidebar = document.getElementById("sidebar");

const sidebarNav = document.getElementById("sidebar-nav");

const sidebarToggle = document.getElementById("sidebarToggle");

const sidebarOverlay = document.getElementById("sidebarOverlay");

const logoutButton = document.getElementById("logoutButton");

const profileCard = document.querySelector(".profile-card");


// ==========================================================
// 3. ROLE CONFIGURATION
// ==========================================================
//
// Supported roles:
//
// admin
// volunteer
// blood_bank
//
// During frontend development, ADMIN is used as the fallback
// when no role exists in localStorage.
//
// Later, the authenticated FastAPI user will determine this.
// ==========================================================

function getCurrentRole() {

    const storedRole = localStorage.getItem(STORAGE_KEYS.ROLE);

    if (!storedRole) {
        return "admin";
    }

    return storedRole
        .trim()
        .toLowerCase()
        .replaceAll("-", "_")
        .replaceAll(" ", "_");
}


// ==========================================================
// 4. NAVIGATION CONFIGURATION
// ==========================================================
//
// Keeping menu configuration as data avoids duplicating
// large HTML template strings for every role.
// ==========================================================

const navigationConfig = {

    admin: [

        {
            title: "MAIN",

            items: [

                {
                    label: "Dashboard",
                    icon: "layout-dashboard",
                    page: "dashboard"
                },

                {
                    label: "Blood Requests",
                    icon: "droplets",
                    page: "bloodRequests"
                },

                {
                    label: "Donors",
                    icon: "users",
                    page: "donors"
                },

                {
                    label: "Donation History",
                    icon: "heart-handshake",
                    page: "donationHistory"
                },

                {
                    label: "Campaigns",
                    icon: "calendar-days",
                    page: "campaigns"
                }

            ]

        },

        {
            title: "MANAGEMENT",

            items: [

                {
                    label: "Notifications",
                    icon: "bell",
                    page: "notifications"
                },

                {
                    label: "Reports",
                    icon: "chart-no-axes-combined",
                    page: "reports"
                },

                {
                    label: "Users",
                    icon: "user-cog",
                    page: "users"
                }

            ]

        },

        {
            title: "ACCOUNT",

            items: [

                {
                    label: "Profile",
                    icon: "circle-user-round",
                    page: "profile"
                },

                {
                    label: "Settings",
                    icon: "settings",
                    page: "settings"
                }

            ]

        }

    ],


    volunteer: [

        {
            title: "MAIN",

            items: [

                {
                    label: "Dashboard",
                    icon: "layout-dashboard",
                    page: "dashboard"
                },

                {
                    label: "Blood Requests",
                    icon: "droplets",
                    page: "bloodRequests"
                },

                {
                    label: "My Donations",
                    icon: "heart-handshake",
                    page: "donationHistory"
                },

                {
                    label: "Campaigns",
                    icon: "calendar-days",
                    page: "campaigns"
                }

            ]

        },

        {
            title: "MANAGEMENT",

            items: [

                {
                    label: "Notifications",
                    icon: "bell",
                    page: "notifications"
                }

            ]

        },

        {
            title: "ACCOUNT",

            items: [

                {
                    label: "Profile",
                    icon: "circle-user-round",
                    page: "profile"
                },

                {
                    label: "Settings",
                    icon: "settings",
                    page: "settings"
                }

            ]

        }

    ],


    blood_bank: [

        {
            title: "MAIN",

            items: [

                {
                    label: "Dashboard",
                    icon: "layout-dashboard",
                    page: "dashboard"
                },

                {
                    label: "Blood Requests",
                    icon: "droplets",
                    page: "bloodRequests"
                },

                {
                    label: "Donors",
                    icon: "users",
                    page: "donors"
                },

                {
                    label: "donationHistory",
                    icon: "heart-handshake",
                    page: "donationHistory"
                }

            ]

        },

        {
            title: "MANAGEMENT",

            items: [

                {
                    label: "Notifications",
                    icon: "bell",
                    page: "notifications"
                },

                {
                    label: "Reports",
                    icon: "chart-no-axes-combined",
                    page: "reports"
                }

            ]

        },

        {
            title: "ACCOUNT",

            items: [

                {
                    label: "Profile",
                    icon: "circle-user-round",
                    page: "profile"
                },

                {
                    label: "Settings",
                    icon: "settings",
                    page: "settings"
                }

            ]

        }

    ]

};


// ==========================================================
// 5. GET CURRENT PAGE
// ==========================================================
//
// router.js can later update the active state directly.
//
// For now, Dashboard is the default page.
// ==========================================================

function getCurrentPage() {

    const activeItem = document.querySelector(
        ".sidebar-nav .nav-item.active"
    );

    if (activeItem?.dataset.page) {
        return activeItem.dataset.page;
    }

    return "dashboard";
}


// ==========================================================
// 6. CREATE NAVIGATION ITEM
// ==========================================================

function createNavigationItem(item, currentPage) {

    const link = document.createElement("a");

    link.href = "#";

    link.className = "nav-item";

    link.dataset.page = item.page;

    link.setAttribute(
        "aria-label",
        item.label
    );


    if (item.page === currentPage) {

        link.classList.add("active");

        link.setAttribute(
            "aria-current",
            "page"
        );

    }


    const icon = document.createElement("i");

    icon.setAttribute(
        "data-lucide",
        item.icon
    );

    icon.setAttribute(
        "aria-hidden",
        "true"
    );


    const label = document.createElement("span");

    label.textContent = item.label;


    link.append(
        icon,
        label
    );


    return link;
}


// ==========================================================
// 7. CREATE NAVIGATION GROUP
// ==========================================================

function createNavigationGroup(group, currentPage) {

    const groupElement = document.createElement("div");

    groupElement.className = "nav-group";


    const title = document.createElement("span");

    title.className = "nav-group-title";

    title.textContent = group.title;


    groupElement.appendChild(title);


    group.items.forEach((item) => {

        const navigationItem =
            createNavigationItem(
                item,
                currentPage
            );

        groupElement.appendChild(
            navigationItem
        );

    });


    return groupElement;
}


// ==========================================================
// 8. RENDER SIDEBAR NAVIGATION
// ==========================================================

function renderSidebarNavigation() {

    if (!sidebarNav) {
        return;
    }


    const role = getCurrentRole();

    const menu =
        navigationConfig[role] ||
        navigationConfig.admin;

    const currentPage =
        getCurrentPage();


    sidebarNav.replaceChildren();


    menu.forEach((group) => {

        const navigationGroup =
            createNavigationGroup(
                group,
                currentPage
            );

        sidebarNav.appendChild(
            navigationGroup
        );

    });


    refreshLucideIcons();
}


// ==========================================================
// 9. REFRESH LUCIDE ICONS
// ==========================================================

function refreshLucideIcons() {

    if (
        window.lucide &&
        typeof window.lucide.createIcons === "function"
    ) {

        window.lucide.createIcons();

    }

}


// ==========================================================
// 10. ACTIVE NAVIGATION STATE
// ==========================================================

function setActiveNavigation(page) {

    if (!sidebarNav || !page) {
        return;
    }


    const navigationItems =
        sidebarNav.querySelectorAll(
            ".nav-item"
        );


    navigationItems.forEach((item) => {

        const isActive =
            item.dataset.page === page;


        item.classList.toggle(
            "active",
            isActive
        );


        if (isActive) {

            item.setAttribute(
                "aria-current",
                "page"
            );

        } else {

            item.removeAttribute(
                "aria-current"
            );

        }

    });

}


// ==========================================================
// 11. HANDLE NAVIGATION
// ==========================================================

function handleNavigation(event) {

    const navigationItem =
        event.target.closest(
            ".nav-item"
        );


    if (!navigationItem) {
        return;
    }


    event.preventDefault();


    const page =
        navigationItem.dataset.page;


    if (!page) {
        return;
    }


    setActiveNavigation(page);


    /*
       router.js will later handle the actual
       page loading.

       We dispatch a reusable event instead of
       tightly coupling sidebar.js to router.js.
    */

    window.dispatchEvent(

        new CustomEvent(
            "bloodlink:navigate",
            {
                detail: {
                    page
                }
            }
        )

    );


    if (isMobileView()) {
        closeMobileSidebar();
    }

}


// ==========================================================
// 12. CHECK MOBILE VIEW
// ==========================================================

function isMobileView() {

    return window.innerWidth <= MOBILE_BREAKPOINT;

}


// ==========================================================
// 13. DESKTOP SIDEBAR STATE
// ==========================================================

function isSidebarCollapsed() {

    return localStorage.getItem(
        STORAGE_KEYS.SIDEBAR_COLLAPSED
    ) === "true";

}


function applySavedSidebarState() {

    if (!dashboard) {
        return;
    }


    /*
       Collapsed state only applies visually
       to desktop layout.
    */

    if (
        !isMobileView() &&
        isSidebarCollapsed()
    ) {

        dashboard.classList.add(
            "sidebar-collapsed"
        );

    } else {

        dashboard.classList.remove(
            "sidebar-collapsed"
        );

    }

}


// ==========================================================
// 14. TOGGLE DESKTOP SIDEBAR
// ==========================================================

function toggleDesktopSidebar() {

    if (!dashboard) {
        return;
    }


    const collapsed =
        dashboard.classList.toggle(
            "sidebar-collapsed"
        );


    localStorage.setItem(
        STORAGE_KEYS.SIDEBAR_COLLAPSED,
        String(collapsed)
    );

}


// ==========================================================
// 15. MOBILE SIDEBAR
// ==========================================================

function openMobileSidebar() {

    if (!sidebar) {
        return;
    }


    sidebar.classList.add(
        "mobile-open"
    );


    sidebarOverlay?.classList.add(
        "active"
    );


    sidebarToggle?.setAttribute(
        "aria-expanded",
        "true"
    );


    document.body.classList.add(
        "sidebar-open"
    );

}


function closeMobileSidebar() {

    if (!sidebar) {
        return;
    }


    sidebar.classList.remove(
        "mobile-open"
    );


    sidebarOverlay?.classList.remove(
        "active"
    );


    sidebarToggle?.setAttribute(
        "aria-expanded",
        "false"
    );


    document.body.classList.remove(
        "sidebar-open"
    );

}


// ==========================================================
// 16. SIDEBAR TOGGLE BUTTON
// ==========================================================

function handleSidebarToggle() {

    if (isMobileView()) {

        const isOpen =
            sidebar?.classList.contains(
                "mobile-open"
            );


        if (isOpen) {

            closeMobileSidebar();

        } else {

            openMobileSidebar();

        }


        return;
    }


    toggleDesktopSidebar();

}


// ==========================================================
// 17. PROFILE NAVIGATION
// ==========================================================

function handleProfileNavigation() {

    setActiveNavigation(
        "profile"
    );


    window.dispatchEvent(

        new CustomEvent(
            "bloodlink:navigate",
            {
                detail: {
                    page: "profile"
                }
            }
        )

    );


    if (isMobileView()) {
        closeMobileSidebar();
    }

}


// ==========================================================
// 18. LOGOUT
// ==========================================================

function handleLogout() {

    logoutUser();

}   


// ==========================================================
// 19. KEYBOARD BEHAVIOUR
// ==========================================================

function handleKeyboard(event) {

    if (
        event.key === "Escape" &&
        isMobileView()
    ) {

        closeMobileSidebar();

    }

}


// ==========================================================
// 20. WINDOW RESIZE
// ==========================================================

function handleWindowResize() {

    if (isMobileView()) {

        /*
           Remove desktop collapsed state while
           using the mobile drawer.
        */

        dashboard?.classList.remove(
            "sidebar-collapsed"
        );

        return;

    }


    /*
       When returning to desktop:
       close the mobile drawer and restore
       the saved desktop sidebar state.
    */

    closeMobileSidebar();

    applySavedSidebarState();

}


// ==========================================================
// 21. EVENT LISTENERS
// ==========================================================

function bindSidebarEvents() {

    sidebarNav?.addEventListener(
        "click",
        handleNavigation
    );


    sidebarToggle?.addEventListener(
        "click",
        handleSidebarToggle
    );


    sidebarOverlay?.addEventListener(
        "click",
        closeMobileSidebar
    );


    profileCard?.addEventListener(
        "click",
        handleProfileNavigation
    );


    logoutButton?.addEventListener(
        "click",
        handleLogout
    );


    document.addEventListener(
        "keydown",
        handleKeyboard
    );


    window.addEventListener(
        "resize",
        handleWindowResize
    );

}


// ==========================================================
// 22. INITIALIZE SIDEBAR
// ==========================================================

function initializeSidebar() {

    renderSidebarNavigation();

    applySavedSidebarState();

    bindSidebarEvents();

    refreshLucideIcons();

}


// ==========================================================
// 23. START
// ==========================================================

if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initializeSidebar
    );

} else {

    initializeSidebar();

}


// ==========================================================
// 24. PUBLIC SIDEBAR API
// ==========================================================
//
// These exports allow router.js and other modules
// to control sidebar state without duplicating logic.
// ==========================================================

export {

    setActiveNavigation,

    openMobileSidebar,

    closeMobileSidebar

};