import json
from pathlib import Path
from collections import Counter
from app.domain.schemas import NormChunk
from app.ingestion.loaders import PROCESSED_INDEX


class Indexer:
    def persist(self, chunks: list[NormChunk]) -> dict:
        PROCESSED_INDEX.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            {
                'chunk_id': c.chunk_id,
                'text': c.text,
                'metadata': c.metadata.model_dump(),
            }
            for c in chunks
        ]
        with PROCESSED_INDEX.open('w', encoding='utf-8') as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
        return {
            'chunks': len(chunks),
            'documents': len({c.metadata.doc_id for c in chunks}),
            'categories': dict(Counter(c.metadata.category for c in chunks)),
        }
