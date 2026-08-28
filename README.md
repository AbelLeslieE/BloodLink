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

The first administrator is created from `DEFAULT_VOLUNTEER_USERNAME` and
`DEFAULT_VOLUNTEER_PASSWORD`; no default password is shipped in source code.

Administrators use the existing dashboard. Donor accounts are redirected to
`/donor-dashboard`, which exposes only safe request details and never returns
patient or bystander contact information.

## QR donor registration and certificates

Administrators can open **Users** in the dashboard to display the donor-registration QR code or create a linked donor account themselves. The QR code opens `/donor-register`, where a donor supplies their name, phone, email, blood group, username, and password. Phone numbers and email addresses are checked across both donor and user records, so a registered donor cannot create a second account through formatting variations.

After an administrator confirms a donation, BloodLink issues a single PDF certificate automatically. The donor can find it under **My certificates** in `/donor-dashboard` and download it directly to a mobile device. Set `BACKEND_URL` to the public URL reachable by donor phones before printing or sharing the QR code.
