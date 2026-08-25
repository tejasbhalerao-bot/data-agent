# Promise Freeze and Reselection Rules

**Project:** Egregiously Miscalibrated Promises
**Date:** 2026-08-25

---

## The freeze contract

Once a delivery date D is shown to a customer, **D must freeze**. Subsequent runs of the system ask:

> "Which courier can hit D?"

Not:

> "Which courier gives the best date?"

This is the fundamental constraint. The customer has been shown a date; the system's job from that point is to fulfil that specific date, not to find a new optimal date.

---

## When reselection is and is not allowed

Reselection at shipping time is **explicitly identified as breaking the promise contract**. It should only be triggered by a genuine operational reason, not by a score improvement found at shipping time.

**Legitimate reselection triggers:**
- Contents of the order changed
- Dispatch slipped (order did not ship on the originally planned day)
- No courier in the pool can hit D

**Not a legitimate trigger:**
- A different courier has a better score now than it did at promise time

---

## Step 13 verbatim (from the 14-step system)

> Lock it in. Save the courier and the date together. Do not re-pick the courier at shipping. If the courier genuinely has to change, run steps 9 to 11 again and update the customer's date.

Note: when a reselection is forced by a genuine trigger, the customer's date is also updated — the freeze applies to the courier-date pair, not to D in isolation if a legitimate reason to change exists.

---

## Open questions (unresolved)

These were identified during the design session and not yet answered:

1. **Clock start for adherence:** Where does the clock start for adherence measurement — actual pickup or predicted pickup? This determines whether pickup compliance is a hidden gap in the system. If the clock starts at predicted pickup but the courier picks up late, those late-to-pickup days are invisible to the scoring model.

2. **Buffered-condition utilisation:** What percentage of buffered days actually had the buffered condition in force? If buffers are adding days to promises on lanes where the trigger condition (e.g. after-cutoff placement) rarely fires, those days are pure waste.

3. **Allocation share and sample size (winner's curse diagnostic):** Is allocation share correlated with sample size? A courier that wins more frequently accumulates more data, making its score estimate more stable and more likely to continue winning — potentially locking out the competitor even if true performance is similar. This is the winner's curse in courier selection.
