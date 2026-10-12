@echo off
echo ===================================================
echo Starting RAS-RAG Backend API Server on Port 8000...
echo ===================================================
cd /d "%~dp0"
call ".\venv\Scripts\activate.bat"
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
pause
