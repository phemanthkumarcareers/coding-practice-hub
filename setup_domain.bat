@echo off
:: Self-elevate to Administrator if not already elevated
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges to update Windows hosts file...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

echo Configuring local domain: coding-practice-hub -> 127.0.0.1 ...
findstr /i "coding-practice-hub" "%SystemRoot%\System32\drivers\etc\hosts" >nul
if %errorLevel% equ 0 (
    echo Entry already exists in %SystemRoot%\System32\drivers\etc\hosts
) else (
    echo. >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo 127.0.0.1 coding-practice-hub >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo Added: 127.0.0.1 coding-practice-hub
)

ipconfig /flushdns >nul
echo.
echo ========================================================
echo  Success! Local domain configured:
echo  http://coding-practice-hub/
echo ========================================================
timeout /t 3 >nul
