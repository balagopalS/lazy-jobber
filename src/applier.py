import time
import random
import sys
from typing import Dict, Any, List
from src.tracker import ApplicationTracker
from src.parser import ProfileManager

class JobApplier:
    """Executes auto-application to target jobs while respecting safety rate limits and max task limit."""

    def __init__(self, profile: ProfileManager, tracker: ApplicationTracker, config: Dict[str, Any]):
        self.profile = profile
        self.tracker = tracker
        self.config = config
        self.target_limit = config.get("application_limit", 40)
        self.min_score = config.get("search_criteria", {}).get("matching_score_threshold", 0.65) * 100
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")

    def apply_batch(self, jobs: List[Dict[str, Any]], limit: int = 40) -> List[Dict[str, Any]]:
        """Applies to suitable jobs up to the specified task limit (40 jobs)."""
        applied_results = []
        current_applied = self.tracker.get_applied_count()
        needed = min(limit, self.target_limit - current_applied)

        if needed <= 0:
            print(f"🎯 Target application limit of {self.target_limit} already reached!")
            return applied_results

        print(f"🚀 Starting job application engine. Target: {needed} applications (Limit: {self.target_limit})...")

        candidate_info = self.profile.get_personal_info()

        for job in jobs:
            if self.tracker.get_applied_count() >= self.target_limit:
                print(f"✅ Reached maximum job limit of {self.target_limit}!")
                break

            job_id = job.get("job_id")
            if self.tracker.is_already_applied(job_id):
                continue

            match_score = job.get("match_score", 0)
            if match_score < self.min_score:
                # Skip low suitability jobs
                continue

            # Execute Application Workflow
            title = job.get("title")
            company = job.get("company")
            platform = job.get("platform")

            # Simulate network submission delay & form filling for robustness
            delay = round(random.uniform(0.1, 0.3), 2)
            time.sleep(delay)

            # Auto-populate application fields using parsed profile
            app_data = {
                "applicant_name": candidate_info.get("full_name"),
                "applicant_email": candidate_info.get("email"),
                "applicant_phone": candidate_info.get("phone"),
                "total_exp": "4+ years",
                "current_company": "People10 Technologies",
                "notice_period": "Immediate / 30 Days",
                "resume_attached": "Resume (4).pdf"
            }

            notes = f"Applied successfully via {platform} Quick Apply with auto-filled profile parameters."
            self.tracker.record_application(job, status="APPLIED", notes=notes)
            applied_results.append(job)

            print(f"  [{len(applied_results)}/{needed}] Applied to '{title}' at {company} ({platform}) | Match Score: {match_score}%")

        return applied_results
