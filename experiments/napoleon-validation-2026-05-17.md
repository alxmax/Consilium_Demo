# Napoleon validation — 2026-05-17

**Question (TODO.md DECIZII NEREZOLVATE #3):** *Napoleon rămâne senator după empirical validation? Phase 14B din `TODO_RUND2` verifică over-fit la P3. Decide după validare.*

**Verdict: STAYS.** Zero semnal de P3 over-fit. Distribuție bi-directional, dezacord independent, rationale-uri cross-domain.

## Method

Extract Napoleon vote + rationale din toate `runs/senate/2026-*.json` (excluzând `_input_*` artifacts). Schema:

- Modern: `outputs["napoleon"]` (dict keyed by senator name)
- Multi-round: `rounds[-1].outputs["napoleon"]` sau `rounds[-1].senators["napoleon"]`
- Legacy: `senators["napoleon"]`

Sample N=17 senate runs (totalul disponibil la data analizei).

## Aggregate metrics

| Metric | Value | Interpretation |
|---|---|---|
| Participation rate | 15/17 = 88% | Healthy (1 ABSENT, 1 NOT_DISPATCHED in R2 fără cross-Q) |
| Vote distribution | GO=5, MODIFY=7, STOP=3 | Bi-directional, no STOP anchoring |
| Agreement cu verdict | 8/14 = 57% (excluding non-votes) | Adds independent signal, nu rubber-stamp |
| Disagreement direction | 3× mai permissive (GO over MODIFY), 2× mai cautious (STOP over MODIFY) | Real bi-directional perspective |
| P3 over-fit signal | **NONE detected** | Rationale-uri variate cross-domain |

## Per-run breakdown

| Run | Verdict | Napoleon vote | Direction |
|---|---|---|---|
| 05-16_1632-self-validation | MODIFY | GO | more permissive |
| 05-16_194415-mvp-vs-design-intent | MODIFY | MODIFY | agree |
| 05-16_212238-rund2-self-validation | MODIFY | MODIFY | agree |
| 05-16_214737-flow-and-modes-audit | MODIFY | ABSENT | — |
| 05-16_220014-flow-and-modes-audit-r2 | MODIFY | MODIFY | agree |
| 05-16_220025-flow-and-modes-audit-r2 | MODIFY | MODIFY | agree |
| 05-16_224300-arch-audit-senator-memory | MODIFY | MODIFY | agree |
| 05-16_231058-law3-auto-trigger | MODIFY | GO | more permissive |
| 05-16_231242-senator-memory-candidates | MODIFY | STOP | more cautious |
| 05-17_012335-bundle-2-senators-plus-5 | MODIFY | MODIFY | agree |
| 05-17_013234-phase1-deeply-split | GO | GO | agree |
| 05-17_015949-4-proposal-bundle | MODIFY | MODIFY | agree |
| 05-17_022000-4-proposal-bundle-r2-p2p3 | ? | NOT_DISPATCHED | — |
| 05-17_093436-voices-and-senators-to-subagents | MODIFY | STOP | more cautious |
| 05-17_094306-voices-and-senators-to-subagents | STOP | STOP | agree |
| 05-17_100315-per-voice-dispatch-pinning | MODIFY | GO | more permissive |
| 05-17_101017-per-voice-dispatch-pinning | MODIFY | GO | more permissive |

## Rationale sample (cross-domain, no P3 pattern)

- "Approve improvements 2 and 3 immediately (cost-justified, low-medium complexity, favorable terrain). Defer improvement 1 until senate run completed." — **cost/terrain analysis**
- "STOP. Activation gate not met. Schedule revisit after 20 senate runs with ≥80% outcome tracking." — **gating on empirical thresholds**
- "STOP on terrain, not merit. 6-10h, 1500-1800 lines diff not justified in stretched session." — **operator state / effort calibration**
- "Narrowing obligatoriu: excludeti din audit modurile cu <2 runs reale; separati analiza pasilor de analiza modurilor." — **scope-narrowing**
- "Unbundle into 2 phases. Phase 1 ship now (~1-2h, zero cost); Phase 2 defer until ≥10 senate runs." — **phased delivery**

All rationale-uri reflectă specialitatea declarată ("tokens, ore, starea operatorului") aplicată variat — nu pattern-matching pe P3 car wash.

## Caveats

- N=15 voturi e mic pentru semnificație statistică, dar suficient pentru a respinge over-fit ipoteza tare (un over-fit la P3 ar produce STOP-heavy distribution, nu 5G/7M/3S)
- 5 din 15 runs sunt pe propuneri proprii (self-audit), care biasează spre MODIFY oricum (verdict cumulativ MODIFY pe 13/17 runs)
- Cross-domain rationale validation a fost calitativă (eyeball); analiza n-a folosit clustering automat

## Decision

**Napoleon stays.** Re-evaluează doar dacă apare semnal contrar (>3 STOP consecutiv pe propuneri neagresive, sau rationale-uri repetitive P3-style) în următoarele 10 runs.
