# T2 result — LRUCache

Run: 2026-05-24. Both arms: fresh Sonnet sub-agents, same spec, neither saw the oracle.

## Oracle outcome (hidden, 8 tests incl. LRU-vs-FIFO discriminators)

| Arm | Mechanism | Oracle pass | Tokens | Tool uses | Wall-clock |
|---|---|---|---|---|---|
| A — baseline | single-shot implement | **8/8** | 17,459 | 1 | 9.1 s |
| B — pipeline | coder→tests→review+gate | **8/8** | 19,783 | 5 | 40.6 s |

Both used `OrderedDict.move_to_end`; both handled get-refreshes-recency and put-updates-recency
correctly. Near-identical solutions again.

## Reading

Another **tie** at higher cost (B/A = 1.13× tokens, ~4.5× wall-clock). The hidden-invariant trap
(get must refresh recency — the classic LRU bug) did **not** trip the baseline: Sonnet knows the LRU
contract, so there was no missed edge for the test-writer to surface.

## Consequence for the gate

Running tally: pipeline **0 wins / 2 ties**. Graduation requires correctness wins on **≥2 of 3** tasks
→ now mathematically **unreachable** (max achievable is 1/3). The graduate/kill outcome is therefore
already decided: **KILL (DEPRECATED_DRAFT)**.

T3 is still run — for the diagnostic question "does the pipeline ever catch a regression the baseline
ships?", which refines the recommendation (blunt kill vs "narrow to refactor/bugfix use").
