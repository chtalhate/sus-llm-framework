from fastapi import FastAPI
from app.db.session import Base, engine
from app.api.routes.ask import router as ask_router
from app.api.routes.benchmark import router as benchmark_router
from app.api.routes.audit import router as audit_router
from app.api.routes.ingest import router as ingest_router

Base.metadata.create_all(bind=engine)
app = FastAPI(title='SUS Guardrails POC', version='0.1.0')
app.include_router(ask_router)
app.include_router(benchmark_router)
app.include_router(audit_router)
app.include_router(ingest_router)


@app.get('/health')
def health():
    return {'status': 'ok'}
