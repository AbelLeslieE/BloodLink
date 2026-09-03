const form = document.querySelector("#donorRegistrationForm");
const message = document.querySelector("#formMessage");
const submit = document.querySelector("#submitRegistration");
const statusSelect = document.querySelector("#currentStatus");
const profileFields = document.querySelector("#profileFields");
let phase = "verify";
let verifiedUsername = null;

const fieldLabels = { full_name: "Full name", phone: "Phone number", email: "Email address", blood_group: "Blood group", current_status: "Current status", username: "Username" };
const select = (name, label, options, required = true) => `<label>${label}${required ? " *" : ""}<select name="${name}" ${required ? "required" : ""}><option value="">Select</option>${options.map((option) => `<option>${option}</option>`).join("")}</select></label>`;
const input = (name, label, { required = true, list = "", type = "text", hint = "" } = {}) => `<label>${label}${required ? " *" : ""}<input name="${name}" type="${type}" ${list ? `list="${list}"` : ""} ${required ? "required" : ""} maxlength="${type === "number" ? "4" : "255"}">${hint ? `<small class="field-hint">${hint}</small>` : ""}</label>`;
const pair = (...fields) => `<div class="pair">${fields.join("")}</div>`;

function setMessage(text, success = false) { message.className = success ? "success" : ""; message.textContent = text; }
function clearFieldError(name) { const input = form.elements.namedItem(name); input?.removeAttribute("aria-invalid"); document.querySelector(`#registration-${CSS.escape(name)}-error`)?.remove(); }
function showFieldError(name, text) { const input = form.elements.namedItem(name); if (!input) return; clearFieldError(name); input.setAttribute("aria-invalid", "true"); const error = document.createElement("small"); error.id = `registration-${name}-error`; error.className = "field-error"; error.textContent = text; input.closest("label")?.append(error); }
function normalisePhone(value) { return value.replace(/[\s()-]/g, "").replace(/^00/, "+"); }

function schoolFields() {
  return `<div class="conditional-card">${input("institution_name", "School name", { list: "institutions", hint: "Choose a listed school or type a school not listed." })}${pair(select("school_class", "Current standard / class", ["8", "9", "10", "11", "12", "Other"]), select("education_board", "Board / syllabus", ["CBSE", "ICSE / ISC", "Kerala State", "Other State Board", "Other"]))}<div data-other="education_board" hidden>${input("education_board_other", "Specify board / syllabus")}</div>${select("stream", "Stream", ["Science", "Commerce", "Humanities", "Other"], false)}</div>`;
}
function collegeFields() {
  return `<div class="conditional-card">${input("institution_name", "College / University name", { list: "institutions", hint: "Choose a listed institution or type one not listed." })}${pair(select("course_level", "Course level / qualification", ["Diploma", "B.Tech / B.E.", "B.Sc", "B.Com", "BBA", "BA", "BCA", "MBBS", "BDS", "Nursing", "M.Tech", "M.Sc", "MBA", "MA", "PhD", "Other"]), input("course_name", "Course / branch", { list: "courses" }))}<div data-other="course_level" hidden>${input("course_level_other", "Specify qualification")}</div>${pair(input("academic_department", "Department"), input("semester_or_year", "Current semester / year", { list: "study-periods" }))}${input("university", "University / syllabus / curriculum", { list: "institutions" })}${input("expected_graduation_year", "Expected graduation year", { required: false, type: "number" })}</div>`;
}
function studentFields() {
  const level = form.elements.namedItem("education_level")?.value || "";
  const base = select("education_level", "Education level", ["School", "College / University", "Other"]);
  if (level === "School") return `${base}${schoolFields()}`;
  if (level === "College / University") return `${base}${collegeFields()}`;
  if (level === "Other") return `${base}<div class="conditional-card">${input("education_level_other", "Describe education level")}${input("institution_name", "Institution name", { list: "institutions" })}</div>`;
  return base;
}
function employedFields() {
  return `<div class="conditional-card">${pair(select("employment_type", "Employment type", ["Full-time", "Part-time", "Contract", "Internship", "Government", "Private", "Other"]), input("occupation", "Occupation / job title"))}<div data-other="employment_type" hidden>${input("employment_type_other", "Specify employment type")}</div>${input("organization_name", "Organisation / company name")}${pair(input("employment_department", "Department / division", { required: false }), select("industry", "Industry / sector", ["Healthcare", "IT / Software", "Education", "Manufacturing", "Government", "Banking / Finance", "Transportation", "Retail", "Construction", "Hospitality", "Other"]))}<div data-other="industry" hidden>${input("industry_other", "Specify industry")}</div>${input("work_location", "Work location", { required: false })}</div>`;
}
function selfEmployedFields() {
  return `<div class="conditional-card">${input("occupation", "Profession / business type")}${pair(input("organization_name", "Business / organisation name", { required: false }), select("industry", "Industry / sector", ["Healthcare", "IT / Software", "Education", "Manufacturing", "Government", "Banking / Finance", "Transportation", "Retail", "Construction", "Hospitality", "Other"]))}<div data-other="industry" hidden>${input("industry_other", "Specify industry")}</div>${input("work_location", "Work location", { required: false })}</div>`;
}
function renderProfile() {
  const status = statusSelect.value;
  let html = "";
  if (status === "Student") html = studentFields();
  else if (status === "Employed") html = employedFields();
  else if (status === "Self-employed / Business") html = selfEmployedFields();
  else if (status === "Unemployed") html = `<div class="conditional-card">${pair(input("previous_occupation", "Previous occupation", { required: false }), input("area_of_interest", "Area of interest", { required: false }))}</div>`;
  else if (status === "Other") html = `<div class="conditional-card">${input("status_description", "Please describe your current status")}</div>`;
  profileFields.innerHTML = html;
  profileFields.querySelectorAll("select").forEach((control) => control.addEventListener("change", (event) => {
    if (event.target.name === "education_level") { renderProfile(); return; }
    const other = profileFields.querySelector(`[data-other="${event.target.name}"]`);
    if (other) other.hidden = event.target.value !== "Other";
  }));
}

function payload() {
  const values = Object.fromEntries(new FormData(form).entries());
  return Object.fromEntries(Object.entries(values).filter(([, value]) => String(value).trim() !== ""));
}
function showApiError(data) {
  const details = Array.isArray(data?.detail) ? data.detail : [];
  const usernameIssue = details.find((item) => item.loc?.at(-1) === "username") || (typeof data?.detail === "string" && /username/i.test(data.detail));
  if (usernameIssue) showFieldError("username", typeof usernameIssue === "string" ? usernameIssue : String(usernameIssue.msg).replace(/^Value error,\s*/i, ""));
  return typeof data?.detail === "string" ? data.detail : "Please correct the highlighted details and try again.";
}

form.addEventListener("input", (event) => { clearFieldError(event.target.name); if (phase === "setup") { phase = "verify"; submit.textContent = "Verify details"; } });
statusSelect.addEventListener("change", renderProfile);
renderProfile();

form.addEventListener("submit", async (event) => {
  event.preventDefault(); setMessage("");
  if (phase === "verify") {
    if (!form.reportValidity()) { setMessage("Please complete the required details."); return; }
    const values = payload();
    if (!/^\+?\d{7,15}$/.test(normalisePhone(values.phone || ""))) { showFieldError("phone", "Enter a valid phone number with 7 to 15 digits."); setMessage("Please correct the highlighted details."); return; }
    submit.disabled = true; submit.textContent = "Verifying details…";
    try {
      const response = await fetch("/api/donor-registration/verify-details", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(values) });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(showApiError(data));
      verifiedUsername = data.username; phase = "setup"; submit.textContent = "Set up your password";
      setMessage("Details verified. Click “Set up your password” to receive a secure email link.", true);
    } catch (error) { setMessage(error instanceof TypeError ? "We could not reach BloodLink. Check your connection and try again." : error.message); }
    finally { submit.disabled = false; if (phase === "verify") submit.textContent = "Verify details"; }
    return;
  }
  submit.disabled = true; submit.textContent = "Sending email…";
  try {
    const response = await fetch("/api/donor-registration/password-setup/send", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: verifiedUsername }) });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || "Unable to send the setup email.");
    setMessage(data.detail, true); submit.textContent = "Resend password setup email";
  } catch (error) { setMessage(error instanceof TypeError ? "We could not reach BloodLink. Check your connection and try again." : error.message); submit.textContent = "Set up your password"; }
  finally { submit.disabled = false; }
});
