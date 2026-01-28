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

# Function to check if potrace is installed
check_potrace() {
    if command -v potrace &> /dev/null; then
        return 0  # Potrace is installed
    else
        return 1  # Potrace is not installed
    fi
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install potrace based on OS
install_potrace() {
    local os=$(detect_os)
    
    echo "🔧 Potrace not found. Attempting to install..."
    
    case $os in
        macos)
            if command -v brew &> /dev/null; then
                echo "   Installing potrace via Homebrew..."
                brew install potrace || {
                    echo "❌ Error: Failed to install potrace via Homebrew"
                    echo "   Please install manually: brew install potrace"
                    return 1
                }
                echo "   ✅ Potrace installed successfully!"
                return 0
            else
                echo "❌ Error: Homebrew not found. Please install Homebrew first:"
                echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                echo "   Then run: brew install potrace"
                return 1
            fi
            ;;
        linux)
            if command -v apt-get &> /dev/null; then
                echo "   Installing potrace via apt-get (requires sudo)..."
                sudo apt-get update && sudo apt-get install -y potrace || {
                    echo "❌ Error: Failed to install potrace via apt-get"
                    echo "   Please install manually: sudo apt-get install potrace"
                    return 1
                }
                echo "   ✅ Potrace installed successfully!"
                return 0
            elif command -v yum &> /dev/null; then
                echo "   Installing potrace via yum (requires sudo)..."
                sudo yum install -y potrace || {
                    echo "❌ Error: Failed to install potrace via yum"
                    echo "   Please install manually: sudo yum install potrace"
                    return 1
                }
                echo "   ✅ Potrace installed successfully!"
                return 0
            elif command -v dnf &> /dev/null; then
                echo "   Installing potrace via dnf (requires sudo)..."
                sudo dnf install -y potrace || {
                    echo "❌ Error: Failed to install potrace via dnf"
                    echo "   Please install manually: sudo dnf install potrace"
                    return 1
                }
                echo "   ✅ Potrace installed successfully!"
                return 0
            else
                echo "❌ Error: No supported package manager found (apt-get, yum, or dnf)"
                echo "   Please install potrace manually for your Linux distribution"
                return 1
            fi
            ;;
        windows)
            echo "⚠️  Windows detected. Potrace installation via script is limited."
            echo "   Please install potrace using one of these methods:"
            echo "   1. Chocolatey: choco install potrace"
            echo "   2. Scoop: scoop install potrace"
            echo "   3. Manual: Download from http://potrace.sourceforge.net/"
            echo "   4. Or use WSL (Windows Subsystem for Linux) for automatic installation"
            read -p "   Press Enter after installing potrace to continue, or Ctrl+C to cancel..."
            # Check again after user installs
            if check_potrace; then
                echo "   ✅ Potrace found!"
                return 0
            else
                echo "   ⚠️  Potrace still not found. Continuing anyway (may fail at runtime)..."
                return 1
            fi
            ;;
        *)
            echo "⚠️  Unknown OS detected. Cannot auto-install potrace."
            echo "   Please install potrace manually for your system"
            echo "   Visit: http://potrace.sourceforge.net/"
            read -p "   Press Enter after installing potrace to continue, or Ctrl+C to cancel..."
            return 1
            ;;
    esac
}

# Trap Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Check for potrace installation
echo "🔍 Checking for Potrace installation..."
if ! check_potrace; then
    echo "⚠️  Potrace is not installed. It's required for DXF file generation."
    read -p "   Would you like to install it now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if ! install_potrace; then
            echo "⚠️  Potrace installation failed or was skipped."
            echo "   The server will start, but DXF generation may fail."
            read -p "   Press Enter to continue anyway, or Ctrl+C to cancel..."
        fi
    else
        echo "⚠️  Potrace installation skipped."
        echo "   The server will start, but DXF generation may fail."
        read -p "   Press Enter to continue anyway, or Ctrl+C to cancel..."
    fi
else
    echo "   ✅ Potrace is installed"
fi
echo ""

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
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 > /tmp/krafzen-backend.log 2>&1 &
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
    
    # Always check and install frontend dependencies (ensures packages are up-to-date after merges)
    if [ ! -d "node_modules" ]; then
        echo "📥 Installing frontend dependencies..."
        npm install || { echo "❌ Error: Failed to install frontend dependencies"; exit 1; }
    else
        echo "📥 Checking frontend dependencies..."
        npm install || { echo "❌ Error: Failed to install frontend dependencies"; exit 1; }
    fi
    
    # Check for npm vulnerabilities
    echo "🔍 Checking for npm security vulnerabilities..."
    if npm audit --audit-level=moderate &> /dev/null; then
        VULN_COUNT=$(npm audit --audit-level=moderate --json 2>/dev/null | grep -o '"vulnerabilities":[0-9]*' | grep -o '[0-9]*' || echo "0")
        if [ "$VULN_COUNT" != "0" ] && [ ! -z "$VULN_COUNT" ]; then
            echo "⚠️  Found $VULN_COUNT security vulnerabilities"
            read -p "   Would you like to try to fix them automatically? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "   Attempting to fix vulnerabilities..."
                if npm audit fix &> /dev/null; then
                    echo "   ✅ Vulnerabilities fixed (or already resolved)"
                else
                    echo "   ⚠️  Some vulnerabilities may require manual attention"
                    echo "   Run 'npm audit' for details, or 'npm audit fix --force' (use with caution)"
                fi
            else
                echo "   ⚠️  Skipping vulnerability fixes. Run 'npm audit fix' manually when ready."
            fi
        else
            echo "   ✅ No vulnerabilities found"
        fi
    else
        echo "   ⚠️  Could not check vulnerabilities (network issue or npm registry unavailable)"
        echo "   Run 'npm audit' manually when network is available"
    fi
    echo ""
    
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

