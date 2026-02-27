@echo off
title Local AI Setup for Legal Work
echo ============================================
echo   Local AI Setup for Legal Work
echo   Windows Launcher
echo ============================================
echo.
echo This will open the setup script in PowerShell.
echo If prompted by Windows security, click "Yes" to allow.
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
