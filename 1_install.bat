@echo off
cd /d "%~dp0"
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate
echo Installing libraries (can take 5-15 minutes)...
python -m pip install -r requirements.txt
if not exist .env (
  echo MOCK_MODE=true> .env
  echo USE_LLM=false>> .env
)
echo.
echo Done. If you saw no red ERROR lines, close this window.
pause
