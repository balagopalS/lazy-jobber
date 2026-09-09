import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import threading
import subprocess
import time
from typing import Dict, Any

from src.parser import ProfileManager
from src.matcher import JobMatcher
from src.platforms.naukri_cdp import NaukriCDPAutomator

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PORT = 5000

class JobberHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Serve UI
        if path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open("ui/index.html", "rb") as f:
                self.wfile.write(f.read())
            return

        elif path.startswith("/ui/"):
            return super().do_GET()

        # API: Profile & Config
        elif path == "/api/profile":
            self.send_json_response(self.get_profile_data())
            return

        # API: Check CDP connection to Chrome port 9222
        elif path == "/api/cdp/status":
            automator = NaukriCDPAutomator()
            res = automator.connect()
            connected = res.get("success", False)
            automator.close()
            self.send_json_response({
                "connected": connected,
                "url": res.get("url", ""),
                "title": res.get("title", ""),
                "open_tabs": res.get("open_tabs", 0)
            })
            return

        # API: Scan jobs on current page & score them
        elif path == "/api/cdp/scan":
            min_score = float(query.get("min_score", [65])[0])
            automator = NaukriCDPAutomator()
            conn = automator.connect()
            if not conn.get("success"):
                automator.close()
                self.send_json_response({"success": False, "error": conn.get("error", "Failed to connect to Chrome")})
                return

            profile = ProfileManager("profile.json")
            matcher = JobMatcher(profile)
            jobs = automator.scan_jobs_on_page()
            automator.close()

            scored_jobs = []
            for job in jobs:
                matcher.calculate_match_score(job)
                scored_jobs.append(job)

            # Sort by match score descending
            scored_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            self.send_json_response({"success": True, "count": len(scored_jobs), "jobs": scored_jobs})
            return

        # API: Execute 1-click batch application for up to 5 jobs
        elif path == "/api/cdp/apply_batch":
            min_score = float(query.get("min_score", [65])[0])
            automator = NaukriCDPAutomator()
            conn = automator.connect()
            if not conn.get("success"):
                automator.close()
                self.send_json_response({"success": False, "error": conn.get("error", "Chrome not connected")})
                return

            res = automator.batch_apply_recommended_jobs(min_match_score=min_score, max_limit=5)
            automator.close()

            # Record to tracker if applied
            if res.get("success") and res.get("applied_count", 0) > 0:
                from src.tracker import ApplicationTracker
                tracker = ApplicationTracker()
                for job in res.get("jobs", []):
                    tracker.record_application(
                        job_id=job.get("job_id", ""),
                        title=job.get("title", ""),
                        company=job.get("company", ""),
                        platform="Naukri",
                        location="Bengaluru",
                        match_score=job.get("match_score", 0),
                        status="APPLIED"
                    )

            self.send_json_response(res)
            return

        # API: Kill zombie python/browser tasks and reload server
        elif path == "/api/system/restart":
            self.send_json_response({"success": True, "message": "Restarting server cleanly in 1s..."})
            def do_restart():
                time.sleep(1)
                curr_pid = os.getpid()
                # Run cleanup powershell command to restart python server.py
                subprocess.Popen(
                    f'powershell -Command "Start-Sleep -Seconds 1; Start-Process -FilePath \'{sys.executable}\' -ArgumentList \'server.py\'"',
                    shell=True
                )
                os._exit(0)

            threading.Thread(target=do_restart, daemon=True).start()
            return

        self.send_error(404, "Endpoint not found")

    def get_profile_data(self) -> Dict[str, Any]:
        try:
            profile = ProfileManager("profile.json")
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            return {
                "personal_info": profile.get_personal_info(),
                "skills": profile.get_all_skills(),
                "target_roles": profile.get_target_roles(),
                "config": config
            }
        except Exception as e:
            return {"error": str(e)}

    def send_json_response(self, data: Any, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), JobberHTTPHandler) as httpd:
        print("=" * 60)
        print(f"🚀 Lazy-Jobber Web Dashboard running at: http://localhost:{PORT}")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    start_server()
