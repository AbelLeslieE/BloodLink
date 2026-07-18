// ==========================================================
// BLOODLINK ROUTER
// File: router.js
//
// Responsibilities:
// - Handle sidebar page navigation
// - Maintain active navigation state
// - Dispatch navigation events
//
// IMPORTANT:
// The Dashboard is already rendered directly in dashboard.html.
// This router must NOT call old renderDashboard() functions.
// ==========================================================


// ==========================================================
// 1. DEFAULT PAGE
// ==========================================================

const DEFAULT_PAGE = "dashboard";


// ==========================================================
// 2. AVAILABLE PAGES
// ==========================================================

const AVAILABLE_PAGES = new Set([

    "dashboard",

    "bloodRequests",

    "donors",

    "donationHistory",

    "campaigns",

    "notifications",

    "reports",

    "users",

    "profile",

    "settings"

]);


// ==========================================================
// 3. SET ACTIVE NAVIGATION ITEM
// ==========================================================

function setActiveNavigation(page) {

    const navigationItems =
        document.querySelectorAll(
            ".nav-item[data-page]"
        );


    navigationItems.forEach(
        (item) => {

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

            }

            else {

                item.removeAttribute(
                    "aria-current"
                );

            }

        }
    );

}


// ==========================================================
// 4. NAVIGATE
// ==========================================================

function navigate(page) {

    if (!page) {
        return;
    }


    if (!AVAILABLE_PAGES.has(page)) {

        console.warn(
            `BloodLink page "${page}" is not registered.`
        );

        return;

    }


    /*
       Dashboard already exists directly inside
       dashboard.html.

       Therefore no renderDashboard() call is needed.
    */

    if (page === "dashboard") {

        setActiveNavigation(
            DEFAULT_PAGE
        );


        window.dispatchEvent(

            new CustomEvent(
                "bloodlink:navigate",
                {
                    detail: {
                        page: DEFAULT_PAGE
                    }
                }
            )

        );


        return;

    }


    /*
       Other pages will be connected here as they
       are built.

       For now we dispatch a navigation event instead
       of calling undefined render functions.
    */

    setActiveNavigation(
        page
    );


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

}


// ==========================================================
// 5. HANDLE NAVIGATION CLICK
// ==========================================================

function handleNavigationClick(event) {

    const navigationElement =
        event.target.closest(
            "[data-page]"
        );


    if (!navigationElement) {
        return;
    }


    const page =
        navigationElement.dataset.page;


    if (!page) {
        return;
    }


    event.preventDefault();


    navigate(
        page
    );

}


// ==========================================================
// 6. INITIALIZE ROUTER
// ==========================================================

function initializeRouter() {

    /*
       sidebar.js creates navigation dynamically.

       Event delegation is therefore used on document
       instead of attaching listeners individually.
    */

    document.addEventListener(
        "click",
        handleNavigationClick
    );


    setActiveNavigation(
        DEFAULT_PAGE
    );

}


// ==========================================================
// 7. INITIALIZATION
// ==========================================================

if (document.readyState === "loading") {

    document.addEventListener(
        "DOMContentLoaded",
        initializeRouter
    );

}

else {

    initializeRouter();

}


// ==========================================================
// 8. EXPORTS
// ==========================================================

export {

    navigate,

    setActiveNavigation

};
