export function renderDashboard() {
    return `
        <div class="dashboard-main">

            <!-- Welcome Section -->
            <section class="dashboard-hero">

                <div class="hero-content">

                    <div>
                        <h1>Good Evening, Administrator 👋</h1>
                        <p>
                            Welcome back to BloodLink.
                            Here's an overview of today's blood donation activities.
                        </p>
                    </div>

                    <div class="hero-date">
                        <span id="currentDate">18 July 2026</span>
                        <span id="currentTime">10:45 PM</span>
                    </div>

                </div>

            </section>

            <!-- KPI Cards -->
            <section class="dashboard-kpi">

                <div class="kpi-card">
                    <div class="kpi-icon red">❤️</div>
                    <div class="kpi-content">
                        <h2 id="totalDonors">1254</h2>
                        <p>Total Donors</p>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-icon blue">🩸</div>
                    <div class="kpi-content">
                        <h2 id="activeRequests">18</h2>
                        <p>Active Blood Requests</p>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-icon green">✅</div>
                    <div class="kpi-content">
                        <h2 id="readyDonors">426</h2>
                        <p>Ready to Donate</p>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-icon red">❤️</div>
                    <div class="kpi-content">
                        <h2 id="monthlyDonations">84</h2>
                        <p>Donations This Month</p>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-icon teal">👨‍💼</div>
                    <div class="kpi-content">
                        <h2 id="volunteers">42</h2>
                        <p>Active Volunteers</p>
                    </div>
                </div>

                <div class="kpi-card">
                    <div class="kpi-icon orange">🚨</div>
                    <div class="kpi-content">
                        <h2 id="emergencyRequests">4</h2>
                        <p>Emergency Requests</p>
                    </div>
                </div>

            </section>

        </div>
    `;
}