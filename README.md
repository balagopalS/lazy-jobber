# 🤖 lazy-jobber

**lazy-jobber** is an intelligent automated job application suite designed for senior backend engineers. It consumes your resume, learns your core technical profile, searches target job portals (Naukri, Indeed, LinkedIn), scores job suitability, and auto-applies up to your set application limit (e.g., 40 jobs).

---

## ✨ Features

- 📄 **Resume Consumer & Profile Learning**: Automatically parses PDF resume details (`Resume (4).pdf`) into structured candidate metrics.
- 🎯 **Task Application Limits**: Configurable batch application cap (e.g., 40 jobs per session).
- 🔍 **Multi-Platform Searcher**: Searches top Indian & Global portals—**Naukri**, **Indeed**, **LinkedIn**.
- 📊 **Smart Match Scoring Engine**: Matches job requirements against candidate skills (Java 8/17/23, Spring Boot, Microservices, Kafka, SQL, AWS, Navitaire/OTA integration).
- 🚀 **Auto-Applier Engine**: Automated form filler and application submitter with rate limiting and safety controls.
- 📑 **Audit Logging & Reporting**: Tracks applications in real-time to [`applied_jobs.json`](file:///C:/Users/balag/Desktop/Coding/lazy-jobber/applied_jobs.json) and [`applied_jobs.csv`](file:///C:/Users/balag/Desktop/Coding/lazy-jobber/applied_jobs.csv).

---

## 🛠️ Project Structure

```
lazy-jobber/
├── main.py              # CLI Application Entry Point
├── profile.json         # Extracted Candidate Profile Data
├── config.json          # Application Task Settings (Limit: 40)
├── applied_jobs.json    # JSON Application Log & History
├── applied_jobs.csv     # CSV Export of Applied Jobs
├── Resume (4).pdf       # User Resume
├── src/
│   ├── parser.py        # Profile Manager & Resume Reader
│   ├── matcher.py       # Relevance & Match Score Calculator
│   ├── searcher.py      # Job Aggregator & Portal Searcher
│   ├── tracker.py       # Application Tracker & Deduplicator
│   └── applier.py       # Batch Application Runner
├── requirements.txt     # Python Dependencies
└── README.md            # Documentation
```

---

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Lazy-Jobber
```bash
python main.py
```

---

## 🔒 Privacy & Security

Your resume details and job search logs stay 100% local on your device. Credentials should be placed in `.env` (derived from `.env.example`) and never committed to public repositories.
