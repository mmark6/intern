<<<<<<< HEAD
# UEDCL Project Management System

A full-stack project management application with Django REST Framework backend and React frontend.

## Project Structure

- `Backend/` - Django REST Framework API
  - Django 6.0.2
  - REST Framework with JWT authentication
  - SQLite database (configurable for PostgreSQL)
  - Apps: users, login, projects, tasks, comments, dashboard

- `Frontend/` - React + Vite frontend
  - React 19.2.6
  - Vite 8.0.12
  - React Router for navigation
  - Lucide React icons

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
```bash
cd Backend
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
cd Uedcl
python manage.py migrate
```

5. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

6. Start the Django development server:
```bash
python manage.py runserver
```

The backend will run on `http://127.0.0.1:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd Frontend/uedcl
```

2. Install dependencies:
```bash
npm install
```

3. Start the Vite development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:5173`

## Running Both Servers

### Option 1: Manual (Two Terminal Windows)

**Terminal 1 - Backend:**
```bash
cd Backend/Uedcl
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd Frontend/uedcl
npm run dev
```

### Option 2: Using the Start Script (Windows)

Run the provided batch script to start both servers:
```bash
start-all.bat
```

This will open two terminal windows with the backend and frontend servers running.

## API Configuration

The frontend is configured to proxy API requests to the backend through Vite:

- Frontend: `http://localhost:5173`
- Backend API: `http://127.0.0.1:8000/api/`
- Proxy: All `/api/*` requests are forwarded to the backend

CORS is configured in Django settings to allow requests from the frontend.

## API Endpoints

### Authentication
- `POST /api/login/login/` - User login
- `POST /api/login/register/` - User registration
- `POST /api/login/logout/` - User logout
- `GET /api/login/me/` - Get current user

### Users
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/` - Get user details
- `GET /api/users/me/` - Get current user profile

### Projects
- `GET /api/projects/` - List projects
- `POST /api/projects/create/` - Create project
- `PATCH /api/projects/{id}/update/` - Update project
- `DELETE /api/projects/{id}/delete/` - Delete project

### Tasks
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/create/` - Create task
- `PATCH /api/tasks/{id}/update/` - Update task
- `DELETE /api/tasks/{id}/delete/` - Delete task

### Comments
- `GET /api/comments/` - List comments
- `POST /api/comments/` - Create comment

### Dashboard
- `GET /api/dashboard/` - Get dashboard statistics

## Authentication

The application uses JWT (JSON Web Tokens) for authentication:

1. Login returns an access token
2. Token is stored in localStorage as `uedcl_access_token`
3. Token is sent in the Authorization header: `Bearer {token}`
4. Access tokens expire after 15 minutes
5. Refresh tokens expire after 7 days

## Default Users

The frontend includes seed users for testing:
- Admin: `admin@uedcl.co.ug` / `Admin123!`
- Manager: `manager@uedcl.co.ug` / `Manager123!`
- Staff: `staff@uedcl.co.ug` / `Staff123!`

## Development

### Backend Development
- Django admin: `http://127.0.0.1:8000/admin/`
- API documentation: Use Django REST Framework's browsable API at any endpoint

### Frontend Development
- The frontend uses a proxy to forward API requests to the backend
- Hot module replacement is enabled
- ESLint is configured for code quality

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in Django settings
2. Configure a production database (PostgreSQL recommended)
3. Set up proper CORS origins
4. Build the frontend: `npm run build`
5. Serve the frontend static files through Django or a CDN
6. Use a production WSGI server (Gunicorn)
7. Configure environment variables for sensitive data

## Troubleshooting

### CORS Errors
- Ensure the backend CORS settings include your frontend URL
- Check that the backend is running on port 8000

### Connection Refused
- Verify both servers are running
- Check that ports 8000 and 5173 are not in use by other applications

### Authentication Issues
- Clear browser localStorage
- Check that the JWT token is being sent in the Authorization header
- Verify token expiration times in Django settings
=======
# intern
>>>>>>> origin/main
