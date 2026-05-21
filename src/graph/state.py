"""
State — O estado compartilhado entre todos os agentes.

CONCEITO CENTRAL DO LANGGRAPH:
  Diferente de um script normal, onde cada funcao recebe seus proprios
  parametros, num grafo de agentes TODOS os nos compartilham o mesmo
  "estado". Cada agente le, modifica e passa adiante.

  E como uma ficha de paciente num hospital: o enfermeiro anota a
  pressao, o medico anota o diagnostico, o farmaceutico anota o
  remedio — todos escrevem na mesma ficha.
"""

from typing import TypedDict, Annotated
import operator


class Finding(TypedDict):
    """Um problema encontrado por um agente."""
    severity: str        # CRITICO, ALTO, MEDIO, BAIXO
    category: str        # security, quality, performance
    file: str            # arquivo onde o problema esta
    line: str            # linha ou trecho relevante
    description: str     # descricao do problema
    suggestion: str      # sugestao de correcao


class ReviewState(TypedDict):
    """
    Estado compartilhado do grafo.

    Annotated[list, operator.add] significa:
      Quando um agente retorna uma lista de findings, ela e CONCATENADA
      com a lista existente (nao substituida). Isso permite que cada
      agente adicione seus proprios findings sem apagar os dos outros.
    """
    repo_path: str
    files: list[dict]                                    # arquivos carregados {path, content, language}
    total_files: int
    total_lines: int
    security_findings: Annotated[list[Finding], operator.add]
    quality_findings: Annotated[list[Finding], operator.add]
    performance_findings: Annotated[list[Finding], operator.add]
    report: str                                          # relatorio final em Markdown
    score: int                                           # nota 0-100
    status: str                                          # loading, analyzing, reporting, done
    total_tokens: Annotated[int, operator.add]           # soma dos tokens gastos no LLM
