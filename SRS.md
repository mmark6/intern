# Software Requirements Specification (SRS)
## UEDCL Task Tracking Application

Revision: 0.2
Date: 2026-07-06

Table of Contents
- 1. Introduction
- 2. Document Conventions
- 3. Overall Description
- 4. Functional Requirements
- 5. External Interface Requirements
- 6. Non-Functional Requirements
- 7. Data Requirements
- 8. Assumptions and Dependencies
- 9. Constraints
- 10. Acceptance Criteria
- 11. Appendices
- Revision History

1. Introduction
1.1 Purpose
This Software Requirements Specification (SRS) describes the functional and non-functional requirements for the UEDCL Task Tracking Application ("the system"). It is intended for the project stakeholders, designers, developers, testers, and maintainers.

1.2 Scope
The UEDCL Task Tracking Application is a web-based system that enables teams to create and manage projects, create and assign tasks, track task progress, notify users of changes, and provide management dashboards and reports. The system comprises a Django REST API backend and a React-based frontend; data is persisted in a relational database (currently SQLite for development; production-grade DB expected in deployment).

1.3 Definitions, Acronyms, and Abbreviations
- JWT: JSON Web Token
- API: Application Programming Interface
- UI: User Interface
- CRUD: Create, Read, Update, Delete

1.4 References
- Project README.md
- Backend requirements.txt
- Security implementation notes: Backend/Uedcl/SECURITY_IMPLEMENTATION.md

2. Document Conventions
- Requirement identifiers use the format FR-<number> for functional and NFR-<number> for non-functional.
- Use cases reference the primary actor and a short title.

3. Overall Description
3.1 Product Perspective
The system is a client-server web application. The backend exposes a RESTful API implemented with Django; the frontend is written with React and communicates via HTTPS JSON APIs. Authentication uses JWT. The app is designed to be modular so services (notifications, authentication) can be scaled or replaced.

3.2 Product Functions (high level)
- User account management (registration, login, password reset)
- Role and permission management (Admin, Manager, Employee)
- Project lifecycle (create, update, archive)
- Task lifecycle (create, assign, update status, comment, attach metadata)
- Notifications (in-app, email optional)
- Dashboard and reports (project/task metrics, filters)

3.3 User Classes and Characteristics
- Admin: manages users, roles, and site-wide settings. Technical familiarity expected.
- Manager: creates projects and tasks, assigns work, and views reports.
- Employee: receives tasks, updates status, comments on tasks.

3.4 Operating Environment
- Backend: Python 3.11+ (per requirements.txt), Django 4.x+, runs on Linux/Windows server environments. Development uses SQLite; production should use PostgreSQL or MySQL.
- Frontend: Node.js 18+, React 18+ (repository uses React 19.x), modern browsers (Chrome, Edge, Firefox, Safari).


3.5 Design and Implementation Constraints
- Must follow the security guidelines in `Backend/Uedcl/SECURITY_IMPLEMENTATION.md`.
- API must be versioned (e.g., /api/v1/).

4. Functional Requirements
Each functional requirement includes a unique id, description, rationale, inputs, processing, outputs, and acceptance criteria.

FR-1: User Registration
- Description: Users can register with name, email, and password. Email verification is optional but recommended.
- Inputs: name, email, password
- Processing: validate input, hash password, store user record, send verification email (if enabled)
- Outputs: success or error message
- Acceptance: new user can authenticate after registration and (if enabled) email verification.

FR-2: Authentication and Authorization
- Description: Users authenticate with email and password to receive a JWT. Role-based access controls restrict actions.
- Inputs: email, password
- Processing: validate credentials, issue JWT with expiry, return user data
- Outputs: JWT token, user profile
- Acceptance: valid credentials return token; expired/invalid credentials rejected.

FR-3: Project Management
- Description: Create, read, update, delete projects. Projects have title, description, start/end dates, owner, status.
- Acceptance: CRUD endpoints pass integration tests and enforce permissions.

FR-4: Task Management
- Description: Tasks belong to projects; tasks have title, description, assignee, priority, due date, status, attachments, comments.
- Acceptance: Tasks can be created/updated/deleted according to role permissions and state transitions.

FR-5: Task Assignment and Notifications
- Description: Managers assign tasks to employees; assignees receive notifications.
- Acceptance: Assigned users receive in-app notifications; notification records are stored.

FR-6: Dashboard and Reporting
- Description: Dashboard shows aggregated metrics: total projects, tasks by status, overdue tasks, tasks per user.
- Acceptance: Dashboard queries return correct aggregated values per dataset.

FR-7: Activity Logs / Audit
- Description: Record changes to projects and tasks (who, what, when) for auditability.
- Acceptance: Audit entries are created on create/update/delete actions.

4.1 Use Cases (brief)
- UC-1: Manager creates a project and adds tasks.
- UC-2: Employee updates task status and adds comments.
- UC-3: Admin manages users and roles.

5. External Interface Requirements
5.1 User Interfaces
- Web UI (React): responsive views for project lists, task boards, task details, user profile, admin console.
- Error handling: show friendly messages for validation and server errors.

5.2 API
- RESTful JSON APIs under `/api/v1/` using HTTPS. Authentication via `Authorization: Bearer <token>` header.
- Standard HTTP response codes: 200, 201, 204, 400, 401, 403, 404, 500.

5.3 Hardware Interfaces
- No specialized hardware required. Server deployment runs on standard VM or container.

5.4 Software Interfaces
- Integrations: optional SMTP for email, optional external storage (S3) for attachments, optional Redis for caching/notifications.

6. Non-Functional Requirements
6.1 Security (NFR-1)
- Use HTTPS for all traffic; store hashed passwords (Argon2 or bcrypt); protect against CSRF and XSS on the frontend; validate and sanitize inputs on backend; implement RBAC; audit logging for sensitive operations.

6.2 Performance (NFR-2)
- Backend API should respond to typical requests within 200–500ms under normal load. Dashboard aggregation queries should complete within 1s for datasets up to 10k tasks.

6.3 Reliability and Availability (NFR-3)
- Target availability: 99.5% (production). Use database backups and retries for transient failures.

6.4 Scalability (NFR-4)
- Design the API and data model to allow horizontal scaling of stateless backend workers and separate stateful services (DB, cache).

6.5 Maintainability (NFR-5)
- Code must include unit and integration tests. Use linters and formatters in CI.

6.6 Usability (NFR-6)
- UI must be accessible (WCAG AA baseline) and responsive. Provide clear workflows for task creation and updates.

6.7 Privacy and Compliance (NFR-7)
- Store only necessary personal data. Provide mechanisms to remove or anonymize user data on request.

7. Data Requirements
7.1 Data Entities (high level)
- User: id, name, email, role, created_at, last_login
- Project: id, title, description, owner_id, status, start_date, end_date
- Task: id, title, description, project_id, assignee_id, priority, status, due_date, metadata
- Notification: id, user_id, type, payload, read, created_at
- AuditLog: id, actor_id, action, object_type, object_id, diff, timestamp

7.1.1 Primary relationships & constraints
- User ↔ Project:
  - Each Project has exactly one owner (owner_id -> User).
  - Only the owner (or Admin) can modify the project.
- Project ↔ Task:
  - Each Task belongs to exactly one Project (project_id -> Project).
  - Tasks are listed and managed in the context of their Project.
- Task ↔ Comments:
  - Each Comment belongs to exactly one Task.
  - Each Comment has exactly one author (author_id -> User).
- Task ↔ Notifications:
  - Notification recipients are Users; notifications reference task-related events via payload.
- Uniqueness/validation:
  - User email is unique (case-insensitive).
  - Task/project status and priority are constrained to enumerated values (enforced at serializer/model level).


7.2 Data Retention
- Audit logs: retain for configurable period (e.g., 1 year) unless regulatory requirements differ.

8. Assumptions and Dependencies
- Users have modern browsers. SMTP and optional third-party services are available for production.
- Production database will be migrated from SQLite to PostgreSQL or equivalent.

9. Constraints
- Initial deployment uses SQLite for development; scale requires moving to production DB.
- Must follow organizational security policies documented in `Backend/Uedcl/SECURITY_IMPLEMENTATION.md`.

10. Acceptance Criteria
- All FR-* endpoints implemented and covered by automated tests.
- Role-based permission checks prevent unauthorized actions.
- Dashboard metrics validated with test datasets.
- Security checklist items implemented (HTTPS, hashed passwords, input validation, audit logging).

11. Appendices
11.1 Traceability
- Map user stories / tickets to FR-* identifiers in the project tracking board.

11.2 Glossary
- See Section 1.3 for common acronyms.

Revision History
- 0.1 (2026-07-06): Initial expanded SRS added.

Recommendations for next steps
- Review requirements with stakeholders and map to user stories/tickets.
- Create a backlog of user stories mapped to FR-* items and assign priorities.
- Implement API contracts (OpenAPI) and agree on versioning and pagination strategies.

12. API Specifications (recommended)
12.1 Authentication
- Expected auth mechanism: JWT Bearer token.
- The frontend stores the access token in browser localStorage under the key `uedcl_access_token`.
- Client must send: `Authorization: Bearer <access_token>` for protected endpoints.
- Token security rules are defined in `Backend/Uedcl/SECURITY_IMPLEMENTATION.md` (access token expiry, refresh token expiry, and refresh rotation).

12.1.1 Endpoint summary (design intent)
NOTE: Some endpoint paths may differ from the exact implementation; the SRS expresses the intended contracts.
- POST /api/v1/auth/register/ — register a new user (name, email, password)
- POST /api/v1/auth/login/ — login, returns `access` and `refresh` JWT tokens
- POST /api/v1/auth/refresh/ — refresh access token using refresh token

12.2 API conventions
- All request/response payloads are JSON.
- Pagination: list endpoints SHALL support pagination (page/page_size or equivalent) to keep responses bounded.
- Filtering: list endpoints SHALL support relevant filtering fields as documented by each resource.
- Standard HTTP status codes: 200, 201, 204, 400, 401, 403, 404, 500.
- Validation errors return a structured error body consistent with `Backend/Uedcl/SECURITY_IMPLEMENTATION.md` custom exception handler.

12.3 Users

- GET /api/v1/users/ — list users (admin only)
- GET /api/v1/users/{id}/ — retrieve user profile
- PUT /api/v1/users/{id}/ — update user (admin or owner)

12.4 Projects
- GET /api/v1/projects/ — list projects (filter by owner, status)
- POST /api/v1/projects/ — create project (manager/admin)
- GET /api/v1/projects/{id}/ — project detail
- PUT /api/v1/projects/{id}/ — update project
- DELETE /api/v1/projects/{id}/ — archive/delete project

12.5 Tasks
- GET /api/v1/projects/{project_id}/tasks/ — list tasks for project
- POST /api/v1/projects/{project_id}/tasks/ — create task
- GET /api/v1/tasks/{id}/ — task detail
- PATCH /api/v1/tasks/{id}/ — partial update (status transitions)
- POST /api/v1/tasks/{id}/comments/ — add comment

12.6 Notifications
- GET /api/v1/notifications/ — list user notifications
- PATCH /api/v1/notifications/{id}/read/ — mark as read

12.7 Audit
- GET /api/v1/audit/?object_type=task&object_id=123 — audit trail for object

12.8 Example: Login request/response
Request: POST /api/v1/auth/login/
{
	"email": "user@example.com",
	"password": "P@ssw0rd"
}
Response (200):
{
	"access": "<jwt-access-token>",
	"refresh": "<jwt-refresh-token>",
	"user": {"id": 1, "email": "user@example.com", "role": "employee"}
}

13. Data Model (recommended)
13.1 Entity summary
- User: id, name, email, role, created_at, last_login
- Project: id, title, description, owner_id, status, start_date, end_date
- Task: id, title, description, project_id, assignee_id, priority, status, due_date, metadata
- Notification: id, user_id, type, payload, read, created_at
- AuditLog: id, actor_id, action, object_type, object_id, diff, timestamp


12.2 Users
- GET /api/v1/users/ — list users (admin only)
- GET /api/v1/users/{id}/ — retrieve user profile
- PUT /api/v1/users/{id}/ — update user (admin or owner)

12.3 Projects
- GET /api/v1/projects/ — list projects (filter by owner, status)
- POST /api/v1/projects/ — create project (manager/admin)
- GET /api/v1/projects/{id}/ — project detail
- PUT /api/v1/projects/{id}/ — update project
- DELETE /api/v1/projects/{id}/ — archive/delete project

12.4 Tasks
- GET /api/v1/projects/{project_id}/tasks/ — list tasks for project
- POST /api/v1/projects/{project_id}/tasks/ — create task
- GET /api/v1/tasks/{id}/ — task detail
- PATCH /api/v1/tasks/{id}/ — partial update (status transitions)
- POST /api/v1/tasks/{id}/comments/ — add comment
- POST /api/v1/tasks/{id}/attachments/ — upload attachment (validated)

12.5 Notifications
- GET /api/v1/notifications/ — list user notifications
- PATCH /api/v1/notifications/{id}/read/ — mark as read

12.6 Audit
- GET /api/v1/audit/?object_type=task&object_id=123 — audit trail for object

12.7 Example: Login request/response
Request: POST /api/v1/auth/login/
{
	"email": "user@example.com",
	"password": "P@ssw0rd"
}
Response (200):
{
	"access": "<jwt-access-token>",
	"refresh": "<jwt-refresh-token>",
	"user": {"id": 1, "email": "user@example.com", "role": "employee"}
}

13. Data Model (recommended)
13.1 Entity summary
- User(id PK, name, email unique, password_hash, role, created_at, last_login)
- Project(id PK, title, description, owner_id FK->User, status, start_date, end_date, created_at)
- Task(id PK, title, description, project_id FK->Project, assignee_id FK->User, priority, status, due_date, created_at, updated_at)
- Comment(id PK, task_id FK->Task, author_id FK->User, content, created_at)
- Attachment(id PK, task_id FK->Task, uploader_id FK->User, file_path, mime_type, size, created_at)
- Notification(id PK, user_id FK->User, type, payload JSON, read Boolean, created_at)
- AuditLog(id PK, actor_id FK->User, action, object_type, object_id, diff JSON, timestamp)

13.2 Simple SQL example (Tasks)
CREATE TABLE task (
	id INTEGER PRIMARY KEY,
	title TEXT NOT NULL,
	description TEXT,
	project_id INTEGER NOT NULL,
	assignee_id INTEGER,
	priority TEXT,
	status TEXT NOT NULL,
	due_date DATE,
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY(project_id) REFERENCES project(id),
	FOREIGN KEY(assignee_id) REFERENCES user(id)
);

13.3 Diagram
- Add an ER diagram (recommended: generate from Django models or use a diagram tool and include PNG/SVG in Appendix).

14. Security Checklist (recommended)
- Enforce HTTPS and HSTS in production.
- Use strong password hashing (Argon2 or bcrypt) and a password policy (min length, complexity, lockouts).
- Short-lived access tokens, rotate refresh tokens, support revocation.
- Validate and sanitize all inputs server-side; use parameterized queries (ORM protects by default).
- Protect against XSS/CSRF on the frontend; use CSRF tokens where needed and set secure cookie flags.
- Validate file uploads (size, type) and store outside web root or use object storage with signed URLs.
- Rate-limit authentication endpoints and critical APIs.
- Centralized logging and monitoring for suspicious activities; secure storage of logs.
- Secrets management: use env variables or a secrets manager; do not commit secrets to repo.

15. Test Plan (recommended)
- Unit tests: models, serializers, utilities (run via `pytest` / Django test runner).
- Integration tests: API endpoints with authentication flows and permissions.
- End-to-end tests: UI flows using Playwright or Cypress for critical paths (login, create project, assign task, update status).
- Load tests: simulate realistic workloads for dashboard queries and task creation.
- Security tests: dependency scanning, static analysis, and regular penetration testing.
- Acceptance tests: map to FR-* entries and verify with example datasets.

16. Deployment & Operations
- Environment variables: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET`, `SMTP_*`, `S3_*`.
- Use database migrations (Django migrations) on deploy; include health-check endpoints.
- Backups: scheduled DB backups and retention policy; test restore procedures periodically.
- Monitoring: application performance (APM), error tracking (Sentry), and system metrics.
- CI/CD: run linters, unit tests, and integration tests before merge; require PR reviews.

17. Risk Assessment & Mitigation
- Risk: Data loss due to DB corruption. Mitigation: daily backups, point-in-time recovery for production DB.
- Risk: Unauthorized access from weak tokens. Mitigation: enforce token expiry and rotation, monitor usage.
- Risk: Large file uploads causing storage issues. Mitigation: enforce size limits and use cloud storage.

18. Traceability Matrix (example)
- FR-1 (User Registration) -> Story: TKT-101 -> Tests: UT-Auth-01, IT-Auth-01
- FR-2 (Authentication & Authorization) -> Story: TKT-102 -> Tests: UT-Auth-02, IT-Auth-02, E2E-Login-01
- FR-4 (Task Management) -> Story: TKT-201 -> Tests: UT-Task-01, IT-Task-01, E2E-Task-Flow-01

Appendix: useful artifacts to add
- OpenAPI/Swagger JSON or YAML for the API surface.
- ER diagram (PNG/SVG) and an optional SQL schema dump for reference.
- Security checklist completion spreadsheet.

Revision History
- 0.2 (2026-07-06): Added API specs, data model summary, security checklist, test plan, deployment notes, risk assessment, and traceability matrix.

End of document.
