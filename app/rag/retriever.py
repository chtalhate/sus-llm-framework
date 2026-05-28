from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable
from app.domain.schemas import NormChunk
from app.ingestion.loaders import CorpusLoader

TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9_]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


class LocalRetriever:
    def __init__(self):
        self.loader = CorpusLoader()
        self.chunks = self.loader.load_chunks()
        self.doc_freq = Counter()
        self.doc_tokens: dict[str, Counter] = {}
        self._build_index()

    def _build_index(self) -> None:
        self.chunks = self.loader.load_chunks()
        self.doc_freq.clear()
        self.doc_tokens.clear()
        for chunk in self.chunks:
            counts = Counter(tokenize(chunk.text + ' ' + chunk.metadata.title + ' ' + chunk.metadata.category))
            self.doc_tokens[chunk.chunk_id] = counts
            for token in counts:
                self.doc_freq[token] += 1

    def refresh(self) -> None:
        self._build_index()

    def search(self, query: str, top_k: int = 6) -> list[NormChunk]:
        if not self.chunks:
            return []
        q_counts = Counter(tokenize(query))
        n_docs = len(self.chunks)
        scored: list[tuple[float, NormChunk]] = []
        for chunk in self.chunks:
            d_counts = self.doc_tokens.get(chunk.chunk_id, Counter())
            score = 0.0
            for token, q_tf in q_counts.items():
                if token not in d_counts:
                    continue
                df = self.doc_freq[token]
                idf = math.log((1 + n_docs) / (1 + df)) + 1.0
                score += (1 + math.log(d_counts[token])) * idf * q_tf
            if score > 0:
                scored.append((score, chunk.model_copy(update={'score': round(score, 4)})))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
