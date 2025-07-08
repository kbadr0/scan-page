# Vulnerability Scanning Platform (OpenVAS/GVM) — HTML/CSS/JS Version

A simple web-based interface for running vulnerability scans using OpenVAS/GVM, designed for use in a cybersecurity lab network (MARWAN).

## Project Architecture

- **Frontend:** Plain HTML, CSS, and JavaScript (no frameworks)
- **Backend:** (To be implemented separately, e.g., Python Flask/FastAPI)
- **Scanner:** OpenVAS/GVM (via python-gvm or gvm-tools)

## Workflow

1. User enters a target (IP/domain) and scan type on the web UI.
2. The frontend would send a request to the backend API (currently simulated with mock data).
3. The backend starts a scan with OpenVAS, monitors it, and returns results.
4. Results are displayed in the frontend.

## How to Run (Frontend Only)

1. Open `index.html` in your web browser (double-click or right-click > Open with...)
2. No installation or server required for the frontend.

## Next Steps
- Implement the backend API (Flask/FastAPI) to connect to OpenVAS/GVM
- Integrate the frontend with the backend API

---

## License
MIT 