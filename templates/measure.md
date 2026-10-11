# Measure: metrics report

Goes under "Answer" in the note. Delete the guidance in angle brackets. Keep only the section for the stage being reported.

**Stage:** baseline | day 1 | day 7 | other day | final result  **Launch date:**  **Compared against:**  **Earlier notes used:** <baseline note, rollout note, design note>

## Headline
<One or two sentences: the result for this stage, and the decision it supports.>

## Baseline (stage: baseline)
- **Windows:** <baseline and comparison windows, as decided by Tejas.>
- **Checks:** <row counts reconcile, key unique, no missing days.>
- **Frozen snapshot:** <the CSV, listed in "Queries to run". Never overwritten.>
- **Alert limits proposed:** <metric, limit.>

## Check (stage: day 1, day 7, other day)
- **Are the events firing:** <yes or no, with evidence.>
- **Safety metrics against limits:** <table.>
- **Anything odd:** <list.>
- **Early read:** <direction only, marked "too early to call".>

## Final result (stage: final result)
| Metric | Baseline or control | Launch | Difference | 95% interval | Enough data? |
|--------|---------------------|--------|------------|--------------|--------------|
| <M-ID: name> | | | | | |
- **Cuts:** <where the effect is bigger or smaller.>
- **Side effects:** <safety metrics.>
- **Decision:** ship | iterate | kill, and the reason.

## Dashboard spec (only if requested)
| Card | Query (Q-ID) | Filters and cuts | Refresh | Alert limit |
|------|--------------|------------------|---------|-------------|
Dashboard queries may aggregate. Tejas builds the dashboard in Metabase from this table.

## Evidence
<Full tables. Cite each by metric, script and output file (local only).>
