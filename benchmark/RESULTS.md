# Benchmark results

*Snapshot: 2026-05-29. Regenerate the visual matrix with `python analyze.py` → `report.html`.*

> ⚠️ **SUPERSEDED (2026-06-23) — kept for provenance only.** This snapshot is out of date in three ways; treat every number below as historical, not current:
> 1. **The corpus is now 3 tasks**, not the 12 core + 7 supplementary described below — only `code/01_circuit_breaker`, `reasoning/01_transport_choice`, and `reasoning/02_rule_of_three` exist in the harness.
> 2. **Grading is now fully deterministic** — the open-ended Opus LLM judge was replaced by exact-answer + keyword checks (no AI grades another AI).
> 3. **"100% on every mode" no longer holds.** Under the deterministic grader, `reasoning/01_transport_choice` is a trick question that the single-pass modes (`sonnet_bare`, `superpowers`) get **wrong** while the deliberation modes get right. The consilium cost figures below were also captured *before* the 2026-06-23 fix that made those modes actually deliberate — at the time they had silently collapsed to a bare-model pass — so they undercount real deliberation cost by roughly 8–10× (a post-fix spot-check measures ~$1–2 per reasoning task). A corrected re-run at n≥15 is pending.

## Setup

- **Modes (5):** `sonnet_bare` (baseline — the model with no scaffolding), `superpowers` (a generic agent-skill harness), and three Consilium modes — `sequential`, `dialectic`, `trias`.
- **Model:** every mode runs on **Claude Sonnet 4.6** at `--effort high`, uniform budget cap. This is deliberate: the benchmark isolates the *deliberation scaffolding*, not the model. (Comparing modes across different models would confound the two.)
- **Judge / oracle:** closed-answer tasks are graded by exact ANSWER/VALUE match against external answer keys (`../Benchmark-scoring/`, kept outside the repo so the model can't read them); open-ended tasks by an **Opus 4.7** LLM judge against a rubric.
- **Corpus:** 12 core tasks — `code/01_circuit_breaker` + `reasoning/01…11` (transport choice, rate problems, schema migration, a binary-search bug, contradiction/consistency, distributed-systems and DB reasoning, etc.). Plus 7 supplementary reasoning tasks (`reasoning/12…18`) run on the baseline only — see note below.

## Headline result: correctness is saturated

**Every mode scores 100% on every scored task in the core corpus.** Sonnet 4.6 at high effort already solves all of them; the deliberation modes neither gain nor lose correctness.

| Mode | Correctness (core corpus) | Avg cost / run | Cost vs baseline |
|---|---|---|---|
| superpowers | 100% | $0.124 | 0.8× |
| **sonnet_bare** (baseline) | 100% | $0.148 | 1.0× |
| consilium_sequential | 100% | $0.189 | 1.3× |
| consilium_dialectic | 100% | $0.398 | 2.7× |
| consilium_trias | 100% | $0.612 | 4.1× |

So on this corpus the **only** axis that separates the modes is **cost** (and, correspondingly, wall-clock): Consilium's deliberation modes cost 1.3×–4.1× the bare baseline for **identical** correctness.

## Honest interpretation

On a task class the base model already solves, multi-voice deliberation does **not** buy a higher score. What it buys is **process**: an explicit Generator/Control/Conservator (and, in Trias, three personality lenses) deliberation, a recorded risk assessment, a confidence signal, a structured audit trail (`.consilium/runs/*.json`), and cost-aware mode selection. That is the value proposition — **auditable, risk-surfaced decisions**, not a benchmark-score uplift.

The corresponding engineering takeaway is built into the skill: **default to the cheapest mode** (sequential/scope-gate) and escalate to dialectic/trias only when the *stake* (irreversibility × magnitude), not the difficulty, justifies the premium.

## What this benchmark does NOT show (limitations)

- **The corpus does not discriminate.** Because all modes hit 100%, these results cannot show whether deliberation helps on tasks where the base model is *flaky or wrong*. We tried to build such discriminators: across **7 deliberately-hard, distinct task vectors** (buried constraints, risk-of-ruin synthesis, a famous-problem twist, adversarial bookkeeping, multi-phase rates, a combinatorial recurrence, a competition-level inclusion-exclusion), Sonnet 4.6 scored 100% on **all 7** — we could not manufacture even a single base-model failure on a clean-oracle problem. (Record: `experiments/trias-discriminating-tasks-design.md`; tasks 12–18.)
- **Consequence for Trias specifically:** since Trias runs *on Sonnet* (3 Sonnet sub-agents + a vote), it can only help where Sonnet fails — and Sonnet doesn't fail this corpus. Trias showed **0 wins**; it is gated behind a "≥2 wins in n≥20" criterion that remains empirically unmet (see `modes/trias.md` "Vehicle decision").
- **Single model tier.** The Sonnet-4.6/Opus-4.8 capability gap is not exercised here. Where a stronger model is needed, the right lever is `--model`, not a more expensive Sonnet mode.

## Bottom line

The benchmark's honest claim is narrow and defensible: **Consilium's deliberation modes preserve correctness while adding an auditable decision process, at a measured cost premium** — it is *not* a claim that they out-score the base model on solved-class tasks. On this corpus they don't, and saying so plainly is the point.
