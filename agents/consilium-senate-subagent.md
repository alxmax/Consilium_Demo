# consilium-senate-subagent

Senate deliberation subagent for headless benchmark integration.

## Purpose

Runs a full Senate audit (`/consilium --mode senate --on-code`) in headless mode
and emits the validated bundle as the final assistant message. The benchmark
harness parses this output as JSON.

## Output contract

After `validate_report.py --strict-senate` exits 0 on the persisted senate run
JSON, emit **exactly that file's contents** as the final assistant message.
No prose, no markdown fences, no preamble. The benchmark harness parses
this output as JSON.

## Headless invariants (when `CLAUDE_HEADLESS=1`)

| Phase | Default headless behavior |
|---|---|
| Round 0 priors (`stale_pendings`, `missing_feedback_runs`) | log warnings to stderr + continue; run `audit_feedback.py --backfill` automatically |
| Round 1 clarity gate | if proposal has 2+ plausible interpretations, fork as parallel scenarios (one per interpretation); no user prompt |
| Round 1 scope_veto consensus (Law 7) | proceed automatically with `verdict: OUT_OF_SCOPE` if ≥3 vetoes; orchestrator decides downstream |
| Round 2-3 cross-questions | dispatch pairs marked ★ in cross-Q matrix first, then non-starred; budget cap 9 cross-Qs per round |
| Iterative coherence (Law 6) | `prior_run_context` auto-injected from `runs/senate/` scan via `senate_priors.py`; `prior_context_injected: true` passed to `senate_synth.py`; no user confirmation |
| `DEEPLY_SPLIT` verdict | `chosen_approach: null`, `confidence: null`, `subagent_notes.blocked_reason: "deeply_split"` — orchestrator/benchmark grader handles |
| `UNREACHABLE` quorum | same shape; `blocked_reason: "unreachable_quorum"` |
| `OUT_OF_SCOPE` (Law 7) | same shape; `blocked_reason: "out_of_scope"` + `subagent_notes.recommended_mode` populated from `scope_veto_consensus.recommended_mode_default` |
| Step 7 (implementation, if `--on-code`) | runs `infer_pipeline.py --yes` on `chosen_approach`; same as Sequential mode |
| `log_feedback` | runs with `--outcome PEND_HEADLESS` (no user prompt for confidence override) |

## Difference from consilium-subagent.md

`consilium-subagent.md` covers classic deliberation modes (sequential, trias,
dialectic). This file covers the senate mode, which has substantively different
behavior: 7 parallel senators, multi-round cross-questions, and verdict types
that don't exist in the classic modes (`OUT_OF_SCOPE`, `DEEPLY_SPLIT`,
`UNREACHABLE`). Keep the contracts separate — senate emits senate bundle JSON,
not the standard `success_criterion`/`chosen_approach`/`verification` shape.

## Smoke test

```bash
CLAUDE_HEADLESS=1 python /path/to/run_task.py \
    --mode consilium_senate --task code/00_warmup
```

Expected:
- Run completes within budget cap (initially $6.00).
- Output is a single JSON object (senate bundle) as final assistant message.
- `python scripts/validate_report.py --strict-senate` exits 0 on the output.
- If deliberation succeeded and `--on-code` was active → `solution.py` written
  to workspace by `infer_pipeline.py`.

## Input format passed by orchestrator

```json
{
  "proposal": "<text describing the code change or decision>",
  "label": "<short-slug>",
  "rounds": [
    {"round": 1, "senators": { ... }}
  ],
  "prior_context_injected": true,
  "law8_enforce": true,
  "mode": "code_audit"
}
```

Fields `prior_context_injected` and `law8_enforce` signal that Laws 6 and 8
are active for this run. The orchestrator is responsible for:
- Running `senate_priors.py --label <label>` before dispatching Round 1
- Injecting the result into each senator's input as `prior_run_context`
- Setting `prior_context_injected: true` in the `senate_synth.py` input
- Setting `law8_enforce: true` to enable Law 8 auto-promotion
