from app.core.constants import SYSTEM_PROMPT


def build_prompt(question: str, context: list[str], condition: str) -> str:
    sections = [SYSTEM_PROMPT, f'Condição experimental: {condition}', f'Pergunta: {question}']
    if context:
        sections.append('Contexto normativo recuperado:')
        for idx, chunk in enumerate(context, start=1):
            sections.append(f'[{idx}] {chunk}')
    sections.append(
        'Responda em tópicos curtos com: resposta objetiva, justificativa normativa, '
        'limitações/condicionantes e orientação institucional final.'
    )
    return "\n\n".join(sections)
