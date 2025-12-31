# ambuda-dcs

Please download the zip and Unzip it to the data folder.https://github.com/woshimajintao/AI-Agentic-Translation-for-Sanskrit/tree/main/Agentic_system/data

https://github.com/ambuda-org/dcs/

Sanitized parse data from the **Digital Corpus of Sanskrit (DCS)**, extracted and lightly corrected for use in the [Ambuda](https://ambuda.org) project and downstream Sanskrit NLP.

> Source: Oliver Hellwig, *Digital Corpus of Sanskrit (DCS)*, 2010–2021.  
> License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). :contentReference[oaicite:0]{index=0}

---

## Overview

This repository contains **token-level parse data** for a small selection of well-known Sanskrit texts.  
The data is derived from the DCS treebank and includes:

- sandhi-split tokenization  
- lemmas and morphological tags  
- basic syntactic / dependency information (as provided by DCS)  

Compared to the original DCS export, these files:

- are **plain UTF-8 text**
- have had a few obvious formatting issues fixed (e.g. extra tabs, missing newlines)
- are grouped **one text per file** for easier scripting

This repo is meant as a lightweight way to:

- explore Sanskrit **morphology and syntax**,
- prototype grammar rules,
- and build / evaluate **taggers and parsers** without having to scrape or mirror the full DCS installation. :contentReference[oaicite:1]{index=1}

---

## Contents

Each `.txt` file corresponds to a single work:

- `amarushatakam.txt` – *Amaruśataka*  
- `bodhicaryavatara.txt` – *Bodhicaryāvatāra*  
- `caurapancashika.txt` – *Caurapañcāśikā*  
- `hamsadutam.txt` – *Haṃsadūta*  
- `kiratarjuniyam.txt` – *Kirātārjunīya*  
- `kokilasandesha.txt` – *Kokilasaṃdeśa*  
- `kumarasambhavam.txt` – *Kumārasambhava*  
- `mahabharatam.txt` – *Mahābhārata* (selected portions, as in DCS)  
- `meghadutam-kale.txt` – *Meghadūta* (Kale edition; includes a fix for double tabs)  
- `mukundamala.txt` – *Mukundamālā*  
- `ramayanam.txt` – *Rāmāyaṇa* (selected portions, as in DCS)  
- `rtusamharam.txt` – *Ṛtusaṃhāra*  
- `saundaranandam.txt` – *Saundarananda*  
- `shatakatrayam.txt` – *Śatakatraya*  

The selection mirrors a subset of DCS texts that are:

- relatively well-edited,
- widely used in teaching and research,
- and representative of classical Sanskrit poetry and narrative.

---

## Data format

The exact format follows DCS’s “parse data” conventions. In short:

- The data is **token-level**, not verse-level.
- Fields are **tab-separated**.
- A typical non-empty line corresponds to **one token** and includes:
  - surface form  
  - lemma  
  - morphological tag(s)  
  - additional features (e.g. case/number/gender for nominals, tense/mood/person for verbs)  
  - basic syntactic / dependency information (as encoded in DCS)  

Blank lines separate higher-level units (e.g. verses or sentences), depending on the source text.

For the **authoritative definition** of tags and fields, please consult the DCS documentation and papers describing the corpus. :contentReference[oaicite:2]{index=2}

---

## Typical use cases

You can use this repository to:

- **Study grammar and syntax**
  - mine case-frames, valency patterns, and common constructions,
  - inspect how DCS analyses specific verses or forms.
- **Train or evaluate NLP models**
  - POS taggers, morphological analyzers,
  - dependency parsers or shallow parsers for Sanskrit.
- **Design rule-based systems**
  - grammar checkers,
  - pattern-based meters, samāsa detectors, etc.

Example: reading one file with Python and doing simple statistics:

```python
from collections import Counter
from pathlib import Path

path = Path("mahabharatam.txt")
pos_counter = Counter()

with path.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue  # sentence / verse boundary
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        # Example: assume parts[2] contains a coarse POS or morph tag
        morph_tag = parts[2]
        pos_counter[morph_tag] += 1

for tag, freq in pos_counter.most_common(20):
    print(f"{tag}\t{freq}")
