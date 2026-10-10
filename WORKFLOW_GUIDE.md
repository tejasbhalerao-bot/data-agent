# Workflow Guide

Copy a template, fill it in, send it. Leave out any field marked (default). Anything else missing, the agent asks once.

Quick question? Skip the template. Write one sentence and name the project. The answer comes in chat.

Want a written note? Add `Note: yes`. Design and rollout always give a note.

## What happens
1. The agent checks your request. If a note from the last 7 days already has the answer, it uses that.
2. It sends you all the queries at once, with the file names to save as.
3. You run them in Metabase. Save the CSVs in the project's `raw-data/` folder.
4. The agent checks the CSVs, calculates the numbers, and answers.
5. Notes: you say "ok", then it saves to GitHub. Chat answers: it saves only if you say "save".

## Analyse
```
Job: analyse
Project: <project folder name>
Question: <what do you want to know>
Window (default): 
Cohort / vertical (default): 
Compare against (default: previous period): 
Metrics (default: the agreed definitions): 
Decision it feeds (optional): 
```
Example: `Job: analyse / Project: egregiously-miscalibrated-promises / Question: why did on-time drop for Pune SDD in September / Window: Sept vs Aug`

## Model
```
Job: model
Project: <project folder name>
Change to test: 
Assumptions (with values if you have them): 
Time period: 
Options to compare (optional): 
Decision it feeds (optional): 
```

## Design
```
Job: design
Project: <project folder name>
PRD (paste text or key points): 
Need: requirements doc | metrics | data check | events to track | experiment plan   (pick any)
For an experiment: hypothesis, main metric, who is eligible, planned split
Decision it feeds (optional): 
```

## Rollout
```
Job: rollout
Project: <project folder name>
What is being launched: 
Plan: <stages, locations, % of traffic or orders, settings, how long>
Success and safety metrics: 
Decision it feeds (optional): 
```

## Measure
```
Job: measure
Project: <project folder name>
Stage: before launch | day 1 | day 7 | other day | final result
Launch date: 
Compare against: <control group, or the period before launch>
Metrics: <names, or "from the PRD" and paste it>
Cuts you want (the agent will suggest more): 
Dashboard spec needed: yes | no
Target and safety limits (if known): 
Decision it feeds (optional): 
```

## Update shared knowledge
```
Job: update-context
Change: table | metric | rule | query
Details: <table name, or metric and its meaning, or the rule, or paste the SQL>
```

## A query failed
Paste the error or the strange result. The agent fixes the query and sends it again.

## Re-run an old analysis
`Job: analyse / Project: <project folder name> / Re-run: <note or script name> / New file: <csv>`

## Manual commands
```bash
scripts/new-file.sh <project> insights <project>-<topic> md
scripts/commit-and-push.sh "message" <path> [path...]
python3 scripts/validate-csv.py <file> --key order_id --require order_id,digitised_ts
```
