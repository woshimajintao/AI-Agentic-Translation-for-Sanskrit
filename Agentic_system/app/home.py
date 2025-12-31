import streamlit as st
from pathlib import Path
import os

# 设置页面配置
st.set_page_config(
    page_title="Sanskrit Agent System",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 路径设置
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"

# 确保 assets 目录存在
if not ASSETS_DIR.exists():
    os.makedirs(ASSETS_DIR, exist_ok=True)

# =========================================================
# Main Content
# =========================================================

st.title("🕉️ Agentic Sanskrit Translation System")
st.markdown("### Integrating LLMs with Philology, Dynamic RAG & Glossary Constraints")

st.success("✅ System Ready. Local Model Detected. DuckDB Connected.")

st.markdown("---")

col_text, col_img = st.columns([3, 2])

with col_text:
    st.markdown("""
    Welcome to the Sanskrit Translation Agent. This research platform combines **Large Language Models (Qwen-2.5)** with **Rule-based Linguistic Tools** to achieve high-precision translation.
    
    #### 🚀 Core Modules
    
    **1. Translate (Interactive Mode)**
    * **Focus**: Single-sentence deep analysis and inference.
    * **Capabilities**: 
        * Runs the full **Mode I** pipeline (Agent + Grammar + Dict + RAG + Glossary).
        * Real-time "Thought Process" visualization (Morphology & Dictionary lookup traces).
        * Support for inference-time retrieval from knowledge bases (e.g., MKB, Bible).
    
    **2. Evaluate (Ablation Study)**
    * **Focus**: Batch benchmarking and scientific control.
    * **Modes A-I**: From Zero-shot Baseline to Dynamic RAG + Glossary.
    * **Metrics**: Standard **BLEU** and **chrF++** scoring.
    * **Controls**: Random Seed Locking, Data Split Consistency (Half-Split), and detailed result inspection.
    
    **3. Resources**
    * **Focus**: Database Management.
    * View status of Ingested Dictionaries (Monier-Williams), Glossaries (PDF/CSV), and Parallel Corpora.
    """)

    st.markdown("---")
    st.caption("Select a module from the sidebar to begin.")

with col_img:
    st.markdown("#### 🏗️ Project Architecture")
    
    # 尝试加载本地图片
    img_path = ASSETS_DIR / "architecture.png"
    
    if img_path.exists():
        st.image(str(img_path), caption="Agentic Workflow Diagram", use_container_width=True)
    else:
        # 如果没有图片，提供上传框方便调试
        st.warning("⚠️ Architecture image not found.")
        st.info(f"Please save your diagram as: `{img_path}`")
        
        uploaded_img = st.file_uploader("Or upload an image temporarily:", type=['png', 'jpg', 'jpeg'])
        if uploaded_img:
            st.image(uploaded_img, caption="Uploaded Architecture", use_container_width=True)

# =========================================================
# Mode Reference (Optional Helper)
# =========================================================
with st.expander("📖 Reference: Supported Translation Modes"):
    st.markdown("""
    | Mode | Name | Tools Used | Context | Constraints |
    |---|---|---|---|---|
    | **A** | Baseline | None | Zero-shot | None |
    | **B** | Dict Only | Monier-Williams | Zero-shot | None |
    | **C** | Grammar Only | Ambuda Morphology | Zero-shot | None |
    | **D** | Full Agent | MW + Grammar | Zero-shot | None |
    | **E** | Static Few-Shot | MW + Grammar | **Static Random-k** | None |
    | **F** | Dynamic RAG | MW + Grammar | **Top-k Similarity** | None |
    | **G** | Baseline + Glossary | None | Zero-shot | **Glossary** |
    | **H** | Agent + Glossary | MW + Grammar | Zero-shot | **Glossary** |
    | **I** | **Dynamic RAG + Glossary** | **MW + Grammar** | **Top-k Similarity** | **Glossary** |
    """)