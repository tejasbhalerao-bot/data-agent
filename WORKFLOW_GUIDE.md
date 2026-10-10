# Workflow Guide

Copy a template, fill it in, send it. Anything missing that the agent needs, it asks once.

Quick question? Skip the template. Write one sentence and name the project.

Every request gets a note (a `.md` file in the project). The chat reply is a short summary.

## What happens
1. The agent checks your request. If a saved note with the same scope already has the answer and is recent enough, it uses it (7 days for a rolling window like "last 30 days"; no limit for a fixed past period like "July 2026").
2. It shows you a short brief of what it will do, including a numbered list of the metrics and cuts it will produce. The first line says how it understands the product flow. Correct it or approve it. Nothing starts before you approve.
3. It adds a "Queries to run" section to the same note. Each query is its own file in the project's `queries-dump/` folder, and the section lists them with the file names to save as. It tells you in chat.
4. You run them in Metabase. Save the CSVs in the project's `raw-data/` folder.
5. The agent checks the CSVs and calculates the numbers with scripts, each its own file in the project's `scripts/` folder. The note lists them under "Scripts and outputs", with the command to re-run each. Then it answers.
6. Each stage is saved on your computer automatically. You say "ok", then it goes to GitHub.

## Analyse
```
Job: analyse
Project: <project folder name>
Question: <what do you want to know>
Window: 
Cohort / vertical: 
Each row should be (optional): <for example one order>
Columns you need (optional): 
Compare against: 
Metrics (blank = the agreed definitions): 
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
