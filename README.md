# lazy-jobber

Automated job search and application suite using Chrome Remote Debugging (CDP), candidate profile matching, and AI-assisted screening response generation.

---

## Overview

Traditional job application bots often fail due to login requirements, bot detection, or two-factor authentication.

`lazy-jobber` attaches directly to an active Google Chrome session using the Chrome DevTools Protocol (CDP) on port 9222. When you start the application server, it automatically launches Chrome if it is not already running. Once you log in to your target job portal, the system can continuously scan job postings, evaluate candidate skill match scores, and handle application questionnaires using local or cloud AI models.

---

## Key Features

- **Automated Chrome Lifecycle**: Automatically detects or launches Chrome with remote debugging enabled on port 9222.
- **Autonomous Agent Mode**: Runs a background monitoring loop to scan active job pages, scroll listings, and submit batch applications automatically.
- **AI Screening Solver**: Integrates with local models (Ollama) or cloud APIs (OpenRouter) to answer recruiter screening questions using candidate profile context.
- **Process Management**: Automatically manages sub-process handles and releases ports cleanly on application exit or restart.
- **Real-Time Logging**: Displays HTTP server and CDP browser events in a live terminal stream on the web dashboard.
- **Application Tracking**: Saves application history and match metadata to local `applied_jobs.json` and `applied_jobs.csv` files.

---

## Quick Start

### 1. Set Up Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Start Application Server

```powershell
python server.py
```

`server.py` will verify port 9222 and launch Google Chrome automatically if it is not currently running.

### 3. Open Web Dashboard

Navigate to:
```
http://localhost:5000
```

From the dashboard you can:
- Configure AI inference providers (Ollama or OpenRouter).
- Start or stop the Autonomous Agent loop.
- Manually scan and apply to active job postings.
- Monitor live terminal and CDP logs.

---

## AI Provider Setup

### Local LLM (Ollama)
Set the provider to `ollama` in the dashboard or `config.json`. Ensure Ollama is running locally on `http://localhost:11434`.

### Cloud API (OpenRouter)
Set the provider to `openrouter` in the dashboard or `config.json`, and supply your API key and model identifier (such as `meta-llama/llama-3.1-8b-instruct:free`).

---

## Project Structure

```
lazy-jobber/
├── server.py               # Application entry point, HTTP server, and API router
├── main.py                 # CLI entry point
├── config.json             # Search criteria, safety limits, and AI configuration
├── profile.json            # Candidate skills, work history, and target roles
├── ui/                     # Web dashboard interface (HTML/CSS/JS)
└── src/
    ├── agent.py            # Autonomous background loop controller
    ├── logger.py           # Centralized logging module with ring buffer for UI stream
    ├── process_manager.py  # Chrome process launcher and clean shutdown handler
    ├── ai/
    │   ├── provider.py     # Base abstract class for LLM providers
    │   ├── ollama_provider.py    # Local Ollama integration
    │   ├── openrouter_provider.py# Cloud OpenRouter API integration
    │   └── solver.py       # Candidate context question solver
    ├── platforms/
    │   └── naukri_cdp.py   # Chrome DevTools automation for Naukri
    ├── parser.py           # Candidate profile loader
    ├── matcher.py          # Skill scoring and relevance calculator
    ├── tracker.py          # Application tracker and record exporter
    └── applier.py          # Batch application controller
```

---

## Privacy and Security

- **Local Credentials**: Passwords and session tokens are never stored by the application.
- **Local Data Storage**: Candidate profiles and application records remain on your local machine.
- **Configurable Thresholds**: Minimum match score requirements and daily application caps prevent unintended submissions.
