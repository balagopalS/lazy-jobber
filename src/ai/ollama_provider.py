import requests
from typing import Dict, Any, Optional
from src.ai.provider import LLMProvider
from src.logger import get_logger

logger = get_logger("ollama")

class OllamaProvider(LLMProvider):
    """Local Ollama Inference Engine Provider."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            logger.info(f"Querying local Ollama ({self.model})...")
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "")
                return {"success": True, "text": content}
            else:
                err_msg = f"Ollama returned HTTP {resp.status_code}: {resp.text}"
                logger.error(err_msg)
                return {"success": False, "error": err_msg, "text": ""}
        except Exception as e:
            err_msg = f"Failed to connect to local Ollama server: {str(e)}"
            logger.error(err_msg)
            return {"success": False, "error": err_msg, "text": ""}
