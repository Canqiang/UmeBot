

# ============== start.sh ==============
# !/bin/bash

echo
"🚀 Starting UMe Bot..."

# Check Python
if ! command -v python3 & > / dev / null; then
echo
"❌ Python 3 is not installed"
exit
1
fi

# Check Node
if ! command -v node & > / dev / null; then
echo
"❌ Node.js is not installed"
exit
1
fi

# Backend setup
echo
"📦 Setting up backend..."
cd
backend

# Create virtual environment
if [ ! -d "venv"]; then
python3 - m
venv
venv
echo
"✅ Virtual environment created"
fi

# Activate virtual environment
source
venv / bin / activate

# Install dependencies
pip
install - r
requirements.txt
echo
"✅ Backend dependencies installed"

# Start backend in background
echo
"🚀 Starting backend server..."
python
run.py &
BACKEND_PID =$!
echo
"✅ Backend started with PID: $BACKEND_PID"

# Frontend setup
cd.. / frontend
echo
"📦 Setting up frontend..."

# Install dependencies
if [ ! -d "node_modules"]; then
npm
install
echo
"✅ Frontend dependencies installed"
fi

# Start frontend
echo
"🚀 Starting frontend server..."
npm
run
dev &
FRONTEND_PID =$!
echo
"✅ Frontend started with PID: $FRONTEND_PID"

# Wait and handle shutdown
echo
""
echo
"========================================="
echo
"✅ UMe Bot is running!"
echo
"Frontend: http://localhost:3000"
echo
"Backend API: http://localhost:8000"
echo
"API Docs: http://localhost:8000/docs"
echo
"========================================="
echo
"Press Ctrl+C to stop all services"
echo
""

# Trap Ctrl+C
trap
cleanup
INT

cleanup()
{
    echo
""
echo
"🛑 Stopping services..."
kill $BACKEND_PID
2 > / dev / null
kill $FRONTEND_PID
2 > / dev / null
echo
"✅ All services stopped"
exit
0
}

# Keep script running
wait
