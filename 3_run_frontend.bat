@echo off
cd /d "%~dp0frontend"
start "" http://localhost:5500
echo Frontend running on http://localhost:5500  (keep this window open)
"%~dp0venv\Scripts\python.exe" -m http.server 5500
pause
