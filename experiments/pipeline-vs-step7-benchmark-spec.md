# Benchmark spec — implementation pipeline vs plain Step 7 (kill-criterion)

**Status:** spec (not yet run). **Purpose:** the kill-criterion gate for the EXPERIMENTAL_DRAFT
post-deliberation implementation pipeline (`agents/consilium-implement-subagent.md`). Decides whether
it graduates to default or is marked DEPRECATED_DRAFT.

Governed by `experiments/README.md` (benchmarking discipline) and SKILL.md → "Benchmarking discipline".

## Hypothesis (falsifiable)

> The 3-role pipeline (Coder → Test Writer ∥ Reviewer + red→green gate) produces **more correct** code
> than plain single-shot `implement`, on the same spec, without disproportionate cost.

Null hypothesis: the pipeline costs ~3× and adds no correctness over single-shot → kill it.

## Design (two arms, shared spec)

For each task, produce **one** Consilium report = the shared spec (`chosen_approach`,
`success_criterion`, `verification`). Both arms consume the *same* spec — this is the core fairness control.

| Arm | Mechanism |
|---|---|
| **A — baseline** | Plain Step 7 `implement`: one Sonnet agent writes the code from the spec. |
| **B — pipeline** | `consilium-implement-subagent`: Coder → Test Writer ∥ Reviewer + red→green gate. |

Controls: same model (`sonnet`) both arms; same spec; same effort budget (uniform — no per-arm tuning,
per project memory); the oracle is hidden from both arms.

## Oracle (independent, hidden, deterministic)

The **only** quality signal is an oracle test suite per task, written **before** the runs and **never
shown to either arm** (Arm B's Test Writer writes its *own* tests — those do not count as the oracle).
Quality = fraction of oracle tests passing. Deterministic `pytest` pass/fail — **not** evaluator judgment
(this is the P3-corrigendum guardrail: a "better" claim with no independent oracle is just disagree-with-evaluator).

Per-task, before running, answer in writing: *"is there an alternative reading of the task under which
Arm A's plausible output is actually correct and the oracle is wrong?"* — explicit answer required.

## Tasks (n=3 — pilot gate, not statistical proof)

Each task is non-trivial with an **implicit constraint** not spelled out in the obvious spec (the regime
where test-writing + review should pay off). Difficulty is preserved, not simplified (project memory).

- **T1 — edge-heavy pure function.** e.g. a `parse_duration("1h30m")` / interval-merge / rate-limiter
  helper. Implicit constraints: empty input, overlapping/adjacent boundaries, overflow, idempotence.
  Oracle: ~10 tests covering the happy path + 5–6 edge cases the obvious implementation tends to miss.
- **T2 — small stateful module with a hidden invariant.** e.g. an LRU/TTL cache or a bounded queue.
  Implicit constraint: an invariant (capacity, eviction order, thread-visibility) not restated in the
  success_criterion. Oracle: tests that assert the invariant under sequences, not just single calls.
- **T3 — bugfix/refactor that must not regress.** Start from a working file + passing tests; the spec
  asks for a behavior change that naively breaks an existing guarantee. Implicit constraint: preserve
  the existing contract. Oracle: the pre-existing test suite **plus** new tests for the changed behavior.

Concrete task statements + oracle test files are authored in a follow-up commit (kept in
`experiments/pipeline-bench/<task>/`), each oracle written before either arm runs.

## Metrics

- **Primary — correctness:** oracle pass rate per arm per task.
- **Secondary — cost:** total tokens (`telemetry`), sub-agent count, wall-clock. Expected ~1× (A) vs ~3×+ (B).
- **Diagnostic — gate value:** did Arm B's red→green gate reject any test, and did Arm B's Reviewer
  (Control voice) flag a real defect that Arm A shipped? (the pipeline's specific value claim.)

## Pre-registered decision rule (fixed before running)

Pipeline **graduates** iff:
1. oracle pass-rate(B) > pass-rate(A) on **≥2 of 3** tasks, **and**
2. cost(B) ≤ **2×** cost(A) on average (3 sub-agents must not balloon beyond ~2× to be worth it).

Otherwise → **DEPRECATED_DRAFT**: mark in SKILL.md, keep bundles in `experiments/pipeline-bench/` as
forensic evidence. A tie on correctness with higher cost is a **kill** (Simplicity first, Constitution P2).

## Honesty caveats (declared up front)

- **n=3** is the documented EXPERIMENTAL_DRAFT pilot threshold, not statistical proof (Deming: a real
  claim needs n≥5 with variance). The verdict is a go/kill gate, not a calibrated effect size.
- **Same operator runs both arms** → bias risk. Mitigated by: deterministic hidden oracle (no judgment
  call on quality) + decision rule fixed before any run + spec shared verbatim.
- Cost figures are token estimates (`telemetry`), not billed dollars.

## How to run (per task)

1. Author the task statement + hidden oracle tests in `experiments/pipeline-bench/<task>/oracle/`.
2. Run `/consilium` once on the task → save the report (the shared spec).
3. **Arm A:** dispatch one Sonnet agent with the spec → write code → run oracle → record pass rate + cost.
4. **Arm B:** `Agent(subagent_type="consilium-implement-subagent")` with the spec → run oracle on its
   output → record pass rate + cost + gate/reviewer diagnostics.
5. Aggregate the 3 tasks → apply the decision rule → consolidate into
   `experiments/pipeline-vs-step7.html` (per the experiments/ report format).
