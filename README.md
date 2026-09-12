# PromptShield

**Secure Prompting and Simulation-based Learning through Avatar Guidance** — S26CS038 FYP, University of Central Punjab.

PromptShield detects, classifies, and mitigates prompt injection attacks against LLMs in real time, and teaches safe prompting through an avatar-guided simulation sandbox. It classifies prompts as **Safe**, **Direct Jailbreak**, or **Indirect Injection** using a fine-tuned DistilBERT model, then applies mitigation (safe rewrite, warnings) and explains the risk to the user via an interactive avatar.

**Team**
- Faiqa Abid — Frontend & UI
- Jawaria Tassawar — Backend & Management
- Rana Shahzaib Naseem Khan — ML & Deployment

## Running the backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy ..\.env.example .env     # then fill in real values
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173` once running.

## Running the ML pipeline

```bash
cd ml
python -m venv .venv
.venv\Scripts\activate                     # Windows
pip install -r requirements.txt
python preprocessing/prepare_dataset.py    # cleans the raw CSV (not committed, see below)
python training/train.py                   # fine-tunes DistilBERT
python training/evaluate.py                # reports accuracy / F1
```

The full 2M-row training dataset is too large for git and is **not** committed — keep it locally at `ml/data/` (the path `prepare_dataset.py` expects). A small labeled sample (`ml/data/sample_1000.csv`) is committed for reference. Trained model weights are also excluded from git; see `ml/models/MODEL_CARD.md` for where they're hosted once trained.

See `tasks/MASTER_PLAN.md` for the full build plan and progress tracker. Per-track detail lives in `ml/TASKS.md`, `backend/TASKS.md`, `frontend/TASKS.md`, and `docs/TESTING_TASKS.md`.
