#!/usr/bin/env python3
"""
Production startup script for the Loan Agent API
Uses optimized Gunicorn configuration to handle AI workloads
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_prerequisites():
    """Check if all prerequisites are met"""
    logger.info("Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ required")
        return False
    
    # Check if data file exists
    if not os.path.exists('processed_data.csv'):
        logger.error("Data file 'processed_data.csv' not found")
        return False
    
    # Check if logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Check if Gunicorn is installed
    try:
        import gunicorn
        logger.info("Gunicorn is available")
    except ImportError:
        logger.error("Gunicorn not installed. Install with: pip install gunicorn")
        return False
    
    # Check if Ollama is running
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            logger.info("Ollama is running")
        else:
            logger.error("Ollama is not responding properly")
            return False
    except Exception as e:
        logger.error(f"Ollama check failed: {e}")
        return False
    
    # Check if Mistral model is available
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        models = response.json().get('models', [])
        mistral_available = any('mistral' in model.get('name', '').lower() for model in models)
        
        if mistral_available:
            logger.info("Mistral model is available")
        else:
            logger.warning("Mistral model not found. You may need to pull it: ollama pull mistral")
    except Exception as e:
        logger.warning(f"Could not check Mistral model: {e}")
    
    logger.info("All prerequisites checked")
    return True

def start_gunicorn():
    """Start the application with Gunicorn"""
    logger.info("Starting Loan Agent API with Gunicorn...")
    
    # Gunicorn command with optimized settings
    cmd = [
        'gunicorn',
        '--config', 'gunicorn_config.py',
        '--bind', '0.0.0.0:5500',
        '--timeout', '120',  # 2 minutes timeout
        '--workers', '3',    # Start with 3 workers
        '--worker-class', 'sync',
        '--preload',         # Preload the application
        '--access-logfile', 'logs/gunicorn_access.log',
        '--error-logfile', 'logs/gunicorn_error.log',
        '--log-level', 'info',
        '--capture-output',
        'app:app'
    ]
    
    try:
        logger.info(f"Starting with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment to see if it starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            logger.info(f"Gunicorn started successfully with PID: {process.pid}")
            logger.info("API is running at: http://localhost:5500")
            logger.info("Press Ctrl+C to stop")
            
            # Wait for the process
            try:
                process.wait()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                process.terminate()
                process.wait()
                logger.info("Server stopped")
        else:
            stdout, stderr = process.communicate()
            logger.error(f"Gunicorn failed to start:")
            logger.error(f"STDOUT: {stdout.decode()}")
            logger.error(f"STDERR: {stderr.decode()}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to start Gunicorn: {e}")
        return False
    
    return True

def start_development():
    """Start the application in development mode"""
    logger.info("Starting Loan Agent API in development mode...")
    
    cmd = [
        sys.executable, 'app.py'
    ]
    
    try:
        logger.info(f"Starting with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        logger.info("API is running at: http://localhost:5500")
        logger.info("Press Ctrl+C to stop")
        
        process.wait()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        process.terminate()
        process.wait()
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 Loan Agent API - Production Startup")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        logger.error("Prerequisites check failed. Please fix the issues above.")
        sys.exit(1)
    
    # Ask user for mode
    print("\nChoose startup mode:")
    print("1. Production (Gunicorn) - Recommended for production")
    print("2. Development (Flask) - For development/testing")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    # Start the appropriate mode
    if choice == '1':
        logger.info("Starting in PRODUCTION mode with Gunicorn")
        success = start_gunicorn()
    else:
        logger.info("Starting in DEVELOPMENT mode with Flask")
        success = start_development()
    
    if not success:
        logger.error("Failed to start the application")
        sys.exit(1)

if __name__ == "__main__":
    main() 