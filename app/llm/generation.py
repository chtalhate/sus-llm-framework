from __future__ import annotations

from app.rag.prompts import build_prompt
from app.llm.ollama_client import OllamaClient


class GeneratorService:
    def __init__(self):
        self.client = OllamaClient()

    def generate(self, question: str, condition: str, context_chunks: list[str]) -> tuple[str, bool]:
        prompt = build_prompt(question=question, context=context_chunks, condition=condition)
        try:
            return self.client.generate(prompt), True
        except Exception:
            return self._fallback(question, condition, context_chunks), False

    def _fallback(self, question: str, condition: str, context_chunks: list[str]) -> str:
        base = [
            f'Resposta em modo {condition}.',
            f'Pergunta: {question}',
        ]
        if context_chunks:
            base.append('Síntese normativa recuperada:')
            base.extend([f'- {c[:220]}' for c in context_chunks[:4]])
            base.append('Com base nos trechos recuperados, a orientação deve ser confirmada na norma local e na regulação aplicável.')
        else:
            base.append('Sem contexto normativo recuperado, a resposta deve ser tratada como preliminar.')
        return "\n".join(base)
