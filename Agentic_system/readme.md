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
```


## ✅ Prerequisites
- Python: 3.10 or 3.11

- Editor: VS Code (Recommended)

- Git: For cloning the repository

- (Optional) It is better if you also used Mac.

## 🚀 Quick Start Guide

Download and Open the Agentic_system project folder in VS Code, open the terminal (Ctrl + ~), and follow these steps.

### Step 1: Create & Activate Virtual Environment

Always use a virtual environment to keep dependencies isolated.

```text
# 1. Create venv
python3 -m venv venv

# 2. Activate venv
source venv/bin/activate
```
Windows (PowerShell)
```text
# 1. Create venv
python -m venv venv

# 2. Activate venv
.\venv\Scripts\activate
```

### Step 2: Install Dependencies (With Hardware Acceleration)

CRITICAL STEP: To enable GPU acceleration (Metal on Mac, CUDA on Windows), you must install llama-cpp-python with specific flags before installing the rest of the requirements.

#### 🍎 macOS (Apple Silicon M1/M2/M3) - Recommended

Enable Metal Performance Shaders (MPS):

```text
CMAKE_ARGS="-DGGML_METAL=on" pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```
#### 🪟 Windows (NVIDIA GPU)
Pre-requisite: Install Build Tools for Visual Studio and CUDA Toolkit.

```text
$env:CMAKE_ARGS = "-DGGML_CUDA=on"; pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

#### 🐧 Linux (NVIDIA GPU)
```text
CMAKE_ARGS="-DGGML_CUDA=on" pip install --upgrade --force-reinstall llama-cpp-python --no-cache-dir
```

#### 🐌 CPU Only (Universal fallback)
If you do not have a compatible GPU, simply run:
```text
pip install llama-cpp-python
```
After installing the core inference engine, install the rest:
```text
pip install -r requirements.txt
```

### Step 3: Download the GGUF Model
We use the 4-bit quantized version of Qwen2.5 to save memory (approx. 4.7GB) without sacrificing much performance.

```text
# Download the model to the local 'models' directory
huggingface-cli download bartowski/Qwen2.5-7B-Instruct-GGUF --include "Qwen2.5-7B-Instruct-Q4_K_M.gguf" --local-dir models/Qwen2.5-7B-GGUF --local-dir-use-symlinks False
```
Verification: Ensure the file exists at: models/Qwen2.5-7B-GGUF/Qwen2.5-7B-Instruct-Q4_K_M.gguf

### Step 4: Run the System
Launch the application using python -m streamlit to ensure path variables are handled correctly.

```text
python -m streamlit run app/Home.py
```

The application should automatically open in your browser at http://localhost:8501.


## 📂 Data Management


### 1. Adding New Test Sets

To evaluate the system on new data (e.g., bible), structure your files as follows:

```text
data/
  └── testsets/
      └── bible/
          ├── bible.sa  (Sanskrit Source Lines)
          └── bible.en  (English Reference Lines)
```
Go to the Evaluate page in the UI and click Scan & Ingest Local Datasets.

### 2. Dictionaries & Glossaries

Monier-Williams Dictionary: The system connects to the DuckDB database in data/ automatically.

Glossaries: Upload PDF, CSV, or JSONL glossaries via the Ingest tab in the UI to enforce terminology constraints.

## 🛠 Troubleshooting

### Q: ModuleNotFoundError: No module named 'llama_cpp'

A: You are likely not inside the virtual environment.

Ensure your terminal prompt shows (venv).

Run the app using python -m streamlit run ... instead of just streamlit run.

### Q: zsh: killed or Memory Overflow

A: Your system ran out of RAM.

Ensure you downloaded the GGUF (Quantized) version in Step 3, not the full 15GB model.

Close other memory-intensive applications (Chrome tabs, Docker, etc.).

### Q: xcrun: error: invalid active developer path (macOS)

A: You are missing Xcode command line tools required to compile llama-cpp. Run:

```text
xcode-select --install
```

### Q: Build fails on Windows

A: Installing llama-cpp-python on Windows can be tricky. You must have Visual Studio Community (with C++ development tools) installed. If CUDA fails, try the CPU-only installation command.



