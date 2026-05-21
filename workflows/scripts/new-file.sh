#!/bin/bash
# Create a versioned file in a project folder.
#
# Usage:
#   ./workflows/scripts/new-file.sh <project> <folder> <descriptor> <ext>
#
# Example:
#   ./workflows/scripts/new-file.sh pba analysis-plans pba-analysis-plan md
#   → archives/pba/analysis-plans/2026-05-21-pba-analysis-plan-v1.md
#
# Folders: analysis-plans | queries-dump | scripts | insights | tests | outputs | context

set -e

PROJECT="$1"
FOLDER="$2"
DESCRIPTOR="$3"
EXT="$4"

if [[ -z "$PROJECT" || -z "$FOLDER" || -z "$DESCRIPTOR" || -z "$EXT" ]]; then
  echo "Usage: $0 <project> <folder> <descriptor> <ext>"
  echo "Example: $0 pba analysis-plans pba-analysis-plan md"
  exit 1
fi

# _context is a special project that maps to context/ at repo root
if [[ "$PROJECT" == "_context" ]]; then
  TARGET_DIR="context/$FOLDER"
else
  TARGET_DIR="archives/$PROJECT/$FOLDER"
fi

if [[ ! -d "$TARGET_DIR" ]]; then
  if [[ "$PROJECT" == "_context" ]]; then
    mkdir -p "$TARGET_DIR"
  else
    echo "Error: folder '$TARGET_DIR' does not exist."
    echo "Create project first: cp -r archives/_template archives/$PROJECT"
    exit 1
  fi
fi

# Find highest existing version for this descriptor
MAX_V=0
for f in "$TARGET_DIR"/*-"$DESCRIPTOR"-v*.* ; do
  [[ -e "$f" ]] || continue
  V=$(echo "$f" | grep -oE '\-v[0-9]+\.' | grep -oE '[0-9]+')
  if [[ -n "$V" && "$V" -gt "$MAX_V" ]]; then
    MAX_V="$V"
  fi
done

NEXT_V=$((MAX_V + 1))
DATE=$(date +%Y-%m-%d)
FILENAME="${DATE}-${DESCRIPTOR}-v${NEXT_V}.${EXT}"
FILEPATH="${TARGET_DIR}/${FILENAME}"

touch "$FILEPATH"
echo "Created: $FILEPATH"
