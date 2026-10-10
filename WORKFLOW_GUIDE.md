# Workflow Guide

Paste a template, fill the fields, send. Fields marked (default) can be left out: the agent fills them from `context/rules.md` and lists what it assumed. Anything else missing is asked once, in a single message. The `Job:` line makes routing exact.

## What happens after you send
1. Ready-check, then context loads. If the answer is already known (`context/findings.md`, a recent note, a CSV on disk) it answers from that with the as-of date.
2. For a new pull: you get **one pack** (queries, a probe, exact filenames). Run it in Metabase once and save the CSVs into the project's `raw-data/` with those names.
3. The agent detects the files, validates them, computes the figures with a script, writes the note and reviews it. You read it and sign off; the push to `main` happens on your sign-off.

## Analyse
```
Job: analyse
Project: <slug>
Question: <what do you want to know>
Decision it feeds: <what you will do with the answer>
Window (default): 
Cohort / vertical (default): 
Compare against (default: prior period): 
Metrics (default: metrics.md): 
```
Example: `Job: analyse / Project: egregiously-miscalibrated-promises / Question: why did on-time drop for Pune SDD in September / Decision it feeds: whether to escalate to the courier team / Window: Sept vs Aug`

## Model
```
Job: model
Project: <slug>
Lever: <the change, rule or option>
Assumptions: <each one, with a value if you have it>
Horizon: 
Alternatives to compare (optional): 
Decision it feeds: 
```

## Design
```
Job: design
Project: <slug>
PRD (paste the text or key points): 
Need: ard | metrics | feasibility | instrumentation | experiment plan   (any combination)
For an experiment: hypothesis, target metric, eligible universe, planned split
Decision it feeds: 
```

## Rollout
```
Job: rollout
Project: <slug>
PRD / change being rolled out: 
Rollout plan: <stages, locations, % of traffic or orders, launch parameters, intended duration>
Success and guardrail metrics: 
Decision it feeds: 
```

## Measure
```
Job: measure
Project: <slug>
Mode: baseline | day1 | day7 | health | readout
Cuts you want (analyst will propose more): 
Dashboard spec needed: yes | no
Launch date: 
Control / baseline window: 
Metrics: <names, or "from the PRD" with the PRD pasted>
Success and guardrail thresholds (if known): 
```

## Update context
```
Job: update-context
Add or change: schema | metric | rule | query | finding
Details: <table name / metric and definition / rule / paste the SQL>
```

## When a query fails
Paste the error, the timeout or the odd result into the chat. The agent diagnoses, fixes and sends a new pack; any new quirk is added to `context/rules.md` automatically.

## Re-running a saved analysis
`Job: analyse / Project: <slug> / Re-run: <note or script name> / New file: <csv>`. The saved script runs on the new CSV; nothing is rebuilt.

## Manual operations
```bash
scripts/new-file.sh <project> insights <project>-<topic> md
scripts/commit-and-push.sh "message" <path> [path...]
python3 scripts/validate-csv.py <file> --key order_id --require order_id,digitised_ts
```
