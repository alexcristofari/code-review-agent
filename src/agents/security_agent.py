"""
Security Agent — Analisa vulnerabilidades de seguranca no codigo.

Busca: SQL injection, XSS, secrets hardcoded, autenticacao fraca,
headers HTTP inseguros, falta de rate limiting, CORS mal configurado.
"""

from langchain_openai import ChatOpenAI
from src.config import OPENAI_API_KEY, LLM_MODEL

SECURITY_PROMPT = """Voce e um especialista em seguranca de aplicacoes web (AppSec).
Analise os trechos de codigo abaixo e identifique vulnerabilidades de seguranca.

REGRAS:
1. Foque APENAS em problemas reais e verificaveis no codigo fornecido.
2. NAO invente problemas que nao existem no codigo.
3. Classifique cada problema por severidade: CRITICO, ALTO, MEDIO, BAIXO.
4. Para cada problema, sugira uma correcao concreta com exemplo de codigo.
5. Se nao encontrar problemas, diga explicitamente "Nenhum problema de seguranca encontrado".

CATEGORIAS A VERIFICAR:
- Injecao (SQL, NoSQL, Command Injection)
- Cross-Site Scripting (XSS)
- Secrets/credenciais hardcoded
- Autenticacao e autorizacao falha
- Criptografia fraca ou ausente
- Headers HTTP inseguros
- Falta de validacao de input
- Dependencias vulneraveis

Responda em formato JSON com a seguinte estrutura:
{
  "findings": [
    {
      "severity": "CRITICO|ALTO|MEDIO|BAIXO",
      "file": "caminho/do/arquivo.ts",
      "line": "trecho da linha relevante",
      "description": "descricao clara do problema",
      "suggestion": "como corrigir com exemplo"
    }
  ]
}

Se nao houver problemas, retorne: {"findings": []}
"""


def run_security_review(files: list[dict], pattern_findings: list[dict]) -> tuple[list[dict], int]:
    """Executa a analise de seguranca nos arquivos. Retorna (findings, tokens_gastos)."""
    llm = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.1,
    )

    # Seleciona arquivos mais relevantes pra seguranca
    security_relevant = [
        f for f in files
        if any(kw in f["path"].lower() for kw in [
            "auth", "login", "middleware", "password", "token",
            "session", "crypto", "security", "cors", "route",
            "controller", "api", "server", "prisma", ".env",
        ])
    ]

    # Se nao encontrou arquivos especificos, pega os primeiros 15
    if not security_relevant:
        security_relevant = files[:15]
    else:
        security_relevant = security_relevant[:20]

    # Monta o contexto com o codigo
    code_context = ""
    for f in security_relevant:
        # Trunca arquivos grandes
        content = f["content"][:4000]
        code_context += f"\n--- {f['path']} ({f['language']}) ---\n{content}\n"

    # Adiciona patterns encontrados pela analise estatica
    if pattern_findings:
        security_patterns = [
            p for p in pattern_findings
            if any(kw in p["pattern"].lower() for kw in ["senha", "key", "eval", "innerHTML", "password", "api"])
        ]
        if security_patterns:
            code_context += "\n\n--- ALERTAS DA ANALISE ESTATICA ---\n"
            for p in security_patterns[:10]:
                code_context += f"  [{p['file']}:{p['line_number']}] {p['pattern']}: {p['line_content']}\n"

    messages = [
        {"role": "system", "content": SECURITY_PROMPT},
        {"role": "user", "content": f"Analise o seguinte codigo:\n\n{code_context}"},
    ]

    response = llm.invoke(messages)
    
    tokens = response.response_metadata.get("token_usage", {}).get("total_tokens", 0)

    # Parseia a resposta JSON
    import json
    try:
        content = response.content.strip()
        # Remove markdown code fences se existirem
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        data = json.loads(content)
        findings = data.get("findings", [])
    except (json.JSONDecodeError, AttributeError):
        findings = []

    # Converte para formato padrao
    result = []
    for f in findings:
        result.append({
            "severity": f.get("severity", "MEDIO"),
            "category": "security",
            "file": f.get("file", "desconhecido"),
            "line": f.get("line", ""),
            "description": f.get("description", ""),
            "suggestion": f.get("suggestion", ""),
        })

    return result, tokens
