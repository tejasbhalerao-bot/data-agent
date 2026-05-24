# Skill: Plan Builder

Converts an analytical objective into a structured plan ready for `plan-refiner` evaluation.
Always followed by `plan-refiner`. Never hand off to `table-mapper` without refiner sign-off.

---

## Trigger

Invoked at the start of any analysis — exploratory, post-release, one-time, recurring.
Input: an objective from Tejas. Can be a hypothesis, an opportunity area, a question, or a feature to assess.

---

## Step 1: Clarify before planning

If the objective is ambiguous, ask — do not assume. One focused question at a time.

Ambiguity signals:
- No measurable outcome stated ("understand delivery performance" = ambiguous)
- Scope unclear — which vertical, which time window, which courier?
- Multiple objectives bundled into one ("check adherence and also cost and also RTO")

If bundled: split into separate objectives. Build one plan per objective. Do not merge.

If objective is clear: proceed without prompting.

---

## Step 1b: Surface business logic assumptions before planning

Before building the plan, identify every point where business knowledge is required to proceed correctly.

**Never assume. Always ask.**

This includes — but is not limited to:

| Assumption type | Example |
|---|---|
| Metric definition | "On-time" — does it mean delivered by promise date, or by cutoff? |
| Inclusion / exclusion rules | Are RTOs included in adherence calculation? Are cancelled orders excluded? |
| Vertical scope | Does this apply to all fulfilment verticals or specific ones? |
| Cohort definition | Which orders qualify — all, or only PBA-eligible? |
| Business rule | If a courier is unavailable, does the order fall back or fail? |
| Date / event anchor | Is "go-live" the date PBA was enabled in prod or the date first order was processed? |
| Threshold / benchmark | What is "good" adherence — is there a target? |

List every assumption as a question. Ask all at once — do not drip-feed one at a time.
Wait for answers before proceeding to plan construction.

If Tejas says "use your judgement" on a business logic question — push back once. Business logic errors invalidate the entire analysis.

---

## Step 2: Detect analysis type

| Type | Signal |
|---|---|
| **Hypothesis test** | Tejas states a specific belief to validate ("PBA couriers deliver faster") |
| **Opportunity hunt** | Tejas gives a vague area to investigate ("delivery adherence feels off") |
| **Post-release assessment** | A feature or change went live and needs evaluation |
| **One-time question** | Specific operational question with a clear answer format |
| **Recurring** | Analysis meant to run on a schedule |

State the detected type at the top of the plan. If unsure, ask.

---

## Step 3: Build the plan

Produce the plan in this exact format:

---

### Analysis Plan

**Objective:** [Restate the objective in one sentence. Must be measurable — answerable with data.]

**Analysis type:** [hypothesis test / opportunity hunt / post-release assessment / one-time / recurring]

**Questions to answer:**
- Q1: [Specific question. Must be answerable yes/no or with a number/distribution.]
- Q2: ...
- Q3: ...

> Each question must be independently answerable. No compound questions.

**Steps:**

| # | Step | Answers | Depends on |
|---|---|---|---|
| 1 | [What to do] | [Which Q#] | [None or Step #] |
| 2 | ... | ... | ... |

> Every Q must be answered by at least one step. Every step must answer at least one Q.

**Data needed (high level):**
- [Table or source name] — [why needed]
- ...

> Do not specify columns or joins here — that is table-mapper's job.
> Flag any source that may not exist or may need ops confirmation.

**Known risks:**
- [Data availability risk, business logic uncertainty, or scope assumption that needs validation]
- If none: state "None identified"

**Definition of done:**
- [Specific condition — e.g. "All 4 questions answered with supporting data, findings doc written"]

---

## Step 4: Hand off to plan-refiner

Do not present the plan to Tejas yet.
Pass the completed plan directly to `plan-refiner` for evaluation.
