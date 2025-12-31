import streamlit as st
import pandas as pd
import sys
import re
import os
import random
import io
import zipfile
from pathlib import Path
import sacrebleu


PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))
DATA_DIR = PROJECT_ROOT / "data"

from src.db.duckdb_conn import get_db_connection
from src.llm.qwen_local import QwenLocalLLM
from src.agent.orchestrator import SanskritAgent
from src.llm.prompts import BASELINE_SYSTEM, GLOSSARY_SYSTEM_ADDENDUM
from src.tools.glossary_lookup import GlossaryLookupTool

@st.cache_resource
def load_engine():
    llm = QwenLocalLLM()
    agent = SanskritAgent(llm)
    return llm, agent

def clean_baseline_output(text: str) -> str:

    if not text: return ""
    patterns = [r'^(Here is|The translation|The meaning|Output).*?:', r'^Translation:', r'^Answer:']
    cleaned = text
    for p in patterns:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    return cleaned.strip().strip('"').strip("'").strip()

def get_similar_examples(src_text: str, dataset_name: str, exclude_id: int, k: int = 3, search_min_id: int = -1, search_max_id: int = 999999999) -> str:
    
    con = get_db_connection()
    try:
        query = """
            SELECT src_text, tgt_text, jaccard(src_text, ?) as similarity
            FROM dataset_items
            WHERE dataset_name = ? 
              AND item_id != ?        
              AND src_text != ?       
              AND item_id >= ?        
              AND item_id <= ?        
            ORDER BY similarity DESC
            LIMIT ?
        """
        results = con.execute(query, [src_text, dataset_name, exclude_id, src_text, search_min_id, search_max_id, k]).fetchall()
        
        if not results: return None
        valid_examples = [r for r in results if r[2] > 0.1] 
        if not valid_examples: return None
            
        builder = []
        for row in valid_examples:
            s_clean = row[0].replace('\n', ' ').strip()
            t_clean = row[1].replace('\n', ' ').strip()
            builder.append(f"Source: {s_clean}\nTarget: {t_clean}")
            
        return "\n\n".join(builder)
    except Exception as e:
        print(f"RAG Error: {e}")
        return None
    finally:
        con.close()

def create_pair_zip(data_items):
    """
    data_items: list of (id, src, tgt) tuples
    Returns bytes of a zip file containing .sa and .en
    """
    src_lines = [item[1].strip() for item in data_items]
    tgt_lines = [item[2].strip() for item in data_items]
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("testset.sa", "\n".join(src_lines))
        zf.writestr("testset.en", "\n".join(tgt_lines))
    
    return zip_buffer.getvalue()

try:
    llm, agent = load_engine()
    glossary_tool = GlossaryLookupTool() 
    st.sidebar.success("✅ Model Loaded")
except Exception as e:
    st.sidebar.error(f"❌ Model Load Failed: {e}")

st.title("📊Ablation & Evaluation")

# =========================================================
# Tab 1: Upload / Ingest Data
# =========================================================
tab1, tab2 = st.tabs(["📤 Ingest Data (Dataset & Glossary)", "🚀 Run Evaluation"])

with tab1:
    st.header("1. Ingest Test Dataset (Parallel Corpus)")
    st.info(f"Put dataset folders in: `{DATA_DIR}/testsets/`\n\nStructure: `folder_name/folder_name.sa` & `folder_name.en`")
    
    col_up1, col_up2 = st.columns(2)
    
    with col_up1:
        st.subheader("Option A: Scan Local Folders")
        if st.button("🔄 Scan & Ingest Local Datasets"):
            con = get_db_connection()
            base_path = DATA_DIR / "testsets"
            
            if not base_path.exists():
                os.makedirs(base_path, exist_ok=True)
                st.warning(f"Created directory: {base_path}")
                
            subdirs = [x for x in base_path.iterdir() if x.is_dir()]
            ingested_count = 0
            
            for subdir in subdirs:
                dataset_name = subdir.name
                sa_file = subdir / f"{dataset_name}.sa"
                en_file = subdir / f"{dataset_name}.en"
                
                if sa_file.exists() and en_file.exists():
                    with st.spinner(f"Ingesting {dataset_name}..."):
                        with open(sa_file, 'r', encoding='utf-8') as f:
                            sa_lines = [l.strip() for l in f.readlines() if l.strip()]
                        with open(en_file, 'r', encoding='utf-8') as f:
                            en_lines = [l.strip() for l in f.readlines() if l.strip()]
                        
                        if len(sa_lines) != len(en_lines):
                            st.warning(f"⚠️ Skipping {dataset_name}: Line count mismatch")
                            continue
                        
                        data_to_insert = []
                        for i in range(len(sa_lines)):
                            data_to_insert.append((dataset_name, i + 1, sa_lines[i], en_lines[i]))
                        
                        con.execute("DELETE FROM dataset_items WHERE dataset_name = ?", [dataset_name])
                        con.executemany("INSERT INTO dataset_items (dataset_name, item_id, src_text, tgt_text) VALUES (?, ?, ?, ?)", data_to_insert)
                        
                        st.success(f"✅ Ingested **{dataset_name}** ({len(data_to_insert)} pairs)")
                        ingested_count += 1
            
            con.close()
            if ingested_count == 0:
                st.warning("No valid datasets found.")
            else:
                st.success(f"🎉 Processed {ingested_count} datasets.")

    with col_up2:
        st.subheader("Option B: Upload CSV File")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        csv_name = st.text_input("Dataset Name for CSV", "custom_csv_v1")
        
        if uploaded_file and csv_name:
            if st.button("Ingest CSV"):
                try:
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                    df = pd.read_csv(stringio)
                    if "source" not in df.columns or "target" not in df.columns:
                        st.error("CSV must contain 'source' and 'target' columns.")
                    else:
                        con = get_db_connection()
                        data_to_insert = []
                        for idx, row in df.iterrows():
                            data_to_insert.append((csv_name, idx + 1, row['source'], row['target']))
                        con.execute("DELETE FROM dataset_items WHERE dataset_name = ?", [csv_name])
                        con.executemany("INSERT INTO dataset_items (dataset_name, item_id, src_text, tgt_text) VALUES (?, ?, ?, ?)", data_to_insert)
                        con.close()
                        st.success(f"✅ Uploaded {len(data_to_insert)} items.")
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.header("2. Ingest Glossary (CSV/JSONL)")
    st.markdown("Load standard glossary files from `data/glossary/`. Supports `.csv` or `.jsonl`.")
    st.info("Files must have fields: `term`, `definition` (and optionally `source`, `page`).")
    
    if st.button("📂 Load Glossary from 'data/glossary'"):
        glossary_dir = DATA_DIR / "glossary"
        if not glossary_dir.exists():
            st.error(f"Directory not found: {glossary_dir}")
        else:
            csv_file = glossary_dir / "sanskrit_glossary.csv"
            jsonl_file = glossary_dir / "sanskrit_glossary.jsonl"
            
            df = None
            source_type = ""
            
            try:
                if csv_file.exists():
                    source_type = "CSV"
                    df = pd.read_csv(csv_file)
                elif jsonl_file.exists():
                    source_type = "JSONL"
                    df = pd.read_json(jsonl_file, lines=True)
                
                if df is not None:
                    required_cols = {"term", "definition"}
                    if not required_cols.issubset(df.columns):
                        st.error(f"File missing required columns: {required_cols}. Found: {df.columns.tolist()}")
                    else:
                        con = get_db_connection()
                        con.execute("CREATE TABLE IF NOT EXISTS glossary (term VARCHAR, definition VARCHAR, source VARCHAR, page INTEGER)")
                        con.execute("DELETE FROM glossary") 
                        
                        if "source" not in df.columns: df["source"] = "Unknown"
                        if "page" not in df.columns: df["page"] = 0
                        
                        data_to_insert = []
                        for _, row in df.iterrows():
                            data_to_insert.append((
                                str(row['term']).strip(), 
                                str(row['definition']).strip(), 
                                str(row['source']), 
                                int(row['page']) if pd.notnull(row['page']) else 0
                            ))
                            
                        con.executemany("INSERT INTO glossary VALUES (?, ?, ?, ?)", data_to_insert)
                        con.close()
                        
                        st.success(f"✅ Successfully loaded {len(data_to_insert)} terms from {source_type}.")
                        with st.expander("View Loaded Terms"):
                            st.dataframe(df.head(10))
                else:
                    st.warning("No 'sanskrit_glossary.csv' or '.jsonl' found in data/glossary/")
            except Exception as e:
                st.error(f"Error loading glossary: {e}")

# =========================================================
# Tab 2: Run Evaluation 
# =========================================================
with tab2:
    st.header("Run Evaluation Task")
    
    con = get_db_connection()
    datasets = con.execute("SELECT DISTINCT dataset_name FROM dataset_items ORDER BY dataset_name").fetchall()
    dataset_options = [d[0] for d in datasets]
    con.close()
    
    # === 1. Mode Selection ===
    # Tuple: (UseAgentClass, UseGrammar, UseDict, UseFewShot, UseGlossary)
    MODES = {
        "A: Baseline (No Tools)":    (False, False, False, False, False),
        "B: Dict Only (MW)":         (True,  False, True,  False, False),
        "C: Grammar Only":           (True,  True,  False, False, False),
        "D: Full Agent (MW+Gram)":   (True,  True,  True,  False, False),
        "E: Static Few-Shot":        (True,  True,  True,  True,  False),
        "F: Dynamic Top-k RAG":      (True,  True,  True,  True,  False),
        "G: Baseline + Glossary":    (False, False, False, False, True),
        "H: Full Agent + Glossary":  (True,  True,  True,  False, True),
        "I: Dynamic RAG + Glossary": (True,  True,  True,  True,  True)
    }
    
    col_mode, col_data = st.columns([2, 1])
    with col_mode:
        mode_selection = st.selectbox("1. Select Translation Mode", list(MODES.keys()))
        
    with col_data:
        if dataset_options:
            selected_dataset = st.selectbox("2. Select Dataset", dataset_options, key="dataset_selector")
        else:
            selected_dataset = None
            st.warning("No datasets found.")

    # Unpack Logic Flags
    is_agent_class, use_grammar, use_dict, use_few_shot, use_glossary = MODES[mode_selection]
    is_dynamic_rag = "F:" in mode_selection or "I:" in mode_selection
    is_static_few_shot = "E:" in mode_selection

    st.markdown("---")
    
    # === 2. Sampling (Common for ALL modes) ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Settings")
        
        run_all = st.checkbox("🔥 Evaluate ALL items", value=False)
        sampling_method = "All"
        limit = None
        
        # [CROSS-MODEL CONSISTENCY LOCK]
        restrict_pool_to_half = st.checkbox("🔒 Restrict Test Pool to 1st Half (Ensure consistency with RAG modes)", value=False, 
                                            help="If checked, Baseline/Agent will also sample ONLY from the 1st half, making it directly comparable to Mode F/I (Sequential RAG).")

        if not run_all:
            sampling_method = st.radio("Selection", ["First N Items", "Random N Items"], horizontal=True)
            limit = st.slider("Test Sample Size (N)", 1, 200, 5)
            
            if sampling_method == "Random N Items":
                if "random_seed" not in st.session_state: st.session_state.random_seed = 42
                
                c_seed1, c_seed2 = st.columns([1, 2])
                with c_seed1:
                    if st.button("🎲 Shuffle"): st.session_state.random_seed = random.randint(1, 100000)
                with c_seed2:
                    st.caption(f"Seed: {st.session_state.random_seed} (Locked)")
        
    # === 3. Conditional Config (Only for specific modes) ===
    with col2:
        # Partition / Few-Shot Settings (Conditional)
        split_strategy = "Global Random (Leave-One-Out)" # Default
        n_examples = 0
        
        if use_few_shot:
            st.subheader("Few-Shot / RAG Config")
            split_strategy = st.radio(
                "Partition Strategy",
                ["Global Random (Leave-One-Out)", "Sequential Split (Half/Half)"],
                help="Sequential: Test 1st Half / Search 2nd Half"
            )
            n_examples = st.slider("Num Examples (k)", 1, 10, 3)
        elif use_glossary:
            st.subheader("Glossary Config")
            st.info("Glossary Constraint: ON")
        else:
            st.subheader("Mode Info")
            st.info(f"Mode: {mode_selection.split(':')[0]}")

    # === Start Button ===
    if st.button("Start Evaluation", type="primary"):
        if not selected_dataset: st.warning("Please select a dataset."); st.stop()
        
        con = get_db_connection()
        all_items = con.execute("SELECT item_id, src_text, tgt_text FROM dataset_items WHERE dataset_name = ? ORDER BY item_id", [selected_dataset]).fetchall()
        con.close()
        
        total_count = len(all_items)
        mid_point = total_count // 2
        
        # === Step 1: Define Pools (The Critical Consistency Logic) ===
        test_universe, search_universe = [], []
        search_min_id, search_max_id = -1, 999999999
        
        should_use_half_pool = restrict_pool_to_half or (use_few_shot and split_strategy.startswith("Sequential"))
        
        if should_use_half_pool:
            test_universe = all_items[:mid_point]
            search_universe = all_items[mid_point:] 
            if search_universe:
                search_min_id = search_universe[0][0]
                search_max_id = search_universe[-1][0]
            
            if use_few_shot and split_strategy.startswith("Sequential"):
                st.info(f"📚 Sequential Split Active: Testing indices 0-{mid_point} (1st Half)")
            else:
                st.info(f"🔒 Consistency Lock: Testing Restricted to indices 0-{mid_point} (1st Half)")
        else:
            test_universe = all_items
            search_universe = all_items
            st.info("🌍 Global Pool: Testing on entire dataset range.")

        if not test_universe: st.error("Test Universe is empty!"); st.stop()

        # === Step 2: Select Items (Apply Random Seed Lock) ===
        final_test_items = []
        if run_all:
            final_test_items = test_universe
        else:
            if len(test_universe) <= limit:
                st.warning("Universe smaller than requested limit. Using all available.")
                final_test_items = test_universe
            else:
                if sampling_method == "First N Items":
                    final_test_items = test_universe[:limit]
                else:
                    random.seed(st.session_state.random_seed)
                    final_test_items = random.sample(test_universe, limit)
        
        st.session_state['last_test_set'] = final_test_items
        st.session_state['last_test_seed'] = st.session_state.random_seed if sampling_method == "Random N Items" else "FirstN"

        # === Step 3: Prepare Static Context (Only Mode E) ===
        static_few_shot_text = None
        if is_static_few_shot:
            test_ids = {item[0] for item in final_test_items}
            candidates = [item for item in search_universe if item[0] not in test_ids]
            if len(candidates) >= n_examples:
                random.seed(st.session_state.random_seed) 
                chosen = random.sample(candidates, n_examples)
                static_few_shot_text = "\n\n".join([f"Source: {ex[1].strip()}\nTarget: {ex[2].strip()}" for ex in chosen])
            else:
                st.warning("Not enough static examples available.")

        # === Step 4: Run Loop ===
        st.write(f"Running **{mode_selection}** on **{len(final_test_items)}** items...")
        results = []
        all_refs, all_hyps = [], []
        progress_bar = st.progress(0)
        
        # Live Display Placeholder (Conditional)
        context_placeholder = st.empty()
        
        for i, item in enumerate(final_test_items):
            item_id, src, ref = item
            
            # Context
            current_context = None
            display_ctx = "None"
            if is_dynamic_rag:
                current_context = get_similar_examples(src, selected_dataset, item_id, n_examples, search_min_id, search_max_id)
                display_ctx = current_context if current_context else "No matches."
            elif is_static_few_shot:
                current_context = static_few_shot_text
                display_ctx = static_few_shot_text
            
            # Glossary Display
            glossary_text_display = "None"
            
            # Execution
            hyp = ""
            try:
                if not is_agent_class: 
                    if not use_glossary:
                        messages = [{"role": "system", "content": BASELINE_SYSTEM}, {"role": "user", "content": f"Translate this Sanskrit text to English:\n{src}"}]
                        hyp = clean_baseline_output(llm.generate(messages))
                    else:
                        g_hits = glossary_tool.run(src)
                        g_str = ""
                        if g_hits:
                            entries = [f"- {t}: {d}" for t, d in g_hits.items()]
                            g_str = GLOSSARY_SYSTEM_ADDENDUM.format(glossary_content="\n".join(entries))
                            glossary_text_display = str(g_hits)
                        messages = [{"role": "system", "content": BASELINE_SYSTEM + g_str}, {"role": "user", "content": f"Translate this Sanskrit text to English:\n{src}"}]
                        hyp = clean_baseline_output(llm.generate(messages))
                else:
                    state = agent.run(src, use_grammar=use_grammar, use_dict=use_dict, few_shot_text=current_context, use_glossary=use_glossary)
                    hyp = state.final_translation
                    
                    if use_glossary:
                        g_hits = glossary_tool.run(src)
                        if g_hits: glossary_text_display = str(g_hits)

                # Live Display Update (Conditional Visibility)
                with context_placeholder.container():
                    st.info(f"Processing ID: {item_id}")
                    
                    cols = st.columns(2) if (use_few_shot and use_glossary) else st.columns(1)
                    
                    if use_few_shot:
                        with cols[0]:
                            with st.expander("🔍 Context (Few-Shot)", expanded=True):
                                st.text_area("Context", display_ctx, height=150, key=f"ctx_{i}")
                    
                    if use_glossary:
                        target_col = cols[1] if use_few_shot else cols[0]
                        with target_col:
                            with st.expander("📖 Glossary Found", expanded=True):
                                st.text_area("Glossary", glossary_text_display, height=150, key=f"glo_{i}")

                # Metrics
                bleu = sacrebleu.sentence_bleu(hyp, [ref]).score
                #chrf = sacrebleu.sentence_chrf(hyp, [ref]).score
                chrf = sacrebleu.sentence_chrf(hyp, [ref], word_order=2).score
                all_refs.append(ref)
                all_hyps.append(hyp)
                results.append({
                    "ID": item_id, "Source": src, "Ref": ref, "Hyp": hyp,
                    "BLEU": round(bleu, 1), "chrF": round(chrf, 1),
                    "Full Context": display_ctx,
                    "Glossary Used": glossary_text_display
                })
            except Exception as e: st.error(f"Error {item_id}: {e}")
            progress_bar.progress((i + 1) / len(final_test_items))
            
        st.success("Complete!")
        res_df = pd.DataFrame(results)
        
        st.dataframe(res_df[["ID", "Source", "Ref", "Hyp", "BLEU", "chrF"]])
        
        if all_hyps:
            c_bleu = sacrebleu.corpus_bleu(all_hyps, [all_refs]).score
            #c_chrf = sacrebleu.corpus_chrf(all_hyps, [all_refs]).score
            c_chrf = sacrebleu.corpus_chrf(all_hyps, [all_refs], word_order=2).score
            st.markdown("---")
            st.subheader(f"🏁 Results: {mode_selection}")
            c1, c2 = st.columns(2)
            c1.metric("Corpus BLEU", f"{c_bleu:.2f}")
            c2.metric("Corpus chrF", f"{c_chrf:.2f}")
            
        st.markdown("---")
        st.subheader("🔍 Detail Inspector")
        if not res_df.empty:
            s_id = st.selectbox("Select ID to Inspect", res_df["ID"], key="inspect")
            row = res_df[res_df["ID"] == s_id].iloc[0]
            ic1, ic2 = st.columns(2)
            with ic1:
                st.text_area("Source", row["Source"], height=100, disabled=True)
                st.text_area("Hypothesis", row["Hyp"], height=100, disabled=True)
            with ic2:
                st.text_area("Reference", row["Ref"], height=100, disabled=True)
            
            if use_few_shot or use_glossary:
                ic3, ic4 = st.columns(2)
                with ic3: 
                    if use_few_shot: st.text_area("RAG Context Used", row["Full Context"], height=200)
                with ic4: 
                    if use_glossary: st.text_area("Glossary Terms Used", row["Glossary Used"], height=200)

# =========================================================
# Step 5: Download Selected Test Set (Always Visible after run)
# =========================================================
if 'last_test_set' in st.session_state:
    st.markdown("---")
    st.header("📥 Download Selected Test Set")
    st.info("Download the subset of items used in the last evaluation (e.g. your specific Random N).")
    
    test_data = st.session_state['last_test_set'] # list of (id, src, tgt)
    
    d_col1, d_col2 = st.columns(2)
    
    # 1. Download as Pair (.sa + .en Zip)
    with d_col1:
        zip_bytes = create_pair_zip(test_data)
        st.download_button(
            label="Download .sa/.en (ZIP)",
            data=zip_bytes,
            file_name=f"testset_subset_{st.session_state.get('last_test_seed', 'custom')}.zip",
            mime="application/zip"
        )
        
    # 2. Download as CSV
    with d_col2:
        df_download = pd.DataFrame(test_data, columns=['item_id', 'source', 'target'])
        csv_str = df_download[['source', 'target']].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download .csv",
            data=csv_str,
            file_name=f"testset_subset_{st.session_state.get('last_test_seed', 'custom')}.csv",
            mime="text/csv"
        )
