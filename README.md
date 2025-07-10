# Vulnerability Scanning Platform (OpenVAS/GVM) — Complete Solution

A complete web-based vulnerability scanning platform that integrates with OpenVAS/GVM (Greenbone Vulnerability Management) running in Docker. This project provides a simple, task wizard-like interface for running vulnerability scans.

## 🎯 Project Overview

This platform consists of:
- **Frontend**: Clean HTML/CSS/JS interface (no frameworks required)
- **Backend**: FastAPI server that communicates with OpenVAS via GMP API
- **Scanner**: OpenVAS/GVM running in Docker container
- **Workflow**: Enter IP → Auto-create target → Auto-create task → Run scan → Get results

## 🏗️ Architecture

```
┌─────────────────┐    HTTP     ┌─────────────────┐    GMP API    ┌─────────────────┐
│   HTML Frontend │ ──────────→ │  FastAPI Backend│ ──────────→   │  OpenVAS Docker │
│   (index.html)  │             │   (backend.py)  │               │   (port 9390)   │
└─────────────────┘             └─────────────────┘               └─────────────────┘
```

## 🚀 Features

- ✅ **Simple Interface**: Just enter an IP address and click "Start Scan"
- ✅ **Real OpenVAS Integration**: Uses actual OpenVAS scans, not mock data
- ✅ **Automatic Target/Task Creation**: Like OpenVAS task wizard
- ✅ **Real-time Progress Monitoring**: Watch scan status updates
- ✅ **Complete Results**: Get actual vulnerability findings
- ✅ **Docker-based**: Easy deployment with OpenVAS container

## 📋 Prerequisites

- Ubuntu/Debian system
- Docker installed
- Python 3.8+
- Git

## 🛠️ Installation & Setup

### Option 1: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd <project-folder>

# Make setup script executable and run it
chmod +x setup-ubuntu.sh
./setup-ubuntu.sh
```

### Option 2: Manual Setup
Follow the steps in `me-to-do.txt` for detailed manual installation.

## 🎮 How to Use

### 1. Start the Backend
```bash
# Activate virtual environment
source venv/bin/activate

# Start the FastAPI server
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test the Connection
- Open your browser and go to: `http://localhost:8000/test-connection`
- You should see the OpenVAS version if connection is successful

### 3. Run a Scan
- Open `index.html` in your browser
- Enter an IP address (e.g., `192.168.1.1`)
- Click "Start Scan"
- Watch the real-time progress and results!

## 📁 Project Structure

```
├── index.html                    # Main frontend interface
├── style.css                     # Frontend styling
├── script-with-real-scans.js     # Frontend logic (real scans)
├── backend.py                    # FastAPI backend (mock data)
├── backend-with-openvas.py       # FastAPI backend (real OpenVAS)
├── setup-ubuntu.sh              # Automated Ubuntu setup script
├── me-to-do.txt                 # Detailed setup checklist
├── backend-setup-instructions.txt # Backend setup guide
└── README.md                    # This file
```

## 🔧 Configuration

### OpenVAS Connection Settings
In `backend-with-openvas.py`:
```python
OPENVAS_HOST = 'localhost'    # OpenVAS Docker container
OPENVAS_PORT = 9390          # GMP API port
OPENVAS_USER = 'admin'       # Default username
OPENVAS_PASS = 'admin'       # Default password
```

### Scan Configuration
- **Default Scan Type**: "Full and fast" (most comprehensive)
- **Auto Target Creation**: Creates target for each IP
- **Auto Task Creation**: Creates task with default settings

## 🔍 API Endpoints

- `GET /` - Backend status
- `GET /test-connection` - Test OpenVAS connectivity
- `POST /scan` - Start a new scan (requires `target` IP)
- `GET /scan-status/{task_id}` - Check scan progress
- `GET /scan-results/{task_id}` - Get completed scan results

## 🐛 Troubleshooting

### Common Issues

1. **"Failed to connect to OpenVAS"**
   - Check if Docker container is running: `docker ps`
   - Verify port 9390 is exposed: `nc -vz localhost 9390`

2. **"Authentication failed"**
   - Default credentials are `admin/admin`
   - Check OpenVAS container logs: `docker logs openvas`

3. **"Scan timeout"**
   - Scans can take 5-30 minutes depending on target
   - Check scan status via OpenVAS web interface: `http://localhost:9392`

### Debug Commands
```bash
# Check OpenVAS container status
docker ps | grep openvas

# View OpenVAS logs
docker logs openvas

# Test GMP connection manually
python test_gvm_connection.py

# Check backend logs
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

## 🔒 Security Notes

- This is designed for **lab/development environments**
- Default OpenVAS credentials are used (`admin/admin`)
- For production, change passwords and restrict access
- Consider using HTTPS for frontend-backend communication

## 🚀 Next Steps

- [ ] Add scan scheduling capabilities
- [ ] Implement scan result export (PDF, CSV)
- [ ] Add user authentication
- [ ] Create scan templates for different use cases
- [ ] Add email notifications for completed scans

## 📄 License

MIT License - Feel free to use and modify for your needs.

---

**🎉 You now have a complete, working vulnerability scanner that integrates with real OpenVAS scans!** 