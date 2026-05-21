"""
Reporter Agent — Consolida os findings de todos os agentes em um relatorio Markdown.

Este e o ultimo no do grafo. Ele recebe todos os findings acumulados
no estado e gera um relatorio profissional, classificado por severidade,
com uma nota geral de 0 a 100.
"""

from langchain_openai import ChatOpenAI
from src.config import OPENAI_API_KEY, LLM_MODEL


REPORTER_PROMPT = """Voce e um Tech Lead gerando um relatorio de code review.

Com base nos findings abaixo, gere um relatorio PROFISSIONAL em Markdown seguindo EXATAMENTE este formato:

# Code Review Report

## Resumo Executivo
[2-3 frases resumindo o estado geral do codigo]

**Nota Geral: [X]/100**

## Estatisticas
- Total de issues: [N]
- Criticos: [N] | Altos: [N] | Medios: [N] | Baixos: [N]

## Issues Criticos e Altos
[Liste cada issue CRITICO e ALTO com detalhes, arquivo e sugestao de correcao]

## Issues Medios
[Liste issues MEDIOS de forma mais resumida]

## Issues Baixos
[Liste issues BAIXOS de forma breve]

## Recomendacoes Prioritarias
[Top 3-5 acoes que devem ser tomadas primeiro]

REGRAS PARA A NOTA:
- 90-100: Codigo excelente, poucos ou nenhum problema
- 70-89: Bom, mas com melhorias necessarias
- 50-69: Precisa de atencao significativa
- 0-49: Problemas criticos que precisam de correcao imediata

Responda APENAS com o Markdown do relatorio. Nada mais.
"""


def generate_report(
    security_findings: list[dict],
    quality_findings: list[dict],
    performance_findings: list[dict],
    total_files: int,
    total_lines: int,
    repo_path: str,
) -> tuple[str, int, int]:
    """
    Gera o relatorio final consolidado.
    Retorna (relatorio_markdown, nota_0_a_100, tokens_gastos).
    """
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.2,
    )

    # Formata todos os findings para o prompt
    all_findings = ""

    if security_findings:
        all_findings += "\n## SEGURANCA\n"
        for f in security_findings:
            all_findings += f"- [{f['severity']}] {f['file']}: {f['description']}\n  Sugestao: {f['suggestion']}\n"

    if quality_findings:
        all_findings += "\n## QUALIDADE\n"
        for f in quality_findings:
            all_findings += f"- [{f['severity']}] {f['file']}: {f['description']}\n  Sugestao: {f['suggestion']}\n"

    if performance_findings:
        all_findings += "\n## PERFORMANCE\n"
        for f in performance_findings:
            all_findings += f"- [{f['severity']}] {f['file']}: {f['description']}\n  Sugestao: {f['suggestion']}\n"

    if not all_findings:
        all_findings = "Nenhum problema encontrado nos agentes de analise."

    context = (
        f"Repositorio: {repo_path}\n"
        f"Arquivos analisados: {total_files}\n"
        f"Total de linhas: {total_lines}\n"
        f"\n{all_findings}"
    )

    messages = [
        {"role": "system", "content": REPORTER_PROMPT},
        {"role": "user", "content": context},
    ]

    response = llm.invoke(messages)
    
    tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)
    report = response.content or "Erro ao gerar relatorio."

    # Tenta extrair a nota do relatorio
    score = 70  # default
    import re
    match = re.search(r"Nota Geral:\s*(\d+)", report)
    if match:
        score = min(100, max(0, int(match.group(1))))

    return report, score, tokens
