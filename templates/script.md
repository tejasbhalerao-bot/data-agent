# Script file layout

A script is a `.py` file made with `scripts/new-file.sh <project> scripts aggregate-<topic> py`. It starts with this comment block, then the code.

```python
# Purpose: <what it calculates, in a few words>
# Serves: <M-IDs from the brief>
# Reads: <the CSV, by full path, and the Q-ID that produced it>
# Writes: <each file written to archives/<project>/outputs/, by full path>
# Run with: python3 archives/<project>/scripts/<this file>

import sys
import pandas as pd

def main():
    df = pd.read_csv("archives/<project>/raw-data/<name>.csv")
    # apply the cuts from the brief, then write the tables to outputs/
    # print each table so the note can cite it
    ...

if __name__ == "__main__":
    main()
```

Rules: every figure in the note comes from an output of a script like this. A script changed after its output has been used is a new version (`-v2`), never an edit in place. Add a test (`scripts/new-file.sh <project> tests test-<script> py`) if the script classifies, does date arithmetic or joins.
