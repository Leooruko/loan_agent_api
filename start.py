#!/usr/bin/env python3
"""
GreenCom Loan Assistant - Startup Script
This script provides a user-friendly way to start the loan assistant application
with proper error handling and setup checks.
"""

import os
import sys
import subprocess
import time
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
        'flask',
        'langchain',
        'langchain_community',
        'pandas',
        'pandasql',
        'requests'
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
        print("Please install missing packages using:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_data_file():
    """Check if the data file exists"""
    data_file = Path("processed_data.csv")
    if not data_file.exists():
        print("❌ Error: processed_data.csv not found")
        print("Please ensure the data file is in the project root directory")
        return False
    print("✅ Data file found")
    return True

def check_ollama():
    """Check if Ollama is running and accessible"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
    except:
        pass
    
    print("⚠️  Warning: Ollama might not be running")
    print("Please ensure Ollama is started with the Mistral model:")
    print("1. Start Ollama: ollama serve")
    print("2. Pull Mistral model: ollama pull mistral")
    print("3. Run Mistral: ollama run mistral")
    return False

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def start_application():
    """Start the Flask application"""
    print("\n🚀 Starting GreenCom Loan Assistant...")
    print("=" * 50)
    
    try:
        from app import app
        print("✅ Application loaded successfully")
        print(f"🌐 Web interface will be available at: http://localhost:5500")
        print(f"🔧 API health check: http://localhost:5500/health")
        print(f"📚 API documentation: http://localhost:5500/api/info")
        print("\nPress Ctrl+C to stop the application")
        print("=" * 50)
        
        app.run(debug=True, host="0.0.0.0", port=5500)
        
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        return False
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False

def main():
    """Main startup function"""
    print("🏦 GreenCom Loan Assistant - Startup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check dependencies
    print("\n📋 Checking dependencies...")
    if not check_dependencies():
        print("\nWould you like to install missing dependencies? (y/n): ", end="")
        if input().lower().startswith('y'):
            if not install_dependencies():
                return False
        else:
            return False
    
    # Check data file
    print("\n📊 Checking data file...")
    if not check_data_file():
        return False
    
    # Check Ollama (warning only)
    print("\n🤖 Checking Ollama...")
    check_ollama()
    
    # Start application
    return start_application()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 