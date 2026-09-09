import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any

class ApplicationTracker:
    """Tracks applied jobs, saves application history to JSON and CSV, and enforces task limits."""

    def __init__(self, json_file: str = "applied_jobs.json", csv_file: str = "applied_jobs.csv"):
        self.json_file = json_file
        self.csv_file = csv_file
        self.applied_jobs: List[Dict[str, Any]] = self._load_json()

    def _load_json(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def is_already_applied(self, job_id: str) -> bool:
        return any(job.get("job_id") == job_id for job in self.applied_jobs)

    def record_application(self, job: Dict[str, Any], status: str = "APPLIED", notes: str = ""):
        entry = {
            "applied_at": datetime.now().isoformat(),
            "job_id": job.get("job_id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "platform": job.get("platform"),
            "location": job.get("location"),
            "match_score": job.get("match_score"),
            "matched_skills": job.get("matched_skills", []),
            "url": job.get("url"),
            "status": status,
            "notes": notes
        }
        self.applied_jobs.append(entry)
        self._save()

    def _save(self):
        # Save JSON
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(self.applied_jobs, f, indent=2)

        # Save CSV
        fieldnames = ["applied_at", "job_id", "title", "company", "platform", "location", "match_score", "matched_skills", "url", "status", "notes"]
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for job in self.applied_jobs:
                row = {k: job.get(k, "") for k in fieldnames}
                if isinstance(row["matched_skills"], list):
                    row["matched_skills"] = ", ".join(row["matched_skills"])
                writer.writerow(row)

    def get_applied_count(self) -> int:
        return len([j for j in self.applied_jobs if j.get("status") == "APPLIED"])

    def get_summary(self) -> Dict[str, Any]:
        applied = [j for j in self.applied_jobs if j.get("status") == "APPLIED"]
        by_platform = {}
        for job in applied:
            plat = job.get("platform", "Unknown")
            by_platform[plat] = by_platform.get(plat, 0) + 1

        avg_match = (
            sum(j.get("match_score", 0) for j in applied) / len(applied)
            if applied else 0.0
        )

        return {
            "total_applied": len(applied),
            "by_platform": by_platform,
            "average_match_score": round(avg_match, 1)
        }
