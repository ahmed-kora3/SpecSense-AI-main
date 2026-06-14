@echo off
echo ===================================================
echo      Cable AI System - Inspection Tool
echo ===================================================
echo.
echo [INFO] Checking dependencies...
pip install -r requirements.txt
echo.
echo [INFO] Starting Inspection System...
echo.
python get_specs.py
echo.
echo [INFO] Process Complete.
pause
