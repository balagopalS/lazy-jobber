import os
import requests
from typing import Dict, Any, Optional
from src.ai.provider import LLMProvider
from src.logger import get_logger

logger = get_logger("openrouter")

class OpenRouterProvider(LLMProvider):
    """OpenRouter Cloud Inference Engine Provider."""

    def __init__(self, api_key: str = "", model: str = "meta-llama/llama-3.1-8b-instruct:free"):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_available():
            return {"success": False, "error": "OpenRouter API Key not configured.", "text": ""}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/balagopalS/lazy-jobber",
            "X-Title": "Lazy Jobber Application Suite",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2
        }

        try:
            logger.info(f"Querying OpenRouter API ({self.model})...")
            resp = requests.post(self.base_url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "text": content}
            else:
                err_msg = f"OpenRouter returned HTTP {resp.status_code}: {resp.text}"
                logger.error(err_msg)
                return {"success": False, "error": err_msg, "text": ""}
        except Exception as e:
            err_msg = f"Failed to connect to OpenRouter API: {str(e)}"
            logger.error(err_msg)
            return {"success": False, "error": err_msg, "text": ""}
