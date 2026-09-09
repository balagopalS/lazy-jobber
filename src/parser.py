import json
import os
from typing import Dict, Any

class ProfileManager:
    """Manages reading and loading the parsed user profile."""

    def __init__(self, profile_path: str = "profile.json"):
        self.profile_path = profile_path
        self.data: Dict[str, Any] = self._load_profile()

    def _load_profile(self) -> Dict[str, Any]:
        if not os.path.exists(self.profile_path):
            raise FileNotFoundError(f"Profile file not found at: {self.profile_path}")
        with open(self.profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_personal_info(self) -> Dict[str, Any]:
        return self.data.get("personal_info", {})

    def get_all_skills(self) -> list[str]:
        skills_dict = self.data.get("skills", {})
        all_skills = []
        for cat, skills in skills_dict.items():
            all_skills.extend(skills)
        return list(set(all_skills))

    def get_target_roles(self) -> list[str]:
        return self.data.get("target_roles", [])

    def get_summary(self) -> str:
        return self.data.get("summary", "")
