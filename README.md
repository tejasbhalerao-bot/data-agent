# data-agent

Tejas's analyst, as a repo. It answers data questions, sizes and models opportunities, designs measurement for PRDs, and watches launches. Tejas runs the queries in Metabase and supplies the CSVs; the agent writes and checks the queries, calculates every number with a script, and writes every answer into a note.

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
2. If a saved note with the same scope already answers it, and is recent enough (data ended within 7 days for a rolling window; no limit for a fixed past period), the agent quotes that note, offers a refresh, and stops.
3. Otherwise it shows you a short brief of what it will do, starting with one line on how it understands the product flow. You correct it or approve it. Nothing starts before you approve.
4. It then writes the queries, each as its own file in the project's `queries-dump/` folder, checks them, and lists them in the same note under "Queries to run".
5. You run them in Metabase and save the CSVs in the project's `raw-data/` folder.
6. The agent checks the CSVs, calculates the numbers with a script, and writes the answer into a note (a `.md` file), with a short summary in chat.
7. You review the note and say "ok" to sign off. Each stage is saved on your computer automatically; it goes to GitHub only after you sign off.

Design record: `changelogs/2026-10-09-analyst-model-redesign-proposal.md`.
