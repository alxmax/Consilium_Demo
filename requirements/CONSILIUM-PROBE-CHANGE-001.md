---
id: CONSILIUM-PROBE-CHANGE-001
status: confirmed
layer: feature
owner: auto
depends_on: []
risk: 1
---

# probe_change

> Returns objective git diff metrics (files/lines changed, optional per-file churn) as JSON.

## Input
- CLI flag `--ref REF`: diff `REF..HEAD` (e.g. `--ref main` or `--ref HEAD~3`); mutually exclusive with `--range`
- CLI flag `--range A..B`: explicit diff range; mutually exclusive with `--ref`
- CLI flag `--files ...`: restrict the diff to specific file paths
- CLI flag `--churn N`: also count commits per changed file over the last N days via `git log --since`
- Working-tree git state: default mode diffs staged + unstaged changes against HEAD
- `git` executable on PATH

## Description
Anchors Conservator's `diff_size` risk factor in objective git data instead of intuition by running `git diff --numstat` and returning the count of changed files and lines added/removed as JSON. It exists because without ground-truth diff metrics Conservator must guess the magnitude of a change, which introduces systematic bias; with this output the aggregator can apply a calibrated `diff_size` score. The optional `--churn` flag adds per-file commit frequency over a configurable lookback window, giving Conservator a second ground-truth signal for `regression_risk`: a file touched eight times in fourteen days is fragile, while one untouched for two years is stable. The script deliberately excludes `modules_touched` and `shared_paths_hit` because those require per-project configuration that would force the script to crash or guess; scope_drift and regression judgment remain with Conservator. On any git error (missing executable, bad ref, non-repo) the script emits `{"error": "..."}` to stdout and exits 1 rather than raising a traceback.

## Output
- JSON object to stdout with `files_changed`, `lines_added`, `lines_removed` (integers)
- When `--churn N` is passed, the JSON object also contains a `churn` key with `window_days` and `commits_per_file` (dict of path -> commit count)
- JSON object `{"error": "..."}` to stdout and exit code 1 on any git error or invalid arguments
- exit code 0 on success

## Acceptance (= tests)
- Running with no flags against a git repo with unstaged changes returns a JSON object with `files_changed >= 1` and correct `lines_added` / `lines_removed` counts matching `git diff --numstat HEAD` output.
- Running with `--ref main` returns diff statistics for the range `main..HEAD`, not the working tree.
- Running with `--churn 14` returns an additional `churn.commits_per_file` dict keyed by changed file paths, with non-negative integer values.
- Running outside a git repository (or with a bad `--ref`) outputs `{"error": "..."}` to stdout and exits 1 without printing a Python traceback.
- File paths containing non-ASCII characters or spaces are correctly decoded from git's C-quoted output and appear unescaped in the JSON result.
