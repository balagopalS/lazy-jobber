import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import threading
import time
from typing import Dict, Any

from src.logger import setup_logger, get_logger, get_recent_logs
from src.process_manager import ProcessManager, ensure_chrome_running
from src.parser import ProfileManager
from src.matcher import JobMatcher
from src.platforms.naukri_cdp import NaukriCDPAutomator
from src.agent import JobberAgent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logger = setup_logger()
PORT = 5000
agent_instance = JobberAgent()

class JobberHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Serve UI Index
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

        # API: Logs Stream / Recent logs
        elif path == "/api/logs":
            limit = int(query.get("limit", [100])[0])
            self.send_json_response({"success": True, "logs": get_recent_logs(limit)})
            return

        # API: Agent Status
        elif path == "/api/agent/status":
            self.send_json_response(agent_instance.get_status())
            return

        # API: Start Agent Loop
        elif path == "/api/agent/start":
            res = agent_instance.start()
            self.send_json_response(res)
            return

        # API: Stop Agent Loop
        elif path == "/api/agent/stop":
            res = agent_instance.stop()
            self.send_json_response(res)
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

        # API: Execute 1-click batch application
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
                        job,
                        status="APPLIED",
                        notes="Manual Batch Apply via Web Dashboard"
                    )

            self.send_json_response(res)
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len) if content_len > 0 else b"{}"

        try:
            body = json.loads(post_body.decode("utf-8"))
        except Exception:
            body = {}

        # API: Update AI Config
        if path == "/api/config/ai":
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    config = json.load(f)

                config["ai_config"] = body
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2)

                logger.info(f"Updated AI Config: provider={body.get('provider')}")
                self.send_json_response({"success": True, "message": "AI config updated successfully."})
            except Exception as e:
                self.send_json_response({"success": False, "error": str(e)}, status=500)
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
    # 1. Auto-launch Chrome CDP if not alive
    logger.info("Initializing Lazy-Jobber environment...")
    ensure_chrome_running(cdp_port=9222)

    # 2. Bind TCP server socket cleanly
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), JobberHTTPHandler) as httpd:
        logger.info("=" * 65)
        logger.info(f"🚀 Lazy-Jobber Web Dashboard running at: http://localhost:{PORT}")
        logger.info("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("\nShutting down server cleanly...")
            agent_instance.stop()
            ProcessManager().cleanup()

if __name__ == "__main__":
    start_server()
