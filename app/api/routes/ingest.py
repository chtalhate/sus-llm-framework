from fastapi import APIRouter
from app.ingestion.loaders import CorpusLoader
from app.ingestion.chunkers import Chunker
from app.ingestion.indexer import Indexer
from app.api.routes.ask import retriever

router = APIRouter(prefix='/ingest', tags=['ingest'])


@router.post('/rebuild')
def rebuild_index():
    docs = CorpusLoader().load_seed_documents()
    chunks = Chunker().chunk_documents(docs)
    summary = Indexer().persist(chunks)
    retriever.refresh()
    return summary
