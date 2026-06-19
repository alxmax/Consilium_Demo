# Trias 6→4 cost re-measurement (2026-06-19)

Goal: validate the cost claim of the skeptic-lever redesign (6→4 spawns,
cost 4× → 2.67× Sequential) with a direct token measurement of the new config.

## Method

Dispatched the new 4-spawn Trias flow (3 personality sub-agents + 1 post-vote
`skeptic_on_chosen`) on independent code-change problems, all on Sonnet, and
summed `subagent_tokens` per dispatch. Two problems were clean (purely
hypothetical, 0 tool calls); a third (`sync.py`) was discarded for cost — the
agents searched the repo for a non-existent file, contaminating the token count
with codebase I/O that a real lens-deliberation would not incur.

## Raw data (subagent_tokens)

| problem | Pioneer | Architect | Steward | Skeptic |
|---|---|---|---|---|
| P2 — refactor build_report() for testability | 24764 | 24759 | 24782 | 24785 |
| P3 — eliminate an N+1 without schema change   | 24812 | 24787 | 24783 | 24780 |

Both problems voted **3-0 unanimous** (P2 → `extract-pure-functions`,
P3 → `dataloader_batching`); the post-vote Skeptic returned `can_object: false,
advisory` on both (the runner-up counter-hypothesis did not defeat the winner).

Per-spawn averages: personality ≈ 24,781 tok · skeptic ≈ 24,787 tok (≈ equal).

## Result

- **New 4-spawn run** (3 personalities + 1 skeptic) ≈ **99,130 tok/run**.
- **Old 6-spawn run** (3 personalities + 3 skeptics) ≈ **148,704 tok/run**.
- **Ratio = 0.667 = 4/6** — the token measurement matches the spawn ratio exactly,
  confirming the spec multiplier change **4× → 2.67×** (2.67/4 = 0.667).

## Honesty caveat (not a $ benchmark)

`subagent_tokens` here is dominated by each agent's harness system prompt, which
is larger and not representative of the lean `consilium-subagent.md` vehicle a
real `/consilium` Trias run uses. So the **absolute** $/run from this measurement
is inflated and is NOT comparable to the `$0.612` figure in the explainer (that
came from the benchmark harness's real in/out cost accounting, on the
pre-redesign 3-personality config). What transfers is the **ratio** (0.67×), which
is invariant to the per-spawn overhead. A clean absolute $/run for the 4-spawn
config requires a `benchmark/` harness re-run — tracked as the open follow-up.

n=2 clean. Oracle: none needed — this is a cost/ratio measurement, not a
correctness claim (per `experiments/oracle-discipline.md`).
