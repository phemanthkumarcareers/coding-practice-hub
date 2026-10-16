@echo off
:: Check for Administrator permissions
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Please right-click this file and select "Run as administrator"!
    echo.
    pause
    exit /b
)

echo Adding local domain mappings to Windows hosts file...

findstr /i "coding-practice-hub" "%SystemRoot%\System32\drivers\etc\hosts" >nul
if %errorLevel% neq 0 (
    echo 127.0.0.1 coding-practice-hub >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo 127.0.0.1 coding-practice-hub.local >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo [OK] Added coding-practice-hub to hosts file.
) else (
    echo [INFO] coding-practice-hub already present in hosts file.
)

ipconfig /flushdns >nul
echo [OK] DNS cache flushed.
echo.
echo ==========================================================
echo  Configuration Successful!
echo  You can now open: http://coding-practice-hub/
echo ==========================================================
echo.
pause
