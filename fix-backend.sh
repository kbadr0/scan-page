#!/bin/bash

# Fix script for backend issues on Ubuntu VM

echo "🔧 Fixing backend issues..."

# Stop the backend service first
echo "Stopping backend service..."
sudo systemctl stop scan-backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating it..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing/updating Python dependencies..."
source venv/bin/activate

# Install required packages
pip install fastapi uvicorn python-gvm python-nmap pydantic

# Check if all imports work
echo "Testing imports..."
python3 -c "
try:
    from fastapi import FastAPI
    from gvm.connections import TLSConnection
    from gvm.protocols.gmp import Gmp
    import nmap
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Import test failed. Please check the error above."
    exit 1
fi

# Test basic backend startup
echo "Testing backend startup..."
python3 -c "
from backend import app
print('✅ Backend app created successfully')
"

if [ $? -ne 0 ]; then
    echo "❌ Backend startup test failed. Please check the error above."
    exit 1
fi

# Restart the backend service
echo "Restarting backend service..."
sudo systemctl restart scan-backend

# Wait a moment for service to start
sleep 3

# Check service status
echo "Checking service status..."
sudo systemctl status scan-backend --no-pager

# Test if backend is responding
echo "Testing backend response..."
curl -s http://localhost:8000/ || echo "❌ Backend not responding"

echo "🔧 Fix completed!" 