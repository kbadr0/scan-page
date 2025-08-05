#!/bin/bash

# Combined setup and fix script for vulnerability scanner web app on Debian 12

# Exit on any error
set -e

echo "Setting up vulnerability scanner web app on Debian 12..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please do not run this script as root. Run as a regular user with sudo privileges."
    exit 1
fi

# -------------------------------
# SYSTEM SETUP
# -------------------------------

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx nmap git curl

# -------------------------------
# PROJECT SETUP
# -------------------------------

# Create project directory
echo "Setting up project directory..."
mkdir -p /home/$USER/scan-app
cd /home/$USER/scan-app

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install fastapi uvicorn python-gvm python-nmap pydantic

# -------------------------------
# BACKEND SERVICE SETUP
# -------------------------------

# Create systemd service for the backend
echo "Creating systemd service for backend..."
sudo tee /etc/systemd/system/scan-backend.service > /dev/null <<EOF
[Unit]
Description=Vulnerability Scanner Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/scan-app
Environment=PATH=/home/$USER/scan-app/venv/bin
ExecStart=/home/$USER/scan-app/venv/bin/uvicorn backend:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the backend service
sudo systemctl daemon-reload
sudo systemctl enable scan-backend
sudo systemctl start scan-backend

# -------------------------------
# NGINX CONFIGURATION
# -------------------------------

# Configure nginx
echo "Configuring nginx..."
sudo tee /etc/nginx/sites-available/scan-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Serve static files (frontend)
    location / {
        root /home/$USER/scan-app;
        index index.html;
        try_files \$uri \$uri/ =404;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the nginx site
sudo ln -sf /etc/nginx/sites-available/scan-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# -------------------------------
# PERMISSIONS AND TESTING
# -------------------------------

# Set proper permissions for the user
echo "Setting proper permissions..."
sudo chown -R $USER:$USER /home/$USER/scan-app
sudo chmod 755 /home/$USER/
sudo chmod 755 /home/$USER/scan-app/
sudo chown -R www-data:www-data /home/$USER/scan-app/

# Test backend functionality
echo "Testing backend functionality..."

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

# Restart services to ensure everything is fresh
echo "Restarting services..."
sudo systemctl restart scan-backend
sudo systemctl restart nginx

# Wait a moment for service to start
sleep 3

# Check service status
echo "Checking service status..."
sudo systemctl status scan-backend --no-pager

# Test if backend is responding
echo "Testing backend response..."
curl -s http://localhost:8000/ || echo "❌ Backend not responding"

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy your project files to /home/$USER/scan-app/"
echo "2. Make sure OpenVAS Docker container is running (if using)"
echo "3. Access the web app at: http://$(hostname -I | awk '{print $1}')"
echo "4. Check backend status: sudo systemctl status scan-backend"
echo "5. Check nginx status: sudo systemctl status nginx"
echo ""
echo "To view logs:"
echo "  Backend: sudo journalctl -u scan-backend -f"
echo "  Nginx: sudo tail -f /var/log/nginx/access.log"