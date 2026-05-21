import streamlit as st
import time
from pathlib import Path
from src.graph.orchestrator import build_graph

# Configuração da página
st.set_page_config(page_title="Code Review Agent", layout="wide")

# Estilos customizados (Monochromatic / Editorial / Minimalist)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=JetBrains+Mono:wght@400;700&display=swap');
    
    :root {
        --bg-color: #121212;
        --text-primary: #EAEAEA;
        --text-secondary: #888888;
        --border-color: #2A2A2A;
        --highlight: #FFFFFF;
    }
    
    /* Força paleta principal e remove fundos do Streamlit */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], .main {
        background-color: var(--bg-color) !important;
        font-family: 'Inter', sans-serif;
        color: var(--text-primary);
    }
    
    p, span, div, li {
        font-family: 'Inter', sans-serif;
    }
    .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0A0A0A !important;
        border-right: 1px solid var(--border-color) !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
    
    /* Tipografia e Markdown (Garante que o relatório fique em minúsculas e na fonte certa) */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 400 !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em !important;
        text-transform: lowercase !important;
    }
    
    /* Destaque sutil no texto (adicionando "cor" dentro da paleta monocromática) */
    .stMarkdown p, .stMarkdown li {
        color: var(--text-secondary) !important;
        line-height: 1.6 !important;
    }
    .stMarkdown strong {
        color: var(--highlight) !important;
        font-weight: 600 !important;
    }
    
    /* Código e Pre */
    code, pre, .stCodeBlock, .stCodeBlock code {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--text-primary) !important;
        background-color: #1A1A1A !important;
        border-radius: 2px !important;
    }
    
    /* Botões */
    .stButton > button {
        background-color: var(--text-primary) !important;
        border: none !important;
        border-radius: 2px !important;
        transition: opacity 0.2s;
        padding: 8px 16px !important;
    }
    .stButton > button p, .stButton > button div {
        color: var(--bg-color) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
    }
    .stButton > button:hover {
        opacity: 0.8 !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: transparent !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-bottom: 1px solid var(--border-color) !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        padding-left: 0 !important;
    }
    .stTextInput > div > div > input:focus {
        border-bottom: 1px solid var(--text-primary) !important;
        box-shadow: none !important;
    }

    /* Alertas e caixas de info (Remove completamente o azul) */
    [data-testid="stAlert"] > div, div[role="alert"] {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 0 !important;
    }
    [data-testid="stAlert"] * {
        color: var(--text-secondary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stAlert"] svg {
        display: none !important;
    }
    
    /* Progress Bar */
    .stProgress > div > div > div > div {
        background-color: var(--text-primary) !important;
        border-radius: 0 !important;
    }
    
    /* Métricas */
    .metric-card {
        background-color: transparent;
        padding: 24px 0;
        border-bottom: 1px solid var(--border-color);
        text-align: left;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 400;
        color: var(--highlight) !important;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        color: var(--text-secondary);
        font-size: 0.75rem;
        text-transform: lowercase;
        letter-spacing: 0.05em;
        font-family: 'Inter', sans-serif;
        margin-top: 8px;
    }
    
    /* Badges de Severidade */
    .severity-CRITICO { color: var(--bg-color) !important; background-color: var(--text-primary) !important; font-family: 'JetBrains Mono', monospace; font-weight: 700; padding: 2px 8px; font-size: 0.75rem; text-transform: lowercase; }
    .severity-ALTO { color: var(--text-primary) !important; border: 1px solid var(--text-primary); font-family: 'JetBrains Mono', monospace; padding: 2px 8px; font-size: 0.75rem; text-transform: lowercase; }
    .severity-MEDIO { color: var(--text-secondary) !important; border: 1px solid var(--text-secondary); font-family: 'JetBrains Mono', monospace; padding: 2px 8px; font-size: 0.75rem; text-transform: lowercase; }
    .severity-BAIXO { color: #555555 !important; border: 1px dashed #555555; font-family: 'JetBrains Mono', monospace; padding: 2px 8px; font-size: 0.75rem; text-transform: lowercase; }
    
    /* Expanders (Remove fundo escuro Streamlit) */
    [data-testid="stExpander"] > details {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid var(--border-color) !important;
        border-radius: 0 !important;
    }
    [data-testid="stExpander"] summary {
        background-color: transparent !important;
        font-family: 'Inter', sans-serif !important;
        color: var(--highlight) !important;
    }
    [data-testid="stExpander"] summary:hover {
        color: var(--highlight) !important;
    }
    [data-testid="stExpanderDetails"] {
        background-color: transparent !important;
        color: var(--text-secondary) !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stExpanderDetails"] strong {
        color: var(--highlight) !important;
        font-weight: 600 !important;
    }
    
    /* Abas Minimalistas */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
        border-bottom: 1px solid var(--border-color) !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        color: var(--text-secondary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        text-transform: lowercase;
        border: none !important;
        font-size: 0.85rem !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--highlight) !important;
        border-bottom: 2px solid var(--highlight) !important;
    }
    .stTabs [aria-selected="true"] div {
        color: var(--highlight) !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>[code review]</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888888; font-family: \"JetBrains Mono\", monospace; font-size: 0.8rem; margin-top: -10px;'>MAY 2026 - AUTOMATED AUDIT</p>", unsafe_allow_html=True)

# Input do diretório
st.sidebar.markdown("<p style='color: #888888; font-family: \"JetBrains Mono\", monospace; font-size: 0.8rem;'>config</p>", unsafe_allow_html=True)
repo_path = st.sidebar.text_input("caminho_repositorio:", value=r"C:\Users\alexc\Desktop\Matchgame")

if st.sidebar.button("iniciar audit", type="primary"):
    if not Path(repo_path).exists():
        st.error("Caminho não encontrado. Verifique o caminho inserido.")
    else:
        st.session_state["review_results"] = None
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Construindo grafo LangGraph...")
        graph = build_graph()
        
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
        
        st.info("Iniciando a análise dos agentes. Isso pode levar alguns minutos dependendo do tamanho do projeto.")
        
        start_time = time.time()
        
        with st.spinner("Agentes em ação..."):
            final_state = graph.invoke(initial_state)
            
        elapsed = round(time.time() - start_time, 1)
        progress_bar.progress(100)
        status_text.text(f"Análise concluída em {elapsed}s")
        
        st.session_state["review_results"] = final_state
        st.session_state["elapsed"] = elapsed

# Mostrar resultados se existirem
if st.session_state.get("review_results"):
    state = st.session_state["review_results"]
    elapsed = st.session_state["elapsed"]
    
    st.markdown("---")
    
    # KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{state["score"]}/100</div><div class="metric-label">nota final</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{state["total_files"]}</div><div class="metric-label">Arquivos</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{state["total_lines"]:,}</div><div class="metric-label">Linhas Analisadas</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{state["total_tokens"]:,}</div><div class="metric-label">Tokens LLM</div></div>', unsafe_allow_html=True)
    with col5:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{elapsed}s</div><div class="metric-label">Tempo Execução</div></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Abas por categoria
    tab_sec, tab_qual, tab_perf, tab_rep = st.tabs(["seguranca", "qualidade", "performance", "relatorio"])
    
    def render_findings(findings, empty_msg):
        if not findings:
            st.success(empty_msg)
            return
            
        for f in findings:
            with st.expander(f"[{f['severity']}] {f['file']}"):
                st.markdown(f"**Severidade:** <span class='severity-{f['severity']}'>{f['severity']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Problema:** {f['description']}")
                st.markdown(f"**Sugestão:** `{f['suggestion']}`")
    
    with tab_sec:
        render_findings(state.get("security_findings", []), "Nenhum problema de segurança encontrado.")
        
    with tab_qual:
        render_findings(state.get("quality_findings", []), "Nenhum problema de qualidade encontrado.")
        
    with tab_perf:
        render_findings(state.get("performance_findings", []), "Nenhum problema de performance encontrado.")
        
    with tab_rep:
        st.markdown(state.get("report", ""))
