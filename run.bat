@echo off
title Coding Practice Hub
echo ========================================================
echo  Starting Coding Practice Hub...
echo  Local URL: http://coding-practice-hub/
echo  Fallback:  http://localhost:5000/
echo ========================================================

:: Open browser after 2 seconds in background
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://coding-practice-hub/"

:: Run the Flask Application
python app.py

pause
