# Training Datasets — what we use and why

> For Faiqa and Rana. This explains every dataset behind the PromptShield classifier: where it came from, which class it teaches, and how much of it survives cleaning.
>
> **The data itself is NOT in this repository.** It totals ~1.6 GB and three files individually exceed GitHub's 100 MB hard limit. It lives at `C:\Users\DELL\Desktop\FYP\dataset\` on Jawaria's machine. Run `python preprocessing/download_datasets.py` to rebuild the folder from scratch — every source URL is in that script.

---

## What the model learns

Three top-level classes, eight sub-types:

| Class | Sub-types |
|---|---|
| **Safe (Benign)** | — |
| **Direct Jailbreak** | Policy Evasion · Multi-Turn Manipulation · Role Override · Persona Hijacking · System Prompt Overwrite |
| **Indirect Prompt Injection** | Document Embedding · Web Content Injection · Tool Output Injection |

The main classifier predicts the **3 classes**. The 8 sub-types are a secondary head (Task 34) and populate the `AttackSubtype` table in the backend.

---

## The 23 source files

### Safe (Benign) — what normal prompts look like

| File | Rows | What it is |
|---|---|---|
| `train.tsv` (WildJailbreak, benign half) | 128,781 | Synthetic benign prompts from AllenAI |
| `alpaca_data.json` | 52,002 | Stanford instruction-following data |
| `train-00000-of-00001.parquet` (TrustAIRLab) | 13,735 | **Real** prompts scraped from Discord/Reddit |
| `jackhhao_…csv` (benign rows) | 1,332 | |
| `Completely-Benign_Dataset.csv` | 1,200 | |
| `slabs_prompt_injection.csv` (label 0) | 6,303 | |
| `safeguard_prompt_injection.parquet` | ~4,000 | |
| `deepset_…parquet` (label 0) | 343 | |
| Old CSV (`benign`) | 594 | Minor — see the warning below |

### Direct Jailbreak — attacks typed straight into the prompt box

| Sub-type | Main files | Rows |
|---|---|---|
| **Policy Evasion** | `train.tsv` harmful halves, TrustAIRLab jailbreak parquet | ~134,000 |
| **Multi-Turn Manipulation** | `Harmful%20Dataset.csv`, `SafeMTData_1K.json`, `Attack_600.json` | ~6,400 |
| **Persona Hijacking** | `jackhhao_…csv`, `rubend18_…csv` (DAN, DUDE, APOPHIS), `neuralchemy_…parquet` | ~1,250 |
| **System Prompt Overwrite** | `jackhhao_…csv`, `deepset_…parquet`, `neuralchemy_…parquet`, `slabs_…csv` | ~700 |
| **Role Override** | `redteam_dataset.v2.json`, `neuralchemy_…parquet` | ~200 |

### Indirect Injection — attacks hidden inside content the AI reads

| Sub-type | Files | Rows |
|---|---|---|
| **Web Content Injection** | `llmail_phase1.json` + `llmail_phase2.json` (Microsoft attack competition) | 145,354 |
| **Document Embedding** | `dataset_for_huggingface.jsonl` (BIPIA) | 34,007 |
| **Tool Output Injection** | NVIDIA `train.jsonl`, `test_cases_dh/ds_enhanced.json` | 656 |

---

## Three things worth understanding before you trust these numbers

### 1. The original 2M-row CSV is almost entirely duplicates

`llm_prompt_injection_jailbreak_dataset.csv` looks like the biggest dataset at 2,000,000 rows and 444 MB. It contains **1,040 unique prompts**, each repeated about **1,923 times**.

Training on it raw would produce a model that memorises ~1,000 sentences and reports ~97% accuracy, then fails the moment someone types an attack in their own words. It is now a *minor* contributor — the real-world data does the work.

### 2. Several sources repeat themselves internally

Deduplication exposed this only after the adapters ran:

| Source | Rows | Actually unique |
|---|---|---|
| `injecagent_dh` | 510 | **30** |
| `injecagent_ds` | 544 | **32** |
| `orq_redteam` | 158 | **51** |
| `nemotron` | 1,272 | 594 |

### 3. Some of this data is explicit

The TrustAIRLab and WildJailbreak files are **real scraped jailbreak attempts** and contain graphic sexual content. Normal for security research, but:

- **Never browse the raw files during a live demo.**
- Any example shown in the UI, the report, or the viva must be hand-picked from `ml/data/sample_1000.csv`.

---

## Where the current dataset is weak

After cleaning, 518,528 rows remain. The weak spots, in order:

| Sub-type | Rows | Real-world |
|---|---|---|
| **Role Override** | 51 | 51 |
| **System Prompt Overwrite** | 251 | 68 |
| **Tool Output Injection** | 656 | 656 |

And the broader issue: **only 5.7% of Direct Jailbreak rows are real-world** (8,113 of 141,248) because 94% of that class is synthetic WildJailbreak. Since the held-out test set uses real-world rows only, Direct Jailbreak gets tested against a thin pool.

This is documented rather than hidden. A known limitation defends well in a viva; a hidden one does not.

---

## Rejected — and why

**`gabrielchua/system-prompt-leakage`** (283,353 rows). Looked ideal for System Prompt Overwrite. On inspection its `content` field holds **system prompts and model responses**, not user-typed attacks. Training on it would teach the classifier to recognise the wrong side of the conversation entirely.

Worth remembering as a general rule: check *what the text actually is* before trusting a dataset's title.

---

## Rebuilding the data

```bash
cd ml
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python preprocessing/download_datasets.py   # fetch all sources -> data/raw/
python preprocessing/inspect_sources.py     # verify row counts
python preprocessing/prepare_dataset.py     # -> data/processed/clean.parquet
python preprocessing/verify_dataset.py      # audit the result
```

Two sources (`allenai/wildjailbreak`, BIPIA) are gated on Hugging Face. Both are `gated: auto`, so accepting the terms on their dataset page grants access instantly. Then run `huggingface-cli login`. **Never put a token in a file that reaches GitHub.**
