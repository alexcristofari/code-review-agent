"""
Tools — Ferramentas que os agentes usam para interagir com o mundo real.

CONCEITO - TOOL USE:
  Um LLM sozinho so sabe gerar texto. Ele NAO consegue ler arquivos,
  acessar a internet, ou rodar codigo. Tools sao funcoes Python que
  dao esses "superpoderes" ao agente.

  Quando o agente precisa de informacao real, ele chama uma tool,
  recebe o resultado, e usa esse resultado pra raciocinar melhor.
"""

from pathlib import Path

from src.config import CODE_EXTENSIONS, IGNORED_DIRS


def load_repo_files(repo_path: str) -> list[dict]:
    """
    Carrega todos os arquivos de codigo de um repositorio.
    Retorna lista de {path, content, language, num_lines}.
    """
    path = Path(repo_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Caminho nao encontrado: {path}")

    ext_to_lang = {
        ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript",
        ".py": "python", ".prisma": "prisma",
        ".sql": "sql", ".json": "json",
        ".yaml": "yaml", ".yml": "yaml",
    }

    files = []
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in CODE_EXTENSIONS:
            continue
        # Ignora diretorios proibidos
        try:
            rel = file_path.relative_to(path)
            if any(part in IGNORED_DIRS for part in rel.parts):
                continue
        except ValueError:
            continue
        # Ignora lockfiles
        if file_path.name in {"pnpm-lock.yaml", "package-lock.json", "yarn.lock"}:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (PermissionError, OSError):
            continue

        if len(content.strip()) < 10:
            continue

        relative = str(file_path.relative_to(path)).replace("\\", "/")
        lang = ext_to_lang.get(file_path.suffix.lower(), "unknown")

        files.append({
            "path": relative,
            "content": content,
            "language": lang,
            "num_lines": content.count("\n") + 1,
        })

    return files


def detect_patterns(content: str, filepath: str) -> list[dict]:
    """
    Detecta anti-patterns comuns via analise estatica simples.
    Retorna lista de {pattern, line_number, line_content}.
    """
    import re
    patterns_found = []
    lines = content.split("\n")

    checks = [
        (r"console\.log\(", "console.log em codigo (remover em producao)"),
        (r"// ?TODO", "TODO pendente encontrado"),
        (r": any\b", "Uso de 'any' no TypeScript (evitar tipagem fraca)"),
        (r"password\s*=\s*['\"]", "Possivel senha hardcoded"),
        (r"api[_-]?key\s*=\s*['\"]", "Possivel API key hardcoded"),
        (r"eval\(", "Uso de eval() (risco de seguranca)"),
        (r"innerHTML\s*=", "Uso de innerHTML (risco de XSS)"),
        (r"\.catch\(\s*\)", "catch vazio (erros silenciados)"),
        (r"SELECT\s+\*\s+FROM", "SELECT * (evitar em producao)"),
    ]

    for i, line in enumerate(lines):
        for pattern, description in checks:
            if re.search(pattern, line, re.IGNORECASE):
                patterns_found.append({
                    "pattern": description,
                    "line_number": i + 1,
                    "line_content": line.strip()[:120],
                    "file": filepath,
                })

    return patterns_found


def analyze_dependencies(files: list[dict]) -> list[dict]:
    """
    Analisa package.json para encontrar problemas em dependencias.
    """
    import json
    issues = []

    for f in files:
        if f["path"].endswith("package.json") and "node_modules" not in f["path"]:
            try:
                pkg = json.loads(f["content"])
            except json.JSONDecodeError:
                continue

            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            # Verifica se tem dependencias sem versao fixa
            for name, version in deps.items():
                if version.startswith("*") or version == "latest":
                    issues.append({
                        "issue": f"Dependencia '{name}' sem versao fixa ({version})",
                        "file": f["path"],
                        "severity": "MEDIO",
                    })

    return issues
