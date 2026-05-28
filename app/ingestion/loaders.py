import json
from pathlib import Path
from app.domain.schemas import ChunkMetadata, NormChunk


RAW_CORPUS = Path('data/raw/seed_corpus.json')
PROCESSED_INDEX = Path('data/processed/norm_chunks.json')


class CorpusLoader:
    def load_seed_documents(self) -> list[dict]:
        with RAW_CORPUS.open('r', encoding='utf-8') as fh:
            return json.load(fh)

    def load_chunks(self) -> list[NormChunk]:
        if not PROCESSED_INDEX.exists():
            return []
        with PROCESSED_INDEX.open('r', encoding='utf-8') as fh:
            rows = json.load(fh)
        chunks = []
        for row in rows:
            chunks.append(
                NormChunk(
                    chunk_id=row['chunk_id'],
                    text=row['text'],
                    metadata=ChunkMetadata(**row['metadata']),
                )
            )
        return chunks
