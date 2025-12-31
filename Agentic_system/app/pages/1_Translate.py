import streamlit as st
import sys
from pathlib import Path
import json

# 路径设置
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.llm.qwen_local import QwenLocalLLM
from src.agent.orchestrator import SanskritAgent
from src.db.duckdb_conn import get_db_connection

@st.cache_resource
def load_engine():
    llm = QwenLocalLLM()
    agent = SanskritAgent(llm)
    return agent

# RAG 检索函数 (用于推理模式)
def get_inference_rag_context(src_text: str, dataset_scope: str = "All", k: int = 3) -> str:
    """
    在推理阶段 (Translate Mode)，从数据库中检索与输入最相似的例句。
    """
    con = get_db_connection()
    try:
        # 如果 scope 是 All，则查所有表；否则查特定 dataset
        scope_clause = "1=1" if dataset_scope == "All" else f"dataset_name = '{dataset_scope}'"
        
        query = f"""
            SELECT src_text, tgt_text, jaccard(src_text, ?) as similarity
            FROM dataset_items
            WHERE {scope_clause}
            ORDER BY similarity DESC
            LIMIT ?
        """
        results = con.execute(query, [src_text, k]).fetchall()
        
        if not results: return None
        
        # 过滤低相似度
        valid_examples = [r for r in results if r[2] > 0.1]
        if not valid_examples: return None
            
        builder = []
        for row in valid_examples:
            # 清洗换行
            s_clean = row[0].replace('\n', ' ').strip()
            t_clean = row[1].replace('\n', ' ').strip()
            builder.append(f"Source: {s_clean}\nTarget: {t_clean}")
            
        return "\n\n".join(builder)
    except Exception as e:
        print(f"RAG Inference Error: {e}")
        return None
    finally:
        con.close()

try:
    agent = load_engine()
    st.sidebar.success("✅ Engine Ready")
except Exception as e:
    st.sidebar.error(f"❌ Engine Error: {e}")

st.title("🕉️ Interactive Translator (Mode I)")
st.caption("Configuration: **Full Agent + Dynamic RAG + Glossary Constraint**")

# =========================================================
# Sidebar: Settings (RAG & Glossary)
# =========================================================
with st.sidebar:
    st.header("⚙️ Enhancement Settings")
    
    # 1. Glossary Switch
    use_glossary = st.toggle("📚 Enable Glossary Constraint", value=True, help="Force specific terminology from uploaded glossary.")
    
    # 2. RAG Settings
    use_rag = st.toggle("🧠 Enable Dynamic RAG", value=True, help="Retrieve similar examples from database to guide style.")
    
    rag_dataset = "All"
    if use_rag:
        # 获取可用数据集列表
        con = get_db_connection()
        datasets = [r[0] for r in con.execute("SELECT DISTINCT dataset_name FROM dataset_items").fetchall()]
        con.close()
        
        if datasets:
            rag_dataset = st.selectbox("RAG Knowledge Base", ["All"] + datasets, index=0, 
                                     help="Which dataset to search for similar examples?")
        else:
            st.warning("No datasets found for RAG.")
            use_rag = False

# =========================================================
# Main Interface
# =========================================================

# 1. Input
src_text = st.text_area("Enter Sanskrit Text:", height=150, placeholder="e.g. dharmakṣetre kurukṣetre samavetā yuyutsavaḥ...")

if st.button("🚀 Translate", type="primary"):
    if not src_text.strip():
        st.warning("Please enter text.")
    else:
        with st.status("Thinking...", expanded=True) as status:
            
            # --- Step A: RAG Retrieval (If enabled) ---
            rag_context = None
            if use_rag:
                st.write("🔍 Searching for similar examples (RAG)...")
                rag_context = get_inference_rag_context(src_text, rag_dataset, k=3)
                if rag_context:
                    st.success(f"Found related examples from '{rag_dataset}'")
                    with st.expander("View RAG Context"):
                        st.text(rag_context)
                else:
                    st.info("No similar examples found (Zero-Shot).")
            
            # --- Step B: Run Agent (Mode I Logic) ---
            # use_grammar=True, use_dict=True (Full Agent)
            # use_glossary = toggle
            # few_shot_text = rag_context
            st.write("🤖 Agent working (Morphology + Dictionary + Glossary)...")
            
            state = agent.run(
                src_text=src_text,
                use_grammar=True,   # 始终开启语法
                use_dict=True,      # 始终开启词典
                few_shot_text=rag_context, # 注入 RAG
                use_glossary=use_glossary  # 注入 Glossary
            )
            
            status.update(label="Translation Complete!", state="complete", expanded=False)

        # 2. Output
        st.subheader("Translation")
        st.success(state.final_translation)
        
        # 3. Process Details (Trace)
        with st.expander("🧐 Inspect Agent Process (Evidence & Steps)"):
            
            # Tab layout for details
            t1, t2, t3 = st.tabs(["Logs", "Evidence", "Draft vs Final"])
            
            with t1:
                st.code("\n".join(state.logs))
                
            with t2:
                # Evidence Parsing
                # Note: agent.run saves evidence inside state in a structured way? 
                # orchestrator saves to DB, but state object usually has draft/final.
                # state.dict_evidence is available.
                
                if hasattr(state, 'dict_evidence') and state.dict_evidence:
                    st.markdown("#### Dictionary Definitions Used")
                    for k, v in state.dict_evidence.items():
                        st.markdown(f"**{k}**: {v}")
                else:
                    st.caption("No dictionary evidence used.")
                    
            with t3:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Draft (Zero-Shot/Baseline)**")
                    st.info(state.draft_translation)
                with c2:
                    st.markdown("**Final (Revised)**")
                    st.success(state.final_translation)

# =========================================================
# Recent History (Optional visual aid)
# =========================================================
st.markdown("---")
st.subheader("🕒 Recent Translations")
con = get_db_connection()
try:
    # 只显示最近的 5 条，按时间倒序
    history = con.execute("SELECT src_text, final_text, mode, timestamp FROM translations ORDER BY timestamp DESC LIMIT 5").fetchall()
    if history:
        for item in history:
            with st.container():
                st.markdown(f"**Source**: {item[0][:50]}...")
                st.caption(f"**Result**: {item[1]}")
                st.caption(f"Mode: {item[2]} | Time: {item[3]}")
                st.divider()
    else:
        st.caption("No history yet.")
except Exception:
    pass
finally:
    con.close()