# Setup — running PromptShield on your machine

Windows instructions. On macOS or Linux, replace `.venv\Scripts\python.exe`
with `.venv/bin/python` throughout.

**Three things are not in the repo and you must get them separately:**

| | Why not in git | Where to get it |
|---|---|---|
| `.env` | holds secrets | copy `.env.example`, step 2 below |
| the trained model (268 MB) | over GitHub's 100 MB file limit | Drive link in `ml/MODEL_CARD.md` |
| the datasets (~1.6 GB) | far too large | only needed to retrain — skip unless you are doing ML work |

---

## 1. Clone

```bash
git clone https://github.com/JaveriaTassawar/PROMPTSHIELD.git
cd PROMPTSHIELD
```

---

## 2. Create `.env`

In the repo root, copy `.env.example` to `.env` and open it.

Change **one** line — generate your own JWT secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the output as `JWT_SECRET_KEY`. Everything else can stay as-is for
local work.

**`.env` is gitignored. Never commit it.** The placeholder in
`.env.example` is rejected at startup when `ENVIRONMENT` is not
`development`, so a real deployment cannot accidentally ship it.

---

## 3. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m alembic upgrade head
```

That last command creates the SQLite database and its nine tables. The
`.db` file is gitignored, so everyone has their own.

**Run it:**

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

→ API at **http://localhost:8000** · docs at **http://localhost:8000/docs**

**Check it:**

```bash
.venv\Scripts\python.exe -m pytest tests/ -q      # expect 254 passed
```

---

## 4. Frontend

Needs Node 18+ (`node --version`).

```bash
cd frontend
npm install
npm run dev
```

→ **http://localhost:5173/register**

Use `localhost`, **not** `127.0.0.1` — Vite binds IPv6 and
`127.0.0.1:5173` will appear dead when the server is fine.

Start at `/register`, not `/`. The root page is a logo with two links;
the app itself begins at register or login.

**Check it:**

```bash
npm run lint
npm run build
```

---

## 5. ML — only if you are working on the model

Separate virtual environment on purpose. `torch` and `transformers` are
about 2 GB, and the API does not need them: it imports the model lazily and
returns a clear 503 when it is absent.

```bash
cd ml
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest tests/ -q      # expect 81 passed
```

The raw datasets are **not** in the repo. You only need them to re-run
preprocessing or retrain — see `ml/TASKS.md` section 2 for the file list.

---

## 6. Optional — make the Analyzer return real classifications

Without this, `/api/analyze-prompt` returns **503** and the UI says the
model is not running. Everything else works.

1. Download `run01_ck28371` from the Drive link in `ml/MODEL_CARD.md`
   into `ml/models/`. You want this layout:

   ```
   ml/models/run01_ck28371/
     config.json
     model.safetensors        (268 MB)
     tokenizer.json
     tokenizer_config.json
   ```

2. Install the ML dependencies **into the backend venv**:

   ```bash
   cd backend
   .venv\Scripts\python.exe -m pip install torch transformers pandas pyarrow
   ```

3. Point `.env` at it — absolute path, forward slashes:

   ```
   PROMPTSHIELD_MODEL_PATH=C:/your/path/PROMPTSHIELD/ml/models/run01_ck28371
   ```

4. Restart the backend and open **http://localhost:8000/health**. You want:

   ```json
   "model_configured": true,
   "model_available": true
   ```

Leave `PROMPTSHIELD_SUBTYPE_MODEL_PATH` empty. The 8-class sub-type model
is optional and the API returns `subtype: null` without it.

---

## Running both together

Two terminals, both kept open. Closing a terminal stops that server — which
looks like a bug and is not one.

```bash
# terminal 1
cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload

# terminal 2
cd frontend && npm run dev
```

Then **http://localhost:5173/register** → register → dashboard → Analyzer.

CORS already permits ports 5173 and 3000.

---

## Git workflow — please follow this

```bash
git checkout main
git pull origin main          # ALWAYS, before branching
git checkout -b <track>/<short-name>
# ... work, commit ...
git push -u origin <track>/<short-name>
# open a PR on GitHub
```

Branch prefixes: `ml/`, `backend/`, `frontend/`, `docs/`, `test/`

**Never push to `main`.** A branch ruleset blocks it, and merging needs a
review.

### Branch from `main`, never from another feature branch

This has nearly cost us work twice:

- Tasks 36/37 were branched before a bug fix landed on Task 35's branch.
  Merging them in order would have **silently reverted the fix** — nothing
  would have failed.
- A frontend branch five weeks stale would have **deleted 1,848 lines** of
  ML work across 8 files, because it predated them.

Both were caught before merging. If your branch is behind:

```bash
git fetch origin
git rebase origin/main
git push --force-with-lease
```

`--force-with-lease`, not `--force` — it refuses if someone else pushed
meanwhile.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `127.0.0.1:5173` not responding | Vite binds IPv6. Use `localhost:5173`. |
| Root page has no content | It is a logo plus two links. Go to `/register`. |
| Analyzer says "model is not running" | Step 6 not done, or `.env` path wrong. Check `/health`. |
| `/api/analyze-prompt` returns 401 | Not logged in. Register first. |
| Import errors in VS Code | Wrong interpreter selected. Ctrl+Shift+P → *Python: Select Interpreter* → pick the venv for the folder you are editing. Two venvs exist. |
| `alembic` says "no changes detected" after editing a CHECK constraint | Alembic does not diff CHECK constraints. Write that migration by hand — see `dd6fb3d909b5`. |
| A route 404s in tests but works in the browser | It was registered after `create_app()` returned. Routers go **inside** the factory. |

---

## Where things are

| | |
|---|---|
| Task plan | `tasks/MASTER_PLAN.md` — owns numbering and dependencies |
| ML detail | `ml/TASKS.md` |
| Backend detail | `backend/TASKS.md` |
| Frontend detail | `frontend/TASKS.md` |
| Progress summary | `PROGRESS.md` |
| Model results & limitations | `ml/MODEL_CARD.md` |
