# Trias Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Ensemble mode with **Trias** — a fixed team of 3 named personalities (Pioneer / Architect / Steward), 9 voice sub-agents with personality lens injection, democratic majority vote with explicit failure modes.

**Architecture:** Spec at `docs/superpowers/specs/2026-05-13-trias-mode-design.md`. Personalities are **logical groupings**, NOT subagents — orchestrator dispatches all 9 voices directly with personality metadata. Each voice receives `prompts/<voice>.md` + `prompts/<personality>_lens.md` prepended.

**Tech Stack:** Python stdlib only (project rule). No pytest — smoke tests via CLI per `CLAUDE.md`. Branch: `feat/trias-impl`. Single commit, amend pattern per `CLAUDE.md` rule 2.

---

## File Structure

**New files (3):**
- `prompts/pioneer_lens.md` — Pioneer's bias prompt (~80 words)
- `prompts/architect_lens.md` — Architect's bias prompt (~80 words)
- `prompts/steward_lens.md` — Steward's bias prompt (~80 words)

**Modified files (8):**
- `scripts/personalities.py` — Rewrite from random sampling → 3 hardcoded
- `scripts/aggregator.py` — Add `team_vote` scheme
- `scripts/confidence.py` — Vote pattern → confidence mapping
- `scripts/build_report.py` — Trias shape assembly
- `scripts/validate_report.py` — Accept Trias shape
- `scripts/log_feedback.py` — Log `vote_pattern` column
- `SKILL.md` — Replace §Ensemble with §Trias
- `evals/scenarios.json` — Add 5 Trias scenarios

**11 files total (3 new, 8 modified).**

---

## Task 0: Commit the plan (initial commit on branch)

**Files:**
- Add: `docs/superpowers/plans/2026-05-13-trias-mode-impl.md` (this file)

- [ ] **Step 1: Stage and commit the plan**

```bash
git add docs/superpowers/plans/2026-05-13-trias-mode-impl.md
git commit -m "feat(trias): implementation plan and lens prompts (WIP)"
```

This is the initial commit. All subsequent tasks **amend** this commit (single-commit-per-branch per `CLAUDE.md`). The final commit message will be updated in Task 9.

---

## Task 1: Create the 3 lens prompt files

**Files:**
- Create: `prompts/pioneer_lens.md`
- Create: `prompts/architect_lens.md`
- Create: `prompts/steward_lens.md`

- [ ] **Step 1: Write `prompts/pioneer_lens.md`**

```markdown
---
personality: pioneer
voice_bias: prepended
---

# Pioneer's Lens

You are evaluating this change through a Pioneer's lens. Pioneer values bold,
high-reward approaches that push the codebase forward.

When applying your voice's role:
- Tolerate moderate risk for novel solutions
- Favor new patterns over existing ones when the new pattern adds clear value
- Weight creative potential and forward momentum heavily
- When in doubt between safe and ambitious, prefer ambitious

This lens biases your perception; it does not change your role. You still
perform your voice's standard job (Generator generates, Control verifies,
Conservator assesses risk) — but through Pioneer's perspective.
```

- [ ] **Step 2: Write `prompts/architect_lens.md`**

```markdown
---
personality: architect
voice_bias: prepended
---

# Architect's Lens

You are evaluating this change through an Architect's lens. Architect values
internal consistency, test coverage, and structural soundness.

When applying your voice's role:
- Prioritize architectural cleanliness, type safety, and clear abstractions
- Weight test coverage and verifiability heavily
- Internal consistency > external speed; long-term maintainability > short-term win
- Prefer changes that strengthen invariants over those that loosen them

This lens biases your perception; it does not change your role. You still
perform your voice's standard job (Generator generates, Control verifies,
Conservator assesses risk) — but through Architect's perspective.
```

- [ ] **Step 3: Write `prompts/steward_lens.md`**

```markdown
---
personality: steward
voice_bias: prepended
---

# Steward's Lens

You are evaluating this change through a Steward's lens. Steward values
reversibility, minimal scope, and protection of working systems.

When applying your voice's role:
- Favor minimal-scope, reversible changes
- Prefer existing patterns over new ones unless the new one is clearly necessary
- Blast radius < novelty: a smaller safe change beats a larger ambitious one
- Weight regression risk and rollback ease heavily

This lens biases your perception; it does not change your role. You still
perform your voice's standard job (Generator generates, Control verifies,
Conservator assesses risk) — but through Steward's perspective.
```

- [ ] **Step 4: Smoke test — verify all 3 files exist and parse as valid markdown**

```bash
ls -la prompts/*_lens.md
```

Expected: 3 files listed (pioneer_lens.md, architect_lens.md, steward_lens.md).

- [ ] **Step 5: Amend commit**

```bash
git add prompts/pioneer_lens.md prompts/architect_lens.md prompts/steward_lens.md
git commit --amend --no-edit
```

---

## Task 2: Rewrite `scripts/personalities.py` with 3 fixed personalities

**Files:**
- Modify: `scripts/personalities.py` (full rewrite — replace random sampling with hardcoded list)

- [ ] **Step 1: Read existing `scripts/personalities.py` to confirm baseline**

```bash
python -X utf8 scripts/personalities.py 3 --seed 42
```

Expected: outputs 3 random weight triples (old behavior). Save this as reference.

- [ ] **Step 2: Replace file content**

Full new file content for `scripts/personalities.py`:

```python
"""Trias mode — 3 fixed personalities with weights + lens paths.

Replaces the old random-sampling Ensemble personalities. Each personality is
a named character with:
- weights: how it ranks candidates after voice scores arrive
- lens: a prompt prepended to each voice prompt that biases voice perception

CLI:
    python personalities.py                  # emit all 3 as JSON array
    python personalities.py --name pioneer   # emit single personality
"""

from __future__ import annotations

import argparse
import json
import sys

PERSONALITIES = [
    {
        "name": "pioneer",
        "weights": {"generator": 0.49, "control": 0.30, "conservator": 0.21},
        "lens": "prompts/pioneer_lens.md",
    },
    {
        "name": "architect",
        "weights": {"generator": 0.30, "control": 0.49, "conservator": 0.21},
        "lens": "prompts/architect_lens.md",
    },
    {
        "name": "steward",
        "weights": {"generator": 0.30, "control": 0.30, "conservator": 0.40},
        "lens": "prompts/steward_lens.md",
    },
]

NAMES = {p["name"] for p in PERSONALITIES}


def get_by_name(name: str) -> dict:
    for p in PERSONALITIES:
        if p["name"] == name:
            return p
    raise KeyError(f"unknown personality: {name!r} (valid: {sorted(NAMES)})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--name",
        choices=sorted(NAMES),
        default=None,
        help="emit single personality by name (default: emit all 3)",
    )
    # Reject the old positional-N signature explicitly for clearer migration.
    ap.add_argument(
        "n_legacy",
        nargs="?",
        default=None,
        help=argparse.SUPPRESS,
    )
    args = ap.parse_args(argv)

    if args.n_legacy is not None:
        print(
            "error: personalities.py no longer samples random N personalities.\n"
            "       Trias mode uses 3 fixed personalities: pioneer, architect, steward.\n"
            "       Run without arguments to emit all 3, or use --name <pioneer|architect|steward>.",
            file=sys.stderr,
        )
        return 2

    if args.name:
        json.dump(get_by_name(args.name), sys.stdout, indent=2)
    else:
        json.dump(PERSONALITIES, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Smoke test — emit all 3**

```bash
python -X utf8 scripts/personalities.py
```

Expected output (JSON array with 3 entries):
```json
[
  {"name": "pioneer", "weights": {"generator": 0.49, "control": 0.3, "conservator": 0.21}, "lens": "prompts/pioneer_lens.md"},
  {"name": "architect", "weights": {"generator": 0.3, "control": 0.49, "conservator": 0.21}, "lens": "prompts/architect_lens.md"},
  {"name": "steward", "weights": {"generator": 0.3, "control": 0.3, "conservator": 0.4}, "lens": "prompts/steward_lens.md"}
]
```

- [ ] **Step 4: Smoke test — emit single personality**

```bash
python -X utf8 scripts/personalities.py --name steward
```

Expected output:
```json
{
  "name": "steward",
  "weights": {"generator": 0.3, "control": 0.3, "conservator": 0.4},
  "lens": "prompts/steward_lens.md"
}
```

- [ ] **Step 5: Smoke test — legacy `N` arg returns exit 2 with migration message**

```bash
python -X utf8 scripts/personalities.py 5 --seed 42; echo "exit=$?"
```

Expected: stderr message about "personalities.py no longer samples random N", exit code 2.

- [ ] **Step 6: Amend commit**

```bash
git add scripts/personalities.py
git commit --amend --no-edit
```

---

## Task 3: Add `team_vote` scheme to `scripts/aggregator.py`

**Files:**
- Modify: `scripts/aggregator.py` (add new function + register in SCHEMES dict)

- [ ] **Step 1: Read existing aggregator.py to confirm SCHEMES location**

```bash
python -X utf8 -c "import importlib.util; spec = importlib.util.spec_from_file_location('agg', 'scripts/aggregator.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(sorted(m.SCHEMES.keys()))"
```

Expected: `['conservative_override', 'majority', 'risk_adjusted_utility', 'weighted']`

- [ ] **Step 2: Add `aggregate_team_vote` function**

Locate the line in `scripts/aggregator.py` right before the `SCHEMES = {...}` dict (around line 234). Insert this function:

```python
def aggregate_team_vote(personalities: list[dict], candidates: list[dict]) -> dict:
    """Trias mode — democratic majority vote over 3 personalities' chosen-uri.

    Input personalities have shape: {"name": str, "chose": str | None}.
    Vote pattern is derived from the count of chosen-uri:
    - 3-0: all 3 personalities agree
    - 2-1: 2 agree, 1 prefers different candidate
    - 2-0: 2 agree, 1 abstain (chose=null)
    - 1-1-1: 3 different chosen-uri
    - 1-1-0: 2 different chosen-uri + 1 abstain
    - 1-0-0: 1 chosen + 2 abstain
    - 0-0-0: all abstain (total veto)
    """
    if len(personalities) != 3:
        raise ValueError(f"team_vote requires exactly 3 personalities, got {len(personalities)}")

    valid_ids = {c["id"] for c in candidates}
    valid_ids.add(None)

    tally: dict = {}
    abstained: list = []
    for p in personalities:
        chose = p.get("chose")
        if chose not in valid_ids:
            raise ValueError(f"personality {p.get('name')!r} chose unknown candidate {chose!r}")
        if chose is None:
            abstained.append({"name": p["name"], "reason": "all candidates vetoed"})
        else:
            tally[chose] = tally.get(chose, 0) + 1

    counts = sorted(tally.values(), reverse=True)
    abstain_count = len(abstained)
    pattern_parts = list(counts) + [0] * abstain_count
    vote_pattern = "-".join(str(x) for x in pattern_parts) or "0-0-0"

    chosen: str | None = None
    if counts:
        top = counts[0]
        # Majority = strictly more than half; with 3 voters, majority is >=2 votes.
        if top >= 2:
            for cid, n in tally.items():
                if n == top:
                    chosen = cid
                    break

    dissent: list = []
    if chosen and len(tally) > 1:
        for p in personalities:
            cid = p.get("chose")
            if cid is not None and cid != chosen:
                dissent.append({"personality": p["name"], "chose": cid})

    result = {
        "scheme": "team_vote",
        "vote_pattern": vote_pattern,
        "chosen": chosen,
        "vote_tally": tally,
        "dissent": dissent,
        "abstained": abstained,
    }
    if vote_pattern == "0-0-0":
        result["retry_suggested"] = {
            "reason": "all 3 personalities vetoed every candidate",
            "hint": "relax conservator threshold or re-run Generator with risk constraints",
        }
    return result
```

- [ ] **Step 3: Register in SCHEMES dict**

In `scripts/aggregator.py`, locate `SCHEMES = {...}` (around line 234-245). Add this entry to the dict:

```python
    "team_vote": lambda data: aggregate_team_vote(
        data["personalities"], data["candidates"]
    ),
```

The full dict should now include 5 keys: `majority`, `weighted`, `conservative_override`, `risk_adjusted_utility`, `team_vote`.

- [ ] **Step 4: Smoke test — 3-0 unanimous**

```bash
echo '{"personalities":[{"name":"pioneer","chose":"A"},{"name":"architect","chose":"A"},{"name":"steward","chose":"A"}],"candidates":[{"id":"A"},{"id":"B"}]}' | python -X utf8 scripts/aggregator.py --scheme team_vote
```

Expected JSON output:
```json
{"scheme": "team_vote", "vote_pattern": "3", "chosen": "A", "vote_tally": {"A": 3}, "dissent": [], "abstained": []}
```

Note: counts list = `[3]`, so `pattern_parts = [3]`, vote_pattern = `"3"`. Adjust test expectation — actual output uses single-digit pattern when no losers.

To force `"3-0"` format with explicit zero for clarity, modify `pattern_parts` line:
```python
    pattern_parts = list(counts) + [0] * abstain_count
    # Always show second slot for 3-personality vote so 3-0/2-1/2-0 are readable.
    while len(pattern_parts) < 2:
        pattern_parts.append(0)
```

Now expected vote_pattern for 3-0 case is `"3-0"`.

- [ ] **Step 5: Smoke test — 2-1 majority with dissent**

```bash
echo '{"personalities":[{"name":"pioneer","chose":"A"},{"name":"architect","chose":"A"},{"name":"steward","chose":"B"}],"candidates":[{"id":"A"},{"id":"B"}]}' | python -X utf8 scripts/aggregator.py --scheme team_vote
```

Expected:
```json
{"scheme": "team_vote", "vote_pattern": "2-1", "chosen": "A", "vote_tally": {"A": 2, "B": 1}, "dissent": [{"personality": "steward", "chose": "B"}], "abstained": []}
```

- [ ] **Step 6: Smoke test — 2-0 majority with abstain**

```bash
echo '{"personalities":[{"name":"pioneer","chose":"A"},{"name":"architect","chose":"A"},{"name":"steward","chose":null}],"candidates":[{"id":"A"},{"id":"B"}]}' | python -X utf8 scripts/aggregator.py --scheme team_vote
```

Expected:
```json
{"scheme": "team_vote", "vote_pattern": "2-0", "chosen": "A", "vote_tally": {"A": 2}, "dissent": [], "abstained": [{"name": "steward", "reason": "all candidates vetoed"}]}
```

- [ ] **Step 7: Smoke test — 1-1-1 fragmented**

```bash
echo '{"personalities":[{"name":"pioneer","chose":"A"},{"name":"architect","chose":"B"},{"name":"steward","chose":"C"}],"candidates":[{"id":"A"},{"id":"B"},{"id":"C"}]}' | python -X utf8 scripts/aggregator.py --scheme team_vote
```

Expected: `vote_pattern: "1-1-1"`, `chosen: null`.

- [ ] **Step 8: Smoke test — 0-0-0 total veto**

```bash
echo '{"personalities":[{"name":"pioneer","chose":null},{"name":"architect","chose":null},{"name":"steward","chose":null}],"candidates":[{"id":"A"}]}' | python -X utf8 scripts/aggregator.py --scheme team_vote
```

Expected: `vote_pattern: "0-0-0"`, `chosen: null`, `retry_suggested` block present.

- [ ] **Step 9: Amend commit**

```bash
git add scripts/aggregator.py
git commit --amend --no-edit
```

---

## Task 4: Extend `scripts/confidence.py` for vote pattern mapping

**Files:**
- Modify: `scripts/confidence.py` (add vote_pattern detection + mapping)

- [ ] **Step 1: Read the confidence.py main path to know where to branch**

```bash
python -X utf8 -c "import importlib.util; spec = importlib.util.spec_from_file_location('c', 'scripts/confidence.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print([n for n in dir(m) if not n.startswith('_')])"
```

Note the existing public functions.

- [ ] **Step 2: Add vote pattern mapping table**

Near the top of `scripts/confidence.py`, after imports, add:

```python
VOTE_PATTERN_CONFIDENCE = {
    "3-0": 0.95,
    "2-1": 0.70,
    "2-0": 0.75,
    "1-1-1": None,
    "1-1-0": None,
    "1-0-0": None,
    "0-0-0": None,
}


def confidence_from_vote_pattern(pattern: str) -> dict:
    """Trias mode — derive confidence directly from democratic vote pattern.

    Returns the canonical confidence shape (confidence, agreement, separation)
    so downstream code doesn't need to branch on whether the input was Trias
    or score-based.
    """
    if pattern not in VOTE_PATTERN_CONFIDENCE:
        raise ValueError(f"unknown vote pattern: {pattern!r}")
    conf = VOTE_PATTERN_CONFIDENCE[pattern]
    if pattern == "3-0":
        agreement = 1.0
    elif pattern in ("2-1", "2-0"):
        agreement = 2 / 3
    else:
        agreement = 0.0
    return {
        "confidence": conf,
        "agreement": agreement,
        "separation": None,  # not meaningful for democratic vote
        "source": "vote_pattern",
    }
```

- [ ] **Step 3: Update `main()` to detect Trias input**

Locate `main()` in `scripts/confidence.py`. Add a branch at the top of the function (after `args = ap.parse_args(...)` and `data = json.load(...)`):

```python
    # Trias mode: when vote_pattern is present, derive confidence from pattern
    # instead of from utility/variance over voice scores.
    if "vote_pattern" in data:
        result = confidence_from_vote_pattern(data["vote_pattern"])
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
```

This must be BEFORE the existing score-based logic.

- [ ] **Step 4: Smoke test — vote pattern 3-0**

```bash
echo '{"vote_pattern":"3-0"}' | python -X utf8 scripts/confidence.py
```

Expected:
```json
{"confidence": 0.95, "agreement": 1.0, "separation": null, "source": "vote_pattern"}
```

- [ ] **Step 5: Smoke test — vote pattern 1-1-1 (null confidence)**

```bash
echo '{"vote_pattern":"1-1-1"}' | python -X utf8 scripts/confidence.py
```

Expected: `confidence: null`, `agreement: 0.0`.

- [ ] **Step 6: Smoke test — existing score-based input still works**

```bash
echo '{"candidates":[{"id":"a","scores":{"generator":0.8,"control":0.9,"conservator":0.3}}],"chosen":"a"}' | python -X utf8 scripts/confidence.py
```

Expected: existing format with `confidence`, `agreement`, `separation` (numeric values, no `source` field or with `source: "scores"`).

- [ ] **Step 7: Amend commit**

```bash
git add scripts/confidence.py
git commit --amend --no-edit
```

---

## Task 5: Extend `scripts/build_report.py` for Trias shape

**Files:**
- Modify: `scripts/build_report.py` (pass through Trias fields when present in bundle)

- [ ] **Step 1: Read build_report.py to find the report-assembly section**

```bash
python -X utf8 -c "print(open('scripts/build_report.py').read())" | grep -n -E "def |chosen_approach|alternatives"
```

Locate the function that builds the final report dict (likely `build_report` or `main`).

- [ ] **Step 2: Add Trias-shape passthrough**

In the report-assembly function, after the existing fields are populated, add:

```python
    # Trias mode: pass through team/personalities/vote_pattern/dissent/abstained
    # fields when present in the bundle. These come from the orchestrator after
    # the team_vote aggregator scheme runs.
    if "team" in bundle:
        report["team"] = bundle["team"]
    if "personalities" in bundle:
        report["personalities"] = bundle["personalities"]
    if "vote_pattern" in bundle:
        report["vote_pattern"] = bundle["vote_pattern"]
    if "dissent" in bundle.get("aggregate", {}):
        report["dissent"] = bundle["aggregate"]["dissent"]
    if "abstained" in bundle.get("aggregate", {}):
        report["abstained"] = bundle["aggregate"]["abstained"]
```

- [ ] **Step 3: Smoke test — bundle with Trias fields produces Trias-shape report**

Create a minimal Trias bundle file `/tmp/trias_bundle.json`:

```bash
cat > /tmp/trias_bundle.json <<'EOF'
{
  "success_criterion": "test",
  "verification": "test cmd",
  "team": "trias",
  "personalities": [
    {"name": "pioneer", "weights": {"generator": 0.49, "control": 0.30, "conservator": 0.21}, "lens": "prompts/pioneer_lens.md", "chose": "A"},
    {"name": "architect", "weights": {"generator": 0.30, "control": 0.49, "conservator": 0.21}, "lens": "prompts/architect_lens.md", "chose": "A"},
    {"name": "steward", "weights": {"generator": 0.30, "control": 0.30, "conservator": 0.40}, "lens": "prompts/steward_lens.md", "chose": "B"}
  ],
  "vote_pattern": "2-1",
  "generator": {"candidates": [{"id": "A", "summary": "...", "sketch": "...", "rationale": "..."}, {"id": "B", "summary": "...", "sketch": "...", "rationale": "..."}]},
  "control": {"verdicts": []},
  "conservator": {"scores": []},
  "aggregate": {"scheme": "team_vote", "chosen": "A", "vote_pattern": "2-1", "dissent": [{"personality": "steward", "chose": "B"}], "abstained": []},
  "confidence": {"confidence": 0.70, "agreement": 0.667, "separation": null, "source": "vote_pattern"},
  "telemetry": {"mode": "trias"}
}
EOF

cat /tmp/trias_bundle.json | python -X utf8 scripts/build_report.py
```

Expected: report includes `team: "trias"`, `personalities: [...]`, `vote_pattern: "2-1"`, `dissent: [...]`, `chosen_approach: "A"`.

- [ ] **Step 4: Amend commit**

```bash
git add scripts/build_report.py
git commit --amend --no-edit
```

---

## Task 6: Extend `scripts/validate_report.py` for Trias shape

**Files:**
- Modify: `scripts/validate_report.py` (accept Trias shape with new field requirements)

- [ ] **Step 1: Locate the main validation function**

```bash
python -X utf8 -c "print(open('scripts/validate_report.py').read())" | grep -n -E "def |required|check_"
```

- [ ] **Step 2: Add Trias-specific validation**

After the existing required-field checks (success_criterion, verification, chosen_approach), add:

```python
import re

VOTE_PATTERN_REGEX = re.compile(r"^[0-3]-[0-3](-[0-1])?$")

def _validate_trias(report: dict, errors: list) -> None:
    """Trias-specific validation. Only runs when report has team == 'trias'."""
    personalities = report.get("personalities")
    if not isinstance(personalities, list) or len(personalities) != 3:
        errors.append("trias: personalities must be a list of exactly 3 entries")
        return
    names_seen = set()
    for i, p in enumerate(personalities):
        for f in ("name", "weights", "lens", "chose"):
            if f not in p:
                errors.append(f"trias: personalities[{i}] missing field {f!r}")
        if "name" in p:
            if p["name"] in names_seen:
                errors.append(f"trias: duplicate personality name {p['name']!r}")
            names_seen.add(p["name"])
    expected = {"pioneer", "architect", "steward"}
    if names_seen and names_seen != expected:
        errors.append(f"trias: personality names must be exactly {sorted(expected)}, got {sorted(names_seen)}")

    pattern = report.get("vote_pattern")
    if not pattern or not VOTE_PATTERN_REGEX.match(pattern):
        errors.append(f"trias: vote_pattern missing or malformed (got {pattern!r})")

    chosen = report.get("chosen_approach")
    conf = report.get("confidence")
    null_patterns = {"1-1-1", "1-1-0", "1-0-0", "0-0-0"}
    if pattern in null_patterns:
        if chosen is not None:
            errors.append(f"trias: vote_pattern {pattern!r} requires chosen_approach=null, got {chosen!r}")
        if conf is not None:
            errors.append(f"trias: vote_pattern {pattern!r} requires confidence=null, got {conf!r}")
```

In the main validate function, call this when team is trias:

```python
    if report.get("team") == "trias":
        _validate_trias(report, errors)
```

- [ ] **Step 3: Smoke test — valid Trias report passes**

```bash
cat > /tmp/trias_valid.json <<'EOF'
{
  "success_criterion": "test goal",
  "verification": "pytest",
  "team": "trias",
  "chosen_approach": "A",
  "personalities": [
    {"name": "pioneer", "weights": {"generator": 0.49, "control": 0.30, "conservator": 0.21}, "lens": "prompts/pioneer_lens.md", "chose": "A"},
    {"name": "architect", "weights": {"generator": 0.30, "control": 0.49, "conservator": 0.21}, "lens": "prompts/architect_lens.md", "chose": "A"},
    {"name": "steward", "weights": {"generator": 0.30, "control": 0.30, "conservator": 0.40}, "lens": "prompts/steward_lens.md", "chose": "B"}
  ],
  "vote_pattern": "2-1",
  "alternatives": [],
  "voice_scores": {"generator": 0.8, "control": 0.85, "conservator": 0.3},
  "confidence": 0.70,
  "deliberation_log": [{"step": "vote_tally"}]
}
EOF

cat /tmp/trias_valid.json | python -X utf8 scripts/validate_report.py; echo "exit=$?"
```

Expected: exit code 0.

- [ ] **Step 4: Smoke test — Trias with 2 personalities fails**

```bash
cat > /tmp/trias_bad.json <<'EOF'
{
  "success_criterion": "x", "verification": "y", "team": "trias",
  "chosen_approach": "A", "vote_pattern": "2-0",
  "personalities": [{"name": "pioneer", "weights": {}, "lens": "x", "chose": "A"}],
  "alternatives": [], "voice_scores": {}, "confidence": 0.7, "deliberation_log": []
}
EOF

cat /tmp/trias_bad.json | python -X utf8 scripts/validate_report.py 2>&1; echo "exit=$?"
```

Expected: stderr "personalities must be a list of exactly 3 entries", exit code 1.

- [ ] **Step 5: Smoke test — non-Trias report still validates**

```bash
cat runs/$(ls runs/ | grep -v README | head -1) | python -X utf8 scripts/validate_report.py; echo "exit=$?"
```

Expected: exit code 0 (existing reports unchanged).

- [ ] **Step 6: Amend commit**

```bash
git add scripts/validate_report.py
git commit --amend --no-edit
```

---

## Task 7: Extend `scripts/log_feedback.py` to log `vote_pattern`

**Files:**
- Modify: `scripts/log_feedback.py` (add vote_pattern as metadata column)

- [ ] **Step 1: Locate the row-building function**

```bash
python -X utf8 -c "print(open('scripts/log_feedback.py').read())" | grep -n -E "def |row|append"
```

- [ ] **Step 2: Capture vote_pattern from the input report**

In the function that builds the FEEDBACK.html row, after reading the report, add:

```python
    vote_pattern = report.get("vote_pattern", "")
```

In the row template (find the existing `<tr>...<td>` construction), add a new `<td>` for vote_pattern. If FEEDBACK.html uses a fixed column order, add at the end before the close.

```python
    row_html = (
        f"<tr>"
        f"<td>{date}</td>"
        f"<td>{context}</td>"
        f"<td>{chosen}</td>"
        f"<td>{outcome}</td>"
        f"<td>{note}</td>"
        f"<td>{vote_pattern}</td>"
        f"</tr>"
    )
```

(Adjust based on actual existing row structure.)

- [ ] **Step 3: Smoke test — log a Trias report**

```bash
cat /tmp/trias_valid.json | python -X utf8 scripts/log_feedback.py --outcome OK --run-path runs/trias_test.json
grep "2-1" FEEDBACK.html | head -3
```

Expected: at least 1 line containing `2-1` (the vote_pattern).

- [ ] **Step 4: Smoke test — non-Trias log still works**

```bash
echo '{"success_criterion":"x","verification":"y","chosen_approach":"a","voice_scores":{"generator":0.8,"control":0.9,"conservator":0.3},"confidence":0.8,"alternatives":[],"deliberation_log":[]}' | python -X utf8 scripts/log_feedback.py --outcome OK --run-path runs/non_trias.json
```

Expected: row appended with empty vote_pattern column (no error).

- [ ] **Step 5: Amend commit**

```bash
git add scripts/log_feedback.py
git commit --amend --no-edit
```

---

## Task 8: Replace §Ensemble with §Trias in `SKILL.md`

**Files:**
- Modify: `SKILL.md` (remove Ensemble section, add Trias section)

- [ ] **Step 1: Locate §"Ensemble mode (opțional)"**

```bash
python -X utf8 -c "print(open('SKILL.md').read())" | grep -n "Ensemble mode"
```

- [ ] **Step 2: Delete the entire §Ensemble section**

Remove the section starting at `## Ensemble mode (opțional)` and ending at the next `##` heading (or end of file).

- [ ] **Step 3: Add §Trias mode**

Insert this section in place of (or right after) where §Ensemble used to be:

```markdown
## Trias mode (high-stakes opt-in)

**Mecanica:** 3 personalități fixe (Pioneer / Architect / Steward) deliberează în paralel cu lens prompts injectate, fiecare aplicând weights diferite peste output. Vot democratic majoritar peste cele 3 chosen-uri.

### Când să folosești
- Schema/DB migration ireversibilă
- Security audit (auth, crypto, RCE potential)
- Refactor > 5 fișiere
- 2+ abordări arhitecturale plauzibile, fără clear winner
- Costul deciziei greșite >> costul rulării (9 sub-agenți, 3× Parallel)

### Workflow
1. Orchestrator citește `python -X utf8 scripts/personalities.py` — emite cele 3 personalități
2. Pentru fiecare personalitate, dispatch 3 voci (Gen/Ctrl/Cons) cu `prompts/<voice>.md` + `prompts/<personality>_lens.md` prepended
3. Personalitatea agregă voice scores cu weights proprii → `chose`
4. Orchestrator rulează `python -X utf8 scripts/aggregator.py --scheme team_vote` peste cele 3 chosen-uri
5. Confidence derivat din vote_pattern (3-0/2-1/2-0 = OK auto; 1-1-1/0-0-0 = PEND)

### Vote patterns
| Pattern | Confidence | Outcome |
|---|---|---|
| 3-0 | 0.95 | OK auto |
| 2-1 | 0.70 | OK auto |
| 2-0 | 0.75 | OK auto |
| 1-1-1 / 1-1-0 / 1-0-0 | null | PEND |
| 0-0-0 | null | PEND + retry_suggested |

### Failure recovery
- **1-1-1 fragmentation:** orchestrator întreabă user — accept one, re-run with constraints, or abort
- **0-0-0 total veto:** emite `retry_suggested` cu relaxed threshold sau Generator constraints

### Skip Trias dacă
- Diff < 20 lines / 1 fișier — `scope_gate.py` va skip oricum
- Conservatism strict cerut (Trias agregat e −18% Conservator)
- Bugfix evident — Sequential blind ajunge
```

- [ ] **Step 4: Update §Resources table**

In `SKILL.md`, locate the Resources table (around line 161). Update the `scripts/personalities.py` row:

```markdown
| `scripts/personalities.py` | Trias mode — 3 personalități fixe cu weights + lens paths |
```

Remove any row referencing Ensemble.

- [ ] **Step 5: Smoke test — SKILL.md parses as valid markdown**

```bash
python -X utf8 -c "
data = open('SKILL.md').read()
assert '## Trias mode' in data, 'missing Trias section'
assert 'Ensemble mode' not in data, 'Ensemble section still present'
print('SKILL.md OK')
"
```

Expected: `SKILL.md OK`.

- [ ] **Step 6: Amend commit**

```bash
git add SKILL.md
git commit --amend --no-edit
```

---

## Task 9: Add Trias scenarios to `evals/scenarios.json`

**Files:**
- Modify: `evals/scenarios.json` (add 5 new scenarios for Trias vote patterns)

- [ ] **Step 1: Read the existing scenarios.json structure**

```bash
python -X utf8 -c "import json; data = json.load(open('evals/scenarios.json')); print('keys:', sorted(data.keys()) if isinstance(data, dict) else 'array of', len(data)); print('sample:', list(data.items() if isinstance(data, dict) else data)[0])"
```

Note the schema (likely array of `{name, input, expected}` or similar).

- [ ] **Step 2: Add 5 Trias scenarios**

Append (or insert) these to the existing scenarios array. Schema follows existing pattern:

```json
{
  "name": "trias_unanimous_3_0",
  "scheme": "team_vote",
  "input": {
    "personalities": [
      {"name": "pioneer", "chose": "A"},
      {"name": "architect", "chose": "A"},
      {"name": "steward", "chose": "A"}
    ],
    "candidates": [{"id": "A"}, {"id": "B"}]
  },
  "expected": {"vote_pattern": "3-0", "chosen": "A"}
},
{
  "name": "trias_majority_2_1",
  "scheme": "team_vote",
  "input": {
    "personalities": [
      {"name": "pioneer", "chose": "A"},
      {"name": "architect", "chose": "A"},
      {"name": "steward", "chose": "B"}
    ],
    "candidates": [{"id": "A"}, {"id": "B"}]
  },
  "expected": {"vote_pattern": "2-1", "chosen": "A"}
},
{
  "name": "trias_abstain_2_0",
  "scheme": "team_vote",
  "input": {
    "personalities": [
      {"name": "pioneer", "chose": "A"},
      {"name": "architect", "chose": "A"},
      {"name": "steward", "chose": null}
    ],
    "candidates": [{"id": "A"}, {"id": "B"}]
  },
  "expected": {"vote_pattern": "2-0", "chosen": "A"}
},
{
  "name": "trias_fragment_1_1_1",
  "scheme": "team_vote",
  "input": {
    "personalities": [
      {"name": "pioneer", "chose": "A"},
      {"name": "architect", "chose": "B"},
      {"name": "steward", "chose": "C"}
    ],
    "candidates": [{"id": "A"}, {"id": "B"}, {"id": "C"}]
  },
  "expected": {"vote_pattern": "1-1-1", "chosen": null}
},
{
  "name": "trias_total_veto_0_0_0",
  "scheme": "team_vote",
  "input": {
    "personalities": [
      {"name": "pioneer", "chose": null},
      {"name": "architect", "chose": null},
      {"name": "steward", "chose": null}
    ],
    "candidates": [{"id": "A"}]
  },
  "expected": {"vote_pattern": "0-0-0", "chosen": null, "retry_suggested": true}
}
```

- [ ] **Step 3: Smoke test — run evals and verify Trias scenarios pass**

```bash
python -X utf8 scripts/run_evals.py
```

Expected: all scenarios pass including the 5 new Trias ones. Note: if `run_evals.py` doesn't know about `team_vote` scheme, you may need to extend the dispatcher in that file too — check before assuming it works.

- [ ] **Step 4: Amend commit**

```bash
git add evals/scenarios.json
git commit --amend --no-edit
```

---

## Task 10: Final commit message + branch push

**Files:** none (rewriting commit message only)

- [ ] **Step 1: Update the final commit message**

```bash
git commit --amend -m "$(cat <<'EOF'
feat(trias): implement Trias mode replacing Ensemble

Trias is a high-stakes opt-in mode where 3 fixed personalities (Pioneer,
Architect, Steward) each orchestrate their own parallel deliberation
with personality lens prompts injected, then vote democratically over
the 3 chosen candidates.

Vote patterns:
- 3-0 (unanimous)        confidence 0.95 -> OK auto
- 2-1 (majority+dissent) confidence 0.70 -> OK auto
- 2-0 (majority+abstain) confidence 0.75 -> OK auto
- 1-1-1 / 1-1-0 / 1-0-0  confidence null -> PEND, escalate to user
- 0-0-0 (total veto)     confidence null -> PEND, retry_suggested

Architecture:
- Personalities are LOGICAL GROUPINGS, not subagents (no nested Agent
  calls). Orchestrator dispatches all 9 voice subagents directly with
  personality metadata and lens prompts prepended.
- Each voice gets prompts/<voice>.md + prompts/<personality>_lens.md.

Aggregate progress bias: Generator +9%, Control +9%, Conservator -18%
vs balanced. Conservator cannot be silenced (K >= 0.21 in all 3).

New files (3):
  prompts/pioneer_lens.md
  prompts/architect_lens.md
  prompts/steward_lens.md

Modified (8):
  scripts/personalities.py    rewrite: 3 hardcoded with name+weights+lens
  scripts/aggregator.py       new team_vote scheme
  scripts/confidence.py       vote_pattern -> confidence mapping
  scripts/build_report.py     pass through Trias fields
  scripts/validate_report.py  accept Trias shape with checks
  scripts/log_feedback.py     log vote_pattern column
  SKILL.md                    replace section Ensemble with section Trias
  evals/scenarios.json        5 new Trias scenarios

Spec: docs/superpowers/specs/2026-05-13-trias-mode-design.md
Plan: docs/superpowers/plans/2026-05-13-trias-mode-impl.md

Breaking change: personalities.py no longer accepts N --seed args.
Old runs/*_ensemble.json remain readable but flagged as legacy.
EOF
)"
```

- [ ] **Step 2: Verify the commit looks right**

```bash
git log --stat -1
```

Expected: single commit, all 11 files listed, message matches above.

- [ ] **Step 3: Run the full evals suite as final smoke test**

```bash
python -X utf8 scripts/run_evals.py
```

Expected: all scenarios pass (including 5 new Trias).

- [ ] **Step 4: Validate that an end-to-end Trias report would pass**

```bash
cat /tmp/trias_valid.json | python -X utf8 scripts/validate_report.py; echo "validate_report exit: $?"
```

Expected: exit 0.

- [ ] **Step 5: Push and ask user for review**

Per `CLAUDE.md` rule 3 — ask user "totul ok sau mai vrei schimbări?" before pushing.

If ok:
```bash
git push -u origin feat/trias-impl
git checkout main
```

PR URL will print on push.

---

## Acceptance criteria (from spec §7)

After Task 10, verify each:

1. ✓ `python -X utf8 scripts/personalities.py` emits 3 personalities (Task 2 step 3)
2. ✓ `python -X utf8 scripts/aggregator.py --scheme team_vote < input.json` works (Task 3 steps 4-8)
3. □ Run `/consilium` mode `trias` on a non-trivial diff → produces `runs/<ts>_trias.json` (manual E2E test, deferred to first real use after merge)
4. ✓ `validate_report.py` accepts valid Trias shape (Task 6 step 3)
5. ✓ `run_evals.py` passes 5 new Trias scenarios (Task 9 step 3)
6. ✓ FEEDBACK.html shows `vote_pattern` column for Trias runs (Task 7 step 3)

Item #3 is checked off only after the impl is merged and used on a real change.

---

## Risks and recovery

| If this fails | Then |
|---|---|
| `aggregator.py team_vote` smoke test fails | Re-read vote_pattern logic in Task 3 step 2; sort tally counts descending; ensure abstain count is appended as zeros |
| `validate_report.py` rejects existing non-Trias reports | Add explicit `if report.get("team") == "trias"` guard around `_validate_trias` call — never run trias checks on non-trias reports |
| `run_evals.py` errors on `team_vote` scheme | Add dispatch case for `team_vote` in `run_evals.py`'s scenario runner (may be an extra file to modify; spec didn't anticipate this) |
| Lens prompts produce unexpected voice output during E2E | Defer empirical fix to follow-up branch; document in `FEEDBACK.md` as PEND with note |
