#!/bin/bash

echo "Starting SEO Analyzer..."

echo ""
echo "[1/3] Starting Backend (FastAPI)..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py &
BACKEND_PID=$!
cd ..

echo ""
echo "[2/3] Starting Frontend (Next.js)..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "[3/3] Starting LLM Worker (Background)..."
cd backend
source venv/bin/activate
python llm_worker.py &
WORKER_PID=$!
cd ..

echo ""
echo "========================================"
echo "SEO Analyzer is running!"
echo "========================================"
echo "Backend:  http://localhost:5000"
echo "Frontend: http://localhost:3000"
echo "API Docs: http://localhost:5000/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $BACKEND_PID $FRONTEND_PID $WORKER_PID 2>/dev/null
    echo "All services stopped."
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for processes
wait
