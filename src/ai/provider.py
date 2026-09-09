from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    """Abstract Base Class for AI Inference Engines (Ollama, OpenRouter, etc.)."""

    @abstractmethod
    def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Sends a prompt to the inference engine and returns a structured result:
        {
            "success": True|False,
            "text": "generated response text",
            "error": "error message if any"
        }
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the inference provider is reachable and active."""
        pass
