"""
Code Review Agent — CLI

Uso:
  python review.py C:\\Users\\alexc\\Desktop\\Matchgame

O agente vai:
  1. Carregar todos os arquivos de codigo
  2. Rodar 3 agentes especializados (Security, Quality, Performance)
  3. Gerar um relatorio consolidado em Markdown
  4. Salvar o relatorio na pasta reports/
"""

import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.graph.orchestrator import build_graph
from src.config import REPORTS_DIR

console = Console()


def main():
    console.print(Panel.fit(
        "[bold cyan]Code Review Agent[/bold cyan]\n"
        "Analise automatizada de seguranca, qualidade e performance",
        border_style="cyan",
    ))

    if len(sys.argv) < 2:
        console.print("[red]Uso: python review.py <caminho-do-repositorio>[/red]")
        console.print("Exemplo: python review.py C:\\Users\\alexc\\Desktop\\Matchgame")
        sys.exit(1)

    repo_path = sys.argv[1]

    if not Path(repo_path).exists():
        console.print(f"[red]Caminho nao encontrado: {repo_path}[/red]")
        sys.exit(1)

    # Estado inicial do grafo
    initial_state = {
        "repo_path": repo_path,
        "files": [],
        "total_files": 0,
        "total_lines": 0,
        "security_findings": [],
        "quality_findings": [],
        "performance_findings": [],
        "report": "",
        "score": 0,
        "status": "loading",
        "total_tokens": 0,
    }

    # Constroi e executa o grafo
    console.print(f"\nAnalisando: [green]{repo_path}[/green]\n")
    start_time = time.time()

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    elapsed = round(time.time() - start_time, 1)

    # Mostra resumo
    console.print("\n" + "=" * 60)

    score = final_state.get("score", 0)
    if score >= 90:
        score_style = "bold green"
    elif score >= 70:
        score_style = "bold yellow"
    elif score >= 50:
        score_style = "bold red"
    else:
        score_style = "bold red blink"

    console.print(Panel.fit(
        f"[{score_style}]NOTA FINAL: {score}/100[/{score_style}]",
        border_style="cyan",
    ))

    # Tabela de resumo
    summary = Table(title="Resumo da Analise")
    summary.add_column("Metrica", style="cyan")
    summary.add_column("Valor", justify="right", style="green")
    summary.add_row("Arquivos analisados", str(final_state["total_files"]))
    summary.add_row("Total de linhas", str(final_state["total_lines"]))
    summary.add_row("Issues de Seguranca", str(len(final_state.get("security_findings", []))))
    summary.add_row("Issues de Qualidade", str(len(final_state.get("quality_findings", []))))
    summary.add_row("Issues de Performance", str(len(final_state.get("performance_findings", []))))
    summary.add_row("Tokens Utilizados", f"{final_state.get('total_tokens', 0):,}")
    summary.add_row("Tempo total", f"{elapsed}s")
    console.print(summary)

    # Salva o relatorio Markdown e HTML
    report = final_state.get("report", "")
    if report:
        repo_name = Path(repo_path).name.lower()
        
        # Salva MD
        md_path = REPORTS_DIR / f"{repo_name}_review.md"
        md_path.write_text(report, encoding="utf-8")
        
        # Gera e salva HTML Elegante
        html_content = generate_html(final_state, elapsed)
        html_path = REPORTS_DIR / f"{repo_name}_review.html"
        html_path.write_text(html_content, encoding="utf-8")
        
        console.print(f"\nRelatorios salvos em:\n  [bold]{md_path}[/bold]\n  [bold]{html_path}[/bold]")

def generate_html(state: dict, elapsed: float) -> str:
    score = state.get("score", 0)
    tokens = state.get("total_tokens", 0)
    files = state.get("total_files", 0)
    lines = state.get("total_lines", 0)
    
    security = state.get("security_findings", [])
    quality = state.get("quality_findings", [])
    performance = state.get("performance_findings", [])
    
    criticos = len([f for f in security + quality + performance if f["severity"] == "CRITICO"])
    altos = len([f for f in security + quality + performance if f["severity"] == "ALTO"])
    medios = len([f for f in security + quality + performance if f["severity"] == "MEDIO"])
    baixos = len([f for f in security + quality + performance if f["severity"] == "BAIXO"])

    def render_issues(title, severity_filter):
        issues = [f for f in security + quality + performance if f["severity"] == severity_filter]
        if not issues:
            return ""
        html = f"<h2>Issues {title}</h2>\n"
        for i in issues:
            cat_color = "badge-security" if i["category"] == "security" else ("badge-quality" if i["category"] == "quality" else "badge-performance")
            sev_badge = f"badge-{severity_filter.lower()}"
            html += f'''
  <div class="issue">
    <div class="issue-header">
      <span class="badge {sev_badge}">{i["severity"]}</span>
      <span class="badge {cat_color}">{i["category"].upper()}</span>
    </div>
    <div class="issue-file">{i["file"]}</div>
    <div class="issue-desc">{i["description"]}</div>
    <div class="issue-suggestion"><strong>Sugestao:</strong> {i["suggestion"]}</div>
  </div>'''
        return html

    html_template = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Code Review Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Inter', sans-serif; background: #0d1117; color: #e6edf3; padding: 40px; line-height: 1.7; }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 8px; background: linear-gradient(135deg, #58a6ff, #bc8cff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  h2 {{ font-size: 1.3rem; font-weight: 600; color: #58a6ff; margin-top: 32px; margin-bottom: 12px; border-bottom: 1px solid #21262d; padding-bottom: 8px; }}
  .score-box {{ display: inline-block; background: {'linear-gradient(135deg, #da3633, #f85149)' if score < 70 else 'linear-gradient(135deg, #238636, #3fb950)'}; padding: 16px 32px; border-radius: 12px; font-size: 2rem; font-weight: 700; color: #fff; margin: 16px 0; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 16px 0; }}
  .stat {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }}
  .stat-value {{ font-size: 1.5rem; font-weight: 700; }}
  .stat-label {{ font-size: 0.8rem; color: #8b949e; margin-top: 4px; }}
  .stat-critico .stat-value {{ color: #f85149; }}
  .stat-alto .stat-value {{ color: #f0883e; }}
  .stat-medio .stat-value {{ color: #d29922; }}
  .stat-baixo .stat-value {{ color: #8b949e; }}
  .issue {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; margin: 10px 0; }}
  .issue-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .badge {{ padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; }}
  .badge-critico {{ background: #f8514922; color: #f85149; border: 1px solid #f8514944; }}
  .badge-alto {{ background: #f0883e22; color: #f0883e; border: 1px solid #f0883e44; }}
  .badge-medio {{ background: #d2992222; color: #d29922; border: 1px solid #d2992244; }}
  .badge-baixo {{ background: #8b949e22; color: #8b949e; border: 1px solid #8b949e44; }}
  .badge-security {{ background: #f8514911; color: #ff7b72; }}
  .badge-quality {{ background: #58a6ff11; color: #58a6ff; }}
  .badge-performance {{ background: #bc8cff11; color: #bc8cff; }}
  .issue-file {{ font-family: 'Courier New', monospace; font-size: 0.85rem; color: #58a6ff; }}
  .issue-desc {{ color: #e6edf3; margin: 6px 0; }}
  .issue-suggestion {{ background: #0d1117; border-left: 3px solid #238636; padding: 10px 14px; margin-top: 8px; border-radius: 4px; font-size: 0.9rem; color: #8b949e; }}
  .issue-suggestion strong {{ color: #3fb950; }}
  .meta {{ display: flex; gap: 24px; color: #8b949e; font-size: 0.85rem; margin: 16px 0; flex-wrap: wrap; }}
  .meta span {{ display: flex; align-items: center; gap: 6px; }}
  .token-badge {{ background: #21262d; padding: 4px 10px; border-radius: 12px; color: #c9d1d9; }}
</style>
</head>
<body>
<div class="container">
  <h1>Code Review Report</h1>
  
  <div class="meta">
    <span>{files} arquivos analisados</span>
    <span>{lines:,} linhas de codigo</span>
    <span>{elapsed}s de execucao</span>
    <span class="token-badge">{tokens:,} Tokens Gasto (LLM)</span>
  </div>

  <div class="score-box">NOTA: {score}/100</div>

  <div class="stats">
    <div class="stat stat-critico"><div class="stat-value">{criticos}</div><div class="stat-label">CRITICOS</div></div>
    <div class="stat stat-alto"><div class="stat-value">{altos}</div><div class="stat-label">ALTOS</div></div>
    <div class="stat stat-medio"><div class="stat-value">{medios}</div><div class="stat-label">MEDIOS</div></div>
    <div class="stat stat-baixo"><div class="stat-value">{baixos}</div><div class="stat-label">BAIXOS</div></div>
  </div>

  {render_issues('Criticos', 'CRITICO')}
  {render_issues('Altos', 'ALTO')}
  {render_issues('Medios', 'MEDIO')}
  {render_issues('Baixos', 'BAIXO')}

  <br>
  <p style="color:#484f58; font-size:0.8rem; margin-top:32px; border-top:1px solid #21262d; padding-top:16px;">
    Gerado automaticamente pelo Code Review Agent (LangGraph + GPT-4o-mini) | Desenvolvido por Alexsander Cristofari
  </p>
</div>
</body>
</html>'''
    return html_template


if __name__ == "__main__":
    main()
