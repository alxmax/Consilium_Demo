# Usage & Efficiency Reporting — Pending Proposal

**Status:** PENDING (not implemented). Captured via `/consilium` (2026-05-17). Awaiting explicit go-ahead before any code change.

**Origin question (user):** *"As vrea ca senatul sa aibe si un raport cu usage-ul total folosit astfel incat pe viitor daca vreau sa compar senatul cu altceva sa stiu cat e de eficient si poate sa vin cu propuneri de eficentizare, de asemenea fiecare mod cum e paralel etc sa poate sa raporteze si cati tokeni in total a folosit, ganditi-va la un mod calculare a usage-ului astfel incat sa stiu eficienta fiecare modului de flow voce etc."*

## Goal (success criterion)

After any `/consilium <mode>` run (incl. `senate`), the orchestrator emits a usage snapshot per voice/senator, persisted in the run JSON. Cross-run rollup (`scripts/usage.py` extended + new `scripts/efficiency.py`) returns a single comparable efficiency score per mode so user can decide whether Senate's ~2.3x cost is justified vs Trias, Parallel, etc.

**Verification:**

```bash
python -X utf8 scripts/efficiency.py --by-mode
# Returns JSON: per mode, total_tokens (estimated), total_dispatches, total_latency_ms,
# OK_count (from FEEDBACK.html), tokens_per_OK (efficiency metric, lower = better).
```

Smoke acceptance: after 5 senate runs + 5 sequential runs with telemetry, `efficiency.py` returns non-null `tokens_per_OK` for both modes and the two values differ.

## User decisions (clarity gate answers)

| Question | Answer |
|---|---|
| Token source | **Hybrid**: estimate from chars (`~4 chars/token`) **AND** track `latency_ms` + `dispatch_count` (no manual user entry) |
| Efficiency metric | **Single score**: `total_tokens / count_OK_outcomes` (from `FEEDBACK.html`) |
| Delivery scope | **Full**: design doc + impl + new `scripts/efficiency.py` + UI tab in `docs/architecture.html` |

## Gap analysis (current infra)

1. `scripts/usage.py` already aggregates `telemetry.voices.{tokens_in, tokens_out, latency_ms}` from `runs/*.json` — but the `telemetry` block is **optional and rarely populated** because orchestrator has no discipline/script that emits it.
2. `runs/senate/*.json` (written by `senate_synth.py`) has **zero telemetry** — Senate is entirely invisible to `usage.py`.
3. `usage.py` walks only `runs/`, not `runs/senate/`.
4. No efficiency metric exists — only raw token totals (per voice, per mode).
5. `docs/architecture.html` has no usage/efficiency tab.

## Proposed design

### Token estimation rule (hybrid — answer 1+3)

For every sub-agent dispatch (voice or senator), orchestrator computes immediately after the dispatch returns:

```python
tokens_in_est  = ceil(len(prompt_text) / 4)
tokens_out_est = ceil(len(response_text) / 4)
latency_ms     = <wall-clock from dispatch start to return>
dispatch_count = 1
```

Persisted into the run's `telemetry.voices` block (existing schema in `runs/README.md`). Senate adds analogous `telemetry.senators` block (new schema, mirror shape).

**Why chars/4?** OpenAI/Anthropic tokenizer rule-of-thumb; error band ~±10–20% but consistent across modes, which is what matters for relative comparisons. Acceptable per user's answer.

**Why also latency + dispatch count?** User chose option 3 in tandem. Latency catches I/O bound modes (Senate's 7 senators ≈ 7 sequential dispatches, even if Sonnet); dispatch_count is the rock-bottom proxy if token estimation drifts.

### Senate telemetry schema (new in `runs/senate/<file>.json`)

```json
{
  "telemetry": {
    "mode": "senate",
    "dispatch_count": 7,
    "passes": 1,
    "senators": {
      "wittgenstein": {"tokens_in": 1850, "tokens_out": 420, "latency_ms": 3100},
      "aurelius":     {"tokens_in": 1850, "tokens_out": 510, "latency_ms": 3400},
      "...":          {"...": "..."}
    },
    "total_tokens_in":  12950,
    "total_tokens_out":  3300,
    "total_latency_ms": 23400
  }
}
```

For multi-round senate: `dispatch_count` includes all rounds + cross-questions + blocaj_resolution dispatches. `passes` = number of rounds executed.

### `scripts/efficiency.py` (new)

```
scripts/efficiency.py — compute single-score efficiency per mode.

CLI:
  python scripts/efficiency.py --by-mode
  python scripts/efficiency.py --by-mode --since 2026-05-01
  python scripts/efficiency.py --compare senate parallel sequential
  python scripts/efficiency.py --since 2026-05-01 --json    # raw JSON for piping

Output (default --by-mode):
{
  "since": "2026-05-01",
  "modes": {
    "sequential":  {"runs": 27, "total_tokens": 81200, "OK_outcomes": 22, "tokens_per_OK": 3691, "dispatches": 81, "avg_latency_ms_per_run": 4200},
    "parallel":    {"runs":  9, "total_tokens": 41800, "OK_outcomes":  7, "tokens_per_OK": 5971, "dispatches": 27, "avg_latency_ms_per_run": 1800},
    "senate":      {"runs": 12, "total_tokens": 148600, "OK_outcomes": 9, "tokens_per_OK": 16511, "dispatches": 84, "avg_latency_ms_per_run": 24000}
  },
  "ranking": [
    {"mode": "sequential", "tokens_per_OK": 3691, "rank": 1},
    {"mode": "parallel",   "tokens_per_OK": 5971, "rank": 2},
    {"mode": "senate",     "tokens_per_OK": 16511, "rank": 3}
  ]
}
```

**Inputs:**
- `runs/*.json` → telemetry.{mode, voices}
- `runs/senate/*.json` → telemetry.{mode=senate, senators}
- `FEEDBACK.html` → `outcome` column (`OK` count per chosen) — joined back to runs via `run-path` reference in FB rows

**Join key:** each FB row has `--run-path runs/<file>.json` argument (per `log_feedback.py`); efficiency.py parses this from the FB row to map outcome → mode.

**Caveats documented in script docstring:**
- OK_count is subjective unless `[confirmed]` marker present (mark_outcome.py). Script emits a parallel column `confirmed_OK_count` weighted 2x same as `priors.py weighted_bad_rate`.
- Modes with <3 runs marked `insufficient_data` (efficiency = null, not 0).
- Senate's `MODIFY` verdict ≠ failure; counts as OK if user did not override. Senate's `STOP` counts as OK only if user accepted.

### `scripts/usage.py` extensions

1. Walk both `runs/*.json` and `runs/senate/*.json` (currently only the first).
2. Add `senators` voice bucket alongside `{generator, control, conservator}`.
3. Add `--mode <name>` filter flag.

### `scripts/senate_synth.py` extension

After `build_bundle(...)`, accept optional `telemetry` kwarg from orchestrator (passed in input JSON or written post-hoc via separate `log_senate_telemetry.py`). Persist into bundle alongside existing fields. No breaking change — telemetry omitted from existing fixtures still valid.

### Orchestrator discipline (SKILL.md addition)

New subsection under "Workflow" Step 6 ("Report"):

> **6c — Telemetry emission (mandatory after Step 6).**
> Before persisting the run JSON, orchestrator MUST populate `telemetry.voices` (or `telemetry.senators` for senate) with `{tokens_in, tokens_out, latency_ms}` per dispatched voice. Use chars/4 for tokens. If a dispatch failed/retried, sum across attempts. Set `telemetry.mode` to the canonical mode label matching the dispatch table in `## Dispatch defaults`.
>
> Why mandatory: `scripts/efficiency.py` returns null for any run with missing telemetry, polluting per-mode averages. A run that ships without telemetry is invisible to efficiency comparisons.

### UI — new tab in `docs/architecture.html`

Tab name: **Usage & Efficiency**.

Content (static at first; later: live read of `efficiency.py --json` baked at build):
- Table: mode × {runs, tokens, OK_count, tokens_per_OK, rank}
- Bar chart (vanilla SVG, no deps): tokens_per_OK per mode, sorted ascending (lower = better)
- Caveats section: estimation accuracy ±10-20%, OK subjectivity, dispatch_count fallback when tokens missing
- Link to `efficiency.py` for live data

## Estimated impact

| File | Change | LOC |
|---|---|---|
| `scripts/efficiency.py` (new) | full script | ~180 |
| `scripts/usage.py` | walk senate dir + senators bucket + --mode filter | ~40 |
| `scripts/senate_synth.py` | accept telemetry kwarg + persist | ~20 |
| `SKILL.md` | new 6c subsection + Resources row | ~25 |
| `docs/architecture.html` | new tab + bar chart | ~150 |
| `runs/README.md` | telemetry.senators schema | ~10 |
| **Total** | | **~425 LOC** |

## Open questions (resolve before promoting from pending)

1. **OK_count attribution to Senate.** Senate verdicts (`GO`/`MODIFY`/`STOP`/`DEEPLY_SPLIT`/`UNREACHABLE`) don't map 1:1 to `OK`/`BAD`/`OVR`/`PEND` in FEEDBACK. Need a mapping table — proposed: GO+user-proceeds→OK; STOP+user-accepts→OK; MODIFY→OK only if user logs follow-up; DEEPLY_SPLIT/UNREACHABLE→PEND. Confirm before impl.
2. **Tokens_in inflation on Senate.** Each senator gets ~same prompt; total_tokens_in = 7 × prompt_chars. Want to count "deliberation tokens" or "user-charged tokens"? Both valid. Proposed: total = raw sum (closer to real cost). Confirm.
3. **Trias mode reporting.** 9 sub-agents = 3 personalities × 3 voices. Persist as `telemetry.personalities.{pioneer,architect,steward}.voices.{...}` or flatten to 9 entries under `voices`? Recommend nested (preserves personality dimension for future "per-personality cost" analysis).
4. **Eval harness.** Add an `evals/` scenario covering "efficiency.py returns deterministic result on fixture telemetry" to `run_evals.py`. Recommend yes.

## Promotion criteria (pending → implementation)

User explicit go-ahead OR /consilium re-run on this proposal with chosen=`implement_efficiency_proposal` and confidence ≥ 0.7.

## References

- Existing infra: `scripts/usage.py`, `runs/README.md` telemetry schema, `scripts/log_feedback.py`
- Related: `scripts/priors.py` (signal source for OK_rate), `scripts/mark_outcome.py` (confirmed marker)
- Mode cost multipliers: SKILL.md `## Dispatch defaults` section
