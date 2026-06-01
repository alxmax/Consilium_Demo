# Benchmarking discipline & the oracle rule

Short methodology note. **Origin: the P3 corrigendum.** An early experiment (an
implicit-constraint reasoning problem) was scored against a *wrong oracle*: the
evaluator's quick-take answer was treated as ground truth, and the model's
deeper reading was labeled a "fabrication." When the oracle was corrected, the
semantic label inverted — what had been called fabrication was actually the
model **catching a real implicit constraint**. The entire set of conclusions had
pointed the wrong way.

> The problem itself is an active benchmark task. Its answer is held only in the
> external scoring repo, never in this repository — so this note is deliberately
> answer-free.

## The rule

Any quantitative claim about voice behavior (`fab-rate`, `accuracy`,
`catch-rate`) must cite an **independent oracle**:

- (a) a second expert who has **not** seen the evaluator's quick-take, **OR**
- (b) an explicit citation from the problem statement / specs that fixes the
  ground truth below a clear ambiguity threshold.

The evaluator's quick-take is **not** an oracle.

Before publishing: for each plausible option (A/B/C/D…), document explicitly
*"is there an alternative reading of the problem in which this option becomes
correct?"* — one answer per option, with "no" **justified**, not assumed
tacitly. This is the step P3 missed.

A `fabrication` verdict on a piece of reasoning stays **blocked** until an
independent oracle confirms it, separately from the evaluator's intuition.

## Retroactive audit

Any previously-published fab-rate / catch-rate / accuracy is re-reviewed through
the grid above. Active risk identified 2026-05-16 (P3 corrigendum):

- **P3** — corrigendum recorded; oracle was inverted, every downstream label
  flipped with it.
- **P1** (data refactor) — un-audited.
- **P2** (auth) — un-audited.

## Skeptic-on-chosen empirical origin

The `skeptic_on_chosen` flag emerged from this experiment.
`chosen_confirmation_pass` (its conceptual ancestor) places a skeptic *on the
chosen answer* and asks "what is the most concrete failure mode for this
choice?". On the P3 implicit-constraint problem it reached **100% catch-rate in
simulation and 4/7 in real reruns** — better than any other mode tested there.
**Scope caveat (n=1):** these figures come from a single problem instance;
generalizability is unconfirmed until ≥3 distinct problems are tested.

Cross-reference: SKILL.md → "Skill maintenance → Benchmarking discipline".
