# data-agent redesign v3 — "the analyst I don't have"

Status: PROPOSAL for Tejas's approval. Nothing else in the repo has changed yet.
Pattern source: `~/pm-agent` (thin CLAUDE.md → entry route → workflows → auto-review → Artifact sign-off → pre-authorised save + push).
v3 adds: an intake contract that makes routing deterministic, and a cut in human touchpoints.

---

## 1. Self-review: gaps found and fixed

| # | Gap | Fix |
|---|---|---|
| G1 | Too much machinery (11 core workflows, 6 engine files, 3 gates) | One shared **loop** + 4 short **job cards**; 5 workflow files |
| G2 | Four documents per request restating each other | **One note per request**, growing through its life |
| G3 | Sessions break at the CSV handoff | Note carries `status` + expected CSVs; router resumes `awaiting-data` notes |
| G4 | Nobody computed the figures | All figures come from a script run on the CSV |
| G5 | Too many questions | Ask only what `metrics.md` / `rules.md` cannot answer |
| G6 | Tier choice subjective | Objective test (4.3) |
| G7 | Three gates | Two, and Gate A is conditional (G14) |
| G8 | Baseline / launch / readout split into 3 workflows | One `measure` job, three modes |
| G9 | Recurring reports as a workflow | Re-run saved query + script on a new CSV |
| G10 | Stale answers from findings | Every finding has an as-of date and window |
| G11 | Non-Redshift sources ignored | Each `data/` file names its source |
| G12 | Stats method homeless | One `methods.md` |
| **G13** | **Routing guessed from free text; inputs not guaranteed** | **Intake contract + ready-check in `route.md`; explicit `Job:` header** |
| **G14** | **Gate A on every Tier 2 request** | **Gate A only when a blocking assumption was made** |
| **G15** | **Several Metabase round trips per request** | **Pull wide, cut offline; reuse CSVs on disk; one handoff pack; Claude detects drops** |
| **G16** | **Gate B blocked saving; every context change needed approval** | **Save first, read after; only definition conflicts need approval** |

---

## 2. Rubric (design is done when all pass)

| # | Criterion | Pass test |
|---|---|---|
| S1 | Few moving parts | ≤ 5 workflow files; ≤ 2 gates; ≤ 4 context file types |
| S2 | One home per fact | Every concept lives in exactly one place |
| S3 | Traceable | Any request traces in ≤ 6 phases (section 4.4) |
| V1 | Low verbosity: artifacts | One note per request |
| V2 | Low verbosity: files | Each workflow file ≤ 60 lines; ≤ 2 templates |
| C1 | PDLC coverage | All 10 stages map to a job |
| C2 | Role coverage | All 6 analyst roles enforced by a named step |
| C3 | Use-case coverage | 15 representative requests all route (section 6) |
| K1 | Correctness | Query writing has an owner and independent checks; figures come from code |
| K2 | Resumable | A request survives a gap between sessions |
| **H1** | **Human touchpoints** | **Typical Tier 2: ≤ 1 blocking question and ≤ 1 data run** |
| **H2** | **No avoidable blocking** | **No blocking step the router could resolve from context or a flagged default** |

### Scorecard

| Criterion | v1 | v2 | v3 |
|---|---|---|---|
| S1 | Fail | Pass | Pass (5 files, 2 gates, 4 context types) |
| S2 | Fail | Pass | Pass |
| S3 | Fail | Pass | Pass (6 phases) |
| V1 | Fail | Pass | Pass |
| V2 | n/a | Pass | Pass |
| C1 | Pass | Pass | Pass |
| C2 | Pass | Pass | Pass |
| C3 | Untested | Pass | Pass (15/15) |
| K1 | Partial | Pass | Pass |
| K2 | Fail | Pass | Pass |
| H1 | Fail | Fail (3 gates, 1–3 runs, error reports) | Pass |
| H2 | Fail | Fail | Pass |

---

## 3. What the analyst does (PDLC), and the job that covers it

| Stage | Analyst's work | Job |
|---|---|---|
| 1 Discover | Baseline, segment, size the problem | analyse |
| 2 Size and prioritise | Opportunity ranges, compare candidates | model |
| 3 Define | Calibrate thresholds, backtest the rule | model |
| 4 Spec | Data feasibility, metric definitions, instrumentation | design |
| 5 Experiment design | Hypothesis, metrics, sample size, holdout, decision rules | design |
| 6 Pre-launch | Baseline snapshot, query tests, alert thresholds | measure (baseline) |
| 7 Launch | D1/D3/D7 health checks | measure (health) |
| 8 Evaluate | Impact vs baseline/control, ship/iterate/kill | measure (readout) |
| 9 Operate | Ad-hoc numbers, anomalies, recurring packs | analyse (+ re-run) |
| 10 Steward | Keep schema, metrics, rules, queries, findings current | update-context |

| Role | Enforced by |
|---|---|
| Translator | Intake contract + ready-check in `route.md` |
| Skeptic | `review.md`, three checkpoints |
| Modeler | `model` card: ranges and stated assumptions are mandatory |
| Narrator | Note template: answer first, decision implication required |
| Monitor | `measure` card, health mode |
| Librarian | Router scans queries, findings, and CSVs on disk first; loop promotes durable learnings |

---

## 4. Design

### 4.1 Repo shape

```
data-agent/
├── CLAUDE.md                 thin: read context/CLAUDE.md; archive + save rules
├── WORKFLOW_GUIDE.md         copy-paste request template per job (the intake contract in prompt form)
├── context/
│   ├── CLAUDE.md             org, systems, verticals, "local workflows only; no built-in data:* skills"
│   ├── data/<system>.md      schema per system; names its source (Redshift / Mixpanel / sheet)
│   ├── metrics.md            one definition per metric: numerator, denominator, exclusions, anchor
│   ├── rules.md              standard exclusions, gotchas, FC/MFC, cutoffs, pricing, default scope
│   ├── queries/              validated SQL, each with a header
│   └── findings.md           durable results, each with as-of date and window
├── workflows/
│   ├── route.md              intake ready-check + routing (entry point)
│   ├── loop.md               shared engine (4.4)
│   ├── jobs.md               4 job cards, each with its required inputs
│   ├── review.md             one checklist, three checkpoints
│   └── update-context.md     add or change schema / metric / rule / query / finding
├── templates/                note.md, methods.md
├── scripts/                  new-file.sh (keep), commit-and-push.sh, validate-csv.py
└── archives/<project>/       existing layout unchanged; insights/ holds the notes
```

### 4.2 `route.md`: intake contract and routing

Routing is classification, and classification needs inputs. So the first step is a ready-check against the job card's required inputs.

| Field | Required for | If missing |
|---|---|---|
| **Job:** analyse / model / design / measure / update-context | all | Infer from text and state the inference |
| **Project** | all | Ask |
| **Decision this feeds** | all except Tier 0/1 | Ask |
| **Scope:** window, cohort, verticals, systems | all | Default from `rules.md` and flag |
| **Definitions:** metrics named | all | Use `metrics.md`; blocking only if a term is undefined there |
| **Comparison:** baseline / control / alternatives | analyse, measure | Ask |
| **Levers and assumptions** | model | Ask |
| **PRD text or key points** | design | Ask |
| **Launch date, mode, control** | measure | Ask |
| **Data on hand:** CSV paths | optional | Check `raw-data/` before requesting a pull |

Steps:
1. **Resume check:** any note in the project with `status: awaiting-data`? Offer to continue.
2. **Job:** explicit `Job:` header wins; otherwise infer and say so. Split bundled requests into separate notes.
3. **Ready-check:** classify each gap as **defaultable** (window = last 30 days, standard exclusions, all verticals of the named systems, comparison = prior period) or **blocking** (undefined metric, cohort that changes the answer, missing control, missing PRD input). Defaultable gaps are filled and listed in the note's first line. If any blocking gap exists, send **one message listing all of them**, then continue.
4. **Load context:** `data/` for the named systems, `metrics.md`, `rules.md`; scan `queries/`, `findings.md` and `raw-data/` for an existing answer. Print a short `[CONTEXT LOADED]` block. A system with no docs: offer "pause and add" or "proceed with flagged assumptions".
5. **Tier** (4.3), then enter `loop.md`.

### 4.3 Tiers (objective test)

| Tier | Test | Path |
|---|---|---|
| 0 Recall | `findings.md` or a note answers it and the as-of date is acceptable | Answer with source and as-of date; offer a refresh |
| 1 Quick | Every term resolves in `metrics.md`, every table is in `data/`, ≤ 1 main query | Loop without a brief |
| 2 Full | Anything else | Full loop |

### 4.4 `loop.md`: six phases

| Phase | What happens | Human |
|---|---|---|
| **1 Route** | Ready-check, defaults, tier (4.2, 4.3) | One batched question, only if a blocking field is missing |
| **2 Brief** | Built from the intake: objective, questions, definitions, tables, output columns and grain, defaults used. Shown as the note header. | **Gate A only if a blocking assumption was made.** Otherwise it proceeds without waiting. |
| **3 Build** | Reuse a fresh CSV on disk if one covers the request. Otherwise `build-sql` writes the queries (owner of correctness): pre-flight that tables, columns and metrics exist in context (else `update-context`); reuse `queries/` first; apply `rules.md` exclusions; **pull wide at the lowest useful grain with all segment columns so cuts happen offline**; header on each query; timeout rating, chunk if High. Check 1 (static review) runs, then **one handoff pack**: all queries, exact filenames to save as, one combined probe. | none |
| **4 Run** | Tejas runs the pack once and saves the files. Claude detects the files by name and runs Check 2 (`validate-csv.py`: schema vs brief, grain unique, nulls, date range, probe). An error or odd result: Tejas pastes it; Claude diagnoses and re-presents; the quirk goes to `rules.md`. | **One run** (plus rework only on failure) |
| **5 Answer** | Script computes all figures and cuts into `outputs/`; note written from `templates/note.md` (answer, decision implication, evidence tables in full, definitions, defaults used, caveats, next check); Check 3 (`review.md`). | none |
| **6 Save** | Save with auto-version, commit and push **immediately**, `signed_off: false`. Context changes proposed as one block: additive items (new validated query, new gotcha row, finding with as-of) apply automatically with the diff shown; a change to an existing definition or rule waits for approval. Tejas reads the note whenever; his sign-off sets `signed_off: true` and is the gate for promotion into `findings.md`. | **Non-blocking read; approval only for definition conflicts** |

Tier 2 notes are also delivered as an Artifact; Tier 0/1 short answers stay in chat with source and as-of.

### 4.5 `jobs.md`: job cards

| Job | Required inputs (on top of the common ones) | Method | Note adds |
|---|---|---|---|
| **analyse** | Window, cohort, comparison | Baseline, segment cuts, confounder check, reconcile sources | Where it concentrates; what it is not |
| **model** | Lever, assumptions, horizon | Counterfactual or backtest on history; low/base/high; sensitivity | Assumption table, range, break-even, risks |
| **design** | PRD text or key points; for XPs: hypothesis and target metric | Data feasibility (schema + probes), metric definitions, instrumentation needs; for XPs: guardrails, MDE, sample size, duration, holdout, SRM, decision rules (`methods.md`) | Paste-ready block for the PRD |
| **measure** | Mode (baseline / health / readout), launch date, control | Baseline snapshot; instrumentation and guardrail checks; impact vs baseline or control with significance and segments | Mode-specific; readout ends ship / iterate / kill |

### 4.6 `review.md`: one reviewer, three checkpoints

| Checkpoint | When | Checks |
|---|---|---|
| 1 SQL | Before handoff | Definitions match `metrics.md`; standard exclusions; grain and fan-out; join-key cardinality; dedupe rules; date filter placement; snake_case names; output matches brief |
| 2 CSV | On file drop | `validate-csv.py` |
| 3 Note | Before save | Every figure reconciles to `outputs/`; denominators; sample size and noise; segment mix; claim strength; as-of date |

Always runs. Fix and re-review until no blocking issue; leftovers are flagged in the note.

### 4.7 `update-context.md`

Add or change a schema table, metric, rule, validated query or finding. Schema additions use the sample-row discovery steps from today's `schema-discovery`. Additive changes auto-apply with a shown diff; changes to existing definitions wait for approval. Triggered by the loop or directly by Tejas.

### 4.8 Note front matter

```
---
project: <slug>
job: analyse | model | design | measure
tier: 1 | 2
status: brief | awaiting-data | analysing | review | saved
awaiting: [<csv names expected in raw-data/>]
defaults_used: [<field = value>]
signed_off: false
as_of: YYYY-MM-DD
---
```

### 4.9 Human touchpoints

| | v2 | v3 |
|---|---|---|
| Tier 1 | request, 1–2 questions, run, read | request, one run, read (non-blocking) |
| Tier 2 | request, questions, Gate A, 1–3 runs, error and "done" reports, Gate B, context approvals | complete request, 0–1 batched question, Gate A only on blocking assumption, 1 run, non-blocking read, definition-conflict approvals only |

**Optional lever, not assumed:** a read-only Metabase API key or warehouse CLI would let Claude execute queries itself, removing the run touchpoint. Phase 4 of the loop is the seam. Tejas has decided to execute queries, so this is not in scope.

---

## 5. Workflow diagram

```
request (use the template in WORKFLOW_GUIDE.md)
   │
   ▼
ROUTE + ready-check ──blocking field missing──► ask once (batched), continue
   │  Tier 0: answer exists ──► answer + as-of ──► end
   ▼
BRIEF (from intake; Gate A only if a blocking assumption)       Tier 1 skips
   ▼
BUILD: reuse CSV on disk, or wide-pull SQL → check 1 → one pack
   ▼
RUN: Tejas runs once → Claude detects files → check 2 (auto)
   │   error / odd / failed check ──► back to BUILD
   ▼
ANSWER: script computes → note → check 3
   ▼
SAVE: push unsigned · additive context auto-applied
   ▼
Tejas reads (non-blocking) · approves definition conflicts · sign-off gates findings.md
```

(Interactive diagram shown in the conversation.)

---

## 6. Coverage test: 15 requests

| # | Request | Job / tier |
|---|---|---|
| 1 | "SDD adherence last week?" | analyse, T1 (T0 if recent) |
| 2 | "Why did on-time drop in Pune?" | analyse, T2 |
| 3 | "How big is the nano-FC opportunity?" | model, T2 |
| 4 | "What promise buffer should we pick?" | model, T2 |
| 5 | "Which of these three ideas first?" | model, T2 |
| 6 | "Are the PRD's metrics measurable?" | design, T2 |
| 7 | "Design the experiment" | design, T2 |
| 8 | "Instrumentation audit of the cart events" | analyse, T2 |
| 9 | "Baseline before launch" | measure (baseline), T2 |
| 10 | "D3 health check" | measure (health), T1/T2 |
| 11 | "Did it work?" | measure (readout), T2 |
| 12 | "Weekly KPI pack" | re-run saved query + script on new CSV |
| 13 | "Reconcile two sources' numbers" | analyse, T2 |
| 14 | "Query timed out" | loop phase 4 → 3 |
| 15 | "Add this metric definition / new table" | update-context |

---

## 7. Migration (all nine projects)

| Phase | Work |
|---|---|
| 1 | New `CLAUDE.md`, `context/CLAUDE.md`, `route.md`; `WORKFLOW_GUIDE.md` with one request template per job; port `commit-and-push.sh` from pm-agent; split `schema.md` into `data/<system>.md`; refresh stale schema (PBA shadow flag, promise tables) |
| 2 | `loop.md`, `jobs.md`, `review.md`, `update-context.md`, templates, `validate-csv.py` |
| 3 | Per project (9): extract definitions to `metrics.md`, gotchas to `rules.md`, reusable SQL to `queries/`, durable results to `findings.md`; add front matter to existing insight docs; list existing CSVs in each `data-sources.md` so the reuse check works |
| 4 | Retire the old five skills and `CLAUDE.md` §6 double-logging |

Archives stay where they are. Kept from today: assumptions gate (now "ask only what context cannot answer"), timeout split and merge, auto-versioning, gitignore rules, archive layout.

## 8. Decisions on record

1. Tejas executes all queries and supplies CSVs.
2. PRD input is supplied case by case.
3. `metrics.md` / `findings.md` not shared with pm-agent for now.
4. Migrate all nine projects.
5. Tier 1 may skip the brief when context suffices (objective test, 4.3).
6. Intake contract and conditional Gate A, save-then-read, and batched context updates adopted (v3).

---

## 9. Implementation status (2026-10-09)

Built: phases 1 and 2, and the extraction in phase 3 for all nine projects. Old skills (`workflows/skills/*`), `workflows/prompts`, `recurring/`, `context/reference-queries` and `context/schema.md` are deleted; `schema.md` is split into `context/data/{allocation,eta,tracking,serviceability,masters}.md`. Archives are untouched except `_template` (no `analysis-plans/`, new `data-sources.md`) and two broken `schema.md` pointers.

Deviations from the design:
- **Context types are 5, not 4** (`data/`, `metrics.md`, `rules.md`, `queries/`, `findings.md`). The earlier count was wrong. Each fact still has one home.
- **`queries/` is an index, not a copy.** `context/queries/INDEX.md` points at each query's canonical path in its project `queries-dump/`; a query moves into `context/queries/` when a second project reuses it. This avoids duplicating SQL.
- **Legacy notes were not given front matter.** Existing `insights/` docs keep their format; the router resumes only notes created from `templates/note.md`.
- **Not mined:** EMP design docs (fallback ladder, option scoring, freeze, sample floor) and the 42 KB early-delivery session recap stay in their projects as project context.
- **Conflicts surfaced, not resolved:** doctor and warehouse leg definitions differ across projects (`rules.md` G1); the PBA shadow-vs-live status is unconfirmed (G4).

## 10. Review decisions on CLAUDE.md (Tejas, 2026-10-09)

7. **Push timing:** nothing is pushed before sign-off. Note and context changes are saved locally after Check 3 and pushed on sign-off. This supersedes decision 6's save-then-read (section 4.4 phase 6, 4.9 and the v3 touchpoint table).
8. **Push target:** straight to `main`.
9. **Built-in skills:** analysis skills stay banned; output-format skills (xlsx, pdf, docx, pptx, charting) are allowed on request.
10. **Notes folder:** stays `insights/`.
11. **`context/queries/` removed (Tejas, 2026-10-10):** the index only pointed at project SQL. Validated queries are now a "Reference queries" section at the bottom of the owning `context/data/<system>.md`. Context has four file types: `data/`, `metrics.md`, `rules.md`, `findings.md`.
12. **Schema merged into one file (Tejas, 2026-10-10):** `context/data/<system>.md` is replaced by `context/schema.md`; each table carries a `Systems:` flag. Reference queries sit at the bottom, grouped by system.
13. **Jobs added (Tejas, 2026-10-10):** `rollout` (GTM design: staged sizing, gates, duration); `design` gains an ARD mode (instrumentation table, Mermaid ER diagram); `measure` gains day1 / day7 modes, explicit baseline correctness checks and a dashboard spec. Five jobs now.
