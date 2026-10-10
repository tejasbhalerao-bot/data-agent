# data-agent

Tejas's analyst, as a repo. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs queries in Metabase; the agent writes and checks them, computes every figure from code, and saves a note per request.

## How to use
Open this folder in Claude Code and paste a request from [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md). Every request starts at `workflows/route.md`. A complete request needs at most one batched question, one Metabase run and a non-blocking read.

## Layout
```
data-agent/
├── CLAUDE.md            working rules, file routing, save rule
├── WORKFLOW_GUIDE.md    one copy-paste request template per job
├── context/             shared knowledge (see context/README.md)
│   ├── CLAUDE.md  README.md
│   ├── schema.md          every table, flagged by system; reference queries
│   └── metrics.md  rules.md  findings.md
├── workflows/           route · loop · jobs · review · update-context
├── templates/           note.md · methods.md
├── scripts/             new-file.sh · commit-and-push.sh · validate-csv.py
├── archives/<project>/  context · queries-dump · scripts · tests · insights · raw-data · outputs
├── changelogs/          design records
└── scratch/             throwaway (gitignored)
```

## Flow
Route (ready-check, job, tier) → Brief (Tier 2) → Build SQL, review, one handoff pack → Tejas runs once → validate CSV → compute with a script → note → review → Tejas reads and signs off → push to `main`.

Design record: `changelogs/2026-10-09-analyst-model-redesign-proposal.md`.
