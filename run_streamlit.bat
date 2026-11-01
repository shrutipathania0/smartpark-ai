@echo off
setlocal
echo ========================================================
echo   SmartPark AI - Streamlit Dashboard
echo ========================================================
echo.

if not exist "smartpark-env\Scripts\streamlit.exe" (
    echo [ERROR] Streamlit is not installed in smartpark-env.
    pause
    exit /b 1
)

echo Starting Streamlit on http://localhost:8501 ...
echo.
smartpark-env\Scripts\streamlit.exe run streamlit_app.py
pause
