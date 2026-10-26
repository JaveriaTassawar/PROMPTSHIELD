# PromptShield FYP — Build Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to work through this task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build PromptShield — a web platform that detects, classifies, and mitigates prompt injection attacks against LLMs in real time, and teaches secure prompting through an avatar-guided simulation sandbox.

**Architecture:** Layered client-server system — React/Tailwind frontend, FastAPI backend, a fine-tuned DistilBERT classifier for detection, PostgreSQL (SQLite for local dev) for persistence. Rule/template-based mitigation and avatar guidance in v1 (no live OpenAI/LLaMA calls).

**Tech Stack:** React + Tailwind CSS, FastAPI, SQLAlchemy + Alembic, PostgreSQL/SQLite, PyTorch + Hugging Face Transformers (DistilBERT), JWT auth.

**Spec:** SRS — `docs/Phase1_SRS.docx`; SDS — `docs/SecurePrompting_Phase2.pdf` (both already in this repo's `docs/`). This file is the authoritative build plan derived from those two documents plus direct inspection of `llm_prompt_injection_jailbreak_dataset.csv`; see "Corrections & resolved decisions" below for where this plan overrides or fills gaps in the SRS/SDS.

## Team & Role Assignment

**This differs from the SRS/SDS team table** (which lists Faiqa=Frontend, Jawaria=Backend, Rana=ML). The team has since reassigned:

| Person | Owns | Notes |
|---|---|---|
| **Rana** | Frontend (all of it, solo) | Was originally ML in the SRS/SDS. Frontend work only depends on API *contracts* (documented in each task), not on ML or Backend being finished — see Dependency Map below for what can start immediately. |
| **Faiqa** | ML (paired with Jawaria) | Was originally Frontend in the SRS/SDS. Works with Jawaria through the full ML pipeline: dataset prep → training → evaluation → inference wrapper. |
| **Jawaria** | ML (paired with Faiqa) + Backend (solo) | Backend role unchanged from SRS/SDS. Additionally co-owns ML with Faiqa. Since ML and Backend share the Python/FastAPI environment and Jawaria is the handoff point where the trained model gets wired into `/api/analyze-prompt`, this pairing is natural — Jawaria has visibility into both sides of that join. |

**How Faiqa + Jawaria split ML work:** the ML pipeline (Tasks 13–37) is one sequential chain — you can't train before the dataset is split, can't evaluate before training finishes. Two people can't run genuinely parallel steps *inside* one script's dependency chain, but they can split by **stage**: e.g. one person drives the preprocessing scripts (Tasks 13–23) while the other studies the SRS/SDS classification requirements and drafts the training script structure (Task 26–27) against the *expected* output schema of Task 18, so both scripts are ready to run back-to-back once real `clean.parquet` exists. Pair-program or alternate ownership per task — either works, since each task is a single script with a single test-it-yourself checkpoint.

## Global Constraints

- Targets: **>90% accuracy / >0.85 F1** on the classifier (SRS §1.4 Objectives) — binding target, not aspirational. See Task 31 for the documented fallback.
- Latency: **<200ms** for the core detection/classification step, **<1s** end-to-end response (SRS §4.1 Performance Requirements).
- 3-class output only: **Safe / Direct Jailbreak / Indirect Injection** (SRS Abstract, SDS §3.4). Subtypes are a secondary, stretch-goal signal (Task 34), not required for the primary classifier.
- Tech simplified vs. the full SDS: **PostgreSQL only** (no MongoDB), **SQLite for local dev**, **no AWS deploy**, **no live OpenAI/LLaMA calls** — rule/template-based rewrite and avatar guidance instead. All of these are documented simplifications of the SDS, not omissions.
- **Out of scope for v1** (SRS §1.3 Out of Scope Features — restated here so nobody scope-creeps into these during the 101-task build):
  - No multimodal input support (image, audio, or video prompts) — text only.
  - No full enterprise/production-grade deployment or rollout.
  - No training of custom deep learning architectures beyond the predefined DistilBERT pipeline.
  - No continuous/streaming prompt monitoring — analysis is per-request, not an always-on stream.
  - Payment/subscription tiers are out of scope for v1 (documented as future work only, per SDS §12 Future Enhancements).
- Dataset: `llm_prompt_injection_jailbreak_dataset.csv` — 466MB, 2,000,000 rows, already inspected (see Task 15 findings below). Too large for git — stays local/gitignored; only a 1000-row sample gets committed (Task 22-23).

---

## Git Workflow

**Never push directly to `main`.** This repo already has one merged PR (`frontend/setup` → `main`, PR #1) — that's the pattern to continue, formalized below:

1. Before starting a task (or a small group of closely related tasks), create a branch off `main`: `git checkout main && git pull && git checkout -b <track>/<short-task-name>`.
   - Branch prefix by track: `ml/`, `backend/`, `frontend/`, `docs/`, `test/`. Example: `ml/label-mapping`, `backend/auth-endpoints`, `frontend/prompt-analyzer-ui`.
2. Commit as you go on that branch, following the existing "one task at a time, test it yourself" loop.
3. When the task (or task group) is verified working, push the branch and open a Pull Request into `main` on GitHub.
4. **At least one other team member reviews the PR before it's merged** — read the diff, pull it locally and run it if it's not trivial, leave comments on anything unclear. This is the "review like professionals" step — don't rubber-stamp your own PRs.
5. Merge via GitHub (squash or merge commit, either is fine) only after review approval. Delete the branch after merge.
6. Pull `main` before starting your next branch, so you're never branching off stale history.

This applies to every task below, including ML/Backend/Frontend work — no exceptions for "it's a small change."

---

## Corrections & resolved decisions (read before starting ML tasks)

This section exists because the original draft plan said "map to Safe / Direct Jailbreak / Indirect Injection" without saying *how* — and the raw dataset's `label` column does not contain those three names. These decisions were made by inspecting real example rows from the dataset (not guessed), and are now binding for Task 16.

### 1. Taxonomy — 3 classes, 8 sub-types (binding for Task 16)

This matches the SRS Abstract and the team's agreed taxonomy. **This is the authoritative label set** — it supersedes any earlier 9-sub-type mapping derived from the old dataset's raw technique labels.

| # | Top-level class | Sub-types |
|---|---|---|
| 1 | **Safe (Benign)** | _(none)_ |
| 2 | **Direct Jailbreak** | Policy Evasion · Multi-Turn Manipulation · Role Override · Persona Hijacking · System Prompt Overwrite |
| 3 | **Indirect Prompt Injection** | Document Embedding · Web Content Injection · Tool Output Injection |

The **primary classifier predicts the 3 top-level classes only**. The 8 sub-types are the secondary head (Task 34) and the value stored in the `AttackSubtype` table (Task 44).

### 2. Dataset inventory & label mapping → see [`../ml/TASKS.md`](../ml/TASKS.md)

**All 20 raw dataset files are downloaded and verified**, living at `C:\Users\DELL\Desktop\FYP\dataset\` (~1.6 GB, outside the repo, never committed). The full inventory — every file, its exact measured row count, its schema quirks, and which class/sub-type it maps to — is in **[`../ml/TASKS.md`](../ml/TASKS.md) section 2**. Don't duplicate it here; that file is the single source of truth for the mapping.

The headline facts that affect *other* tracks:

- **Scale:** ~600k+ real-world rows across the 3 classes. The largest contributors are BIPIA (70,000 rows, balanced 35k/35k) for Document Embedding, Microsoft llmail (160,741 + 37,303) for Web Content Injection, and WildJailbreak (261,559 rows) split across Safe and Policy Evasion.
- **The old 2M-row CSV is ~1,041 unique prompts** repeated ~192× each. It is a **minor** contributor; the real-world datasets carry the training. Task 18 deduplicates before anything else.
- **Thinnest sub-type: Role Override (158 examples).** Expect it to be the weakest class in the sub-type head — flag it in `MODEL_CARD.md` rather than hiding it.
- **Content warning:** the in-the-wild data contains explicit/NSFW prompts. Any example shown in the UI, the report, or the committed sample must be hand-picked (ML Task 22).

### 3. Training environment — Google Colab (binding for Tasks 27–29, 33)

Training runs on **Colab's free T4 GPU**, not a laptop — CPU training is ~10+ hours per run versus ~20–40 minutes on a T4, and several tuning passes are expected. Mount Google Drive and save checkpoints there (Colab wipes its disk after ~90 min idle). Keep `train.py` runnable as a script, not only as notebook cells, so it can be reviewed in a PR. Details in [`../ml/TASKS.md`](../ml/TASKS.md) section 3.

### 4. Evaluation rule (binding for Tasks 20, 30, 31)

The **headline accuracy/F1 must come from a real-world-only held-out test set** — never from a split of the synthetic old CSV, which measures memorisation rather than detection. Report the real-world and synthetic scores as two clearly-labelled numbers. Expect a genuine high-80s/low-90s, not a fake 97%. Details in [`../ml/TASKS.md`](../ml/TASKS.md) section 5.

### 3. Accuracy target — two-tier (binding for Task 31 and Task 32)

The SRS itself is internally inconsistent: §1.4 Objectives states ">90% accuracy, F1 > 0.85" as the target, while §2.5 Assumptions separately states the model "will achieve acceptable performance (≥80% accuracy)" as a baseline assumption, and the SDS's own UI wireframes show "≥80% Accuracy" as a badge/threshold. Resolution:

- **Primary, binding target:** >90% accuracy and >0.85 F1 (SRS §1.4). Task 31 evaluates against this first.
- **Documented fallback floor:** ≥80% accuracy (SRS §2.5) — only invoked if >90% is genuinely unreachable after reasonable hyperparameter tuning (see Task 29's tuning pass before declaring failure).
- If the fallback is invoked, it must be stated explicitly and visibly in `MODEL_CARD.md` (Task 32) — e.g. "Target was >90%/F1>0.85 per SRS §1.4; achieved fallback-tier performance of X% under SRS §2.5's documented ≥80% assumption; raised with advisor on [date]." This is never a silent substitution — the shortfall must be flagged to the advisor, not hidden in a metrics file nobody reads.

---

## Dependency Map

**Read this before deciding who works on what next.** Tasks in the same row-group can run fully in parallel (different people, different branches, no shared files). An arrow (→) means the task on the right cannot start until the task on the left is merged to `main`.

### Independent tracks (can start immediately, in parallel, right now)
- **ML Dataset Prep** (Tasks 13–23, Faiqa + Jawaria) — needs nothing but the raw CSV, which already exists locally.
- **Backend DB Models** (Tasks 38–49, Jawaria) — needs nothing but SQLAlchemy; schema doesn't depend on the trained model existing.
- **Frontend Scaffold & Auth UI** (Tasks 67–73, Rana) — needs nothing but the SDS's documented API contract for `/api/register` and `/api/login` (already specified in SDS §6.2); Rana can build and test the UI against mocked responses before real Backend endpoints exist.
- **Docs/scope work** — anything touching README, MODEL_CARD structure, etc. can happen anytime.

These three tracks can all be worked on simultaneously by different people from day one — that's the biggest scheduling win available in this plan.

### Sequential chains (cannot be parallelized internally)
- **ML pipeline**: 13→14→15→16→17→18→19→20→21→22→23 (dataset prep) → 24→25→26→27→28→29→30→31→32→33 (training/eval) → 34 (stretch) → 35→36→37 (inference wrapper). Each step consumes the previous step's output file — this is why Faiqa/Jawaria split by *stage*, not by running two stages at once.
- **Backend DB Models**: 38→39→40, then 41–49 can go in roughly any order since they're independent tables, but all must exist before Auth/Prompt Analysis endpoints that reference them.
- **Frontend**: 67→68 (scaffold) must finish before any UI task; 69→70→71→72→73 (auth) is sequential since each step builds on the last screen/wiring.

### Cross-track join points (this is where "we need each other's part" actually happens)
1. **ML → Backend, at Task 56**: `POST /api/analyze-prompt` needs `ml/inference/classifier.py`'s `classify(text)` function (Task 35) to exist and return the 3-class label + confidence. Backend can build and test everything up through Task 55 (Auth) without ML being done at all — Task 56 is the first hard dependency. If ML is running behind, Backend can stub `classify()` with a fake rule-based function (e.g., "contains 'ignore instructions' → Direct Jailbreak") to keep building Tasks 57–66 without blocking, then swap in the real classifier once Task 35 lands.
2. **Backend → Frontend, at Task 76**: "Wire Analyze button" needs `/api/analyze-prompt` (Task 56) actually responding. Frontend can build the entire UI shell for the Analyzer screen (Task 75) and even all three Detection Result state designs (Tasks 77–79) against a hardcoded/mocked JSON response shaped like the SDS §6.5 sample response, so Rana isn't blocked waiting on Backend — only the final wiring step (Task 76) needs the real endpoint.
3. **Backend → Frontend, throughout**: every "Wire X" frontend task (71, 72, 76, 82, 85, 89, 91) has this same shape — the corresponding screen/UI task can be built and demoed with mock data first, and only the wiring step is a hard blocker on the matching backend endpoint being merged to `main`.
4. **ML → Backend, at Task 62 (partial)**: seeding sandbox scenarios does NOT need the classifier — scenario scripts are hand-authored content, and real example prompts can be lifted straight from the downloaded datasets (Task 14). Only if a sandbox scenario needs live classification of user input mid-simulation would it depend on Task 35 — check each scenario's design before assuming this blocks on ML.
5. **Testing (93–101)** needs everything else merged — this is the one stage where no further parallelism helps; it's the integration checkpoint.

**Practical scheduling suggestion:** Rana can be productively building Frontend Tasks 67–75 and 77–79 (UI + mocked states) from day one, entirely in parallel with Faiqa/Jawaria's ML pipeline and Jawaria's Backend DB Models work — nobody needs to wait idle at the start.

---

## How we work

- One task at a time, numbered #1–#101 below.
- Loop for every task: whoever's driving says what they'll build → builds it on a feature branch (see Git Workflow above) → **the other person(s) test it themselves** (exact run/expect instructions given) → once confirmed, open a PR, get it reviewed, merge → check the task off here → move to the next task.
- This file is `tasks/MASTER_PLAN.md` inside the cloned repo, so progress is visible to the whole team. The root-level `PLAN.md` in the parent folder mirrors this file; update both when either changes.
- **Per-task working notes:** when you start a task, create a small `task.md` inside the folder that task's work lives in (e.g. `ml/preprocessing/task.md` while working through Tasks 13–23, `backend/app/task.md` while working through DB Models, `frontend/src/task.md` while working through a UI task group). Use it to jot down what you're doing, decisions made mid-task, things you tried that didn't work, and anything the reviewer should know — this is scratch/working documentation local to that folder, not a replacement for this file. Once the task is verified and merged, either delete that `task.md` or fold anything worth keeping into this file's task description or into `MODEL_CARD.md`/`README.md` as appropriate — don't let stale `task.md` files accumulate in the repo after their task is done.

## Repo structure & where the detail lives

This file is the **master plan** — it owns task numbering, the dependency map, roles, and the git workflow. Each track has its **own detailed task file** next to the code it describes:

```
FYP/
├── dataset/                    # ← ALL raw data lives HERE, OUTSIDE the repo (~1.6 GB, never committed)
└── PROMPTSHIELD/
    ├── frontend/
    │   └── TASKS.md            # Frontend detail — Tasks 67–92 (Rana)
    ├── backend/
    │   └── TASKS.md            # Backend detail — Tasks 38–66 (Jawaria)
    ├── ml/
    │   └── TASKS.md            # ML detail — Tasks 13–37 (Faiqa + Jawaria)
    ├── docs/
    │   ├── TESTING_TASKS.md    # Testing detail — Tasks 93–101 (whole team)
    │   └── (SRS / SDS files)
    ├── tasks/
    │   └── TASKS.md            # ← this file: the master plan
    └── README.md
```

| Track | Detailed file | Tasks | Owner |
|---|---|---|---|
| ML | [`../ml/TASKS.md`](../ml/TASKS.md) | 13–37 | Faiqa + Jawaria |
| Backend | [`../backend/TASKS.md`](../backend/TASKS.md) | 38–66 | Jawaria |
| Frontend | [`../frontend/TASKS.md`](../frontend/TASKS.md) | 67–92 | Rana |
| Testing | [`../docs/TESTING_TASKS.md`](../docs/TESTING_TASKS.md) | 93–101 | Whole team |

**Rule:** when a task's detail changes, edit the track file. When numbering, ownership, or cross-track dependencies change, edit this file. Keep the one-line summaries below in sync with the track files.

### Where the datasets live

All 20 raw dataset files stay at **`C:\Users\DELL\Desktop\FYP\dataset\`** — deliberately **outside** the git repo. They total ~1.6 GB and must never be committed. Scripts read from that path; `.gitignore` blocks the data extensions as a second line of defence. The only data file that ever enters git is the hand-checked `ml/data/sample_1000.csv` (ML Task 22).

---

## Tasks

**Status/marker legend** (used on every task line below):

| Marker | Meaning |
|---|---|
| ✅ | **Done** — merged to `main`, verified |
| 🔵 | **Ready now** — no blockers, can be started immediately |
| 🟡 | **In progress order** — just finish the task right before it first (same person/track, normal step-by-step order — not waiting on anyone else) |
| 🔴 | **Needs teammate's task first** — can't be started (or at least not finished/wired up) until a specific task from someone else's track is merged; that task is always named right there |

✅ Task 1 — Install Git for Windows — **done, verified**
✅ Task 2 — Configure git user.name and user.email — **done, verified**
✅ Task 3 — Clone https://github.com/JaveriaTassawar/PROMPTSHIELD into C:\Users\DELL\Desktop\FYP\PROMPTSHIELD — **done, verified**
✅ Task 4 — Create empty folders: frontend/, backend/, ml/, docs/, tasks/ — **done, verified**
✅ Task 5 — Write .gitignore — **done, verified**
✅ Task 6 — Write .env.example — **done, verified**
✅ Task 7 — README: project summary — **done, verified**
✅ Task 8 — README: how to run backend — **done, verified**
✅ Task 9 — README: how to run frontend — **done, verified**
✅ Task 10 — README: how to run ml pipeline — **done, verified**
✅ Task 11 — Copy SDS/SRS docs into docs/ — **done, verified**
✅ Task 12 — Initial commit + push — **done, verified** (commit 59f7b13)

### ML Pipeline (Faiqa + Jawaria) — Tasks 13–37
_Independent track — can start immediately. Branch prefix: `ml/`._
_**Full detail — dataset inventory, schema quirks, label mapping, Colab setup, evaluation rules — is in [`../ml/TASKS.md`](../ml/TASKS.md). Read that before starting any ML task.** The lines below are the index only._

**Dataset Prep**
✅ Task 13 — Create `ml/data/raw/`, `ml/data/processed/`, `ml/preprocessing/`, `ml/training/`, `ml/inference/` + `requirements.txt` — **done** (`7bdc06c`)
✅ Task 14 — `download_datasets.py` — copy/fetch all sources into `ml/data/raw/`; re-runnable, prints a summary — **done** (`e33dfb2`; later re-run for 3 added sources → **23 files**, see the addendum in [`../ml/TASKS.md`](../ml/TASKS.md))
✅ Task 15 — `inspect_sources.py` — row count, columns, 2 examples per source; confirm each matches the inventory — **done** (`d347f46`)
✅ Task 16 — `map_labels.py` — one adapter per source → `{text, label_3class, subtype, source}`, using the 3-class / 8-sub-type taxonomy — **done** (**22 adapters** after the second pass, all 8 sub-types populated)
✅ Task 17 — Unit-test the adapters — cover all 3 classes and all 8 sub-types — **done** (**62 fast + 6 slow tests**, all passing)
✅ Task 18 — `prepare_dataset.py` — run adapters, concatenate, **deduplicate on normalised text**, tag `is_synthetic`, write `clean.parquet` — **done** (**547,063 rows, 204.2 MB**)
✅ Task 19 — Run it, confirm counts; old CSV should collapse ~2,000,000 → ~1,041; flag sub-types under 200 examples — **done** (`verify_dataset.py`; old CSV 2,000,000 → 1,040 at 1,923× duplication; **Role Override flagged at 109**)

> _Tasks 14–19 were each run twice: once against the original 20 sources, then again after three more were added. The figures above are the **current** ones. The first-pass numbers and what changed between them are recorded in the addendum in [`../ml/TASKS.md`](../ml/TASKS.md)._
✅ Task 20 — `split_dataset.py` — stratified split; **test set = real-world rows only**; no text overlap across splits — **done** (train 453,935 · val 50,438 · test 42,690 · synthetic_test 42,690; both hard rules verified)
✅ Task 21 — Run, confirm balance and zero cross-split overlap; down-sample Safe or set class weights — **done** (both rules re-verified; train balance 1.33× so **weighting chosen over down-sampling**; weights persisted to `class_weights.json` for Task 27)
✅ Task 22 — `make_sample.py` — stratified 1,000-row sample for git, **NSFW rows excluded by hand** — **done** (997 rows, all 8 sub-types, 14,009 explicit rows filtered dataset-wide; still needs a human read-through)
✅ Task 23 — Run, commit sample (raw data + `clean.parquet` stay gitignored) — **done** (997 rows, 374 KB; ignore rules verified three ways, exactly one file staged)

> **🎉 Dataset Prep complete — Tasks 13–23 all done.** Next is Training & Evaluation, starting with Task 24.

**🔵 Backend DB Models (Task 38) and Frontend Scaffold & Auth (Task 67) can be worked on in parallel with all of the above — see Dependency Map.**

**Training & Evaluation** — _needs Task 18/20 output_
✅ Task 24 — `tokenize_check.py` — tokenizer sanity check; decide `max_length` here — **done** (**MAX_LENGTH = 512**, DistilBERT's ceiling; truncates 15.3% of rows vs 43.1% at the default 128 — Multi-Turn Manipulation's median row exceeds 512, logged for `MODEL_CARD.md`)
✅ Task 25 — Run it — **done** (exit 0; `MAX_LENGTH` confirmed importable for Tasks 26/27)
✅ Task 26 — `training/dataset.py` — PyTorch Dataset class, 3-class label as the primary target — **done** (lazy tokenization, label order pinned as a constant, `token_type_ids` dropped for DistilBERT compatibility)
✅ Task 27 — `training/train.py` — model + TrainingArguments; runnable as a script **and** from the Colab notebook — **done** (all 4 sub-steps pass; class weights bound **by name** not file order — the naive `.values()` read would have up-weighted Safe; `fp16` derived from CUDA so one file serves laptop and T4; eval on `val` never `test`; `accelerate` was missing and is now pinned. **Construction checks only — no training step has run yet, so Task 28 is not optional**)
✅ Task 28 — Smoke-test on 100 rows, 1 epoch, locally on CPU before spending GPU time — **done** (13 steps in 2m 04s; losses `1.095 → 1.078`, eval `1.055`, **no `nan`/`inf`** anywhere in `log_history`. Loss sitting near `ln(3)≈1.099` is correct for 100 rows — this tests plumbing, not learning. **Proved the weighted loss actually executes**: weighted vs unweighted differ on the same batch, so class weights reach the optimiser. Checkpoint reloads with `out_features==3`; nothing entered the repo)
✅ Task 29 — Full training run **on Colab's free T4** (mount Drive first) + hyperparameter tuning pass — **done** (Faiqa) (2 runs compared; best `run_01/checkpoint-28371`, val loss 0.05065. **Overfits after epoch 1** — loss rises 0.05065 → 0.05366 → 0.05843, so epoch 1 selected and 3 epochs is the wrong setting. Added `resume_from_checkpoint` and `validate_checkpoint.py`. Its 98.54% is validation-set and weighted — the honest 99.11% came from Task 30's real-world set)
✅ Task 30 — `training/evaluate.py` — accuracy/F1/confusion matrix, **per-class and per-sub-type**, real-world and synthetic reported separately — **done** (Faiqa) (**99.11% accuracy / 0.9911 F1 on the real-world held-out test set — clears the >90% / F1 >0.85 target**. All 5 sub-steps plus 4 unasked-for unit tests; suite 66 passed / 0 failed. **Per-sub-type exposed Persona Hijacking at 84.40%** — the real weak point, for `MODEL_CARD.md`. **Synthetic scored 98.91%, *lower* than real-world, contradicting the plan's earlier prediction** — cause is class mix, 9 Indirect rows vs 27,001)
✅ Task 31 — Run, save `metrics.json`. **Headline = real-world test score**; synthetic is comparison only — **done** (Faiqa) (**TARGET MET: 99.11% accuracy / 0.9911 F1 vs the required >90% / >0.85 — the §2.5 fallback is NOT invoked**. Machine-generated JSON in `ml/results/`; verified three ways including an independent re-run on a stratified sample. **Two figures for Task 32 that are in the JSON but not her write-up: macro F1 0.9756** (vs weighted 0.9911 — Direct Jailbreak is 0.9420), and **244 of 381 errors are Safe flagged as Direct Jailbreak**, the single biggest failure mode)
✅ Task 32 — `MODEL_CARD.md` — taxonomy, source inventory, dedup findings, both scores, weak sub-types, fallback wording if used — **done** (Faiqa) (982 lines, all 6 sub-steps; carried macro F1 0.9756 and the 244 false positives without chasing. 32.6 a no-op — target met outright. §19.7 added after review for the sub-type head's Role Override failure)
✅ Task 33 — Save the checkpoint to Google Drive, record the link in `MODEL_CARD.md` (weights stay out of git) — **done** (Faiqa) (**link opened and verified** — complete self-contained checkpoint, 10 files including the tokenizer, which Task 35 needs so it does not have to guess which one produced the weights)
✅ Task 34 — *(Stretch)* Sub-type classifier head — 8 sub-types; metrics reported separately from the primary classifier — **done** (Faiqa) (8-class head over attack rows; suite 74 passed / 0 failed. **99.52% accuracy but macro F1 only 0.8283** — **Role Override scores 0.0000, never predicted, 0 of 18 correct**, on 83 training examples; 14 of the 18 land as Policy Evasion. Disclosed openly and written up in `MODEL_CARD.md` §19.7. Stretch goal, so the 3-class headline is unaffected — **quote macro F1, not the 99.52%**)

**Inference Wrapper** — _the ML→Backend handoff_
✅ Task 35 — `inference/classifier.py` — `classify(text)` → 3-class label + confidence (+ sub-type if Task 34 done) — **done** (Faiqa) (lazy model caching, paths from env so weights stay out of git. **Bug found in review and fixed**: raised on every attack prompt when the optional sub-type model was unset — safe prompts worked, attacks crashed, which would have been backend 500s at Task 51. The fix also nearly got reverted because Tasks 36/37 were branched before it — **branch from `main`, not from a sibling branch**)
✅ Task 36 — Test on example prompts, one per 3-class bucket, from the **real-world** test set — **done** (Faiqa) (3/3 correct on held-out examples. **Then she hand-wrote 3 novel Indirect Injection prompts and the model got 0/3 — one classified Safe outright.** Documented as `MODEL_CARD.md` §19.8; this is the honest counterweight to the 99.11% headline)
✅ Task 37 — Time it, confirm **<200 ms** (SRS §4.1) — **done** (Faiqa) (**PASS with ~20× headroom** — 4.69 ms Safe, 10.88 ms attack. Safe prompts skip the sub-type model. The caching is load-bearing: first call costs ~1.2 s, so a backend reloading per request would miss the target sixfold)

**✅ ML TRACK COMPLETE — Tasks 13–37 all merged. Backend Task 56 is unblocked: `classify()` exists and works, no stub needed.**

---

### ML results — what to claim, and what not to

_Read this before writing the report or the viva slides. All figures measured, sources in `ml/results/`._

| Claim | Figure |
|---|---|
| **Headline (SRS §1.4 target: >90% / F1 >0.85)** | **99.11% accuracy · 0.9911 weighted F1** — PASS |
| More representative | **macro F1 0.9756** — classes weighted equally |
| Latency (SRS §4.1 target: <200 ms) | **4.69 ms** Safe · **10.88 ms** attack — PASS |
| Sub-type head (stretch) | 99.52% accuracy but **macro F1 only 0.8283** |

**Composition-capped re-score** (`training/evaluate_balanced.py` → `results/metrics_balanced.json`). Capping each sub-type at 1,000 rows **and** each source at 400 within a sub-type drops Web Content Injection from 51.4% of the set to 16.1%. On the resulting 4,957 rows:

| | Full test set | Composition-capped |
|---|---:|---:|
| Accuracy | 99.11% | **97.14%** |
| Weighted F1 | 0.9911 | **0.9714** |
| Macro F1 | 0.9756 | **0.9731** |

**The model holds up.** Removing the easy bulk costs about 2 points, not 10 — so the headline is flattered by composition but not hollow, and **both figures clear the SRS >90% / F1 >0.85 target**. That is a stronger claim than either number alone: performance survives a test set no single sub-type or source dominates.

Macro F1 barely moves (0.9756 → 0.9731), which is the expected result and a useful cross-check — macro already weighted the classes equally, so capping mostly confirms what it was already reporting.

**Three caveats that must travel with the headline.** Stating these first is what makes the result credible; being caught by them is what makes it look overclaimed.

1. **The test set flatters the number.** 51.4% of its 42,690 rows are Web Content Injection, all from Microsoft llmail, and the model scores 100.00% on them. Over half the headline is one easy category from one source.

2. **No unseen sources.** Test rows are unseen *rows*, but every one of the 20 source datasets also appears in training. This measures generalisation to new examples of familiar data, not to new data.

3. **Novel attacks exposed the gap (Task 36).** Three hand-written Indirect Injection prompts: **0 of 3 correct**, one classified **Safe**. `MODEL_CARD.md` §19.8.

**Also disclose:** 244 of 381 errors are Safe prompts flagged as Direct Jailbreak (64% of all errors — the failure a live demo surfaces), and **Role Override is never predicted** by the sub-type head (0 of 18, on 83 training examples).

**Honest one-line summary:** _"99.11% on our held-out set. That set is 51% one easy category, so we re-scored it with every sub-type and source capped — 97.14%, still clearing the target. The real limitation is generalisation: on hand-written novel indirect attacks we scored 0 of 3."_

**Persona Hijacking is the consistent weak point** — **84.40% on both** the full and the capped set, the only sub-type with a meaningful sample that stays below 90%. Pair it with the Task 36 novel-prompt result when discussing limitations: both point at the same underlying thing, that the model leans on surface wording more than on the structure of an attack.

### Backend (Jawaria) — DB Models
_Independent track — can start immediately, in parallel with ML. Branch prefix: `backend/`._

✅ Task 38 — Scaffold FastAPI app, health route — **done** (10 tests pass; `/health`, `/`, `/docs`, `/openapi.json` all 200. `create_app()` factory — **every later router must be included inside it**, a route added after it returns attaches only to the module-level app and 404s in tests. Config **refuses to boot** with the placeholder JWT secret outside development. CORS from `CORS_ORIGINS`, not `*`. **Found: `.env.example` says `MODEL_PATH` but the ML wrapper reads `PROMPTSHIELD_MODEL_PATH` — `Settings` accepts either; fix the example file at Task 56**)
✅ Task 39 — SQLAlchemy engine + session (SQLite) — **done** (21 tests pass. Session closes in a `finally`, verified through FastAPI — a 500 from one endpoint leaves the pool healthy for the next request; a trailing `close()` would instead hang under load. `check_same_thread` applied to SQLite only, since it is a `TypeError` on psycopg2. `Base` is 2.x `DeclarativeBase` for the typed models in 41–45. **Task 40 note: Alembic autogenerate reads `Base.metadata`, so every model must be imported in `app/models/__init__.py` or migrations will not see it**)
✅ Task 40 — Alembic init — **done** (30 tests pass; baseline `c3a2d1223098`, upgrade/downgrade both verified. **`alembic.ini`'s `sqlalchemy.url` left deliberately blank** — `env.py` sets it from `settings.database_url`, proven by `DATABASE_URL=...proof_override.db` creating that file instead. A URL left in the ini would make a deployment migrate SQLite while the app used Postgres, with nothing failing. `render_as_batch` on for SQLite since it cannot `ALTER` columns; `compare_type` on since type changes are otherwise undetected. **`app/models/__init__.py` must import every model** or autogenerate emits an empty migration and the table is silently missing)
✅ Task 41 — Model: User — **done** (45 tests pass, migration `49db872b27a3`, upgrade/downgrade verified. **Column named `password_hash`, not `password`** — the plan said `password`, which invites storing plaintext at the Task 50 call site and would pass every test. Email case-folded via `normalise_email()`, since a UNIQUE index alone treats `Jawaria@` and `jawaria@` as two accounts — **Task 50 must normalise on login too**. Role CHECK-constrained to the four Task 55 values so a typo cannot silently strip access. Added `is_active` so an admin can disable an account without deleting history the Tasks 60–63 analytics need)
✅ Task 42 — Model: Prompt — **done** (59 tests pass, migration `2ec02dd6e931`. **⚠️ Found that SQLite was silently ignoring every foreign key** — it ships with `PRAGMA foreign_keys=OFF` per connection, so orphan rows inserted cleanly; proven and fixed with a connect listener in `database.py`. Would have worked locally and broken on Postgres, which enforces FKs unconditionally. `ondelete=SET NULL` not CASCADE, so deleting a user anonymises prompts rather than destroying the history Tasks 60–63 aggregate. `prompt_text` is `Text` — real attacks reach 3,923 tokens and a VARCHAR cap would truncate the long persona/multi-turn prompts. `status` CHECK-constrained)
✅ Task 43 — Model: AnalysisResult — **done** (79 tests pass, migration `35be3efd8cb0`. **The 3-class labels are duplicated from the ML package rather than imported** — importing would pull torch into the API process — **with a test that parses `ml/training/dataset.py` and fails on drift in either direction**; verified it catches an added label. Without it the classifier could return a label the CHECK rejects and every attack analysis would 500. `confidence_score` constrained to 0..1 so a percentage written for a probability cannot silently skew every average. `prompt_id` UNIQUE — one analysis per prompt, else the dashboard double-counts. FK CASCADEs here, unlike Prompt→User, because an analysis without its prompt is meaningless. **`severity_level` values had to be invented — the plan only ever shows "High"**)
✅ Task 44 — Model: AttackSubtype — **done** (101 tests pass, migration `926713d73a9c`. 8 sub-type strings duplicated from the ML package with a drift test — **which caught a real failure on first run** (my regex assumed a tuple, the ML file uses a list). `SUBTYPE_PARENT` + `is_valid_for()` stop "Policy Evasion" being stored under an Indirect Injection analysis, which a plain CHECK would accept. **`UNRELIABLE_SUBTYPES` encodes the Role Override finding in code** — 0.00 F1, never predicted, 14 of 18 land as Policy Evasion — so Task 56 and the UI can qualify it rather than trusting it. Separate nullable `confidence`, since the sub-type head is a different model) (subtype_name stores one of the 8 sub-type names from "Corrections" section 1 — the 5 Direct Jailbreak ones or the 3 Indirect Injection ones; nullable, since Safe results have no sub-type)
✅ Task 45 — Model: MitigationAction — **done** (115 tests pass, migration `da76a18a6ead`. **All five DB models complete.** This FK is deliberately NOT unique, unlike Tasks 43/44 — one prompt can be warned about and then rewritten, and forcing one row would overwrite the audit trail this table exists for. A `rewriting` action with no rewritten text is CHECK-rejected, since that is a bug not a state. `Prompt.prompt_text` is never overwritten — the original is what the analytics and any audit need)
✅ Task 46 — Model: SafeSuggestion — **done** (126 tests pass, migration `d08f96bbb4b6`. **Resolved an overlap with Task 45**: a `rewriting` MitigationAction also stores a rewritten prompt, so two tables could hold "a safer version". The split is now explicit — MitigationAction is the audit log of what the system *did*; SafeSuggestion is the teaching advice, and **the API `safePromptSuggestion` field reads from SafeSuggestion**. `suggestion_reason` is NOT NULL, since a suggestion without reasoning is a rewrite not a lesson)
✅ Task 47 — Model: AvatarGuidance — **done** (138 tests pass, migration `b750a18e0179`. **⚠️ Found the frontend does not consume this table yet** — `AriaGuidancePanel.jsx` renders fixed per-class copy from its own config and only calls the backend at Task 82, so Aria currently says the same thing for every Direct Jailbreak. **Task 56 must treat guidance as optional**, like sub-type. Also: the frontend guidance object is richer (`summary/why/nextSteps/do/dont/keyDefence`) than this table`s two fields — **Task 82 must flatten or extend**. `displayed_at` records when the user *saw* it, not creation, so the analytics can tell whether anyone reads it)
✅ Task 48 — Model: SimulationSession — **done** (162 tests pass. NULL `outcome` is a real state — "in progress", distinct from `abandoned`. `end_time >= start_time` CHECK-enforced, else the analytics get negative durations. `difficulty` reuses the frontend`s Beginner/Intermediate/Advanced so Task 62 needs no remapping. **This FK CASCADEs unlike Prompt→User** — a session is personal progress, not evidence)
✅ Task 49 — Model: LearningProgress — **done** (**all nine DB models complete**. `(user_id, module_name)` UNIQUE, else re-opening a module inflates every completion count. `completed_at` must agree with `comp_status` both ways — **and that CHECK caught a real bug in my own `mark_complete()`**: SQLAlchemy autoflush fires between two assignments, so setting status before timestamp briefly hit the DB in the forbidden state. **Set `completed_at` first**)

### Backend (Jawaria) — Auth Endpoints
_Depends only on Task 41 (User model), not on ML._

✅ Task 50 — POST /api/register (+hash password) — **done** (179 tests pass; verified live. **⚠️ Swapped passlib for bcrypt directly** — passlib 1.7.4 reads `bcrypt.__about__` which bcrypt 5.0 removed, so every hash call raised; passlib last released 2020. Same `$2b$` stored format, no migration needed. **bcrypt`s 72-byte limit is rejected not truncated** — two long passwords sharing a prefix would otherwise unlock each other. Response lists fields explicitly so a column added later cannot leak. **✅ privilege escalation found and FIXED — anyone could register as `admin` by posting the role directly; now validated against `SELF_ASSIGNABLE_ROLES`. Also found the frontend offers `organization`, which the CHECK rejected — added, via a **hand-written** migration because **Alembic does not diff CHECK constraints** and autogenerate produced an empty file**)
✅ Task 51 — Reject duplicate email with **409** — **done** (409 not 400: the request was well-formed and failed on existing state, and the frontend must distinguish "email taken" from "check your details". Pre-check **and** a caught IntegrityError, so the two-request race does not 500 the loser — rare on SQLite, real on Postgres. Case-insensitive via `normalise_email()`)
✅ Task 52 — POST /api/login (JWT) — **done** (199 tests pass. **Same 401 for unknown email and wrong password**, so the endpoint cannot enumerate accounts — and the password is verified even when no user matched, since returning early is measurably faster and enumerable by timing. Deactivated account gets 403, but only after the password checks out, else the 403 reveals the account exists. `sub` is a string per RFC 7519; `decode_token()` returns None rather than raising. Forged-signature and payload-swap tests included. **⚠️ Task 55: role travels in the token, so a demotion lags until expiry — read from the DB if immediate revocation is needed**)
✅ Task 53 — Reject wrong password — **done** (delivered with Task 52 — same status *and* same detail string for both cases, plus timing equalisation)
✅ Task 54 — GET /api/profile (JWT-protected) — **done** (215 tests pass. **Takes no `user_id` parameter on purpose** — one that did would need an authorisation check to stop user 1 reading user 2, and forgetting it is among the commonest API bugs; reading the id from the token makes it unexpressible. Missing header returns 401 not FastAPI`s default 403. **Deactivation takes effect on the next request**, not at token expiry)
✅ Task 55 — Role field, reusable dependency — **done** (`require_roles()` factory keeps the allowed set beside the endpoint. **⚠️ Resolved the Task 52 staleness warning: the role is read from the DB, never the token** — a demoted admin loses access on the next request, and a correctly-signed token *claiming* admin is still refused. 403 not a concealing 404, since the routes are in the OpenAPI schema anyway)

**🔴 Frontend Tasks 71–73 (wiring Register/Login/route guard) depend on Tasks 50/52/54 being merged. Frontend UI-only Tasks 69–70 do not — see Dependency Map join point #3.**

### Backend (Jawaria) — Prompt Analysis Endpoints
_Task 56 is the hard ML dependency — see join point #1 above._

✅ Task 56 — POST /api/analyze-prompt — **done** (232 tests pass. **torch is deliberately NOT in the backend venv** — the import is lazy and a missing model is **503, not a startup crash**; the suite stays at ~50s and the API runs without 2 GB of ML dependencies. Verified against the real model from the ML venv: Safe/Direct Jailbreak both correct, no taxonomy drift. **The prompt is stored before classification** so a model failure does not lose it. One transaction for prompt+analysis+subtype. Oversized input 422 at the edge. `.env.example` corrected)
✅ Task 57 — Store AnalysisResult row — **done** (delivered with Task 56; prompt + analysis + sub-type commit as one transaction so a partial write cannot leave an analysed prompt with no analysis)
✅ Task 58 — Test with jailbreak-style prompt — **done** (`test_stored_row_matches_the_response` compares the stored row against the returned body field by field — checking each separately can both pass while they disagree)
🔵 Task 59 — POST /api/safe-prompt
🟡 Task 60 — POST /api/avatar-guide
🟡 Task 61 — GET /api/history

### Backend (Jawaria) — Simulation / Analytics / Admin

🔵 Task 62 — Seed 3-5 sandbox scenarios covering a spread of the 8 sub-types. Scenario scripts are hand-authored narrative content, so this does not depend on ML — real example prompts can be lifted from the SafeMTData multi-turn conversations and the Microsoft llmail submissions once Task 14 has downloaded them. Only becomes 🔴 (pending Task 37) if a scenario needs live classification of free-text the user types mid-simulation.
🟡 Task 63 — POST /api/simulate-attack
🟡 Task 64 — GET /api/dashboard
🟡 Task 65 — GET /api/admin/users (403 for non-admin)
🟡 Task 66 — Confirm error status codes

### Frontend (Rana) — Scaffold & Auth
_Independent track — can start immediately, in parallel with ML and Backend. Branch prefix: `frontend/`. UI tasks (67-70) need no backend; wiring tasks (71-73) need Backend Auth (50-55) merged._

🔵 Task 67 — Scaffold Vite + React
🟡 Task 68 — Tailwind config
🟡 Task 69 — Login page UI
🟡 Task 70 — Register page UI
✅ Task 71 — Wire Register — **done** (posts `name`/`email`/`password`/`role`, then signs in with the same credentials so the user does not type them twice. 409 and 422 are unwrapped into a readable message)
✅ Task 72 — Wire Login (JWT storage) — **done** (axios interceptor attaches the token; a 401 clears the session but a **403 does not**, else an admin visiting one forbidden page gets logged out. The interceptor notifies a handler rather than navigating, keeping the HTTP client independent of the router. **⚠️ `localStorage` is a documented trade-off** — survives refresh, readable by any script, so XSS becomes a stolen session)
✅ Task 73 — Route guard — **done** (**the stored token is verified against `GET /api/profile` before it is trusted** — it may be expired or the account deactivated since. `status` is three-valued, not boolean: with a boolean the first render after F5 looks like logged-out and the guard bounces an authenticated user to Login — the commonest bug in hand-rolled guards)

### Frontend (Rana) — Prompt Analyzer & Detection Result
_UI tasks (74-75, 77-79) can be built against a mocked JSON response shaped like SDS §6.5's sample and don't need to wait on Backend. Only Task 76 (wiring) needs Task 56 merged — see join point #2._

🔵 Task 74 — Dashboard shell
🟡 Task 75 — Prompt Analyzer UI
🔴 Task 76 — Wire Analyze button — **needs Task 56 merged**
🔵 Task 77 — Detection Result — Safe state _(buildable with mock data any time — doesn't strictly need Task 75 first, but grouped here for flow)_
🔵 Task 78 — Detection Result — Direct Jailbreak state (show sub-type from "Corrections" section 1 if available) _(buildable with mock data)_
🔵 Task 79 — Detection Result — Indirect Injection state _(buildable with mock data)_
🔴 Task 80 — Confirm all 3 states — **needs Task 76 wired for a real end-to-end check**, though the UI itself can be visually confirmed earlier with mock data

### Frontend (Rana) — Avatar Guidance & Simulation Lab

🔵 Task 81 — Avatar Guidance UI
🔴 Task 82 — Wire Avatar Guidance — **needs Task 60 merged**
🟡 Task 83 — Simulation scenario picker (include the Multi-Turn Manipulation scripted scenario from Task 62) — UI buildable with a mocked scenario list; real data **needs Task 62 merged**
🟡 Task 84 — Active Simulation screen
🔴 Task 85 — Wire simulation flow — **needs Task 63 merged**
🟡 Task 86 — Simulation Results screen

### Frontend (Rana) — Learning Hub, Analytics & Admin

🔵 Task 87 — Learning Hub screen
🔵 Task 88 — Analytics dashboard UI
🔴 Task 89 — Wire Analytics dashboard — **needs Task 64 merged**
🔵 Task 90 — Admin panel UI
🔴 Task 91 — Wire Admin users table — **needs Task 65 merged**
🟡 Task 92 — Profile & settings page

### Testing & Submission
_All prior tracks must be merged to main before this stage — the one part of the plan with no further parallelism._

🔴 Task 93 — TC-01, TC-02 (per SRS/SDS Test Design table — registration success + duplicate email) — **needs Tasks 50–51 merged**
🟡 Task 94 — TC-03, TC-04 (login success + invalid credentials)
🔴 Task 95 — TC-05, TC-06, TC-07 (Safe / Direct Jailbreak / Indirect Injection classification — use real-world example prompts from the held-out test set, hand-picked to avoid explicit content) — **needs Task 56 merged**
🟡 Task 96 — TC-08, TC-09, TC-10 (sub-type identification, safe prompt suggestion, avatar guidance)
🔴 Task 97 — TC-11, TC-12 (simulation sandbox access, admin dashboard analytics) — **needs Tasks 63–64 merged**
🟡 Task 98 — TC-13, TC-14, TC-15 (detection results stored, learning progress view, response time under load)
🟡 Task 99 — Fix failing cases
🟡 Task 100 — Finalize README
🟡 Task 101 — Tag release for submission
