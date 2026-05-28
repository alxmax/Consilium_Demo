# Dialectic Skeptic-on-scale_down empirical validation (2026-05-28)

## Spec change validated

PR #259 (`fix/dialectic-skeptic-on-scale-down`, commit `3d50215`) updated SKILL.md Step 2 and modes/dialectic.md to require the Skeptic stage to dispatch even when Conservator returns `meta_recommendation: scale_down`. Previously, scale_down short-circuited the entire workflow, silently violating the dialectic spec ("Skeptic runs unconditionally — not gated on the confidence band").

## Method

Re-ran `consilium_dialectic` mode against the 10-task reasoning benchmark corpus (`benchmark/prompts/reasoning/01..10`). Compared against:
- Old dialectic n=10 (pre-fix, from 2026-05-27 benchmark): 9/10 correct, ~$1 total cost
- Oracle answers in `C:/Users/ALEX/Desktop/Doc/Benchmark-scoring/reasoning/*/expected_answer.txt`

Each task workspace was wiped before re-run (`--clean` equivalent via `rm -rf`).

## Per-task results

| Task | Wall | Cost | Letter | Skeptic dispatched? |
|---|---|---|---|---|
| 01 transport_choice | 18.5s | $0.0864 | B ✓ | No (scale_down direct) |
| 02 rule_of_three | 52.3s | $0.1326 | C ✓ | No |
| 03 schema_migration | 1m13s | $0.1349 | C ✓ | No |
| 04 binary_search_bug | **5m20s** | **$0.8285** | C ✓ | **Yes** |
| 05 warehouse_contradiction | **4m53s** | **$0.8445** | D ✓ | **Yes** |
| 06 split_brain_db | 47.9s | $0.1109 | B ✓ | No |
| 07 composite_index_prefix | 43.0s | $0.1135 | D ✓ | No |
| 08 locking_strategy | **6m50s** | **$0.9843** | B ✓ | **Yes** |
| 09 pipeline_freshness | 3m23s | $0.4736 | A ✓ | Likely |
| 10 checkout_degradation | 3m43s | $0.4487 | C ✓ | Likely |

**Total:** 10/10 correct (up from 9/10), ~$4.16, ~28 min wall.

"Skeptic dispatched" inferred from cost+wall thresholds: scale_down direct path is ~$0.10 / <1min; Skeptic-dispatched is >$0.40 / >3min. Not directly observable from `pipeline_audit.json` (which still reads `pipeline_executed: false` because Gen+Ctrl were skipped per scale_down — Skeptic is a separate sub-agent dispatch not reflected in that field; see TODO "pipeline_executed integration gaps").

## What the data says

**Positive:**
- 10/10 vs 9/10 previously → +1 win (task 01 flipped A→B)
- Zero regression on the 9 previously-correct tasks
- Skeptic empirically dispatched on at least 5 tasks (04, 05, 08, 09, 10) — the mechanism is real, not just spec-text priming

**Negative:**
- Cost grew 4× (~$1 → ~$4.16) for +10 percentage points accuracy on this corpus
- Task 01's flip cannot be cleanly attributed to Skeptic-as-mechanism because the spec text in modes/dialectic.md and SKILL.md NOW CONTAINS the correct answer ("correct is B (drive)"). Orchestrator reads spec during Bootstrap → answer leaks via context, separately from any Skeptic dispatch. This is a contamination bug introduced by the same PR.
- Per-task variance is large ($0.09 to $0.98). Conservator's scale_down vs full-dispatch decision is not stable run-to-run; expect noise in repeated runs.

**Net:**
- Fix works mechanically (Skeptic real-dispatched on 5/10 tasks).
- Cost-benefit ratio uncertain — 1 win for 4× cost increase is poor return if generalized, but on isolated runs the wins may concentrate where they matter (the "implicit-constraint" tasks).
- Task 01 specifically is contaminated and should be re-validated with a clean task.

## Clean re-validation 2026-05-28 (post spec-leak removal)

PR #261 (`fix/spec-priming-leak-cleanup`) removed the answer text from modes/dialectic.md and SKILL.md. Task 01 was re-run across all 5 modes with a wiped workspace.

**Result: all 5 modes scored 100/100, including `sonnet_bare`, with `pipeline_executed=False` and `num_turns=2` across the board.**

| Mode | Score | Pipeline executed | Turns | Cost |
|---|---|---|---|---|
| consilium_sequential | 100/100 | False | 2 | $0.091 |
| consilium_trias | 100/100 | False | 2 | $0.088 |
| consilium_dialectic | 100/100 | False | 2 | $0.090 |
| superpowers | 100/100 | N/A | 2 | $0.089 |
| sonnet_bare | 100/100 | N/A | 2 | $0.088 |

**Interpretation:** Task 01 is not a discriminator for the Skeptic-on-scale_down mechanism. The base model at `--effort high` answers B correctly on its own — the previous A→B flip was non-determinism on an early run, not a spec-priming or Skeptic effect. None of the consilium modes ran the deliberation pipeline (all scale_down or bare-answer). The correct answer was already achievable by the base model; removing spec-priming had no impact on correctness. Task 01 cannot be used to isolate the Skeptic mechanism.

**Next step:** construct a new eval task where the base model reliably fails without Skeptic guidance (see Follow-ups item 2 below).

## Follow-ups (in TODO.md HIGH PRIORITY)

1. **Validation-leak cleanup:** rewrite the empirical-motivation prose in modes/dialectic.md + SKILL.md so the validation task's correct letter is NOT embedded in spec text the orchestrator reads.
2. **New blind eval task:** construct a task that exercises Skeptic-on-scale_down without spec leak, to empirically distinguish (a) Skeptic catching constraints from (b) spec priming.
3. **`--skeptic-can-override` as Dialectic default?** Currently advisory; for the scale_down + Skeptic path, advisory means Skeptic's challenge has no effect on the published answer. If we want the cost (Skeptic ran in 5/10 tasks at avg ~$0.7 extra) to translate into changed outcomes, override may need to be default. Decision deferred to after the blind validation task exists.

## Cost-benefit comparison across modes (n=10)

| Mode | Accuracy | Total cost | $/task | Wall/task |
|---|---|---|---|---|
| sonnet_bare | 10/10 | ~$1.00 | $0.10 | ~35s |
| consilium_sequential | 10/10 | ~$1.00 | $0.10 | ~25s |
| consilium_dialectic (old) | 9/10 | ~$1.00 | $0.10 | ~30s |
| **consilium_dialectic (after fix)** | **10/10** | **~$4.16** | **$0.42** | **~2m48s** |
| consilium_trias | 8/9* | ~$10.00 | $1.20 | ~7min |

*task 08 timed out in original benchmark (pre-Trias-parallel-dispatch fix)

The fix moves dialectic from "indistinguishable from sonnet_bare on this corpus" to "+1 accuracy at 4× cost". Whether that's a winning trade is unresolved until task 01 contamination is removed and a new blind task is added.
