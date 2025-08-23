@echo off
REM Axiom PWA Startup Script (Windows)
REM Simple script to start the Axiom PWA server

echo ⚡ Axiom PWA - Coherent AI Collaboration Platform
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check for .env file
if not exist ".env" (
    echo ⚠️  Warning: .env file not found
    if "%ANTHROPIC_API_KEY%"=="" (
        echo ❌ ANTHROPIC_API_KEY not set
        echo    Please set your Anthropic API key:
        echo    set ANTHROPIC_API_KEY=your_key_here
        echo    or create a .env file with ANTHROPIC_API_KEY=your_key_here
        pause
        exit /b 1
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -e .

REM Start the server
echo.
echo 🚀 Starting Axiom PWA server...
echo 🌐 Server will be available at:
echo    http://localhost:8000
echo    http://127.0.0.1:8000
echo.
echo 💡 Press Ctrl+C to stop the server
echo ==================================================

cd axiom\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause