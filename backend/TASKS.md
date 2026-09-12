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

🔵 **Task 38** — Scaffold the FastAPI app + `GET /health`. Structure: `app/main.py`, `app/models/`, `app/routers/`, `app/schemas/`, `app/core/`. Add `requirements.txt`.

🟡 **Task 39** — SQLAlchemy engine + session (SQLite), with a `get_db()` dependency.

🟡 **Task 40** — `alembic init`, wire it to the same `DATABASE_URL`, generate the first migration.

🟡 **Task 41** — Model: **User** — `user_id` PK, `user_name`, `email` (unique, not null), `password` (hash), `role`, `created_at`.

🟡 **Task 42** — Model: **Prompt** — `prompt_id` PK, `user_id` FK, `prompt_text`, `submission_time`, `status` (`pending` / `analyzed` / `blocked`).

🟡 **Task 43** — Model: **AnalysisResult** — `analysis_id` PK, `prompt_id` FK, `detection_result`, `prompt_type` (**stores the 3-class label**), `severity_level`, `confidence_score`, `analysed_at`.

🟡 **Task 44** — Model: **AttackSubtype** — `subtype_id` PK, `analysis_id` FK (nullable), `subtype_name` (**one of the 8 sub-types above**; null for Safe), `type_description`.

🟡 **Task 45** — Model: **MitigationAction** — `mitigation_id` PK, `analysis_id` FK, `action_type` (warning / blocking / rewriting), `action_description`, `mitigated_prompt`, `action_time`.

🟡 **Task 46** — Model: **SafeSuggestion** — `suggestion_id` PK, `analysis_id` FK, `suggested_prompt`, `suggestion_reason`, `generated_at`.

🟡 **Task 47** — Model: **AvatarGuidance** — `guidance_id` PK, `analysis_id` FK, `message_text`, `explanation`, `displayed_at`.

🟡 **Task 48** — Model: **SimulationSession** — `simulation_id` PK, `user_id` FK, `scenario_name`, `description`, `start_time`, `end_time`, `outcome`.

🟡 **Task 49** — Model: **LearningProgress** — `progress_id` PK, `user_id` FK, `module_name`, `comp_status`, `completed_at`.

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
