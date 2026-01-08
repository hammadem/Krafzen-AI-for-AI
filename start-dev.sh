#!/bin/bash

# Generic Development Server Startup Script
# Starts both backend and frontend servers for local development

echo "🚀 Starting KRAFZEN AI Development Environment"
echo "=============================================="
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
    if [ ! -z "$pid" ]; then
        echo "   ⚠️  Killing process $pid on port $port..."
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   ✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   ✅ Frontend stopped"
    fi
    if [ ! -z "$TAIL_PID" ]; then
        kill $TAIL_PID 2>/dev/null
        echo "   ✅ Log streamer stopped"
    fi
    exit 0
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Check backend port
if check_port 8000; then
    echo "⚠️  Backend port 8000 is in use. Stopping existing server..."
    kill_port 8000
fi

if true; then
    echo "📦 Starting Backend Server..."
    echo "   Backend will run on: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    
    cd backend || { echo "❌ Error: backend directory not found"; exit 1; }
    
    # Check for virtual environment
    if [ ! -d "venv" ]; then
        echo "⚠️  Virtual environment not found. Creating..."
        python3 -m venv venv || { echo "❌ Error: Failed to create virtual environment"; exit 1; }
        echo "📥 Installing backend dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt || { echo "❌ Error: Failed to install dependencies"; exit 1; }
    else
        source venv/bin/activate
        echo "📥 Checking backend dependencies..."
        pip install -r requirements.txt || { echo "❌ Error: Failed to install dependencies"; exit 1; }
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo "⚠️  .env file not found. Creating from env.example..."
        if [ -f "env.example" ]; then
            cp env.example .env
            echo "⚠️  Please update .env with your API keys before continuing!"
            echo "   Required: OPENAI_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY"
            read -p "Press Enter after updating .env to continue, or Ctrl+C to cancel..."
        else
            echo "⚠️  env.example not found. Please create .env manually."
            read -p "Press Enter to continue anyway, or Ctrl+C to cancel..."
        fi
    fi
    
    echo "🔄 Initializing Database Schema..."
    python app/db/init_db.py || { echo "⚠️  Database initialization failed. Continuing..."; }
    echo ""
    echo "🚀 Starting backend server..."
    echo "   (Press Ctrl+C to stop all servers)"
    echo ""
    uvicorn main:app --reload --port 8000 > /tmp/krafzen-backend.log 2>&1 &
    BACKEND_PID=$!
    echo "   Backend started with PID: $BACKEND_PID"
    cd ..
fi

# Wait a bit for backend to start
sleep 2

# Check if backend started successfully
if [ ! -z "$BACKEND_PID" ]; then
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Error: Backend failed to start. Check /tmp/krafzen-backend.log for details"
        exit 1
    fi
fi

# Check frontend port
if check_port 3000; then
    echo "⚠️  Frontend port 3000 is in use. Stopping existing server..."
    kill_port 3000
fi

if true; then
    echo ""
    echo "📦 Starting Frontend Server..."
    echo "   Frontend will run on: http://localhost:3000"
    echo ""
    
    cd frontend || { echo "❌ Error: frontend directory not found"; exit 1; }
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "📥 Installing frontend dependencies..."
        npm install || { echo "❌ Error: Failed to install frontend dependencies"; exit 1; }
    fi
    
    echo "🚀 Starting frontend server..."
    echo "   (Press Ctrl+C to stop all servers)"
    echo ""
    npm run dev > /tmp/krafzen-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "   Frontend started with PID: $FRONTEND_PID"
    cd ..
fi

# Wait a bit for frontend to start
sleep 3

echo ""
echo "=============================================="
echo "✅ Development Servers Started!"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo "📍 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f /tmp/krafzen-backend.log"
echo "   Frontend: tail -f /tmp/krafzen-frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "=============================================="
echo ""

# Stream logs to console
echo "📋 Streaming logs (Ctrl+C to stop)..."
# Using tail -f to stream logs from both files, forcing output to stdout
tail -f /tmp/krafzen-backend.log /tmp/krafzen-frontend.log &
TAIL_PID=$!

# Wait for user interrupt
wait

