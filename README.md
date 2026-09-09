# lazy-jobber

Automated job search and application tool using Chrome Remote Debugging (CDP) and candidate profile matching.

---

## Overview

Most job application bots fail because logins, Cloudflare verification, and OTPs block automated scripts. 

lazy-jobber avoids this by attaching directly to an existing, authenticated Google Chrome session via Chrome DevTools Protocol (port 9222). You log in manually, and the tool automates scanning, relevance scoring, and submitting batch applications.

---

## How It Works

1. Launch Chrome in remote debugging mode using the provided script.
2. Sign in to your account manually in the opened Chrome window.
3. Open the lazy-jobber dashboard at http://localhost:5000.
4. Scan job postings on your active tab and view real-time match scores based on your profile skills.
5. Trigger automated applications (including batch selection and handling common recruiter questionnaires like relocation and experience).
6. View real-time logs saved to your local machine.

---

## Quick Start

### 1. Set Up Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start Chrome with Debugging

Run the launcher batch file:

```powershell
.\launch_chrome.bat
```

Log in to your job portal (such as Naukri) in this Chrome window.

### 3. Start the Web Dashboard

```powershell
python server.py
```

Open your browser at:
```
http://localhost:5000
```

From the dashboard, verify the connection on port 9222, scan jobs on the active tab, and run auto-apply.

---

## Process Management

If a previous background server instance is holding port 5000:
- Click the "Restart Server" button on the dashboard navbar, or
- Run the cleanup script:
  ```powershell
  .\restart_server.bat
  ```

---

## Project Structure

```
lazy-jobber/
├── launch_chrome.bat       # Starts Chrome with remote debugging on port 9222
├── restart_server.bat      # Terminates lingering processes and restarts server
├── server.py               # Local HTTP server and API router
├── main.py                 # CLI entry point
├── config.json             # Search criteria, limits, and thresholds
├── profile.json            # Candidate skills, experience, and target roles
├── ui/                     # Web dashboard
│   ├── index.html          # Dashboard interface
│   ├── app.css             # Interface styling
│   └── app.js              # Client-side state and execution handlers
└── src/
    ├── platforms/
    │   └── naukri_cdp.py   # Chrome DevTools automation for Naukri
    ├── parser.py           # Profile reader
    ├── matcher.py          # Skill scoring and relevance calculator
    ├── tracker.py          # Application tracker and deduplicator
    └── applier.py          # Application batch controller
```

---

## Privacy and Security

- No credentials stored: Passwords and session tokens are never saved or accessed by scripts.
- Local execution: All profile matching and application records remain strictly on your local device.
- Configurable limits: Match score thresholds and application caps prevent unintended submissions.
