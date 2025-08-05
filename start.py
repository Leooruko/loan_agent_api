#!/usr/bin/env python3
"""
Startup script for the Brightcom Loan Assistant API
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask', 'langchain', 'langchain-community', 
        'pandas', 'pandasql', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} - Missing")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages with: pip install -r requirements.txt")
        return False
    
    return True

def check_data_file():
    """Check if the data file exists"""
    data_file = Path("processed_data.csv")
    if data_file.exists():
        print(f"✅ Data file found: {data_file}")
        return True
    else:
        print(f"❌ Data file not found: {data_file}")
        print("Please ensure processed_data.csv exists in the project root")
        return False

def check_ollama():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            mistral_found = any('mistral' in model.get('name', '').lower() for model in models)
            if mistral_found:
                print("✅ Ollama is running with Mistral model")
                return True
            else:
                print("⚠️  Ollama is running but Mistral model not found")
                print("Please run: ollama pull mistral")
                return False
        else:
            print("❌ Ollama is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Ollama is not running")
        print("Please start Ollama with: ollama serve")
        return False

def create_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory exists")

def run_tests():
    """Run basic tests to verify functionality"""
    print("\n🧪 Running basic tests...")
    try:
        result = subprocess.run([sys.executable, "test_improvements.py"], 
                              capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            print("✅ Basic tests passed")
            return True
        else:
            print("❌ Basic tests failed")
            print("Error output:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def start_application():
    """Start the Flask application"""
    print("\n🚀 Starting Brightcom Loan Assistant API...")
    print("=" * 50)
    
    try:
        # Import and run the app
        from app import app
        print("✅ Application imported successfully")
        print(f"🌐 Server will be available at: http://localhost:5500")
        print("📊 Health check: http://localhost:5500/health")
        print("📚 API info: http://localhost:5500/api/info")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 50)
        
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5500
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🚀 Brightcom Loan Assistant API v2.0")
    print("=" * 50)
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_data_file():
        sys.exit(1)
    
    if not check_ollama():
        print("\n⚠️  Ollama issues detected. You can still try to start the application,")
        print("   but it may not work properly without Ollama running.")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    create_logs_directory()
    
    # Run tests if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        if not run_tests():
            print("\n❌ Tests failed. Please fix issues before starting the application.")
            sys.exit(1)
    
    # Start the application
    start_application()

if __name__ == "__main__":
    main() 