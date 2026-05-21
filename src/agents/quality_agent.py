"""
Quality Agent — Analisa boas praticas e clean code.

Busca: funcoes muito longas, codigo duplicado, nomes ruins,
violacoes de SRP/DRY, tratamento de erros ausente.
"""

from langchain_openai import ChatOpenAI
from src.config import OPENAI_API_KEY, LLM_MODEL

QUALITY_PROMPT = """Voce e um engenheiro de software senior especialista em Clean Code e SOLID.
Analise os trechos de codigo abaixo e identifique problemas de qualidade.

REGRAS:
1. Foque em problemas que impactam manutenibilidade e legibilidade.
2. NAO reporte questoes de estilo triviais (tabs vs spaces, ponto-e-virgula).
3. Classifique por severidade: CRITICO, ALTO, MEDIO, BAIXO.
4. Sugira correcoes concretas.

CATEGORIAS:
- Funcoes com mais de 50 linhas (Single Responsibility Principle)
- Codigo duplicado (DRY)
- Tratamento de erros ausente ou generico
- Nomes de variaveis/funcoes pouco descritivos
- Acoplamento excessivo entre modulos
- Falta de tipagem (uso excessivo de 'any')
- Complexidade ciclomatica alta (muitos ifs aninhados)

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


def run_quality_review(files: list[dict], pattern_findings: list[dict]) -> tuple[list[dict], int]:
    """Executa a analise de qualidade nos arquivos. Retorna (findings, tokens_gastos)."""
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.1,
    )

    # Seleciona os arquivos de codigo mais substanciais
    code_files = [
        f for f in files
        if f["language"] in ("typescript", "javascript", "python")
        and f["num_lines"] > 10
    ]
    # Ordena por tamanho (maiores primeiro — mais chance de ter problemas)
    code_files.sort(key=lambda x: x["num_lines"], reverse=True)
    code_files = code_files[:15]

    code_context = ""
    for f in code_files:
        content = f["content"][:4000]
        code_context += f"\n--- {f['path']} ({f['num_lines']} linhas) ---\n{content}\n"

    # Adiciona patterns encontrados
    if pattern_findings:
        quality_patterns = [
            p for p in pattern_findings
            if any(kw in p["pattern"].lower() for kw in ["todo", "any", "console", "catch"])
        ]
        if quality_patterns:
            code_context += "\n\n--- ALERTAS DA ANALISE ESTATICA ---\n"
            for p in quality_patterns[:15]:
                code_context += f"  [{p['file']}:{p['line_number']}] {p['pattern']}: {p['line_content']}\n"

    messages = [
        {"role": "system", "content": QUALITY_PROMPT},
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
            "category": "quality",
            "file": f.get("file", "desconhecido"),
            "line": f.get("line", ""),
            "description": f.get("description", ""),
            "suggestion": f.get("suggestion", ""),
        })

    return result, tokens
