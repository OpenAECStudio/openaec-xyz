@echo off
rem Dubbelklik om Y-Next lokaal te installeren of te starten (Windows, Docker Desktop).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installeer.ps1" %*
echo.
pause
