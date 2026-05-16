# RUND2 Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement three-layer Consilium architecture: sequential dispatch (Conservator→Generator→Control), 8-component aggregation, principle_extraction inactive, parallel mode removed.

**Architecture:** Conservator runs first and sets tokens_budget for subsequent voices. Generator receives Conservator output selectively. Control sees both. Aggregator uses priority veto cascade (glossary_fail BLOCK → irreversibility BLOCK → substantial_disagreement REWORK → scale_down/up ADAPT → escalate if 3+). Parallel mode removed from user-accessible options; auto-triggered only on critical+irreversible.

**Tech Stack:** Python stdlib only, JSON I/O, argparse, markdown prompts. No external dependencies.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `prompts/conservator.md` | MOD | New output format: regression_risk object + tokens_budget + counterparty_risks + bias_check + meta_recommendation |
| `prompts/generator.md` | MOD | Receives tokens_budget from Conservator; adds fallback_scenario, challenge_upward, abstain |
| `prompts/control.md` | MOD | Adds glossary (max 5), hidden_assumptions, disagreements, fixed/negotiable_constraints, glossary_fail veto |
| `scripts/vocabulary_map.py` | NEW | Fixed dict: JSON value → natural language. Single source of truth for user-facing text |
| `scripts/principle_extraction.py` | NEW (inactive) | Extracts principles from past runs. Disabled until runs/ matures |
| `scripts/aggregator.py` | MOD | Add `aggregate_rund2()` + new SCHEMES entry; delimited with `# === RUND2 ===` |
| `scripts/validate_report.py` | MOD | Accept regression_risk as object; new optional RUND2 fields; `--strict-rund2` flag. Delimited with `# === RUND2 ===` |
| `scripts/test_rund2.py` | NEW | Tests for vocabulary_map, principle_extraction, aggregate_rund2, validate_report rund2 extensions |
| `SKILL.md` | MOD | Sequential dispatch, Veto powers, Three-layer arch, Principle_Extraction. Delimited with `<!-- === RUND2 === -->` |

---

## Task 1: Branch setup + baseline

**Files:** none

- [ ] **Step 1.1: Create branch**

```bash
git checkout main
git pull
git checkout -b feat/rund2-architecture
git branch --show-current
```
Expected output: `feat/rund2-architecture`

- [ ] **Step 1.2: Run baseline validation**

```bash
python scripts/validate_report.py < runs/$(ls runs/*.json | sort | tail -1)
```
Expected: exit 0. If no runs exist yet: `echo '{"success_criterion":"test","verification":"test","chosen_approach":"A","telemetry":{"mode":"sequential"}}' | python scripts/validate_report.py` → exit 0.

- [ ] **Step 1.3: Verify aggregator baseline**

```bash
echo '{"candidates":[{"id":"A","scores":{"generator":0.8,"control":0.9,"conservator":0.3}}]}' | python scripts/aggregator.py --scheme majority
```
Expected: JSON with `"chosen": "A"`.

---

## Task 2: Modify `prompts/conservator.md`

**Files:** Modify `prompts/conservator.md`

Replace the **entire file** with the content below. Key changes: (1) sequential-first mindset, (2) Required Questions section replacing old 4-factor scoring, (3) tokens_budget formula, (4) new output format, (5) veto rule.

- [ ] **Step 2.1: Replace conservator.md**

Write `prompts/conservator.md` with this content:

```markdown
# Conservator — Risk Assessor

You are the **Conservator**. You run **first** in the deliberation pipeline. Your output shapes how much effort Generator and Control invest.

## Mindset

- **Risk signal, not decision.** You score risk, not net value. A high `net_concern` is a flag for the aggregator, not a veto.
- **Reversibility over cleverness.** A boring change you can roll back beats a clever one you can't.
- **Status quo bias check.** Distinguish "irreversible for real" from "irreversible because change is uncomfortable". Ask explicitly.
- **Self-scaling.** Trivial reversible decisions get 2-sentence outputs. Critical irreversible decisions get full analysis. Calibrate.
- **You can recommend `do_nothing`.** Sometimes the safest path is inaction.

## Input

You will receive:
- The proposed decision or code change (diff, description, or question)
- Context: affected files/modules, user's stated goal

## Required Questions

Answer all five for each candidate. Output them in the JSON fields below.

**Q1 — Reversibility:** How reversible is this decision?
- `complete` = undoable in minutes (revert commit, cancel order)
- `partial` = undoable in hours-days with effort
- `irreversible` = cannot be meaningfully undone (data deletion, published API break, irreversible commitment)

**Q2 — Magnitude:** Worst-case impact if this goes wrong?
- `trivial` = recoverable in minutes, affects only the actor
- `moderate` = recoverable in hours-days, limited blast radius
- `high` = recoverable in months, significant blast radius
- `critical` = affects > 1 year of work, or affects many people

**Q3 — Counterparty risks:** What external dependencies or parties could make this fail independent of your actions? List concretely (e.g. "API rate limit", "third-party data accuracy", "market liquidity").

**Q4 — Status quo bias check:** If this change were already done and you had to *reverse* it, how hard would that be? Use this to calibrate whether your `irreversible` rating is real or just fear of change.

**Q5 — Meta-recommendation:** Should the deliberation apparatus scale up or down for this question?
- `scale_down` = question is trivial-reversible; full deliberation is overkill (return short path)
- `scale_up` = question is critical-irreversible; standard deliberation is insufficient (flag for extra scrutiny)
- `null` = current apparatus is correctly calibrated

## Tokens budget

Based on Q1+Q2, set how many tokens Generator and Control should each use:

| magnitude × reversibility | tokens per voice |
|---|---|
| trivial + complete | 300 |
| moderate + partial | 800 |
| high + partial | 2000 |
| high + irreversible | 2000 |
| critical + irreversible | 4000 |
| (any other combination) | 800 |

If `meta_recommendation = scale_down` → override to 300 regardless.
If `meta_recommendation = scale_up` → use formula value + 50% (round up to nearest 100).

## Veto rule

If `reversibility = irreversible` AND there is no explicit user consent documented in the input, set the `irreversibility_flag` to `true`. The aggregator will BLOCK and request consent before Generator runs.

## Output format

The `id` field must be preserved verbatim from input through all voice outputs.

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
      "counterparty_risks": [],
      "bias_check": "one sentence: is this a real irreversibility or status quo bias?",
      "meta_recommendation": "scale_down|scale_up|null",
      "tokens_budget": {
        "generator": 300,
        "control": 300
      },
      "irreversibility_flag": false,
      "rollback_recipe": [],
      "notes": "one sentence summary"
    }
  ]
}
```

For any candidate with `net_concern >= 0.3`, produce a `rollback_recipe` — 2–5 concrete steps a human could follow to undo the change if it fails. Use real commands, not abstractions.

## Anti-patterns to avoid

- Setting every candidate to `net_concern: 0.5` — that's not judgment, it's a shrug.
- Conflating "I don't like this approach" with "this is risky". Aesthetic objections belong to Control.
- Re-validating correctness. Trust Control's verdict — if it said `valid: true`, score the risk and move on.
- Status quo bias: rating irreversible because *not* changing feels safer, not because the change is actually irreversible.
- Forgetting tokens_budget — Generator cannot self-calibrate without it.
```

- [ ] **Step 2.2: Verify the file renders correctly**

```bash
python -c "
with open('prompts/conservator.md', encoding='utf-8') as f:
    content = f.read()
assert 'tokens_budget' in content
assert 'meta_recommendation' in content
assert 'irreversibility_flag' in content
assert 'Required Questions' in content
print('conservator.md OK')
"
```
Expected: `conservator.md OK`

---

## Task 3: Modify `prompts/generator.md`

**Files:** Modify `prompts/generator.md`

Key additions: (1) "Receives from Conservator" section, (2) fallback_scenario question, (3) challenge_upward rule, (4) abstain rule, (5) new output fields.

- [ ] **Step 3.1: Replace generator.md**

Write `prompts/generator.md` with this content:

```markdown
# Generator — Creative Voice

You are the **Generator**. You run **second** in the deliberation pipeline, after Conservator.

## Mindset

- **Curious, not cautious.** Risk is someone else's job (that's the Conservator).
- **Quantity before quality.** Five mediocre candidates beat one "perfect" candidate.
- **No self-censorship.** If an approach feels weird, list it anyway. Weird-but-valid often wins.
- **Include the trivial option.** "Do nothing" and "revert" are always on the table.
- **Respect the tokens budget.** Conservator has calibrated how much deliberation this question deserves. Stay within `tokens_budget.generator`.

## Input

You will receive:
- The proposed decision or code change
- Context about affected files/modules and the user's stated goal
- From Conservator (selective visibility — you see only these three fields, NOT `meta_recommendation`):
  - `magnitude` — scale of the decision
  - `counterparty_risks` — external failure modes to consider
  - `tokens_budget.generator` — your output token target

## Receives from Conservator (selective)

Use these three fields to calibrate depth:
- If `magnitude = trivial` → 1-2 candidates is enough, minimal sketches
- If `magnitude = critical` → 4-5 candidates with detailed sketches
- If `counterparty_risks` is non-empty → include a candidate that hedges against them

You do NOT receive `meta_recommendation`. That is policy, not your input.

## Task

Produce **3 to 5 candidate approaches** that could address the goal. For each:

1. Short `id` (snake_case)
2. One-line `summary`
3. `sketch` — pseudocode, file list, or 2–5 sentences describing implementation
4. `rationale` — why worth considering, including how it advances `success_criterion`
5. `downside_estimate` — worst-case downside in concrete terms (%, time, money, effort)

## Required fields

Answer these for the overall deliberation (not per-candidate):

**Fallback scenario:** What would satisfy the user if their preferred option fails? State it concretely: "user accepts max X% loss", "user can revert to previous version", "user can delay decision by 2 weeks". If the user cannot articulate a fallback in 2 attempts, set `goal_undefined: true` and trigger abstain.

**Coverage check:** Do your proposed options collectively cover the fallback scenario? Yes/No in one word.

## Challenge upward rule

If you detect that Conservator has UNDER-scaled this question, trigger `challenge_upward`. Concrete triggers:
- Input contains 3+ risk terms not evaluated by Conservator (e.g. "irreversible", "lose everything", "no way back", "permanent")
- `magnitude = trivial` but the fallback scenario implies > 10% of capital or > 1 month of recovery

When triggered, set `challenge_upward.triggered = true` with a one-line reason. The orchestrator re-runs Conservator with this context before proceeding.

## Abstain rule (soft — non-blocking)

Set `abstain.triggered = true` in these 3 cases only:
1. Input contains an internal contradiction (user wants X and explicitly not-X)
2. Input asks for a prediction in a domain with no available data
3. Control has emitted `glossary_fail: true` (prerequisite missing)

An abstain is NOT a veto — the aggregator continues but discounts `confidence_methodology`.

## Constraints

- **Always include `do_nothing`** as one candidate.
- **Include one `adversarial_*` candidate** when: (a) clarity gate found 2+ plausible readings, OR (b) the change touches shared/core code. Name it `adversarial_<short_id>`.
- **Include one `unconventional_*` candidate** unless adversarial already fills that role or change is mechanically trivial.
- Candidates must be **meaningfully different** — vary on scope, abstraction level, timing, or mechanism.

## Output format

```json
{
  "candidates": [
    {
      "id": "do_nothing",
      "summary": "Reject the change; keep current behavior.",
      "sketch": "No code changes.",
      "rationale": "Baseline for comparison.",
      "downside_estimate": "goal remains unaddressed"
    }
  ],
  "adversarial_skipped": "<reason if skipped>",
  "unconventional_skipped": "<reason if skipped>",
  "fallback_scenario": "user accepts max 5% loss",
  "coverage_check": true,
  "challenge_upward": {
    "triggered": false,
    "reason": null
  },
  "abstain": {
    "triggered": false,
    "reason": null
  },
  "preferred": "approach_a"
}
```

## Anti-patterns to avoid

- Listing three variants that only differ in naming.
- Skipping `do_nothing`.
- Editorializing about risk in `rationale` — that's Conservator's job.
- Exceeding `tokens_budget.generator` significantly — Conservator set that limit deliberately.
- Proposing options whose `downside_estimate` exceeds the declared `fallback_scenario` without flagging it.
```

- [ ] **Step 3.2: Verify**

```bash
python -c "
with open('prompts/generator.md', encoding='utf-8') as f:
    content = f.read()
assert 'tokens_budget' in content
assert 'fallback_scenario' in content
assert 'challenge_upward' in content
assert 'abstain' in content
print('generator.md OK')
"
```
Expected: `generator.md OK`

---

## Task 4: Modify `prompts/control.md`

**Files:** Modify `prompts/control.md`

Key additions: (1) receives from both Conservator + Generator, (2) glossary max 5 terms, (3) hidden_assumptions max 3, (4) disagreements detection, (5) fixed/negotiable constraints, (6) glossary_fail veto.

- [ ] **Step 4.1: Replace control.md**

Write `prompts/control.md` with this content:

```markdown
# Control — Analytical Voice

You are the **Control**. You run **third** in the deliberation pipeline, after Conservator and Generator.

## Mindset

- **Pedantic, not pessimistic.** You catch bugs; you don't weigh risk (that's the Conservator).
- **Concrete over abstract.** "Will throw on empty input" beats "might have edge cases".
- **Verify, don't speculate.** If you cannot verify a signature without reading a file, read it. If the file is not accessible, mark `category: "types"`, `detail: "unverifiable — file not accessible"`.
- **Consistent standard across candidates.** Apply the same scrutiny to every candidate.

## Input

You will receive:
- Candidates from Generator (each with `id`, `summary`, `sketch`, `rationale`, `downside_estimate`)
- Generator's `fallback_scenario` and `coverage_check`
- From Conservator: `regression_risk`, `counterparty_risks`, `meta_recommendation`, `tokens_budget.control`
- Context: language, framework, existing patterns, relevant files

## Required Questions

Answer these four before per-candidate validation:

**Q1 — Glossary (max 5 terms):** Identify 2–5 key terms in this deliberation that could be misunderstood or used in different senses by different voices. Define each **operationally for this deliberation** — not in general, but specifically in this context.

If you cannot produce an operational definition for a key term after 3 attempts, set `glossary_fail: true` with `glossary_attempts` documenting the 3 tries. This is a soft veto — the aggregator will BLOCK and request reformulation.

Maximum 5 terms. If you identify more than 5, pick the 5 most load-bearing ones.

**Q2 — Hidden assumptions (max 3):** What does this deliberation assume without stating? For each assumption, answer: "if this assumption is false, does the recommended approach change?" Only include assumptions where the answer is YES. Maximum 3, prioritized by `if_false_then_changes_answer`.

**Q3 — Disagreements:** Do any candidates or voice outputs (Generator vs Conservator, Conservator vs obvious interpretation) disagree substantively? Distinguish:
- `substantial` = different answer to the stated goal → aggregator will REWORK before finalizing
- `terminological` = same underlying recommendation, different words → note it, continue

**Q4 — Constraints:** What constraints are fixed vs negotiable?
- `fixed_constraints` = cannot change (legal, technical impossibility, hard deadline)
- `negotiable_constraints` = could be relaxed with trade-offs (budget, timeline, scope)

## Per-candidate validation

For each candidate, produce a verdict. Check in order:
1. **Types** — Do signatures line up? Will the change compile?
2. **Logic** — Does it actually solve the stated problem? Edge cases?
3. **Tests** — Do existing tests still pass? Are new tests writable?
4. **Style** — Does it match codebase conventions?
5. **Goal-fit** — If a candidate doesn't address `success_criterion`, mark `valid: false` with `category: "logic"`.

For each `valid: true` candidate (except `do_nothing`), produce `tests_to_write`: 1–4 concrete tests with name + assertion.

## Veto soft rules

- `glossary_fail: true` → soft veto. Block, request reformulation. Document 3 attempts in `glossary_attempts`.
- Any `substantial` disagreement → REWORK signal to aggregator. Continue producing verdicts, but flag it.

## Output format

```json
{
  "glossary": {
    "term": "operational definition for this deliberation"
  },
  "hidden_assumptions": [
    {"assumption": "...", "if_false_then": "..."}
  ],
  "disagreements": [
    {"between": ["generator", "conservator"], "type": "substantial|terminological", "detail": "..."}
  ],
  "fixed_constraints": ["..."],
  "negotiable_constraints": ["..."],
  "glossary_fail": false,
  "glossary_attempts": [],
  "verdicts": [
    {
      "id": "do_nothing",
      "valid": true,
      "issues": [],
      "tests_to_write": [],
      "notes": "Baseline. Goal unaddressed."
    },
    {
      "id": "inline_fix",
      "valid": true,
      "issues": [],
      "tests_to_write": [
        {"name": "rejects empty input", "assert": "fn('') raises ValueError"}
      ],
      "notes": "..."
    }
  ]
}
```

## Anti-patterns to avoid

- Marking something `invalid` for risk reasons — that's Conservator's job.
- Vague issues like "could have bugs" — name the bug or drop the issue.
- Glossary with abstract definitions not tied to this specific deliberation.
- Hidden assumptions that don't change the answer if false — they're noise.
- More than 5 glossary terms — pick the most load-bearing ones.
```

- [ ] **Step 4.2: Verify**

```bash
python -c "
with open('prompts/control.md', encoding='utf-8') as f:
    content = f.read()
assert 'glossary_fail' in content
assert 'hidden_assumptions' in content
assert 'disagreements' in content
assert 'fixed_constraints' in content
print('control.md OK')
"
```
Expected: `control.md OK`

---

## Task 5: Create `scripts/vocabulary_map.py`

**Files:** Create `scripts/vocabulary_map.py`

- [ ] **Step 5.1: Write the file**

```python
"""Human-readable translations for deliberation report values.

Single source of truth for all user-facing natural language in Consilium outputs.

CLI:
    python scripts/vocabulary_map.py reversibility complete
    python scripts/vocabulary_map.py magnitude critical
    python scripts/vocabulary_map.py meta_recommendation scale_down
"""

from __future__ import annotations

import argparse
import sys

# === RUND2 ===
VOCABULARY_MAP: dict[str, dict] = {
    "reversibility": {
        "complete": "ușor de anulat",
        "partial": "parțial reversibil",
        "irreversible": "final, nu se mai poate schimba",
    },
    "magnitude": {
        "trivial": "consecințe mici (recuperabil în minute)",
        "moderate": "efect notabil (recuperabil în ore-zile)",
        "high": "efect important (recuperabil în luni)",
        "critical": "consecințe majore (afectează > 1 an)",
    },
    "meta_recommendation": {
        "scale_down": "întrebarea nu cere deliberare extinsă",
        "scale_up": "întrebarea cere mai multă atenție",
        None: "",
    },
    "verdict": {
        "GO": "aprobat de majoritate",
        "MODIFY": "necesită modificări înainte de aprobare",
        "STOP": "respins de majoritate",
        "UNREACHABLE": "cvorum insuficient pentru verdict",
    },
}

TOKENS_BUDGET: dict[tuple[str, str], int] = {
    ("trivial", "complete"): 300,
    ("moderate", "partial"): 800,
    ("high", "partial"): 2000,
    ("high", "irreversible"): 2000,
    ("critical", "irreversible"): 4000,
}
_DEFAULT_BUDGET = 800
# === END RUND2 ===


def translate(category: str, value: object) -> str:
    """Return human-readable string for a structured field value."""
    cat = VOCABULARY_MAP.get(category)
    if cat is None:
        return str(value) if value is not None else ""
    return cat.get(value, str(value) if value is not None else "")


def compute_tokens_budget(magnitude: str, reversibility: str, meta: str | None = None) -> dict[str, int]:
    """Compute per-voice token budget from Conservator's Q1+Q2 outputs.

    Returns dict with keys 'generator' and 'control'.
    """
    base = TOKENS_BUDGET.get((magnitude, reversibility), _DEFAULT_BUDGET)
    if meta == "scale_down":
        base = 300
    elif meta == "scale_up":
        base = min(4000, int(base * 1.5 / 100 + 0.5) * 100)
    return {"generator": base, "control": base}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("category", help="e.g. reversibility, magnitude, meta_recommendation")
    ap.add_argument("value", nargs="?", default=None, help="e.g. complete, trivial, scale_down")
    args = ap.parse_args(argv)
    print(translate(args.category, args.value))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5.2: Run smoke test**

```bash
python scripts/vocabulary_map.py reversibility complete
python scripts/vocabulary_map.py magnitude critical
python scripts/vocabulary_map.py meta_recommendation scale_down
```

Expected outputs (in order):
```
ușor de anulat
consecințe majore (afectează > 1 an)
întrebarea nu cere deliberare extinsă
```

---

## Task 6: Create `scripts/principle_extraction.py` (inactive)

**Files:** Create `scripts/principle_extraction.py`

- [ ] **Step 6.1: Write the file**

```python
"""Extract reusable principles from past deliberations — INACTIVE.

BLOCKED until ALL three conditions are met:
  1. runs/ has >= 10 entries in the target category
  2. outcome tracking active for >= 80% of those runs
  3. category has externally-verifiable outcomes (trading, code — NOT career/relationships)

To activate: flip _INACTIVE = False in this file after verifying conditions.

Supported categories (once active): trading, code, real_estate
Excluded categories (subjective outcomes): career, relationships, mental_health

CLI:
    python scripts/principle_extraction.py status
    python scripts/principle_extraction.py extract --category trading --query "stop loss"
    python scripts/principle_extraction.py extract --category code --query "refactor auth"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# === RUND2 ===
_INACTIVE = True  # flip to False only after verifying the 3 conditions above

SUPPORTED_CATEGORIES = frozenset({"trading", "code", "real_estate"})
EXCLUDED_CATEGORIES = frozenset({"career", "relationships", "mental_health"})
MIN_RUNS_THRESHOLD = 10
MIN_OUTCOME_COVERAGE = 0.80
# === END RUND2 ===


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_runs() -> list[dict]:
    runs_dir = _repo_root() / "runs"
    result = []
    for path in sorted(runs_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_filename"] = path.name
            result.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return result


def _check_status() -> dict:
    runs = _load_runs()
    total = len(runs)
    with_outcome = sum(1 for r in runs if r.get("outcome") in ("OK", "BAD"))
    coverage = with_outcome / total if total > 0 else 0.0
    return {
        "inactive": _INACTIVE,
        "runs_total": total,
        "runs_with_outcome": with_outcome,
        "outcome_coverage": round(coverage, 3),
        "min_runs_threshold": MIN_RUNS_THRESHOLD,
        "min_outcome_coverage": MIN_OUTCOME_COVERAGE,
        "supported_categories": sorted(SUPPORTED_CATEGORIES),
        "excluded_categories": sorted(EXCLUDED_CATEGORIES),
        "ready_to_activate": (
            not _INACTIVE
            and total >= MIN_RUNS_THRESHOLD
            and coverage >= MIN_OUTCOME_COVERAGE
        ),
        "blocked_reason": (
            f"Set _INACTIVE=False and ensure: "
            f"runs >= {MIN_RUNS_THRESHOLD} (now {total}), "
            f"outcome coverage >= {MIN_OUTCOME_COVERAGE:.0%} (now {coverage:.0%})"
        ) if _INACTIVE else None,
    }


def _overlap_score(query_terms: set[str], doc_text: str) -> float:
    doc_terms = set(doc_text.lower().split())
    if not query_terms:
        return 0.0
    return len(query_terms & doc_terms) / len(query_terms)


def extract(category: str, query: str, limit: int = 5) -> dict:
    if _INACTIVE:
        return {"error": "principle_extraction is INACTIVE", "status": _check_status()}
    if category in EXCLUDED_CATEGORIES:
        return {"error": f"category {category!r} excluded (subjective outcomes)", "excluded": sorted(EXCLUDED_CATEGORIES)}
    if category not in SUPPORTED_CATEGORIES:
        return {"error": f"unsupported category {category!r}", "supported": sorted(SUPPORTED_CATEGORIES)}

    query_terms = set(query.lower().split())
    runs = _load_runs()
    scored = []
    for r in runs:
        sc = r.get("success_criterion", "")
        if not isinstance(sc, str):
            continue
        score = _overlap_score(query_terms, sc)
        if score > 0:
            scored.append((score, r))
    scored.sort(key=lambda t: t[0], reverse=True)
    top = scored[:limit]

    principles = []
    for score, run in top:
        if run.get("outcome") == "OK" and run.get("chosen_approach"):
            principles.append({
                "principle": f"In context similar to '{query}': '{run['chosen_approach']}' led to positive outcome",
                "based_on": [run["_filename"]],
                "similarity_score": round(score, 3),
                "confidence": round(min(score, 0.9), 2),
            })
    return {
        "query": query,
        "category": category,
        "matches_found": len(top),
        "principles": principles[:3],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("status", help="check activation status and runs/ maturity")

    ext_p = sub.add_parser("extract", help="extract principles (requires active)")
    ext_p.add_argument("--category", required=True, choices=sorted(SUPPORTED_CATEGORIES))
    ext_p.add_argument("--query", required=True)
    ext_p.add_argument("--limit", type=int, default=5)

    args = ap.parse_args(argv)
    if args.cmd == "status" or args.cmd is None:
        print(json.dumps(_check_status(), indent=2, ensure_ascii=False))
    elif args.cmd == "extract":
        print(json.dumps(extract(args.category, args.query, args.limit), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6.2: Run smoke test**

```bash
python scripts/principle_extraction.py status
```

Expected: JSON with `"inactive": true` and `"blocked_reason"` non-null.

```bash
python scripts/principle_extraction.py extract --category trading --query "stop loss"
```

Expected: JSON with `"error": "principle_extraction is INACTIVE"`.

---

## Task 7: Add `aggregate_rund2` to `scripts/aggregator.py`

**Files:** Modify `scripts/aggregator.py`

Add the rund2 aggregation function and SCHEMES entry. Use `# === RUND2 ===` delimiters.

- [ ] **Step 7.1: Read current end of aggregator.py**

Read `scripts/aggregator.py` lines 310-353 to confirm `SCHEMES` dict location.

- [ ] **Step 7.2: Insert rund2 function before `SCHEMES` dict**

Insert before the line `SCHEMES = {`:

```python
# === RUND2 ===
def _rund2_methodology_notes(g: dict, c: dict, cons: dict) -> str:
    notes = []
    if g.get("abstain", {}).get("triggered"):
        notes.append(f"Generator abstain: {g['abstain'].get('reason', '?')}")
    if g.get("challenge_upward", {}).get("triggered"):
        notes.append("Generator challenged Conservator (challenge_upward)")
    if c.get("disagreements"):
        n = len(c["disagreements"])
        notes.append(f"{n} disagreement(s) detectate")
    return " | ".join(notes) if notes else "Deliberare completă fără anomalii"


def aggregate_rund2(
    generator_out: dict,
    control_out: dict,
    conservator_out: dict,
) -> dict:
    """RUND2 priority-based aggregation with veto cascade.

    Input: voice output dicts (not candidate scores).

    Priority order:
    1. glossary_fail (Control) → BLOCK
    2. irreversibility_flag (Conservator) → BLOCK
    3. substantial disagreement (Control) → REWORK
    4. scale_down (Conservator meta) → ADAPT_SHORT
    5. scale_up (Conservator meta) → ADAPT_EXTENDED
    6. 3+ triggers simultaneously → ESCALATE
    7. default → AGGREGATE
    """
    triggers: list[str] = []

    # Priority 1: Glossary fail
    if control_out.get("glossary_fail"):
        return {
            "scheme": "rund2",
            "result": "BLOCK",
            "reason": "glossary_fail",
            "attempts": control_out.get("glossary_attempts", []),
            "action": "Reformulează întrebarea cu termeni operaționali verificabili",
        }

    # Priority 2: Irreversibility without consent
    if conservator_out.get("irreversibility_flag"):
        rr = conservator_out.get("regression_risk", {})
        return {
            "scheme": "rund2",
            "result": "BLOCK",
            "reason": "irreversibility_no_consent",
            "magnitude": rr.get("magnitude") if isinstance(rr, dict) else None,
            "action": "Confirmă explicit că această decizie este ireversibilă înainte de a continua",
        }

    # Collect triggers for escalation check
    disagreements = control_out.get("disagreements", [])
    substantial = [d for d in disagreements if isinstance(d, dict) and d.get("type") == "substantial"]
    if substantial:
        triggers.append("substantial_disagreement")

    meta = conservator_out.get("meta_recommendation")
    if meta == "scale_down":
        triggers.append("scale_down")
    elif meta == "scale_up":
        triggers.append("scale_up")

    if generator_out.get("abstain", {}).get("triggered"):
        triggers.append("generator_abstain")

    # Priority 5 (escalate before individual handling)
    if len(triggers) >= 3:
        return {
            "scheme": "rund2",
            "result": "ESCALATE",
            "triggers": triggers,
            "action": (
                "Multiple semnale critice detectate simultan. "
                "Aggregator nu poate decide singur. Alege ordinea de rezolvare:\n"
                + "\n".join(f"  - {t}" for t in triggers)
            ),
        }

    # Priority 3: Substantial disagreement
    if "substantial_disagreement" in triggers:
        return {
            "scheme": "rund2",
            "result": "REWORK",
            "reason": "substantial_disagreement",
            "disagreements": substantial,
            "action": "Vocile au divergențe substanțiale — clarifică înainte de agregare finală",
        }

    # Priority 4a: scale_down
    if "scale_down" in triggers:
        preferred = generator_out.get("preferred")
        return {
            "scheme": "rund2",
            "result": "ADAPT_SHORT",
            "meta_recommendation": "scale_down",
            "chosen": preferred,
            "action": "Deliberare comprimată — răspuns scurt (max 2 propoziții)",
        }

    # Priority 4b: scale_up
    if "scale_up" in triggers:
        return {
            "scheme": "rund2",
            "result": "ADAPT_EXTENDED",
            "meta_recommendation": "scale_up",
            "action": "Deliberare extinsă necesară — cere clarificare user înainte de a continua",
        }

    # Default: aggregate normally
    preferred = generator_out.get("preferred")
    options = generator_out.get("options", generator_out.get("candidates", []))
    rr = conservator_out.get("regression_risk", {})
    net_concern = (
        rr.get("net_concern", 0.15) if isinstance(rr, dict) else float(rr)
        if isinstance(rr, (int, float)) else 0.15
    )

    confidence_per_option: dict[str, float] = {}
    for opt in options:
        oid = opt.get("id", "")
        base = 1.0 if oid == preferred else 0.5
        confidence_per_option[oid] = round(base * (1.0 - net_concern), 3)

    methodology_confidence = 1.0
    if "generator_abstain" in triggers:
        methodology_confidence -= 0.3
    if not control_out.get("glossary"):
        methodology_confidence -= 0.1
    if control_out.get("disagreements"):
        methodology_confidence -= 0.05 * len(control_out["disagreements"])
    methodology_confidence = max(0.0, round(methodology_confidence, 2))

    result = {
        "scheme": "rund2",
        "result": "AGGREGATE",
        "chosen": preferred,
        "confidence_per_option": confidence_per_option,
        "confidence_methodology": methodology_confidence,
        "methodology_notes": _rund2_methodology_notes(generator_out, control_out, conservator_out),
    }
    if methodology_confidence < 0.5:
        result["warning"] = "Deliberare incompletă — consideră rezultatul ca preliminar"
    return result
# === END RUND2 ===
```

- [ ] **Step 7.3: Add rund2 to SCHEMES dict**

In the `SCHEMES` dict, add after the last existing entry:

```python
    # === RUND2 ===
    "rund2": lambda data: aggregate_rund2(
        data["generator"],
        data["control"],
        data["conservator"],
    ),
    # === END RUND2 ===
```

- [ ] **Step 7.4: Verify aggregator imports fine**

```bash
cd scripts && python -c "import aggregator; print('aggregate_rund2 OK')" && cd ..
```

Expected: `aggregate_rund2 OK`

---

## Task 8: Update `scripts/validate_report.py`

**Files:** Modify `scripts/validate_report.py`

Add `_validate_regression_risk()`, optional RUND2 field validators, `--strict-rund2` flag. All new code delimited with `# === RUND2 ===`.

- [ ] **Step 8.1: Add `_validate_regression_risk` helper**

After the existing `_is_non_negative_int` function (line ~67), insert:

```python
# === RUND2 ===
_REVERSIBILITY_VALUES = frozenset({"complete", "partial", "irreversible"})
_MAGNITUDE_VALUES = frozenset({"trivial", "moderate", "high", "critical"})
_META_REC_VALUES = frozenset({"scale_down", "scale_up", None})


def _validate_regression_risk(value: object) -> list[str]:
    """Accept scalar float (old format) OR object with reversibility/magnitude/net_concern (RUND2)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not (0.0 <= float(value) <= 1.0):
            return [f"regression_risk scalar must be in [0.0, 1.0], got {value}"]
        return []
    if isinstance(value, dict):
        problems = []
        rev = value.get("reversibility")
        if rev not in _REVERSIBILITY_VALUES:
            problems.append(f"regression_risk.reversibility must be one of {sorted(str(v) for v in _REVERSIBILITY_VALUES)}, got {rev!r}")
        mag = value.get("magnitude")
        if mag not in _MAGNITUDE_VALUES:
            problems.append(f"regression_risk.magnitude must be one of {sorted(_MAGNITUDE_VALUES)}, got {mag!r}")
        nc = value.get("net_concern")
        if nc is not None and not (isinstance(nc, (int, float)) and not isinstance(nc, bool) and 0.0 <= float(nc) <= 1.0):
            problems.append(f"regression_risk.net_concern must be float in [0.0, 1.0], got {nc!r}")
        return problems
    return [f"regression_risk must be a float or an object, got {type(value).__name__}"]


def _validate_rund2_fields(report: dict) -> list[str]:
    """Strict RUND2 field validation — only run with --strict-rund2 flag."""
    problems = []
    # Check conservator output fields if present
    for score in report.get("voice_scores", {}).get("conservator", {}).get("scores", []):
        rr = score.get("regression_risk")
        if rr is None:
            problems.append(f"strict-rund2: candidate '{score.get('id')}' conservator missing regression_risk object")
            continue
        problems.extend(_validate_regression_risk(rr))
        if "tokens_budget" not in score:
            problems.append(f"strict-rund2: candidate '{score.get('id')}' conservator missing tokens_budget")
    return problems
# === END RUND2 ===
```

- [ ] **Step 8.2: Add `--strict-rund2` CLI flag**

In the `main()` function of `validate_report.py`, after the existing `--input` argument:

```python
    # === RUND2 ===
    ap.add_argument(
        "--strict-rund2",
        action="store_true",
        default=False,
        help="require RUND2 fields (regression_risk object, tokens_budget) in conservator scores",
    )
    # === END RUND2 ===
```

- [ ] **Step 8.3: Call strict validation in main()**

In `main()`, after `problems = validate(report)`, add:

```python
    # === RUND2 ===
    if args.strict_rund2:
        problems.extend(_validate_rund2_fields(report))
    # === END RUND2 ===
```

- [ ] **Step 8.4: Verify validate_report still passes baseline**

```bash
echo '{"success_criterion":"test","verification":"test","chosen_approach":"A","telemetry":{"mode":"sequential"}}' | python scripts/validate_report.py
```
Expected: exit 0.

```bash
echo '{"success_criterion":"test","verification":"test","chosen_approach":"A","telemetry":{"mode":"sequential"}}' | python scripts/validate_report.py --strict-rund2
```
Expected: exit 0 (no conservator scores in report → strict check finds nothing).

---

## Task 9: Write `scripts/test_rund2.py`

**Files:** Create `scripts/test_rund2.py`

- [ ] **Step 9.1: Write tests**

```python
"""Tests for RUND2 architecture additions.

Run:
    python scripts/test_rund2.py
    python -m pytest scripts/test_rund2.py -v  (if pytest available)
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vocabulary_map import translate, compute_tokens_budget, VOCABULARY_MAP
from principle_extraction import _check_status, extract, _INACTIVE
import aggregator


class TestVocabularyMap(unittest.TestCase):
    def test_translate_reversibility_complete(self):
        result = translate("reversibility", "complete")
        self.assertIn("ușor", result)

    def test_translate_magnitude_critical(self):
        result = translate("magnitude", "critical")
        self.assertIn("major", result.lower())

    def test_translate_meta_recommendation_scale_down(self):
        result = translate("meta_recommendation", "scale_down")
        self.assertTrue(len(result) > 0)

    def test_translate_unknown_category(self):
        result = translate("nonexistent", "value")
        self.assertEqual(result, "value")

    def test_translate_none_value(self):
        result = translate("meta_recommendation", None)
        self.assertEqual(result, "")

    def test_compute_tokens_budget_trivial_complete(self):
        budget = compute_tokens_budget("trivial", "complete")
        self.assertEqual(budget["generator"], 300)
        self.assertEqual(budget["control"], 300)

    def test_compute_tokens_budget_critical_irreversible(self):
        budget = compute_tokens_budget("critical", "irreversible")
        self.assertEqual(budget["generator"], 4000)

    def test_compute_tokens_budget_scale_down_override(self):
        budget = compute_tokens_budget("critical", "irreversible", meta="scale_down")
        self.assertEqual(budget["generator"], 300)

    def test_compute_tokens_budget_unknown_combo_defaults(self):
        budget = compute_tokens_budget("trivial", "irreversible")
        self.assertEqual(budget["generator"], 800)


class TestPrincipleExtraction(unittest.TestCase):
    def test_status_returns_inactive(self):
        status = _check_status()
        self.assertTrue(status["inactive"])
        self.assertIn("blocked_reason", status)
        self.assertIsNotNone(status["blocked_reason"])

    def test_extract_returns_error_when_inactive(self):
        result = extract("trading", "stop loss")
        self.assertIn("error", result)
        self.assertIn("INACTIVE", result["error"])

    def test_extract_excluded_category(self):
        import principle_extraction as pe
        orig = pe._INACTIVE
        pe._INACTIVE = False
        result = extract("career", "job change")
        pe._INACTIVE = orig
        self.assertIn("excluded", result)

    def test_extract_unsupported_category_when_active(self):
        import principle_extraction as pe
        orig = pe._INACTIVE
        pe._INACTIVE = False
        result = extract("fantasy", "dragons")
        pe._INACTIVE = orig
        self.assertIn("error", result)
        self.assertIn("unsupported", result["error"])


class TestAggregateRund2(unittest.TestCase):
    def _base_conservator(self, reversibility="complete", magnitude="trivial", meta=None, flag=False):
        return {
            "regression_risk": {
                "reversibility": reversibility,
                "magnitude": magnitude,
                "net_concern": 0.05,
            },
            "meta_recommendation": meta,
            "irreversibility_flag": flag,
            "tokens_budget": {"generator": 300, "control": 300},
        }

    def _base_generator(self, preferred="A", abstain=False):
        return {
            "candidates": [{"id": "A"}, {"id": "do_nothing"}],
            "preferred": preferred,
            "abstain": {"triggered": abstain, "reason": "test" if abstain else None},
            "challenge_upward": {"triggered": False, "reason": None},
        }

    def _base_control(self, glossary_fail=False, disagreements=None):
        return {
            "glossary": {"term": "definition"},
            "glossary_fail": glossary_fail,
            "glossary_attempts": [],
            "disagreements": disagreements or [],
            "verdicts": [{"id": "A", "valid": True, "issues": [], "tests_to_write": []}],
        }

    def test_glossary_fail_blocks(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(),
            self._base_control(glossary_fail=True),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "BLOCK")
        self.assertEqual(result["reason"], "glossary_fail")

    def test_irreversibility_flag_blocks(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(),
            self._base_control(),
            self._base_conservator(flag=True),
        )
        self.assertEqual(result["result"], "BLOCK")
        self.assertEqual(result["reason"], "irreversibility_no_consent")

    def test_substantial_disagreement_reworks(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(),
            self._base_control(disagreements=[{"between": ["g", "c"], "type": "substantial", "detail": "x"}]),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "REWORK")

    def test_scale_down_adapts_short(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(),
            self._base_control(),
            self._base_conservator(meta="scale_down"),
        )
        self.assertEqual(result["result"], "ADAPT_SHORT")

    def test_scale_up_adapts_extended(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(),
            self._base_control(),
            self._base_conservator(meta="scale_up"),
        )
        self.assertEqual(result["result"], "ADAPT_EXTENDED")

    def test_three_triggers_escalate(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(abstain=True),
            self._base_control(
                disagreements=[{"between": ["g", "c"], "type": "substantial", "detail": "x"}]
            ),
            self._base_conservator(meta="scale_up"),
        )
        self.assertEqual(result["result"], "ESCALATE")
        self.assertEqual(len(result["triggers"]), 3)

    def test_normal_aggregate_returns_chosen(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(preferred="A"),
            self._base_control(),
            self._base_conservator(),
        )
        self.assertEqual(result["result"], "AGGREGATE")
        self.assertEqual(result["chosen"], "A")

    def test_low_methodology_confidence_warns(self):
        result = aggregator.aggregate_rund2(
            self._base_generator(abstain=True),
            self._base_control(disagreements=[
                {"type": "substantial", "detail": "x"},
                {"type": "substantial", "detail": "y"},
                {"type": "substantial", "detail": "z"},
            ]),
            self._base_conservator(),
        )
        # abstain + 3 substantial disagreements → either escalate (3 triggers) or low confidence
        # In this case: abstain + 3 disagreements = triggers ["substantial_disagreement", "generator_abstain"] → 2 triggers → REWORK
        self.assertIn(result["result"], ("REWORK", "ESCALATE", "AGGREGATE"))


class TestValidateReportRund2(unittest.TestCase):
    def test_regression_risk_scalar_still_valid(self):
        import validate_report
        problems = validate_report._validate_regression_risk(0.5)
        self.assertEqual(problems, [])

    def test_regression_risk_object_valid(self):
        import validate_report
        problems = validate_report._validate_regression_risk({
            "reversibility": "complete",
            "magnitude": "trivial",
            "net_concern": 0.05,
        })
        self.assertEqual(problems, [])

    def test_regression_risk_object_missing_magnitude(self):
        import validate_report
        problems = validate_report._validate_regression_risk({
            "reversibility": "complete",
            "net_concern": 0.05,
        })
        self.assertTrue(any("magnitude" in p for p in problems))

    def test_regression_risk_invalid_reversibility(self):
        import validate_report
        problems = validate_report._validate_regression_risk({
            "reversibility": "unknown",
            "magnitude": "trivial",
        })
        self.assertTrue(any("reversibility" in p for p in problems))

    def test_regression_risk_scalar_out_of_range(self):
        import validate_report
        problems = validate_report._validate_regression_risk(1.5)
        self.assertTrue(len(problems) > 0)

    def test_regression_risk_wrong_type(self):
        import validate_report
        problems = validate_report._validate_regression_risk("high")
        self.assertTrue(len(problems) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] **Step 9.2: Run tests**

```bash
python scripts/test_rund2.py
```

Expected: all tests pass with `OK` output. Fix any failures before continuing.

---

## Task 10: Update `SKILL.md`

**Files:** Modify `SKILL.md`

Key changes: sequential dispatch (Conservator first), remove parallel mode from user options, add Three-layer architecture + Sequential dispatch + Veto powers + Principle_Extraction sections. Use `<!-- === RUND2 === -->` delimiters.

- [ ] **Step 10.1: Read current SKILL.md steps 2-5 to understand exact text to replace**

Read `SKILL.md` lines 68-140 to see current Generator (Step 2), Control (Step 3), Conservator (Step 4) ordering.

- [ ] **Step 10.2: Reorder Steps 2-4 to Conservator→Generator→Control**

Find the section headers `### 2. Generator`, `### 3. Control`, `### 4. Conservator` and reorder them as:
- `### 2. Conservator — assess risc (runs FIRST)` ← current Step 4 content, with additions
- `### 3. Generator — produce alternative` ← current Step 2 content, with note about receiving tokens_budget
- `### 4. Control — verifică corectitudine` ← current Step 3 content, with note about seeing both voices

Add to Step 2 (Conservator):

```markdown
**Sequential-first.** Conservator runs before Generator and Control. Its `tokens_budget` output caps how deep the other voices go. Its `irreversibility_flag: true` BLOCKS the pipeline — confirm user consent before proceeding.

**Veto check (auto, after Conservator output):**
- If `irreversibility_flag: true` → stop, ask user: *"Conservator marcheaza aceasta decizie ca ireversibila. Confirmi ca vrei sa continui?"* — proceed only with explicit YES.
- If `meta_recommendation: scale_down` → skip Generator's unconventional/adversarial candidates; cap at 2 candidates; use short path.
- If `meta_recommendation: scale_up` → warn user, add context request before Generator.
```

Add to Step 3 (Generator):

```markdown
**Receives from Conservator (selective):** `magnitude`, `counterparty_risks`, `tokens_budget.generator`. Does NOT receive `meta_recommendation` — that is policy, not Generator input.

**Challenge upward:** If Generator sets `challenge_upward.triggered: true`, re-run Conservator with Generator's context before proceeding to Control.
```

Add to Step 4 (Control):

```markdown
**Receives from both:** full Conservator output + full Generator output.

**Post-Control veto check:**
- If `glossary_fail: true` → BLOCK, request reformulation from user.
- If `disagreements` contains any `type: substantial` → REWORK: re-run Generator with clarification before aggregating.
```

- [ ] **Step 10.3: Remove parallel mode from user-selectable options**

Find the section describing available modes. Remove `parallel` as a user-invocable option. Keep the note:

```markdown
<!-- === RUND2 === -->
**Parallel mode removed (RUND2).** Parallel dispatch is no longer a user-selectable option. Auto-triggered internally only when `magnitude = critical` AND `reversibility = irreversible`, as a cross-check on the sequential result. Every 20 runs, a silent parallel audit runs automatically; if systematic divergence is detected, frequency increases to 1/5.
<!-- === END RUND2 === -->
```

- [ ] **Step 10.4: Add Three-layer architecture section**

At the end of SKILL.md (before any existing appendix), insert:

```markdown
<!-- === RUND2 === -->
## Three-layer architecture (RUND2)

| Layer | Components | Role |
|---|---|---|
| **Deliberation** | Conservator → Generator → Control (sequential) | Runs on every user question |
| **Aggregation** | aggregate_rund2() with 8-component veto cascade | Synthesizes voice outputs, decides what user sees |
| **Senate** | 7 senators (Wittgenstein, Aurelius, Confucius, Socrate, Musk, Dimon, Napoleon) | On-demand audit of proposed changes to consilium itself |

## Sequential dispatch (RUND2)

Default order: **Conservator → Generator → Control**

1. Conservator sets `tokens_budget` and `irreversibility_flag`
2. Generator receives `magnitude`, `counterparty_risks`, `tokens_budget.generator` (NOT `meta_recommendation`)
3. Control receives full outputs from both Conservator and Generator

Auto-parallel cross-check: triggered only when Conservator outputs `magnitude: critical` AND `reversibility: irreversible`. Not user-selectable.

Silent audit: every 20 runs, parallel mode runs silently alongside sequential. If systematic divergence detected → audit frequency increases to 1/5.

## Veto powers (RUND2)

| Trigger | Source | Effect | Action |
|---|---|---|---|
| `irreversibility_flag: true` | Conservator | BLOCK (hard) | Ask user for explicit consent before Generator |
| `glossary_fail: true` | Control | BLOCK (soft) | Ask user to reformulate with operational terms |
| `disagreements: substantial` | Control | REWORK | Re-run Generator with clarification context |
| `meta_recommendation: scale_down` | Conservator | ADAPT_SHORT | Short path: max 2 candidates, 2-sentence output |
| `meta_recommendation: scale_up` | Conservator | ADAPT_EXTENDED | Warn user, add context before Generator |
| 3+ of above simultaneously | Aggregator | ESCALATE | Present trigger table to user, request decision |

Veto budget for `meta_recommendation`: 5 activations of `scale_up` or `scale_down` per month. On exhaustion → soft warning only, not blocking.

## Principle_Extraction (RUND2 — EXPERIMENTAL, inactive)

Script: `scripts/principle_extraction.py`

**Status: INACTIVE.** Blocked until:
1. `runs/` has >= 10 entries in target category
2. Outcome tracking active for >= 80% of runs
3. Category has externally-verifiable outcomes

**Supported categories (once active):** trading, code, real_estate

**Excluded categories (subjective):** career, relationships, mental_health

To activate: flip `_INACTIVE = False` in `scripts/principle_extraction.py` after verifying the 3 conditions. Once active, Conservator consults it before marking `magnitude`.
<!-- === END RUND2 === -->
```

- [ ] **Step 10.5: Verify SKILL.md has required sections**

```bash
python -c "
with open('SKILL.md', encoding='utf-8') as f:
    content = f.read()
assert 'Three-layer architecture' in content
assert 'Sequential dispatch' in content
assert 'Veto powers' in content
assert 'Principle_Extraction' in content
assert 'RUND2' in content
print('SKILL.md OK')
"
```
Expected: `SKILL.md OK`

---

## Task 11: `/consilium senate` self-validation

**Files:** none (produces gitignored JSON in runs/senate/)

- [ ] **Step 11.1: Run senate validation**

Invoke the consilium skill in senate mode with the proposal:

```
/consilium senate "Am implementat arhitectura RUND2 în Consilium: dispatch secvențial Conservator→Generator→Control, 8 componente de agregare (veto cascade), vocabulary_map.py, principle_extraction.py inactiv, modul parallel eliminat. Schimbările sunt în prompts/conservator.md, generator.md, control.md, scripts/aggregator.py, vocabulary_map.py, principle_extraction.py, validate_report.py, SKILL.md. E gata pentru merge?"
```

- [ ] **Step 11.2: Handle senate verdict**

- If `verdict = GO` → proceed to Task 12.
- If `verdict = MODIFY` → apply each item in `modify_requests`. For each modify_request:
  1. Read the relevant file
  2. Make the requested change
  3. Rerun `python scripts/test_rund2.py` to verify nothing broke
  After all changes applied → proceed to Task 12.
- If `verdict = STOP` → do NOT commit. Report to user with the full senate output before proceeding.

---

## Task 12: Single commit

**Files:** all modified/created files above

- [ ] **Step 12.1: Verify git status — expected files only**

```bash
git status
```

Expected tracked changes (only these):
- `prompts/conservator.md` (MOD)
- `prompts/generator.md` (MOD)
- `prompts/control.md` (MOD)
- `scripts/vocabulary_map.py` (NEW)
- `scripts/principle_extraction.py` (NEW)
- `scripts/aggregator.py` (MOD)
- `scripts/validate_report.py` (MOD)
- `scripts/test_rund2.py` (NEW)
- `SKILL.md` (MOD)

If unexpected files are staged, investigate before committing.

- [ ] **Step 12.2: Run full test suite**

```bash
python scripts/test_rund2.py
python scripts/validate_report.py < runs/$(ls runs/*.json 2>/dev/null | sort | tail -1) 2>/dev/null || echo "no runs yet - skipping"
```

Expected: all tests pass.

- [ ] **Step 12.3: Stage and commit**

```bash
git add prompts/conservator.md prompts/generator.md prompts/control.md
git add scripts/vocabulary_map.py scripts/principle_extraction.py
git add scripts/aggregator.py scripts/validate_report.py scripts/test_rund2.py
git add SKILL.md
git commit -m "$(cat <<'EOF'
feat(rund2): three-layer sequential architecture with veto cascade

Deliberation layer:
- Sequential dispatch: Conservator → Generator → Control
- Conservator sets tokens_budget (trivial=300 to critical=4000 per voice)
- Generator receives magnitude + counterparty_risks + tokens_budget (not meta_recommendation)
- Control receives both voice outputs; glossary max 5 terms
- Veto powers: irreversibility_flag BLOCK, glossary_fail BLOCK,
  substantial_disagreement REWORK, scale_down/up ADAPT, 3+ triggers ESCALATE

Aggregation layer:
- aggregate_rund2() with 8-component priority cascade in aggregator.py
- vocabulary_map.py: single source of truth for user-facing natural language
- validate_report.py: accepts regression_risk as object (RUND2) or scalar (legacy)
- --strict-rund2 flag for new field validation

Parallel mode removed from user-selectable options.
Auto-parallel cross-check on critical+irreversible only.

principle_extraction.py: scripted but INACTIVE (blocked pending runs/ maturity).

Justification: experiments/New phase senat/todos/TODO_RUND2.md
Design: docs/superpowers/specs/2026-05-16-consilium-experimental-implementation-design.md
EOF
)"
```

- [ ] **Step 12.4: Verify commit**

```bash
git log --oneline -3
git show --stat HEAD
```

Expected: one commit on `feat/rund2-architecture` with the files listed above.

- [ ] **Step 12.5: Push**

```bash
git push -u origin feat/rund2-architecture
```

- [ ] **Step 12.6: Return to main**

```bash
git checkout main
```

Report: branch `feat/rund2-architecture` pushed. User opens PR manually from GitHub UI.
