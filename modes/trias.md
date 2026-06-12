---
name: trias
subagents: 6
cost_multiplier: 4.0
confidence_floor: 0.80
models: haiku(pioneer),sonnet(architect),opus(steward)
dispatch_count_worst_case: 10
lazy_routing: true
description: 3 personalities (Pioneer/Architect/Steward), each runs Sequential internally then challenged by a Skeptic sub-agent at orchestrator level before voting. Lazy routing downgrades by magnitude tier — low/medium → Sequential, high → Dialectic, critical → full Trias (blocklist hits only).
---

# Trias mode (high-stakes opt-in)

**Mechanics:** 3 fixed personalities (Pioneer / Architect / Steward), each dispatched as **one Sequential sub-agent** (Conservator→Generator→Control internally) with the personality lens prepended, then challenged by a **Skeptic sub-agent** dispatched by the orchestrator before the team vote. Democratic majority vote over the (possibly revised) 3 chosen results. Cost: 4× Sequential (6 sub-agents vs 1).

**Why the vote diverges (D4).** The three sub-agents use distinct models (Pioneer → Haiku, Architect → Sonnet, Steward → Opus) and distinct lenses. Divergence has two independent sources: (1) **lens re-weighting** — Pioneer up-weights Generator (upside), Steward up-weights Conservator (risk), Architect balances; (2) **model-level reasoning** — Haiku is fast and decisive, Opus is thorough and conservative, Sonnet is the calibrated middle. Neither source alone is sufficient: lens re-weighting explains *which* candidate each personality selects; model characteristics explain *how confidently* and *at what depth* it reasons about that selection. Divergence is measured by `vote_degeneracy.py` — historical baseline ~52% non-unanimous at n=25 (uniform Sonnet). Post-change target: non-unanimity ≥ baseline; revert signal: < 40% non-unanimity over ≥15 runs.

The weights act **within** each personality only — they decide that personality's own `chose`. **Between** personalities there is no precedence ordering: `aggregator.py --scheme team_vote` is a flat majority over the three `chose` values, and no lens outranks another. A true tie (1-1-1) does not resolve to a "senior" personality — it routes to the B2 deadlock cascade (Round 2 → Skeptic → PEND). So there is no authority hierarchy among the three; the only re-ranking is internal to each sub-agent.

**Previous mechanics (archived):** The old Trias dispatched 9 parallel sub-agents (3 personalities × 3 voices). The new design reduces from 9 to 3 personality sub-agents — each personality runs its own Sequential deliberation internally. Three Skeptic sub-agents (one per personality, Step 3.5) are added at the orchestrator level after Step 3. The democratic vote over 3 (possibly revised) chosen results is preserved.

## When to use
- Irreversible schema/DB migration
- Security audit (auth, crypto, RCE potential)
- Refactor > 5 files
- 2+ plausible architectural approaches, no clear winner
- Cost of wrong decision >> cost of running (6 sub-agents, 4× Sequential)

## Lazy routing (default: enabled)

**Purpose:** Avoid the 4× Trias cost when the change does not warrant it. Trias classifies magnitude via `scope_gate.py` and routes to the cheapest mode that fits — a **graduated ladder** keyed on `scope_gate._MODE_CEILING`:

| magnitude | routes to | cost |
|---|---|---|
| low / medium | **Sequential** | 1× |
| high | **Dialectic** | 1.33× |
| critical (blocklist hit: auth, security, migrations, CI workflows, secrets) | **full Trias** | 4× |

**Default:** `lazy=true`. Only `critical` magnitude proceeds to full Trias; `high` downgrades to Dialectic; `low`/`medium` downgrade all the way to bare Sequential — at low/medium magnitude the marginal scrutiny of Dialectic's Skeptic isn't worth the 1.33× over Sequential. To force full Trias on a non-critical change, the user must explicitly state "use full Trias" or "no lazy routing" in their request.

**Override cost-warning (D2).** An explicit override on a sub-critical change is honored, but **not silently** — the user is paying 4× for a change `scope_gate.py` judged low/medium/high. Before dispatching the 6 sub-agents on an overridden change, emit a one-line warning so the cost is a conscious choice:
```json
{"trias_override_warning": true, "magnitude": "<low|medium|high>", "cost_multiplier": 4.0,
 "note": "Full Trias forced below critical magnitude — 4x cost. Drop the override to auto-route (low/medium → Sequential, high → Dialectic)."}
```
This is a warning, not a refusal: there is no hard block, because the user holds the authority on their own spend (a hard floor would override an explicit, informed instruction). The warning makes the tradeoff visible; the override still proceeds.

**Sequencing contract (mandatory):** Magnitude classification MUST run on the **original unstripped context** BEFORE Phase 1 context stripping is applied. Strip happens after the routing decision.

**Routing logic:**
```bash
gate=$(python -X utf8 scripts/scope_gate.py)          # on original context
magnitude=$(echo "$gate" | python -c "import sys,json; print(json.load(sys.stdin)['magnitude'])")
```
- `magnitude == "critical"` → proceed to full Trias (then apply Phase 1 strip below)
- `magnitude == "high"` → downgrade to **Dialectic**
- `magnitude in {"low", "medium"}` → downgrade to **Sequential**

For any downgrade, emit the structured notification:
```json
  {
    "trias_lazy_routed": true,
    "routed_to": "<sequential|dialectic>",
    "magnitude": "<low|medium|high>",
    "magnitude_score": {"files": "<n>", "lines": "<n>", "blocklist_hits": "<n>"},
    "threshold": "critical",
    "context_tokens_available": "<approx>",
    "override_instruction": "Re-invoke with explicit 'use full Trias' to force 6-sub-agent mode."
  }
  ```

## Workflow
0. **(Phase 2 — lazy routing)** Run scope_gate on original context and check magnitude. If `magnitude != "critical"` AND user has not explicitly requested full Trias, downgrade per the ladder above (high → Dialectic; low/medium → Sequential), emit the notification, and stop the Trias workflow here.
1. Orchestrator reads `python -X utf8 scripts/personalities.py` — emits the 3 personalities
2. **(Phase 1 — context strip)** Before building each sub-agent prompt, truncate the raw conversation context to ≈15 000 tokens:
   ```bash
   stripped=$(echo "$raw_context" | python -X utf8 scripts/strip_context.py --truncate-text 15000)
   ```
   Use `$stripped` (not `$raw_context`) in each personality sub-agent prompt. This runs **per sub-agent** so each gets the same budget-capped context. The truncation marker `[... context truncated ...]` signals to the sub-agent that context was cut; it should proceed normally.
3. **Dispatch all 3 personalities in parallel** (3 `consilium-subagent` Agent calls in the **same** orchestrator message), each with `prompts/<personality>_lens.md` prepended over the task context (using stripped context from Step 2). Each sub-agent runs a full Sequential deliberation (Conservator→Generator→Control) internally with its personality lens applied, and returns `{chosen_approach, rationale, confidence}`. Parallel dispatch is mandatory — sequential dispatch triples wall-clock for no quality gain, and is the root cause of the task-08 timeout pattern observed in benchmark n=10 (2026-05-27).

   **Model dispatch.** Each personality sub-agent is dispatched with `model: <personality.model>` from `personalities.py` output (pioneer → `haiku`, architect → `sonnet`, steward → `opus`). **Steward (Opus) is dispatched schema-less** — do not pass a StructuredOutput schema; Steward returns fenced JSON which the orchestrator parses with `json.loads()`. This is required because Opus+schema StructuredOutput is unreliable and may silently skip the tool call (see project memory `reference_opus_schema_structuredoutput_flaky.md`).

   **Pioneer circuit-breaker.** If Pioneer (Haiku) returns malformed or empty JSON → substitute `model: sonnet` and re-dispatch that personality once. If the substitution also fails, treat Pioneer as a non-vote and continue per B2 timeout rules (≥2 valid votes from the remaining two personalities yield a clear majority; < 2 valid votes → PEND immediately).

   **Token cost.** The 3 personality sub-agents (Haiku+Sonnet+Opus) average ≈ $3/$15 per 1M in/out — break-even with 3× Sonnet. The 3 Skeptic sub-agents (Step 3.5, each on Sonnet) add ≈ 1× Sequential each, raising the total to `cost_multiplier: 4.0` (vs Sequential).

   **Runtime audit (Senate 2026-05-28, [trias-parallelism-enforcement](../runs/senate/2026-05-28_220338-trias-parallelism-enforcement.json), MODIFY 6-3-0):** `benchmark/scripts/check_trias_parallelism.py` reads the Claude CLI session JSONL transcript after each Trias run and writes `trias_dispatch_pattern: "serial"|"parallel"|"mixed"|"scale_down"` into `pipeline_audit.json`. Empirical observation as of 2026-05-28: 7/7 real-deliberation Trias runs were SERIAL despite this mandate. A spec-rewrite attempt (imperative phrasing + worked example + anti-pattern) also produced SERIAL — voice-prompt rewrites do not enforce orchestrator dispatch order (Tacitus retrospective, 0/6 clean-GO). The mandate stays as guidance; the runtime audit is the observability mechanism. Full evidence: [experiments/trias-parallelism-2026-05-28.md](../experiments/trias-parallelism-2026-05-28.md).

   **Vehicle decision (Senate 2026-05-29, [trias-parallelism-vehicle-a1-vs-a2](../runs/senate/2026-05-29_140645-trias-parallelism-vehicle-a1-vs-a2.json), MODIFY 6-3-0):** a follow-up audit reviewed the two architectural fixes deferred above — A1 (benchmark subprocess fan-out) and A2 (reimplement the mode via a Workflow orchestration vehicle). Outcome: **serial dispatch is accepted as by-construction-not-intent, not a bug to fix now.** A2 was rejected (the LangGraph orchestration-vehicle pattern — STOP×2 historically, never regretted; needs a separate architectural proposal if ever revived). A1 is admissible only as an explicitly-labeled *benchmark-harness* wall-clock fix, never claimed as real `/consilium` behavior. Crucially, any parallelism investment is **gated on the existing kill-criterion** — ≥2 Trias wins in n≥20 oracle-validated tasks (current record: 0 wins at n=6 on a saturated corpus). Until Trias demonstrates value, the proportional path is accept-serial + observe. Graduation mechanism: `benchmark/scripts/check_trias_escalation.py` (counts accumulated serial runs; logs a "revisit parallelism" recommendation at threshold).
3.5. **Skeptic challenge — 3 parallel Skeptic sub-agents (one per personality chosen).** After Step 3 completes and all 3 personality chosens are collected, dispatch 3 Skeptic sub-agents in parallel (3 Skeptic Agent calls in the **same** orchestrator message). Each Skeptic receives `{chosen: <personality's chosen_approach + sketch + rationale>, success_criterion, verification}` per `prompts/voices/skeptic.md`. If Skeptic returns `can_object: true` with `addressable: "in_place"`, the personality's chosen is revised to the Skeptic's preferred alternative (advisory by default; orchestrator-level only — the sub-agent is not re-dispatched). `team_vote` proceeds on the (possibly revised) chosens. **B2 cascade exception:** Round 2 dispatches personality sub-agents only (no Skeptics) — the deadlock resolution path prioritizes speed. Cost: +3 sub-agents over Step 3.

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
  "vote_pattern": "3-0",
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
| 1-1-0 | null | → B2 cascade (2 distinct chosen + 1 abstain) |
| 1-0-0 | null | → B2 cascade (1 chosen + 2 abstain) |
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

**Max cost (worst case 1-1-1 → Round 2 → Skeptic):** 6 (Round 1: 3 personalities + 3 Skeptics) + 3 (Round 2 personalities, no Skeptics) + 1 (tiebreaker Skeptic) = 10 sub-agents.

**Dispatch failure / timeout guard (B2).** The cascade is depth-bounded (≤10 sub-agents) but each dispatch can still hang or error — a sub-agent that never returns must not strand the run with burned budget and no result. Every cascade dispatch (Round 2 ×3, Skeptic ×1) is treated as **best-effort**:

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

`trias_split` is no longer a user-selectable mode. With Trias reduced from 9 to 3 sub-agents at the time of deprecation (since grown to 6 with the per-personality Skeptic challenge, 4× Sequential), `trias_split`'s 3.3× cost advantage over the old 9× Trias no longer exists — both are now effectively the same cost tier. Use standard `trias` instead.

`validate_report.py` maps legacy `trias_split` runs to `trias` via `_LEGACY_MODE_ALIASES` for telemetry backward-compat.

<!-- implements: CONSILIUM-MODE-TRIAS-001 -->

