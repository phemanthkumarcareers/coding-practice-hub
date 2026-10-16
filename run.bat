@echo off
title Coding Practice Hub
echo ========================================================
echo  Starting Coding Practice Hub...
echo  Local URL: http://localhost:5000
echo ========================================================

:: Open browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:5000"

:: Run the Flask Application
python app.py

pause
