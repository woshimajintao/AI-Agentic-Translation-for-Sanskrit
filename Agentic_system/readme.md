## Agent System Project Structure.

## 📂 Project Structure

The project is organized to separate the UI (Streamlit), Data Layer, and Core Logic (Agent/Tools).

```text
.
├── app/
│   ├── Home.py              # 🏠 Application Entry Point (Landing Page & Project Overview)
│   └── pages/
│       ├── 1_Translate.py   # 🗣️ Interactive Mode: Human-AI Translation Interface
│       ├── 2_Evaluate.py    # 📊 Evaluation Mode: Batch Testing, Ablation Studies (A-I) & Metrics
│       └── 3_Resources.py   # 📚 Data Viewer: Inspect Monier-Williams Dict, Glossaries & History
├── data/
│   ├── mw_lexicon.db        # 📖 DuckDB: Monier-Williams Dictionary Storage
│   ├── history.db           # 🕰️ Database: Translation logs, user feedback, and agent traces
│   ├── glossary/            # 📝 Domain-specific constraints (CSV/JSONL)
│   │   ├── sanskrit_glossary.csv
│   │   └── sanskrit_glossary.jsonl
│   └── testsets/            # 📂 Parallel Corpora for Evaluation
│       ├── mkb/             # Example dataset folder (e.g., Mahabharata)
│       └── ...
├── models/                  # 🤖 Local LLM Artifacts
│   ├── Qwen2.5-7B-GGUF/Qwen2.5-7B-Instruct-Q4_K_M.gguf    # Quantized models 
├── src/
│   ├── agent/
│   │   ├── orchestrator.py  # 🧠 Core Brain: Manages the Draft -> Tool -> Revise loop
│   │   └── state.py         # 📦 Data Class: Passes context (logs, drafts) between agent steps
│   ├── db/
│   │   └── duckdb_conn.py   # 🔌 Connection Manager: Handles Dictionary & History DB connections
│   ├── llm/
│   │   ├── prompts.py       # 💬 Prompt Engineering: System instructions for Modes A-I
│   │   └── qwen_local.py    # 🔗 LLM Wrapper: Interface for Ollama/Transformers
│   └── tools/
│       ├── dict_lookup.py   # 🔍 Tool: Monier-Williams Dictionary Retrieval
│       ├── glossary_lookup.py # 🔐 Tool: Glossary Constraint Enforcement
│       └── morph_lookup.py  # 🧩 Tool: Morphological Segmentation & Analysis
├── requirements.txt         # 📦 Python Dependencies
└── README.md                # 📄 Project Documentation



## ✅ Prerequisites
- Python: 3.10 or 3.11

- Editor: VS Code (Recommended)

- Git: For cloning the repository
