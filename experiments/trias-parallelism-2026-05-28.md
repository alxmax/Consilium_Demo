# Trias parallelism empirical audit (2026-05-28)

## Question

`modes/trias.md` Step 3 mandates parallel dispatch of the 3 personality sub-agents in a single orchestrator message:

> *"Dispatch all 3 personalities in parallel (3 consilium-subagent Agent calls in the same orchestrator message)... Parallel dispatch is mandatory — sequential dispatch triples wall-clock for no quality gain, and is the root cause of the task-08 timeout pattern observed in benchmark n=10 (2026-05-27)."*

Does this actually happen at runtime?

## Method

For each Trias workspace with a saved `claude_raw.json` (n=12, including replicates), compute the **api/wall ratio**:

```
ratio = duration_api_ms / duration_ms
```

Interpretation:
- **ratio ≈ 1.0** → pure sequential: each Agent call waits for the previous one to return; API time roughly equals wall time.
- **ratio ≈ 3.0** → ideal parallel dispatch of 3 personalities: 3 concurrent API calls, each taking ~T seconds → API time = 3T, wall time = T.
- **ratio between 1.0 and 3.0** → partial-parallel: some overlapping API time, but not full concurrency.

A separate filter excludes scale_down runs (`num_turns ≤ 4`) — those never dispatched personalities, so the ratio is meaningless.

## Results

| Task | Turns | Wall (s) | API (s) | Ratio | Pattern |
|---|---:|---:|---:|---:|---|
| 01_transport_choice/rep_1 | 2 | 21.6 | 21.5 | 1.00 | scale_down |
| 02_rule_of_three/rep_1 | 22 | 359.3 | 369.1 | 1.03 | **SERIAL** |
| 03_schema_migration/rep_1 | 25 | 359.1 | 371.8 | 1.04 | **SERIAL** |
| 04_binary_search_bug/rep_1 | 17 | 259.8 | 256.2 | 0.99 | **SERIAL** |
| 05_warehouse_contradiction/rep_2 | 2 | 19.8 | 19.7 | 1.00 | scale_down |
| 05_warehouse_contradiction/rep_3 | 4 | 68.8 | 68.7 | 1.00 | scale_down |
| 06_split_brain_db | 30 | 380.7 | 387.5 | 1.02 | **SERIAL** |
| 07_composite_index_prefix | 28 | 249.1 | 256.7 | 1.03 | **SERIAL** |
| 08_locking_strategy | 2 | 47.8 | 47.7 | 1.00 | scale_down |
| 09_pipeline_freshness | 29 | 435.9 | 518.4 | 1.19 | **SERIAL** (partial) |
| 10_checkout_degradation | 24 | 440.1 | 478.8 | 1.09 | **SERIAL** |
| 11_marathon_prep/rep_1 | 2 | 59.5 | 59.5 | 1.00 | scale_down |

## Findings

- **7/7 real-deliberation Trias runs flagged as SERIAL.** Range of ratios: 0.99 – 1.19. None reached even 1.5x.
- **5/5 scale_down runs correctly excluded** (no dispatch to measure).
- **Theoretical parallel target: 3.0x. Observed maximum: 1.19x.** Trias is effectively running 3 sequential Sequential sub-deliberations, paying the 3× cost without any wall-clock savings.

## Implication for code tasks

Code tasks (e.g. `code/01_circuit_breaker`) have a 10-minute wall-clock cap. With ~4 minutes per personality dispatched serially, Trias on code tasks will routinely hit the timeout (confirmed empirically — see PR thread 2026-05-28). The spec already names this: *"sequential dispatch... is the root cause of the task-08 timeout pattern."*

## Why does this happen?

`modes/trias.md` instructions are descriptive, not enforced. The orchestrator (Claude CLI) decides when to emit Agent tool_use blocks. Reading "dispatch in parallel" as guidance, the model often chooses serial dispatch — likely because:
- Each personality's output influences how the model frames the next call's prompt
- Serial feels safer / more "deliberate" to the LLM
- No external check or counter-incentive

## What we shipped (2026-05-28)

Soft enforcement / observability — `scope_c_benchmark_coupled` per [Consilium deliberation](../.consilium/runs/2026-05-28_1545_trias-parallelism-observability.json):

1. **`benchmark/scripts/check_trias_parallelism.py`** — computes ratio from `claude_raw.json`, writes verdict to `pipeline_audit.json` (`trias_serial_dispatch: bool`, `trias_parallel_ratio: float`, `trias_dispatch_pattern: serial|parallel|scale_down`).
2. **`benchmark/run_task.py`** — calls the audit after every `consilium_trias` run completes.
3. **`benchmark/analyze.py`** — surfaces a `⚠ trias: serial dispatch (1.XXx)` badge in `report.html` for any flagged cell.

Threshold: `ratio < 1.5` is flagged as serial. Chosen empirically — the observed serial-dispatch maximum is 1.19x, so 1.5 leaves a wide margin for partial-parallel runs to register as "parallel evidence" rather than serial.

## What we did NOT ship (and why)

- **No schema change to `validate_report.py`.** A `trias_serial_dispatch` field on every `.consilium/runs/*.json` would touch the validation gate that runs on every Consilium mode, not just Trias. Violates Surgical Changes.
- **No wall-clock telemetry refactor.** Adding wall-clock per voice across all dispatch sites is a separate sub-change, 3-5x the scope of the audit feature.
- **No `check_doc_drift.py` invariant.** Spec-vs-impl parity check would add ongoing tracking burden for a Trias-only concern.
- **No prompt rewrite in `modes/trias.md`.** This is observability, not enforcement. Whether to rewrite Step 3 imperatively (option B from the deliberation) is a separate decision deferred until we have parallel-dispatch data points to compare against.

## Next steps (deferred)

- Run a corpus where we **observe** at least one `ratio ≥ 1.5` Trias run, validating the threshold isn't permanently below the floor.
- If never seen, consider option B: prompt rewrite in `modes/trias.md` Step 3 with imperative phrasing + explicit anti-patterns.
- Reopen the `--skeptic-can-override` decision (see TODO.md) if the parallelism audit changes Trias's cost-benefit picture.
