"""
Performance Agent — Analisa problemas de performance no codigo.

Busca: queries N+1, loops desnecessarios, memory leaks,
falta de caching, imports pesados, bundles grandes.
"""

from langchain_openai import ChatOpenAI
from src.config import OPENAI_API_KEY, LLM_MODEL

PERFORMANCE_PROMPT = """Voce e um engenheiro de performance especialista em otimizacao de aplicacoes web.
Analise os trechos de codigo abaixo e identifique problemas de performance.

REGRAS:
1. Foque em problemas que causam lentidao REAL (nao micro-otimizacoes).
2. Classifique por severidade: CRITICO, ALTO, MEDIO, BAIXO.
3. Sugira correcoes concretas com exemplos.

CATEGORIAS:
- Query N+1 (Prisma/ORM buscando em loop)
- Loops desnecessarios ou ineficientes
- Falta de paginacao em listagens
- Memory leaks (event listeners nao removidos, closures)
- Falta de caching para dados frequentes
- Imports desnecessarios ou pesados
- Operacoes sincronas que deveriam ser async
- Re-renders desnecessarios (React)

Responda em formato JSON:
{
  "findings": [
    {
      "severity": "CRITICO|ALTO|MEDIO|BAIXO",
      "file": "caminho/do/arquivo.ts",
      "line": "trecho relevante",
      "description": "descricao do problema",
      "suggestion": "como corrigir"
    }
  ]
}

Se nao houver problemas, retorne: {"findings": []}
"""


def run_performance_review(files: list[dict]) -> tuple[list[dict], int]:
    """Executa a analise de performance nos arquivos. Retorna (findings, tokens_gastos)."""
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.1,
    )

    # Foca em arquivos que provavelmente tem logica pesada
    perf_relevant = [
        f for f in files
        if any(kw in f["path"].lower() for kw in [
            "controller", "service", "route", "prisma",
            "query", "fetch", "api", "hook", "component",
            "page", "middleware", "sync",
        ])
        and f["num_lines"] > 10
    ]

    if not perf_relevant:
        perf_relevant = [f for f in files if f["num_lines"] > 20]

    perf_relevant = perf_relevant[:15]

    code_context = ""
    for f in perf_relevant:
        content = f["content"][:4000]
        code_context += f"\n--- {f['path']} ({f['num_lines']} linhas) ---\n{content}\n"

    messages = [
        {"role": "system", "content": PERFORMANCE_PROMPT},
        {"role": "user", "content": f"Analise o seguinte codigo:\n\n{code_context}"},
    ]

    response = llm.invoke(messages)

    tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

    import json
    try:
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        data = json.loads(content)
        findings = data.get("findings", [])
    except (json.JSONDecodeError, AttributeError):
        findings = []

    result = []
    for f in findings:
        result.append({
            "severity": f.get("severity", "MEDIO"),
            "category": "performance",
            "file": f.get("file", "desconhecido"),
            "line": f.get("line", ""),
            "description": f.get("description", ""),
            "suggestion": f.get("suggestion", ""),
        })

    return result, tokens
