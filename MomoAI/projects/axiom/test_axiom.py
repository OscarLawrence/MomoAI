#!/usr/bin/env python3
"""
Axiom PWA Test Script
Quick verification that the implementation is working
"""

import asyncio
import json
import os
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    print("🔍 Testing file structure...")
    
    required_files = [
        # Backend files
        "axiom/backend/main.py",
        "axiom/backend/api/sessions.py",
        "axiom/backend/api/messages.py",
        "axiom/backend/core/anthropic_client.py",
        "axiom/backend/core/session_manager.py",
        "axiom/backend/core/contracts.py",
        "axiom/backend/tools/parser.py",
        "axiom/backend/tools/executor.py",
        
        # Frontend files
        "axiom/frontend/index.html",
        "axiom/frontend/manifest.json",
        "axiom/frontend/sw.js",
        "axiom/frontend/css/app.css",
        "axiom/frontend/js/api.js",
        "axiom/frontend/js/ui.js",
        "axiom/frontend/js/stages.js",
        "axiom/frontend/js/app.js",
        
        # Config files
        "pyproject.toml",
        ".env.example",
        "start.py",
        "start.sh",
        "start.bat"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files present")
    return True

def test_imports():
    """Test that Python modules can be imported"""
    print("🔍 Testing Python imports...")
    
    try:
        # Test backend imports
        import sys
        sys.path.insert(0, "axiom/backend")
        
        from core.contracts import contract_enforced
        from core.anthropic_client import AnthropicClient
        from core.session_manager import SessionManager
        from tools.parser import ToolCallParser
        from tools.executor import ToolExecutor
        
        print("✅ All Python modules import successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_tool_parser():
    """Test the tool call parser"""
    print("🔍 Testing tool call parser...")
    
    try:
        import sys
        sys.path.insert(0, "axiom/backend")
        from tools.parser import ToolCallParser
        
        parser = ToolCallParser()
        
        # Test parsing
        text = 'I need to read_file("/test.txt") and then write_file("/output.txt", "content")'
        tool_calls = parser.parse_tool_calls(text)
        
        if len(tool_calls) == 2:
            print("✅ Tool parser working correctly")
            return True
        else:
            print(f"❌ Expected 2 tool calls, got {len(tool_calls)}")
            return False
            
    except Exception as e:
        print(f"❌ Tool parser error: {e}")
        return False

def test_manifest_json():
    """Test that PWA manifest is valid JSON"""
    print("🔍 Testing PWA manifest...")
    
    try:
        with open("axiom/frontend/manifest.json", "r") as f:
            manifest = json.load(f)
        
        required_fields = ["name", "short_name", "start_url", "display", "icons"]
        for field in required_fields:
            if field not in manifest:
                print(f"❌ Missing required field in manifest: {field}")
                return False
        
        print("✅ PWA manifest is valid")
        return True
        
    except Exception as e:
        print(f"❌ Manifest error: {e}")
        return False

def test_env_example():
    """Test that .env.example has required variables"""
    print("🔍 Testing environment configuration...")
    
    try:
        with open(".env.example", "r") as f:
            content = f.read()
        
        required_vars = ["ANTHROPIC_API_KEY", "HOST", "PORT"]
        for var in required_vars:
            if var not in content:
                print(f"❌ Missing environment variable in .env.example: {var}")
                return False
        
        print("✅ Environment configuration is complete")
        return True
        
    except Exception as e:
        print(f"❌ Environment config error: {e}")
        return False

async def test_session_manager():
    """Test session manager functionality"""
    print("🔍 Testing session manager...")
    
    try:
        import sys
        sys.path.insert(0, "axiom/backend")
        from core.session_manager import SessionManager
        
        # Mock the API key for testing
        os.environ['ANTHROPIC_API_KEY'] = 'test-key'
        
        manager = SessionManager()
        session = manager.create_session()
        
        if session and session.id:
            print("✅ Session manager working correctly")
            return True
        else:
            print("❌ Session creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Session manager error: {e}")
        return False

def main():
    """Run all tests"""
    print("⚡ Axiom PWA Implementation Test")
    print("=" * 40)
    
    tests = [
        test_file_structure,
        test_imports,
        test_tool_parser,
        test_manifest_json,
        test_env_example,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    # Run async test
    try:
        if asyncio.run(test_session_manager()):
            passed += 1
            total += 1
        print()
    except Exception as e:
        print(f"❌ Async test failed: {e}")
        total += 1
        print()
    
    print("=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Implementation is ready.")
        print("\n🚀 To start Axiom PWA:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your ANTHROPIC_API_KEY to .env")
        print("   3. Run: ./start.sh (or start.bat on Windows)")
        print("   4. Open: http://localhost:8000")
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())