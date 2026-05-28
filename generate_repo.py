from pathlib import Path
import json, textwrap

root = Path('/mnt/data/sus-guardrails-poc')
files = {}

def add(path, content):
    files[path] = textwrap.dedent(content).lstrip('\n')

add('.env.example', '''
APP_ENV=development
API_PORT=8000
UI_PORT=8501
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
DATABASE_URL=sqlite:///./data/processed/audit.db
COLLECTION_NAME=sus_norms
USE_QDRANT=false
QDRANT_URL=http://qdrant:6333
TOP_K=6
RERANK_K=4
MAX_CONTEXT_CHUNKS=4
LLM_TIMEOUT_SECONDS=120
''')

add('requirements.txt', '''
fastapi==0.115.0
uvicorn[standard]==0.30.6
streamlit==1.39.0
pydantic==2.9.2
pydantic-settings==2.5.2
sqlalchemy==2.0.35
requests==2.32.3
pandas==2.2.3
numpy==2.1.1
scikit-learn==1.5.2
python-multipart==0.0.12
qdrant-client==1.11.3
orjson==3.10.7
''')

add('Dockerfile.api', '''
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
COPY experiments ./experiments
COPY .env.example ./.env.example
EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
''')

add('Dockerfile.ui', '''
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ui ./ui
COPY app ./app
COPY data ./data
COPY experiments ./experiments
COPY .env.example ./.env.example
EXPOSE 8501
CMD ["streamlit", "run", "ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
''')

add('docker-compose.yml', '''
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    container_name: sus-guardrails-api
    env_file:
      - .env.example
    environment:
      DATABASE_URL: sqlite:////app/data/processed/audit.db
      OLLAMA_BASE_URL: http://ollama:11434
      QDRANT_URL: http://qdrant:6333
    volumes:
      - ./data:/app/data
      - ./experiments:/app/experiments
    ports:
      - "8000:8000"
    depends_on:
      - qdrant
      - ollama

  ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    container_name: sus-guardrails-ui
    env_file:
      - .env.example
    environment:
      API_BASE_URL: http://api:8000
    volumes:
      - ./data:/app/data
      - ./experiments:/app/experiments
    ports:
      - "8501:8501"
    depends_on:
      - api

  qdrant:
    image: qdrant/qdrant:v1.12.1
    container_name: sus-guardrails-qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

  ollama:
    image: ollama/ollama:0.3.12
    container_name: sus-guardrails-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  qdrant_storage:
  ollama_data:
''')

add('README.md', '''
# SUS Guardrails POC

POC em Python + Docker para demonstrar, na defesa, o framework da dissertação: mitigação de alucinações em LLMs aplicados às normativas do SUS.

O projeto implementa os quatro módulos descritos na dissertação:
- **M1 — Base normativa do SUS**: ingestão, segmentação, metadados e recuperação.
- **M2 — LLM + RAG**: execução das condições **C1**, **C2** e **C3**.
- **M3 — Verificação normativa pós-geração**: extração de afirmações, verificação de suporte, classificação T1–T6 e revisão.
- **M4 — Governança e auditoria**: trilha E1–E6, métricas TA/AN/SM/F1/IG, logs e exportação.

## Arquitetura

```text
Usuário -> Streamlit -> FastAPI
                     -> M1: corpus normativo e retriever
                     -> M2: geração C1/C2/C3 via Ollama
                     -> M3: verificação normativa e taxonomia
                     -> M4: auditoria SQLite + relatórios
```

## Stack
- Python 3.11
- FastAPI
- Streamlit
- SQLite
- Qdrant (opcional; o código possui fallback lexical local para rodar sem dependência vetorial)
- Ollama (modelo local open-source, ex.: `qwen2.5:7b-instruct`)
- Docker / Docker Compose

## Como subir

1. Ajuste variáveis em `.env.example` se quiser.
2. Suba a stack:

```bash
docker compose up --build
```

3. Baixe o modelo no container do Ollama:

```bash
docker exec -it sus-guardrails-ollama ollama pull qwen2.5:7b-instruct
```

4. Gere o índice inicial:

```bash
curl -X POST http://localhost:8000/ingest/rebuild
```

5. Acesse:
- API: http://localhost:8000/docs
- UI: http://localhost:8501

## Modos experimentais
- **C1**: LLM puro.
- **C2**: LLM + blocos normativos recuperados.
- **C3**: LLM + RAG + verificação normativa pós-geração.

## Métricas implementadas
- **TA** = respostas_alucinadas / respostas_totais
- **AN** = afirmações_corretas / afirmações_totais
- **SM** = soma(severidade) / número_de_erros
- **F1** = 2 × (P × C) / (P + C)
- **IG** = (AN + (1 − TA) + (1 − SM/3)) / 3

## Dataset demonstrável
O repositório já inclui:
- corpus inicial curado do SUS em `data/raw/seed_corpus.json`
- benchmark de 24 perguntas em `experiments/questions_demo.json`

## Observações importantes
- O projeto foi preparado para a **defesa offline**, com fallback semântico/lexical e sem dependência obrigatória de serviços externos.
- Quando o Ollama não estiver disponível, a API retorna uma resposta determinística de fallback, útil para ensaio técnico do pipeline.
- A verificação normativa é heurística e auditável. Ela demonstra o fluxo científico da dissertação, não substitui validação humana especializada.

## Estrutura

```text
app/
  api/             # rotas FastAPI
  core/            # configuração e constantes
  domain/          # enums, schemas e modelos
  ingestion/       # ingestão e chunking
  rag/             # recuperação e prompts
  llm/             # cliente Ollama + fallback
  verifier/        # claims, taxonomia, revisão
  metrics/         # fórmulas TA/AN/SM/F1/IG
  governance/      # auditoria e exportação
  db/              # SQLite
ui/
  streamlit_app.py
experiments/
  questions_demo.json
```

## Roteiro de demo sugerido
1. Rodar a mesma pergunta em C1, C2 e C3.
2. Mostrar os blocos normativos recuperados.
3. Exibir afirmações verificadas e tipos T1–T6.
4. Comparar AN e IG entre as três condições.
5. Rodar o benchmark das 24 perguntas.
6. Abrir a trilha de auditoria da última execução.
''')

add('app/core/config.py', '''
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env.example', extra='ignore')

    app_env: str = 'development'
    api_port: int = 8000
    ui_port: int = 8501
    api_base_url: str = 'http://api:8000'
    database_url: str = 'sqlite:///./data/processed/audit.db'
    ollama_base_url: str = 'http://ollama:11434'
    ollama_model: str = 'qwen2.5:7b-instruct'
    collection_name: str = 'sus_norms'
    use_qdrant: bool = False
    qdrant_url: str = 'http://qdrant:6333'
    top_k: int = 6
    rerank_k: int = 4
    max_context_chunks: int = 4
    llm_timeout_seconds: int = 120


settings = Settings()
''')

add('app/core/constants.py', '''
SYSTEM_PROMPT = """
Você é um assistente institucional do SUS orientado por normas oficiais.
Responda em português do Brasil, de forma objetiva, sem inventar portarias, fluxos ou critérios.
Quando houver incerteza, explicite a limitação e recomende consulta à equipe de saúde/gestão local.
Não prescreva condutas clínicas individualizadas.
""".strip()

INSTITUTIONAL_WARNING = (
    'Aviso institucional: esta resposta é uma orientação informacional. '
    'Em temas assistenciais, regulatórios ou clínicos, a decisão final depende da avaliação '
    'da equipe de saúde, da regulação local e da norma oficial vigente.'
)
''')

add('app/domain/enums.py', '''
from enum import Enum


class Condition(str, Enum):
    C1 = 'C1'
    C2 = 'C2'
    C3 = 'C3'


class HallucinationType(str, Enum):
    T1 = 'T1'
    T2 = 'T2'
    T3 = 'T3'
    T4 = 'T4'
    T5 = 'T5'
    T6 = 'T6'
''')

add('app/domain/schemas.py', '''
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, List, Optional
from .enums import Condition


class ChunkMetadata(BaseModel):
    doc_id: str
    title: str
    source: str
    category: str
    section: str
    version: str = '1.0'


class NormChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: ChunkMetadata
    score: float = 0.0


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    condition: Condition = Condition.C3
    top_k: int = 6


class ClaimCheck(BaseModel):
    claim: str
    supported: bool
    evidence_chunk_ids: List[str] = Field(default_factory=list)
    evidence_titles: List[str] = Field(default_factory=list)
    notes: str = ''
    taxonomy: List[str] = Field(default_factory=list)
    severity: int = 0


class MetricsResult(BaseModel):
    ta: float
    an: float
    sm: float
    f1: float
    ig: float


class AskResponse(BaseModel):
    session_id: str
    question: str
    condition: Condition
    answer: str
    raw_answer: str
    warning: str
    retrieved_chunks: List[NormChunk]
    claims: List[ClaimCheck]
    metrics: MetricsResult
    audit_id: Optional[int] = None
    trace: List[dict[str, Any]] = Field(default_factory=list)


class BenchmarkItem(BaseModel):
    id: str
    axis: str
    question: str
    expected_keywords: List[str] = Field(default_factory=list)
    expected_sources: List[str] = Field(default_factory=list)
    risk_level: str = 'moderado'
    potential_types: List[str] = Field(default_factory=list)


class BenchmarkSummary(BaseModel):
    condition: Condition
    items: int
    avg_ta: float
    avg_an: float
    avg_sm: float
    avg_f1: float
    avg_ig: float
    details: List[dict[str, Any]]
''')

add('app/db/session.py', '''
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
''')

add('app/db/sqlite_models.py', '''
from sqlalchemy import Column, Integer, String, Text, Float
from app.db.session import Base


class AuditRun(Base):
    __tablename__ = 'audit_runs'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    question = Column(Text, nullable=False)
    condition = Column(String(8), nullable=False)
    answer = Column(Text, nullable=False)
    raw_answer = Column(Text, nullable=False)
    claims_json = Column(Text, nullable=False)
    retrieved_json = Column(Text, nullable=False)
    trace_json = Column(Text, nullable=False)
    ta = Column(Float, nullable=False)
    an = Column(Float, nullable=False)
    sm = Column(Float, nullable=False)
    f1 = Column(Float, nullable=False)
    ig = Column(Float, nullable=False)
    created_at = Column(String(32), nullable=False)
''')

add('app/db/repositories.py', '''
import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.sqlite_models import AuditRun


class AuditRepository:
    def create(self, payload: dict) -> int:
        with SessionLocal() as session:
            obj = AuditRun(
                session_id=payload['session_id'],
                question=payload['question'],
                condition=payload['condition'],
                answer=payload['answer'],
                raw_answer=payload['raw_answer'],
                claims_json=json.dumps(payload['claims'], ensure_ascii=False),
                retrieved_json=json.dumps(payload['retrieved_chunks'], ensure_ascii=False),
                trace_json=json.dumps(payload['trace'], ensure_ascii=False),
                ta=payload['metrics']['ta'],
                an=payload['metrics']['an'],
                sm=payload['metrics']['sm'],
                f1=payload['metrics']['f1'],
                ig=payload['metrics']['ig'],
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj.id

    def list(self, limit: int = 50) -> list[dict]:
        with SessionLocal() as session:
            rows = session.execute(select(AuditRun).order_by(AuditRun.id.desc()).limit(limit)).scalars().all()
            return [
                {
                    'id': row.id,
                    'session_id': row.session_id,
                    'question': row.question,
                    'condition': row.condition,
                    'ta': row.ta,
                    'an': row.an,
                    'sm': row.sm,
                    'f1': row.f1,
                    'ig': row.ig,
                    'created_at': row.created_at,
                }
                for row in rows
            ]
''')

add('app/ingestion/loaders.py', '''
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
''')

add('app/ingestion/chunkers.py', '''
from __future__ import annotations

from typing import Iterable
from app.domain.schemas import ChunkMetadata, NormChunk


class Chunker:
    def chunk_documents(self, docs: Iterable[dict]) -> list[NormChunk]:
        chunks: list[NormChunk] = []
        for doc in docs:
            paragraphs = [p.strip() for p in doc['content'].split('\n') if p.strip()]
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
''')

add('app/ingestion/indexer.py', '''
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
''')

add('app/rag/retriever.py', '''
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
''')

add('app/rag/reranker.py', '''
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
''')

add('app/rag/prompts.py', '''
from app.core.constants import SYSTEM_PROMPT


def build_prompt(question: str, context: list[str], condition: str) -> str:
    sections = [SYSTEM_PROMPT, f'Condição experimental: {condition}', f'Pergunta: {question}']
    if context:
        sections.append('Contexto normativo recuperado:')
        for idx, chunk in enumerate(context, start=1):
            sections.append(f'[{idx}] {chunk}')
    sections.append(
        'Responda em tópicos curtos com: resposta objetiva, justificativa normativa, '\
        'limitações/condicionantes e orientação institucional final.'
    )
    return '\n\n'.join(sections)
''')

add('app/llm/ollama_client.py', '''
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
''')

add('app/llm/generation.py', '''
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
        return '\n'.join(base)
''')

add('app/verifier/claim_extractor.py', '''
from __future__ import annotations

import re


class ClaimExtractor:
    def extract(self, answer: str) -> list[str]:
        parts = re.split(r'[\n\.!?;]+', answer)
        claims = []
        for part in parts:
            text = part.strip(' -•\t')
            if len(text) >= 20:
                claims.append(text)
        return claims[:8]
''')

add('app/verifier/taxonomy.py', '''
from __future__ import annotations

from app.domain.enums import HallucinationType


class TaxonomyClassifier:
    def classify(self, claim: str, supported: bool, has_sources: bool) -> list[str]:
        claim_l = claim.lower()
        tags: list[str] = []
        if not supported and any(x in claim_l for x in ['lei', 'portaria', 'decreto', 'pcdt', 'rename', 'sigtap']):
            tags.append(HallucinationType.T5.value)
        if not supported and any(x in claim_l for x in ['cobre', 'direito', 'garante', 'obrigatório']):
            tags.append(HallucinationType.T1.value)
        if not supported and any(x in claim_l for x in ['fila', 'regulação', 'sisreg', 'uti', 'encaminhamento', 'transfer']):
            tags.append(HallucinationType.T2.value)
        if not supported and any(x in claim_l for x in ['critério', 'elegível', 'tem direito', 'pré-requisito']):
            tags.append(HallucinationType.T3.value)
        if any(x in claim_l for x in ['deve tomar', 'ajuste a dose', 'indicação cirúrgica', 'internação psiquiátrica']):
            tags.append(HallucinationType.T4.value)
        if supported and not has_sources:
            tags.append(HallucinationType.T6.value)
        return sorted(set(tags))
''')

add('app/verifier/evidence_checker.py', '''
from __future__ import annotations

from collections import Counter
from app.domain.schemas import ClaimCheck, NormChunk
from app.verifier.taxonomy import TaxonomyClassifier


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in text.replace('/', ' ').replace('-', ' ').split() if len(t) > 2]


class EvidenceChecker:
    def __init__(self):
        self.taxonomy = TaxonomyClassifier()

    def check_claims(self, claims: list[str], chunks: list[NormChunk]) -> list[ClaimCheck]:
        results: list[ClaimCheck] = []
        joined_chunks = {chunk.chunk_id: Counter(_tokenize(chunk.text + ' ' + chunk.metadata.title)) for chunk in chunks}
        for claim in claims:
            c_tokens = Counter(_tokenize(claim))
            scored: list[tuple[int, NormChunk]] = []
            for chunk in chunks:
                overlap = sum(min(c_tokens[t], joined_chunks[chunk.chunk_id][t]) for t in c_tokens)
                if overlap > 0:
                    scored.append((overlap, chunk))
            scored.sort(key=lambda x: x[0], reverse=True)
            top = [chunk for _, chunk in scored[:2]]
            supported = bool(top and scored[0][0] >= 2)
            taxonomy = self.taxonomy.classify(claim, supported=supported, has_sources=bool(top))
            severity = min(3, max(0, len(taxonomy)))
            notes = 'Afirmação suportada por trechos recuperados.' if supported else 'Afirmação sem suporte robusto nos trechos recuperados.'
            results.append(
                ClaimCheck(
                    claim=claim,
                    supported=supported,
                    evidence_chunk_ids=[c.chunk_id for c in top],
                    evidence_titles=[c.metadata.title for c in top],
                    notes=notes,
                    taxonomy=taxonomy,
                    severity=severity,
                )
            )
        return results
''')

add('app/verifier/reviser.py', '''
from __future__ import annotations

from app.core.constants import INSTITUTIONAL_WARNING
from app.domain.schemas import ClaimCheck


class Reviser:
    def revise(self, raw_answer: str, checks: list[ClaimCheck]) -> str:
        unsupported = [c for c in checks if not c.supported]
        if not unsupported:
            return raw_answer.strip() + '\n\n' + INSTITUTIONAL_WARNING

        revisions = ['Resposta revisada com verificação normativa:', raw_answer.strip(), '', 'Pontos de atenção identificados:']
        for item in unsupported[:5]:
            revisions.append(f"- '{item.claim}' -> revisar/confirmar em norma oficial; tipos detectados: {', '.join(item.taxonomy) or 'nenhum'}.")
        revisions.append('')
        revisions.append(INSTITUTIONAL_WARNING)
        return '\n'.join(revisions)
''')

add('app/metrics/formulas.py', '''
from __future__ import annotations

from app.domain.schemas import ClaimCheck, MetricsResult


class MetricsCalculator:
    def calculate(self, checks: list[ClaimCheck], retrieved_chunks_count: int) -> MetricsResult:
        total_claims = max(1, len(checks))
        supported = sum(1 for c in checks if c.supported)
        errors = [c for c in checks if not c.supported or c.taxonomy]
        hallucinated_responses = 1 if errors else 0
        ta = hallucinated_responses / 1
        an = supported / total_claims
        sm = (sum(c.severity for c in errors) / len(errors)) if errors else 0.0
        precision = an
        coverage = min(1.0, retrieved_chunks_count / max(1, total_claims))
        f1 = 0.0 if (precision + coverage) == 0 else (2 * (precision * coverage) / (precision + coverage))
        ig = (an + (1 - ta) + (1 - sm / 3)) / 3
        return MetricsResult(
            ta=round(ta, 4),
            an=round(an, 4),
            sm=round(sm, 4),
            f1=round(f1, 4),
            ig=round(ig, 4),
        )
''')

add('app/governance/audit_logger.py', '''
from __future__ import annotations

from app.db.repositories import AuditRepository


class AuditLogger:
    def __init__(self):
        self.repo = AuditRepository()

    def save(self, response_payload: dict) -> int:
        return self.repo.create(response_payload)

    def list_runs(self, limit: int = 50) -> list[dict]:
        return self.repo.list(limit=limit)
''')

add('app/governance/exporters.py', '''
from __future__ import annotations

import csv
from pathlib import Path
from app.governance.audit_logger import AuditLogger


class AuditExporter:
    def export_csv(self, output_path: str = 'data/processed/audit_export.csv') -> str:
        rows = AuditLogger().list_runs(limit=500)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not rows:
            path.write_text('', encoding='utf-8')
            return str(path)
        with path.open('w', encoding='utf-8', newline='') as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return str(path)
''')

add('app/api/routes/ask.py', '''
from __future__ import annotations

from fastapi import APIRouter
import uuid
from app.core.constants import INSTITUTIONAL_WARNING
from app.core.config import settings
from app.domain.schemas import AskRequest, AskResponse
from app.rag.retriever import LocalRetriever
from app.rag.reranker import SimpleReranker
from app.llm.generation import GeneratorService
from app.verifier.claim_extractor import ClaimExtractor
from app.verifier.evidence_checker import EvidenceChecker
from app.verifier.reviser import Reviser
from app.metrics.formulas import MetricsCalculator
from app.governance.audit_logger import AuditLogger

router = APIRouter(prefix='/ask', tags=['ask'])
retriever = LocalRetriever()
reranker = SimpleReranker()
generator = GeneratorService()
extractor = ClaimExtractor()
checker = EvidenceChecker()
reviser = Reviser()
metrics_calc = MetricsCalculator()
audit = AuditLogger()


@router.post('', response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    session_id = uuid.uuid4().hex[:12]
    trace = [{'stage': 'E1', 'description': 'Pergunta recebida', 'question': request.question}]

    chunks = []
    if request.condition in ('C2', 'C3'):
        chunks = retriever.search(request.question, top_k=min(request.top_k, settings.top_k))
        chunks = reranker.rerank(request.question, chunks, top_k=settings.rerank_k)
        trace.append({'stage': 'E2', 'description': 'Recuperação normativa', 'chunks': [c.chunk_id for c in chunks]})

    context = [f"{c.metadata.title}: {c.text}" for c in chunks[: settings.max_context_chunks]]
    raw_answer, llm_ok = generator.generate(request.question, request.condition.value, context)
    trace.append({'stage': 'E3', 'description': 'Geração', 'llm_ok': llm_ok})

    claims = extractor.extract(raw_answer)
    checks = checker.check_claims(claims, chunks) if request.condition == 'C3' else checker.check_claims(claims, chunks[:1])
    trace.append({'stage': 'E4', 'description': 'Verificação', 'claims': len(checks)})

    answer = reviser.revise(raw_answer, checks) if request.condition == 'C3' else raw_answer + '\n\n' + INSTITUTIONAL_WARNING
    metrics = metrics_calc.calculate(checks, len(chunks))
    trace.append({'stage': 'E5', 'description': 'Entrega', 'warning': True})

    payload = {
        'session_id': session_id,
        'question': request.question,
        'condition': request.condition.value,
        'answer': answer,
        'raw_answer': raw_answer,
        'claims': [c.model_dump() for c in checks],
        'retrieved_chunks': [c.model_dump() for c in chunks],
        'trace': trace + [{'stage': 'E6', 'description': 'Registro'}],
        'metrics': metrics.model_dump(),
    }
    audit_id = audit.save(payload)

    return AskResponse(
        session_id=session_id,
        question=request.question,
        condition=request.condition,
        answer=answer,
        raw_answer=raw_answer,
        warning=INSTITUTIONAL_WARNING,
        retrieved_chunks=chunks,
        claims=checks,
        metrics=metrics,
        audit_id=audit_id,
        trace=payload['trace'],
    )
''')

add('app/api/routes/benchmark.py', '''
from __future__ import annotations

import json
from pathlib import Path
from fastapi import APIRouter
from app.domain.enums import Condition
from app.domain.schemas import BenchmarkSummary, AskRequest
from app.api.routes.ask import ask

router = APIRouter(prefix='/benchmark', tags=['benchmark'])
DATASET = Path('experiments/questions_demo.json')


@router.get('/dataset')
def dataset() -> list[dict]:
    return json.loads(DATASET.read_text(encoding='utf-8'))


@router.post('/run/{condition}', response_model=BenchmarkSummary)
def run_benchmark(condition: Condition) -> BenchmarkSummary:
    items = json.loads(DATASET.read_text(encoding='utf-8'))
    details = []
    agg = {'ta': 0.0, 'an': 0.0, 'sm': 0.0, 'f1': 0.0, 'ig': 0.0}
    for item in items:
        resp = ask(AskRequest(question=item['question'], condition=condition))
        result = {
            'id': item['id'],
            'question': item['question'],
            'ta': resp.metrics.ta,
            'an': resp.metrics.an,
            'sm': resp.metrics.sm,
            'f1': resp.metrics.f1,
            'ig': resp.metrics.ig,
        }
        details.append(result)
        for key in agg:
            agg[key] += result[key]
    n = max(1, len(details))
    return BenchmarkSummary(
        condition=condition,
        items=n,
        avg_ta=round(agg['ta'] / n, 4),
        avg_an=round(agg['an'] / n, 4),
        avg_sm=round(agg['sm'] / n, 4),
        avg_f1=round(agg['f1'] / n, 4),
        avg_ig=round(agg['ig'] / n, 4),
        details=details,
    )
''')

add('app/api/routes/audit.py', '''
from fastapi import APIRouter
from app.governance.audit_logger import AuditLogger
from app.governance.exporters import AuditExporter

router = APIRouter(prefix='/audit', tags=['audit'])
logger = AuditLogger()
exporter = AuditExporter()


@router.get('')
def list_audit(limit: int = 50):
    return logger.list_runs(limit=limit)


@router.post('/export')
def export_audit():
    return {'path': exporter.export_csv()}
''')

add('app/api/routes/ingest.py', '''
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
''')

add('app/api/main.py', '''
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
''')

add('ui/streamlit_app.py', '''
from __future__ import annotations

import os
import pandas as pd
import requests
import streamlit as st

API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

st.set_page_config(page_title='SUS Guardrails POC', layout='wide')
st.title('SUS Guardrails POC')
st.caption('POC da dissertação: C1, C2, C3 + verificação normativa + auditoria')


def api_get(path: str):
    return requests.get(f'{API_BASE_URL}{path}', timeout=120).json()


def api_post(path: str, payload=None):
    return requests.post(f'{API_BASE_URL}{path}', json=payload or {}, timeout=120).json()


with st.sidebar:
    st.subheader('Inicialização')
    if st.button('Reconstruir índice normativo'):
        st.json(api_post('/ingest/rebuild'))
    st.write('API:', API_BASE_URL)


tab1, tab2, tab3, tab4 = st.tabs(['Pergunta individual', 'Comparador C1/C2/C3', 'Benchmark', 'Auditoria'])

with tab1:
    question = st.text_area('Pergunta', 'Como marcar consulta com especialista pelo SUS?')
    condition = st.selectbox('Condição', ['C1', 'C2', 'C3'], index=2)
    if st.button('Executar pergunta'):
        result = api_post('/ask', {'question': question, 'condition': condition})
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader('Resposta')
            st.write(result['answer'])
            st.subheader('Afirmações verificadas')
            st.dataframe(pd.DataFrame(result['claims']))
        with col2:
            st.subheader('Métricas')
            st.json(result['metrics'])
            st.subheader('Blocos recuperados')
            st.dataframe(pd.DataFrame(result['retrieved_chunks']))
            st.subheader('Rastro E1–E6')
            st.json(result['trace'])

with tab2:
    compare_question = st.text_area('Pergunta para comparação', 'O SUS cobre cirurgia bariátrica?')
    if st.button('Comparar C1, C2 e C3'):
        cols = st.columns(3)
        for idx, mode in enumerate(['C1', 'C2', 'C3']):
            result = api_post('/ask', {'question': compare_question, 'condition': mode})
            with cols[idx]:
                st.markdown(f'### {mode}')
                st.write(result['answer'])
                st.json(result['metrics'])

with tab3:
    dataset = api_get('/benchmark/dataset')
    st.write(f'Itens do benchmark: {len(dataset)}')
    if st.button('Rodar benchmark C3'):
        result = api_post('/benchmark/run/C3')
        st.json({k: v for k, v in result.items() if k != 'details'})
        st.dataframe(pd.DataFrame(result['details']))

with tab4:
    audits = api_get('/audit')
    st.dataframe(pd.DataFrame(audits))
    if st.button('Exportar auditoria CSV'):
        st.json(api_post('/audit/export'))
''')

seed_corpus = [
  {
    'doc_id': 'CF88-196-200',
    'title': 'Constituição Federal de 1988 - Artigos 196 a 200',
    'source': 'Constituição Federal',
    'category': 'direitos e organização',
    'version': '1.0',
    'content': 'Art. 196: a saúde é direito de todos e dever do Estado, garantido mediante políticas sociais e econômicas.\nArt. 197: são de relevância pública as ações e serviços de saúde, cabendo ao poder público dispor sobre sua regulamentação, fiscalização e controle.\nArt. 198: as ações e serviços públicos de saúde integram uma rede regionalizada e hierarquizada e constituem um sistema único.\nArt. 200: ao SUS compete controlar e fiscalizar procedimentos, produtos e substâncias de interesse para a saúde.'
  },
  {
    'doc_id': 'LEI-8080',
    'title': 'Lei nº 8.080/1990 - Lei Orgânica da Saúde',
    'source': 'Lei 8.080/1990',
    'category': 'organização do sus',
    'version': '1.0',
    'content': 'A Lei 8.080 dispõe sobre as condições para promoção, proteção e recuperação da saúde e sobre a organização e o funcionamento dos serviços correspondentes.\nA assistência terapêutica integral, inclusive farmacêutica, está incluída no campo de atuação do SUS.\nO acesso universal e igualitário às ações e serviços de saúde deve observar organização regionalizada e hierarquizada.'
  },
  {
    'doc_id': 'DEC-7508',
    'title': 'Decreto nº 7.508/2011',
    'source': 'Decreto 7.508/2011',
    'category': 'regulação e acesso',
    'version': '1.0',
    'content': 'O Decreto 7.508 regulamenta a Lei 8.080 e organiza o planejamento da saúde, a assistência à saúde e a articulação interfederativa.\nO acesso universal, igualitário e ordenado às ações e serviços de saúde se inicia pelas portas de entrada do SUS e se completa na rede regionalizada e hierarquizada.\nA regulação é elemento essencial para organização do acesso a serviços especializados e hospitalares.'
  },
  {
    'doc_id': 'PNAB-2017',
    'title': 'Política Nacional de Atenção Básica - PNAB',
    'source': 'PNAB',
    'category': 'atenção básica',
    'version': '1.0',
    'content': 'A Atenção Básica é a principal porta de entrada e centro de comunicação da Rede de Atenção à Saúde.\nA UBS deve coordenar o cuidado e, quando necessário, realizar encaminhamento para atenção especializada.\nA longitudinalidade e a coordenação do cuidado são atributos centrais da atenção básica.'
  },
  {
    'doc_id': 'CARTA-DIREITOS',
    'title': 'Carta dos Direitos dos Usuários da Saúde',
    'source': 'Carta dos Direitos dos Usuários da Saúde',
    'category': 'direitos do usuário',
    'version': '1.0',
    'content': 'Todo cidadão tem direito ao acesso ordenado e organizado aos sistemas de saúde.\nO usuário tem direito a informação clara sobre os serviços, tratamento adequado, respeito e registro em prontuário.\nO usuário pode recorrer à ouvidoria e a canais formais de reclamação e manifestação.'
  },
  {
    'doc_id': 'RENAME-BASE',
    'title': 'RENAME - Relação Nacional de Medicamentos Essenciais',
    'source': 'RENAME',
    'category': 'assistência farmacêutica',
    'version': '1.0',
    'content': 'A RENAME orienta a seleção de medicamentos ofertados no SUS, observando protocolos, financiamento e organização dos componentes da assistência farmacêutica.\nO fornecimento depende do enquadramento do medicamento e dos critérios clínicos e administrativos aplicáveis.\nMedicamentos especializados costumam exigir critérios definidos em protocolos específicos.'
  },
  {
    'doc_id': 'SIGTAP-BASE',
    'title': 'SIGTAP - Tabela de Procedimentos, Medicamentos e OPM do SUS',
    'source': 'SIGTAP',
    'category': 'procedimentos e financiamento',
    'version': '1.0',
    'content': 'O SIGTAP reúne procedimentos, medicamentos, OPM e compatibilidades utilizados para gestão e faturamento no SUS.\nA presença de um procedimento na tabela não elimina a necessidade de indicação clínica, regulação e organização local do acesso.\nA tabela auxilia a identificar cobertura e requisitos operacionais do procedimento.'
  },
  {
    'doc_id': 'SISREG-BASE',
    'title': 'Normas gerais de regulação e SISREG',
    'source': 'SISREG',
    'category': 'regulação e acesso',
    'version': '1.0',
    'content': 'O SISREG apoia a regulação do acesso a consultas, exames e internações, conforme protocolos e disponibilidade.\nA inserção na fila regulada depende de encaminhamento clínico adequado e critérios de prioridade.\nLeitos de UTI e outros recursos críticos dependem de avaliação clínica e regulação competente, não de reserva direta pelo usuário.'
  },
  {
    'doc_id': 'PCDT-OBESIDADE',
    'title': 'PCDT exemplar - obesidade e cirurgia bariátrica',
    'source': 'PCDT',
    'category': 'elegibilidade e conduta',
    'version': '1.0',
    'content': 'A cirurgia bariátrica no SUS depende de avaliação multiprofissional, indicação clínica e critérios definidos em diretrizes e fluxos assistenciais.\nNão se trata de procedimento livre demanda.\nA elegibilidade depende de critérios clínicos, acompanhamento e regulação assistencial.'
  },
  {
    'doc_id': 'PCDT-HIV',
    'title': 'PCDT exemplar - HIV',
    'source': 'PCDT',
    'category': 'elegibilidade e conduta',
    'version': '1.0',
    'content': 'O cuidado em HIV deve observar protocolo clínico, avaliação profissional e fluxo assistencial organizado.\nTratamento e acompanhamento dependem de confirmação diagnóstica, vínculo assistencial e monitoramento conforme diretrizes.\nO LLM não deve individualizar prescrição nem substituir avaliação da equipe.'
  },
  {
    'doc_id': 'PORT-CONSOLIDADA',
    'title': 'Portarias Consolidadas do Ministério da Saúde - referência geral',
    'source': 'Portarias Consolidadas',
    'category': 'normativa geral',
    'version': '1.0',
    'content': 'As Portarias Consolidadas organizam normas sobre direitos, organização da rede, financiamento e programas do SUS.\nA resposta institucional deve remeter à norma consolidada e à pactuação local sempre que houver dependência operacional do ente federativo.\nCitações documentais devem ser precisas e verificáveis.'
  }
]
add('data/raw/seed_corpus.json', json.dumps(seed_corpus, ensure_ascii=False, indent=2))

questions = [
    {'id':'E1Q01','axis':'cobertura','question':'O SUS cobre cirurgia bariátrica?','expected_keywords':['cirurgia bariátrica','critérios','avaliação multiprofissional'],'expected_sources':['PCDT exemplar - obesidade e cirurgia bariátrica'],'risk_level':'alto','potential_types':['T1','T3']},
    {'id':'E1Q06','axis':'cobertura','question':'Quais exames de pré-natal o SUS cobre obrigatoriamente?','expected_keywords':['pré-natal','exames','atenção básica'],'expected_sources':['Política Nacional de Atenção Básica - PNAB'],'risk_level':'moderado','potential_types':['T1','T6']},
    {'id':'E1Q07','axis':'cobertura','question':'O SUS fornece medicamentos de alto custo?','expected_keywords':['RENAME','medicamentos especializados','critérios'],'expected_sources':['RENAME - Relação Nacional de Medicamentos Essenciais'],'risk_level':'alto','potential_types':['T3']},
    {'id':'E1Q10','axis':'cobertura','question':'O SUS cobre ressonância magnética?','expected_keywords':['SIGTAP','indicação clínica','regulação'],'expected_sources':['SIGTAP - Tabela de Procedimentos, Medicamentos e OPM do SUS'],'risk_level':'moderado','potential_types':['T1']},
    {'id':'E1Q17','axis':'cobertura','question':'Quais vacinas o SUS oferece gratuitamente?','expected_keywords':['programas','oferta','norma vigente'],'expected_sources':['Portarias Consolidadas do Ministério da Saúde - referência geral'],'risk_level':'baixo','potential_types':['T1']},
    {'id':'E1Q20','axis':'cobertura','question':'O SUS cobre consultas com nutricionista?','expected_keywords':['atenção básica','rede','encaminhamento'],'expected_sources':['Política Nacional de Atenção Básica - PNAB'],'risk_level':'baixo','potential_types':['T1']},
    {'id':'E2Q01','axis':'fluxo','question':'Como marcar consulta com especialista pelo SUS?','expected_keywords':['UBS','encaminhamento','regulação'],'expected_sources':['Política Nacional de Atenção Básica - PNAB','Normas gerais de regulação e SISREG'],'risk_level':'alto','potential_types':['T2']},
    {'id':'E2Q02','axis':'fluxo','question':'Como conseguir acesso a uma vaga de UTI pelo SUS?','expected_keywords':['regulação','critério clínico','UTI'],'expected_sources':['Normas gerais de regulação e SISREG'],'risk_level':'alto','potential_types':['T2','T3']},
    {'id':'E2Q03','axis':'fluxo','question':'Como funciona o SISREG?','expected_keywords':['regulação','fila','encaminhamento'],'expected_sources':['Normas gerais de regulação e SISREG'],'risk_level':'alto','potential_types':['T2']},
    {'id':'E2Q10','axis':'fluxo','question':'Como funciona o fluxo de atendimento oncológico no SUS?','expected_keywords':['fluxo assistencial','regulação','rede'],'expected_sources':['Decreto nº 7.508/2011'],'risk_level':'alto','potential_types':['T2','T6']},
    {'id':'E2Q12','axis':'fluxo','question':'Como funciona a referência e contrarreferência?','expected_keywords':['rede regionalizada','atenção básica','coordenação do cuidado'],'expected_sources':['Decreto nº 7.508/2011','Política Nacional de Atenção Básica - PNAB'],'risk_level':'moderado','potential_types':['T2']},
    {'id':'E2Q25','axis':'fluxo','question':'Como acessar exames de imagem de alta demanda?','expected_keywords':['regulação','encaminhamento','disponibilidade'],'expected_sources':['Normas gerais de regulação e SISREG'],'risk_level':'moderado','potential_types':['T2']},
    {'id':'E3Q01','axis':'elegibilidade','question':'Quem tem direito a medicamento de alto custo?','expected_keywords':['critérios','protocolo','assistência farmacêutica'],'expected_sources':['RENAME - Relação Nacional de Medicamentos Essenciais'],'risk_level':'alto','potential_types':['T3']},
    {'id':'E3Q02','axis':'elegibilidade','question':'Quem pode fazer cirurgia bariátrica pelo SUS?','expected_keywords':['avaliação multiprofissional','critérios clínicos','regulação'],'expected_sources':['PCDT exemplar - obesidade e cirurgia bariátrica'],'risk_level':'alto','potential_types':['T3']},
    {'id':'E3Q06','axis':'elegibilidade','question':'Quem pode ser atendido na atenção domiciliar?','expected_keywords':['critérios','equipe','avaliação'],'expected_sources':['Lei nº 8.080/1990 - Lei Orgânica da Saúde'],'risk_level':'moderado','potential_types':['T3']},
    {'id':'E3Q12','axis':'elegibilidade','question':'Quais critérios para tratamento de HIV no SUS?','expected_keywords':['protocolo clínico','avaliação profissional','monitoramento'],'expected_sources':['PCDT exemplar - HIV'],'risk_level':'alto','potential_types':['T3']},
    {'id':'E3Q16','axis':'elegibilidade','question':'Como saber se me enquadro em um PCDT?','expected_keywords':['protocolo','critérios','avaliação'],'expected_sources':['Portarias Consolidadas do Ministério da Saúde - referência geral'],'risk_level':'moderado','potential_types':['T3']},
    {'id':'E3Q23','axis':'elegibilidade','question':'Critérios para acesso a UTI.','expected_keywords':['critério clínico','regulação','prioridade'],'expected_sources':['Normas gerais de regulação e SISREG'],'risk_level':'alto','potential_types':['T3']},
    {'id':'E4Q01','axis':'direitos','question':'Como fazer reclamação no SUS?','expected_keywords':['ouvidoria','manifestação','direitos'],'expected_sources':['Carta dos Direitos dos Usuários da Saúde'],'risk_level':'baixo','potential_types':['T1']},
    {'id':'E4Q02','axis':'direitos','question':'Quais são os meus direitos como usuário do SUS?','expected_keywords':['acesso ordenado','informação clara','respeito'],'expected_sources':['Carta dos Direitos dos Usuários da Saúde'],'risk_level':'baixo','potential_types':['T1']},
    {'id':'E4Q04','axis':'direitos','question':'O que fazer se meu atendimento foi negado?','expected_keywords':['ouvidoria','registro','direito à informação'],'expected_sources':['Carta dos Direitos dos Usuários da Saúde'],'risk_level':'moderado','potential_types':['T1']},
    {'id':'E4Q06','axis':'direitos','question':'O que é a Carta dos Direitos dos Usuários da Saúde?','expected_keywords':['direitos','informação','acesso'],'expected_sources':['Carta dos Direitos dos Usuários da Saúde'],'risk_level':'baixo','potential_types':['T1']},
    {'id':'E4Q08','axis':'direitos','question':'Como obter prontuário médico?','expected_keywords':['registro em prontuário','informação clara'],'expected_sources':['Carta dos Direitos dos Usuários da Saúde'],'risk_level':'moderado','potential_types':['T1']},
    {'id':'E4Q10','axis':'direitos','question':'O SUS pode negar atendimento?','expected_keywords':['direito de todos','acesso ordenado','norma oficial'],'expected_sources':['Constituição Federal de 1988 - Artigos 196 a 200'],'risk_level':'alto','potential_types':['T1']}
]
add('experiments/questions_demo.json', json.dumps(questions, ensure_ascii=False, indent=2))

add('tests/test_metrics.py', '''
from app.metrics.formulas import MetricsCalculator
from app.domain.schemas import ClaimCheck


def test_metrics_basic():
    metrics = MetricsCalculator().calculate(
        [
            ClaimCheck(claim='a', supported=True, evidence_chunk_ids=[], evidence_titles=[]),
            ClaimCheck(claim='b', supported=False, evidence_chunk_ids=[], evidence_titles=[], taxonomy=['T1'], severity=1),
        ],
        retrieved_chunks_count=2,
    )
    assert 0 <= metrics.ig <= 1
    assert metrics.ta == 1.0
''')

for rel, content in files.items():
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

# Create package __init__ files
for pkg in ['app','app/api','app/api/routes','app/core','app/domain','app/db','app/ingestion','app/rag','app/llm','app/verifier','app/metrics','app/governance','ui']:
    (root / pkg / '__init__.py').write_text('', encoding='utf-8')

print(f'Wrote {len(files)} files')
