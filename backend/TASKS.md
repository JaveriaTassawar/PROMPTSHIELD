# Backend Track — Detailed Tasks (Jawaria)

> Part of the PromptShield FYP. The master plan is [`../tasks/MASTER_PLAN.md`](../tasks/MASTER_PLAN.md) — it owns task numbering, the dependency map, team roles, and the git workflow. **This file owns the backend detail**: schema, endpoints, and per-task specifics for Tasks 38–66.
>
> Branch prefix for all work here: `backend/`

---

## Stack & conventions

- **FastAPI** + **SQLAlchemy** + **Alembic**.
- **SQLite for local dev**, **PostgreSQL** for anything deployed. No MongoDB — a documented simplification of the SDS.
- **JWT** auth (`python-jose` or `pyjwt`), passwords hashed with **bcrypt** (`passlib`).
- All request/response bodies are JSON. Pydantic models for every endpoint.
- `.env` drives config — see `.env.example` at the repo root. **Never commit real secrets.**

Run locally:
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
API docs at `http://localhost:8000/docs`.

---

## The 3-class contract (shared with ML and Frontend)

Every analysis response uses the taxonomy owned by [`../ml/TASKS.md`](../ml/TASKS.md):

- `prompt_type` — one of **`Safe`**, **`Direct Jailbreak`**, **`Indirect Injection`**
- `subtype` — one of the 8 sub-types, or `null` for Safe:
  - Direct Jailbreak → Policy Evasion · Multi-Turn Manipulation · Role Override · Persona Hijacking · System Prompt Overwrite
  - Indirect Injection → Document Embedding · Web Content Injection · Tool Output Injection
- `severity` — one of **`Low`**, **`Medium`**, **`High`**, **`Critical`**

### Severity vocabulary — pinned here (Task 43)

The SRS and SDS never enumerate severity; the sample below shows only `"High"`. These four values were therefore **chosen at Task 43** and are now the contract, enforced by a CHECK constraint on `analysis_results.severity_level`.

| Value | Meaning | Default for |
|---|---|---|
| `Low` | No threat detected | **Safe** |
| `Medium` | Attack pattern present but low-confidence or low-impact | — |
| `High` | Confident attack detection | **Direct Jailbreak**, **Indirect Injection** |
| `Critical` | Reserved for Task 57 mitigation to escalate | — |

**Frontend (Task 78) must use exactly these strings.** The frontend has not implemented severity yet — its code defers it to Tasks 78–82 and deliberately avoids inventing a vocabulary — so there is no existing conflict. Anything outside this set is rejected by the database, so a badge built against e.g. `"Severe"` would break on a real response.

**To change the set:** edit `SEVERITY_LEVELS` in `backend/app/models/analysis.py`, generate a migration, and update this table. One place, three steps.

Sample response shape (per SDS §6.5):
```json
{
  "classification": "Direct Jailbreak",
  "subtype": "Persona Hijacking",
  "severity": "High",
  "confidenceScore": 0.94,
  "safePromptSuggestion": "…",
  "avatarFeedback": "…"
}
```

---

## Tasks 38–66

Markers: ✅ done · 🔵 ready now · 🟡 in progress order (finish the one before it) · 🔴 needs a teammate's task first

### DB Models — independent track, start immediately

✅ **Task 38** — Scaffold the FastAPI app + `GET /health`. Structure: `app/main.py`, `app/models/`, `app/routers/`, `app/schemas/`, `app/core/`. Add `requirements.txt`. — **done**

_Server starts and serves: `/health`, `/`, `/docs` and `/openapi.json` all return 200. **10 tests pass.** FastAPI 0.146.0, SQLAlchemy 2.1.5, venv at `backend/.venv`._

_**`create_app()` is a factory, not a module-level app.** Tests build isolated instances, and importing `app.main` does not wire things up as a side effect._

_**Fixed while testing:** the `/` route was registered with `@app.get` *after* `create_app()` returned, so it attached only to the module-level instance — any app a test built would 404 there. Caught by `test_root_points_at_docs`; the route now lives inside the factory. Worth knowing because every later router must be included **inside** `create_app()` for the same reason._

_**Config refuses to boot unsafely.** `JWT_SECRET_KEY` defaults to the `.env.example` placeholder, and `Settings` raises on startup if that placeholder (or anything under 32 chars) is used when `ENVIRONMENT` is not `development`. A usable default would ship a signing key in the repo and make every token forgeable by anyone who read the source. Four tests cover this, including that `repr()` never prints the secret._

_**CORS is read from `CORS_ORIGINS`, not wildcarded** — defaults to the Vite (5173) and CRA (3000) dev ports for Rana's frontend. `allow_origins=["*"]` with credentials is rejected by browsers anyway, and would let any site call this API with a logged-in user's session once Task 47 lands._

_**Config inconsistency found and handled:** `.env.example` names the model path `MODEL_PATH`, but the ML wrapper (`ml/inference/classifier.py`) reads `PROMPTSHIELD_MODEL_PATH`. `Settings` accepts **either**, preferring the ML name, so the two tracks cannot disagree about one path at Task 56. The example file also points at `distilbert-promptshield`, which does not exist — the real checkpoint is `ml/models/run01_ck28371`. **Update `.env.example` at Task 56.**_

_`/health` reports `environment`, `database`, `model_configured` and `subtype_model_configured` rather than a bare `ok` — those are what tend to be wrong on a new machine, and surfacing them here beats discovering them via a 500 from Task 56. It touches neither the database nor the model, so it cannot fail for reasons unrelated to liveness._

_Verified gitignored: `backend/.venv/`, `backend/promptshield.db`, `__pycache__/`, `.env`. Exactly 10 source files stage._

✅ **Task 39** — SQLAlchemy engine + session (SQLite), with a `get_db()` dependency. — **done**

_`app/core/database.py` — engine, `SessionLocal`, `Base`, `get_db()`. **21 tests pass** (10 from Task 38 + 11 new). Self-check: `python -m app.core.database`._

_**The session closes in a `finally`, not after the `yield`.** Verified through FastAPI, not just in isolation — an endpoint that raises returns 500, and **the next request still succeeds**:_

```
GET /dbcheck -> 200 {'one': 1}
GET /dbfail  -> 500          (session still closed)
GET /dbcheck -> 200 {'one': 1}   <- pool healthy after the error
```

_With a trailing `db.close()` instead, that third request would eventually hang rather than error, once the pool drained. **That failure looks like a network problem and is miserable to trace**, so it is worth the test._

_**`get_db()` does not commit.** Each endpoint commits its own unit of work — a dependency that auto-committed would persist half of a failed operation._

_**Driver args are computed, not hardcoded.** SQLite needs `check_same_thread=False` because FastAPI runs sync endpoints in a threadpool and would otherwise raise *"SQLite objects created in a thread can only be used in that same thread"*. **That same argument is a `TypeError` on psycopg2**, so `_connect_args()` returns it only for SQLite — one module serves local SQLite and deployed Postgres with no edit. Two tests pin both directions._

_**`pool_pre_ping` is on for Postgres only** — a pooled connection dropped by the server while idle would otherwise fail one request before being replaced. Pointless against a local file._

_**`Base` is a SQLAlchemy 2.x `DeclarativeBase`**, not the legacy `declarative_base()` factory — SQLAlchemy 2.1.5 is installed and the models in Tasks 41–45 will use typed `Mapped[...]` annotations, which the old idiom mixes badly with._

_**`expire_on_commit=False`** so an endpoint can return the object it just saved without a second query against an already-closed session._

_**For Task 40:** Alembic autogenerate reads `Base.metadata`, so a model that is defined but never imported is **invisible to migrations**. `app/models/__init__.py` must import all five._

✅ **Task 40** — `alembic init`, wire it to the same `DATABASE_URL`, generate the first migration. — **done**

_`alembic.ini`, `alembic/env.py` rewritten from the template, baseline revision `c3a2d1223098`. **30 tests pass.** Verified: `upgrade head` applies, `downgrade base` rolls back, and re-upgrading works._

_**The URL comes from `app.core.config`, not `alembic.ini`.** The generated template hardcodes `sqlalchemy.url`; that line is now **deliberately blank** and `env.py` sets it from `settings.database_url` at runtime._

_Proven, not assumed — running with `DATABASE_URL=sqlite:///./proof_override.db` created **that** file rather than the default:_

```
DATABASE_URL=sqlite:///./proof_override.db alembic upgrade head
  -> proof_override.db created, 12288 bytes
```

_**Why this matters:** with a real URL left in `alembic.ini`, a deployment pointing `DATABASE_URL` at Postgres would still migrate the local SQLite file. The app and its schema would be on **different databases** with nothing failing. It would also commit credentials to the repo._

_**`render_as_batch` is on for SQLite.** SQLite cannot `ALTER` a column, so without batch mode the first migration in Tasks 41–45 that changes or drops one fails outright. Batch mode rebuilds the table instead. Harmless on Postgres._

_**`compare_type=True` and `compare_server_default=True`** — both off by default, meaning a changed column type or server default is silently **not detected** by autogenerate._

_**`app/models/__init__.py` created with the import requirement documented.** Autogenerate diffs against `Base.metadata`, and a model only registers there when its module is imported. A model missing from that file produces an **empty migration** — Alembic says "no changes detected", the table is absent, and the failure surfaces much later as `no such table`. `env.py` imports the package; Tasks 41–45 each add one line to it._

_Test coverage targets exactly those silent failures: that `alembic.ini` has no hardcoded URL, that `env.py` overrides it, that `app.models` is imported, that batch mode is on, and that every migration has both `upgrade()` and `downgrade()`._

**Commands:**
```bash
cd backend
.venv\Scripts\python.exe -m alembic upgrade head      # apply
.venv\Scripts\python.exe -m alembic current           # which revision
.venv\Scripts\python.exe -m alembic revision --autogenerate -m "add user"
.venv\Scripts\python.exe -m alembic downgrade -1      # roll back one
```

✅ **Task 41** — Model: **User** — `user_id` PK, `user_name`, `email` (unique, not null), `password` (hash), `role`, `created_at`. — **done**

_`app/models/user.py`, migration `49db872b27a3`. **45 tests pass** (14 new). Upgrade and downgrade both verified — the table and its two indexes drop and recreate cleanly._

_**The column is `password_hash`, not `password` — a deliberate change from the plan's wording.** Naming it `password` invites `User(password=payload.password)` at the call site in Task 50, which stores plaintext and passes every test, because nothing about a string column objects. `password_hash=` reads visibly wrong when handed a raw password. **For a project whose subject is security, a plaintext password column found by an examiner would undercut the whole thing.** Width is 60, bcrypt's fixed output._

_**Email is case-folded via `normalise_email()`.** `Jawaria@ucp.edu.pk` and `jawaria@ucp.edu.pk` are one mailbox, but a plain UNIQUE index treats them as two accounts — a duplicate-registration hole, plus a login that only works with the original casing. **Task 50 must call it on register AND login**; normalising only on write still locks the user out._

_**Role is CHECK-constrained** to `student` / `developer` / `researcher` / `admin`, the values Task 55 gates on. A typo like `"admim"` would otherwise write fine and silently strip that user's access with no error anywhere. A native ENUM would be stricter but needs a migration per value and SQLite has no real enum type, so CHECK is the portable choice. Tests cover every valid role plus a rejected invalid one._

_**`created_at` uses `server_default=func.now()`**, not a Python default — so the timestamp comes from the database for every row however it was inserted, including seed scripts and manual SQL, rather than from whichever app server happened to handle the request._

_**Added `is_active`** (not in the plan's field list): lets an admin disable an account without deleting it, which matters because the analytics in Tasks 60–63 still need that user's prompt history._

_`__repr__` omits the hash — `repr()` lands in logs and tracebacks._

_**The Task 40 import trap was handled:** `app/models/__init__.py` now imports `User`, and autogenerate correctly detected `users` plus both indexes. A test asserts the registration so a future model cannot silently miss it._

✅ **Task 42** — Model: **Prompt** — `prompt_id` PK, `user_id` FK, `prompt_text`, `submission_time`, `status` (`pending` / `analyzed` / `blocked`). — **done**

_`app/models/prompt.py`, migration `2ec02dd6e931`. **59 tests pass** (14 new)._

_**⚠️ FOUND AND FIXED: SQLite was silently ignoring every foreign key.** SQLite ships with `PRAGMA foreign_keys = OFF`, and the setting is **per-connection**. Without it, every FK in this schema — this one and Tasks 43–45 — is decorative. Demonstrated directly:_

```
WITHOUT the pragma:  INSERT prompts(user_id=99999)  ->  row inserted, FK ignored
WITH    the pragma:  INSERT prompts(user_id=99999)  ->  IntegrityError
```

_**Why this would have been nasty:** it works locally and fails on deploy. Postgres enforces FKs unconditionally, so orphan rows created during development would hit constraint violations on migration — or pass unnoticed and leave the Tasks 60–63 analytics joining against users that do not exist. Fixed with a `connect` event listener in `app/core/database.py`, guarded by a driver check so it does not fire for Postgres. A test asserts `PRAGMA foreign_keys == 1`._

_**`ondelete="SET NULL"`, not CASCADE, and `user_id` is nullable.** Deleting a user must not delete their prompts: the analytics aggregate over historical prompts, and CASCADE would silently rewrite past totals the moment an account was removed. SET NULL keeps the row and anonymises it. Task 41's `is_active` remains the preferred path — deactivate rather than delete._

_**`prompt_text` is `Text`, not `String(n)`.** The ML work measured real attacks at up to **3,923 tokens**, with Persona Hijacking averaging over a thousand. A VARCHAR cap would truncate exactly the long multi-turn and persona prompts the classifier is already weakest on — and MySQL truncates silently. No length cap here on purpose: **Task 56 should reject oversized input with a 422** before it reaches the database, where it would be a 500 instead._

_**`status` CHECK-constrained** to `pending` / `analyzed` / `blocked`. A typo (`"analysed"` — the British spelling is an easy slip) leaves a prompt in a state no query matches, invisible until a dashboard count looks wrong. Tested, including that exact misspelling._

_**Composite index `(user_id, submission_time)`** — Tasks 58 and 60 both ask "this user's prompts, newest first", which two single-column indexes do not serve._

_`__repr__` truncates the text to 40 chars: prompt content is user data and may be an attack payload, and `repr()` lands in logs._

✅ **Task 43** — Model: **AnalysisResult** — `analysis_id` PK, `prompt_id` FK, `detection_result`, `prompt_type` (**stores the 3-class label**), `severity_level`, `confidence_score`, `analysed_at`. — **done**

_`app/models/analysis.py`, migration `35be3efd8cb0`. **79 tests pass** (20 new). This is where the backend meets the ML track._

_**The 3-class labels are duplicated from `ml/training/dataset.py`, with a test guarding the drift.** Importing `LABEL2ID` directly would make the API depend on torch and pandas — a 30 MB service becoming a 2 GB one, with every endpoint waiting on a model import. So the three strings are restated, and `test_prompt_types_match_the_ml_label_set` parses the ML file and fails if the sets diverge in **either** direction. Verified it has teeth: adding a fourth label to the backend makes it fail._

_**Without that guard the failure mode is ugly** — the classifier returns a label the CHECK constraint rejects, and every attack analysis 500s at runtime while Safe prompts keep working._

_**`confidence_score` is CHECK-constrained to 0..1.** The classifier returns a softmax probability. Writing `94.0` where `0.94` belongs would not fail anywhere — it would silently make every confidence display and every analytics average wrong, in a way that looks plausible until someone checks. Both boundaries tested; `1.0` is allowed because the model genuinely returns it on obvious attacks._

_**`prompt_id` is UNIQUE — one analysis per prompt.** Without it, re-running analysis appends a second row and the dashboard counts that prompt twice. Re-analysis must update the existing row, and the constraint forces that to be a deliberate choice._

_**This FK CASCADES, unlike Prompt → User.** The asymmetry is intentional: a prompt survives its user (the history matters), but an analysis without its prompt has no text to display and nothing to explain. Both directions are tested._

_**`severity_level` had to be invented** — the plan shows only `"High"` in one sample response and never enumerates the set. Defined as `Low` / `Medium` / `High` / `Critical` with `DEFAULT_SEVERITY_BY_TYPE` mapping Safe→Low and both attack classes→High. **If the SRS or frontend pins a different vocabulary, this constraint is the one place to change.**_

_Also added `explanation` (nullable Text) for Task 57's mitigation note, and a composite index on `(prompt_type, analysed_at)` for the Tasks 60–63 "how many of each class over time" queries._

✅ **Task 44** — Model: **AttackSubtype** — `subtype_id` PK, `analysis_id` FK (nullable), `subtype_name` (**one of the 8 sub-types above**; null for Safe), `type_description`. — **done**

_`app/models/subtype.py`, migration `926713d73a9c`. **101 tests pass** (22 new)._

_**The 8 sub-type strings are duplicated from `ml/training/subtype_dataset.py`** with a drift test, same reasoning as Task 43. **The test caught a real failure on first run** — my regex assumed a tuple, the ML file uses a list. Names matched; the test was wrong. Fixed to accept either container, and verified it still fails on a renamed sub-type._

_**`SUBTYPE_PARENT` maps each sub-type to its 3-class label**, with `is_valid_for()` for Task 56 to call before storing. A plain CHECK on `subtype_name` alone would happily accept **"Policy Evasion" under an Indirect Injection analysis**, which is nonsense. Not enforced in the database because the parent class lives on another table and a cross-table CHECK is not portable — enforced at the write path instead._

_**⚠️ `UNRELIABLE_SUBTYPES` encodes the Role Override finding in code, not just prose.** ML Task 34 measured the sub-type head at **0.00 F1 on Role Override — never predicted, 0 of 18**, with **14 of those 18 landing as Policy Evasion**. So a stored `"Policy Evasion"` may in fact be Role Override._

_`is_reliable` and `reliability_note` expose that on the model, so **Task 56 and the UI can qualify a sub-type instead of presenting it with the same authority as the 3-class label**. See `ml/MODEL_CARD.md` §19.7._

_**`confidence` is a separate nullable column**, not reused from Task 43. The sub-type head is a *different model* with its own softmax; storing both in one column would conflate unrelated numbers. Nullable because the sub-type model is optional — `ml/inference/classifier.py` returns `subtype=None` when it is not configured._

_`analysis_id` stays nullable per the plan (a sub-type may be seeded for a Task 62 simulation before any analysis exists) but is **unique**, so one analysis cannot accumulate several rows and make the dashboard count one attack as many._

✅ **Task 45** — Model: **MitigationAction** — `mitigation_id` PK, `analysis_id` FK, `action_type` (warning / blocking / rewriting), `action_description`, `mitigated_prompt`, `action_time`. — **done**

_`app/models/mitigation.py`, migration `da76a18a6ead`. **115 tests pass** (14 new). **All five DB models are complete — Tasks 41–45.**_

_**This FK is deliberately NOT unique, unlike Tasks 43 and 44.** One prompt can be warned about *and then* rewritten, or blocked after a warning. Forcing one row would make the second action overwrite the first — and the audit trail is the entire point of this table. The relationship orders by `action_time` so it reads in the order things happened._

_**A `rewriting` action with no rewritten text is rejected** by a CHECK constraint. That is a bug, not a state, and without the constraint Task 57 could silently record an empty rewrite that the UI would render as a blank "safe version"._

_**`Prompt.prompt_text` is never overwritten.** The rewrite lives here; the original stays on the prompt, because the Tasks 60–63 analytics and any audit need what the user actually typed. Tested explicitly._

_**Append-only by convention** — nothing enforces it in SQL, but Task 57 should insert, never update. Rewriting history is exactly what an audit trail must not permit._

_`mitigated_prompt` is `Text` and nullable: a rewrite is as long as the original (~3,900 tokens measured in the ML work), and only `rewriting` produces one — keeping it null makes "was this rewritten?" answerable without comparing strings._

---

### ✅ DB Models complete — Tasks 38–45 all done

115 tests, 5 migrations, 5 tables. **Task 50 (`POST /api/register`) is unblocked** — it needed Task 41.

**Two things Task 50 must honour, both decided at Task 41:**
1. Hash with bcrypt into `password_hash`. The column is named that way so assigning a raw password reads wrong at the call site.
2. Call `normalise_email()` on **register and login**. Normalising only on write leaves the user unable to log in with different casing.



✅ **Task 46** — Model: **SafeSuggestion** — `suggestion_id` PK, `analysis_id` FK, `suggested_prompt`, `suggestion_reason`, `generated_at`. — **done**

_`app/models/suggestion.py`, migration `d08f96bbb4b6`. **126 tests pass** (11 new)._

_**⚠️ OVERLAP WITH TASK 45 — resolved here, read before writing Task 56 or 57.** `MitigationAction` with `action_type='rewriting'` also stores a rewritten prompt. Two tables can hold "a safer version of this prompt", and without a rule Task 56 would have two places to read `safePromptSuggestion` from and could pick differently in different endpoints._

| Table | Holds | Answers |
|---|---|---|
| `MitigationAction.mitigated_prompt` | what the system **did** | "what action was taken, and when" — audit log, append-only, several per analysis |
| `SafeSuggestion.suggested_prompt` | what the user **should have written** | "show me a better prompt" — teaching material, one per analysis |

_**The API's `safePromptSuggestion` field reads from `SafeSuggestion`.** A `rewriting` MitigationAction is written alongside when the system actually substituted text, and the two often agree — but one is a log entry and the other is advice. A test stores both and asserts they stay independently reachable._

_**`suggestion_reason` is NOT NULL.** The project exists to teach secure prompting; a suggestion with no explanation of *why* it is safer is a rewrite, not a lesson, and the Task 47 avatar would have nothing to narrate._

_`analysis_id` is unique — regenerating should update the row, not append a second one the API has to choose between._

_No CHECK compares the suggestion to the original (the original is on another table and cross-table CHECKs are not portable). **Task 57 should refuse to store a suggestion identical to the input.**_

✅ **Task 47** — Model: **AvatarGuidance** — `guidance_id` PK, `analysis_id` FK, `message_text`, `explanation`, `displayed_at`. — **done**

_`app/models/guidance.py`, migration `b750a18e0179`. **138 tests pass** (12 new)._

_**⚠️ CONTRACT MISMATCH FOUND — the frontend does not consume this table yet.** `AriaGuidancePanel.jsx` renders **fixed per-class copy** from `frontend/src/config/ariaGuidance.js`, whose own header states:_

> _"Fixed educational content written for each classification… It is **NOT** generated by a model or the backend and never refers to the specific prompt. **Task 82** will add guidance from `POST /api/avatar-guide`."_

_So Aria currently says the same thing for every Direct Jailbreak. This table is what lets Task 82 replace that with guidance about *this* prompt. Rows are stored but not displayed until then — correct order, since the backend must exist before the frontend can call it._

_**Two consequences for Task 56:**_
1. _**Treat guidance as optional in the response**, exactly as it already treats sub-type. Nothing breaks when the table is empty — there is a test for that._
2. _**The frontend's guidance object is richer than this table.** It has `summary / whyTitle / why / nextSteps[] / do[] / dont[] / keyDefence`; this table has `message_text` + `explanation`. **Task 82 must either flatten that shape into two fields or extend the table.** Flagged now rather than discovered then._

_**`displayed_at` is not a creation timestamp.** The plan names it `displayed_at`, so it records when the user actually *saw* the guidance — a different question from when it was generated, and the only way the Tasks 60–63 analytics can tell whether anyone reads it. `generated_at` records creation separately, and `mark_displayed()` is idempotent so re-serving does not overwrite the first-seen time._

_Both `message_text` and `explanation` are required: guidance with no explanation is a notification, not teaching, and teaching is the avatar's stated purpose in the project title._

✅ **Task 48** — Model: **SimulationSession** — `simulation_id` PK, `user_id` FK, `scenario_name`, `description`, `start_time`, `end_time`, `outcome`. — **done**

_`app/models/simulation.py`, migration `3b3e1cf60111` (shared with Task 49). **162 tests pass.**_

_**NULL `outcome` is a real state, not missing data** — "started, not finished", distinct from `abandoned`. One is a user still working, the other gave up, and the Tasks 60–63 analytics must not conflate them._

_**`end_time >= start_time` is CHECK-enforced.** Catches clock problems and transposed arguments; without it a session that ended before it began silently produces **negative durations** in the analytics._

_**`difficulty` reuses the frontend's existing labels** — `Beginner` / `Intermediate` / `Advanced` from `frontend/src/config/simulation.js`, which notes "Backend Task 62 may replace it". Same strings means Task 62 can seed scenarios with no remapping._

_**This FK CASCADEs, unlike `Prompt → User`.** Deliberate: a prompt is evidence the analytics aggregate over, so it survives its user anonymised; a training session is personal progress with no meaning detached from the person, and orphans would inflate completion counts for users who no longer exist._



✅ **Task 49** — Model: **LearningProgress** — `progress_id` PK, `user_id` FK, `module_name`, `comp_status`, `completed_at`. — **done**

_`app/models/progress.py`. **All nine DB models are now complete.**_

_**`(user_id, module_name)` is UNIQUE** — the schema's first composite unique constraint. Without it, re-opening a module appends a row and every completion count inflates: a progress bar reading over 100%._

_**`completed_at` must agree with `comp_status`, both directions.** A completed module must carry a timestamp; an unfinished one must not. Otherwise a module could read `in_progress` while holding a completion date, which Task 63 would count as finished._

_**⚠️ That constraint caught a real bug in my own code.** `mark_complete()` originally set the status first, then the timestamp. SQLAlchemy's **autoflush fires between two assignments**, so the row briefly hit the database as `completed` with a null timestamp and the flush failed. Fixed by setting the timestamp first. **Any code touching both fields must set `completed_at` before `comp_status`** — an ordering bug that would otherwise surface only intermittently, under load._

_`not_started` is stored explicitly rather than as a missing row, so "has this user opened this module?" and "have they finished it?" stay separate queries._

---

### ✅ All nine DB models complete — Tasks 38–49

162 tests · 8 migrations · 9 tables, all verified to tear down and rebuild cleanly. **Auth endpoints (Tasks 50–55) are next.**

### Auth Endpoints

🔴 **Task 50** — `POST /api/register` — hash the password with bcrypt, never store plaintext — **needs Task 41 merged**. Returns 201.

🟡 **Task 51** — Reject duplicate email with **409** (or 400 — pick one and keep it consistent; document it).

🟡 **Task 52** — `POST /api/login` — verify the hash, return a JWT. Token carries `user_id` and `role`.

🟡 **Task 53** — Reject wrong password with **401**. Same generic message for "wrong password" and "no such user" — don't leak which emails exist.

🟡 **Task 54** — `GET /api/profile` — JWT-protected; 401 without a valid token.

🟡 **Task 55** — Role field: `student` / `developer` / `researcher` / `admin`, enforced by a reusable dependency.

> **🔴 Frontend Tasks 71–73 (wiring Register / Login / route guard) depend on Tasks 50 / 52 / 54.** Frontend UI-only Tasks 69–70 do not.

### Prompt Analysis Endpoints

🔴 **Task 56** — `POST /api/analyze-prompt` — **needs ML Task 35 merged** (`ml/inference/classifier.py` → `classify(text)`).
  **Unblock trick:** if ML is still running, stub `classify()` behind an interface — e.g. a keyword rule ("ignore previous instructions" → Direct Jailbreak) — and keep building Tasks 57–66. Swap in the real classifier when Task 35 lands. Keep the stub in one file so the swap is a one-line change.

🟡 **Task 57** — Persist the `AnalysisResult` row (and the `AttackSubtype` row when a sub-type is returned).

🟡 **Task 58** — Test with a jailbreak-style prompt end to end; confirm the stored row matches the response.

🟡 **Task 59** — `POST /api/safe-prompt` — rule/template-based rewrite (no live LLM call in v1).

🟡 **Task 60** — `POST /api/avatar-guide` — template-based explanation keyed by `prompt_type` + `subtype`.

🟡 **Task 61** — `GET /api/history` — JWT-protected, returns the caller's own prompts + results, newest first, paginated.

### Simulation / Analytics / Admin

🔵 **Task 62** — Seed 3–5 sandbox scenarios spanning several of the 8 sub-types. Scenario scripts are hand-authored, so **this does not depend on ML** — real example prompts can be lifted from the downloaded datasets (SafeMTData multi-turn conversations, Microsoft llmail submissions). Only becomes 🔴 if a scenario needs live classification of free text mid-simulation.

🟡 **Task 63** — `POST /api/simulate-attack` — takes `scenario_id` + prompt, returns the simulation result, writes a `SimulationSession` row.

🟡 **Task 64** — `GET /api/dashboard` — aggregate stats: total analyses, counts per class, counts per sub-type, recent activity.

🟡 **Task 65** — `GET /api/admin/users` — **403 for non-admin**, driven by the Task 55 role dependency.

🟡 **Task 66** — Confirm error status codes across the API against SDS §6.4: 200, 201, 400, 401, 403, 404, 500.
