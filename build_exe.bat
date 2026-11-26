@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  [1/2] Building SecurePasswordManager.exe with PyInstaller
echo ============================================================
echo.

rem ---- Find Python launcher ----
set "PY="
where py >nul 2>nul && set "PY=py"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto :nopython

%PY% --version
if errorlevel 1 goto :pyfail

rem ---- Build virtual environment ----
if not exist ".venv-build\Scripts\python.exe" (
    echo Creating build environment .venv-build ...
    %PY% -m venv .venv-build
    if errorlevel 1 goto :venvfail
)
call ".venv-build\Scripts\activate.bat"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt "pyinstaller>=6.10,<7"
if errorlevel 1 goto :pipfail

rem ---- Run PyInstaller ----
python -m PyInstaller --noconfirm --clean SecurePasswordManager.spec
if errorlevel 1 goto :buildfail

if not exist "dist\SecurePasswordManager.exe" goto :buildfail

echo.
echo [OK] Built: dist\SecurePasswordManager.exe
echo      Next step: run build_installer.bat to create Setup.exe
if "%NOPAUSE%"=="" pause
exit /b 0

:nopython
echo [ERROR] Python was not found.
echo         Install Python 3.10+ from https://www.python.org/downloads/
echo         and enable "Add python.exe to PATH" during installation.
if "%NOPAUSE%"=="" pause
exit /b 1

:pyfail
echo [ERROR] Python launcher failed to run.
if "%NOPAUSE%"=="" pause
exit /b 1

:venvfail
echo [ERROR] Failed to create virtual environment.
if "%NOPAUSE%"=="" pause
exit /b 1

:pipfail
echo [ERROR] Failed to install requirements. Check internet connection.
if "%NOPAUSE%"=="" pause
exit /b 1

:buildfail
echo [ERROR] PyInstaller build failed. Read the log above.
if "%NOPAUSE%"=="" pause
exit /b 1
