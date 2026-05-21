"""
Configuracoes centralizadas do Code Review Agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Extensoes de codigo que o agente sabe analisar
CODE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".py",
    ".prisma", ".sql", ".json", ".yaml", ".yml",
}

# Diretorios ignorados
IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", "dist",
    "build", ".next", ".venv", "venv", "coverage",
}
