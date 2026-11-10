@echo off
cd /d "%~dp0"
call venv\Scripts\activate
echo Backend running on http://localhost:8000  (keep this window open)
uvicorn app.main:app --reload
pause
