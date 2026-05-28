from __future__ import annotations

import requests
from app.core.config import settings


class OllamaClient:
    def generate(self, prompt: str) -> str:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            'model': settings.ollama_model,
            'prompt': prompt,
            'stream': False,
            'options': {'temperature': 0.1},
        }
        response = requests.post(url, json=payload, timeout=settings.llm_timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return data.get('response', '').strip()
