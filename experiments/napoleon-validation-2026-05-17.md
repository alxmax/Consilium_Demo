# Napoleon validation — 2026-05-17

**Question (TODO.md UNRESOLVED DECISIONS #3):** *Does Napoleon stay as senator after empirical validation? Phase 14B of `TODO_RUND2` checks for over-fit on P3. Decide after validation.*

**Verdict: STAYS.** Zero P3 over-fit signal. Bi-directional distribution, independent disagreement, cross-domain rationales.

> **Update 2026-05-25 (N=73, run4):** Distribuția s-a schimbat față de N=15: GO=42 (58%), MODIFY=22 (30%), STOP=9 (12%). Napoleon mai permisiv decât verdictul final în 51% din cazuri. Nu există pattern P3; GO-bias este monitorizat cu trigger >3 STOP consecutive pe propuneri non-agresive. Detalii: `experiments/run4-rund2-empirical-validation.html#14a`.

## Method

Extract Napoleon vote + rationale din toate `runs/senate/2026-*.json` (excluzând `_input_*` artifacts). Schema:

- Modern: `outputs["napoleon"]` (dict keyed by senator name)
- Multi-round: `rounds[-1].outputs["napoleon"]` sau `rounds[-1].senators["napoleon"]`
- Legacy: `senators["napoleon"]`

Sample N=17 senate runs (total available at analysis date).

## Aggregate metrics

| Metric | Value | Interpretation |
|---|---|---|
| Participation rate | 15/17 = 88% | Healthy (1 ABSENT, 1 NOT_DISPATCHED in R2 without cross-Q) |
| Vote distribution | GO=5, MODIFY=7, STOP=3 | Bi-directional, no STOP anchoring |
| Agreement with verdict | 8/14 = 57% (excluding non-votes) | Adds independent signal, not rubber-stamp |
| Disagreement direction | 3× more permissive (GO over MODIFY), 2× more cautious (STOP over MODIFY) | Real bi-directional perspective |
| P3 over-fit signal | **NONE detected** | Varied rationales across domains |

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
- "Mandatory narrowing: exclude from audit modes with <2 real runs; separate step analysis from mode analysis." — **scope-narrowing**
- "Unbundle into 2 phases. Phase 1 ship now (~1-2h, zero cost); Phase 2 defer until ≥10 senate runs." — **phased delivery**

All rationales reflect the declared specialty ("tokens, hours, operator state") applied variably — no pattern-matching on P3 car wash.

## Caveats

- N=15 votes is small for statistical significance, but sufficient to reject the strong over-fit hypothesis (a P3 over-fit would produce a STOP-heavy distribution, not 5G/7M/3S)
- 5 of 15 runs are on own proposals (self-audit), which biases toward MODIFY anyway (cumulative verdict MODIFY on 13/17 runs)
- Cross-domain rationale validation was qualitative (eyeball); the analysis did not use automatic clustering

## Decision

**Napoleon stays.** Re-evaluate only if a contrary signal appears (>3 consecutive STOPs on non-aggressive proposals, or repetitive P3-style rationales) in the next 10 runs.
