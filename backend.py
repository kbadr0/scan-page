from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gvm.connections import TLSConnection
from gvm.protocols.gmp import Gmp
import time
import uuid
import xml.etree.ElementTree as ET

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
    target: str  # Just the IP address

# OpenVAS connection settings
OPENVAS_HOST = '192.168.1.36'  # Ubuntu VM IP
OPENVAS_PORT = 9390
OPENVAS_USER = 'admin'
OPENVAS_PASS = 'admin'

# Default port list UUID for "All IANA assigned TCP"
DEFAULT_PORT_LIST_ID = '33d0cd82-57c6-11e1-8ed1-406186ea4fc5'

# Default scan config UUID for "Full and fast"
DEFAULT_SCAN_CONFIG_ID = 'daba56c8-73ec-11df-a475-002264764cea'

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

def extract_id_from_response(response):
    """Extract ID from GMP response (handles both string and XML)"""
    if isinstance(response, str):
        # Parse XML string
        try:
            root = ET.fromstring(response)
            # Look for id attribute in the root element
            return root.get('id')
        except ET.ParseError:
            # If it's not XML, try to extract ID from string
            if 'id=' in response:
                import re
                match = re.search(r'id="([^"]+)"', response)
                if match:
                    return match.group(1)
    elif hasattr(response, 'get'):
        # It's already a parsed object
        return response.get('id')
    
    return None

def get_default_scanner_id(gmp):
    """Get the default scanner ID from OpenVAS"""
    scanners = gmp.get_scanners()
    print(f"[DEBUG] gmp.get_scanners() returned: {scanners} (type: {type(scanners)})")
    # If scanners is an int, return None and print debug
    if isinstance(scanners, int):
        print(f"[DEBUG] get_scanners() returned int: {scanners}")
        return None
    # If scanners is a string, parse as XML
    if isinstance(scanners, str):
        try:
            scanners_root = ET.fromstring(scanners)
        except Exception as e:
            print(f"[DEBUG] Failed to parse scanners XML: {e}")
            return None
        for scanner in scanners_root.findall("scanner"):
            name_elem = scanner.find('name')
            name = name_elem.text if name_elem is not None else ''
            if name and name.lower().startswith('openvas'):
                return scanner.get('id')
        # Fallback: just use the first scanner
        first_scanner = scanners_root.find('scanner')
        if first_scanner is not None:
            return first_scanner.get('id')
        return None
    # If scanners is already an iterable of elements
    for scanner in scanners:
        if hasattr(scanner, 'get') and scanner.get('name', '').lower().startswith('openvas'):
            return scanner.get('id')
        # If using ElementTree XML
        if hasattr(scanner, 'find') and scanner.find('name') is not None:
            name = scanner.find('name').text
            if name and name.lower().startswith('openvas'):
                return scanner.get('id')
    # Fallback: just use the first scanner
    if scanners:
        if hasattr(scanners[0], 'get'):
            return scanners[0].get('id')
        if hasattr(scanners[0], 'find'):
            return scanners[0].get('id')
    return None

def find_existing_target_id(gmp, target_ip):
    print(f"[DEBUG] find_existing_target_id called with target_ip: {target_ip}")
    targets = gmp.get_targets()
    print(f"[DEBUG] gmp.get_targets() returned: {targets} (type: {type(targets)})")
    # If targets is a string, parse it as XML
    if isinstance(targets, str):
        try:
            targets = ET.fromstring(targets)
        except Exception as e:
            print(f"[DEBUG] Failed to parse targets XML: {e}")
            return None
        # Now targets is the root element, so iterate over its 'target' children
        for t in targets.findall("target"):
            print(f"[DEBUG] Checking target: {t} (type: {type(t)})")
            hosts_elem = t.find('hosts')
            print(f"[DEBUG] hosts_elem: {hosts_elem}")
            if hosts_elem is not None and hosts_elem.text:
                hosts = [h.strip() for h in hosts_elem.text.split(',')]
                print(f"[DEBUG] hosts: {hosts}")
                if target_ip in hosts:
                    print(f"[DEBUG] Found existing target with id: {t.get('id')}")
                    return t.get('id')
        print(f"[DEBUG] No existing target found for {target_ip}")
        return None
    # If targets is already an iterable of elements
    for t in targets:
        print(f"[DEBUG] Checking target: {t} (type: {type(t)})")
        # ElementTree XML
        if hasattr(t, 'find'):
            hosts_elem = t.find('hosts')
            print(f"[DEBUG] hosts_elem: {hosts_elem}")
            if hosts_elem is not None and hosts_elem.text:
                hosts = [h.strip() for h in hosts_elem.text.split(',')]
                print(f"[DEBUG] hosts: {hosts}")
                if target_ip in hosts:
                    print(f"[DEBUG] Found existing target with id: {t.get('id')}")
                    return t.get('id')
        # Dict-like
        elif hasattr(t, 'get'):
            hosts = t.get('hosts')
            print(f"[DEBUG] hosts: {hosts}")
            if hosts and target_ip in hosts:
                print(f"[DEBUG] Found existing target with id: {t.get('id')}")
                return t.get('id')
    print(f"[DEBUG] No existing target found for {target_ip}")
    return None

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
    print(f"[DEBUG] /scan called with target: {request.target}")
    try:
        connection = get_gmp_connection()
        print(f"[DEBUG] Got GMP connection: {connection}")
        
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            print(f"[DEBUG] Authenticated with GVM")
            
            # Create a unique name for this scan
            scan_name = f"scan_{request.target}_{int(time.time())}"
            print(f"[DEBUG] scan_name: {scan_name}")
            
            # Check if target already exists
            target_id = find_existing_target_id(gmp, request.target)
            print(f"[DEBUG] Existing target_id for {request.target}: {target_id}")
            if not target_id:
                # Create target (like task wizard)
                try:
                    target_response = gmp.create_target(
                        name=f"target_{request.target}",
                        hosts=[request.target],
                        port_list_id=DEFAULT_PORT_LIST_ID,
                        comment=f"Auto-created target for {request.target}"
                    )
                    print(f"[DEBUG] create_target response: {target_response}")
                    target_id = extract_id_from_response(target_response)
                    print(f"[DEBUG] New target_id: {target_id}")
                    
                    if not target_id:
                        return {
                            "target": request.target,
                            "status": "error",
                            "message": f"Failed to create target: {target_response}"
                        }
                except Exception as e:
                    print(f"[DEBUG] Exception during create_target: {e}")
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": f"Failed to create target: {str(e)}"
                    }
            
            # Get default scanner ID
            try:
                scanner_id = get_default_scanner_id(gmp)
                print(f"[DEBUG] scanner_id: {scanner_id}")
                if not scanner_id:
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": "Failed to find a valid scanner ID."
                    }
            except Exception as e:
                print(f"[DEBUG] Exception during get_default_scanner_id: {e}")
                return {
                    "target": request.target,
                    "status": "error",
                    "message": f"Failed to get scanner ID: {str(e)}"
                }
            
            # Use default "Full and fast" scan config (most common)
            config_id = DEFAULT_SCAN_CONFIG_ID
            print(f"[DEBUG] config_id: {config_id}")
            
            # Create task (like task wizard)
            try:
                task_response = gmp.create_task(
                    name=scan_name,
                    config_id=config_id,
                    target_id=target_id,
                    scanner_id=scanner_id,
                    comment=f"Auto-created scan for {request.target}"
                )
                print(f"[DEBUG] create_task response: {task_response}")
                task_id = extract_id_from_response(task_response)
                print(f"[DEBUG] New task_id: {task_id}")
                
                if not task_id:
                    return {
                        "target": request.target,
                        "status": "error",
                        "message": f"Failed to create task: {task_response}"
                    }
            except Exception as e:
                print(f"[DEBUG] Exception during create_task: {e}")
                return {
                    "target": request.target,
                    "status": "error",
                    "message": f"Failed to create task: {str(e)}"
                }
            
            # Start the task
            try:
                print(f"[DEBUG] Starting task with task_id: {task_id}")
                gmp.start_task(task_id)
                print(f"[DEBUG] Task started successfully.")
            except Exception as e:
                print(f"[DEBUG] Exception during start_task: {e}")
                return {
                    "target": request.target,
                    "status": "error",
                    "message": f"Failed to start task: {str(e)}"
                }
            
            return {
                "target": request.target,
                "task_id": task_id,
                "status": "started",
                "message": f"Scan started successfully for {request.target}. Task ID: {task_id}"
            }
            
    except Exception as e:
        print(f"[DEBUG] Exception in /scan: {e}")
        return {
            "target": request.target,
            "status": "error",
            "message": f"Failed to start scan: {str(e)}"
        }

@app.post("/stop-scan/{task_id}")
def stop_scan(task_id: str, request: Request):
    """Stop a running scan/task by task_id."""
    try:
        connection = get_gmp_connection()
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            # Attempt to stop the task
            try:
                gmp.stop_task(task_id)
                return {"status": "success", "message": f"Scan/task {task_id} stopped."}
            except Exception as e:
                return {"status": "error", "message": f"Failed to stop scan/task: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to OpenVAS: {str(e)}"}

@app.get("/scan-status/{task_id}")
def get_scan_status(task_id: str):
    """Get the status of a running scan"""
    try:
        connection = get_gmp_connection()
        
        with Gmp(connection) as gmp:
            authenticate_gmp(gmp)
            
            task = gmp.get_task(task_id)
            # Debug print
            print(f"[DEBUG] get_task({task_id}) returned: {task} (type: {type(task)})")
            # Robust type checking
            status = 'unknown'
            if hasattr(task, 'find'):
                status_elem = task.find('status')
                if status_elem is not None and hasattr(status_elem, 'text'):
                    status = status_elem.text
            elif isinstance(task, dict):
                status = task.get('status', 'unknown')
            elif isinstance(task, int):
                return {"task_id": task_id, "status": "error", "message": f"Task not found or invalid response (int): {task}"}
            else:
                return {"task_id": task_id, "status": "error", "message": f"Unexpected task response: {type(task)}: {task}"}
            
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
            # Debug print
            print(f"[DEBUG] get_task({task_id}) returned: {task} (type: {type(task)})")
            # Robust type checking
            status = 'unknown'
            if hasattr(task, 'find'):
                status_elem = task.find('status')
                if status_elem is not None and hasattr(status_elem, 'text'):
                    status = status_elem.text
            elif isinstance(task, dict):
                status = task.get('status', 'unknown')
            elif isinstance(task, int):
                return {"task_id": task_id, "status": "error", "message": f"Task not found or invalid response (int): {task}"}
            else:
                return {"task_id": task_id, "status": "error", "message": f"Unexpected task response: {type(task)}: {task}"}
            
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
                vulns = report.findall('.//nvt') if hasattr(report, 'findall') else []
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