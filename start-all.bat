@echo off
echo Starting UEDCL Project Management System...
echo.

echo Starting Backend Server (Django)...
start "UEDCL Backend" cmd /k "cd Backend\Uedcl && python manage.py runserver"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo Starting Frontend Server (React + Vite)...
start "UEDCL Frontend" cmd /k "cd Frontend\uedcl && npm run dev"

echo.
echo Both servers are starting...
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
echo Press any key to close this window (servers will continue running)...
pause >nul
