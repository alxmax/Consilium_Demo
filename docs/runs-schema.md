# Deliberation Runs

Each time the skill is invoked on a real task, the agent writes the full
deliberation as a JSON file to `.consilium/runs/` at the end of Step 6.
Files are gitignored — they're personal logs that feed the priors loop,
not part of the skill itself. The data directory layout and the path
constants that locate it (`RUNS_DIR`/`FEEDBACK_PATH`) live in
`scripts/utils.py`.

Filename: `YYYY-MM-DD_HHMM_<short-label>.json`
Example: `2026-05-12_1430_pr42-extract-helper.json`

## Schema

The exact shape is enforced by `scripts/validate_report.py`. Required
fields are marked **REQUIRED**; the rest are recommended but not blocking.

### Full deliberation report

```json
{
  "success_criterion": "REQUIRED — testable sentence from Step 1",
  "verification": "REQUIRED — concrete check that proves success_criterion",
  "chosen_approach": "approach_id OR null (if all candidates vetoed)",
  "reasoning": "short summary of why chosen won",
  "alternatives": [
    {"id": "...", "summary": "...", "why_not": "..."}
  ],
  "voice_scores": {
    "generator": 0.8,
    "control": 0.9,
    "conservator": 0.4
  },
  "confidence": 0.85,
  "telemetry": {
    "mode": "sequential | parallel | dialectic | trias | senate",
    "dispatch_count": 3,
    "passes": 1,
    "voices": {
      "generator":   {"tokens_in": 1200, "tokens_out": 400, "latency_ms": 3500},
      "control":     {"tokens_in":  800, "tokens_out": 200, "latency_ms": 2100},
      "conservator": {"tokens_in":  900, "tokens_out": 180, "latency_ms": 1800}
    },
    "senators": {
      "wittgenstein": {"tokens_in": 2000, "tokens_out": 500, "latency_ms": 3100},
      "aurelius":     {"tokens_in": 2000, "tokens_out": 510, "latency_ms": 3400},
      "confucius":    {"tokens_in": 2000, "tokens_out": 490, "latency_ms": 3200},
      "socrate":      {"tokens_in": 2000, "tokens_out": 520, "latency_ms": 3300},
      "musk":         {"tokens_in": 2000, "tokens_out": 480, "latency_ms": 2900},
      "dimon":        {"tokens_in": 2000, "tokens_out": 510, "latency_ms": 3100},
      "napoleon":     {"tokens_in": 2000, "tokens_out": 500, "latency_ms": 3000},
      "deming":       {"tokens_in": 2000, "tokens_out": 505, "latency_ms": 3050},
      "tacitus":      {"tokens_in": 2000, "tokens_out": 515, "latency_ms": 3150}
    },
    "personalities": {
      "pioneer":   {"tokens_in": 5200, "tokens_out": 1400, "latency_ms": 8000},
      "architect": {"tokens_in": 5200, "tokens_out": 1400, "latency_ms": 8200},
      "steward":   {"tokens_in": 5200, "tokens_out": 1400, "latency_ms": 7900}
    },
    "total_tokens_in": 12950,
    "total_tokens_out": 3300,
    "total_latency_ms": 23400
  },
  "deliberation_log": [
    {"step": "generator",   "candidates": [...]},
    {"step": "control",     "verdicts":   [...]},
    {"step": "conservator", "scores":     [...]},
    {"step": "aggregate",   "scheme": "conservative_override", "result": {...}}
  ]
}
```

### Skipped report (scope_gate said the change is too small to deliberate)

```json
{
  "success_criterion": "REQUIRED",
  "verification": "REQUIRED",
  "chosen_approach": "skipped",
  "skipped": true,
  "skip_reason": "REQUIRED when skipped=true — e.g. '1 file, 4 lines, no sensitive paths'",
  "signals": {
    "files_changed": 1,
    "lines_changed": 4,
    "blocklist_hits": []
  },
  "voice_scores": null,
  "confidence": null,
  "alternatives": [],
  "deliberation_log": []
}
```

## Field notes

- **`telemetry`** is optional. Fill what you can measure (parallel/dialectic
  give per-voice latencies; sequential mode often can't isolate per-voice
  tokens) and omit the rest. Downstream readers tolerate missing blocks.
- **`chosen_approach`** can be `null` legitimately when `aggregator.py`
  with `conservative_override` vetoes every candidate. In that case
  `deliberation_log[aggregate].result` should carry `retry_suggested`.
- **`deliberation_log[aggregate].result`** is what `scripts/priors.py`
  inspects to compute `conservator_veto_rate` — if you change its shape,
  update the `_run_had_veto` helper in `scripts/priors.py` to match.

## Consumers

- **`scripts/priors.py`** — at start of each new deliberation, summarizes
  recent runs to surface patterns (override rate, veto rate, repeating
  keywords).
- **`scripts/feedback.py`** — counts schemes used across runs (reads from
  `deliberation_log[aggregate].scheme`).
- **`scripts/memory.py`** — uniform read API over runs (medium tier).
- **`scripts/validate_report.py`** — shape-check before persisting a
  report; fails fast if `success_criterion`/`verification` are missing.
