import time
import json
import threading
from typing import Dict, Any, Optional
from src.parser import ProfileManager
from src.matcher import JobMatcher
from src.tracker import ApplicationTracker
from src.platforms.naukri_cdp import NaukriCDPAutomator
from src.ai.solver import QuestionSolver
from src.logger import get_logger

logger = get_logger("agent")

class JobberAgent:
    """Autonomous Agentic Controller that continuously monitors Chrome, scans jobs, and auto-applies."""

    def __init__(self, config_path: str = "config.json", profile_path: str = "profile.json"):
        self.config_path = config_path
        self.profile_path = profile_path
        self.state = "IDLE"  # IDLE, RUNNING, PAUSED, STOPPED
        self.current_action = "Agent Idle"
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.stats = {
            "total_scanned": 0,
            "total_applied": 0,
            "started_at": None,
            "last_active": None,
            "errors": 0
        }

    def load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "current_action": self.current_action,
            "stats": self.stats
        }

    def start(self) -> Dict[str, Any]:
        if self.state == "RUNNING":
            return {"success": False, "message": "Agent is already running."}

        self.state = "RUNNING"
        self.stop_event.clear()
        self.stats["started_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.thread = threading.Thread(target=self._run_agent_loop, daemon=True)
        self.thread.start()
        logger.info("🤖 Autonomous JobberAgent started!")
        return {"success": True, "message": "Agent started successfully."}

    def stop(self) -> Dict[str, Any]:
        if self.state != "RUNNING":
            return {"success": False, "message": "Agent is not currently running."}

        self.state = "STOPPED"
        self.current_action = "Stopping agent..."
        self.stop_event.set()
        logger.info("🛑 Autonomous JobberAgent stopping...")
        return {"success": True, "message": "Agent stopped."}

    def _run_agent_loop(self):
        config = self.load_config()
        profile = ProfileManager(self.profile_path)
        matcher = JobMatcher(profile)
        tracker = ApplicationTracker()
        solver = QuestionSolver(profile, config)

        target_limit = config.get("application_limit", 40)
        min_score = config.get("search_criteria", {}).get("matching_score_threshold", 0.65) * 100
        delay_sec = config.get("safety", {}).get("delay_between_applications_seconds", 3)

        logger.info(f"Agent Loop running. Target limit: {target_limit} jobs, Min match score: {min_score}%")

        while not self.stop_event.is_set():
            if tracker.get_applied_count() >= target_limit:
                logger.info(f"🎉 Target application limit of {target_limit} reached!")
                self.current_action = f"Target limit ({target_limit}) reached!"
                self.state = "IDLE"
                break

            try:
                self.current_action = "Connecting to Chrome CDP on port 9222..."
                automator = NaukriCDPAutomator()
                conn = automator.connect()

                if not conn.get("success"):
                    logger.warning(f"Chrome CDP connection failed: {conn.get('error')}. Retrying in 10s...")
                    self.stats["errors"] += 1
                    automator.close()
                    time.sleep(10)
                    continue

                # Auto-scroll page to load dynamically rendered cards
                self.current_action = "Scanning & auto-scrolling active page for jobs..."
                if automator.page:
                    try:
                        automator.page.evaluate("window.scrollBy(0, 500)")
                        time.sleep(1)
                    except Exception:
                        pass

                jobs = automator.scan_jobs_on_page()
                self.stats["total_scanned"] += len(jobs)
                self.stats["last_active"] = time.strftime("%Y-%m-%d %H:%M:%S")

                logger.info(f"Scanned {len(jobs)} job cards on active browser tab.")

                # Filter suitable unapplied jobs
                eligible_jobs = []
                for job in jobs:
                    if tracker.is_already_applied(job.get("job_id")):
                        continue
                    matcher.calculate_match_score(job)
                    if job.get("match_score", 0) >= min_score:
                        eligible_jobs.append(job)

                eligible_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

                if eligible_jobs:
                    self.current_action = f"Batch applying to {min(5, len(eligible_jobs))} high-match jobs..."
                    logger.info(f"Found {len(eligible_jobs)} suitable jobs (>= {min_score}%). Executing batch apply...")
                    res = automator.batch_apply_recommended_jobs(min_match_score=min_score, max_limit=5)

                    if res.get("success") and res.get("applied_count", 0) > 0:
                        for job in res.get("jobs", []):
                            tracker.record_application(
                                job,
                                status="APPLIED",
                                notes=f"Auto-applied by Autonomous Agent (Match: {job.get('match_score')}%)"
                            )
                            self.stats["total_applied"] += 1

                        logger.info(f"✅ Successfully applied to {res.get('applied_count')} jobs!")
                    else:
                        logger.info(f"Batch result: {res.get('message') or res.get('error')}")

                automator.close()

                # Safety sleep between polling iterations
                self.current_action = f"Waiting {delay_sec * 2}s before next monitoring check..."
                for _ in range(int(delay_sec * 2)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in Agent loop: {e}")
                self.stats["errors"] += 1
                self.current_action = f"Error occurred: {e}"
                time.sleep(5)

        self.state = "IDLE"
        self.current_action = "Agent Idle"
        logger.info("Autonomous Agent loop exited.")
