from typing import Dict, Any, List

class JobMatcher:
    """Calculates match suitability score between candidate profile and a job listing."""

    def __init__(self, profile_manager):
        self.profile = profile_manager
        self.skills = [s.lower() for s in self.profile.get_all_skills()]
        self.target_roles = [r.lower() for r in self.profile.get_target_roles()]

    def calculate_match_score(self, job: Dict[str, Any]) -> float:
        title = job.get("title", "").lower()
        description = job.get("description", "").lower()

        # Title match weighting (40%)
        title_score = 0.0
        for role in self.target_roles:
            if role in title or any(w in title for w in ["java", "backend", "spring boot"]):
                title_score = 1.0
                break
            elif "software engineer" in title:
                title_score = 0.85
                break

        # Skill match weighting (50%)
        skill_count = 0
        matched_skills = []
        for skill in self.skills:
            clean_skill = skill.split("(")[0].strip()
            if clean_skill in description or clean_skill in title:
                skill_count += 1
                matched_skills.append(clean_skill)

        skill_score = min(1.0, skill_count / max(1, len(self.skills) * 0.4))

        # Experience level match (10%)
        exp_score = 1.0

        total_score = (title_score * 0.40) + (skill_score * 0.50) + (exp_score * 0.10)
        job["matched_skills"] = matched_skills
        job["match_score"] = round(total_score * 100, 1)

        return total_score
