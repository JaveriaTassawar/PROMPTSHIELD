# Frontend Track — Detailed Tasks (Rana)

> Part of the PromptShield FYP. The master plan is [`../tasks/MASTER_PLAN.md`](../tasks/MASTER_PLAN.md) — it owns task numbering, the dependency map, team roles, and the git workflow. **This file owns the frontend detail**: screens, API contracts, and per-task specifics for Tasks 67–92.
>
> Branch prefix for all work here: `frontend/`

---

## Stack

**React + Vite + Tailwind CSS.** Scaffolding already exists (merged in PR #1: Vite + Tailwind + routing + axios + recharts).

```bash
cd frontend
npm install
npm run dev
```
App at `http://localhost:5173`.

---

## The single most important thing about this track

**You are almost never blocked.** Every screen can be built against **mocked JSON** shaped like the real response, and only the final "Wire X" step needs the matching backend endpoint merged.

That means Tasks 67–70, 74–75, 77–79, 81, 83–84, 86–88, 90, 92 — the large majority — can all be built from day one, in parallel with ML and Backend. Keep the mock responses in one file (e.g. `src/mocks/`) so swapping to real API calls is a small, contained change.

### Mock response to build against (per SDS §6.5)

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

`classification` is always one of **`Safe`**, **`Direct Jailbreak`**, **`Indirect Injection`**.
`subtype` is one of the 8 below, or `null` when Safe:

| Class | Sub-types |
|---|---|
| Direct Jailbreak | Policy Evasion · Multi-Turn Manipulation · Role Override · Persona Hijacking · System Prompt Overwrite |
| Indirect Injection | Document Embedding · Web Content Injection · Tool Output Injection |

`severity` is one of **`Low`**, **`Medium`**, **`High`**, **`Critical`** — pinned at Task 43 and enforced by a CHECK constraint in the database. The SRS never enumerated these, so they were chosen backend-side; the full table and rationale are in [`../backend/TASKS.md`](../backend/TASKS.md#severity-vocabulary--pinned-here-task-43).

**Use these exact strings in Task 78's severity badge.** Anything else (`"Severe"`, `"Warning"`, lowercase) will never arrive from the API, because the database rejects it — so a badge keyed on a different value silently renders nothing.

Defaults: `Safe` → `Low`; both attack classes → `High`. `Critical` is reserved for Task 57 mitigation to escalate.

**Design for all 8 sub-type labels**, not just the 3 classes — the Detection Result and Analytics screens both display them.

### Content warning

When picking example prompts for the UI, take them from the **hand-checked sample** (`ml/data/sample_1000.csv`, ML Task 22), not from the raw datasets — the raw in-the-wild jailbreak data contains explicit/NSFW content.

---

## Tasks 67–92

Markers: ✅ done · 🔵 ready now · 🟡 in progress order (finish the one before it) · 🔴 needs a teammate's task first

### Scaffold & Auth

🔵 **Task 67** — Scaffold Vite + React _(largely done in PR #1 — verify and finish)_.

🟡 **Task 68** — Tailwind config — set up the dark theme, colour tokens, and typography matching the SDS wireframes.

🟡 **Task 69** — Login page UI — email + password, validation states, error display. Mock the submit.

🟡 **Task 70** — Register page UI — name, email, password, role picker (student / developer / researcher / organization) per the SDS prototype.

✅ **Task 71** — Wire Register → `POST /api/register` — **done**

✅ **Task 72** — Wire Login → `POST /api/login`; store the JWT, attach it to axios — **done**

✅ **Task 73** — Route guard — redirect unauthenticated users; verify the token via `GET /api/profile` — **done**

_New: `src/api/client.js`, `src/api/auth.js`, `src/auth/{context.js, AuthContext.jsx, useAuth.js, RequireAuth.jsx}`. Edited: `LoginPage`, `RegisterPage`, `App.jsx`. **Lint clean, build passes in 480ms.** The whole flow was verified against a running backend._

```
POST /api/register  (role: organization)  -> 201
POST /api/login                           -> 200 + token
GET  /api/profile   with token            -> 200
GET  /api/profile   without token         -> 401
CORS preflight from localhost:5173        -> allowed, incl. the Authorization header
```

_**The stored token is verified against the server before it is trusted** — Task 73's real requirement, and the reason `AuthContext` is more than a `useState`. A token in `localStorage` proves nothing: it may be expired, or the account deactivated since (the backend re-checks `is_active` on every request). Trusting it blindly would show the dashboard to someone whose access was revoked, then fail every request they made._

_**`status` is three-valued — `checking` / `authenticated` / `anonymous` — not a boolean.** With a boolean, the first render after a refresh is indistinguishable from logged-out, so the guard would bounce an authenticated user to Login every time they pressed F5. That is the commonest bug in hand-rolled route guards, and the three-state machine is what avoids it._

_**A 401 clears the session; a 403 does not.** The backend returns 401 for missing/expired/revoked tokens and 403 for "authenticated but not allowed" (wrong role, or deactivated). Clearing on a 403 would log an admin out for visiting one page they lack rights to._

_**The axios interceptor does not navigate.** It notifies a handler the auth layer registers, so the HTTP client stays independent of React Router — otherwise any non-component caller would break._

_**⚠️ `localStorage` is a documented trade-off, not an oversight.** Task 72 specifies it, and it survives a refresh where a memory-only token does not — but any script on the page can read it, so an XSS bug becomes a stolen session. `httpOnly` cookies avoid that at the cost of backend changes and CSRF handling. **Worth a sentence in the report**, given the project's subject._

_Two lint errors were fixed properly rather than suppressed: the context object and the `useAuth` hook each moved to their own file, because a module exporting both a component and a plain value breaks Vite's Fast Refresh — editing the provider would full-reload and drop the session mid-work._

### Prompt Analyzer & Detection Result

🔵 **Task 74** — Dashboard shell — persistent sidebar (Dashboard · Prompt Analyzer · Simulation Lab · Learning Hub · Analytics · Profile) per the SDS wireframes.

🟡 **Task 75** — Prompt Analyzer UI — textarea, Analyze button, example-prompt chips, loading state.

🔴 **Task 76** — Wire the Analyze button → `POST /api/analyze-prompt` — **needs Backend Task 56 merged**.

🔵 **Task 77** — Detection Result — **Safe** state — green treatment, confidence meter, "why this is safe" bullets. _Buildable with mock data._

🔵 **Task 78** — Detection Result — **Direct Jailbreak** state — red/critical treatment, **show the sub-type** (one of the 5), flagged-content highlighting, "Get Safe Rewrite" + "Ask Avatar" actions. _Buildable with mock data._

🔵 **Task 79** — Detection Result — **Indirect Injection** state — amber treatment, **show the sub-type** (one of the 3), explain that the malicious instruction came from embedded content rather than the user. _Buildable with mock data._

🔴 **Task 80** — Confirm all 3 states end to end — **needs Task 76 merged** for a real check; visual confirmation with mocks can happen earlier.

### Avatar Guidance & Simulation Lab

🔵 **Task 81** — Avatar Guidance UI — the "Aria" panel: what happened / why it's dangerous / next steps, with DO and DON'T columns per the SDS prototype.

🔴 **Task 82** — Wire Avatar Guidance → `POST /api/avatar-guide` — **needs Backend Task 60 merged**.

🟡 **Task 83** — Simulation scenario picker — cards with difficulty badges. UI buildable with a mocked scenario list; real data **needs Backend Task 62 merged**.

🟡 **Task 84** — Active Simulation screen — conversation turns on the left, live detection results on the right, objective banner, progress bar.

🔴 **Task 85** — Wire the simulation flow → `POST /api/simulate-attack` — **needs Backend Task 63 merged**.

🟡 **Task 86** — Simulation Results screen — score, challenges passed/missed, per-challenge breakdown, recommended next steps.

### Learning Hub, Analytics & Admin

🔵 **Task 87** — Learning Hub screen — tutorial cards, progress bar, XP, category filters.

🔵 **Task 88** — Analytics dashboard UI — attack-frequency chart, model-accuracy tile, avg-response-time tile, **sub-type breakdown table** (recharts is already installed).

🔴 **Task 89** — Wire Analytics → `GET /api/dashboard` — **needs Backend Task 64 merged**.

🔵 **Task 90** — Admin panel UI — user management table, role controls, system-health panel.

🔴 **Task 91** — Wire the Admin users table → `GET /api/admin/users`; handle the 403 case for non-admins — **needs Backend Task 65 merged**.

🟡 **Task 92** — Profile & settings page — personal info, notification toggles, API key display.
