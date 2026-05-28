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
