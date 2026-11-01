@echo off
setlocal
echo ========================================================
echo   SmartPark AI - Local Intelligent Parking Facility
echo ========================================================
echo.

if not exist "smartpark-env\Scripts\python.exe" (
    echo [ERROR] Virtual environment 'smartpark-env' not found.
    echo Please run installation setup first.
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
call smartpark-env\Scripts\activate.bat

echo [2/3] Verifying database and trained models...
smartpark-env\Scripts\python.exe -c "from database.models import init_db; init_db(); print('Database ready.')"

echo [3/3] Starting SmartPark AI Local Server on http://127.0.0.1:8000 ...
echo.
echo ========================================================
echo  Access Interfaces:
echo   - Home Portal:      http://127.0.0.1:8000/
echo   - Driver Entry:     http://127.0.0.1:8000/entry
echo   - Parking Monitor:  http://127.0.0.1:8000/parking
echo   - Guard Dashboard:  http://127.0.0.1:8000/guard
echo   - Driver Exit:      http://127.0.0.1:8000/exit
echo.
echo  Default Guard Credentials:
echo   - Username: guard_admin
echo   - Password: GuardPass@2026
echo ========================================================
echo.

smartpark-env\Scripts\python.exe app.py
pause

