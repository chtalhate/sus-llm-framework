from __future__ import annotations

from app.domain.schemas import NormChunk


class SimpleReranker:
    def rerank(self, question: str, chunks: list[NormChunk], top_k: int = 4) -> list[NormChunk]:
        q = question.lower()
        rescored = []
        for chunk in chunks:
            bonus = 0.0
            for term in q.split():
                if term in chunk.text.lower():
                    bonus += 0.15
                if term in chunk.metadata.title.lower():
                    bonus += 0.25
            rescored.append(chunk.model_copy(update={'score': round(chunk.score + bonus, 4)}))
        rescored.sort(key=lambda c: c.score, reverse=True)
        return rescored[:top_k]
