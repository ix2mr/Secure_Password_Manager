@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  [2/2] Creating SecurePasswordManager_Setup.exe (Inno Setup)
echo ============================================================
echo.

if not exist "dist\SecurePasswordManager.exe" (
    echo [ERROR] dist\SecurePasswordManager.exe was not found.
    echo         Run build_exe.bat first.
    if "%NOPAUSE%"=="" pause
    exit /b 1
)

rem ---- Locate Inno Setup 6 compiler ----
set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC goto :noinno

"%ISCC%" "installer\SecurePasswordManager.iss"
if errorlevel 1 goto :isccfail

if not exist "installer\Output\SecurePasswordManager_Setup.exe" goto :isccfail

echo.
echo [OK] Installer created: installer\Output\SecurePasswordManager_Setup.exe
if "%NOPAUSE%"=="" pause
exit /b 0

:noinno
echo [ERROR] Inno Setup 6 was not found.
echo         Install the free edition from: https://jrsoftware.org/isdl.php
echo         then re-run this script.
if "%NOPAUSE%"=="" pause
exit /b 1

:isccfail
echo [ERROR] Inno Setup compilation failed. Read the log above.
if "%NOPAUSE%"=="" pause
exit /b 1
