#!/usr/bin/env python3
"""
Axiom PWA Startup Script with Coherence Validation
Starts the complete Axiom system with coherence pipeline enabled
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        print("  ✅ FastAPI and Uvicorn available")
    except ImportError:
        print("  ❌ FastAPI/Uvicorn not found. Install with: pip install fastapi uvicorn")
        return False
    
    try:
        import anthropic
        print("  ✅ Anthropic client available")
    except ImportError:
        print("  ❌ Anthropic client not found. Install with: pip install anthropic")
        return False
    
    # Check for .env file
    env_file = Path("axiom/.env")
    if not env_file.exists():
        print("  ⚠️  No .env file found. Copy .env.example and add your API key")
        return False
    else:
        print("  ✅ Environment configuration found")
    
    return True

def start_backend():
    """Start the FastAPI backend with coherence validation"""
    print("🚀 Starting Axiom backend with coherence validation...")
    
    os.chdir("axiom/backend")
    
    # Start uvicorn server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload",
        "--log-level", "info"
    ]
    
    return subprocess.Popen(cmd)

def wait_for_server():
    """Wait for the server to be ready"""
    print("⏳ Waiting for server to start...")
    
    import requests
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:8000/")
            if response.status_code == 200:
                print("  ✅ Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        time.sleep(1)
        print(f"  ... waiting ({i+1}/30)")
    
    print("  ❌ Server failed to start")
    return False

def test_coherence_endpoints():
    """Test coherence validation endpoints"""
    print("🧠 Testing coherence validation endpoints...")
    
    import requests
    
    # Test input validation
    try:
        response = requests.post(
            "http://localhost:8000/api/coherence/validate-input",
            json={"content": "Create an efficient sorting algorithm"}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Input validation: {result['level']} (Score: {result['score']:.2f})")
        else:
            print(f"  ❌ Input validation failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Input validation error: {e}")
    
    # Test output validation
    try:
        test_code = '''
@coherence_contract(
    input_types={"x": "int"},
    output_type="int",
    complexity_time="O(1)",
    pure=True
)
def double(x: int) -> int:
    return x * 2
        '''
        
        response = requests.post(
            "http://localhost:8000/api/coherence/validate-output",
            json={"content": test_code}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Output validation: Contracts={result['has_contracts']}, Valid={result['contracts_valid']}")
        else:
            print(f"  ❌ Output validation failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Output validation error: {e}")

def open_browser():
    """Open the PWA in browser"""
    print("🌐 Opening Axiom PWA...")
    
    url = "http://localhost:8000"
    try:
        webbrowser.open(url)
        print(f"  ✅ Opened {url}")
    except Exception as e:
        print(f"  ⚠️  Could not open browser automatically: {e}")
        print(f"  📱 Please open {url} manually")

def main():
    """Main startup sequence"""
    print("🎯 Axiom PWA with Coherence Validation")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install required packages.")
        return 1
    
    # Start backend
    backend_process = None
    try:
        backend_process = start_backend()
        
        # Wait for server
        if not wait_for_server():
            return 1
        
        # Test coherence endpoints
        test_coherence_endpoints()
        
        # Open browser
        open_browser()
        
        print("\n" + "=" * 50)
        print("🎉 Axiom PWA is running with coherence validation!")
        print("\n📋 Features enabled:")
        print("  • Real-time input coherence validation")
        print("  • AI output contract verification")
        print("  • Formal contract system")
        print("  • Mathematical complexity validation")
        print("  • Contradiction detection and suggestions")
        print("\n🔧 Controls:")
        print("  • Ctrl+H: Toggle coherence settings")
        print("  • Ctrl+C: Stop server")
        print("\n🌐 Access: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        
        # Keep running
        print("\n⏳ Server running... Press Ctrl+C to stop")
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        print("✅ Axiom stopped")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if backend_process:
            backend_process.terminate()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())