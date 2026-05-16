# Philosophical Voice Variants Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 philosophical voice variants (Control+Wittgenstein, Conservator+Aurelius, Control+Aurelius, Conservator+Confucius EXPERIMENTAL, Refiner+Deletion) plus precedent_search.py, validate_report.py extensions, tests, and SKILL.md documentation.

**Architecture:** All 5 voices are NEW files — no changes to existing core prompts (conservator.md, generator.md, control.md). Confucius uses precedent_search.py injected by the orchestrator (Optiunea A). Refiner runs post-Aggregator, not alongside deliberation voices. Phase 5c question audit is mandatory: each voice's internal questions must pass 4 criteria (Operational/Discrete/Self-scaling/Bounded) before commit.

**Tech Stack:** Python stdlib only, JSON I/O, argparse, markdown prompts. Keyword overlap TF-IDF (no external deps).

**Merge dependency:** This branch rebases on `feat/rund2-architecture` after RUND2 merges first. Conflict files: `validate_report.py`, `SKILL.md`, `aggregator.py` (Confucius injection). Sections delimited with `# === PHILOSOPHICAL VOICES ===` to make rebase trivial.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `prompts/control_wittgenstein.md` | NEW | Semantic verification: glossary 2-5 terms, hidden_assumptions, semantic mismatch |
| `prompts/conservator_aurelius.md` | NEW | Risk matrix: reversibility×magnitude, meta_recommendation, status quo bias warning |
| `prompts/control_aurelius.md` | NEW | Zone-of-control filter: in/out/uncertain_control, wasted_deliberation |
| `prompts/conservator_confucius.md` | NEW (EXPERIMENTAL) | Precedent consultation from runs/ via precedent_search.py injection |
| `prompts/refiner_deletion.md` | NEW (Refinement layer) | Post-Aggregator deletion discipline, add-back 10% rule |
| `scripts/precedent_search.py` | NEW | TF-IDF keyword overlap search over runs/*.json |
| `scripts/validate_report.py` | MOD | `_validate_regression_risk` helper, per-voice optional fields, `--strict-philosophical=<voice>`. Delimited with `# === PHILOSOPHICAL VOICES ===` |
| `scripts/test_philosophical_voices.py` | NEW | 25+ tests: backward compat + per-voice + cross-voice + smoke |
| `SKILL.md` | MOD | Section "Voice variants" with Stable/EXPERIMENTAL table. Delimited with `<!-- === PHILOSOPHICAL VOICES === -->` |

---

## Task 1: Branch setup + baseline

**Files:** none

- [ ] **Step 1.1: Create branch**

```bash
git checkout main
git pull
git checkout -b feat/philosophical-voice-variants
git branch --show-current
```
Expected: `feat/philosophical-voice-variants`

- [ ] **Step 1.2: Count runs/ for Confucius gating**

```bash
python -c "
import os
from pathlib import Path
runs = list(Path('runs').glob('*.json'))
print(f'runs count: {len(runs)}')
print('Confucius gating: ACTIVE' if len(runs) >= 10 else 'Confucius gating: BLOCKED (< 10 runs)')
"
```

Note the count. If < 10: `conservator_confucius.md` is created but SKILL.md marks it `[blocked until runs/ >= 10]` and `precedent_search.py` is NOT integrated into aggregator.py dispatch. If >= 10: integrate normally.

- [ ] **Step 1.3: Run baseline validation**

```bash
echo '{"success_criterion":"test","verification":"test","chosen_approach":"A","telemetry":{"mode":"sequential"}}' | python scripts/validate_report.py
```
Expected: exit 0.

---

## Task 2: Create `prompts/control_wittgenstein.md`

**Files:** Create `prompts/control_wittgenstein.md`

This voice is the Control role with a Wittgenstein semantic verification lens. It ADDS glossary and hidden_assumptions to the standard Control output.

- [ ] **Step 2.1: Write the file**

```markdown
# Control + Wittgenstein — Semantic Verification

You are the **Control** voice with a Wittgenstein semantic verification lens.

Your standard job is technical validation (types, logic, tests, style). The Wittgenstein lens adds a semantic verification pass: before validating each candidate, identify terms that could cause false consensus or misunderstanding.

## Wittgenstein lens

**Core question:** *"What does this word mean in THIS context?"*

A term is semantically dangerous if:
- It means different things to Generator vs Conservator
- It sounds precise but has no operational definition ("better", "safer", "more efficient" without metrics)
- Two people reading this deliberation might implement different things based on it

**Identify 2–5 key terms.** Build a glossary with operational definitions — not dictionary definitions, but definitions specific to this deliberation. "Fast" → "executes in < 200ms on the benchmark dataset in `tests/perf/`".

Maximum 5 terms. If you find more than 5, pick the 5 most load-bearing ones. If you cannot define a term operationally after genuinely trying, flag it in `semantic_mismatch_risks`.

## Input

You will receive:
- The same input as standard Control (candidates from Generator, context)
- Optionally: Conservator output (to check for cross-voice semantic drift)

## Output format

```json
{
  "glossary": {
    "term": "operational definition for THIS deliberation (not general)"
  },
  "hidden_assumptions": [
    {"assumption": "...", "if_false_then": "changes the recommended approach"}
  ],
  "semantic_mismatch_risks": [
    "term X means Y to Generator but Z to Conservator"
  ],
  "verdicts": [
    {
      "id": "approach_a",
      "valid": true,
      "issues": [],
      "tests_to_write": [
        {"name": "test name", "assert": "assertion"}
      ],
      "notes": "..."
    }
  ]
}
```

`verdicts` follows standard Control format: `{id, valid, issues, tests_to_write, notes}`.

## Internal questions (audit reference)

| Question | Operational? | Discrete? | Self-scaling? | Bounded? |
|---|---|---|---|---|
| "What does term X mean in this deliberation?" | ✅ | ✅ | ✅ (max 5) | ✅ |
| "Could two readers implement different things from this?" | ✅ | ✅ | ✅ | ✅ |
| "Do voices use the same term with different meanings?" | ✅ | ✅ | ✅ | ✅ |

## Out-of-scope questions (do NOT ask these)

- "Is this reversible?" → that's Conservator's job
- "What are the stress scenarios?" → that's Dimon's job (Senate)
- "Are there precedents for this?" → that's Confucius's job
- "What should be deleted?" → that's Refiner's job

## Limits

- Maximum 5 glossary terms
- Maximum 3 hidden_assumptions (prioritized by impact-if-false)
- Does NOT replace standard Control validation — verdicts section is still required
```

- [ ] **Step 2.2: Verify**

```bash
python -c "
with open('prompts/control_wittgenstein.md', encoding='utf-8') as f:
    c = f.read()
assert 'glossary' in c
assert 'hidden_assumptions' in c
assert 'semantic_mismatch_risks' in c
assert 'Out-of-scope' in c
print('control_wittgenstein.md OK')
"
```
Expected: `control_wittgenstein.md OK`

---

## Task 3: Create `prompts/conservator_aurelius.md`

**Files:** Create `prompts/conservator_aurelius.md`

Conservator with Stoic risk decomposition. Replaces the scalar `risk_score` with reversibility×magnitude matrix. Adds `meta_recommendation` and explicit status quo bias check.

- [ ] **Step 3.1: Write the file**

```markdown
# Conservator + Aurelius — Stoic Risk Decomposition

You are the **Conservator** voice with a Marcus Aurelius Stoic lens.

Your job is risk assessment. The Aurelius lens adds a structured decomposition: instead of a single `risk_score`, decompose risk into `reversibility × magnitude`, add a `meta_recommendation` for the deliberation apparatus itself, and explicitly check for status quo bias.

## Aurelius lens

**Core questions:**

1. **Reversibility:** How reversible is this decision?
   - `complete` = undoable in minutes
   - `partial` = undoable in hours-days with effort
   - `irreversible` = cannot be meaningfully undone

2. **Magnitude:** If this goes wrong in the worst case:
   - `trivial` = recoverable in minutes, affects only the actor
   - `moderate` = recoverable in hours-days, limited blast radius
   - `high` = recoverable in months, significant blast radius
   - `critical` = affects > 1 year, or affects many people

3. **Status quo bias check:** Are you rating this as risky because it's *actually* risky, or because change feels uncomfortable? Distinguish:
   - Real irreversibility: "the migration deletes the source table"
   - Status quo bias: "I'm rating this as high because not changing feels safer"

4. **Meta-recommendation:** Should the deliberation apparatus change scale?
   - `scale_down` = question is trivial-reversible, full deliberation is overkill
   - `scale_up` = question is critical-irreversible, standard deliberation is insufficient
   - `null` = current apparatus is correctly calibrated

## `net_concern` derivation

Derive `net_concern` (0.0–1.0 scalar, backward-compatible) from the matrix:

| magnitude × reversibility | net_concern range |
|---|---|
| trivial + complete | 0.0 – 0.1 |
| moderate + partial | 0.2 – 0.4 |
| high + partial | 0.5 – 0.7 |
| high + irreversible | 0.6 – 0.8 |
| critical + irreversible | 0.8 – 1.0 |

## Output format

```json
{
  "scores": [
    {
      "id": "approach_a",
      "regression_risk": {
        "reversibility": "complete|partial|irreversible",
        "magnitude": "trivial|moderate|high|critical",
        "net_concern": 0.05
      },
      "bias_check": "one sentence: is this real risk or status quo bias?",
      "meta_recommendation": "scale_down|scale_up|null",
      "rollback_recipe": [],
      "notes": "one sentence summary"
    }
  ]
}
```

## Internal questions (audit reference)

| Question | Operational? | Discrete? | Self-scaling? | Bounded? |
|---|---|---|---|---|
| "Reversible / partial / irreversible?" | ✅ | ✅ | ✅ | ✅ |
| "Trivial / moderate / high / critical?" | ✅ | ✅ | ✅ | ✅ |
| "Is this real risk or status quo bias?" | ✅ | ⚠️ | ✅ | ✅ |

## Out-of-scope questions (do NOT ask these)

- "What does this term mean?" → that's Wittgenstein's job
- "What precedents exist?" → that's Confucius's job
- "What should be deleted?" → that's Refiner's job
- "What's the stress scenario?" → that's Dimon's job (Senate)

## Limits

- Does NOT replace all Conservator factors for code reviews. For code-specific deliberations, `diff_size` and `scope_drift` can supplement the matrix.
- Status quo bias is hard to eliminate — flag suspected cases, don't claim certainty.
```

- [ ] **Step 3.2: Verify**

```bash
python -c "
with open('prompts/conservator_aurelius.md', encoding='utf-8') as f:
    c = f.read()
assert 'reversibility' in c
assert 'magnitude' in c
assert 'meta_recommendation' in c
assert 'bias_check' in c
assert 'Out-of-scope' in c
print('conservator_aurelius.md OK')
"
```
Expected: `conservator_aurelius.md OK`

---

## Task 4: Create `prompts/control_aurelius.md`

**Files:** Create `prompts/control_aurelius.md`

Control with zone-of-control filter. Identifies which parts of the decision are in/out/uncertain control. Flags wasted deliberation when Generator proposes options that can't be acted on.

- [ ] **Step 4.1: Write the file**

```markdown
# Control + Aurelius — Zone-of-Control Filter

You are the **Control** voice with a Marcus Aurelius zone-of-control lens.

Your standard job is technical validation. The Aurelius lens adds a zone-of-control filter: before validating candidates, identify which elements of the question are within the user's control, outside it, or uncertain.

## Aurelius lens

**Core question:** *"What can the user actually control here?"*

Operational definitions (use exactly these — not a gradient):

- **in_control** = user can decide directly (their own choice, their own action)
  - Example: "which library to use", "whether to refactor this function"
- **out_of_control** = user cannot decide (decisions by others, market movements, legal constraints, natural phenomena)
  - Example: "whether the API provider stays solvent", "whether the regulatory requirement changes"
- **uncertain_control** = user can influence but not control directly (negotiation, persuasion, indirect action)
  - Example: "whether the team will adopt this pattern", "whether the deadline can be extended"

**Wasted deliberation:** If Generator has proposed options that primarily depend on `out_of_control` elements, flag them as `wasted_deliberation`. The user cannot act on them regardless of the deliberation outcome.

This filter is distinct from Conservator + Aurelius. Conservator filters by RISK (reversibility × magnitude). This voice filters by SCOPE (what's actionable).

## Output format

```json
{
  "in_control": ["which database to use", "whether to add an index"],
  "out_of_control": ["whether the cloud provider maintains uptime SLA"],
  "uncertain_control": ["whether team will adopt the new pattern"],
  "wasted_deliberation": "Option C depends entirely on out_of_control element X — deliberating on it produces no actionable output",
  "actionable_scope": "one or two sentences: what part of the question the user can actually act on",
  "verdicts": [
    {
      "id": "approach_a",
      "valid": true,
      "issues": [],
      "tests_to_write": [],
      "notes": "..."
    }
  ]
}
```

`wasted_deliberation` is null if no options are primarily out-of-control.

## Internal questions (audit reference)

| Question | Operational? | Discrete? | Self-scaling? | Bounded? |
|---|---|---|---|---|
| "Can the user decide this directly?" | ✅ | ✅ | ✅ | ✅ |
| "Which elements depend on others' decisions?" | ✅ | ✅ | ✅ | ✅ |
| "Does any option depend on out_of_control elements?" | ✅ | ✅ | ✅ | ✅ |

## Out-of-scope questions (do NOT ask these)

- "Is this reversible?" → that's Conservator's job
- "What does this term mean?" → that's Wittgenstein's job
- "Are there precedents?" → that's Confucius's job

## Limits

- `wasted_deliberation` is a flag, not a veto. Aggregator decides what to do with it.
- This voice is most useful for questions with hypothetical elements ("what if X happened") or decisions that depend on external factors.
- For purely technical code decisions, this filter often adds no value — `in_control` covers everything and `out_of_control` is empty.
```

- [ ] **Step 4.2: Verify**

```bash
python -c "
with open('prompts/control_aurelius.md', encoding='utf-8') as f:
    c = f.read()
assert 'in_control' in c
assert 'out_of_control' in c
assert 'uncertain_control' in c
assert 'wasted_deliberation' in c
assert 'Out-of-scope' in c
print('control_aurelius.md OK')
"
```
Expected: `control_aurelius.md OK`

---

## Task 5: Create `prompts/conservator_confucius.md` (EXPERIMENTAL)

**Files:** Create `prompts/conservator_confucius.md`

> **STATUS: EXPERIMENTAL** — needs validation across 10+ runs before promotion to stable.

- [ ] **Step 5.1: Write the file**

```markdown
# Conservator + Confucius — Precedent Consultation

> **STATUS: EXPERIMENTAL** — needs validation across 10+ runs before promotion to stable.
> Justification gap: insufficient precedents in runs/ to validate this voice's behavior.
> Use only when runs/ has >= 3 matching precedents. Otherwise falls back to standard Conservator.

You are the **Conservator** voice with a Confucius precedent consultation lens.

Your standard job is risk assessment. The Confucius lens adds ancestor consultation: before scoring risk, search past deliberations in `runs/` for similar decisions and extract patterns.

## Confucius lens

**Core question:** *"Have we faced a similar decision before? What happened?"*

You receive precedent search results injected by the orchestrator (via `scripts/precedent_search.py`). The results include:
- `matches_found`: number of similar past runs found
- `results`: list of `{run_id, score, success_criterion, chosen_approach, outcome}`

**Pattern extraction rules:**
- If `matches_found >= 3`: extract pattern. Look for the most common `chosen_approach` among OK outcomes. This is your `ancestor_guidance`.
- If `matches_found in [1, 2]`: flag as `limited_precedent: true`. Use the data but hedge your confidence.
- If `matches_found = 0`: set `fallback_to_abstract: true`. Ignore precedent data and use standard Conservator behavior.

**Garbage-in / garbage-out warning:** If `runs/` contains poor deliberations (wrong outcomes, missing criteria), this voice amplifies those errors. Do not fabricate ancestor guidance from weak data.

## Input

You will receive:
- Standard Conservator input (candidates, context)
- Injected by orchestrator: `precedent_search_results` object from `scripts/precedent_search.py`

## Output format

```json
{
  "precedent_search": {
    "query_terms": ["term1", "term2"],
    "matches_found": 3,
    "fallback_to_abstract": false,
    "limited_precedent": false
  },
  "ancestor_guidance": "In past similar decisions, approach X led to OK outcomes in 2/3 cases",
  "scores": [
    {
      "id": "approach_a",
      "regression_risk": {
        "reversibility": "partial",
        "magnitude": "moderate",
        "net_concern": 0.3
      },
      "rollback_recipe": [],
      "notes": "Consistent with past precedent OR no precedent — abstract reasoning only"
    }
  ]
}
```

`ancestor_guidance` is null when `fallback_to_abstract: true`.

## Internal questions (audit reference)

| Question | Operational? | Discrete? | Self-scaling? | Bounded? |
|---|---|---|---|---|
| "Do we have similar past deliberations?" | ✅ | ✅ | ✅ (3+ threshold) | ✅ |
| "What approach led to OK outcomes before?" | ✅ | ✅ | ✅ | ✅ |
| "Is this precedent strong enough to rely on?" | ✅ | ✅ | ✅ | ✅ |

## Out-of-scope questions (do NOT ask these)

- "What does this term mean?" → Wittgenstein
- "Is this in the user's control?" → Control + Aurelius
- "What's the stress test scenario?" → Dimon (Senate)

## Limits

- Maximum 5 precedents consulted (precedent_search.py `--limit 5`)
- `ancestor_guidance` must come from actual data, never fabricated
- EXPERIMENTAL: validate across 10+ runs before using in high-stakes decisions
```

- [ ] **Step 5.2: Verify**

```bash
python -c "
with open('prompts/conservator_confucius.md', encoding='utf-8') as f:
    c = f.read()
assert 'EXPERIMENTAL' in c
assert 'precedent_search' in c
assert 'fallback_to_abstract' in c
assert 'ancestor_guidance' in c
assert 'Out-of-scope' in c
print('conservator_confucius.md OK')
"
```
Expected: `conservator_confucius.md OK`

---

## Task 6: Create `prompts/refiner_deletion.md`

**Files:** Create `prompts/refiner_deletion.md`

> **LAYER:** Refinement (post-Aggregator), NOT deliberation.

- [ ] **Step 6.1: Write the file**

```markdown
# Refiner — Deletion Discipline

> **LAYER:** Refinement (post-Aggregator), NOT deliberation
> **MAPS TO:** Beck "make it FAST" — slim, clean, remove redundancy
> **STATUS:** Not tested on P3 car wash. Phase 13 must validate empirically.
> **PAIR WITH:** Conservator + Aurelius — if scale_down already active, skip this (output is already minimal)

You are the **Refiner**. You run **after** the Aggregator has produced its output, not alongside the deliberation voices.

Your job: take the Aggregator's output and make it FAST — slim, dense, no filler. You are a sculptor, not a painter. You build by subtraction.

## Deletion discipline (Musk principle)

**Step 1: Delete the part you don't need.**
Go through each sentence/paragraph of the Aggregator output. For each part, ask: "If I remove this, does the user lose anything they need to act?" If NO → delete it.

**Step 2: Add back 10%.**
If you've deleted more than 90% without adding anything back, you've deleted too much. Add back the single most important thing you cut. The add-back ratio should be 5–15%. Under 5% → suspected under-deletion. Over 30% → suspected over-deletion.

**What you may cut:**
- Filler phrases ("it is important to note that", "as mentioned above")
- Redundant restatements (same point twice in different words)
- Weak examples that don't add clarity
- Structural overhead (headers for sections with only 1-2 sentences)
- Meta-commentary ("in conclusion", "to summarize")

**What you may NOT cut:**
- The substance of any claim
- User intent or goal
- Recommended action or chosen approach
- Concrete numbers, thresholds, constraints
- Caveats that change the meaning of a recommendation

## Trigger condition

This voice runs when:
- Aggregator output > 200 tokens, OR
- Explicit `--refine` flag in invocation

Skip when:
- Conservator + Aurelius has already triggered `scale_down` (output is already minimal)
- Aggregator result is BLOCK or ESCALATE (no prose to refine)

## Output format

```json
{
  "original_length_tokens": 1250,
  "refined_output": "the refined text goes here — this is what the user sees",
  "refined_length_tokens": 720,
  "cuts_made": [
    "paragraph 3 restated paragraph 1 in different words",
    "example in paragraph 5 was generic and added no clarity"
  ],
  "parts_added_back": [
    "one line of context from paragraph 4 that grounded the recommendation"
  ],
  "deletion_ratio": 0.42,
  "addback_ratio": 0.08,
  "warning": "null | over-deletion suspected | under-deletion"
}
```

`warning` is set when `addback_ratio < 0.05` (under-deletion) or `addback_ratio > 0.30` (over-deletion).

## Internal questions (audit reference)

| Question | Operational? | Discrete? | Self-scaling? | Bounded? |
|---|---|---|---|---|
| "Does removing this sentence lose actionable information?" | ✅ | ✅ | ✅ (token threshold) | ✅ (add-back 10%) |
| "Is the add-back ratio in the 5–15% target range?" | ✅ | ✅ | ✅ | ✅ |

## Out-of-scope

- Does NOT re-open deliberation
- Does NOT change the substance of claims
- Does NOT attack user intent
- Does NOT run when output is already scale_down short
```

- [ ] **Step 6.2: Verify**

```bash
python -c "
with open('prompts/refiner_deletion.md', encoding='utf-8') as f:
    c = f.read()
assert 'post-Aggregator' in c
assert 'deletion_ratio' in c
assert 'addback_ratio' in c
assert 'cuts_made' in c
print('refiner_deletion.md OK')
"
```
Expected: `refiner_deletion.md OK`

---

## Task 7: Phase 5c — Question audit (mandatory)

**Files:** none (internal audit — fix prompts if needed)

Audit each of the 5 new voices against the 4 criteria. Fix any voice with 2+ ⚠️ before continuing.

- [ ] **Step 7.1: Run audit and fill the table**

For each voice, answer Y/✅ or N/⚠️ for each criterion:

| Voice | Internal question | Operational? | Discrete? | Self-scaling? | Bounded? |
|---|---|---|---|---|---|
| Control+Wittgenstein | "What does term X mean in this deliberation?" | ✅ | ✅ | ✅ (max 5) | ✅ |
| Conservator+Aurelius | "Reversible / partial / irreversible?" | ✅ | ✅ | ✅ | ✅ |
| Conservator+Aurelius | "Is this real risk or status quo bias?" | ✅ | ⚠️ | ✅ | ✅ |
| Control+Aurelius | "Can user decide this directly?" | ✅ | ✅ | ✅ | ✅ |
| Conservator+Confucius | "Do we have >= 3 matching precedents?" | ✅ | ✅ | ✅ (3+ threshold) | ✅ |
| Refiner | "Does removing this lose actionable information?" | ✅ | ✅ | ✅ (token threshold) | ✅ (add-back rule) |

- [ ] **Step 7.2: Check for 2+ ⚠️ in any row**

Current assessment: Conservator+Aurelius has 1 ⚠️ on bias_check discreteness. This is 1 ⚠️, below the 2 ⚠️ threshold — acceptable. No prompt rewrites required.

If any voice has 2+ ⚠️ after your own audit: rewrite that prompt's internal question to make it operational, discrete, self-scaling, and bounded. Rerun the check.

---

## Task 8: Create `scripts/precedent_search.py`

**Files:** Create `scripts/precedent_search.py`

- [ ] **Step 8.1: Write the file**

```python
"""Search past deliberations for precedents using keyword overlap (TF-IDF light).

Stdlib-only. No external dependencies.

Used by conservator_confucius voice: the orchestrator calls this script and injects
the results into the voice's input (Optiunea A — pre-processing injection).

CLI:
    python scripts/precedent_search.py --query "stop loss trading"
    python scripts/precedent_search.py --query "refactor auth" --limit 3
    python scripts/precedent_search.py --query "car wash decision" --category trivial
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# === PHILOSOPHICAL VOICES ===


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenization, lowercased."""
    return text.lower().split()


def _overlap_score(query_terms: set[str], doc_text: str) -> float:
    """Jaccard-style overlap: |query ∩ doc| / |query|.

    Returns 0.0 if query is empty. Score is in [0.0, 1.0].
    """
    if not query_terms:
        return 0.0
    doc_terms = set(_tokenize(doc_text))
    return len(query_terms & doc_terms) / len(query_terms)


def _load_runs() -> list[dict]:
    runs_dir = _repo_root() / "runs"
    result = []
    for path in sorted(runs_dir.glob("*.json")):
        if path.parent.name == "senate":
            continue  # skip senate runs
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_filename"] = path.name
            result.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return result


def search(query: str, limit: int = 5, category: str | None = None) -> dict:
    """Search runs/ for past deliberations similar to `query`.

    Returns:
        {
          "query": str,
          "matches_found": int,
          "results": [
            {
              "run_id": str,
              "score": float,          # overlap score in [0.0, 1.0]
              "success_criterion": str,
              "chosen_approach": str | null,
              "outcome": str | null,   # "OK" | "BAD" | null
            },
            ...
          ]
        }
    """
    query_terms = set(_tokenize(query))
    runs = _load_runs()
    scored: list[tuple[float, dict]] = []

    for run in runs:
        if category and run.get("category") != category:
            continue
        sc = run.get("success_criterion", "")
        if not isinstance(sc, str):
            continue
        score = _overlap_score(query_terms, sc)
        if score > 0.0:
            scored.append((score, run))

    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:limit]

    results = []
    for score, run in top:
        results.append({
            "run_id": run["_filename"],
            "score": round(score, 3),
            "success_criterion": run.get("success_criterion", ""),
            "chosen_approach": run.get("chosen_approach"),
            "outcome": run.get("outcome"),
        })

    return {
        "query": query,
        "matches_found": len(top),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True, help="search query (success criterion text)")
    ap.add_argument("--limit", type=int, default=5, help="max results (default: 5)")
    ap.add_argument("--category", default=None, help="filter by run category field")
    args = ap.parse_args(argv)

    result = search(args.query, args.limit, args.category)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# === END PHILOSOPHICAL VOICES ===
```

- [ ] **Step 8.2: Run smoke test**

```bash
python scripts/precedent_search.py --query "test query no results expected"
```

Expected: JSON with `"matches_found": 0` and `"results": []` (or some results if runs/ has matching content).

```bash
python scripts/precedent_search.py --query "car wash" --limit 3
```

Expected: JSON output (may have 0 or more results depending on runs/).

---

## Task 9: Update `scripts/validate_report.py`

**Files:** Modify `scripts/validate_report.py`

Add per-voice optional field validators and `--strict-philosophical=<voice>` flag. All new code delimited with `# === PHILOSOPHICAL VOICES ===`.

- [ ] **Step 9.1: Add optional field validators**

After the last existing function in validate_report.py (before `validate()`), insert:

```python
# === PHILOSOPHICAL VOICES ===
_PHILOSOPHICAL_VOICES = frozenset({
    "wittgenstein", "aurelius-conservator", "aurelius-control", "confucius"
})


def _validate_philosophical_wittgenstein(voice_output: dict) -> list[str]:
    problems = []
    glossary = voice_output.get("glossary")
    if not isinstance(glossary, dict):
        problems.append("strict-philosophical=wittgenstein: glossary must be a dict")
    elif len(glossary) > 5:
        problems.append(f"strict-philosophical=wittgenstein: glossary has {len(glossary)} terms, max is 5")
    ha = voice_output.get("hidden_assumptions")
    if not isinstance(ha, list):
        problems.append("strict-philosophical=wittgenstein: hidden_assumptions must be a list")
    return problems


def _validate_philosophical_aurelius_conservator(voice_output: dict) -> list[str]:
    problems = []
    for score in voice_output.get("scores", []):
        rr = score.get("regression_risk")
        if rr is None:
            problems.append(f"strict-philosophical=aurelius-conservator: candidate '{score.get('id')}' missing regression_risk")
            continue
        if not isinstance(rr, dict):
            problems.append(f"strict-philosophical=aurelius-conservator: regression_risk must be object, got {type(rr).__name__}")
            continue
        for field in ("reversibility", "magnitude"):
            if field not in rr:
                problems.append(f"strict-philosophical=aurelius-conservator: regression_risk missing '{field}'")
        meta = score.get("meta_recommendation")
        if meta is not None and meta not in ("scale_down", "scale_up"):
            problems.append(f"strict-philosophical=aurelius-conservator: meta_recommendation must be scale_down|scale_up|null, got {meta!r}")
    return problems


def _validate_philosophical_aurelius_control(voice_output: dict) -> list[str]:
    problems = []
    for field in ("in_control", "out_of_control"):
        val = voice_output.get(field)
        if not isinstance(val, list):
            problems.append(f"strict-philosophical=aurelius-control: '{field}' must be a list")
    # uncertain_control is optional
    wasted = voice_output.get("wasted_deliberation")
    if wasted is not None and not isinstance(wasted, str):
        problems.append("strict-philosophical=aurelius-control: wasted_deliberation must be string or null")
    return problems


def _validate_philosophical_confucius(voice_output: dict) -> list[str]:
    problems = []
    ps = voice_output.get("precedent_search")
    if not isinstance(ps, dict):
        problems.append("strict-philosophical=confucius: precedent_search must be a dict")
    else:
        for field in ("matches_found", "fallback_to_abstract"):
            if field not in ps:
                problems.append(f"strict-philosophical=confucius: precedent_search missing '{field}'")
    # Warn about experimental status
    if ps and ps.get("fallback_to_abstract") is False and ps.get("matches_found", 0) < 3:
        problems.append(
            "strict-philosophical=confucius: [WARNING] fallback_to_abstract=false but matches_found < 3 — "
            "EXPERIMENTAL voice with limited precedent data"
        )
    return problems


_PHILOSOPHICAL_VALIDATORS = {
    "wittgenstein": _validate_philosophical_wittgenstein,
    "aurelius-conservator": _validate_philosophical_aurelius_conservator,
    "aurelius-control": _validate_philosophical_aurelius_control,
    "confucius": _validate_philosophical_confucius,
}
# === END PHILOSOPHICAL VOICES ===
```

- [ ] **Step 9.2: Add `--strict-philosophical` CLI flag**

In `main()`, after the existing `--input` argument (and after any RUND2 flags if already present):

```python
    # === PHILOSOPHICAL VOICES ===
    ap.add_argument(
        "--strict-philosophical",
        choices=sorted(_PHILOSOPHICAL_VOICES),
        default=None,
        metavar="VOICE",
        help=f"require philosophical voice fields; one of: {', '.join(sorted(_PHILOSOPHICAL_VOICES))}",
    )
    # === END PHILOSOPHICAL VOICES ===
```

- [ ] **Step 9.3: Call strict validation in main()**

After the existing strict-rund2 block (or after `problems = validate(report)` if RUND2 block not yet merged):

```python
    # === PHILOSOPHICAL VOICES ===
    if args.strict_philosophical:
        validator = _PHILOSOPHICAL_VALIDATORS.get(args.strict_philosophical)
        if validator:
            # look for voice output in report structure
            voice_output = report.get("voice_outputs", {}).get(args.strict_philosophical, report)
            problems.extend(validator(voice_output))
    # === END PHILOSOPHICAL VOICES ===
```

- [ ] **Step 9.4: Verify baseline unchanged**

```bash
echo '{"success_criterion":"test","verification":"test","chosen_approach":"A","telemetry":{"mode":"sequential"}}' | python scripts/validate_report.py
```
Expected: exit 0.

---

## Task 10: Write `scripts/test_philosophical_voices.py`

**Files:** Create `scripts/test_philosophical_voices.py`

- [ ] **Step 10.1: Write tests**

```python
"""Tests for philosophical voice variants.

Run:
    python scripts/test_philosophical_voices.py
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import validate_report
from precedent_search import search, _overlap_score, _tokenize


class TestBackwardCompat(unittest.TestCase):
    """Old runs must still pass validation."""

    def test_old_run_passes_default(self):
        report = {
            "success_criterion": "fix the bug",
            "verification": "tests pass",
            "chosen_approach": "inline_fix",
            "telemetry": {"mode": "sequential"},
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])

    def test_old_run_no_philosophical_fields_passes(self):
        report = {
            "success_criterion": "fix the bug",
            "verification": "tests pass",
            "chosen_approach": "inline_fix",
            "telemetry": {"mode": "parallel", "voices": {"generator": {}, "control": {}, "conservator": {}}},
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])


class TestWittgensteinValidator(unittest.TestCase):

    def test_valid_output_passes(self):
        output = {
            "glossary": {"term": "definition"},
            "hidden_assumptions": [{"assumption": "x", "if_false_then": "y"}],
        }
        problems = validate_report._validate_philosophical_wittgenstein(output)
        self.assertEqual(problems, [])

    def test_missing_glossary_fails(self):
        output = {"hidden_assumptions": []}
        problems = validate_report._validate_philosophical_wittgenstein(output)
        self.assertTrue(any("glossary" in p for p in problems))

    def test_glossary_over_5_terms_fails(self):
        output = {
            "glossary": {f"term{i}": f"def{i}" for i in range(6)},
            "hidden_assumptions": [],
        }
        problems = validate_report._validate_philosophical_wittgenstein(output)
        self.assertTrue(any("5" in p for p in problems))

    def test_missing_hidden_assumptions_fails(self):
        output = {"glossary": {"term": "def"}}
        problems = validate_report._validate_philosophical_wittgenstein(output)
        self.assertTrue(any("hidden_assumptions" in p for p in problems))


class TestAureliusConservatorValidator(unittest.TestCase):

    def test_valid_output_passes(self):
        output = {
            "scores": [{
                "id": "A",
                "regression_risk": {
                    "reversibility": "complete",
                    "magnitude": "trivial",
                    "net_concern": 0.05,
                },
                "meta_recommendation": None,
            }]
        }
        problems = validate_report._validate_philosophical_aurelius_conservator(output)
        self.assertEqual(problems, [])

    def test_missing_regression_risk_object_fails(self):
        output = {"scores": [{"id": "A"}]}
        problems = validate_report._validate_philosophical_aurelius_conservator(output)
        self.assertTrue(any("regression_risk" in p for p in problems))

    def test_missing_magnitude_fails(self):
        output = {"scores": [{"id": "A", "regression_risk": {"reversibility": "complete"}}]}
        problems = validate_report._validate_philosophical_aurelius_conservator(output)
        self.assertTrue(any("magnitude" in p for p in problems))

    def test_invalid_meta_recommendation_fails(self):
        output = {"scores": [{"id": "A", "regression_risk": {"reversibility": "complete", "magnitude": "trivial"}, "meta_recommendation": "invalid"}]}
        problems = validate_report._validate_philosophical_aurelius_conservator(output)
        self.assertTrue(any("meta_recommendation" in p for p in problems))

    def test_null_meta_recommendation_passes(self):
        output = {"scores": [{"id": "A", "regression_risk": {"reversibility": "complete", "magnitude": "trivial"}, "meta_recommendation": None}]}
        problems = validate_report._validate_philosophical_aurelius_conservator(output)
        self.assertEqual(problems, [])


class TestAureliusControlValidator(unittest.TestCase):

    def test_valid_output_passes(self):
        output = {
            "in_control": ["choice A"],
            "out_of_control": [],
            "uncertain_control": ["negotiation"],
            "wasted_deliberation": None,
        }
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])

    def test_missing_in_control_fails(self):
        output = {"out_of_control": []}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertTrue(any("in_control" in p for p in problems))

    def test_uncertain_control_optional(self):
        output = {"in_control": [], "out_of_control": []}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])

    def test_wasted_deliberation_accepts_string(self):
        output = {"in_control": [], "out_of_control": [], "wasted_deliberation": "option C is out of control"}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertEqual(problems, [])

    def test_wasted_deliberation_rejects_non_string(self):
        output = {"in_control": [], "out_of_control": [], "wasted_deliberation": 42}
        problems = validate_report._validate_philosophical_aurelius_control(output)
        self.assertTrue(any("wasted_deliberation" in p for p in problems))


class TestConfuciusValidator(unittest.TestCase):

    def test_valid_fallback_output_passes(self):
        output = {
            "precedent_search": {"matches_found": 0, "fallback_to_abstract": True},
            "ancestor_guidance": None,
        }
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertEqual(problems, [])

    def test_missing_precedent_search_fails(self):
        output = {"ancestor_guidance": None}
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("precedent_search" in p for p in problems))

    def test_missing_matches_found_fails(self):
        output = {"precedent_search": {"fallback_to_abstract": True}}
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("matches_found" in p for p in problems))

    def test_experimental_warning_on_low_matches(self):
        output = {
            "precedent_search": {"matches_found": 1, "fallback_to_abstract": False},
        }
        problems = validate_report._validate_philosophical_confucius(output)
        self.assertTrue(any("EXPERIMENTAL" in p or "limited" in p.lower() for p in problems))


class TestPrecedentSearch(unittest.TestCase):

    def test_overlap_score_empty_query(self):
        score = _overlap_score(set(), "any text here")
        self.assertEqual(score, 0.0)

    def test_overlap_score_full_match(self):
        score = _overlap_score({"stop", "loss"}, "stop loss strategy trading")
        self.assertEqual(score, 1.0)

    def test_overlap_score_partial_match(self):
        score = _overlap_score({"stop", "loss", "limit"}, "stop loss strategy")
        self.assertAlmostEqual(score, 2/3, places=5)

    def test_overlap_score_no_match(self):
        score = _overlap_score({"stop", "loss"}, "hello world")
        self.assertEqual(score, 0.0)

    def test_tokenize_lowercases(self):
        tokens = _tokenize("Stop Loss STRATEGY")
        self.assertIn("stop", tokens)
        self.assertIn("loss", tokens)
        self.assertIn("strategy", tokens)

    def test_search_returns_zero_results_on_no_match(self):
        result = search("xyzzy_not_in_any_run_ever_hopefully_12345")
        self.assertEqual(result["matches_found"], 0)
        self.assertEqual(result["results"], [])

    def test_search_returns_structure(self):
        result = search("test query")
        self.assertIn("query", result)
        self.assertIn("matches_found", result)
        self.assertIn("results", result)

    def test_search_limit_respected(self):
        # Even with broad query, limit=2 returns at most 2
        result = search("the a is of", limit=2)
        self.assertLessEqual(len(result["results"]), 2)


class TestCrossVoice(unittest.TestCase):

    def test_all_voices_active_report_passes_default(self):
        """A report with all philosophical voice outputs passes default validation."""
        report = {
            "success_criterion": "validate all voices",
            "verification": "test passes",
            "chosen_approach": "A",
            "telemetry": {"mode": "parallel", "voices": {}},
            "voice_outputs": {
                "wittgenstein": {
                    "glossary": {"term": "def"},
                    "hidden_assumptions": [],
                },
                "aurelius-conservator": {
                    "scores": [{"id": "A", "regression_risk": {"reversibility": "complete", "magnitude": "trivial"}, "meta_recommendation": None}],
                },
                "aurelius-control": {
                    "in_control": [],
                    "out_of_control": [],
                },
                "confucius": {
                    "precedent_search": {"matches_found": 0, "fallback_to_abstract": True},
                    "ancestor_guidance": None,
                },
            },
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])

    def test_wittgenstein_only_active_does_not_require_aurelius(self):
        report = {
            "success_criterion": "test",
            "verification": "test",
            "chosen_approach": "A",
            "telemetry": {"mode": "sequential"},
            "voice_outputs": {
                "wittgenstein": {"glossary": {"t": "d"}, "hidden_assumptions": []},
            },
        }
        problems = validate_report.validate(report)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 10.2: Run tests**

```bash
python scripts/test_philosophical_voices.py
```

Expected: all tests pass. Fix any failures before continuing.

---

## Task 11: Update `SKILL.md`

**Files:** Modify `SKILL.md`

Add "Voice variants" section with Stable/EXPERIMENTAL table. Use `<!-- === PHILOSOPHICAL VOICES === -->` delimiters.

- [ ] **Step 11.1: Add Voice variants section**

At the end of SKILL.md (after any RUND2 sections if present, before end of file), insert:

```markdown
<!-- === PHILOSOPHICAL VOICES === -->
## Voice variants

Philosophical lenses extend the three baseline voices (Generator, Control, Conservator) without replacing them. Each variant is a separate prompt file that adds a specialized perspective.

### Baseline voices (unchanged)

- **Generator** — divergent thinking, candidate generation (`prompts/generator.md`)
- **Control** — technical validation (`prompts/control.md`)
- **Conservator** — risk assessment (`prompts/conservator.md`)

### Philosophical variants

> **Empirical caveat:** These variants were validated on limited data (P3 car wash, Run 3). Phase 13 post-merge validation extends coverage to 10-15 deliberations.

| Variant | Prompt file | Status | When to use |
|---|---|---|---|
| Control + Wittgenstein | `prompts/control_wittgenstein.md` | Stable | Questions with ambiguous terms, semantic traps, potential false consensus between voices |
| Conservator + Aurelius | `prompts/conservator_aurelius.md` | Stable | Questions where reversibility and magnitude decomposition add clarity over scalar risk |
| Control + Aurelius | `prompts/control_aurelius.md` | Stable (niche) | Questions with hypothetical elements, decisions depending on external factors |
| Conservator + Confucius | `prompts/conservator_confucius.md` | **EXPERIMENTAL** [blocked until runs/ >= 10] | Recurring decision types only — requires precedents in runs/ |

### Refinement layer

| Variant | Prompt file | Status | When to use |
|---|---|---|---|
| Refiner + Deletion | `prompts/refiner_deletion.md` | Not yet validated | Post-Aggregator; when output > 200 tokens or `--refine` flag; skip if scale_down already active |

### Combined mode (advanced)

Running Control+Wittgenstein together with Conservator+Aurelius provides semantic precision (are we deliberating on the right question?) AND risk decomposition (how reversible/large is the outcome?). Zero extra cost — same voice count.

### How to use a variant

Replace the standard voice invocation with the variant prompt. Example:
- Standard: "Use `prompts/control.md`..."
- Variant: "Use `prompts/control_wittgenstein.md`..."

The variant output JSON is a superset of the standard voice output — backward compatible with `validate_report.py` default mode. Use `--strict-philosophical=<voice>` flag for strict validation.

### Conservator + Confucius — precedent injection

When using Confucius variant, the orchestrator must inject precedent results:

```bash
python scripts/precedent_search.py --query "<success_criterion text>" --limit 5
```

Inject the JSON output as `precedent_search_results` in the voice's input. If `matches_found = 0` → voice falls back to standard Conservator behavior automatically.

### Empirical validation status (post-merge)

Track after 10+ real deliberations:
- **Q1 (Wittgenstein):** Catches semantic traps in > 30% of runs?
- **Q2 (Conservator+Aurelius):** `scale_down` activations correct?
- **Q3 (Control+Aurelius):** `wasted_deliberation` flags real waste?
- **Q4 (Confucius):** With >= 3 precedents, generates useful guidance?

If Q3 negative → Control+Aurelius deprecated. If Q4 negative → Confucius deprecated. Results in `experiments/run4-empirical-validation.html`.
<!-- === END PHILOSOPHICAL VOICES === -->
```

- [ ] **Step 11.2: Verify SKILL.md**

```bash
python -c "
with open('SKILL.md', encoding='utf-8') as f:
    c = f.read()
assert 'Voice variants' in c
assert 'EXPERIMENTAL' in c
assert 'control_wittgenstein' in c
assert 'conservator_aurelius' in c
assert 'refiner_deletion' in c
print('SKILL.md OK')
"
```
Expected: `SKILL.md OK`

---

## Task 12: `/consilium senate` self-validation

**Files:** none (produces gitignored JSON in runs/senate/)

- [ ] **Step 12.1: Run senate validation**

Invoke the consilium skill in senate mode with the proposal:

```
/consilium senate "Am adăugat 5 variante filozofice de voce în Consilium: Control+Wittgenstein (verificare semantică), Conservator+Aurelius (reversibilitate×magnitudine), Control+Aurelius (zonă de control), Conservator+Confucius EXPERIMENTAL (precedente), Refiner+Deletion (post-Aggregator). Plus precedent_search.py, validate_report.py extins cu --strict-philosophical, și documentație în SKILL.md. E gata pentru merge?"
```

- [ ] **Step 12.2: Handle senate verdict**

- If `verdict = GO` → proceed to Task 13.
- If `verdict = MODIFY` → apply each `modify_request` item:
  1. Identify which file each request targets
  2. Make the requested change
  3. Rerun `python scripts/test_philosophical_voices.py` to verify nothing broke
  After all changes applied → proceed to Task 13.
- If `verdict = STOP` → do NOT commit. Report to user with full senate output before proceeding.

---

## Task 13: Single commit

**Files:** all created/modified files above

- [ ] **Step 13.1: Verify git status — expected files only**

```bash
git status
```

Expected tracked changes (only these):
- `prompts/control_wittgenstein.md` (NEW)
- `prompts/conservator_aurelius.md` (NEW)
- `prompts/control_aurelius.md` (NEW)
- `prompts/conservator_confucius.md` (NEW)
- `prompts/refiner_deletion.md` (NEW)
- `scripts/precedent_search.py` (NEW)
- `scripts/validate_report.py` (MOD)
- `scripts/test_philosophical_voices.py` (NEW)
- `SKILL.md` (MOD)

NO changes to: `prompts/conservator.md`, `prompts/generator.md`, `prompts/control.md` (these are modified by RUND2 branch, not this one).

- [ ] **Step 13.2: Run full test suite**

```bash
python scripts/test_philosophical_voices.py
python scripts/validate_report.py < runs/$(ls runs/*.json 2>/dev/null | sort | tail -1) 2>/dev/null || echo "no runs yet — skipping"
```

Expected: all tests pass.

- [ ] **Step 13.3: Stage and commit**

```bash
git add prompts/control_wittgenstein.md prompts/conservator_aurelius.md
git add prompts/control_aurelius.md prompts/conservator_confucius.md
git add prompts/refiner_deletion.md
git add scripts/precedent_search.py
git add scripts/validate_report.py scripts/test_philosophical_voices.py
git add SKILL.md
git commit -m "$(cat <<'EOF'
feat(voices): add 5 philosophical voice variants

Deliberation layer (new variant files, no changes to core prompts):
- Control + Wittgenstein: semantic verification (glossary max 5 terms, hidden_assumptions)
- Conservator + Aurelius: reversibility×magnitude decomposition + meta_recommendation
- Control + Aurelius: zone-of-control filter (in/out/uncertain_control, wasted_deliberation)
- Conservator + Confucius: precedent consultation [EXPERIMENTAL, blocked until runs/ >= 10]

Refinement layer (post-Aggregator, new category):
- Refiner + Deletion: Musk-FAST deletion discipline, add-back 10% rule

Infrastructure:
- precedent_search.py: TF-IDF keyword overlap over runs/ (stdlib-only)
- validate_report.py: _validate_regression_risk helper + --strict-philosophical=<voice> flags
- test_philosophical_voices.py: 25+ tests (backward compat + per-voice + cross-voice)

Phase 5c question audit: all 5 voices pass 4 criteria (Operational/Discrete/Self-scaling/Bounded).
Confucius marked EXPERIMENTAL until runs/ >= 10 entries.
Refiner not yet validated — Phase 13 empirical validation pending.

Conflict files for RUND2 rebase: validate_report.py, SKILL.md (sections delimited).
Merge order: RUND2 first, this branch rebases on updated main.

Justification: experiments/New phase senat/todos/TODO-philosophical-voice-variants.md
Design: docs/superpowers/specs/2026-05-16-consilium-experimental-implementation-design.md
EOF
)"
```

- [ ] **Step 13.4: Verify commit**

```bash
git log --oneline -3
git show --stat HEAD
```

Expected: one commit on `feat/philosophical-voice-variants` with the files listed above.

- [ ] **Step 13.5: Push**

```bash
git push -u origin feat/philosophical-voice-variants
```

- [ ] **Step 13.6: Return to main**

```bash
git checkout main
```

Report: branch `feat/philosophical-voice-variants` pushed. User opens PR manually from GitHub UI. **Merge RUND2 first** — then rebase this branch and resolve conflicts on `validate_report.py` + `SKILL.md` + `aggregator.py` (Confucius injection).
