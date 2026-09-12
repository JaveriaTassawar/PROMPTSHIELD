# Testing & Submission — Detailed Tasks (whole team)

> Part of the PromptShield FYP. The master plan is [`../tasks/MASTER_PLAN.md`](../tasks/MASTER_PLAN.md) — it owns task numbering, the dependency map, team roles, and the git workflow. **This file owns the testing detail**: the TC-01…TC-15 cases from the SRS/SDS Test Design table, and Tasks 93–101.
>
> Branch prefix for all work here: `test/`

---

## When this stage starts

This is the **one stage with no parallelism left** — it needs the ML, Backend, and Frontend tracks merged to `main`. Everything before it can run in parallel; this is the integration checkpoint.

## Test case reference (SRS/SDS Test Design)

| ID | Scenario | Expected result |
|---|---|---|
| TC-01 | Register with valid information | Account created, confirmation shown |
| TC-02 | Register with an existing email | "Email already exists" error |
| TC-03 | Login with valid credentials | Redirected to dashboard |
| TC-04 | Login with invalid credentials | Authentication error shown |
| TC-05 | Submit a safe prompt | Classified **Safe**, confidence displayed |
| TC-06 | Submit a direct jailbreak prompt | Classified **Direct Jailbreak** |
| TC-07 | Submit an indirect prompt injection | Classified **Indirect Injection** |
| TC-08 | System identifies attack sub-type | Correct sub-type displayed (one of the 8) |
| TC-09 | Request safe prompt suggestion | Safer alternative generated |
| TC-10 | Receive avatar guidance after detection | Explanation + recommendations shown |
| TC-11 | Access the simulation sandbox | Environment loads, accepts test prompts |
| TC-12 | Admin views dashboard analytics | Stats, attack counts, severity metrics correct |
| TC-13 | Detection results stored in DB | Analysis records saved |
| TC-14 | View learning progress | Completed modules and status accurate |
| TC-15 | Prompt analysis under normal load | Result within the expected response time |

**Prompt sourcing:** take TC-05/06/07/08 prompts from the **real-world held-out test set**, not the synthetic old CSV — and hand-pick them to avoid the explicit content present in the raw in-the-wild data (see [`../ml/TASKS.md`](../ml/TASKS.md) section 2e).

**Timing targets** (SRS §4.1): **<200 ms** core detection (TC-15 measures the endpoint, so allow for HTTP overhead on top), **<1 s** end-to-end.

---

## Tasks 93–101

Markers: ✅ done · 🔵 ready now · 🟡 in progress order · 🔴 needs a teammate's task first

🔴 **Task 93** — TC-01, TC-02 — **needs Backend Tasks 50–51 merged**.

🟡 **Task 94** — TC-03, TC-04.

🔴 **Task 95** — TC-05, TC-06, TC-07 — **needs Backend Task 56 merged** (and therefore ML Task 35, unless the stub is still in place — note in the results which was used).

🟡 **Task 96** — TC-08, TC-09, TC-10 — sub-type identification, safe prompt suggestion, avatar guidance.

🔴 **Task 97** — TC-11, TC-12 — **needs Backend Tasks 63–64 merged**.

🟡 **Task 98** — TC-13, TC-14, TC-15 — persistence, learning progress, response time under load.

🟡 **Task 99** — Fix failing cases. Record each defect in the SRS/SDS **Appendix B IV&V table** (defect description, origin stage, status, fix time) — the documents already have the empty table waiting.

🟡 **Task 100** — Finalise `README.md` — setup steps for all three tracks, the real accuracy numbers from ML Task 31, and a link to `MODEL_CARD.md`.

🟡 **Task 101** — Tag the release for submission (e.g. `v1.0-fyp-submission`).
