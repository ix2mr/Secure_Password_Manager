@echo off
chcp 65001 >nul
title Secure Password Manager - مدير كلمات المرور الآمن
echo ==================================================
echo   مدير كلمات المرور الآمن (Secure Password Manager)
echo   مشروع تخرج - الأمن السيبراني 2026
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [خطأ] بايثون غير مثبت. رجاءً ثبّت Python 3.10 أو أحدث من python.org
    echo       مع تفعيل خيار Add to PATH أثناء التثبيت.
    pause
    exit /b 1
)

echo [1/2] تثبيت المكتبات المطلوبة (PySide6, argon2-cffi, cryptography)...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo [خطأ] فشل تثبيت المكتبات. تحقق من اتصال الإنترنت ثم أعد المحاولة.
    pause
    exit /b 1
)

echo.
echo [2/2] تشغيل التطبيق...
python "%~dp0main.py"
if errorlevel 1 pause
