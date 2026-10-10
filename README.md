# data-agent

Tejas's analyst, as a repo. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs the queries in Metabase and supplies the CSVs; the agent writes and checks the queries, calculates every number with a script, and writes a note when asked, and always for design and rollout.

## How to use
Open this folder in Claude Code and paste a request template from [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md). Name the project: anything that creates a query or script is saved in that project's folder under `archives/`, and nothing is saved without one. Start the request with a `Job:` line, one of:

| Job | Use it to |
|---|---|
| analyse | Find out what happened, where, and why |
| model | Size an opportunity, simulate a change, compare options |
| design | Write analytics requirements, define metrics, plan an experiment |
| rollout | Plan the stages, locations and gates of a launch |
| measure | Set a baseline, check a launch on day 1 or day 7, read the final result |

## Layout
```
data-agent/
├── CLAUDE.md             working rules and what every file is for
├── WORKFLOW_GUIDE.md     one copy-paste request template per job
├── context/              shared knowledge
│   ├── CLAUDE.md         Truemeds teams, systems and verticals
│   ├── README.md         how context files are formatted and loaded
│   ├── schema.md         every database table and its columns, known data quirks, and tested queries
│   ├── metrics.md        the agreed meaning of each metric
│   └── rules.md          rules that apply to every analysis (empty for now)
├── workflows/            route · loop · jobs · review · update-context
├── templates/            note.md · methods.md
├── scripts/              new-file.sh · commit-and-push.sh · validate-csv.py
├── archives/<project>/   context · queries-dump · scripts · tests · insights · raw-data · outputs
├── changelogs/           design records
└── scratch/              throwaway work (never uploaded)
```
What each file is for and when it is used: `CLAUDE.md`, "Elements of the repo".

## What happens to a request
1. The agent checks the request is complete and asks, in one message, only what it cannot work out.
2. If a saved note already answers it and its data ended within the last 7 days, the agent quotes that note, offers a refresh, and stops.
3. Otherwise it writes the queries, checks them, and gives you all of them at once, starting with one line on how it understands the product flow. Correct it if wrong.
4. You run them in Metabase and save the CSVs in the project's `raw-data/` folder.
5. The agent checks the CSVs, calculates the numbers with a script, and answers in chat, or in a note if you asked for one (design and rollout always produce a note).
6. You review the note and say "ok" to sign off. Only then is it saved to GitHub. Chat answers are not saved to GitHub unless you say "save".

Design record: `changelogs/2026-10-09-analyst-model-redesign-proposal.md`.
