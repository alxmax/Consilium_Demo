# Deliverable Contract Enforcement Implementation Plan

> ⚠ **POST-MORTEM (added 2026-05-18 22:00) — DO NOT EXECUTE.**
>
> This plan executes the failed Step 6.5 approach documented in
> `../specs/2026-05-18-deliverable-enforcement-design.md`. Execution
> reached Task 3 (T1 warmup re-run); the empirical re-run showed
> `solution.py` still missing from disk — same failure mode as the
> prior `CONSILIUM_SUFFIX` attempt. Plan EXECUTION HALTED at Task 3
> per the documented decision gate (Step 3.4 "If passed < 8 → STOP").
>
> Pivot via Senate audit (`runs/senate/2026-05-18_203925-deliverable-enforcement-r2.json`,
> MODIFY 7-0): authority moved to harness layer. Implemented separately:
>
> **`benchmark-modes/scripts/extract_deliverables.py`** (alxmax/Benchmark
> commit `81fd6a4`, merged via PR #4 on 2026-05-18).
>
> Preserved as historical execution record. **Do not re-execute.**

---

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Step 6.5 "Deliverable contract enforcement (auto)" to Consilium SKILL.md so that any deliberation triggered on a prompt declaring deliverable files (`Required output files` section or inline `save to ...` phrasing) writes those files to disk with verify-then-emit gate before closing. Remove the now-redundant `CONSILIUM_SUFFIX` from the benchmark harness.

**Architecture:** Behavioral rule (no regex/parsing infrastructure) embedded in SKILL.md as a new workflow step between Step 6 (feedback log) and Step 7 (auto-pipeline). Trigger is opt-in: rule activates only when the model recognizes a deliverable contract in its task prompt. Single source of truth — `run_task.py` suffix is removed.

**Tech Stack:** Markdown (SKILL.md), Python stdlib only (run_task.py edit). No new dependencies, no new scripts.

---

## File Structure

| File | Action | Lines | Responsibility |
|---|---|---|---|
| `C:\Users\ALEX\Desktop\Doc\Consilium\SKILL.md` | Modify | +~35 | Add Step 6.5 section between Step 6 and Step 7 |
| `C:\Users\ALEX\Desktop\Doc\benchmark-modes\run_task.py` | Modify | -~15 / +3 | Remove `CONSILIUM_SUFFIX` constant + main append; leave tracking comment |
| `C:\Users\ALEX\Desktop\Doc\Consilium\docs\superpowers\plans\2026-05-18-deliverable-enforcement.md` | Create | (this file) | Plan document |
| `C:\Users\ALEX\Desktop\Doc\Consilium\docs\superpowers\specs\2026-05-18-deliverable-enforcement-design.md` | (already exists) | — | Spec — source of truth |

**Files explicitly NOT touched (per user constraint):**
- `C:\Users\ALEX\Desktop\Doc\benchmark-modes\prompts\code\*.md`
- `C:\Users\ALEX\Desktop\Doc\benchmark-modes\prompts\reasoning\*.md`

**Testing approach:** No pytest harness — per CLAUDE.md project "No tests dir". Validation is via integration runs of the benchmark harness itself (each ~$0.7-$1.5 in API costs).

---

## Pre-flight context

**Branch:** `feat/deliverable-enforcement` (already created off main)
**Baseline failure:** `workspace/consilium_sequential/code/00_warmup/RESULT.md` already documents `Score: 0/60` because `solution.py` was never written despite `CONSILIUM_SUFFIX` existing.
**Consilium deliberation:** already complete (`runs/2026-05-18_2012_skill-step-6-5-deliverable-enforcement.json`, chosen: `add_step_6_5_behavioral`, confidence 0.78).
**Git workflow constraint (CLAUDE.md):** single commit per branch, push once at the end, user creates PR manually.

---

### Task 1: Edit SKILL.md — insert Step 6.5

**Files:**
- Modify: `C:\Users\ALEX\Desktop\Doc\Consilium\SKILL.md:199-201` (insert between end-of-Step-6 and start-of-Step-7)

- [ ] **Step 1.1: Locate insertion point**

Verify exact lines:
```bash
grep -n "^### 7. Auto-pipeline" /c/Users/ALEX/Desktop/Doc/Consilium/SKILL.md
```
Expected: a single match at line ~201 (`### 7. Auto-pipeline (opt-in, post-report)`).

- [ ] **Step 1.2: Insert Step 6.5 section**

Use Edit tool. Find the exact transition between Step 6 (ends with paragraph about `mark_outcome.py` and `weighted_bad_rate`) and `### 7. Auto-pipeline (opt-in, post-report)`. Insert this section verbatim BEFORE the `### 7.` line:

```markdown
### 6.5. Deliverable contract enforcement (auto)

Dacă input-ul task-ului declară explicit fișiere de livrat — fie via secțiune
dedicată (ex: `**Required output files**`, `**Deliverables**`), fie via frază
inline ("save your response to `<file>`", "deliver `<file>`", "write to
`<name>`") — TREBUIE să scrii fiecare fișier pe disc **înainte** de a emite
linia finală.

**Acțiunea:**
1. Identifică fiecare filename declarat (backticked, relativ la `cwd`).
2. Pentru fiecare, apelează `Write` cu conținutul implementării
   `chosen_approach` (codul/textul produs în cursul deliberării — pentru
   cod, implementarea concretă a `chosen` candidate-ului; pentru reasoning,
   răspunsul concret cerut, ex. `ANSWER: <letter>` + motivație).
3. Verifică prezența cu `Read <file>` sau `ls`. Dacă lipsește, retry `Write`
   o singură dată; dacă tot lipsește, adaugă `deliverable_write_failed:
   <file>` în `notes` al raportului final și emite linia.

**Gate (obligatoriu):**
- Codul într-un fenced block din răspuns NU este un livrabil acceptat.
  Doar `Write` pe disc satisface contractul.
- Linia finală `chosen: <id> | conf: <X> | runs/<file>.json` se emite
  **doar după** ce toate fișierele declarate există pe disc (sau au fost
  raportate ca `deliverable_write_failed`).

**Nu se aplică dacă:**
- Promptul nu declară niciun deliverable (consilium pe diff / refactor /
  PR review) — Step 6.5 trece transparent.
- `chosen_approach ∈ {"do_nothing", "skipped"}` — nimic de scris.

```

- [ ] **Step 1.3: Verify insertion**

```bash
grep -n "^### 6\.5\." /c/Users/ALEX/Desktop/Doc/Consilium/SKILL.md
grep -n "^### 7\." /c/Users/ALEX/Desktop/Doc/Consilium/SKILL.md
```
Expected:
- Line ~201: `### 6.5. Deliverable contract enforcement (auto)`
- Line ~234: `### 7. Auto-pipeline (opt-in, post-report)` (shifted by ~33 lines)

Confirm Step 7 still exists (not accidentally replaced).

---

### Task 2: Edit run_task.py — remove CONSILIUM_SUFFIX

**Files:**
- Modify: `C:\Users\ALEX\Desktop\Doc\benchmark-modes\run_task.py:77-84` (constant definition)
- Modify: `C:\Users\ALEX\Desktop\Doc\benchmark-modes\run_task.py:519-521` (append in main)

- [ ] **Step 2.1: Replace constant definition**

Use Edit tool. Find this exact block (lines 76-84):

```python
# Post-deliberation implementation instruction appended to full_prompt for all
# consilium_* modes. The skill intentionally skips Step 7 in headless mode
# (CLAUDE_HEADLESS=1); this suffix re-anchors the model to write output files
# after the deliberation workflow completes.
CONSILIUM_SUFFIX = (
    "\n\nIMPORTANT — POST-DELIBERATION STEP: After the consilium deliberation "
    "workflow is complete (after Step 6/7), immediately implement the "
    "chosen_approach. Write all required output files to the current working "
    "directory: solution.py for code tasks, or answer.md containing a line "
    "'ANSWER: <letter>' for reasoning tasks. The task is NOT complete until "
    "the output files exist on disk."
)
```

Replace with:

```python
# CONSILIUM_SUFFIX removed (2026-05-18) — Step 6.5 in Consilium SKILL.md now
# enforces deliverable writes for any prompt that declares files (benchmark or
# not), with verify-then-emit gate. Keeping the suffix here would duplicate the
# contract across two sources of truth.
```

- [ ] **Step 2.2: Remove suffix append in main**

Find this exact block (around line 519):

```python
    if args.mode.startswith("consilium_") and not args.manual:
        os.environ["CLAUDE_HEADLESS"] = "1"
        full_prompt += CONSILIUM_SUFFIX
```

Replace with:

```python
    if args.mode.startswith("consilium_") and not args.manual:
        os.environ["CLAUDE_HEADLESS"] = "1"
        # Step 6.5 in Consilium SKILL.md handles deliverable enforcement.
```

- [ ] **Step 2.3: Verify no remaining references**

```bash
grep -n "CONSILIUM_SUFFIX" /c/Users/ALEX/Desktop/Doc/benchmark-modes/run_task.py
```
Expected: zero matches.

Also check Python still parses:
```bash
python -c "import ast; ast.parse(open(r'C:\Users\ALEX\Desktop\Doc\benchmark-modes\run_task.py', encoding='utf-8').read())"
```
Expected: silent (exit 0).

---

### Task 3: T1 — warmup regression test (priority 1)

**Files:**
- Test: `C:\Users\ALEX\Desktop\Doc\benchmark-modes\workspace\consilium_sequential\code\00_warmup\`

- [ ] **Step 3.1: Run benchmark**

```powershell
cd C:\Users\ALEX\Desktop\Doc\benchmark-modes
python run_task.py --mode consilium_sequential --task code/00_warmup --clean
```

Wait time: ~4-6 min wall-clock. Cost: ~$0.7-$1.5.

- [ ] **Step 3.2: Verify solution.py exists on disk**

```bash
ls -la /c/Users/ALEX/Desktop/Doc/benchmark-modes/workspace/consilium_sequential/code/00_warmup/solution.py
```
Expected: file exists, non-empty.

- [ ] **Step 3.3: Check pytest report**

```bash
cat /c/Users/ALEX/Desktop/Doc/benchmark-modes/workspace/consilium_sequential/code/00_warmup/verify/report.json
```
Expected JSON contents:
- `"ok": true`
- `"kind": "pytest"`
- `"passed": 8`
- `"total": 8`
- `"score": 60`

- [ ] **Step 3.4: Decision gate**

If `passed < 8`:
- **STOP** — design hypothesis #3 (textual rule sufficient) is invalidated. Mark consilium outcome as BAD via `mark_outcome.py`, revert changes (`git checkout main -- SKILL.md`), reconsider approach. Do NOT continue to Task 4.

If `passed == 8`:
- Proceed to Task 4.

---

### Task 4: T2 — car_wash outlier test (priority 1)

**Files:**
- Test: `C:\Users\ALEX\Desktop\Doc\benchmark-modes\workspace\consilium_sequential\reasoning\01_car_wash\`

This is the riskiest test — `01_car_wash.md` uses inline phrasing (`save the same response to a file \`answer.md\``) rather than the `**Required output files**` header. Validates behavioral trigger across the outlier format.

- [ ] **Step 4.1: Run benchmark**

```powershell
cd C:\Users\ALEX\Desktop\Doc\benchmark-modes
python run_task.py --mode consilium_sequential --task reasoning/01_car_wash --clean
```

Wait time: ~5-8 min. Cost: ~$0.7-$1.5.

- [ ] **Step 4.2: Verify answer.md exists**

```bash
ls -la /c/Users/ALEX/Desktop/Doc/benchmark-modes/workspace/consilium_sequential/reasoning/01_car_wash/answer.md
```
Expected: file exists, non-empty.

- [ ] **Step 4.3: Check first non-empty line**

```bash
grep -m 1 "^ANSWER:" /c/Users/ALEX/Desktop/Doc/benchmark-modes/workspace/consilium_sequential/reasoning/01_car_wash/answer.md
```
Expected: `ANSWER: C` (per project memory `project_p3_correct_answer.md`).

Note: model may reach a different conclusion than C (that's a separate reasoning-quality issue). For T2, the gate is **structural**: `answer.md` exists with valid `ANSWER: <letter>` shape. Reasoning correctness is verified separately via `verify/report.json`.

- [ ] **Step 4.4: Check closed_answer report**

```bash
cat /c/Users/ALEX/Desktop/Doc/benchmark-modes/workspace/consilium_sequential/reasoning/01_car_wash/verify/report.json
```
Expected JSON:
- `"ok": true`
- `"kind": "closed_answer"`
- `"extracted"` is a single letter (A/B/C/D)

- [ ] **Step 4.5: Decision gate**

If `report.json.ok == false` (no `ANSWER:` line found):
- **STOP** — behavioral trigger missed the inline-phrasing case. Two recovery paths:
  - (a) revise Step 6.5 to add explicit `"save to <file>"` pattern recognition language
  - (b) accept outlier as known limitation; document in spec; proceed with rest of plan
- Discuss with user before deciding.

If `report.json.ok == true`:
- Proceed to Task 5.

---

### Task 5: T3 — no-op verification on non-deliverable prompt (priority 2)

**Files:**
- No file changes; this is a behavioral check.

This validates that Step 6.5 is truly opt-in — does NOT write spurious files when the user's prompt has no deliverable contract.

- [ ] **Step 5.1: Confirm via structural read**

Read the just-written Step 6.5 in `SKILL.md`. Confirm the section `"Nu se aplică dacă:"` includes the clause `"Promptul nu declară niciun deliverable"`. The no-op behavior is structurally guaranteed by the rule's own text.

- [ ] **Step 5.2: (optional) Run interactive smoke**

In a SEPARATE Claude Code session (not this one — it's already mid-implementation), invoke `/consilium` on a trivial diff request like "review this 1-line typo fix". Confirm closing line emits normally and zero `Write` calls happen.

Skip Step 5.2 if cost/time is a concern — structural read in Step 5.1 is sufficient evidence.

- [ ] **Step 5.3: Decision gate**

If Step 5.2 ran and produced spurious Write: **STOP** and revisit rule wording.
Otherwise: proceed to Task 6.

---

### Task 6: T5 — do_nothing short-circuit (priority 3, OPTIONAL)

**Files:**
- No file changes; structural check only.

- [ ] **Step 6.1: Confirm via structural read**

Re-read Step 6.5 in `SKILL.md`. Confirm the `"Nu se aplică dacă:"` block includes `chosen_approach ∈ {"do_nothing", "skipped"}`.

The do_nothing skip is enforced by the rule text itself — same mechanism as Step 7's existing skip (per `SKILL.md:233`). No experimental run needed unless explicitly requested.

- [ ] **Step 6.2: (skipped by default)**

Empirical smoke would require an artificial prompt with declared file + chosen_approach=do_nothing, plus a benchmark run. Cost-benefit doesn't justify. Skip unless user requests.

---

### Task 7: Cross-mode sweep (priority 3, OPTIONAL)

**Files:**
- Test workspaces for 12 combinations.

- [ ] **Step 7.1: Decision gate**

Discuss with user: this is a ~$5-10 sweep (3 modes × 4 tasks). Recommended only if:
- T1 + T2 both passed cleanly
- User wants confidence that fix generalizes to trias / dialectic modes too

If user declines: skip Task 7, proceed to Task 8.

- [ ] **Step 7.2: Run sweep (if approved)**

```powershell
cd C:\Users\ALEX\Desktop\Doc\benchmark-modes
foreach ($mode in 'consilium_sequential','consilium_trias','consilium_dialectic') {
  foreach ($task in 'code/00_warmup','code/01_circuit_breaker','reasoning/01_car_wash','reasoning/02_sprint_collapse') {
    python run_task.py --mode $mode --task $task --clean
  }
}
```

Wait time: ~60-90 min wall-clock total.

- [ ] **Step 7.3: Spot-check each run**

For each of the 12 workspace folders, verify the declared deliverable exists on disk. Tabulate pass/fail.

---

### Task 8: Final commit + push

**Files:**
- All modifications staged via `git add`.

Per CLAUDE.md project git workflow:
- Single commit per branch
- Push automat după commit (no asking)
- Push o singură dată
- `git checkout main` after push
- User creates PR manually

- [ ] **Step 8.1: Confirm branch state**

```bash
cd /c/Users/ALEX/Desktop/Doc/Consilium
git branch --show-current
```
Expected: `feat/deliverable-enforcement`

- [ ] **Step 8.2: Review changes**

```bash
git status
git diff
```
Expected file list:
- `SKILL.md` modified
- `docs/superpowers/specs/2026-05-18-deliverable-enforcement-design.md` (new file)
- `docs/superpowers/plans/2026-05-18-deliverable-enforcement.md` (new file)

The Consilium run report (`runs/2026-05-18_2012_*.json`) is gitignored — does not appear in `git status`.

For `benchmark-modes/run_task.py` — this is in a SEPARATE repo (`C:\Users\ALEX\Desktop\Doc\benchmark-modes`). Check:
```bash
cd /c/Users/ALEX/Desktop/Doc/benchmark-modes
git status
git diff run_task.py
```
Expected: `run_task.py` modified (CONSILIUM_SUFFIX removed).

- [ ] **Step 8.3: Decision — commit strategy**

The change spans TWO repos:
- `Consilium/` (SKILL.md, spec, plan)
- `benchmark-modes/` (run_task.py)

Per CLAUDE.md, single commit + push applies to the Consilium repo. Decide:
- **Option A:** Commit + push only in Consilium. Manually inform user that benchmark-modes also has uncommitted edits requiring separate workflow.
- **Option B:** Commit + push in both repos sequentially.

Recommended: **Option A** — CLAUDE.md project rules are written for Consilium; benchmark-modes has its own workflow. Ask user before touching benchmark-modes git.

- [ ] **Step 8.4: Stage Consilium changes**

```bash
cd /c/Users/ALEX/Desktop/Doc/Consilium
git add SKILL.md
git add docs/superpowers/specs/2026-05-18-deliverable-enforcement-design.md
git add docs/superpowers/plans/2026-05-18-deliverable-enforcement.md
git status
```
Expected: only the 3 files staged. NO other tracked-file modifications staged.

- [ ] **Step 8.5: Commit**

Per CLAUDE.md project memory `feedback_no_claude_coauthor.md`: omit `Co-Authored-By: Claude ...` line.

```bash
git commit -m "feat(skill): add Step 6.5 deliverable contract enforcement

Step 6.5 in SKILL.md forces models to write declared deliverable files
to disk via verify-then-emit gate before emitting the closing deliberation
line. Triggers on any prompt that declares files (header or inline phrasing);
no-op when no contract is present. Enables benchmark harness to remove its
duplicated CONSILIUM_SUFFIX in run_task.py (separate repo).

Spec: docs/superpowers/specs/2026-05-18-deliverable-enforcement-design.md
Consilium audit: runs/2026-05-18_2012_skill-step-6-5-deliverable-enforcement.json (conf 0.78)
Failure mode addressed: workspace/consilium_sequential/code/00_warmup/RESULT.md (0/60 → expected 60/60)"
```

- [ ] **Step 8.6: Push branch**

```bash
git push -u origin feat/deliverable-enforcement
```
Expected: branch published; PR creation URL returned.

- [ ] **Step 8.7: Return to main**

```bash
git checkout main
```

- [ ] **Step 8.8: Decide on benchmark-modes edit**

Ask user: commit `run_task.py` edit in `benchmark-modes` repo now (same workflow rules), or defer to user-managed commit?

- [ ] **Step 8.9: Report to user**

Final report:
- Branch: `feat/deliverable-enforcement` pushed; PR creation pending (manual)
- T1 result: PASS / FAIL
- T2 result: PASS / FAIL (or partial — answer letter)
- Outstanding: `benchmark-modes/run_task.py` edit (separate repo, awaiting user direction)
- Spec + plan + Consilium audit run all linked in commit message

---

## Self-review check

**Spec coverage:**
- ✓ Section 1 (Step 6.5 textual rule) → Task 1
- ✓ Section 2 (CONSILIUM_SUFFIX cleanup) → Task 2
- ✓ Section 5 T1 → Task 3
- ✓ Section 5 T2 → Task 4
- ✓ Section 5 T3 → Task 5
- ✓ Section 5 T4 (cross-mode sweep) → Task 7
- ✓ Section 5 T5 (do_nothing skip) → Task 6
- ✓ Section 5 "Self-improvement loop obligatoriu" → already done pre-implementation (consilium run `2026-05-18_2012_*.json`)

**Placeholder scan:** No TBD / TODO / "implement later" / "add appropriate error handling" present. Each step has either an exact command, an exact text block to insert, or a structural read instruction.

**Type consistency:** N/A (no types defined — Markdown + Python edits only).

**Risks called out per task:** Task 3 + Task 4 have explicit decision gates with stop conditions; Task 7 has user-decision gate; Task 8 has cross-repo commit-strategy decision gate.
