@echo off
echo [Aira] Starting Aira (Single Port)...

:: Start Backend (Multi-Worker)
echo Starting Backend (FastAPI with Uvicorn Multi-Worker)...
echo You only need to tunnel Port 8000.
start "Aira Backend" cmd /k "call conda activate aira_back && cd backend && python run_server.py"


echo ---------------------------------------------------
echo Access Local: http://localhost:8000
echo Access External:
echo 1. Run 'ngrok http 8000'
echo 2. Open the https URL in your browser.
echo ---------------------------------------------------
pause
