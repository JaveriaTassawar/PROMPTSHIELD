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
🔵 Task 20 — `split_dataset.py` — stratified split; **test set = real-world rows only**; no text overlap across splits — **next up**
🟡 Task 21 — Run, confirm balance and zero cross-split overlap; down-sample Safe or set class weights
🟡 Task 22 — `make_sample.py` — stratified 1,000-row sample for git, **NSFW rows excluded by hand**
🟡 Task 23 — Run, commit sample (raw data + `clean.parquet` stay gitignored)

**🔵 Backend DB Models (Task 38) and Frontend Scaffold & Auth (Task 67) can be worked on in parallel with all of the above — see Dependency Map.**

**Training & Evaluation** — _needs Task 18/20 output_
🔴 Task 24 — `tokenize_check.py` — tokenizer sanity check; decide `max_length` here — **needs Task 18 merged**
🟡 Task 25 — Run it
🟡 Task 26 — `training/dataset.py` — PyTorch Dataset class, 3-class label as the primary target
🟡 Task 27 — `training/train.py` — model + TrainingArguments; runnable as a script **and** from the Colab notebook
🟡 Task 28 — Smoke-test on 100 rows, 1 epoch, locally on CPU before spending GPU time
🟡 Task 29 — Full training run **on Colab's free T4** (mount Drive first) + hyperparameter tuning pass
🟡 Task 30 — `training/evaluate.py` — accuracy/F1/confusion matrix, **per-class and per-sub-type**, real-world and synthetic reported separately
🟡 Task 31 — Run, save `metrics.json`. **Headline = real-world test score**; synthetic is comparison only
🟡 Task 32 — `MODEL_CARD.md` — taxonomy, source inventory, dedup findings, both scores, weak sub-types, fallback wording if used
🟡 Task 33 — Save the checkpoint to Google Drive, record the link in `MODEL_CARD.md` (weights stay out of git)
🟡 Task 34 — *(Stretch)* Sub-type classifier head — 8 sub-types; metrics reported separately from the primary classifier

**Inference Wrapper** — _the ML→Backend handoff_
🔴 Task 35 — `inference/classifier.py` — `classify(text)` → 3-class label + confidence (+ sub-type if Task 34 done) — **needs Task 33 merged**
🟡 Task 36 — Test on example prompts, one per 3-class bucket, from the **real-world** test set
🟡 Task 37 — Time it, confirm **<200 ms** (SRS §4.1)

**🔴 Backend Task 56 (POST /api/analyze-prompt) depends on Task 35. If ML is still in progress, Backend can stub `classify()` with a keyword-rule fake to keep moving — see Dependency Map join point #1 — which downgrades Task 56 back to 🔵 in practice.**

### Backend (Jawaria) — DB Models
_Independent track — can start immediately, in parallel with ML. Branch prefix: `backend/`._

🔵 Task 38 — Scaffold FastAPI app, health route
🟡 Task 39 — SQLAlchemy engine + session (SQLite)
🟡 Task 40 — Alembic init
🟡 Task 41 — Model: User
🟡 Task 42 — Model: Prompt
🟡 Task 43 — Model: AnalysisResult (prompt_type field stores the 3-class label: Safe / Direct Jailbreak / Indirect Injection, per SDS §5.2 Analysis Result Table)
🟡 Task 44 — Model: AttackSubtype (subtype_name stores one of the 8 sub-type names from "Corrections" section 1 — the 5 Direct Jailbreak ones or the 3 Indirect Injection ones; nullable, since Safe results have no sub-type)
🟡 Task 45 — Model: MitigationAction
🟡 Task 46 — Model: SafeSuggestion
🟡 Task 47 — Model: AvatarGuidance
🟡 Task 48 — Model: SimulationSession
🟡 Task 49 — Model: LearningProgress

### Backend (Jawaria) — Auth Endpoints
_Depends only on Task 41 (User model), not on ML._

🔴 Task 50 — POST /api/register (+hash password) — **needs Task 41 merged (User model must exist)**
🟡 Task 51 — Reject duplicate email
🟡 Task 52 — POST /api/login (JWT)
🟡 Task 53 — Reject wrong password
🟡 Task 54 — GET /api/profile (JWT-protected)
🟡 Task 55 — Role field (student/developer/researcher/admin)

**🔴 Frontend Tasks 71–73 (wiring Register/Login/route guard) depend on Tasks 50/52/54 being merged. Frontend UI-only Tasks 69–70 do not — see Dependency Map join point #3.**

### Backend (Jawaria) — Prompt Analysis Endpoints
_Task 56 is the hard ML dependency — see join point #1 above._

🔴 Task 56 — POST /api/analyze-prompt (safe prompt test) — **needs Task 37 merged (or a stubbed classifier — see note above)**
🟡 Task 57 — Store AnalysisResult row
🟡 Task 58 — Test with jailbreak-style prompt
🟡 Task 59 — POST /api/safe-prompt
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
🔴 Task 71 — Wire Register — **needs Task 50 merged**
🔴 Task 72 — Wire Login (JWT storage) — **needs Task 52 merged**
🔴 Task 73 — Route guard — **needs Task 54 merged**

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
