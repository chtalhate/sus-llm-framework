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
