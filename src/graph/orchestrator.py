"""
Orchestrator — O grafo LangGraph que conecta todos os agentes.

CONCEITO CENTRAL:
  Este arquivo define o "fluxo de trabalho" do agente. Cada funcao
  (load_files_node, security_node, etc.) e um "no" no grafo.
  O LangGraph executa os nos na ordem definida pelas "edges" (arestas).

  Fluxo:
    START -> load_files -> security -> quality -> performance -> reporter -> END

  Cada no recebe o estado atual, faz seu trabalho, e retorna as
  atualizacoes para o estado. O LangGraph cuida de merge automatico.
"""

from langgraph.graph import StateGraph, START, END
from rich.console import Console

from src.graph.state import ReviewState
from src.tools.tools import load_repo_files, detect_patterns, analyze_dependencies
from src.agents.security_agent import run_security_review
from src.agents.quality_agent import run_quality_review
from src.agents.performance_agent import run_performance_review
from src.agents.reporter_agent import generate_report

console = Console()


# =============================================
# NOS DO GRAFO (cada funcao = um passo)
# =============================================

def load_files_node(state: ReviewState) -> dict:
    """
    Primeiro no: carrega todos os arquivos do repositorio.
    """
    console.print("[bold cyan][Orchestrator][/] Carregando arquivos...")

    files = load_repo_files(state["repo_path"])
    total_lines = sum(f["num_lines"] for f in files)

    console.print(f"[bold cyan][Orchestrator][/] {len(files)} arquivos carregados ({total_lines} linhas)")

    return {
        "files": files,
        "total_files": len(files),
        "total_lines": total_lines,
        "status": "analyzing",
    }


def security_node(state: ReviewState) -> dict:
    """
    Segundo no: agente de seguranca analisa o codigo.
    """
    console.print("\n[bold red][Security Agent][/] Analisando vulnerabilidades...")

    # Roda analise estatica primeiro (patterns via regex)
    all_patterns = []
    for f in state["files"]:
        patterns = detect_patterns(f["content"], f["path"])
        all_patterns.extend(patterns)

    if all_patterns:
        console.print(f"[red]  Analise estatica: {len(all_patterns)} alertas detectados[/]")

    # Roda analise com LLM
    findings, tokens = run_security_review(state["files"], all_patterns)

    for f in findings:
        severity_color = {"CRITICO": "red bold", "ALTO": "red", "MEDIO": "yellow", "BAIXO": "dim"}.get(f["severity"], "white")
        console.print(f"  [{severity_color}][{f['severity']}][/] {f['file']}: {f['description']}")

    if not findings:
        console.print("  [green]Nenhum problema de seguranca encontrado[/]")

    return {"security_findings": findings, "total_tokens": tokens}


def quality_node(state: ReviewState) -> dict:
    """
    Terceiro no: agente de qualidade analisa boas praticas.
    """
    console.print("\n[bold blue][Quality Agent][/] Analisando qualidade do codigo...")

    all_patterns = []
    for f in state["files"]:
        patterns = detect_patterns(f["content"], f["path"])
        all_patterns.extend(patterns)

    findings, tokens = run_quality_review(state["files"], all_patterns)

    for f in findings:
        severity_color = {"CRITICO": "red bold", "ALTO": "red", "MEDIO": "yellow", "BAIXO": "dim"}.get(f["severity"], "white")
        console.print(f"  [{severity_color}][{f['severity']}][/] {f['file']}: {f['description']}")

    if not findings:
        console.print("  [green]Nenhum problema de qualidade encontrado[/]")

    return {"quality_findings": findings, "total_tokens": tokens}


def performance_node(state: ReviewState) -> dict:
    """
    Quarto no: agente de performance analisa otimizacoes.
    """
    console.print("\n[bold magenta][Performance Agent][/] Analisando performance...")

    findings, tokens = run_performance_review(state["files"])

    for f in findings:
        severity_color = {"CRITICO": "red bold", "ALTO": "red", "MEDIO": "yellow", "BAIXO": "dim"}.get(f["severity"], "white")
        console.print(f"  [{severity_color}][{f['severity']}][/] {f['file']}: {f['description']}")

    if not findings:
        console.print("  [green]Nenhum problema de performance encontrado[/]")

    return {"performance_findings": findings, "total_tokens": tokens}


def reporter_node(state: ReviewState) -> dict:
    """
    Quinto e ultimo no: gera o relatorio consolidado.
    """
    console.print("\n[bold green][Reporter Agent][/] Gerando relatorio consolidado...")

    report, score, tokens = generate_report(
        security_findings=state.get("security_findings", []),
        quality_findings=state.get("quality_findings", []),
        performance_findings=state.get("performance_findings", []),
        total_files=state["total_files"],
        total_lines=state["total_lines"],
        repo_path=state["repo_path"],
    )

    return {
        "report": report,
        "score": score,
        "status": "done",
        "total_tokens": tokens,
    }


# =============================================
# MONTAGEM DO GRAFO
# =============================================

def build_graph():
    """
    Constroi e compila o grafo LangGraph.

    CONCEITO - StateGraph:
      StateGraph e o "canvas" onde desenhamos o fluxo de trabalho.
      Adicionamos "nos" (funcoes) e "edges" (conexoes entre elas).
      Depois compilamos com .compile() pra obter um grafo executavel.

      START e END sao nos especiais do LangGraph:
        START = ponto de entrada
        END = ponto de saida (agente terminou)
    """
    graph = StateGraph(ReviewState)

    # Adiciona os nos
    graph.add_node("load_files", load_files_node)
    graph.add_node("security", security_node)
    graph.add_node("quality", quality_node)
    graph.add_node("performance", performance_node)
    graph.add_node("reporter", reporter_node)

    # Conecta os nos (define a ordem de execucao)
    graph.add_edge(START, "load_files")
    graph.add_edge("load_files", "security")
    graph.add_edge("security", "quality")
    graph.add_edge("quality", "performance")
    graph.add_edge("performance", "reporter")
    graph.add_edge("reporter", END)

    # Compila o grafo
    return graph.compile()
