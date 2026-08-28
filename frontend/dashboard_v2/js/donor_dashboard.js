const token = localStorage.getItem("access_token");
if (!token) window.location.replace("/login");

const authFetch = (url, options = {}) => fetch(url, {
    ...options,
    headers: { Authorization: `Bearer ${token}`, ...(options.headers || {}) },
});
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

async function clearSession({ revoke = false } = {}) {
    if (revoke && token) {
        try {
            await authFetch("/api/auth/logout", { method: "POST" });
        } catch (error) {
            console.warn("Server logout could not be completed.", error);
        }
    }
    ["access_token", "volunteer_name", "username", "role", "full_name"].forEach((key) => localStorage.removeItem(key));
    window.location.replace("/login");
}

async function loadDashboard() {
    const [summaryResponse, requestsResponse, leaderboardResponse, certificatesResponse] = await Promise.all([
        authFetch("/api/donor-dashboard/summary"), authFetch("/api/donor-dashboard/requests"), authFetch("/api/donor-dashboard/leaderboard"), authFetch("/api/donor-dashboard/certificates"),
    ]);
    if ([summaryResponse, requestsResponse, leaderboardResponse, certificatesResponse].some((response) => response.status === 401 || response.status === 403)) return clearSession();
    const summary = await summaryResponse.json();
    const requests = await requestsResponse.json();
    const leaders = await leaderboardResponse.json();
    const certificates = await certificatesResponse.json();
    document.querySelector("#welcome").textContent = `Welcome, ${summary.donor.name}`;
    document.querySelector("#points").textContent = summary.total_points;
    document.querySelector("#donations").textContent = summary.donation_count;
    document.querySelector("#badge").textContent = summary.badge;
    document.querySelector("#pending").textContent = summary.pending_verification;
    document.querySelector("#eligibility").textContent = summary.eligibility_reminder;
    document.querySelector("#donorCode").textContent = summary.donor.donor_code;
    document.querySelector("#profile").innerHTML = [
        ["Blood group", summary.donor.blood_group], ["Email", summary.donor.email],
        ["Phone", summary.donor.phone], ["Department", summary.donor.department || "Not provided"],
    ].map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
    renderRequests(requests);
    document.querySelector("#history").innerHTML = summary.recent_donations.length ? summary.recent_donations.map((item) => `<div class="history-row"><strong>${escapeHtml(item.hospital_name)}</strong><br><span>${escapeHtml(item.donation_date)} · ${item.points_awarded} points · ${escapeHtml(item.status)}</span></div>`).join("") : '<p class="empty">No confirmed donations yet.</p>';
    document.querySelector("#leaderboard").innerHTML = leaders.map((item) => `<li><strong>${escapeHtml(item.name)}</strong> — ${item.points} points, ${item.donations} donations (${escapeHtml(item.badge)})</li>`).join("") || '<li class="empty">No donors to show.</li>';
    const certificateContainer = document.querySelector("#certificates");
    certificateContainer.innerHTML = certificates.length ? certificates.map((certificate) => `<article class="certificate"><div><strong>${escapeHtml(certificate.hospital_name)}</strong><span>${escapeHtml(certificate.donation_date)} · ${escapeHtml(certificate.certificate_number)}</span></div><button type="button" data-certificate-url="${escapeHtml(certificate.download_url)}">Download PDF</button></article>`).join("") : '<p class="empty">Certificates appear here after an administrator confirms a donation.</p>';
    certificateContainer.querySelectorAll("button[data-certificate-url]").forEach((button) => button.addEventListener("click", async () => {
        button.disabled = true;
        try {
            const response = await authFetch(button.dataset.certificateUrl);
            if (!response || !response.ok) throw new Error("Unable to download this certificate.");
            const fileUrl = URL.createObjectURL(await response.blob());
            const link = document.createElement("a");
            link.href = fileUrl;
            link.download = "BloodLink-donation-certificate.pdf";
            link.click();
            setTimeout(() => URL.revokeObjectURL(fileUrl), 1000);
        } catch (error) {
            alert(error.message);
        } finally {
            button.disabled = false;
        }
    }));
}

function renderRequests(requests) {
    const container = document.querySelector("#requests");
    container.innerHTML = requests.length ? requests.map((request) => `<article class="request"><h3>${escapeHtml(request.blood_group)} needed · ${escapeHtml(request.priority)}</h3><p>${escapeHtml(request.message)}</p><p class="meta">${escapeHtml(request.hospital_location)} · ${escapeHtml(request.required_date)} · ${request.units_required} unit(s)</p><p class="status">${escapeHtml(request.donor_status)}</p>${request.response || request.donor_status === "Points Awarded" ? "" : `<div class="actions"><button class="yes" data-request="${request.id}" data-response="Yes">Yes, I am available</button><button class="no" data-request="${request.id}" data-response="No">No</button></div>`}</article>`).join("") : '<p class="empty">No matched open requests at the moment.</p>';
    container.querySelectorAll("button[data-request]").forEach((button) => button.addEventListener("click", async () => {
        button.disabled = true;
        const response = await authFetch(`/api/donor-dashboard/requests/${button.dataset.request}/response`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({response: button.dataset.response}) });
        if (!response.ok) alert((await response.json()).detail || "Unable to save your response.");
        await loadDashboard();
    }));
}

document.querySelector("#logout").addEventListener("click", () => clearSession({ revoke: true }));
document.querySelector("#hideLeaderboard").addEventListener("change", async (event) => {
    await authFetch(`/api/donor-dashboard/privacy/leaderboard?hidden=${event.target.checked}`, {method:"PATCH"});
    await loadDashboard();
});
loadDashboard().catch(() => { document.querySelector("#requests").textContent = "Unable to load the donor dashboard."; });
