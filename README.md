# MTG Card Price Checker

Serverless web app for comparing Magic: The Gathering card prices across multiple stores. Live demo: https://mtgvillage.vercel.app/

## Features
- Compare prices across supported MTG retailers with real-time availability
- Sort, filter, and export results using DataTables
- Responsive Bootstrap UI with Font Awesome icons
- Serverless Python backend that normalizes store-specific responses

## Tech Stack
- Frontend: Static HTML/CSS/JavaScript + Bootstrap, DataTables, jQuery
- Backend: Python 3.9 serverless functions (Vercel)
- Hosting: GitHub Pages (frontend) + Vercel (API)
- Dependencies: `requests` for outbound store API calls

## Quick Start (Local Testing)

### Requirements
- Python 3.9 or newer
- pip on your PATH
- PowerShell (Windows) or Bash (macOS/Linux)

### macOS/Linux
```bash
./scripts/local_test_mac.sh [port]
```
- Installs `requirements.txt`
- Runs a backend smoke test to confirm configured stores
- Serves the site at `http://127.0.0.1:[port]` (defaults to `8000`)

### Windows
```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_test_windows.ps1 -Port 8000
```
- Mirrors the macOS workflow using PowerShell
- Stops with `Ctrl+C`

### Browser Check
1. Open the URL printed by the script.
2. Enter sample card names, choose stores, and run a price check.
3. Use browser dev tools to confirm calls to `/api/stores` and `/api/check-prices` succeed.

> Tip: When testing against production APIs, ensure `API_BASE_URL` in `assets/js/app.js` points to your deployed Vercel URL. The scripts assume the backend is reachable at `http://localhost:3000`.

## Project Structure
```
mtgvillage/
├── api/                  # Python serverless endpoints
├── assets/               # Static CSS/JS assets
├── scripts/              # Shared backend logic + helper scripts
├── index.html            # Frontend entry point
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel configuration
└── README.md             # Documentation
```

## Deployment Overview
1. **Frontend**: Publish the repo on GitHub Pages (root). The static assets require no build step.
2. **Backend**: Import the repository into Vercel. Vercel auto-detects Python functions inside `/api`.
3. **Configure Frontend**: Update `API_BASE_URL` in `assets/js/app.js` with the Vercel domain.
4. **Verify**: Visit the GitHub Pages site and run sample searches.

## Troubleshooting
- **CORS errors**: Confirm the `API_BASE_URL` matches your Vercel deployment and that the API is responding.
- **Store returns `n/a`**: Indicates the external store API timed out or the card name could not be found.
- **Local script fails**: Make sure Python 3.9+ and pip are installed and accessible from the terminal.
- **Static server unavailable**: Check if another process is using the requested port; pass a different port to the script.

## License
Apache License 2.0. See `LICENSE` for the full text.

## Acknowledgments
- Bootstrap, DataTables, and Font Awesome for the UI.
- External MTG store APIs for price and availability data.
