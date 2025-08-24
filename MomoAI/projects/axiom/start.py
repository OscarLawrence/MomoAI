#!/usr/bin/env python3
"""
Axiom Chat Startup Script
Starts the minimal web chat interface at http://localhost:8000
"""

import os
import sys
import signal
import subprocess
from pathlib import Path

def check_port_usage(port):
    """Check what's running on the given port."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], 
            capture_output=True, 
            text=True, 
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except FileNotFoundError:
        # lsof not available, try netstat
        try:
            result = subprocess.run(
                ["netstat", "-tlnp"], 
                capture_output=True, 
                text=True, 
                check=False
            )
            for line in result.stdout.split('\n'):
                if f":{port} " in line:
                    return line.strip()
            return None
        except FileNotFoundError:
            return "unknown"

def kill_process_on_port(port):
    """Kill process running on the given port."""
    try:
        result = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split()
            subprocess.run(["kill", "-9"] + pids, check=True)
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False

def find_free_port(start_port=8001, max_port=8010):
    """Find a free port starting from start_port."""
    for port in range(start_port, max_port + 1):
        if not check_port_usage(port):
            return port
    return None

def main():
    # Auto-resolve environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found!")
        print("Please set your Anthropic API key in a .env file:")
        print("ANTHROPIC_API_KEY=your_api_key_here")
        print("(The .env file will be auto-discovered up the directory tree)")
        sys.exit(1)
    
    # Check if port 8000 is in use
    port_usage = check_port_usage(8000)
    target_port = 8000
    
    if port_usage:
        # Check if it's Axiom running by looking at the process command line
        is_axiom = False
        try:
            result = subprocess.run(["lsof", "-ti", f":8000"], capture_output=True, text=True, check=True)
            if result.stdout.strip():
                pid = result.stdout.strip().split()[0]
                # Check the command line of the process
                cmd_result = subprocess.run(["ps", "-p", pid, "-o", "command="], capture_output=True, text=True, check=False)
                if cmd_result.returncode == 0:
                    command_line = cmd_result.stdout.strip()
                    if ("backend.main" in command_line or "start.py" in command_line or 
                        "axiom" in command_line.lower() or "uvicorn" in command_line):
                        is_axiom = True
        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            pass
        
        if is_axiom:
            print("🔄 Axiom is already running on port 8000, restarting...")
            kill_process_on_port(8000)
        else:
            print(f"⚠️  Port 8000 is in use by:")
            print(f"   {port_usage}")
            print()
            choice = input("Choose action: (k)ill process, (f)ind free port, or (q)uit: ").lower().strip()
            
            if choice == 'k':
                if kill_process_on_port(8000):
                    print("✅ Process killed")
                else:
                    print("❌ Failed to kill process")
                    sys.exit(1)
            elif choice == 'f':
                free_port = find_free_port()
                if free_port:
                    target_port = free_port
                    print(f"🔍 Using free port {target_port}")
                else:
                    print("❌ No free ports found in range 8001-8010")
                    sys.exit(1)
            else:
                print("👋 Exiting")
                sys.exit(0)
    
    print("🚀 Starting Axiom Chat...")
    print(f"📍 URL: http://localhost:{target_port}")
    print("💡 Use Ctrl+C to stop")
    
    # Set up graceful shutdown
    def signal_handler(sig, frame):
        print("\n👋 Axiom Chat stopped gracefully")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run from current directory, pointing to backend module
    try:
        import uvicorn
        uvicorn.run("backend.main:app", host="0.0.0.0", port=target_port, reload=False)
    except KeyboardInterrupt:
        print("\n👋 Axiom Chat stopped")
    except ImportError as e:
        print(e)
        print("❌ Dependencies not installed!")
        print("Run: pip install fastapi uvicorn httpx python-dotenv pydantic")
        sys.exit(1)

if __name__ == "__main__":
    main()