import json
from typing import Dict, Any, List
import requests
from app.core.config import settings


class OllamaClient:
    """
    Local LLM client communicating with Ollama API on localhost.
    Includes an extractive grounding fallback generator to ensure
    continuous testing even if Ollama service is temporarily offline.
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.fallback_enabled = settings.FALLBACK_LLM_ENABLED

    def generate(self, prompt: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Send prompt to local Ollama API. Falls back to extractive synthesis if Ollama is unreachable.
        """
        api_url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for strict factual grounding
                "top_p": 0.9,
            }
        }

        try:
            response = requests.post(api_url, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                return {
                    "answer": result.get("response", "").strip(),
                    "source": "ollama",
                    "model": self.model,
                }
        except Exception as e:
            print(f"[INFO] Ollama service not reachable on {self.base_url}: {e}")

        # If Ollama is unreachable, execute extractive fallback if enabled
        if self.fallback_enabled:
            return self._extractive_fallback(context_chunks)

        return {
            "answer": "Ollama local inference service is currently offline. Please ensure Ollama is running.",
            "source": "offline_error",
            "model": self.model,
        }

    def _extractive_fallback(self, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deterministic extractive grounding engine for local development & fallback.
        Extracts verified factual sentences directly from authorized chunks.
        """
        if not context_chunks:
            return {
                "answer": "The available authorized documents do not contain sufficient information to answer this question.",
                "source": "extractive_grounding",
                "model": "grounded-fallback",
            }

        answers = []
        for i, chunk in enumerate(context_chunks[:3]):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("filename", "Authorized Document")
            page = meta.get("page", 1)
            content = chunk.get("content", "").strip()

            # Take the most relevant sentences
            sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 25]
            if sentences:
                selected = ". ".join(sentences[:3]) + "."
                answers.append(f"According to **{doc_name}** (Page {page}):\n{selected}")

        composite_answer = "\n\n".join(answers)
        return {
            "answer": composite_answer,
            "source": "extractive_grounding",
            "model": "grounded-fallback",
        }


# Singleton Ollama client
ollama_client = OllamaClient()
