from __future__ import annotations

from typing import Iterable
from app.domain.schemas import ChunkMetadata, NormChunk


class Chunker:
    def chunk_documents(self, docs: Iterable[dict]) -> list[NormChunk]:
        chunks: list[NormChunk] = []
        for doc in docs:
            paragraphs = [p.strip() for p in doc['content'].split("\n") if p.strip()]
            for idx, paragraph in enumerate(paragraphs, start=1):
                chunk_id = f"{doc['doc_id']}-{idx:03d}"
                chunks.append(
                    NormChunk(
                        chunk_id=chunk_id,
                        text=paragraph,
                        metadata=ChunkMetadata(
                            doc_id=doc['doc_id'],
                            title=doc['title'],
                            source=doc['source'],
                            category=doc['category'],
                            section=paragraph[:80],
                            version=doc.get('version', '1.0'),
                        ),
                    )
                )
        return chunks
