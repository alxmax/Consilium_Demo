#!/usr/bin/env bash
# Stop hook: remind to commit on feat/* or fix/* branches if there are staged/unstaged changes.
branch=$(git branch --show-current 2>/dev/null)
if [[ "$branch" == feat/* || "$branch" == fix/* ]]; then
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "Uncommitted changes on branch '$branch' -- run git add + commit + push."
    fi
fi
