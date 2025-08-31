@echo off
echo Starting SEO Analyzer...

echo.
echo [1/3] Starting Backend (FastAPI)...
start "SEO Analyzer Backend" cmd /k "cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python main.py"

echo.
echo [2/3] Starting Frontend (Next.js)...
start "SEO Analyzer Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo [3/3] Starting LLM Worker (Background)...
start "SEO Analyzer Worker" cmd /k "cd backend && venv\Scripts\activate && python llm_worker.py"

echo.
echo ========================================
echo SEO Analyzer is starting up!
echo ========================================
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:5000/docs
echo ========================================
echo.
echo Press any key to close this window...
pause > nul
