# BloodLink

BloodLink is a blood donor management system developed exclusively for National Service Scheme (NSS) volunteers. It is intended to replace the existing Excel-based workflow for finding and contacting blood donors. Donors do not access the application.

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

The project includes the backend configuration, database foundation, and NSS volunteer
authentication. Business workflows and non-authentication frontend functionality remain
intentionally unimplemented.
