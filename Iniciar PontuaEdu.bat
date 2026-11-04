@echo off
chcp 65001 >nul
title PontuaEdu
cd /d "%~dp0"

echo Iniciando o servidor do PontuaEdu (porta 8000)...
start "PontuaEdu - servidor" /min backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000

echo Iniciando o app (porta 8082)...
start "PontuaEdu - app" /min backend\.venv\Scripts\python.exe -m http.server 8082 --directory dist

timeout /t 3 /nobreak >nul
start "" http://localhost:8082

echo.
echo PontuaEdu aberto em http://localhost:8082
echo Para desligar, feche as janelas "PontuaEdu - servidor" e "PontuaEdu - app".
timeout /t 8 >nul
