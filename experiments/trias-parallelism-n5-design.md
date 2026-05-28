# Trias parallel-dispatch — N≥5 variant test design

## Origin

Senate 2026-05-28 ([trias-parallelism-enforcement](../runs/senate/2026-05-28_220338-trias-parallelism-enforcement.json), MODIFY 6-3-0): Deming and Socrate flagged that the conclusion "imperative spec rewrite is robust against parallel-dispatch enforcement" rests on N=1 attempt. Statistical discipline requires N≥5 distinct interventions before declaring the prompt-enforcement path falsified.

This file is the test plan. Each variant is a distinct intervention class with a falsifiable success criterion. Variants are runnable independently.

## Falsification criterion

For each variant, success = at least 1 Trias run (`consilium_trias` mode on a real-deliberation task, `num_turns > 4`) produces `trias_max_agents_in_message >= 3` in `pipeline_audit.json`.

Baseline established: 7/7 SERIAL across the benchmark corpus (modes/trias.md current text). Any variant that produces ≥1 PARALLEL run flips that variant's verdict from "ineffective" to "promising"; further N to confirm.

## Variants

### V1 — Imperative rewrite (BASELINE FAILURE, already tested)
- **Intervention:** rewrite `modes/trias.md` Step 3 with "MUST ... in your VERY NEXT MESSAGE" + worked example + anti-pattern with "DO NOT do this".
- **Result (2026-05-28):** SERIAL (3 separate messages, ~13s apart). Timeout at 10-min wall cap.
- **Verdict:** does not work in isolation.

### V2 — First-token rewrite
- **Intervention:** rewrite `modes/trias.md` Step 3 so the parallel-dispatch instruction is the FIRST sentence, before any context-strip preamble. Hypothesis: orchestrator's reading order matters; sequential narration may bias toward sequential execution.
- **Run command:** `python run_task.py --mode consilium_trias --task code/01_circuit_breaker --clean`
- **Success:** `cat workspace/consilium_trias/code/01_circuit_breaker/pipeline_audit.json | jq .trias_max_agents_in_message` returns 3.

### V3 — Reorder MODE_PREFIXES injection point
- **Intervention:** in `benchmark/run_task.py`, change `MODE_PREFIXES["consilium_trias"]` from `"/consilium --mode trias "` to `"/consilium --mode trias - PARALLEL DISPATCH MANDATORY: emit 3 Agent tool_use blocks in your first response. "`. Tests whether instruction position relative to the task description matters.
- **Run command:** same as V2.
- **Success:** same JSONL audit.

### V4 — PreToolUse hook (architectural intervention)
- **Intervention:** add a `PreToolUse` hook in `.claude/settings.json` that runs a Python validator before any `Agent` tool call. The validator:
  - reads the current message's tool_use blocks from the session JSONL (if accessible at hook time)
  - if `subagent_type` is a Trias personality (`pioneer|architect|steward`) AND `tool_use` count in this message is 1, emit stderr warning + non-zero exit (rejects the dispatch)
  - the orchestrator must then retry with all 3 in one message
- **Caveat:** Claude Code's PreToolUse hook receives a single tool invocation context, not the full message. May not see siblings. Test feasibility before committing.
- **Success:** as above; also note if hook fires deterministically per Trias dispatch.

### V5 — Concrete tool_use JSON example in spec
- **Intervention:** rewrite `modes/trias.md` Step 3 to include the LITERAL expected `tool_use` JSON shape, e.g.:
  ```
  Your next response MUST be exactly this structure:
  [
    {"type": "text", "text": "..."},  // optional brief preamble
    {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "consilium-subagent", "prompt": "<Pioneer lens + ...>"}},
    {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "consilium-subagent", "prompt": "<Architect lens + ...>"}},
    {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "consilium-subagent", "prompt": "<Steward lens + ...>"}}
  ]
  ```
- **Success:** same JSONL audit.

### V6 — Negative-framing penalty
- **Intervention:** rewrite to include "**If you dispatch personalities one at a time, you have FAILED the Trias mode. The run becomes invalid and the user loses 9 minutes of wall-clock to a degenerate result.**"
- **Success:** same JSONL audit.

### V7 — Tools.json multi-agent template (if feasible)
- **Intervention:** check whether Claude Code CLI supports a `tools.json` configuration that pre-declares a multi-Agent dispatch template. If yes, define `trias_dispatch` as a single composite tool that internally emits 3 Agent calls.
- **Caveat:** May not be exposed in `claude -p`. Test feasibility first.
- **Success:** same JSONL audit.

## Running the matrix

For each variant V2–V7:
1. Apply the intervention (edit file or settings.json).
2. Wipe the workspace: `python scripts/run.py clean --task code/01_circuit_breaker` (or a reasoning task that triggers full Trias; reasoning tasks may scale_down, so prefer code task with explicit override).
3. Run: `python run_task.py --mode consilium_trias --task code/01_circuit_breaker --clean`.
4. Read `pipeline_audit.json`:
   ```bash
   cat workspace/consilium_trias/code/01_circuit_breaker/pipeline_audit.json
   ```
5. Record `trias_max_agents_in_message`, `trias_dispatch_pattern`, and the wall-clock in this file.
6. Revert the intervention before testing the next variant (each variant tested in isolation).

## Estimated cost

- Each Trias run on `code/01_circuit_breaker`: ~10 min wall, ~$1.00–$1.30, ~$0.20-0.40 if scale_down fires
- 6 variants × 1 run each = ~60 min wall, ~$6-10 total
- If any variant flips to PARALLEL, run an additional N=4 confirmations on the same variant = +~40 min, +~$5

## Decision rule

- **≥1 variant of V2–V7 produces PARALLEL** → prompt-enforcement path is NOT falsified; the failing variant's specific phrasing is. Investigate why that variant worked and ship it.
- **All variants produce SERIAL** → prompt-enforcement path is empirically falsified at N≥6. Next escalation: PreToolUse hook becomes mandatory (V4 must work or be ruled out by feasibility), or accept the cost permanently and shrink Trias to 2 personalities (Musk's STOP).

## Status

- 2026-05-28: design ready, V1 already failed. V2–V7 deferred until user explicitly opts in to the ~$6-10 spend.
- Awaiting variant run results.
