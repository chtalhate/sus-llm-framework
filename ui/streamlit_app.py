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
