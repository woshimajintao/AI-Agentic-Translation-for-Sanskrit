# Agentic Sanskrit–English Translation 

This repository contains the codebase for an **agentic, tool-augmented Sanskrit–English translation framework** built on a frozen small language model (Qwen2.5-7B).  
The system improves translation quality **without any training or fine-tuning**, by orchestrating external linguistic tools (dictionary, morphology, glossary, and retrieval) at inference time.

The project accompanies an academic study on low-resource, morphologically rich language translation, with a focus on **robustness, interpretability, and reproducibility**.

---

## Key Features

- **Training-free agentic translation**  
  All experiments are conducted with frozen models; improvements come solely from inference-time orchestration.

- **Philologically grounded tools**
  - Monier–Williams Sanskrit–English dictionary (lexical grounding)
  - Ambuda-DCS morphological and syntactic analysis
  - Deterministic glossary constraints for terminology consistency
  - Optional dynamic top-*k* example retrieval (RAG)

- **Comprehensive evaluation**
  - Agentic system ablations (A–I)
  - General-purpose LLM baselines (GPT series)
  - Sanskrit-specific MT baselines (M2M100, IndicTrans2)

- **Leakage-safe experimental design**
  Strict separation between evaluation data and retrieval pools.

---

## Repository Structure


---

## Agentic Translation Pipeline

The system follows a **draft–evidence–revision** paradigm inspired by human translation practice:

1. *(Optional)* Retrieve glossary constraints and similar examples  
2. Generate a draft translation with a frozen LLM  
3. Acquire linguistic evidence via dictionary and morphology tools  
4. Compress raw tool outputs into structured summaries  
5. Revise the draft using only the provided evidence and constraints  

This design allows the model to correct lexical and grammatical errors while preserving fluency.

---

## Evaluation Overview

### Internal Ablations
Multiple system configurations (A–I) evaluate the individual and combined effects of:
- Dictionary lookup
- Morphological analysis
- Dynamic retrieval
- Glossary constraints

### External Baselines
- **General-purpose LLMs**: GPT-based translation
- **Sanskrit-specific MT systems**: M2M100, IndicTrans2

Metrics:
- **chrF** (primary)
- **BLEU** (secondary, via SacreBLEU)

---

## Data and Resources

All linguistic resources are stored locally in a **DuckDB-backed infrastructure**.
They contain **no sentence-level translations from the evaluation sets**, ensuring no data leakage.

- Monier–Williams Dictionary: lexical definitions only
- Ambuda-DCS: structured morphological annotations
- Glossaries: curated domain-specific terminology

---

## Reproducibility Notes

- No model parameters are updated at any stage
- All tool calls and outputs are logged with run identifiers
- Retrieval is leakage-safe (sequential split or leave-one-out)
- Random seeds and decoding settings are fixed across experiments

---

## Model

The agent uses **Qwen2.5-7B-Instruct** as the base language model (frozen):
https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

Model weights are **not included** in this repository and are loaded via Hugging Face.

---

## License and Usage

This repository is intended for **research and educational purposes**.
Please consult the original licenses of external models and linguistic resources before use.

---



