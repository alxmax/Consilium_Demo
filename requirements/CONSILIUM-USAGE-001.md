---
id: CONSILIUM-USAGE-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# usage

> Aggregates telemetry across runs into per-voice + per-mode token/latency stats.

## Input
- `--runs <path>`: optional path to runs directory (default: `.consilium/runs` from `CONSILIUM-UTILS-001 RUNS_DIR`)
- `--last <N>`: optional integer, restrict to the most-recent N run files
- `--mode <name>`: optional string filter on `telemetry.mode` (e.g. `trias`, `sequential`)

## Description
Aggregates telemetry across all run JSON files in the runs directory and emits a structured usage report with per-voice and per-mode breakdowns. For each voice it computes count, sum, mean, p50, and p95 over `tokens_in`, `tokens_out`, and `latency_ms`; for each mode it accumulates total tokens and latency, using max latency across voices for parallel/Trias modes to reflect wall-clock cost rather than summed sequential cost. It also detects latency spikes in parallel runs by flagging any voice whose latency exceeds 2x the median of its peers. The script exists to quantify the ROI of the scope gate (skipped runs cost no voice tokens) and to compare deliberation cost across modes.

## Output
- JSON object to stdout with keys: `runs_total`, `with_telemetry`, `skipped_runs`, `voices` (per-voice percentile stats), `modes` (per-mode token/latency totals), `warnings` (latency spike list)
- exit code 0 on success; 1 if the runs directory does not exist

## WHAT — Verify intent (open questions for the human)
- None — doc is unambiguous.

## Acceptance (= tests)
- Running against a populated runs directory emits valid JSON with `runs_total` equal to the number of JSON files loaded.
- Skipped runs (`skipped=true`) are counted in `skipped_runs` but excluded from voice token statistics.
- For a Trias or parallel mode run, the mode's `latency_ms` reflects the maximum voice latency rather than the sum.
- The `--mode` flag filters the breakdown so only runs matching that `telemetry.mode` value appear in the `modes` and `with_telemetry` counts.
- A voice whose latency exceeds twice the median of its peers in a parallel run appears in the `warnings` array with `type='latency_spike'`.
