@echo off
echo [Aira] Starting Aira (Single Port)...

:: Start Backend (which serves Frontend)
echo Starting Backend Server on Port 8000...
echo You only need to tunnel Port 8000.
start "Aira Server" cmd /k "conda activate aira_back && cd backend && uvicorn server:app --host 0.0.0.0 --port 8000 --reload"

echo ---------------------------------------------------
echo Access Local: http://localhost:8000
echo Access External:
echo 1. Run 'ngrok http 8000'
echo 2. Open the https URL in your browser.
echo ---------------------------------------------------
pause
