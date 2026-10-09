#!/bin/bash
# Commit and push only the paths you name. Never stages anything else.
# Usage: scripts/commit-and-push.sh "Commit message" <path> [path...]
# Example: scripts/commit-and-push.sh "Add note: sdd adherence (v1)" archives/pba-integration/insights/2026-10-09-sdd-adherence-v1.md

cd "$(dirname "$0")/.." || exit 1

MSG="$1"
shift

if [ -z "$MSG" ] || [ "$#" -eq 0 ]; then
  echo "Usage: commit-and-push.sh \"message\" <path> [path...]" >&2
  exit 1
fi

git add -- "$@" || exit 1

if git diff --cached --quiet -- "$@"; then
  echo "Nothing to commit for the given paths" >&2
  exit 1
fi

echo "Committing: $MSG"
git commit -m "$MSG" -- "$@" || exit 1

echo "Pushing..."
git push || exit 1
echo "Pushed."
