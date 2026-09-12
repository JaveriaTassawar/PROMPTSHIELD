# ML Track — Detailed Tasks (Faiqa + Jawaria)

> Part of the PromptShield FYP. The master plan is [`../tasks/MASTER_PLAN.md`](../tasks/MASTER_PLAN.md) — it owns task numbering, the dependency map, team roles, and the git workflow. **This file owns the ML detail**: dataset inventory, label mapping, training environment, and per-task specifics for Tasks 13–37.
>
> Branch prefix for all work here: `ml/`

---

## 1. Taxonomy — 3 classes, 8 sub-types

Matches the SRS Abstract and the team's agreed taxonomy. **Authoritative label set.**

| # | Top-level class | Sub-types |
|---|---|---|
| 1 | **Safe (Benign)** | _(none)_ |
| 2 | **Direct Jailbreak** | Policy Evasion · Multi-Turn Manipulation · Role Override · Persona Hijacking · System Prompt Overwrite |
| 3 | **Indirect Prompt Injection** | Document Embedding · Web Content Injection · Tool Output Injection |

The **primary classifier predicts the 3 top-level classes only**. The 8 sub-types are the secondary head (Task 34) and the value stored in the `AttackSubtype` table (backend Task 44).

---

## 2. Dataset inventory — all files verified and downloaded

Everything lives in `C:\Users\DELL\Desktop\FYP\dataset\` (outside the repo, gitignored — 1.6 GB total). Row counts below were measured directly, not estimated.

### 2a. Safe (Benign)

| File | Rows | Notes |
|---|---|---|
| `alpaca_data.json` | 52,002 | Clean instruction-following data. Keys: `instruction`, `input`, `output` — use `instruction` as the text. |
| `train-00000-of-00001.parquet` (TrustAIRLab `regular`) | 13,735 | Real forum prompts, `jailbreak == False`. Columns: `platform, source, prompt, jailbreak, created_at, date`. |
| `train.tsv` (WildJailbreak) — `vanilla_benign` + `adversarial_benign` | **128,781** | Of 261,559 total rows. TSV, columns: `vanilla, adversarial, completion, data_type`. |
| `Completely-Benign_Dataset.csv` (tom-gibbs) | 1,200 | Columns: `Goal ID, Goal, Prompt, Multi-turn conversation, …` |
| `jackhhao_jailbreak_classification.csv` — `type == benign` | 1,332 | |
| `deepset_prompt_injections.parquet` — `label == 0` | 343 | |
| Old CSV — `label == 'benign'` (after dedup) | **594 unique** | Minor contributor only. |

### 2b. Direct Jailbreak

| Sub-type | File | Rows | Notes |
|---|---|---|---|
| **Policy Evasion** | `train-00000-of-00001 (1).parquet` (TrustAIRLab `jailbreak`) | 1,405 | Real in-the-wild jailbreaks. |
| **Policy Evasion** | `train.tsv` — `adversarial_harmful` | 82,728 | Synthetic but large and varied. Use the `adversarial` column. |
| **Policy Evasion** | `train.tsv` — `vanilla_harmful` | 50,050 | Direct harmful requests; use the `vanilla` column. |
| **Policy Evasion** | Old CSV — `hypothetical_framing`, `refusal_suppression`, `context_manipulation` | 18 unique each | Minor. |
| **Multi-Turn Manipulation** | `Attack_600.json` (SafeMTData) | 600 records / **2,996 turns** | Every record has `multi_turn_queries` (a list). Flatten turns or join them — decide once, document in the adapter. |
| **Multi-Turn Manipulation** | `SafeMTData_1K.json` | 1,680 records | **Different schema** — no `multi_turn_queries`; uses a `conversations` list of `{role, content}`. Adapter must handle both shapes. |
| **Multi-Turn Manipulation** | `Harmful%20Dataset.csv` (tom-gibbs) | 4,136 | Has a `Multi-turn conversation` column. |
| **Role Override** | `redteam_dataset.v2.json` (orq) — `input.vulnerability == "goal_hijacking"` | **158** | Structure: `{"metadata": …, "samples": [{"input": {…}, "messages": […]}]}`. Filter on `sample["input"]["vulnerability"]`. Still the thinnest sub-type — flag in `MODEL_CARD.md`. |
| **Persona Hijacking** | `jackhhao_jailbreak_classification.csv` — jailbreak rows matching persona patterns | ~530 | 1,998 rows total (666 jailbreak / 1,332 benign), 651 unique jailbreaks. |
| **Persona Hijacking** | `rubend18_chatgpt_jailbreak_prompts.csv` | 79 | Named personas: DAN, DUDE, APOPHIS, BasedGPT… 68 match persona patterns. |
| **Persona Hijacking** | Old CSV — `role_play_persona` | 90 unique | |
| **System Prompt Overwrite** | `jackhhao_…csv` — jailbreak rows matching override wording | ~143 | |
| **System Prompt Overwrite** | `deepset_prompt_injections.parquet` — `label == 1` w/ override wording | 41 | 546 rows total (203 injection / 343 benign). |
| **System Prompt Overwrite** | Old CSV — `instruction_override` | 90 unique | |

### 2c. Indirect Prompt Injection

| Sub-type | File | Rows | Notes |
|---|---|---|---|
| **Document Embedding** | `dataset_for_huggingface.jsonl` (BIPIA) | **70,000** — perfectly balanced 35,000 / 35,000 | Keys: `context`, `user_intent`, `label`, `source`. `label == 1` is the injection. Best Indirect source by far. |
| **Document Embedding** | Old CSV — `indirect_injection` | 90 unique | Minor. |
| **Web Content Injection** | `llmail_phase1.json` (Microsoft) | **160,741** | JSON object keyed by the email text; value `{attack_attempt, reason}`. Values seen: `'True'`, `'False'`, `'Unclear'`, and boolean `True` — **normalise all four forms**; drop `'Unclear'`. |
| **Web Content Injection** | `llmail_phase2.json` (Microsoft) | **37,303** | Same shape as phase1. |
| **Tool Output Injection** | `train.jsonl` (NVIDIA Nemotron) | 1,272 | Keys include `domain`, `attack_category`, `target_tool`, `injection_vector`, `injection`. |
| **Tool Output Injection** | `test_cases_dh_enhanced.json` | 510 | InjecAgent-style. Keys: `Attacker Instruction`, `Attack Type`, `User Instruction`, `Tool Response`… |
| **Tool Output Injection** | `test_cases_ds_enhanced.json` | 544 | Same schema as above. |

### 2d. The old CSV is heavily duplicated — deduplicate before use

Measured over 600,000 rows; scanning further did **not** raise the counts, so these are effectively whole-file totals.

| Raw label | Unique prompts |
|---|---|
| `benign` | 594 |
| `indirect_injection` | 90 |
| `instruction_override` | 90 |
| `delimiter_confusion` | 90 |
| `role_play_persona` | 90 |
| `context_manipulation` | 18 |
| `encoding_obfuscation` | 18 |
| `hypothetical_framing` | 18 |
| `refusal_suppression` | 18 |
| `payload_splitting` | 12 |
| `prompt_leak` | **3** |
| **Total unique** | **1,041** |

The entire 2,000,000-row file is ~1,041 template sentences repeated ~192× each. Training on the raw rows produces a model that **memorises those sentences and reports a falsely high accuracy** while staying weak against real, differently-worded attacks. Task 18 deduplicates before anything else, and the old CSV is treated as a **minor** contributor — the real-world datasets carry the training.

**Also verified:** the old CSV's `source_channel` column (`email_assistant`, `browser_plugin`, `agent_tool`, …) is **random noise**, not a signal — `indirect_injection` rows spread almost perfectly evenly across all five channels (~3,300 each per 400k rows). Do **not** use it to derive the three Indirect sub-types.

### 2e. Content warning

The TrustAIRLab in-the-wild prompts and parts of WildJailbreak contain **explicit / NSFW content** — they are scraped real jailbreak attempts. Normal for this research area, but: don't browse them in a live demo, and hand-pick any example shown in the UI, the report, or the committed sample (Task 22).

---

## 3. Training environment — Google Colab

Training runs on **Colab's free T4 GPU**, not a local laptop.

- DistilBERT fine-tuning on CPU is ~10+ hours per run; on a T4 it is ~20–40 minutes. Several tuning attempts are expected (Task 29), so this decides whether the ML track finishes on schedule.
- Free tier is sufficient — no Colab Pro needed.
- **Two Colab constraints to handle in the notebook, not discover at 2am:**
  1. Sessions disconnect after ~90 minutes idle and the VM is wiped. **Mount Google Drive at the top of the notebook and save checkpoints there**, never to Colab's local disk.
  2. Upload `clean.parquet` to Drive rather than re-uploading raw sources each session — the raw data is 1.6 GB.
- Keep `training/train.py` runnable **both** as a plain script and importable from the notebook. Training logic must not live only in notebook cells, or it can't be version-controlled or reviewed in a PR.

---

## 4. Accuracy target — two-tier

The SRS is internally inconsistent: §1.4 Objectives says ">90% accuracy, F1 > 0.85"; §2.5 Assumptions says "≥80% accuracy"; the SDS wireframes show "≥80%". Resolution:

- **Primary, binding target:** >90% accuracy and >0.85 F1 (SRS §1.4).
- **Documented fallback floor:** ≥80% accuracy (SRS §2.5) — only after a genuine tuning pass in Task 29.
- If the fallback is used it must be stated visibly in `MODEL_CARD.md` and raised with the advisor. Never a silent substitution.
- **Realistic expectation:** high-80s to low-90s on the real-world test set. That is the honest number, and it is what survives an examiner typing their own jailbreak into the live demo.

---

## 5. Evaluation rules (binding for Tasks 20, 30, 31)

- **Deduplicate first** (Task 18), then balance. Safe still dominates after dedup (Alpaca + WildJailbreak benign alone exceed 180k) — down-sample Safe or apply class weights.
- **Hold out a real-data-only test set** (Task 20). The headline accuracy/F1 in Task 31 must come from **real, human-written prompts never seen in training** — TrustAIRLab, SafeMTData, Microsoft llmail, NVIDIA Nemotron. Never report the headline from a synthetic split; that measures memorisation.
- Report the real-world and synthetic scores as **two clearly-labelled numbers**.
- Task 30 reports **per-class and per-sub-type** metrics. Likely weak spots: Role Override (158), System Prompt Overwrite (~270), Persona Hijacking (~690).

---

## 6. Tasks 13–37

Markers: ✅ done · 🔵 ready now · 🟡 in progress order (finish the one before it) · 🔴 needs a teammate's task first

### Dataset Prep

🔵 **Task 13** — Create `ml/data/raw/`, `ml/data/processed/`, `ml/preprocessing/`, `ml/training/`, `ml/inference/`. Add `requirements.txt`: `pandas`, `pyarrow`, `transformers`, `torch`, `scikit-learn`, `datasets`.

🟡 **Task 14** — `preprocessing/download_datasets.py`. **All 20 files are already downloaded** to `C:\Users\DELL\Desktop\FYP\dataset\` — this script's job is to copy/symlink them into `ml/data/raw/` and re-download any that are missing. Must be re-runnable (skip files already present) and print a summary of downloaded / skipped / failed.
  - Public, no auth: SafeMTData ×2, tom-gibbs ×2, orq, llmail phase1+phase2, NVIDIA Nemotron, jackhhao, rubend18, deepset.
  - **Gated — need a Hugging Face token** (`huggingface-cli login`, after accepting terms on each dataset page; both are `gated: auto`, so access is instant): WildJailbreak `train.tsv`, BIPIA `dataset_for_huggingface.jsonl`. **Both already downloaded and verified.** Read the token from the environment or the CLI login — **never hardcode it**; this file goes to GitHub.

🟡 **Task 15** — `preprocessing/inspect_sources.py` — for every file in `ml/data/raw/`, print row count, columns/keys, and 2 example records. Confirm each matches section 2 above before writing any mapping.

🟡 **Task 16** — `preprocessing/map_labels.py` — one adapter function per source file, each returning uniform records `{text, label_3class, subtype, source}` per the tables in section 2. Watch for:
  - `SafeMTData_1K.json` uses `conversations` (list of `{role, content}`), while `Attack_600.json` uses `multi_turn_queries` (list of strings) — handle both.
  - `llmail_*.json` `attack_attempt` appears as `'True'`, `'False'`, `'Unclear'`, and boolean `True` — normalise; drop `'Unclear'`.
  - `redteam_dataset.v2.json` — filter `sample["input"]["vulnerability"] == "goal_hijacking"`.
  - `train.tsv` — pick the column by `data_type`: `vanilla` for `vanilla_*`, `adversarial` for `adversarial_*`.
  - Do **not** use the old CSV's `source_channel` for Indirect sub-types (section 2d).

🟡 **Task 17** — Unit-test the adapters — at least one assertion per source file, covering all 3 classes and all 8 sub-types, asserting both `label_3class` and `subtype`.

🟡 **Task 18** — `preprocessing/prepare_dataset.py` — run every adapter, concatenate, then **deduplicate on normalised `text`** (strip + lowercase to compare; keep original casing in the output). Tag each row with `source` and `is_synthetic` (True for old-CSV and WildJailbreak rows, False for real-world sources). Write `ml/data/processed/clean.parquet`.

🟡 **Task 19** — Run it, confirm counts. Report unique rows per class and per sub-type; print before/after dedup for the old CSV (expect ~2,000,000 → ~1,041). Flag any sub-type under 200 unique examples as a weak spot for `MODEL_CARD.md`.

🟡 **Task 20** — `preprocessing/split_dataset.py` — stratified train/val/test on `label_3class`, with two hard rules: (1) the test set contains **only** `is_synthetic == False` rows; (2) no `text` value appears in more than one split. Also emit `synthetic_test.parquet` for comparison reporting.

🟡 **Task 21** — Run, confirm balance. Verify zero text overlap across splits and that the test set is 100% real-world. Down-sample Safe or compute class weights here.

🟡 **Task 22** — `preprocessing/make_sample.py` — stratified 1,000-row sample for git covering all 3 classes and all 8 sub-types. **Hand-check and exclude explicit/NSFW rows** (section 2e) — this is what teammates and the examiner will browse.

🟡 **Task 23** — Run, commit sample. Raw data and `clean.parquet` stay gitignored; only `sample_1000.csv` is committed.

### Training & Evaluation

🔴 **Task 24** — `training/tokenize_check.py` — sanity-check the DistilBERT tokenizer — **needs Task 18 merged** (`clean.parquet` must exist). Check the token-length distribution and decide `max_length` here; multi-turn conversations are long and will truncate badly at the default 128.

🟡 **Task 25** — Run it.

🟡 **Task 26** — `training/dataset.py` — PyTorch `Dataset` class, 3-class label as the primary target.

🟡 **Task 27** — `training/train.py` — model + `TrainingArguments`. Runnable both as a script and from the Colab notebook (section 3).

🟡 **Task 28** — Smoke-test on 100 rows, 1 epoch — run locally on CPU to prove the code path works before spending GPU time.

🟡 **Task 29** — Full training run **on Colab's T4** (section 3 — mount Drive first). Include a hyperparameter tuning pass (learning rate, epochs, batch size) before accepting anything below the >90%/F1>0.85 target.

🟡 **Task 30** — `training/evaluate.py` — accuracy / F1 / confusion matrix. **Per-class and per-sub-type**, not just aggregate. Report real-world and synthetic test sets as two separate, clearly-labelled numbers.

🟡 **Task 31** — Run, save `metrics.json`, check vs targets. **Headline = the real-world test score** (section 5); the synthetic score is comparison only and must never be presented as the project's accuracy.

🟡 **Task 32** — `MODEL_CARD.md` — must include: the taxonomy (section 1); the full source→label inventory (section 2); the dedup finding with before/after counts (section 2d); both scores with an explanation of why the real-world one is honest; every sub-type flagged weak in Task 19; and the fallback wording from section 4 if that tier was used.

🟡 **Task 33** — Save the checkpoint to Google Drive, record the shareable link in `MODEL_CARD.md` (weights stay out of git).

🟡 **Task 34** — *(Stretch)* Sub-type classifier head — second head predicting the 8 sub-types, trained only on rows whose 3-class label is Direct Jailbreak or Indirect Injection. It **will** be weaker than the 3-class head because several sub-types have far fewer examples — report its metrics separately.

### Inference Wrapper

🔴 **Task 35** — `inference/classifier.py` — `classify(text)` returning the 3-class label + confidence (+ sub-type if Task 34 is done) — **needs Task 33 merged**.

🟡 **Task 36** — Test on example prompts — at least one per 3-class bucket, taken from the **real-world** test set, not the synthetic CSV.

🟡 **Task 37** — Time it, confirm **<200 ms** (SRS §4.1).

> **🔴 Backend Task 56 (`POST /api/analyze-prompt`) depends on Task 35.** If ML is still running, Backend can stub `classify()` with a keyword rule and keep moving — see the master plan's dependency map.
