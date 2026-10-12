@echo off
echo ===================================================
echo Starting RAS-RAG Vite Frontend on Port 5173...
echo ===================================================
cd /d "%~dp0\frontend"
call npm.cmd run dev
pause
