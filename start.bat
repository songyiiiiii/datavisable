@echo off
title Nyx Dashboard
echo ============================================
echo   Nyx Visual Analytics Dashboard
echo ============================================
echo.
echo [1/3] Checking port 5001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5001.*LISTENING"') do (
    echo   Killing old process on port 5001 (PID: %%a)
    taskkill /F /PID %%a >nul 2>nul
)
timeout /t 1 /nobreak >nul
echo   Port 5001 is free.
echo.
echo [2/3] Starting Python server...
echo   Loading 100 time steps (~800MB, please wait)...
echo.
cd /d "%~dp0"
"C:\Users\LENOVO\AppData\Local\Programs\Python\Python311\python.exe" app.py
echo.
echo [3/3] Server stopped.
pause
