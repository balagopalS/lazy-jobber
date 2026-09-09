import json
import re
from typing import Dict, Any, Optional
from src.ai.provider import LLMProvider
from src.ai.ollama_provider import OllamaProvider
from src.ai.openrouter_provider import OpenRouterProvider
from src.parser import ProfileManager
from src.logger import get_logger

logger = get_logger("solver")

class QuestionSolver:
    """Uses Candidate Profile + AI LLM Engine to solve recruiter screening questions."""

    def __init__(self, profile_manager: Optional[ProfileManager] = None, config: Optional[Dict[str, Any]] = None):
        self.profile = profile_manager or ProfileManager("profile.json")
        self.config = config or {}
        self.provider = self._init_provider()

    def _init_provider(self) -> LLMProvider:
        ai_cfg = self.config.get("ai_config", {})
        provider_name = ai_cfg.get("provider", "ollama").lower()

        if provider_name == "openrouter":
            or_cfg = ai_cfg.get("openrouter", {})
            api_key = or_cfg.get("api_key", "")
            model = or_cfg.get("model", "meta-llama/llama-3.1-8b-instruct:free")
            p = OpenRouterProvider(api_key=api_key, model=model)
            if p.is_available():
                logger.info(f"Initialized OpenRouterProvider with model {model}")
                return p
            else:
                logger.warning("OpenRouter API key missing or invalid. Falling back to Ollama.")

        # Default / Fallback to Ollama
        ol_cfg = ai_cfg.get("ollama", {})
        base_url = ol_cfg.get("base_url", "http://localhost:11434")
        model = ol_cfg.get("model", "llama3")
        p = OllamaProvider(base_url=base_url, model=model)
        logger.info(f"Initialized OllamaProvider ({base_url}) with model {model}")
        return p

    def solve_question(self, question_text: str, field_type: str = "text", options: Optional[list] = None) -> Dict[str, Any]:
        """
        Solves a recruiter screening prompt given candidate profile context.
        Returns: { "answer": "...", "confidence": float, "source": "llm"|"heuristic" }
        """
        # Rule-based fast paths for standard recruiter queries
        q_lower = question_text.lower()
        personal = self.profile.get_personal_info()
        exp_years = self.profile.data.get("experience_years", 4.5)

        # Relocation / Current City
        if "relocat" in q_lower or "comfortable moving" in q_lower or "bengaluru" in q_lower:
            return {"answer": "Yes", "confidence": 0.99, "source": "heuristic"}

        # Total Experience
        if "total experience" in q_lower or "years of experience" in q_lower or "how many years" in q_lower:
            return {"answer": str(exp_years), "confidence": 0.98, "source": "heuristic"}

        # Notice Period
        if "notice period" in q_lower or "serving notice" in q_lower:
            return {"answer": "Immediate / 30 Days", "confidence": 0.95, "source": "heuristic"}

        # If LLM provider is available, use it for custom open-ended questions
        if self.provider and self.provider.is_available():
            system_prompt = (
                "You are an AI assistant helping a job candidate auto-fill recruiter questionnaires.\n"
                f"Candidate Summary:\n{json.dumps(self.profile.data, indent=2)}\n\n"
                "Return a JSON response strictly in format:\n"
                '{"answer": "short precise answer", "explanation": "brief reasoning"}'
            )

            user_prompt = f"Recruiter Question: '{question_text}'"
            if options:
                user_prompt += f"\nAvailable Radio/Dropdown Options: {options}"

            res = self.provider.generate_completion(user_prompt, system_prompt=system_prompt)
            if res.get("success") and res.get("text"):
                raw_text = res["text"].strip()
                try:
                    # Attempt JSON extraction
                    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        return {
                            "answer": parsed.get("answer", raw_text),
                            "confidence": 0.90,
                            "source": "llm"
                        }
                except Exception:
                    pass

                return {"answer": raw_text, "confidence": 0.80, "source": "llm"}

        # Ultimate fallback heuristic
        if options and "Yes" in options:
            return {"answer": "Yes", "confidence": 0.70, "source": "fallback"}

        return {"answer": "Yes", "confidence": 0.50, "source": "fallback"}
