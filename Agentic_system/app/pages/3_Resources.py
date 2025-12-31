import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# 路径设置
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.db.duckdb_conn import get_db_connection

st.set_page_config(page_title="Data Resources", layout="wide")
st.title("📚 Knowledge Base & Resources")

# 获取数据库连接
con = get_db_connection()

# --- 概览统计 ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    count_dict = con.execute("SELECT COUNT(*) FROM mw_lexicon").fetchone()[0]
    st.metric("📖 Dictionary Entries", f"{count_dict:,}")
with col2:
    count_morph = con.execute("SELECT COUNT(*) FROM morph_analysis").fetchone()[0]
    st.metric("🧬 Morph/Grammar Rows", f"{count_morph:,}")
with col3:
    count_test = con.execute("SELECT COUNT(*) FROM dataset_items").fetchone()[0]
    st.metric("🧪 Testset Pairs", f"{count_test:,}")
with col4:
    count_logs = con.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
    st.metric("📜 Translation Logs", f"{count_logs:,}")

st.markdown("---")

# --- 详细浏览器 ---
tab1, tab2, tab3, tab4 = st.tabs(["📖 Dictionary (MW)", "🧬 Grammar (Ambuda)", "🧪 Testsets", "📜 History"])

# === Tab 1: Dictionary ===
with tab1:
    st.header("Monier-Williams Dictionary")
    search_term = st.text_input("Lookup Lemma (e.g., 'dharma', 'agni')", "")
    
    if search_term:
        # 使用 ILIKE 进行模糊搜索
        df = con.execute("""
            SELECT lemma, gloss, raw_xml 
            FROM mw_lexicon 
            WHERE lemma ILIKE ? 
            LIMIT 20
        """, [f"{search_term}%"]).fetch_df()
        
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No entries found.")
    else:
        st.info("Enter a word above to search. Showing random 5 entries:")
        df = con.execute("SELECT lemma, gloss FROM mw_lexicon ORDER BY RANDOM() LIMIT 5").fetch_df()
        st.table(df)

# === Tab 2: Grammar (Ambuda) ===
with tab2:
    st.header("Ambuda Morphological Analysis")
    st.markdown("Maps **Inflected Words** (e.g., *kṣetre*) to **Lemmas** (e.g., *kṣetra*).")
    
    morph_search = st.text_input("Check Morphology (e.g., 'bhavati')", "")
    
    if morph_search:
        df = con.execute("""
            SELECT word, lemma, pos_tag, sent_id 
            FROM morph_analysis 
            WHERE word ILIKE ? 
            LIMIT 20
        """, [morph_search]).fetch_df()
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Showing random 10 grammar records:")
        df = con.execute("SELECT * FROM morph_analysis ORDER BY RANDOM() LIMIT 10").fetch_df()
        st.dataframe(df, use_container_width=True)

# === Tab 3: Testsets ===
with tab3:
    st.header("Evaluation Datasets")
    
    # 列出所有数据集名称
    datasets = con.execute("SELECT DISTINCT dataset_name FROM dataset_items").fetch_df()
    
    if not datasets.empty:
        selected_ds = st.selectbox("Select Dataset", datasets['dataset_name'])
        
        df = con.execute("""
            SELECT item_id, src_text, tgt_text 
            FROM dataset_items 
            WHERE dataset_name = ? 
            LIMIT 50
        """, [selected_ds]).fetch_df()
        
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No testsets found. Go to 'Evaluate' page to upload one.")

# === Tab 4: History ===
with tab4:
    st.header("Run History")
    history_df = con.execute("""
        SELECT run_id, timestamp, mode, src_text, final_text 
        FROM translations 
        ORDER BY timestamp DESC 
        LIMIT 20
    """).fetch_df()
    st.dataframe(history_df, use_container_width=True)

con.close()