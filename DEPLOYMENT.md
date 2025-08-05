# Deployment Guide - Ubuntu VM Setup

This guide explains how to deploy the vulnerability scanner web application on the Ubuntu VM where OpenVAS is running.

## 🎯 Why Ubuntu VM Deployment is Required

The web application **must** run on the Ubuntu VM (not Windows) because:

1. **Network Access**: Only the Ubuntu VM can access the target network via VPN
2. **Nmap Scanning**: Network discovery requires direct access to the target network
3. **OpenVAS Integration**: Direct communication with OpenVAS container

## 🚀 Quick Deployment

### Step 1: Transfer Files to Ubuntu VM
```bash
# From your Windows machine, copy files to Ubuntu VM
scp -r /path/to/scan-page user@192.168.1.38:/home/user/scan-app
#scp -r "C:\Users\msi\Desktop\stage ete\scan-page" ubuntu@192.168.1.38:/home/ubuntu/scan-app
```

### Step 2: Run Setup Script (FIXED)
```bash
# On Ubuntu VM - IMPORTANT: Run as regular user, not root
cd /home/user/scan-app

# Make sure the script is executable
chmod +x setup-ubuntu-vm.sh

# Run the script (it will use sudo internally)
./setup-ubuntu-vm.sh
```

**⚠️ Important Notes:**
- **DO NOT** run the script as root (`sudo ./setup-ubuntu-vm.sh`)
- Run as a regular user with sudo privileges
- The script will handle sudo commands internally
- If you get "Permission denied", make sure the file is executable: `chmod +x setup-ubuntu-vm.sh`

### Step 3: Start OpenVAS Container
```bash
# Make sure OpenVAS is running
docker run -d -p 9390:9390 -p 9392:9392 --name openvas immauss/openvas:22.4.51
```

### Step 4: Access Web Application
- Open browser and go to: `http://192.168.1.38`
- The web interface will be served by nginx

## 🔧 Manual Deployment

If you prefer manual setup:

### 1. Install Dependencies
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx nmap git
```

### 2. Set Up Python Environment
```bash
cd /home/$USER/scan-app
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn python-gvm python-nmap
```

### 3. Configure Nginx
```bash
sudo tee /etc/nginx/sites-available/scan-app > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        root /home/$USER/scan-app;
        index index.html;
        try_files \$uri \$uri/ =404;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/scan-app /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Create Systemd Service
```bash
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

sudo systemctl daemon-reload
sudo systemctl enable scan-backend
sudo systemctl start scan-backend
```

## 🔍 Verification

### Check Services
```bash
# Check backend service
sudo systemctl status scan-backend

# Check nginx service
sudo systemctl status nginx

# Check OpenVAS container
docker ps | grep openvas
```

### Test Connectivity
```bash
# Test backend API
curl http://localhost:8000/

# Test nginx proxy
curl http://localhost/api/

# Test OpenVAS connection
curl http://localhost/api/test-connection
```

### View Logs
```bash
# Backend logs
sudo journalctl -u scan-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log

# OpenVAS logs
docker logs openvas
```

## 🐞 Troubleshooting

### Common Issues

1. **"Permission denied" on setup script**
   ```bash
   chmod +x setup-ubuntu-vm.sh
   ./setup-ubuntu-vm.sh  # Run as regular user, not root
   ```

2. **"sudo: command not found"**
   ```bash
   # Make sure you're running as regular user with sudo privileges
   whoami  # Should show your username, not root
   sudo whoami  # Should work without password or prompt for password
   ```

3. **Backend import errors (most common)**
   ```bash
   # Run the fix script
   chmod +x fix-backend.sh
   ./fix-backend.sh
   
   # Or manually fix:
   sudo systemctl stop scan-backend
   cd /home/$USER/scan-app
   source venv/bin/activate
   pip install fastapi uvicorn python-gvm python-nmap pydantic
   sudo systemctl restart scan-backend
   ```

4. **"Port already in use"**
   ```bash
   sudo netstat -tulpn | grep :8000
   sudo pkill -f uvicorn
   ```

5. **"Nginx configuration error"**
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **"Backend not starting"**
   ```bash
   sudo journalctl -u scan-backend -f
   cd /home/$USER/scan-app && source venv/bin/activate && python backend.py
   ```

7. **"Nginx can't access files"**
   ```bash
   # Fix permissions
   sudo chmod 755 /home/$USER/
   sudo chmod 755 /home/$USER/scan-app/
   sudo chown -R www-data:www-data /home/$USER/scan-app/
   ```

### Quick Fix for Backend Issues

If you see import errors in the backend logs, run this quick fix:

```bash
# On Ubuntu VM
cd /home/ubuntu/scan-app

# Make the fix script executable
chmod +x fix-backend.sh

# Run the fix script
./fix-backend.sh
```

This script will:
- Stop the backend service
- Install/update all required Python packages
- Test all imports
- Restart the service
- Verify it's working

### Network Configuration

Make sure your Ubuntu VM has:
- **VPN connection** to the target network
- **Port forwarding** for HTTP (port 80) if accessing from outside
- **Firewall rules** allowing HTTP traffic

## 🔒 Security Considerations

1. **Change default passwords** in production
2. **Use HTTPS** for production deployments
3. **Restrict access** to the web interface
4. **Regular updates** of system packages

## 📊 Monitoring

### System Resources
```bash
# Check CPU and memory usage
htop

# Check disk space
df -h

# Check network connections
netstat -tulpn
```

### Application Health
```bash
# Check all services
sudo systemctl status scan-backend nginx docker

# Test web interface
curl -I http://localhost/
```

---

**🎉 Your vulnerability scanner is now deployed and ready to scan networks!** 