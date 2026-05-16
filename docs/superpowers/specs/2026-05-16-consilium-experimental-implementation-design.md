# Design: Consilium Experimental Implementation
**Date:** 2026-05-16
**Branches:** `feat/rund2-architecture`, `feat/philosophical-voice-variants`
**Status:** Approved

---

## Overview

Two parallel branches implement the full experimental backlog for Consilium:

1. **`feat/rund2-architecture`** — Three-layer architecture (sequential dispatch, 8-component aggregator, principle_extraction)
2. **`feat/philosophical-voice-variants`** — 5 philosophical voice variants + refinement layer

SENAT (`feat/senat-entity`) is complete (PRs #56, #57). No remaining tracked changes.

**Merge order:** RUND2 first → Philosophical rebases on updated main, resolves conflicts on `validate_report.py` + `SKILL.md`.

---

## Branch 1: `feat/rund2-architecture`

### Files changed

| File | Type | Change |
|---|---|---|
| `prompts/conservator.md` | MOD | reversibility×magnitude matrix, tokens_budget, counterparty_risks, bias_check, veto irreversible |
| `prompts/generator.md` | MOD | fallback_scenario, coverage_check, challenge_upward, abstain, selective visibility from Conservator |
| `prompts/control.md` | MOD | glossary (max 5), hidden_assumptions, disagreements, fixed/negotiable_constraints, veto soft on glossary_fail |
| `scripts/aggregator.py` | MOD massive | 8 components (see below) |
| `scripts/vocabulary_map.py` | NEW | Fixed dict JSON→natural language |
| `scripts/principle_extraction.py` | NEW (inactive) | Written but disabled until runs/ >= 10 entries with verifiable outcome |
| `scripts/validate_report.py` | MOD | Accepts regression_risk as object, new optional fields, `--strict-rund2` flag. Sections delimited with `# === RUND2 ===` |
| `scripts/test_validate_report.py` | NEW/MOD | Tests for all new components |
| `SKILL.md` | MOD | Sections: Three-layer architecture, Sequential dispatch, Veto powers, Principle_Extraction. Delimited with `<!-- === RUND2 === -->` |

### Aggregator 8 components

1. **Vocabulary_map** — translates JSON values to user-facing natural language (single source of truth)
2. **Length_targets** — max sentence count based on magnitude × reversibility matrix
3. **Priority veto order** — glossary_fail (BLOCK) → irreversibility without consent (BLOCK) → substantial disagreement (REWORK) → scale_down/up (ADAPT) → default aggregate
4. **Tension expose** — detects unresolved tensions between voices, outputs explicitly instead of forcing consensus
5. **Metadata** — rich run metadata: date, question, category, veto_triggered, execution_metrics, outcome placeholder
6. **user_profile.json** — minimal persistent profile (gitignored): veto patterns, recurring categories, last_updated
7. **Multi-confidence** — `confidence_per_option` + `confidence_methodology` (< 0.5 → "deliberare incompletă")
8. **Escalation rule** — if 3+ priorities trigger simultaneously, output explicit table and request user decision

### Dispatch change

**Old:** parallel (all 3 voices simultaneously)  
**New:** sequential Conservator → Generator → Control

- Parallel mode **removed completely** from dispatch options
- Auto-trigger parallel as cross-check only on `critical + irreversible`
- Audit parallel silently every 20 runs; increases to 1/5 if systematic divergence detected

### Decisions resolved

| Decision | Resolution |
|---|---|
| Parallel mode | Removed completely |
| Veto budget (meta_recommendation) | 5 scale_up/down per month; soft warning on exhaustion |
| user_profile.json | Gitignored (local only, like FEEDBACK.md) |
| Phase 11 self-validation | Agent runs `/consilium senate` on its own changes |

### Skipped / deferred

- Phase 8 (Senate): already done in PRs #56, #57
- Phase 14 (empirical validation): post-merge, not in this PR
- Decisions in Annexe D items 3, 4, 5: deferred to after empirical data

---

## Branch 2: `feat/philosophical-voice-variants`

### Files changed

| File | Type | Change |
|---|---|---|
| `prompts/control_wittgenstein.md` | NEW | Semantic verification: glossary 2-5 terms, hidden_assumptions, semantic mismatch detection |
| `prompts/conservator_aurelius.md` | NEW | Risk matrix: reversibility×magnitude, meta_recommendation scale_down/up, status quo bias warning |
| `prompts/control_aurelius.md` | NEW | Zone-of-control filter: in/out/uncertain_control, wasted_deliberation |
| `prompts/conservator_confucius.md` | NEW (EXPERIMENTAL) | Precedent consultation from runs/, fallback_to_abstract if < 3 matches |
| `prompts/refiner_deletion.md` | NEW (Refinement layer) | Post-Aggregator, Musk-FAST: deletion discipline + add-back 10% rule |
| `scripts/precedent_search.py` | NEW | TF-IDF light, stdlib-only, CLI: `--query "..." --limit 5` |
| `scripts/validate_report.py` | MOD | `_validate_regression_risk` helper, per-voice optional fields, `--strict-philosophical=<voice>` flags. Sections delimited with `# === PHILOSOPHICAL VOICES ===` |
| `scripts/test_validate_report.py` | NEW | 20+ tests: backward compat + per-voice + cross-voice + smoke |
| `SKILL.md` | MOD | Section "Voice variants" with Stable/EXPERIMENTAL table. Delimited with `<!-- === PHILOSOPHICAL VOICES === -->` |

### Voice specs

**Control + Wittgenstein** (Stable)
- Identifies 2-5 key terms, builds operational glossary for this deliberation
- Output: `{"glossary": {...}, "hidden_assumptions": [...]}`
- Limit: max 5 terms; above that, voice refuses to proceed

**Conservator + Aurelius** (Stable)
- Replaces scalar regression_risk with reversibility×magnitude object
- Adds meta_recommendation: scale_down / scale_up / null
- Explicit status quo bias warning in prompt
- Output: `{"regression_risk": {"reversibility": "...", "magnitude": "...", "net_concern": 0.05}, "meta_recommendation": "..."}`

**Control + Aurelius** (Stable, niche use-case)
- Filters decisions by zone of control
- Output: `{"in_control": [...], "out_of_control": [...], "uncertain_control": [...], "wasted_deliberation": "...|null", "actionable_scope": "..."}`
- Explicitly documented distinction from Conservator+Aurelius: scope filter vs risk filter

**Conservator + Confucius** (EXPERIMENTAL)
- Consults runs/ via precedent_search.py (injected by dispatcher, Optiunea A)
- Falls back to standard conservator.md behavior with `fallback_to_abstract: true` if 0 precedents
- Output: `{"precedent_search": {"query_terms": [...], "matches_found": 0, "fallback_to_abstract": true}, "ancestor_guidance": "...|null", "regression_risk": 0.15}`
- Gating: if runs/ < 10 → voice file created but SKILL.md marks `[blocked until runs/ >= 10]`

**Refiner + Deletion** (Refinement layer — NOT deliberation)
- Runs post-Aggregator, not alongside other voices
- Deletion discipline: identify indispensable parts, delete rest, add back max 10%
- Trigger: Aggregator output > 200 tokens OR explicit `--refine` flag; skip if scale_down already active
- Output: `{"original_length_tokens": ..., "refined_length_tokens": ..., "cuts_made": [...], "parts_added_back": [...], "deletion_ratio": ..., "addback_ratio": ..., "warning": "null|over-deletion suspected|under-deletion"}`

### Phase 5c — Question audit (mandatory pre-commit)

Agent audits all 5 prompts against 4 criteria: Operational / Discrete / Self-scaling / Bounded.
If any voice has 2+ ⚠️ → rewrite prompt until criteria pass. No PR without passing audit.

### Phase 10 — Self-improvement

Agent runs `/consilium senate` on its own changes.
- if verdict GO: proceed to commit
- if verdict MODIFY: apply modify_requests, then commit
- if verdict STOP: flag to user before committing

---

## Conflict resolution plan

**Conflicting files:** `scripts/validate_report.py`, `SKILL.md`, `scripts/aggregator.py`

- `aggregator.py`: RUND2 rewrites it entirely; Philosophical adds a small Confucius injection case on top after rebase
- `validate_report.py`: both add independent sections (delimited)
- `SKILL.md`: both add independent sections (delimited)

**Strategy:**
1. Each agent writes clearly delimited sections in validate_report.py + SKILL.md (see delimiter comments above)
2. RUND2 merges first
3. Philosophical rebases on updated main
4. At rebase, conflicts on validate_report.py + SKILL.md resolved by keeping all content from both sections
5. At rebase, aggregator.py conflict resolved by adding Confucius injection case to RUND2's rewritten aggregator
6. Combined `--strict-rund2` + `--strict-philosophical=<voice>` flags coexist independently

---

## Agent execution plan

```
Phase 1: Verify main is clean
Phase 2: Spawn Agent RUND2 on feat/rund2-architecture (background)
Phase 3: Spawn Agent Philosophical on feat/philosophical-voice-variants (background)
Phase 4: Both agents work independently
Phase 5: RUND2 agent runs /consilium senate on its own changes (Phase 11)
         → if verdict GO: proceed to commit
         → if verdict MODIFY: apply modify_requests, then commit
         → if verdict STOP: flag to user before committing
Phase 6: Philosophical agent runs /consilium standard on its own changes (Phase 10)
Phase 7: Both agents push and report branch names
Phase 8: User merges RUND2 first, then Philosophical rebases
```

---

## Success criteria

- `python scripts/validate_report.py < runs/<latest>.json` passes with no errors on both branches
- All new test files pass: `python scripts/test_validate_report.py`
- No modifications to existing voice prompts except the 3 core ones (conservator.md, generator.md, control.md) in RUND2
- Philosophical voices do NOT modify core prompts (only create new variant files)
- Phase 5c question audit passes for all 5 philosophical voices
- Single commit per branch following CLAUDE.md Conventional Commits format
