@echo off
set "params=%*"
cd /d "%~dp0" && ( if exist "%temp%\getadmin.vbs" del "%temp%\getadmin.vbs" ) && fsutil dirty query %systemdrive% 1>nul 2>nul || (  echo Set UAC = CreateObject^("Shell.Application"^) : UAC.ShellExecute "cmd.exe", "/c cd /d ""%~dp0"" && ""%~f0"" %params%", "", "runas", 1 >> "%temp%\getadmin.vbs" && "%temp%\getadmin.vbs" && exit /B )

echo ==========================================================
echo  Configuring local domain for Coding Practice Hub...
echo ==========================================================

findstr /i "coding-practice-hub" "%SystemRoot%\System32\drivers\etc\hosts" >nul
if %errorLevel% neq 0 (
    echo. >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo 127.0.0.1 coding-practice-hub >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo 127.0.0.1 coding-practice-hub.local >> "%SystemRoot%\System32\drivers\etc\hosts"
    echo [OK] Successfully added coding-practice-hub to hosts file!
) else (
    echo [INFO] coding-practice-hub is already in hosts file.
)

ipconfig /flushdns >nul
echo [OK] DNS cache flushed.
echo.
echo ==========================================================
echo  Configuration Successful!
echo  You can now open:
echo  http://coding-practice-hub/
echo  http://coding-practice-hub:5000/
echo ==========================================================
echo.
pause
