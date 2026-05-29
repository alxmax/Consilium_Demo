# Trias value experiment — discriminating-task design

## Origin

Senate 2026-05-29 ([trias-parallelism-vehicle-a1-vs-a2](../runs/senate/2026-05-29_140645-trias-parallelism-vehicle-a1-vs-a2.json), MODIFY 6-3-0) reframed the parallelism question: **do not invest in any parallelism vehicle until Trias proves value.** Musk/Deming/Socrate/Tacitus converged — Trias has **0 wins at n=6** on a saturated corpus (all modes ~100/100), and the user's own pinned kill-criterion (**≥2 Trias wins in n≥20 oracle-validated tasks**, from the 2026-05-21 reframe) is unmet.

This file designs the experiment that resolves that gate. Runs are a separate, budgeted opt-in (like [trias-parallelism-n5-design.md](trias-parallelism-n5-design.md)).

## Why the current corpus can't discriminate

The existing tasks (`code/01`, `reasoning/01–11`) are single-correct-answer problems the base model (Sonnet 4.6 at effort=max) already nails → all modes score ~100/100. A mode that re-weights three perspectives cannot show value where one perspective already suffices.

## Hypothesis

Trias's mechanism is **3 personality lenses re-ranking the Generator/Control/Conservator scores** (Pioneer up-weights upside, Steward up-weights risk, Architect balances) + a democratic vote. It can only outperform a single-perspective run on problems with **genuine multi-perspective tension** where the base model's *default lean* is systematically wrong or incomplete:

- the obvious/eager answer is a **trap** that only a risk lens (Steward) catches;
- the correct answer is **unconventional** and the balanced default underrates it (Pioneer);
- there are **two valid readings** and the right move is to surface the tension, not silently pick one.

**Falsifiable form:** Trias "wins" a task iff it returns the oracle answer AND the cheap baseline (`sonnet_bare`) returns a wrong/incomplete one, on the same task.

## Design principles for a discriminating task

1. **A plausible wrong default.** There must be an answer the base model is *drawn to* that is wrong — otherwise no mode can improve on it.
2. **The correct answer needs a minority perspective.** The fix should be exactly what one lens (risk / upside / balance) surfaces and a single pass misses.
3. **Oracle-unambiguous.** Despite the tension, one answer is defensibly correct (oracle in `../Benchmark-scoring/`, NOT here — see benchmark/CLAUDE.md isolation rule).
4. **Hard, not tricky.** Difficulty from genuine tension, not from wordplay (per project policy: tasks stay hard, don't simplify).

## Candidate tasks (specs only — oracle answers authored externally)

Described by their *discriminating property* + the *trap*, not their answer.

- **T1 — Irreversible migration with a tempting fast path.** A schema/data migration where the obvious one-shot approach silently drops rows under a concurrency edge; only the risk lens flags the irreversibility and forces the staged/backfill answer. Trap: base model picks the clean-looking one-shot.
- **T2 — do_nothing is correct.** A "should we add caching here?" decision where the eager answer adds complexity that a careful read shows is unjustified (no measured hot path); the correct call is do_nothing/defer. Trap: base model over-builds.
- **T3 — Unconventional-but-correct.** A problem where the textbook approach is dominated by a non-obvious cheaper/safer design that the balanced default dismisses as weird; Pioneer's up-weighting surfaces it. Trap: base model picks the textbook answer.
- **T4 — Two valid readings (clarify).** An underspecified spec with two materially different correct implementations; the right output names both and the deciding question, rather than silently committing to one. Trap: base model picks one branch confidently.
- **T5 — Risk/reward inversion under a hidden counterparty.** A choice that looks net-positive until an external dependency/failure mode (rate limit, partial write, downstream consumer) is weighted; only the risk lens inverts the ranking. Trap: base model takes the headline-positive option.
- **T6 — Stretch (optional).** A multi-step decision where each lens individually is wrong but the *vote* over three partial views lands on the oracle answer — tests whether the aggregation itself adds value beyond any single lens.

> To satisfy the **n≥20** gate, expand to ~20 tasks in this family (T1–T6 are the seed templates × variations). Authoring is the cost driver, not compute.

## Protocol

1. Author each task: prompt in `benchmark/prompts/<category>/<id>.md`; oracle answer + rubric in `../Benchmark-scoring/` only.
2. Run **paired**, append-mode, oracle-validated:
   ```
   python scripts/run.py task --task <category>/<id> --reps 1   # appends; no --clean
   # arms: sonnet_bare (baseline) + consilium_trias (+ consilium_sequential as a 3rd arm)
   python verify.py --mode <mode> --task <category>/<id>
   ```
   Budget the wall-clock: serial Trias ≈ 3× (raise the cap or expect timeouts — known, see trias-parallelism docs).
3. Record per task: did Trias return the oracle answer? did sonnet_bare? → win / tie / loss.

## Decision rule (the gate)

- **≥2 Trias wins in n≥20** (Trias correct ∧ sonnet_bare wrong) → Trias earns its 3× cost; **then** parallelism (A1 labeled benchmark fix, or A2 as a separate architectural proposal) becomes worth revisiting.
- **<2 wins in n≥20** → Trias does not earn its keep; deprecate toward Dialectic (Musk's STOP), do not invest in parallelism.
- **Methodology guard (Deming):** report per-task run files; if a task ties (both correct or both wrong) it is not a discriminator — it neither confirms nor refutes; only Trias-correct ∧ baseline-wrong counts as a win.

## Cost & caveats

- Each Trias run ≈ $1–1.3, ~10 min (serial); sonnet_bare ≈ $0.1–0.3. ~20 tasks × 2–3 arms ≈ $30–50 + several hours wall-clock.
- Nested `claude -p` reliability in-session is unproven here (an earlier single Trias run was cancelled mid-buffer) — smoke-test one cheap arm end-to-end before the full matrix.
- Authoring 20 genuinely-discriminating, oracle-clean tasks is the real effort; expect that, not compute, to dominate.

## Status

- 2026-05-29: design ready; T1–T6 are seed templates. Task authoring + runs deferred to explicit user opt-in (per the budget + the Senate gate).
