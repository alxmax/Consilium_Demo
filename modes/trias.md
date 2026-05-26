---
name: trias
subagents: 3
cost_multiplier: 3.0
confidence_floor: 0.80
models: sonnet
dispatch_count_worst_case: 7
lazy_routing: true
description: 3 personalities (Pioneer/Architect/Steward), each runs Sequential internally. Auto-downgrades to Dialectic for low/medium magnitude.
---

# Trias mode (high-stakes opt-in)

**Mechanics:** 3 fixed personalities (Pioneer / Architect / Steward), each dispatched as **one Sequential sub-agent** (Conservator→Generator→Control internally) with the personality lens prepended. Democratic majority vote over the 3 chosen results. Cost: 3× Sequential (3 sub-agents vs 1).

**Previous mechanics (archived):** The old Trias dispatched 9 parallel sub-agents (3 personalities × 3 voices). The new design reduces from 9 to 3 sub-agents — each personality runs its own Sequential deliberation internally. The democratic vote over 3 chosen results is preserved.

## When to use
- Irreversible schema/DB migration
- Security audit (auth, crypto, RCE potential)
- Refactor > 5 files
- 2+ plausible architectural approaches, no clear winner
- Cost of wrong decision >> cost of running (3 sub-agents, 3× Sequential)

## Lazy routing (default: enabled)

**Purpose:** Avoid the 3× Sequential cost when the change does not warrant it. Trias checks magnitude via `scope_gate.py` and auto-downgrades to Dialectic for low/medium changes.

**Default:** `lazy=true` — Trias auto-downgrades low/medium magnitude to Dialectic. To force full Trias, the user must explicitly state "use full Trias" or "no lazy routing" in their request.

**Sequencing contract (mandatory):** Magnitude classification MUST run on the **original unstripped context** BEFORE Phase 1 context stripping is applied. Strip happens after the routing decision.

**Routing logic:**
```bash
gate=$(python -X utf8 scripts/scope_gate.py)          # on original context
magnitude=$(echo "$gate" | python -c "import sys,json; print(json.load(sys.stdin)['magnitude'])")
```
- If `magnitude == "high"` → proceed to full Trias (then apply Phase 1 strip below)
- If `magnitude != "high"` → downgrade to Dialectic and emit structured notification:
  ```json
  {
    "trias_lazy_routed": true,
    "routed_to": "dialectic",
    "magnitude": "<low|medium>",
    "magnitude_score": {"files": "<n>", "lines": "<n>", "blocklist_hits": "<n>"},
    "threshold": "high",
    "context_tokens_available": "<approx>",
    "override_instruction": "Re-invoke with explicit 'use full Trias' to force 3-sub-agent mode."
  }
  ```

## Workflow
0. **(Phase 2 — lazy routing)** Run scope_gate on original context and check magnitude. If `magnitude != "high"` AND user has not explicitly requested full Trias, downgrade to Dialectic (emit notification above) and stop Trias workflow here.
1. Orchestrator reads `python -X utf8 scripts/personalities.py` — emits the 3 personalities
2. **(Phase 1 — context strip)** Before building each sub-agent prompt, truncate the raw conversation context to ≈15 000 tokens:
   ```bash
   stripped=$(echo "$raw_context" | python -X utf8 scripts/strip_context.py --truncate-text 15000)
   ```
   Use `$stripped` (not `$raw_context`) in each personality sub-agent prompt. This runs **per sub-agent** so each gets the same budget-capped context. The truncation marker `[... context truncated ...]` signals to the sub-agent that context was cut; it should proceed normally.
3. For each personality, dispatch **1 `consilium-subagent`** with `prompts/<personality>_lens.md` prepended over the task context (using stripped context from Step 2). Each sub-agent runs a full Sequential deliberation (Conservator→Generator→Control) internally with the personality lens applied, and returns `{chosen_approach, rationale, confidence}`.
4. Collect the 3 `chosen_approach` values (one per personality) → `chose` per personality
5. **Unanimous check (B1).** If all 3 personalities chose the same `chose`, skip `team_vote` — the result is unanimous. Set `vote_pattern: "3-0"` and `vote_skipped: true`. Confidence derived directly from `confidence_from_vote_pattern("3-0")`. Log in `deliberation_log` with `reason: "unanimous_personalities"`. If not unanimous, run `team_vote` normally.
6. Orchestrator runs `python -X utf8 scripts/aggregator.py --scheme team_vote` over the 3 chosens (skip if B1 detected unanimity)
7. Confidence derived from vote_pattern — pipe aggregator output directly to `confidence.py`:
   ```bash
   echo '{"personalities":[...],"candidates":[...]}' | python scripts/aggregator.py --scheme team_vote | python scripts/confidence.py
   ```
   Do not manually build `{"candidates":[...],"chosen":"..."}` for Trias — the candidates don't have `scores` per voice.
8. **Deadlock cascade (B2) — only if vote_pattern is 1-1-1 or 0-0-0.** See Failure recovery below.

## Output schema (Trias-specific fields)
```json
{
  "chosen_approach": "candidate_id or null",
  "confidence": 0.82,
  "vote_pattern": "3-0-0",
  "personalities": [
    {"name": "Pioneer", "lens": "pioneer_lens.md", "chose": "candidate_id", "weights": {}},
    {"name": "Architect", "lens": "architect_lens.md", "chose": "candidate_id", "weights": {}},
    {"name": "Steward", "lens": "steward_lens.md", "chose": "candidate_id", "weights": {}}
  ]
}
```

## Vote patterns
| Pattern | Confidence | Outcome |
|---|---|---|
| 3-0 | 0.95 | OK auto |
| 2-1 | 0.75 | OK auto |
| 2-0 | 0.70 | OK auto |
| 1-1-1 | null | → B2 cascade (Round 2 → Skeptic → PEND) |
| 0-0-0 | null | → B2 cascade (Round 2 → PEND) |

## Output JSON (Trias-specific fields)

```json
{
  "success_criterion": "<testable sentence>",
  "chosen_approach": "<id>",
  "team": ["pioneer", "architect", "steward"],
  "vote_pattern": "2-1",
  "vote_counts": {"pioneer": "approach_a", "architect": "approach_a", "steward": "approach_b"},
  "confidence": 0.75,
  "deliberation_log": [{"step": "trias_vote", "vote_pattern": "2-1", "trias_rounds": 1}]
}
```

## Failure recovery

**B2 — Deadlock cascade.** Fires when Round 1 yields 1-1-1 or 0-0-0.

**Round 2 (always first):** Re-dispatch all 3 personality sub-agents. Each receives the other two personalities' `{chosen_approach, reasoning_summary}` from Round 1 as additional context. Re-vote via `team_vote`. Cost: +3 sub-agents.

- Round 2 produces 2-1 or 3-0 → cascade exits, report normally. Set `trias_rounds: 2` in telemetry.
- Round 2 still **1-1-1** → proceed to Skeptic tiebreaker (below).
- Round 2 still **0-0-0** → **PEND** (Skeptic cannot arbitrate among nothing). Set `trias_rounds: 2, deadlock: "0-0-0"` in telemetry.
- Round 2 converts 0-0-0 → 1-1-1 → proceed to Skeptic tiebreaker.

**Skeptic tiebreaker (only after Round 2 1-1-1):** Dispatch 1 sub-agent with `prompts/voices/skeptic.md` plus modified input — all 3 competing `{chosen_approach, reasoning_summary}` pairs. Skeptic selects one id as `chosen`. Cost: +1 sub-agent. Set `trias_rounds: 2, tiebreak: "skeptic"` in telemetry.

- Skeptic returns a valid id → chosen confirmed. Confidence: 0.65 (tiebreak path).
- Skeptic abstains or errors → **PEND**.

**Headless (B2):** All Round 2 and Skeptic dispatches run as non-interactive sub-agents — no prompt needed. Final PEND falls through to `PEND_HEADLESS` logging.

**Max cost (worst case 1-1-1 → Round 2 → Skeptic):** 3 + 3 + 1 = 7 sub-agents.

**Dispatch failure / timeout guard (B2).** The cascade is depth-bounded (≤7 sub-agents) but each dispatch can still hang or error — a sub-agent that never returns must not strand the run with burned budget and no result. Every cascade dispatch (Round 2 ×3, Skeptic ×1) is treated as **best-effort**:

- A sub-agent that errors, times out, or returns malformed JSON is counted as a **non-vote** (it does not block the others). Do not retry more than once per dispatch.
- After Round 2, vote over **whichever personalities returned**. If ≥2 valid votes yield a clear majority → exit normally. If fewer than 2 valid votes remain, or the surviving votes still tie → **PEND immediately**; do NOT escalate to the Skeptic tiebreaker on incomplete data.
- A Skeptic dispatch that fails or times out → **PEND** (never hang waiting on it).
- Whenever the cascade exits on incomplete data, surface the **partial result** — the Round 1 `{personality, chosen_approach}` triple — in the report so the user sees the divergence, and set `cascade_incomplete: true` in telemetry alongside the count of sub-agents that actually returned (`cascade_dispatches_returned: <n>`). A PEND with the three competing positions shown is more useful than a silent stall.

Rationale: Senate audit 2026-05-26 (Dimon) flagged that the 6th/7th cascade dispatch hanging on a slow/near-budget session would burn cost and write no run report (the badge never fires). This guard makes the failure **graceful and visible** instead of silent. The 1-1-1 path that triggers the cascade is rare in practice (≈8% of Trias runs — see `scripts/vote_degeneracy.py`), so the guard protects a real but infrequent tail.

## Skip Trias if
- Diff < 20 lines / 1 file — `scope_gate.py` will skip anyway
- Strict conservatism required (aggregated Trias is −18% Conservator)
- Obvious bugfix — Sequential blind is enough

## trias_split — DEPRECATED

`trias_split` is no longer a user-selectable mode. With Trias reduced from 9 to 3 sub-agents (3× Sequential), `trias_split`'s 3.3× cost advantage over the old 9× Trias no longer exists — both are now effectively the same cost tier. Use standard `trias` instead.

`validate_report.py` maps legacy `trias_split` runs to `trias` via `_LEGACY_MODE_ALIASES` for telemetry backward-compat.
