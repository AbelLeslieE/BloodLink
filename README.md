# BloodLink

BloodLink is a blood donor management system developed exclusively for National Service Scheme (NSS) volunteers. It replaces the existing Excel-based workflow for finding and contacting donors. Administrators manage campaigns, while donors have a separate, privacy-safe portal.

## Technology Stack

- Frontend: HTML5, CSS3, and Vanilla JavaScript
- Backend: Python, FastAPI, SQLAlchemy, and Alembic
- Database: PostgreSQL
- Authentication: Login architecture to be reused from the existing BloodLink project

## Folder Structure

```text
BloodLink/
├── backend/
│   ├── auth/
│   ├── config/
│   ├── database/
│   │   ├── migrations/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── crud.py
│   ├── middleware/
│   ├── routers/
│   ├── services/
│   ├── static/
│   ├── utils/
│   ├── __init__.py
│   └── main.py
├── frontend/
│   ├── assets/
│   │   ├── icons/
│   │   ├── images/
│   │   └── fonts/
│   ├── components/
│   ├── css/
│   ├── js/
│   ├── pages/
│   └── index.html
├── tests/
├── uploads/
├── docs/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Development Phases

1. Foundation: establish the project structure, standards, and dependencies.
2. Application modules: implement approved functionality in future phases.
3. Quality assurance: add validation, automated testing, and review.
4. Release readiness: prepare the application for deployment.

## Coding Standards

- Keep frontend and backend code fully separated.
- Do not use inline CSS or inline JavaScript.
- Give every file one clear responsibility and avoid duplication.
- Keep business logic in `backend/services/`.
- Keep database operations in `backend/database/crud.py`.
- Keep database models in `backend/database/models.py` and Pydantic schemas in `backend/database/schemas.py`.
- Keep API endpoints in `backend/routers/`, utilities in `backend/utils/`, and configuration in `backend/config/`.

## Current Status

The project includes administrator workflows, donor matching and notifications, secure
donor accounts, a donor dashboard, rewards, and automatically issued donation certificates.

## Donor rewards and verification

BloodLink now treats a **Yes** response as willingness only. It never awards
points until an administrator confirms the completed donation. A confirmation
creates one donation-history record per donor and blood request, awards the
configured 100 points, and cannot be repeated for that same pair.

Before starting the application, configure the required environment variables
including `DEFAULT_VOLUNTEER_PASSWORD`, then apply the schema with:

```powershell
alembic upgrade head
uvicorn backend.main:app --reload
```

## PWA and secure push notifications

BloodLink is served normally and as one installable PWA from the same Render
deployment. Set these **Render server environment variables** to enable real
browser push delivery; never put the private key in frontend files:

```text
VAPID_PUBLIC_KEY=<base64url public VAPID key>
VAPID_PRIVATE_KEY=<private VAPID key>
VAPID_SUBJECT=mailto:alerts@example.org
```

Generate one VAPID key pair securely, store it in Render's encrypted environment
settings, and keep the same pair across redeployments. Apply `alembic upgrade
head` during deployment. Donors enable notifications explicitly from their donor
dashboard; subscriptions are authenticated and are removed when a push provider
reports them invalid. New requests are created through `POST /api/blood-requests`
and server-side push targeting uses the current donor blood group and availability,
leaving a policy hook for structured district/city and emergency-priority targeting.

## Donor registration

Public registration now creates an active donor account immediately after the
donor completes the personal/profile fields and confirms a password. The normal
registration flow does not require email delivery, and success shows a direct
link to sign in. The legacy one-time email password-setup endpoints remain
available for existing pending registrations.

If you use those legacy email endpoints, configure these Render variables:

```text
RESEND_API_KEY=<Resend server API key>
EMAIL_FROM=<verified sender address>
BACKEND_URL=<public BloodLink HTTPS URL>
```

New registrations are inactive until their 30-minute, single-use setup token
is redeemed. Existing users and administrator-created donor accounts remain
active and continue to use their current passwords. Apply `alembic upgrade
head` to add the pending-registration fields and `donor_profiles` table.

### Gmail SMTP alternative for Render

If you do not own a custom domain for Resend, BloodLink uses Gmail SMTP when
all of these Render environment variables are configured. Create a **Google App
Password** (not your normal Google password) after enabling two-step
verification, and keep it only in Render:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail-address@gmail.com
SMTP_PASSWORD=<16-character Google App Password>
SMTP_FROM=BloodLink <your-gmail-address@gmail.com>
```

SMTP takes precedence over Resend, so registration and blood-request emails can
be delivered to arbitrary recipients without a Resend domain. Never commit the
App Password to source control.

### Render deployment commands

This repository has no `render.yaml`, so keep the existing Render service and
set its commands in the Render dashboard:

```text
Build Command: pip install -r requirements.txt
Start Command: alembic upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

The start command applies all current migrations before the application starts,
including Web Push subscriptions and pending donor registration profiles.

The first administrator is created from `DEFAULT_VOLUNTEER_USERNAME` and
`DEFAULT_VOLUNTEER_PASSWORD`; no default password is shipped in source code.

Administrators use the existing dashboard. Donor accounts are redirected to
`/donor-dashboard`, which exposes only safe request details and never returns
patient or bystander contact information.

## QR donor registration and certificates

Administrators can open **Users** in the dashboard to display the donor-registration QR code or create a linked donor account themselves. The QR code opens `/donor-register`, where a donor verifies their details, receives a one-time password-setup email, and then creates their password. Phone numbers and email addresses are checked across both donor and user records, so a registered donor cannot create a second account through formatting variations.

After an administrator confirms a donation, BloodLink issues a single PDF certificate automatically. The donor can find it under **My certificates** in `/donor-dashboard` and download it directly to a mobile device. Set `BACKEND_URL` to the public URL reachable by donor phones before printing or sharing the QR code.
