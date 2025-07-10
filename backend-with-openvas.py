from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
import time
import uuid

app = FastAPI()

# Allow your HTML frontend to call the API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    target: str
    scan_type: str

# OpenVAS connection settings
OPENVAS_HOST = 'localhost'
OPENVAS_PORT = 9390
OPENVAS_USER = 'admin'
OPENVAS_PASS = 'admin'

def get_gmp_connection():
    """Create and return a GMP connection"""
    try:
        connection = TLSConnection(hostname=OPENVAS_HOST, port=OPENVAS_PORT)
        return connection
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to OpenVAS: {str(e)}")

def authenticate_gmp(gmp):
    """Authenticate with OpenVAS"""
    try:
        gmp.authenticate(OPENVAS_USER, OPENVAS_PASS)
        return True
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

@app.get("/test-connection")
def test_openvas_connection():
    """Test the connection to OpenVAS"""
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            version = gmp.get_version()
            return {"status": "success", "version": str(version)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/scan")
async def scan(request: ScanRequest):
    """Start a real scan using OpenVAS"""
    try:
        connection = get_gmp_connection()
        
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            
            # Create a unique name for this scan
            scan_name = f"scan_{request.target}_{int(time.time())}"
            
            # Create target
            target_response = gmp.create_target(
                name=f"target_{request.target}",
                hosts=[request.target],
                comment=f"Target for {request.target}"
            )
            target_id = target_response.get('id')
            
            # Get scan config based on scan type
            scan_configs = gmp.get_scan_configs()
            config_id = None
            
            # Map scan types to OpenVAS configs
            scan_type_mapping = {
                'full': 'daba56c8-73ec-11df-a475-002264764cea',  # Full and fast
                'fast': 'daba56c8-73ec-11df-a475-002264764cea',  # Full and fast
                'discovery': '698f691e-7489-11df-9d8c-002264764cea'  # Discovery
            }
            
            config_id = scan_type_mapping.get(request.scan_type, 'daba56c8-73ec-11df-a475-002264764cea')
            
            # Create task
            task_response = gmp.create_task(
                name=scan_name,
                config_id=config_id,
                target_id=target_id,
                comment=f"Scan of {request.target}"
            )
            task_id = task_response.get('id')
            
            # Start the task
            gmp.start_task(task_id)
            
            return {
                "target": request.target,
                "scan_type": request.scan_type,
                "task_id": task_id,
                "status": "started",
                "message": f"Scan started successfully. Task ID: {task_id}"
            }
            
    except Exception as e:
        return {
            "target": request.target,
            "scan_type": request.scan_type,
            "status": "error",
            "message": f"Failed to start scan: {str(e)}"
        }

@app.get("/scan-status/{task_id}")
def get_scan_status(task_id: str):
    """Get the status of a running scan"""
    try:
        connection = get_gmp_connection()
        
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            
            task = gmp.get_task(task_id)
            status = task.find('status').text if task.find('status') is not None else 'unknown'
            
            return {
                "task_id": task_id,
                "status": status
            }
            
    except Exception as e:
        return {"task_id": task_id, "status": "error", "message": str(e)}

@app.get("/scan-results/{task_id}")
def get_scan_results(task_id: str):
    """Get the results of a completed scan"""
    try:
        connection = get_gmp_connection()
        
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            
            # Get the task to check if it's completed
            task = gmp.get_task(task_id)
            status = task.find('status').text if task.find('status') is not None else 'unknown'
            
            if status != 'Done':
                return {
                    "task_id": task_id,
                    "status": status,
                    "message": "Scan is not completed yet"
                }
            
            # Get the report
            reports = gmp.get_reports(task_id=task_id)
            
            if not reports:
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "message": "No vulnerabilities found",
                    "vulnerabilities": []
                }
            
            # Parse the latest report for vulnerabilities
            vulnerabilities = []
            for report in reports:
                # This is a simplified version - you might want to parse the XML more thoroughly
                vulns = report.findall('.//nvt')
                for vuln in vulns:
                    name = vuln.find('name')
                    if name is not None:
                        vulnerabilities.append({
                            "name": name.text,
                            "severity": "medium"  # You can extract this from the report
                        })
            
            return {
                "task_id": task_id,
                "status": "completed",
                "vulnerabilities": vulnerabilities
            }
            
    except Exception as e:
        return {"task_id": task_id, "status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 