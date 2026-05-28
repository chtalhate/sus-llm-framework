# SUS LLM Framework
Framework experimental para mitigação de alucinações e conformidade normativa em modelos de linguagem (LLMs) aplicados ao Sistema Único de Saúde (SUS).
O projeto implementa um pipeline completo de recuperação normativa, geração assistida por contexto (RAG), verificação pós-geração e governança auditável para avaliação de confiabilidade em sistemas de IA generativa voltados ao domínio regulatório da saúde pública.

---

## Objetivo

Este projeto foi desenvolvido como prova de conceito da dissertação:

> **“Confiabilidade de LLMs no SUS: framework para mitigação de alucinações e conformidade normativa.”**

A pesquisa investiga mecanismos técnicos capazes de:

- reduzir alucinações em respostas geradas por LLMs;
- aumentar aderência normativa;
- melhorar rastreabilidade e auditabilidade;
- permitir avaliação quantitativa de confiabilidade.

---

## Arquitetura do Framework

```text
Usuário
   ↓
Streamlit UI
   ↓
FastAPI
   ├── M1 → Base normativa e recuperação
   ├── M2 → LLM + RAG
   ├── M3 → Verificação normativa pós-geração
   └── M4 → Governança e auditoria
```

---

## Módulos Implementados

### M1 — Base Normativa do SUS

- ingestão documental;
- chunking semântico;
- metadados normativos;
- indexação;
- recuperação contextual.

### M2 — LLM + RAG

Execução experimental em três condições:

- **C1** → LLM puro;
- **C2** → LLM + recuperação normativa;
- **C3** → LLM + RAG + verificação normativa.

### M3 — Verificação Pós-Geração

- extração de claims;
- validação de suporte documental;
- classificação taxonômica T1–T6;
- revisão heurística;
- análise de consistência.

### M4 — Governança e Auditoria

- trilha auditável;
- métricas de confiabilidade;
- persistência SQLite;
- exportação de relatórios;
- rastreamento de execução.

---

## Tecnologias Utilizadas

- Python 3.11
- FastAPI
- Streamlit
- SQLite
- Ollama
- Docker
- Docker Compose
- Qdrant (opcional)

---

## Execução Local

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/sus-llm-guardrails.git
cd sus-llm-guardrails
```

### 2. Configure o ambiente

```bash
cp .env.example .env
```

### 3. Suba os containers

```bash
docker compose up --build
```

### 4. Baixe o modelo local

```bash
docker exec -it sus-guardrails-ollama ollama pull qwen2.5:7b-instruct
```

### 5. Reconstrua o índice

```bash
curl -X POST http://localhost:8000/ingest/rebuild
```

---

## Interfaces

| Serviço | URL |
|---|---|
| API | http://localhost:8000/docs |
| UI | http://localhost:8501 |

---

## Métricas de Avaliação

O framework implementa métricas experimentais de confiabilidade:

| Métrica | Descrição |
|---|---|
| TA | Taxa de alucinação |
| AN | Aderência normativa |
| SM | Severidade média |
| F1 | Precisão e cobertura |
| IG | Índice global de governança |

---

## Dataset Experimental

O projeto inclui:

- corpus normativo inicial do SUS;
- benchmark demonstrativo com perguntas experimentais;
- pipeline de avaliação comparativa entre C1, C2 e C3.

---

## Estrutura do Projeto

```text
app/
  api/
  core/
  db/
  domain/
  governance/
  ingestion/
  llm/
  metrics/
  rag/
  verifier/

ui/
  streamlit_app.py

experiments/
  questions_demo.json
```

---

## Limitações

- O sistema possui finalidade acadêmica e experimental.
- Não substitui validação jurídica ou médica especializada.
- A verificação normativa é heurística.
- O desempenho depende da qualidade documental recuperada.

---

## Possíveis Evoluções

- fine-tuning especializado;
- integração com bases oficiais do Ministério da Saúde;
- avaliação com modelos multimodais;
- validação clínica;
- implementação de guardrails probabilísticos;
- explicabilidade baseada em grafos normativos.

---

## Licença

Este projeto está licenciado sob a licença MIT.

Consulte o arquivo `LICENSE` para mais informações.

---

## Autor

**Christiano Talhate**

Pesquisa em:
- Inteligência Artificial Aplicada
- Governança de IA
- LLMs Confiáveis
- Saúde Digital
- Sistemas Auditáveis

---

## Tags

```text
llm
rag
healthcare
sus
ai-governance
hallucination-detection
guardrails
fastapi
streamlit
ollama
compliance
artificial-intelligence
```

