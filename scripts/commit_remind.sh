#!/usr/bin/env bash
# Fires after each Claude turn. If on a feature branch with uncommitted changes,
# prompts Claude to complete the COMMIT workflow (Steps 3-5).
b=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
c=$(git status --porcelain 2>/dev/null)
if [[ "$b" =~ ^(feat|fix)/ ]] && [[ -n "$c" ]]; then
    echo "COMMIT_HOOK: uncommitted changes on $b — if implementation is complete, run the COMMIT workflow: stage all files, commit with a Conventional Commits message, and push to origin/$b. Use scripts/commit.ps1 -Message \"feat(scope): description\""
    exit 2
fi
exit 0
