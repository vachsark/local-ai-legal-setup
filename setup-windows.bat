@echo off
title Local AI Setup for Legal Work

:: Check if already running as admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator access...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ============================================
echo   Local AI Setup for Legal Work
echo   Windows Launcher
echo ============================================
echo.
echo This will open the setup script in PowerShell.
echo.
pause

:: Run the PowerShell script from the same folder as this .bat file
:: -ExecutionPolicy Bypass: allows the downloaded script to run
:: "%~dp0": resolves to this .bat file's directory (handles spaces in path)
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0setup-windows.ps1"

echo.
echo ============================================
echo   Setup script finished.
echo ============================================
echo.
pause
