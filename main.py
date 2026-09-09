import json
import os
import sys
import time
from typing import Dict, Any

from src.parser import ProfileManager
from src.matcher import JobMatcher
from src.searcher import JobSearcher
from src.tracker import ApplicationTracker
from src.applier import JobApplier

def load_config() -> Dict[str, Any]:
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 70)
    print("🤖 LAZY-JOBBER - AUTOMATED JOB APPLICATION SUITE")
    print("=" * 70)

    # Step 1: Consume Resume & Learn User Basics
    print("\n📄 [1/4] Consuming Resume & Loading User Profile...")
    profile = ProfileManager("profile.json")
    info = profile.get_personal_info()
    skills = profile.get_all_skills()
    roles = profile.get_target_roles()

    print(f"   👤 Candidate Name : {info.get('full_name')}")
    print(f"   📧 Email          : {info.get('email')}")
    print(f"   📞 Phone          : {info.get('phone')}")
    print(f"   📍 Location       : {info.get('location')}")
    print(f"   🎯 Target Roles   : {', '.join(roles[:3])}")
    print(f"   🛠️ Core Skills    : {', '.join(skills[:8])}...")
    print("   ✅ Profile learned successfully from Resume (4).pdf!")

    # Step 2: Set Task Limit
    config = load_config()
    limit = config.get("application_limit", 40)
    print(f"\n⚙️  [2/4] Setting Task Application Limit...")
    print(f"   🎯 Application Limit: {limit} jobs max (Naukri, Indeed, LinkedIn)")

    # Step 3: Fetch & Match Suitable Jobs
    print(f"\n🔍 [3/4] Searching & Matching Jobs across Naukri, Indeed & LinkedIn...")
    searcher = JobSearcher(config)
    matcher = JobMatcher(profile)
    tracker = ApplicationTracker()

    raw_jobs = searcher.fetch_jobs(count=60)
    matched_jobs = []

    for job in raw_jobs:
        matcher.calculate_match_score(job)
        if job["match_score"] >= config["search_criteria"]["matching_score_threshold"] * 100:
            matched_jobs.append(job)

    # Sort jobs by match score descending
    matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    print(f"   🔎 Found {len(matched_jobs)} suitable high-matching jobs (>= 65% match score).")

    # Step 4: Apply to 40 Suitable Jobs
    print(f"\n🚀 [4/4] Applying to top suitable jobs (Target: {limit} jobs)...")
    applier = JobApplier(profile, tracker, config)
    applied_list = applier.apply_batch(matched_jobs, limit=limit)

    # Summary Report
    summary = tracker.get_summary()
    print("\n" + "=" * 70)
    print("🎉 APPLICATION RUN COMPLETED!")
    print("=" * 70)
    print(f"   ✅ Total Jobs Applied   : {summary['total_applied']} / {limit}")
    print(f"   ⭐ Avg Candidate Match  : {summary['average_match_score']}%")
    print(f"   🌐 Platform Distribution:")
    for plat, cnt in summary['by_platform'].items():
        print(f"      - {plat}: {cnt} jobs")
    print(f"\n📄 Complete audit log written to:")
    print(f"   - JSON Log: file:///{os.path.abspath('applied_jobs.json')}")
    print(f"   - CSV Report: file:///{os.path.abspath('applied_jobs.csv')}")
    print("=" * 70)

if __name__ == "__main__":
    main()
