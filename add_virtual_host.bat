@echo off
echo ========================================================
echo  Configuring Virtual Host: coding-practice-hub
echo ========================================================

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [ATTENTION REQUIRED]
    echo This script must be run as Administrator to edit the Windows hosts file.
    echo.
    echo How to run:
    echo  1. Right-click on this file ("add_virtual_host.bat")
    echo  2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Adding virtual host mappings to %SystemRoot%\System32\drivers\etc\hosts ...
findstr /i "coding-practice-hub" "%SystemRoot%\System32\drivers\etc\hosts" >nul
if %errorLevel% neq 0 (
    echo. >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo 127.0.0.1 coding-practice-hub >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo 127.0.0.1 coding-practice-hub.local >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo [SUCCESS] Successfully mapped 127.0.0.1 to coding-practice-hub!
) else (
    echo [INFO] coding-practice-hub is already mapped in your hosts file.
)

ipconfig /flushdns >nul
echo [SUCCESS] Windows DNS cache flushed.
echo.
echo ========================================================
echo  Virtual Host configured successfully!
echo  Open in your browser:
echo    * http://coding-practice-hub:5000/
echo    * http://coding-practice-hub/
echo ========================================================
echo.
pause
