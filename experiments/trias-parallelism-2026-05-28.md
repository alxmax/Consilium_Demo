# Trias parallelism empirical audit (2026-05-28)

## Question

`modes/trias.md` Step 3 mandates parallel dispatch of the 3 personality sub-agents in a single orchestrator message:

> *"Dispatch all 3 personalities in parallel (3 consilium-subagent Agent calls in the same orchestrator message)... Parallel dispatch is mandatory — sequential dispatch triples wall-clock for no quality gain, and is the root cause of the task-08 timeout pattern observed in benchmark n=10 (2026-05-27)."*

Does this actually happen at runtime?

## Method (revised — deterministic)

Initial attempt used `api/wall ratio` from `claude_raw.json` as a proxy. That measure is **dominated by orchestrator overhead between dispatches and Step 7 implementation**, not by the dispatch pattern itself — so it cannot cleanly distinguish parallel from serial.

Final method reads the **Claude CLI session JSONL transcript** at `~/.claude/projects/<encoded_cwd>/<session_id>.jsonl`. Each assistant message lists its tool_use blocks; the count of `Agent` blocks per assistant message tells us directly:

- **Parallel dispatch** → one assistant message with 3 `Agent` tool_use blocks.
- **Serial dispatch** → 3 consecutive assistant messages, each with 1 `Agent` tool_use block.

This is exact, not a proxy.

## Results

Backfilled across all `consilium_trias` workspaces with a saved JSONL:

| Task | Turns | Pattern | Max Agents in single message |
|---|---:|---|---:|
| code/01_circuit_breaker | 20 | **SERIAL** | 1 |
| reasoning/01_transport_choice/rep_1 | 2 | scale_down | 0 |
| reasoning/02_rule_of_three/rep_1 | 22 | **SERIAL** | 1 |
| reasoning/03_schema_migration/rep_1 | 25 | **SERIAL** | 1 |
| reasoning/04_binary_search_bug/rep_1 | 17 | no_dispatch_observed | 0 |
| reasoning/05_warehouse_contradiction/rep_2 | 2 | scale_down | 0 |
| reasoning/05_warehouse_contradiction/rep_3 | 4 | scale_down | 0 |
| reasoning/06_split_brain_db | 30 | **SERIAL** | 1 |
| reasoning/07_composite_index_prefix | 28 | **SERIAL** | 1 |
| reasoning/08_locking_strategy | 2 | scale_down | 0 |
| reasoning/09_pipeline_freshness | 29 | **SERIAL** | 1 |
| reasoning/10_checkout_degradation | 24 | **SERIAL** | 1 |
| reasoning/11_marathon_prep/rep_1 | 2 | scale_down | 0 |

For code/01_circuit_breaker, the JSONL shows the dispatch timestamps explicitly:

```
17:57:44.477  → Pioneer deliberation: circuit breaker C++17    (1 Agent call)
17:57:55.208  → Architect deliberation: circuit breaker C++17  (1 Agent call, +10.7s)
17:58:05.762  → Steward deliberation: circuit breaker C++17    (1 Agent call, +10.5s)
```

Each personality dispatched in its own assistant message, ~10 seconds apart.

## Findings

- **7/7 real-deliberation Trias runs (where the JSONL was located): perfectly SERIAL. `max_agents_in_message = 1`. Zero exceptions.**
- 5 scale_down runs correctly excluded (no dispatch to measure).
- 1 task (04) lookup ambiguous: JSONL found via glob fallback but contained no Agent dispatches, suggesting the wrong session was matched. Not a counterexample.

The descriptive mandate in `modes/trias.md` is **never honored at runtime** for the corpus measured. The orchestrator dispatches each personality in a separate message, waiting for one to return before issuing the next.

## Why the original `api/wall ratio` audit was misleading

The 9-minute Trias run on `code/01_circuit_breaker` consisted of:

- Conservator (in-context, no Agent call) — embedded in orchestrator turns
- Pioneer Agent call — 15.7s internal work (telemetry)
- Architect Agent call — 15.3s internal work
- Steward Agent call — 12.0s internal work
- Step 7 implementation: Coder writes solution.hpp + tests_self.cpp, compile, fix, test loop — **~8 minutes**
- log_feedback, validate_report, etc.

The 3 personality calls together = ~43 seconds. The remaining ~501 seconds = orchestrator overhead + Step 7 (which is inherently serial: Coder → Test Writer → Reviewer). Computing api/wall over the entire run averages all of this and produces a meaningless ratio near 1.0 regardless of how the 3 personalities were actually dispatched.

## What we shipped (2026-05-28)

`benchmark/scripts/check_trias_parallelism.py` reads the JSONL transcript and writes to `pipeline_audit.json`:

```json
{
  "trias_serial_dispatch": true,
  "trias_max_agents_in_message": 1,
  "trias_total_dispatches": 3,
  "trias_dispatch_pattern": "serial",
  "trias_num_turns": 20
}
```

`benchmark/run_task.py` invokes it post-run for every `consilium_trias` run. `benchmark/analyze.py` surfaces a `⚠ trias: serial dispatch (max=1)` badge in `report.html`.

## Implication for the spec

The 7-for-7 finding indicates the descriptive mandate in `modes/trias.md` Step 3 is reliably ignored.

### Prompt rewrite attempt (2026-05-28) — FAILED

Tested empirically. Replaced Step 3 with imperative phrasing, a worked correct-pattern example, and an explicit anti-pattern marked `DO NOT do this`. Re-ran `consilium_trias` on `code/01_circuit_breaker` with a clean workspace. JSONL transcript inspection:

```
18:41:04.663Z → Pioneer  (1 Agent call)
18:41:16.872Z → Architect  (+12s, 1 Agent call)
18:41:30.776Z → Steward   (+14s, 1 Agent call)
```

Still serial. Three separate assistant messages, max_agents_in_message=1. The run timed out at the 10-minute wall-clock cap. **Prompt rewrite reverted.** The orchestrator's bias toward serial dispatch for "deliberative" sub-agents is robust against imperative language at the spec level.

### Remaining paths forward

1. **Accept the cost.** Document that Trias on code tasks runs ~3× the personality time serially. Budget benchmark wall-clock caps accordingly (current 10-min cap fails Trias on most code tasks). The audit badge in `report.html` makes the drift permanently visible.
2. **Investigate model-side cause.** The orchestrator and sub-agents share the same model family. Deliberative-task dispatch may be a learned behavior pattern that prompts cannot override at the user-prompt layer. Out of scope here; would require either a different orchestration vehicle or a model fine-tune.
3. **Reduce Trias to 2 personalities.** If the cost can't be fixed by parallelizing, it can be fixed by halving the work. Tradeoff: lose Architect's balancing lens. Separate decision.

Decision: option 1 by default. Options 2 and 3 deferred.

### Senate audit (2026-05-28, MODIFY 6 · STOP 3 · GO 0)

[runs/senate/2026-05-28_220338-trias-parallelism-enforcement.json](../runs/senate/2026-05-28_220338-trias-parallelism-enforcement.json)

| Senator | Vote | Core point |
|---|---|---|
| Wittgenstein | MODIFY | "Parallel" has 3 coexisting definitions; success threshold not stated |
| Aurelius | MODIFY | `partial × moderate` quadrant; over-engineered; scope to (a) |
| Confucius | MODIFY | Only (a) consistent with `detect-log-don't-block` institutional pattern; (c)/(d) require architectural-layer review; (f) is structurally identical to deliverable-enforcement R2/R3 (rejected) |
| Socrate | MODIFY | N=1 rewrite ≠ "robust"; PreToolUse hook untested; user's "Python script" is 2 distinct proposals conflated |
| Musk | **STOP** | All options add complexity to a mode with no demonstrated value over Dialectic (benchmark: all 5 modes 100/100 including sonnet_bare); delete Trias |
| Dimon | MODIFY | Silent-failure modes in every option; quorum validation + session isolation mandatory |
| Napoleon | **STOP** | ROI break-even ~3-10 years at current Trias usage rate (low single-digit invocations/month) |
| Deming | **STOP** | N=1 rewrite attempt is statistically insufficient; need N≥5 variants across ≥2 prompt injection points |
| Tacitus | MODIFY | 0/6 clean-GO historical record for "prompt rewrite fixes model behavior"; 3/3 green for "detect-log-don't-block"; pin enforcement at orchestrator/check_doc_drift layer, NOT voice prompts |

**Convergent modify_requests:**
1. **Layer-pin (Tacitus, Confucius):** enforcement belongs in `scripts/check_doc_drift.py` + the orchestrator contract, not in voice prompts. — **SHIPPED 2026-05-28** (new invariant `trias_parallelism_runtime_audit` in `check_doc_drift.py`; runtime audit reference added to `modes/trias.md` Step 3 with pointer to `check_trias_parallelism.py`).
2. **N≥5 variant test (Deming, Socrate):** raise N above 1 before declaring prompt-enforcement falsified. Test PreToolUse hook + system prompt injection + 3-5 phrasing variants. — **DESIGN SHIPPED 2026-05-28** ([trias-parallelism-n5-design.md](trias-parallelism-n5-design.md)); execution deferred to user opt-in (~$6-10 spend).
3. **Semantic disambiguation (Wittgenstein, Socrate):** user must clarify "Python script" = read-by-orchestrator vs executed-as-validator, and defect = correctness vs performance. — **DEFERRED** to user.
4. **Cost-benefit gate (Napoleon):** no (c)/(d) implementation until Trias usage exceeds ~20 invocations/month. — **ACCEPTED**.
5. **Existential question (Musk):** does Trias justify 3× cost vs Dialectic? — **OPEN**; reopen if N≥5 experiment fails.

### What we shipped after the Senate audit

| Component | Pin layer |
|---|---|
| `benchmark/scripts/check_trias_parallelism.py` | Runtime detector (already shipped pre-Senate) |
| `benchmark/run_task.py` hook | Post-run audit invocation |
| `benchmark/analyze.py` badge | Visibility in `report.html` |
| `scripts/check_doc_drift.py` invariant `trias_parallelism_runtime_audit` | **NEW** — requires `modes/trias.md` to reference the runtime audit script; prevents the spec text from drifting away from the detector |
| `modes/trias.md` Step 3 audit reference | **NEW** — minimal pointer to the runtime audit (not a behavioral rewrite; the spec mandate stays the same) |
| `experiments/trias-parallelism-n5-design.md` | **NEW** — pre-registered N≥5 test plan with falsification criterion |

### What we did NOT ship (Senate dissent)

- Spec rewrite of `modes/trias.md` Step 3 with imperative phrasing — empirically falsified at N=1, reverted, and Tacitus's retrospective (0/6 clean-GO for voice-prompt enforcement) makes further attempts unjustified without first widening N via the V2-V7 design.
- `claude -p` subprocess launcher (option c) — breaks in-session contract; Confucius requires architectural-layer review before eligibility.
- Direct API Python orchestrator (option d) — loses MCP, prompt caching, session integration; Napoleon's ROI break-even is decade-scale.
- Pre-dispatch intent declaration script (option e) — Socrate flagged ambiguous semantics; would have the same failure mode as the spec rewrite if read by orchestrator.
- Reducing Trias 3→2 personalities (option b) — Dimon: introduces 1-1 tie silent-failure; Confucius: identity change requiring separate proposal.

## Cost picture (code/01_circuit_breaker, 2026-05-28 successful run)

| Component | Time | Notes |
|---|---:|---|
| Personality dispatches (Pioneer + Architect + Steward) | ~43s API time, ~32s wall | Could have been ~16s wall if dispatched in one message |
| Step 7 implementation | ~8 minutes | Inherently serial (Coder→Test Writer pipeline); not a parallelism concern |
| Orchestrator overhead between steps | ~30-60s | Routing decisions, intermediate scoring, etc. |
| **Total wall** | **9m 4s** | Of which ~10s could be saved by parallel personality dispatch |

The wall-clock savings from forcing parallel dispatch are **bounded to ~10 seconds per Trias run on code tasks** — modest. On reasoning tasks where Step 7 is absent, parallel dispatch would save ~20-30 seconds per run. Neither is large enough to justify aggressive prompt rewrites unless future spec changes increase the personality count or per-personality work.
