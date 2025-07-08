from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Allow your HTML frontend to call the API (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

class ScanRequest(BaseModel):
    target: str
    scan_type: str

@app.post("/scan")
async def scan(request: ScanRequest):
    # For now, just return mock data
    return {
        "target": request.target,
        "scan_type": request.scan_type,
        "result": [
            {"cve": "CVE-2023-1234", "desc": "Example Vulnerability"},
            {"cve": "CVE-2022-5678", "desc": "Another Example"}
        ]
    } 