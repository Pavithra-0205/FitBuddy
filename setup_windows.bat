@echo off
setlocal
py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env

echo.
echo Setup complete.
echo Edit .env and add your GEMINI_API_KEY, then run run_windows.bat
pause
