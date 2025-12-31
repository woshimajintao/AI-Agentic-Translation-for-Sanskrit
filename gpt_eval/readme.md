# GPT-based Sanskrit → English Evaluation

This directory contains evaluation notebooks for **Sanskrit-to-English machine translation** using GPT models.
The focus is on **sentence-level translation quality**, evaluated with **BLEU** and **chrF2**.

---

## 📁 Directory Structure

```text
gpt_eval/
├── GPT_4o_mini.ipynb   # Evaluation using GPT-4o-mini
├── GPT_5.ipynb        # Evaluation using GPT-5
└── readme.md          # This file
```

---

## 📂 Dataset Location (Required)

The notebooks assume they are executed **from the repository root**.

Parallel datasets must be placed under:

```text
data/<domain>/testset_subset_42/
├── testset.sa   # Sanskrit source sentences
└── testset.en   # English reference translations
```

Supported domains:

* `itihasa`
* `bible`
* `gitasopanam`
* `mkb`
* `spoken-tutorials`

---

## 🔧 Environment Setup

### Install dependencies

```bash
pip install -U openai sacrebleu pandas tqdm gitpython "httpx>=0.28.1,<1"
```

---

### OpenAI API Key

#### Local / GitHub

```bash
export OPENAI_API_KEY="your_api_key_here"
```

#### Google Colab

Store the key as a **Colab secret** named `gpt`.

The notebooks automatically detect the environment.

---

## ▶️ Running the Evaluation

From the **repository root**, open and run one of the notebooks:

* `gpt_eval/GPT_4o_mini.ipynb`
* `gpt_eval/GPT_5.ipynb`

Each notebook performs the following steps:

1. Load Sanskrit–English sentence pairs
2. Translate Sanskrit → English using a GPT model
3. Cache model outputs to avoid repeated API calls
4. Compute **BLEU** and **chrF2** scores

---

## 📊 Evaluation Metrics

* **BLEU**: SacreBLEU with `tokenize="13a"`
* **chrF2**: Character F-score with word order = 2

---

## 💾 Caching Mechanism

Model outputs are cached as `.jsonl` files under:

```text
gpt_cache/
```

Each cached entry records:

* sentence index
* model-generated translation

Caching allows safe resumption of interrupted runs without re-querying the API.

> The `gpt_cache/` directory is generated automatically and should not be committed to version control.

---

## ⚠️ Notes

* API usage may incur costs depending on OpenAI pricing.
* A small delay is introduced between requests to reduce rate-limit risk.
* All paths are resolved relative to the repository root.

---

## 📜 Usage

This module is intended for **research and evaluation purposes**.
Please ensure that dataset licenses are respected.

