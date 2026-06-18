@echo off
chcp 65001 >nul
echo ============================================
echo Nyx Visual Analytics Dashboard
echo ============================================
echo.
echo Killing old Python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM python3.11.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo Starting server on http://127.0.0.1:9050 ...
echo.
cd /d "e:\数据可视化"
C:\Users\LENOVO\AppData\Local\Programs\Python\Python311\python.exe app.py
pause
