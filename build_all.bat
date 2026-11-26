@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   Secure Password Manager - Full Windows build
echo   Step 1/2: EXE  (PyInstaller)  -  Step 2/2: Setup.exe (Inno Setup)
echo ============================================================
echo   Requirements (one time):
echo     - Python 3.10 or newer  https://www.python.org/downloads/
echo     - Inno Setup 6 (free)   https://jrsoftware.org/isdl.php
echo     - Internet connection for the first build (pip download)
echo ============================================================
echo.

set "NOPAUSE=1"

call build_exe.bat
if errorlevel 1 (
    echo.
    echo [ABORTED] EXE build failed. Setup.exe was not created.
    pause
    exit /b 1
)

call build_installer.bat
if errorlevel 1 (
    echo.
    echo [ABORTED] Installer build failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   [DONE] Final deliverables:
echo     dist\SecurePasswordManager.exe
echo     installer\Output\SecurePasswordManager_Setup.exe
echo.
echo   The Setup.exe installs the app, creates a desktop shortcut
echo   and a Start-menu item, and uninstalls normally while KEEPING
echo   user data in %APPDATA%\SecurePasswordManager unless deletion
echo   is explicitly requested during uninstall.
echo ============================================================
pause
