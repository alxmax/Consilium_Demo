# TODO — single source Consilium (consolidated 2026-05-17)

> All TODOs + repo bugs in a single file.
> Consolidated from: `TODO.md` (old), `TO_DO_Consilium.md` (prompts/skill audit), `BUGS.md` (audit 2026-05-16, 107 findings, previously gitignored).
>
> The reference document `experiments/New phase senat/todos/SENAT-todo-rol-legi-functii.md` remains as conceptual specification (not an actionable TODO).

## Table of Contents

1. [❌ NOT IMPLEMENTED](#-not-implemented)
2. [🤔 UNRESOLVED DECISIONS](#-unresolved-decisions)
3. [📋 POST-MERGE VALIDATION](#-post-merge-validation)
4. [🔧 Prompts & skill audit (TO_DO_Consilium #2-#53)](#-prompts--skill-audit)
5. [🐞 Bugs (107 from audit 2026-05-16)](#-bugs)
6. [🏛 Senate Resolutions](#-senate-resolutions)
7. [Rollback hooks](#rollback-hooks)

---

## ❌ NOT IMPLEMENTED

### Investigate: senate_transcript.py — deprecated but still called — INVESTIGATE

> **Status:** INVESTIGATE (2026-05-17, discovered while generating transcripts for the Senate top-5 diagnostic audit).

- [ ] `scripts/deprecated/senate_transcript.py` is marked as deprecated but **actively called** by `scripts/senate_synth.py:595` (`_generate_transcript()` via `importlib.util.spec_from_file_location`).
- [ ] The bundle schema it renders is the legacy single-round one `{senators: {...}, vote_counts: ...}`. On non-standard bundles (e.g. diagnostic audit with schema `{top_5: [...], honorable_mentions: [...]}`) it works only partially — produces shorter HTML without votes.
- [ ] **To decide:** (a) re-promote `senate_transcript.py` from `scripts/deprecated/` to `scripts/` (clarifies the real status); OR (b) inline the generation into `senate_synth.py` and delete the file; OR (c) extend it to support the diagnostic schema (top_5 + honorable_mentions) as a first-class option.
- [ ] Falls out naturally from the Musk HM5 audit (dual-schema path in senate_synth.py) — same theme: shims retained after migrations, with no explicit cleanup.
- [ ] Found: 2026-05-17, post Senate top-5 diagnostic audit (the session that manually generated `runs/senate/transcripts/2026-05-17/top5-diagnostic-audit.html` via `python -c "import senate_transcript; ..."`).

### Usage & Efficiency reporting — IN PROGRESS

> **Status:** Senate deliberation 2026-05-17 (`efficiency-py-design-decisions`) resolved all 4 open questions. Design in `experiments/usage-efficiency-proposal-pending.md`.
>
> **Senate-confirmed decisions (bundle `runs/senate/2026-05-17_194232-efficiency-py-design-decisions.json`):**
> - Q1: Binary gate — FEEDBACK outcome=OK → OK, anything else → excluded from OK_count
> - Q2: Raw sum (tokens_in + tokens_out); output also includes `tokens_per_dispatch` (normalized, per Socrate)
> - Q3: Flat Trias schema: `{pioneer_generator, architect_control, ...}`
> - Q4: `--self-test` flag in efficiency.py + `--feedback`/`--runs` CLI overrides (not a run_evals.py scenario)

- [ ] **Token capture (orchestrator):** emit `telemetry` at every run (chars/4 over the full prompt — proposal + persona + context, not just proposal). Affects cross-mode accuracy.
- [ ] **SKILL.md Step 6c:** mandatory telemetry emission discipline after each run.
- [ ] **UI tab:** "Usage & Efficiency" tab in `docs/architecture.html` with per-mode bar chart.

### Philosophical voice variants — REMAINING

> **Status (audit 2026-05-17 via /consilium):** PR #62 (`c358484`) delivered 3 variants + script + tests. Wittgenstein and Aurelius (conservator) were absorbed into the core voices in RUND2.
>
> **Delivered** (no longer TODO): `prompts/control_aurelius.md`, `prompts/conservator_confucius.md`, `prompts/refiner_deletion.md`, `scripts/precedent_search.py`, `scripts/test_philosophical_voices.py` (27 tests PASS), `validate_report.py --strict-philosophical={aurelius-control,confucius}`.

---

## 🤔 UNRESOLVED DECISIONS

From `TODO_RUND2.md` Appendix D — personal decisions that do not block current implementation:

- [ ] **[SENATE] Consilium as a deliberation + implementation tool** — In the benchmark context, Consilium deliberates but does not implement. Temporary fix: Step 7 `implement` extended (2026-05-18) to write files when the prompt declares `**Required output files**`. Unresolved architecture decision: do we want Consilium to be a *pure deliberation* tool (verdict + report → implementer decides) or a *deliberation + implementation* tool (verdict → Consilium writes the code)? Implications: (1) if implementation is in-scope, who decides where files get written in non-benchmark contexts? (2) the `implement` step becomes a blocking operation (Write tool), not an advisory reminder. To be discussed in Senate before extending scope beyond the current benchmark fix.

- [ ] **Veto budget for `meta_recommendation`: is 5/month acceptable?** Aurelius+Napoleon proposed it, but the number is arbitrary. You might prefer 10 or 3.
- [ ] **Outcome tracking — manual or automatic?** For trading it can be automatic from MT4. For other domains it requires manual completion. If not, `principle_extraction` never activates.
From `TODO_SENAT.md` Appendix D:

- [ ] **Future senators (slot 8 and 9)** — decide when candidates appear. Rules: the P3 test, non-overlapping specialty >50%, audit by the existing Senate before adding.
- [ ] **Reduce Senate from 7 to 6 if it seems too expensive after 5-10 invocations?**

---

## 📋 POST-MERGE VALIDATION

Empirical pendings after the RUND2 merge (PR #59 — `2026-05-16`):

- [ ] **14A — Napoleon validation** on 5-10 diverse questions (operational + philosophical + ambiguous). Check for P3 over-fit.
- [ ] **14B — Sequential dispatch validation**: does it produce better calibration than the old parallel on 10 real questions?
- [ ] **14C — Aggregator decisions validation**: pattern detection on vetoes in the first 30 runs.
- [ ] **14D — Generate `experiments/run4-rund2-empirical-validation.html`**

---

## 🔧 Prompts & skill audit

> Source: `TO_DO_Consilium.md` (now consolidated). Items numbered #2-#53. Ranked by impact/effort. Categories: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch**.

### Batch status

- **#1, #16, #17, #20 dropped** after Consilium triage (`runs/2026-05-15_2236_todo-triage.json`).
- **#9, #18 INVESTIGATE** (user, kept for later decision).
- **#2-#8 ✅ DONE** (discovered implemented during the Branches 1-5 audit).
- **#13-#15, #19 ✅ DONE** (branch `feat/feedback-and-quality-loop`).
- **#36-#38 ✅ DONE** (branch `fix/audit-flow-modes-top3`).
- **#51-#53 ✅ DONE** (P3 corrigendum lessons).

### Follow-up eval parity (planned after parallel-review 0.57 conf)

Branch `feat/eval-parity-rest` with scenarios for:
- `memory.py` tier medium/long/unknown (3 scenarios — require `runs/` fixtures)
- `audit_feedback.py` orphan detection + `--backfill` idempotency (2 scenarios — require FEEDBACK.html + runs/*.json fixtures)
- `mark_outcome.py` `[confirmed]` marker preservation (1 scenario — requires FEEDBACK.html fixture)
- `priors.py` `weighted_bad_rate` + `missing_feedback_runs` + `stale_pendings` cutoff (3 scenarios)

Total ~9 new scenarios. Requires extending `run_evals.py` to accept filesystem fixtures.

### Open items (Tier 2)

> **Status update 2026-05-19:** 8 items closed in main (#31, #32, #35, #39, #40, #41, #42, #44):
> - #31 `VOTE_PATTERN_CONFIDENCE`: `confidence.py:102-105` — veto (`2-0`) scores 0.70 < dissent (`2-1`) 0.75 (veto = stronger risk signal → lower confidence). Already in correct order.
> - #32 `_TRIAS_EXPECTED_NAMES` dedup: `validate_report.py:52` imports `NAMES` from `personalities`.
> - #35 Issue severity: `build_report.py:82` + `dialectic_merge.py:88` both use `utils.issue_penalty` (severity-weighted 0.05/0.15/0.30).
> - #39 scope_gate `secrets` glob: pattern is `**/*secrets*` (matches `with-secrets/foo`).
> - #40 `telemetry.voices` empty: `validate_report._validate_telemetry_required:289-296` returns a problem (error) for multi-voice modes when voices empty.
> - #41 `team_vote` deterministic tie-break: `aggregator.py:258` raises `ValueError` on tie.
> - #42 `signals.files_changed=None` type-safe: `scope_gate.py:213` emits `-1` instead of `None` under `CONSILIUM_FORCE_FULL=1`.
> - #44 Chinese-wall illusion in Sequential: documented in `SKILL.md:755` AND `docs/architecture.html:744` (the `<div class="use-when">` caveat block) — both explicit that "role separation, not Chinese wall."
>
> Remaining Open items (Medium effort or INVESTIGATE-class): #9, #18, #27, #28, #43, #45, #46.

#### 9. Goal-fit check moved to step 1 in Control · Prompt · Medium · Small-Medium · INVESTIGATE
Currently Control runs types → logic → tests → style → goal-fit. If the candidate doesn't address success_criterion, the first 4 checks are wasted. Fix: move goal-fit to **step 0** in Task, before types. Fail fast.

#### 18. Observe → Think → Act → Learn formal loop · Arch · Medium · Very Large · INVESTIGATE
The skeleton already exists implicitly (Step 1 = Observe, Steps 2-4 = Think, Step 5 = Act, Step 6 = Learn). Formalizing it would enable restart, enrichment, conditional skips. Risk: Consilium becomes agentic and non-deterministic — contradicts Principle 2 (Simplicity first). Only implement if the meta-controller (16, dropped) is already stable.

### Open items — Voice audit (Trias + parallel-skeptic, session 2026-05-16)

> Source: `runs/2026-05-16_0148_voice_audit_meta.json` (synthesis of 2 sub-agents, Trias 3-0 unanimous + parallel-skeptic confirms).

#### 27. `confidence_in_verdict` field in Control + meta_critic flag · Prompt+Skill · Low · Medium
`control.md:9` requires "verify, don't speculate" but Control receives only sketches. Speculation passes silently. Fix: add `confidence_in_verdict: high|medium|low` in the verdict schema; meta_critic flags any `valid:true + confidence_in_verdict:low` as a warning.

#### 28. New meta_critic metrics — `pass2_revision_quality` + `personalities_divergence` · Skill · Low · Medium
Two gaps in meta_critic.py:
- Does not audit dialectic Pass-2 — `peer_evidence` may be boilerplate.
- Does not measure whether Trias lenses actually produce divergence.

Fix:
- `pass2_revision_quality`: require `peer_evidence` >20 chars and no match with a boilerplate list.
- `personalities_divergence` (Trias-only): advisory flag when all 3 personalities converge.

### Open items — Flow models audit

#### 31. VOTE_PATTERN_CONFIDENCE counterintuitive ordering · Skill · Small · Small
`2-0` (total veto from one personality) gets 0.75 confidence, `2-1` (active dissent) gets 0.70. Veto is a more serious signal.

#### 32. Deduplicate _TRIAS_EXPECTED_NAMES · Skill · Small · Small
`validate_report.py:161` and `personalities.py:21-37` duplicate the list. Fix: import from `personalities.NAMES`.

#### 35. Use issue severity in `_voice_score_from_verdict` · Skill · Medium · Small
`dialectic_merge.py:88` and `build_report.py:70` subtract 0.15 per issue regardless of severity. Fix: weight `0.05 / 0.15 / 0.30` for `severity: low/medium/high`.

#### 39. scope_gate blocklist extends for `*secrets*` folder · Skill · Small · Trivial
`**/secrets*` matches `secrets.json` but not `with-secrets/foo`. Add `**/*secrets*`.

#### 40. telemetry.voices empty in Parallel → error (not warning) · Skill · Medium · Trivial
`validate_report.py:146-154` only emits a warning. A parallel orchestrator that forgets to capture telemetry passes the gate → `usage.py` skips the run.

#### 41. Deterministic tie-break on `team_vote` duplicate top · Skill · Small · Trivial
`aggregator.py:277-280` uses `for ... break` on a dict — non-deterministic. Add explicit `raise ValueError`.

#### 42. `signals.files_changed = None` on `CONSILIUM_FORCE_FULL=1` type-safe · Skill · Small · Trivial
`scope_gate.py:212-213` emits `None` for numerics. Fix: emit `-1` or omit the fields.

#### 43. Iterative Dialectic — SPEC without implementation · Arch · Medium · Large
`docs/architecture.html` describes the iterative mode with N=1..3 rounds + convergence stop, marked `SPEC`. `dialectic_merge.py` strictly accepts `{pass1, pass2}`. Fix: either implement the schema `{rounds: [...]}` with convergence detection, or delete the mode from the HTML.

#### 44. Illusory Sequential "Chinese wall" — clarify in HTML docs · Arch · Medium · Small
Sequential runs the same LLM playing 3 roles in the same context. `strip_context.py` only cleans the prompt. Not a real Chinese wall. Fix: explicit note in `docs/architecture.html` (SKILL.md already updated).

#### 45. End-to-end lens injection validation · Skill · Medium · Medium
`prompts/<personality>_lens.md` are arbitrary files. No test that Pioneer is progress-leaning vs Steward risk-averse. Fix: eval scenario that runs a diff with a conservator-vs-progress trade-off.

#### 46. Generator Pass-2 candidate semantic diff in `revision_log` · Skill · Small · Medium
`dialectic_merge._diff_candidates` lists `fields: ["sketch", "summary"]` as "modified" but does not emit a proper diff. Fix: include before/after payload per field in `revision_log.diffs`.

### Open items — LangGraph/LangChain integration audit

> Source: `runs/2026-05-16_1430_audit_langgraph_langchain.json` (parallel mode, chosen=`do_nothing` conf=0.36 PEND).
> The audit rejected deep integration: veto on full rewrite (risk 0.95), invalid on LangChain output parsers, invalid on topology-only.

#### 47. `optional_sidecar_visualizer` — isolated `experiments/langgraph_replay/` · Arch · Medium · Medium · PROPOSED
Optional sidecar that visualizes `runs/*.json` post-hoc. No role in live deliberation, no imports from `scripts/`, isolated venv.

Mandatory contracts before ship:
1. `experiments/langgraph_replay/` stays gitignored or explicitly marked "not part of the skill"
2. `grep -r 'from scripts\|import scripts' experiments/` returns zero matches
3. `replay.py` defined output schema: Mermaid with at least one node per step from `deliberation_log`

#### 48. Analysis: per-step checkpoint between voices · Arch · Medium · Medium · INVESTIGATE
Currently `runs/<id>.json` is written once at Step 6. If Control crashes, we lose all Generator output.

Questions to explore:
- Partial `runs/<id>_partial.json` per voice or directory `runs/<id>/<voice>.json`?
- How does it interact with `audit_feedback.py`?
- Cost/benefit: how often do Control/Conservator fail?

Decision blocked until we have data.

#### 49. Analysis: streaming / human-in-the-loop between Generator and Control · Arch · Medium · Large · INVESTIGATE
After Generator, pause; user excludes/edits candidates before Control + Conservator see them.

Questions:
- Native Claude Code mechanism for pause + user input between sub-agent calls?
- How is intervention logged in `runs/*.json`?
- Conflict with Principle 1 (Think before coding)?

Decision blocked until we know pause/resume availability.

#### 50. Analysis: time-travel over `runs/*.json` · Skill · Small · Small-Medium · INVESTIGATE
`scripts/replay_aggregator.py` that reads a run, allows manual score editing, re-runs aggregator + confidence.

Questions:
- Output: new run or stdout?
- How does it interact with `validate_report.py`?

Soft-positive decision, low priority.

### Prompts & skill audit summary

| # | Title | Category | Impact | Effort |
|---|-------|-----------|--------|-------|
| 9 | Goal-fit → step 0 in Control (INVESTIGATE) | Prompt | Medium | Small-Medium |
| 18 | Observe→Think→Act→Learn formal (INVESTIGATE) | Arch | Medium | Very Large |
| 27 | confidence_in_verdict in Control | Prompt+Skill | Low | Medium |
| 28 | pass2_revision + personalities_divergence metrics | Skill | Low | Medium |
| 31 | VOTE_PATTERN_CONFIDENCE reorder | Skill | Small | Small |
| 32 | Deduplicate _TRIAS_EXPECTED_NAMES | Skill | Small | Small |
| 35 | Severity-aware control score | Skill | Medium | Small |
| 43 | Iterative Dialectic — SPEC without implementation | Arch | Medium | Large |
| 44 | Sequential Chinese wall — clarify HTML docs | Arch | Medium | Small |
| 45 | End-to-end lens injection validation | Skill | Medium | Medium |
| 46 | Pass-2 semantic diff in revision_log | Skill | Small | Medium |
| 47 | `optional_sidecar_visualizer` PROPOSED | Arch | Medium | Medium |
| 48 | Per-step checkpoint between voices INVESTIGATE | Arch | Medium | Medium |
| 49 | Streaming / HITL Generator↔Control INVESTIGATE | Arch | Medium | Large |
| 50 | Time-travel over runs/ INVESTIGATE | Skill | Small | Small-Medium |

---

## 🐞 Bugs

> Source: `BUGS.md` (audit 2026-05-16, 4 parallel sub-agents × 2 waves). Previously gitignored — promoted into TODO.md as single source.
> **Method:** Per file, 3-lens reasoning (Pioneer / Architect / Steward) inline. ≥2 lenses agreeing required.
> **Total:** 107 bugs · 4 critical · 12 high · 39 medium · 52 low.

### Tally

| Agent | Bucket | Wave 1 | Wave 2 | Total |
|---|---|---|---|---|
| 1 | Voting/decision (6 files) | 9 (0C/0H/2M/7L) | 11 (0C/0H/3M/8L) | **20** |
| 2 | Feedback/persistence (7 files) | FAILED (usage limit) | 21 (3C/3H/7M/8L) | **21** |
| 3 | Context/utility (10 files) | 17 (0C/1H/7M/9L) | 9 (0C/0H/3M/6L) | **26** |
| 4 | Prompts + docs (12 files) | 17 (0C/3H/6M/8L) | 23 (1C/5H/10M/7L) | **40** |
| **Total** | **35 files** | — | — | **107** |

### Highest-impact recommendations (fix-first)

1. **Atomic writes to FEEDBACK.html** — fixes 2 critical (`log_feedback.py:209`, `mark_outcome.py:173`) + medium-severity O(N²) backfill race window with a shared helper.
2. **VETO threshold alignment** (`render_feedback_html.py:211,217`) — fixes 1 critical; any historical drill-down lies about vetoes.
3. **Pass-2 verdict schema** (`control_pass2.md` + `dialectic_merge.py`) — fixes 1 critical; without this, Dialectic mode collapses to control_score=0.0.
4. **`dialectic_merge.py` null risk_score guard** (lines 217, 239) — 1 high; one-line defensive fix prevents whole-merge crash.
5. **Clarity gate prescription reconciliation** (SKILL.md / generator.md / consilium-subagent.md) — 1 high; three documents prescribe three different actions for the same trigger.
6. **Subagent doc audit** (`agents/consilium-subagent.md`) — 3 high concentrated here.

### Critical (4)

#### [scripts/log_feedback.py:209] FEEDBACK.html written non-atomically — crash mid-write corrupts long-term memory
- **Type:** error-handling · **Lenses:** steward, pioneer
- **Why:** `append_entry` re-renders the entire FEEDBACK.html and writes with single non-atomic `write_text`. Crash → truncated file → lost history.
- **Evidence:** `feedback_path.write_text(render_mod.render(entries, runs_dir), encoding="utf-8")`
- **Fix:** Write to `feedback_path.with_suffix(".html.tmp")` then `os.replace(tmp, feedback_path)`; optional `.html.bak` first.

#### [scripts/mark_outcome.py:173] FEEDBACK.html written non-atomically — same crash-corruption risk as log_feedback
- **Type:** error-handling · **Lenses:** steward
- **Why:** Identical hazard, more likely interactive (Step 6 retroactive correction).
- **Evidence:** `feedback_path.write_text(render_mod.render(entries, runs_dir), encoding="utf-8")`
- **Fix:** Share an atomic-write helper between `log_feedback`, `mark_outcome`, `audit_feedback`.

#### [scripts/render_feedback_html.py:211,217] Conservator drill-down marks candidates as VETOED at risk ≥ 0.7 — UI lies
- **Type:** logic · **Lenses:** architect, steward
- **Why:** `aggregator.py` defines `DEFAULT_VETO = 0.8` with `if risk > veto_threshold`. Renderer hard-codes `>= 0.7` → candidates in `[0.7, 0.8]` are shown "VETOED" although aggregator let them pass.
- **Fix:** Import `DEFAULT_VETO` from `aggregator` and use `> DEFAULT_VETO`. Better: derive `vetoed` from `aggregate_result.get("vetoed")`.

#### [prompts/control_pass2.md:43-62 vs dialectic_merge.py:202-216] Pass-2 verdict schema lacks `valid`/`issues` — merge silently computes control_score=0.0
- **Type:** schema-mismatch · **Lenses:** pioneer, architect, steward
- **Why:** control_pass2.md defines `{id, revision|maintained}` without `valid`, `issues`. dialectic_merge.merge() does `verdict.get("valid")` → falsy → `return 0.0`. The entire aggregation collapses.
- **Fix:** (a) require Pass-2 control verdicts to carry the full Pass-1 verdict shape PLUS revision/maintained, or (b) change `dialectic_merge.py` to fetch `valid`/`issues` from Pass-1.

### High (12)

#### [scripts/log_feedback.py:162-209] No deduplication / no concurrency lock — re-runs silently duplicate rows
- **Type:** concurrency · **Lenses:** steward, architect
- **Fix:** Fingerprint-based dedup + OS-level file lock (`msvcrt.locking` Windows / `fcntl.flock` POSIX).

#### [scripts/audit_feedback.py:95-117 + priors.py:127-148] `--backfill` silently skips runs colliding by (date, chosen[:40])
- **Type:** logic · **Lenses:** architect, steward
- **Fix:** Use `run_path` as matching key when available; fallback to `(date, chosen, context_hash)`.

#### [scripts/migrate_feedback_md_to_html.py:51-72] Fuzzy match accepts zero-overlap candidates
- **Type:** logic · **Lenses:** architect, steward
- **Fix:** Return `None` when `candidates[0][0] == 0`, or minimum threshold ≥ 2 tokens.

#### [scripts/dialectic_merge.py:217,239] `float(risk_entry.get("risk_score", 0.5))` crashes on null risk_score
- **Type:** type / error-handling · **Lenses:** architect, steward
- **Fix:** `rs = risk_entry.get("risk_score"); rs = 0.5 if rs is None else float(rs)`

#### [SKILL.md:71 vs prompts/generator.md:38-40] SKILL.md missing `unconventional_*` requirement and `unconventional_skipped` sibling
- **Type:** instruction-conflict · **Lenses:** architect, steward
- **Fix:** Add to SKILL.md Step 2 a sentence about unconventional being required by default with `unconventional_skipped` opt-out.

#### [prompts/control.md:29] Goal-fit fallback id `_no_viable_candidate` — aggregator/build_report doesn't know this synthetic id
- **Type:** schema-mismatch · **Lenses:** pioneer, architect, steward
- **Fix:** Drop fallback from control.md (aggregator handles total veto), OR document that `_no_viable_candidate` must be added as a Generator candidate.

#### [prompts/skeptic.md:38-51 vs SKILL.md:336-342] Skeptic output schema lacks formal validator
- **Type:** missing-field · **Lenses:** pioneer, architect, steward
- **Fix:** (a) implement `validate_skeptic.py`, OR (b) rewrite skeptic.md "Validation gate" as orchestrator-side check.

#### [prompts/control_pass2.md:33 + control.md:31] Revised valid:true verdict has no slot for `tests_to_write`
- **Type:** missing-field · **Lenses:** architect, steward
- **Fix:** Add to control_pass2.md: if a revision flips `valid: false → true` for any candidate other than `do_nothing`, emit the full Pass-1 verdict shape in addition to `revision` metadata.

#### [prompts/pioneer_lens.md:9-15 vs conservator.md:7] Pioneer lens "tolerate moderate risk" conflicts with Conservator's `risk_score` mandate
- **Type:** instruction-conflict · **Lenses:** pioneer, architect, steward
- **Fix:** Restrict lens prepending to Generator only (change personalities.py `lens_applies_to: ["generator"]`), OR per-voice carve-outs.

#### [agents/consilium-subagent.md:33 vs SKILL.md:236-247] Subagent "Sequential mode only" but SKILL.md says default is parallel
- **Type:** instruction-conflict · **Lenses:** pioneer, architect, steward
- **Fix:** Update consilium-subagent.md description: "...returns canonical runs/<file>.json report. **Note: runs Sequential mode**".

#### [agents/consilium-subagent.md:6] Tools list missing `Write` — persistence relies on shell redirect (brittle on Windows)
- **Type:** schema-mismatch · **Lenses:** pioneer, architect
- **Fix:** Add `Write` to tools list (scope to `runs/` only), OR document the Windows-encoding gotcha and prescribe `python -X utf8`.

#### [SKILL.md:48 vs generator.md:31 vs consilium-subagent.md:37] Clarity gate has 3 incompatible prescriptions
- **Type:** instruction-conflict · **Lenses:** pioneer, architect, steward
- **Why:** Same trigger, three docs, three actions:
  1. SKILL.md L48: stop and ask user
  2. generator.md L31-35: emit `adversarial_*`
  3. consilium-subagent.md L37: emit `interp_a_*`, `interp_b_*`
- **Fix:** Reconcile: distinguish "ambiguity Generator can disambiguate" from "ambiguity requiring user input".

### Medium (39)

#### [scripts/aggregator.py:54-67] `aggregate_majority` sort crashes with TypeError on (mean, -stdev) tie
- **Lenses:** architect, pioneer, steward · **Fix:** Insert stable tiebreaker before `c` (enumerate index). Same exposure in `aggregate_weighted` (line 97).

#### [scripts/build_report.py:64-75] `_voice_scores_for` silently zeros control_score when chosen has no verdict
- **Fix:** Raise/warn when `verdict == {}` after lookup, or surface missing-verdict as a distinct null/sentinel.

#### [scripts/build_report.py:215-222] `_default_reasoning` mislabels Trias fragmentation as "all candidates vetoed"
- **Fix:** Branch on `scheme == "team_vote"` + `vote_pattern`. Fragmentation: "deliberation fragmented (vote_pattern=…); orchestrator must intervene".

#### [scripts/validate_report.py:170-174] `_validate_trias` iterates fields on personality entry without verifying dict
- **Fix:** `if not isinstance(p, dict): errors.append(...); continue`.

#### [scripts/validate_report.py:138-155] `_validate_telemetry_required` only enforces voices for "parallel" mode, not Trias
- **Fix:** `mode in ("parallel", "trias", "dialectic", "trias_split", "parallel_skeptic", "dialectic_skeptic")`.

#### [scripts/log_feedback.py:188,205-206] Fingerprint truncates context to 30 chars — distinct deliberations share drill-down run_path
- **Fix:** Include full context (or `run_path`) in fingerprint, or key sidecar map by `run_path` directly.

#### [scripts/log_feedback.py:146] OVR outcome with missing --override-target produces silent no-op
- **Fix:** Raise `ValueError("--outcome OVR requires --override-target <alt_id>")`.

#### [scripts/mark_outcome.py:83-91] `_annotate_note` not idempotent — duplicates `outcome_reason=` entries
- **Fix:** Filter existing `outcome_reason=` parts before appending.

#### [scripts/audit_feedback.py:116] Backfill performs N full read-render-write cycles — O(N²) work
- **Fix:** Batch backfill — accumulate Entry objects, render and write ONCE atomically.

#### [scripts/render_feedback_html.py:258-261] JSONDecodeError silently downgraded to "no detailed run data"
- **Fix:** Render dedicated `<div class="stub error">corrupted run JSON: <name></div>`.

#### [scripts/migrate_feedback_md_to_html.py:30] TOKEN_RE is ASCII-only — Romanian diacritics never tokenize
- **Fix:** `re.compile(r"[^\W\d_]{4,}", re.UNICODE)`.

#### [scripts/test_feedback_html.py:61-87] Test depends on tracked run file — couples tests to mutable session data
- **Fix:** Create temp directory with synthetic run JSON.

#### [scripts/test_feedback_html.py:1-225] Coverage gaps — no tests for log_feedback dedup, mark_outcome, audit_feedback, sidecar map
- **Fix:** Add dedup test, sidecar map round-trip, mark_outcome and audit_feedback happy-path.

#### [scripts/scope_gate.py:192-220] CONSILIUM_FORCE_FULL overridden by config load failure
- **Fix:** Move env override check to top of `main()`, before `load_config`.

#### [scripts/priors.py:197-203] `find_stale_pendings` surfaces entries with empty/missing dates
- **Fix:** Positive guard: `... and e.get("date", "") and e["date"] < cutoff`.

#### [scripts/dialectic_merge.py:124-126] `validate_input` strictly requires all 3 voices in pass1 (uses `sys.exit`)
- **Fix:** Tolerate missing voices as `{}` in `merge()`, or raise instead of `sys.exit`.

#### [scripts/run_evals.py:49-55] `subprocess.run(text=True)` uses platform encoding for stdin/stdout
- **Fix:** Pass `encoding="utf-8"` and `PYTHONIOENCODING=utf-8` in `env=`.

#### [scripts/utils.py:50-65] `validate_keys` calls `sys.exit(1)` — fatal for in-process callers
- **Fix:** Raise `ValidationError`; convert to exit code only in `main()` wrappers.

#### [scripts/probe_change.py:60-84] `parse_numstat` mis-handles rename syntax `{old => new}`
- **Fix:** Pass `--no-renames` to `git diff --numstat`, or parse and expand.

#### [scripts/dialectic_merge.py:122-126] `validate_input` accepts `pass2: [...]` (list) but `merge()` crashes
- **Fix:** `if "pass2" in payload and not isinstance(payload["pass2"], dict): exit/raise`.

#### [scripts/usage.py:96,120] Strict `isinstance(int)` silently drops `tokens_in: 5.0` (float JSON values)
- **Fix:** `isinstance(vdata[f], (int, float)) and not isinstance(vdata[f], bool)`.

#### [SKILL.md:108-110] Confidence input contract for null chosen says wrong thing
- **Fix:** Reword to "the `confidence` field in the response is `null`" + add "Step 5d is skipped in this case".

#### [SKILL.md:240 + Step 5 (parallel)] Parallel mode never mentions Step 5b/5c/5d before Step 6
- **Fix:** Add to Parallel section: "Continue with Step 5b → 6; capture tokens/latency per sub-agent dispatch".

#### [SKILL.md:286-294 (Trias workflow)] Workflow doesn't show JSON schema for Trias report
- **Fix:** Add an "Output JSON" mini-schema example in the Trias section.

#### [prompts/generator.md:47-74 Output format] Example JSON missing `adversarial_skipped` / `unconventional_skipped` siblings
- **Fix:** Add a second example: `{"candidates": [...], "adversarial_skipped": "goal unambiguous", "unconventional_skipped": "trivial doc fix"}`.

#### [prompts/conservator.md:39] Cumulative cap -0.20 vs quality-progress math doesn't add up
- **Fix:** "Apply up to two mitigations; cap total at -0.20. After mitigation 1 (-0.15), budget for mitigation 2 is -0.05 max." Mirror in pass2.

#### [prompts/generator_pass2.md] Pass-2 generator content shape ambiguous — missing summary/sketch/rationale
- **Fix:** Update generator_pass2.md to require full candidate fields (`summary`, `sketch`, `rationale`).

#### [prompts/control_pass2.md (entire)] Pass-2 schema has no escape hatch for `_no_viable_candidate` fallback
- **Fix:** Allow emission of new synthetic verdicts in Pass-2, OR drop the synthetic mechanism entirely.

#### [prompts/pioneer_lens.md/architect_lens.md/steward_lens.md vs SKILL.md] Lens prompts: no link from `voice_bias: prepended` to score-weighting
- **Fix:** Footer in each lens: "Your voice output will be re-weighted by the personality's aggregator weights — focus on perception-shift in your role."

#### [prompts/architect_lens.md:13 vs conservator.md L11] Architect lens "Weight test coverage heavily" overlaps with Control role
- **Fix:** Carve-out: "When applied to Conservator, 'test coverage' bias affects only the `regression_risk` quality-progress adjustment — do NOT inflate risk_score for absent tests."

#### [prompts/steward_lens.md:13 vs generator.md:9] Steward lens "Favor minimal-scope" suppresses Generator divergence
- **Fix:** Per-voice guidance: "When applied to Generator: still produce full 3-5 candidate spread, but order candidates with smaller-blast-radius first; do NOT suppress big-blast-radius candidates."

#### [agents/consilium-subagent.md:40 + 38] Final-message contract: "exactly that file's contents" but description adds extra top-level keys
- **Fix:** Define `subagent_notes` as an optional documented field in validate_report.py and SKILL.md.

#### [agents/consilium-subagent.md:38 vs SKILL.md:163-165] Step 6 confidence override delegated to "no --outcome flag" — different from SKILL.md null branch
- **Fix:** "Use `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json` with no `--outcome` for both confidence < 0.7 and null cases."

#### [agents/consilium-subagent.md:14-23] Working directory setup uses bash export — Windows PowerShell can't execute verbatim
- **Fix:** Add PowerShell alternative, or wrap in launcher.

#### [prompts/conservator.md:49 vs scripts/aggregator.py] "Matches aggregator.py's expectation" claim is false
- **Fix:** Reword: "There is no automated check that this rule was applied — keep it disciplined manually."

#### [SKILL.md:39 Bootstrap step] "Read the contracts of the 3 voices" enumerates only 3 — skeptic.md and lens prompts not bootstrapped
- **Fix:** Update Step 0: "Read the contracts required by the mode: minimum 3 core; Dialectic adds `*_pass2.md`; Trias adds `<personality>_lens.md`; skeptic modes add `skeptic.md`."

#### [prompts/generator.md:31 + 40] adversarial/unconventional rationale overlap silently disables anti-stagnation
- **Fix:** Tighten (a): "Skip unconventional ONLY when adversarial ALSO varies on a non-scope axis."

### Low (52)

#### [scripts/aggregator.py:148-156] `auto_relax` retry_suggested emits non-actionable suggestion when lowest_risk exceeds RELAXED_VETO_CAP
- **Fix:** Omit `retry_suggested` or replace with `escalation_required` when `lowest_risk > RELAXED_VETO_CAP`.

#### [scripts/aggregator.py:239-309] `aggregate_team_vote` hardcodes abstain reason, losing per-personality context
- **Fix:** `abstained.append({"name": p["name"], "reason": p.get("abstain_reason") or "all candidates vetoed"})`.

#### [scripts/build_report.py:114-131] `_alternatives` emits misleading why_not when chosen=None
- **Fix:** When chosen=None, set why_not based on the candidate's actual veto/risk record.

#### [scripts/build_report.py:174] `int(bundle.get("alternatives_limit", 3))` raises on explicit None
- **Fix:** `alt_limit = int(bundle.get("alternatives_limit") or 3)`.

#### [scripts/build_report.py:78-91] `_why_not` slices `first.get("detail")` with `[:80]` without verifying string
- **Fix:** Add `isinstance(first.get("detail"), str)` guard.

#### [scripts/build_report.py:128-130] `_alternatives` off-by-one: `alternatives_limit=0` emits 1 alt
- **Fix:** Check `if len(out) >= limit: break` BEFORE append, or `if limit <= 0: return []`.

#### [scripts/build_report.py:206] aggregate variable reassigned with subtly different semantics
- **Fix:** Remove reassignment on line 206, reuse existing local.

#### [scripts/validate_report.py:158] VOTE_PATTERN_REGEX accepts impossible 3-voter patterns
- **Fix:** Tighten regex or add post-match sum check.

#### [scripts/validate_report.py:164-201] `_validate_trias` early-returns on personalities shape failure
- **Fix:** Replace `return` with flag; checks should run anyway.

#### [scripts/validate_report.py:164-201] `_validate_trias` doesn't verify weights sum to 1.0 or lens is a string
- **Fix:** Add weights-sum check + `isinstance(lens, str)` check.

#### [scripts/meta_critic.py:162-178] `conservator_spread` returns 0.0 for single candidate, falsely triggering "shrug" flag
- **Fix:** Return None for single-candidate; skip flag when spread is None.

#### [scripts/meta_critic.py:137-139] `_issue_is_concrete` raises TypeError on non-string detail
- **Fix:** `if not isinstance(detail, str): return False`.

#### [scripts/meta_critic.py:82] MAX_RISK_STDEV=0.5 under-normalizes for N≥3
- **Fix:** Compute as a function of N: `max_stdev = sqrt((n//2) * (n - n//2)) / n`.

#### [scripts/retry_context.py:103-119] `_grep_patterns` appends `\(` suffix to dotted symbols that aren't callable
- **Fix:** Only append `\(` for symbols matched by SYMBOL_CALL_RE.

#### [scripts/retry_context.py:65,99,103-110] `extract_targets` accepts multi-word backtick "symbols" yielding non-grep-able patterns
- **Fix:** Tighten `BACKTICK_RE` to `[\w.]{2,40}` or filter quoted entries with whitespace.

#### [scripts/log_feedback.py:108-109,116] `bool` slips past `isinstance(x, (int, float))` and prints as `1.00`/`0.00`
- **Fix:** Exclude bools: `isinstance(x, (int, float)) and not isinstance(x, bool)`.

#### [scripts/mark_outcome.py:144-147] Run-path match falls back to filename-only — can mis-match rows
- **Fix:** Match by `name` only when `wanted` is bare filename; otherwise require exact `as_posix()` equality.

#### [scripts/audit_feedback.py:111] Backfilled row inherits today's note tense
- **Fix:** Append `; backfilled` marker to note text.

#### [scripts/feedback.py:1-9,106] Docstring still describes FEEDBACK.md while code reads FEEDBACK.html
- **Fix:** s/FEEDBACK.md/FEEDBACK.html/.

#### [scripts/feedback.py:27] ROW_RE assumes `class="entry"` is first attribute of `<tr>` — implicit renderer coupling
- **Fix:** Order-agnostic regex `<tr[^>]*class="entry"[^>]*>`, or regression test.

#### [scripts/migrate_feedback_md_to_html.py:117-120] `md_path.rename(bak)` raises on Windows if .bak exists
- **Fix:** Use `os.replace(md_path, bak)`, or check `bak.exists()` before writing HTML.

#### [scripts/test_feedback_html.py:176] `import json` placed mid-file with `# noqa: E402` — fragile order
- **Fix:** Move import to top of file.

#### [scripts/scope_gate.py:213] CONSILIUM_FORCE_FULL emits sentinel `-1` signals not in documented schema
- **Fix:** Use `0` with `"reason": "...override..."`, or add documented `"forced": true` flag.

#### [scripts/priors.py:1] Docstring references `FEEDBACK.md` but code uses `FEEDBACK.html`
- **Fix:** s/FEEDBACK.md/FEEDBACK.html/.

#### [scripts/priors.py:117-149] `find_missing_feedback_runs` truncates `chosen` to 40 chars enabling collisions
- **Fix:** Use full chosen string, or document truncation with longer cap (≥80).

#### [scripts/feedback.py:90-99] `parse_runs` swallows JSON errors silently with no diagnostic
- **Fix:** Emit stderr warning for skipped files.

#### [scripts/dialectic_merge.py:142] Diff includes `revision`/`maintained` fields, producing noisy "modified" entries
- **Fix:** Filter `BOOKKEEPING = {"revision", "maintained"}` from diff keys.

#### [scripts/memory.py:125] Long tier `"total"` reports filtered count, not source total
- **Fix:** Compute `parse_feedback(FEEDBACK)` length, return as `"total"`.

#### [scripts/run_evals.py:97-103] No type-check on loaded scenarios; dict input crashes downstream
- **Fix:** `if not isinstance(scenarios, list): print(..., file=sys.stderr); return 2`.

#### [scripts/utils.py:50] `validate_keys` doesn't verify `data` is a dict
- **Fix:** `if not isinstance(data, dict): raise/exit with clear message`.

#### [scripts/probe_change.py:87-97] `_commit_count` silently returns 0 on git failure
- **Fix:** Distinguish via sentinel (`-1` or None) and log error to stderr.

#### [scripts/usage.py:91-99] Mode-level latency_ms summed across voices is misleading for parallel mode
- **Fix:** Track latency_ms as `max` for parallel mode, or document the field.

#### [scripts/strip_context.py:61,67] `c["id"]` / `v["id"]` raises KeyError on malformed inputs
- **Fix:** Use `c.get("id")` and skip entries with falsy id.

#### [scripts/probe_change.py:65-67] Tab-separated numstat parser silently drops paths containing tabs
- **Fix:** `parts = line.split("\t", 2)` or pass `-z` to git and split by null bytes.

#### [scripts/scope_gate.py:83-98] Case-sensitive `fnmatchcase` lets lowercase `dockerfile` bypass blocklist — "fails open"
- **Fix:** Case-insensitive variant for known-case-insensitive patterns.

#### [scripts/scope_gate.py:91-98] Blocklist patterns with backslashes never match anything
- **Fix:** `pattern = pattern.replace("\\", "/")` mirroring path normalization.

#### [scripts/personalities.py:21-37,84] PERSONALITIES is mutable module-level list; bulk-emit path doesn't deep-copy
- **Fix:** `MappingProxyType` for immutability, or `[copy.deepcopy(p) for p in PERSONALITIES]`.

#### [SKILL.md:144] voice_scores schema example shows 0.0 floats — Generator score never produced by Generator voice
- **Fix:** Add parenthetical: "voice_scores is derived by `build_report.py`, not emitted by voices directly."

#### [SKILL.md:206 + Resources table] dialectic_merge.py description omits silently_dropped recovery
- **Fix:** Skip (cosmetic), or augment Resources table description.

#### [SKILL.md:177-180] Eval harness skill_maintenance lists dialectic_merge.py but personalities.py omitted
- **Fix:** Add `personalities.py` to trigger list at SKILL.md L178.

#### [prompts/generator.md:45 vs dialectic_merge.py:101-112] adversarial_* gets generator_score=0.5; unconventional_* gets 1.0
- **Fix:** Add note in generator.md: "unconventional_* compete on equal footing in voice scoring; adversarial_* and do_nothing get 0.5 generator-score handicap."

#### [prompts/control.md:9] "category: 'types', detail: 'unverifiable — file not accessible'" — no way to emit unverifiable for valid:true candidate
- **Fix:** Add: "When emitting unverifiable issue, prefer `valid: true` and put note in `notes` rather than `issues`."

#### [prompts/conservator.md:51 + SKILL.md:87] rollback_recipe threshold 0.3 — Pass-2 conservator doesn't restate
- **Fix:** Add explicit instruction in conservator_pass2.md: if Pass-1 risk < 0.3 and Pass-2 ≥ 0.3, include new rollback_recipe in `what_changed` prose.

#### [prompts/skeptic.md:48 Output format] `failure_mode` required but no enumerated vocabulary beyond meta_scope_mismatch
- **Fix:** Document expected vocabulary: `regression_risk_uncovered | edge_case_drop | scope_creep | meta_scope_mismatch | ...`.

#### [prompts/generator_pass2.md vs SKILL.md:271] Pass-2 generator schema mismatch
- **Fix:** Reword SKILL.md L271 to clarify revision is a metadata wrapper, not new content.

#### [prompts/control_pass2.md:35] Rule misnamed — Conservator risk *can* surface a correctness concern
- **Fix:** Reword: "Don't revise valid:true because Conservator's aggregate score is high. DO revise if Conservator's factors.regression_risk notes name a concrete failure path."

#### [prompts/pioneer_lens.md/architect_lens.md/steward_lens.md] `voice_bias: prepended` front-matter declared but no code reads it
- **Fix:** Remove front-matter (no consumer), or wire it into the orchestrator template.

#### [agents/consilium-subagent.md:60] Subagent says "appends to runs/ and FEEDBACK.md" — project uses FEEDBACK.html
- **Fix:** s/FEEDBACK.md/FEEDBACK.html/.

#### [agents/consilium-subagent.md:5 model:sonnet vs SKILL.md:251 Sonnet 4.6 default] Model declared as "sonnet" — alias resolves to latest
- **Fix:** Either pin to `claude-sonnet-4-6-...` for reproducibility, or document that subagent tracks the alias.

#### [prompts/skeptic.md:46 + 67] `quoted_scenario` typed inconsistently
- **Fix:** Replace `"Optional: '...' OR null"` literal with comment-style marker.

#### [SKILL.md:69 "3-5 candidate"] Generator candidate budget tension with mandatory roles
- **Fix:** Bump upper bound to 6, or clarify mandatory roles count toward 3-5 budget.

#### [SKILL.md:104 vs SKILL.md:89] Aggregator description omits `risk_score > veto_threshold` veto semantics
- **Fix:** Reword: "veto at `risk_score > 0.8` (strict; 0.80 exact is NOT vetoed, 0.81+ IS)".

### Wave tracker

| Agent | Bucket | Wave 1 | Wave 2 |
|-------|--------|--------|--------|
| 1 | Voting/decision (6 files) | done (9: 0H/2M/7L) | done (+11: 0H/3M/8L) |
| 2 | Feedback/persistence (7 files) | FAILED (0 bugs, usage limit) | done (+21: 3C/3H/7M/8L) |
| 3 | Context/utility (10 files) | done (17: 1H/7M/9L) | done (+9: 0H/3M/6L) |
| 4 | Prompts + docs (12 files) | partial (17: 3H/6M/8L, ~7/12 files) | done (+23: 1C/5H/10M/7L) |

**Total runs:** 8 (4 agents × 2 waves), with 1 wave-1 failure (Agent 2). Cap reached per user instruction.

---

## 🏛 Senate Resolutions

### Hotărârea Senate — langgraph-langchain-integration-audit · 19 Mai 2026 · MODIFY (GO 0 · MODIFY 3 · STOP 6)

> **Propunere:** Decizie arhitecturală: Ar trebui Consilium skill să integreze LangGraph/LangChain (oricare formă)? Deliberare anterioară (2026-05-16, confidence=0.36): do_nothing câștigat prin eliminare. Candidat via…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Reformulează propunerea ca decizie binară pe un singur candidate cu termeni operaționali: 'Adoptăm candidate #2 (optional_sidecar_visualizer) cu invariante verificabile: (1) grep -r scripts/ → 0 match-uri (CI check); (2) experiments/langgraph_replay/ are propriul venv gitignored și requirements.txt; (3) validate_report.py și run_evals.py trec înainte și după adopție; (4) CLAUDE.md adaugă secțiune care exceptează explicit experiments/ de la constraint-ul stdlib-only, condiționat de no-import-back.' Fără aceste definiții, votul produce o decizie false-clear.
- [ ] **[AURELIUS]** do_nothing rămâne decizia proporțională pentru quadrantul partial×high cu beneficiu slab articulat. MODIFY ar fi justificat doar dacă există un use-case concret, frecvent, neacoperit de stdlib — nedemonstrat. Dacă vizualizarea e scopul real, se reexaminează ca propunere separată, mai mică: scripts/trace_run.py stdlib-only, fără LangGraph, fără venv extern.
- [ ] **[CONFUCIUS]** Deliberarea anterioară (2026-05-16) a produs deja un veto pe toate formele care ating scripts/ sau introduc deps externe. Senate-ul poate confirma STOP. Dacă se dorește redeschiderea pentru optional_sidecar_visualizer, condiția prealabilă este formalizarea contractului de izolare în CLAUDE.md: (1) never-imported de scripts/; (2) never tracked în CI; (3) self-contained venv; (4) deletable unilateral. Până când contractul nu e scris și aprobat, optional_sidecar_visualizer rămâne STOP.
- [ ] **[SOCRATE]** Înainte de GO pe optional_sidecar_visualizer, autorul trebuie să declare: (1) cazul de uz concret care cere vizualizare; (2) un kill-criterion falsifiabil cu deadline; (3) contractul de schema între runs/*.json și parser-ul sidecar; (4) confirmarea că adăugarea unui venv separat în experiments/ nu setează precedent pentru deps în scripts/ core. Fără aceste asumpții declarate, MODIFY-ul e do_nothing cu overhead.
- [ ] **[MUSK]** Nu există modificare viabilă. Niciun candidat LangGraph/LangChain nu adaugă funcție care să nu fie deja acoperită sau acoperibilă fără deps externe. do_nothing e decizia corectă și e deja la minim.
- [ ] **[DIMON]** Address all critical stress scenarios before any GO: (1) Add explicit CI check banning imports of experiments/ in scripts/ (pre-commit hook, grep assertion); (2) Provide platform-specific venv setup for Windows (pathlib.Path, .bat activation); (3) Document schema versioning for runs/*.json replay compatibility with version guard in replay.py; (4) Make sidecar startup bounded timeout with loud failure, not silent degradation; (5) Add kill-criterion in CLAUDE.md: if sidecar unused after N months, delete.
- [ ] **[NAPOLEON]** STOP pe toate variantele care implică LangGraph/LangChain. Calculul de cost e decisiv: do_nothing costă 0h; optional_sidecar_visualizer costă 8-16h pentru beneficiu marginal nevalidat empiric. Recomand reluarea întrebării doar dacă apare evidență empirică din FEEDBACK.html că operatorii au nevoie concretă de vizualizare.
- [ ] **[DEMING]** Re-run the deliberation under the current pipeline (RUND2) at least once more to establish n≥2 with comparable inputs. If the two runs agree on chosen_approach and both produce confidence>0.5, that constitutes minimally sufficient evidence. If they diverge, produce n≥5 or explicitly label the recommendation as provisional with stated uncertainty bounds.
- [ ] **[TACITUS]** Adopt optional_sidecar_visualizer (candidate #2) bounded by explicit historical conditions: (a) lives only under experiments/langgraph_replay/ with separate venv; (b) zero edits to scripts/, prompts/, runs/*.json schema, or SKILL.md Constitution; (c) the 3 Control acceptance tests are gating CI before merge; (d) cite this run AND row 156 in CLAUDE.md so the next re-audit inherits the precedent chain. If any of (a)-(c) cannot be enforced mechanically, fall back to do_nothing.

### Senate Resolution — consilium-refactor-cleanup-20pct · 19 May 2026 · MODIFY (GO 2 · MODIFY 6 · STOP 1)

> **Proposal:** Refactor Consilium with a 20-30% LOC/bytes reduction target via 5 pure-cleanup actions (zero semantics changed): (1) TODO consolidation 3 files → 1 reorganized by categories; (2) Junk cleanup root (…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Before GO: (1) exact numeric baseline measured on HEAD; (2) operational definition of 'zero semantics changed' (list of tests + invariants); (3) explicit triage protocol for BUGS.md (how fixed/open/obsolete is decided per finding); (4) declared choice for senate_transcript.py (delete/wrapper/inline); (5) mitigation for untracked deletion (tar/zip archived before rm).
- [ ] **[CONFUCIUS]** Split bundle into 2 tracks: Track 1 (immediate GO) = actions 1+2+5; Track 2 (separate deliberation) = action 3 (BUGS.md triage) + action 4 (SKILL.md extraction). Precedent: heterogeneous bundles → MODIFY 4/4 historical.
- [ ] **[SOCRATE]** Declare explicitly before execution: (1) stage2/stage3 status confirmed with user; (2) tmp_*/bundle_* inventory with per-file verdict; (3) canonical senator count (7 or 9) confirmed; (4) concrete plan for action 5 that does not touch senate_synth.py; (5) end-to-end post-refactor semantic preservation test.
- [ ] **[MUSK]** 1. Eliminate Action 4 first part (extracting Senate to docs/senate.md) — fragments SKILL.md without real total-byte reduction; replace with in-place compression. 2. Action 5: delete the _generate_transcript() call from senate_synth.py if it's not actively consumed, don't repair deprecated/. 3. Redefine SC as 'tracked bytes drop ≥15%' to prevent gaming through redistribution.
- [ ] **[DIMON]** Required pre-execution: (1) backup of untracked stage2/3 + tmp_* before delete (git reset --hard does NOT recover untracked); (2) audit all hardcoded paths in scripts/ — senate_synth.py:753 (importlib senate_transcript) + senate_todo.py:29 (TODO_DEFAULT) must be updated; (3) UTF-8 encoding discipline for TODO merge (emoji corruption risk on Windows CRLF); (4) pre-flight test cascade on read-only snapshot before delete; (5) lock/mtime check for concurrent TODO.md edits.
- [ ] **[DEMING]** Add at least 1 measured pilot: execute the highest-LOC-impact action on a separate branch, measure the actual delta, compare with the estimate. If delta ±30% from estimate → proposal calibrated. Alternatively: restrict SC to actions with deterministic outcome (junk cleanup + senate_transcript.py fix) and eliminate quantitative claims based on judgment.
- [ ] **[TACITUS]** Cite 2026-05-17 refactor-bundle-7items run and 2026-05-19 claude-md R1→R2→R3 chain as governing precedent, then split into 5 atomic proposals with per-action SC. Ship cleared subset (likely actions 1+2) now; defer 3 (BUGS triage — NOT pure cleanup), 4 (SKILL.md extraction — global-mount gate), 5 (touches authoritative areas indirectly).

**B. Track decisions (user-approved 19 May 2026):**

- [x] **Track 1 — SHIP NOW** (executed in branch `refactor/consilium-track1-cleanup`):
  - [x] Junk cleanup root: deleted 13 untracked files (TEST .txt, FEEDBACK.md.bak, bundle_trias_warmup.json, runs${ts}_self_estimate_fix.json, tmp_build_bundle.py, tmp_bundle*.json (3), tmp_conf.json, tmp_deliberation_bundle.json, tmp_dialectic_bundle.py, tmp_report_out.json, tmp_senate_input.json). Pre-flight backup in `.tmp_backup/track1_untracked_<ts>.tar.gz`.
  - [x] Moved `bugs-agent-2.md` → `docs/archive/bugs-agent-2.md` (orphan note about runs/ write denied).
  - [x] Fixed 7→9 senators inconsistency in SKILL.md (4 places: L361, L561-573 table extended with Deming+Tacitus, L729, L739). Senate cost multiplier corrected from `~2.3×` to `~3×`.
  - [x] `senate-history.html` **stays at root** — regenerable output from `scripts/senate_history.py:233` (moving requires a code change, out-of-scope for Track 1).

- [ ] **Track 2 — R2 SEPARATE DELIBERATION:** TODO consolidation (merge `TODO.md` + `TODO.md.stage2` + `TODO.md.stage3` into one reorganized file). Requires atomic R2 proposal with:
  - Pre-flight: explicit per-item diff between the 3 files (stage2/3 contain the ✅ IMPLEMENTED section that current TODO.md does NOT have — they are NOT abandoned drafts, they are previous consolidation drafts with useful work)
  - Explicit backup before deleting stage2/3 (Dimon: `git reset --hard` does NOT recover untracked)
  - UTF-8 encoding discipline on Windows (emojis ❌🐞✅🤔📋🏛 risk corruption on CRLF)
  - File lock / mtime check for concurrent TODO.md edits
  - Explicit protocol for category-based reorganization (classification criterion per item)
  - Rerun Senate on the revised R2 proposal

- [ ] **Track 3 — DEFERRED (separate deliberations, each its own):**
  - [ ] **BUGS.md triage 107 findings** — requires operational criterion for "fixed" (Wittgenstein D2): (a) grep keyword/path in git log for fix commit; (b) if found → archived in BUGS.archive.md with commit hash; (c) if not found + references existing code → stays open; (d) if references deleted code → obsolete, deleted with note.
  - [ ] **SKILL.md Senate extraction → docs/senate.md** — requires subagent dispatch update (Step 0 Bootstrap include also `docs/senate.md` in inline-paste) + cross-ref audit (README.md, CLAUDE.md, agents/). Musk recommended **in-place compression** as an alternative (no public contract fragmentation).
  - [ ] **scripts/ dedup senate_transcript.py** — touches `senate_synth.py:753` (importlib spec) and `senate_todo.py:29` (TODO_DEFAULT) — out-of-scope originally. Three options stated by Wittgenstein: (1) delete the script + all calls (grep-verify); (2) keep as wrapper with DeprecationWarning; (3) inline the logic in the caller. Choice in the PR description before implementation.

### Senate Resolution — claude-md-refactor-r2-AplusC · 19 May 2026 · MODIFY (GO 6 · MODIFY 3 · STOP 0)

> **Proposal:** R2 (revised scope): apply only A (rm duplicate '# CLAUDE.md' H1 on L9) + C (replace 'workflow-ul în 6 pași' with 'workflow-ul în 8 pași', Steps 0..7 excl. sub-step 1.5). B/D/E deferred (B1 pending emp…

**A. Per-senator decisions:**

- [ ] **[SOCRATE]** C creates internal inconsistency: line 98 of CLAUDE.md says 'pașilor 1-6' which remains stale after line 7 fix. Also: Step 0 may not count as a 'pas' (pre-workflow) — convention should be declared.
- [ ] **[MUSK]** Implement A+C now. B1 gated on Dimon's empirical headless verification. E permanently rejected.
- [ ] **[DIMON]** C must include simultaneous update to README.md L55 ('workflow în 6 pași' → same new string) to prevent cross-file divergence. Verify integer convention before merge.

**B. Actionable items (extracted from requests above):**

- [ ] **C** (cross-ref: SOCRATE, MUSK, DIMON)

### Senate Resolution — claude-md-refactor-and-subdir-files · 19 May 2026 · MODIFY (GO 1 · MODIFY 7 · STOP 0)

> **Proposal:** Refactor Consilium/CLAUDE.md: (A) remove duplicate '# CLAUDE.md' H1 on L9; (B1) delete generic Sections 1-5 entirely OR (B2) keep at bottom + cross-reference; (C) fix 'în 6 pași' to actual SKILL.md st…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Define operational meaning of: 'single source of truth per topic', 'orphaned section', 'project-specific'; supply exact step count integer; specify content template for each subdirectory CLAUDE.md; treat L11 preamble as Claude Code harness loading instruction with behavioral consequences.
- [ ] **[AURELIUS]** Quadrant complete×moderate is over-engineered for 9-senator session. Scope down to A+C only this session; B1/B2/D/E to separate explicit request.
- [ ] **[CONFUCIUS]** Split into Track 1 (approve immediately): A + C — matches 2026-05-18 fix_count_only precedent (conf=0.95, OK). Track 2 (dedicated deliberation): B1/B2 + D + E — requires documented fallback policy and subdirectory governance model. Confirm Claude Code loads subdirectory CLAUDE.md.
- [ ] **[SOCRATE]** Verify 3 load-bearing assumptions before implementation: (1) global CLAUDE.md mounted in headless/CI/worktree; (2) numbering convention for step count; (3) Claude Code supports subdirectory CLAUDE.md.
- [ ] **[MUSK]** Execute A + B1 (full deletion of Sections 1-5 + preamble) + C (remove the count entirely, not replace) + D-implicit (reorder happens automatically after B1). Reject E.
- [ ] **[DIMON]** B1 is STOP unless global-mount guarantee verified across CI/headless/Agent-dispatched subagents. Until then B2 only. E needs empirical load confirmation. D requires moving or removing closing summary to avoid orphan.
- [ ] **[NAPOLEON]** Execute only A + C. Drop B1/B2, D, E. Total: ~10 min, zero maintenance drag. Revisit D only on empirical contributor feedback.
- [ ] **[DEMING]** n=0 on all process claims. Only C is verifiable (n=1, zero variance). For B1/B2/D/E: provide runs/senate evidence of measured outcome impact, or a sync mechanism that reduces drift probability measurably.
- [ ] **[TACITUS]** Ship only C first (matches fix_count_only precedent OK, conf=0.95). Each of B1/B2/D/E proposed separately. E has no precedent in corpus.

**B. Actionable items (extracted from requests above):**

- [ ] **C** (cross-ref: AURELIUS, CONFUCIUS, MUSK, NAPOLEON, DEMING, TACITUS)

### Senate Resolution — deliverable-enforcement-step7-plus-deming-tacitus-integration · 18 May 2026 · MODIFY (GO 2 · MODIFY 7 · STOP 0)

> **Proposal:** feat/deliverable-enforcement: 3 clusters — (A) SKILL.md Step 7 implement expansion 1 line: implement becomes an active instruction with Write tool for files declared in prompt; (B) senate_synth.py: D…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Cluster A requires at least two operational clarifications before merge: (1) exact definition of the trigger section (which text format activates the behavior), (2) exact definition of the declared file. Cluster B requires resolving an internal contradiction: ABSTAIN does not reduce quorum vs voters_present decreases by 1.
- [ ] **[CONFUCIUS]** Cluster A: explicitly document WHY Step 7 (vs Step 6.5) overcomes the R3 failure cause — without this justification, the proposal repeats the previously rejected text-only pattern without demonstrating that the critical variable has changed. Cluster B: add a comment in senate_synth.py explaining the QUORUM=5 decision with 9 senators.
- [ ] **[SOCRATE]** Before merge it must be declared explicitly: (1) the mechanism by which the model is constrained to use the Write tool; (2) the naming convention for the Deliverables section must be documented publicly; (3) ABSTAIN semantics (present-neutral vs absent) fixed consistently in quorum vs voters_present calculation.
- [ ] **[MUSK]** 1) Delete or implement quorum scaling — TODO comment without code is noise. 2) Verify whether SENATOR_REQUIRED_FIELDS custom keys for deming/tacitus are actively consumed by the validator; if not, remove them from the PR and add them when the validator actually checks them.
- [ ] **[DIMON]** Address at least 2 critical scenarios before GO: (1) specify the exact format of paths in Required output files and add a smoke test that verifies the file on disk; (2) define the expected behavior when ABSTAIN > N-QUORUM — either raise QUORUM dynamically, or add a hard cap on permitted ABSTAINs.
- [ ] **[DEMING]** Cluster B+C: sufficient evidence, GO. Cluster A: n=3 senate runs + n=1 empirical T1 all predict that SKILL.md text is not enough. Before GO on Cluster A: (1) empirical evidence that the **Required output files** trigger reaches the executor agent context; (2) at least n=1 controlled test where the model invokes the Write tool on this specific trigger; (3) or explicit acknowledgment that it's advisory-only and enforcement falls to the harness level.
- [ ] **[TACITUS]** The historical lesson of R2 (BAD confirmed) indicates that any text-only solution in SKILL.md for Write tool enforcement has empirically failed. The proposal must include a verifiable acceptance criterion (documented T1 smoke-test) before merge. Without empirical evidence that Cluster A produces different behavior than Step 6.5, the senate is reapproving a mechanism already invalidated.

**B. Actionable items (extracted from requests above):**

- [ ] **B** (cross-ref: WITTGENSTEIN, CONFUCIUS, DEMING)
- [ ] **C** (cross-ref: DEMING)

### Senate Resolution — 2-senators-phase-a-r3-final · 18 May 2026 · GO (GO 7 · MODIFY 0 · STOP 0)

> **Proposal:** Phase A re-audit (2026-05-18): Add 2 new senators to Senate mode — Deming (statistical-discipline: hit-rate, calibration, sample size, anti-anecdote) and Tacitus (retrospective-historian: compares pas…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** None blocking. Recommended inline comments: voters_present single-definition note, casefold+unescape pipeline note, graceful-degradation scope as run-level no_data not evaluation-level ABSTAIN.
- [ ] **[SOCRATE]** Optional one-liner: strip+casefold normalization note in label match operational definition. Not a blocker.

### Senate Resolution — 2-senators-phase-a-r2 · 18 May 2026 · MODIFY (GO 3 · MODIFY 4 · STOP 0)

> **Proposal:** Phase A re-audit (2026-05-18): Add 2 new senators to Senate mode — Deming (statistical-discipline: hit-rate, calibration, sample size, anti-anecdote) and Tacitus (retrospective-historian: compares pas…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** (1) Operational def of label match (verbatim substring, case-insensitive). (2) Add timestamp field to runs/senate JSON schema. (3) Define demotion mechanism concretely (registry.yaml + synth.py reader) or remove falsification language.
- [ ] **[CONFUCIUS]** Add to pre-merge checklist (item 5): audit test_senate_synth.py for coverage of (a) ABSTAIN branch corpus<5, (b) voters_present-1 arithmetic, (c) new Deming/Tacitus tuple fields. tacitus.md must include note about ABSTAIN for first 30 days post-deployment.
- [ ] **[SOCRATE]** (1) Verify vote_counts field exists in current schema or scope migration in this PR. (2) Correlation falsification needs concrete storage (runs/senate/vote_history.json) and named evaluation script. (3) Expand grep pattern to range(7), N_SENATORS, senators[:7].
- [ ] **[DIMON]** (1) Corpus-diversity check alongside count gate — entries span >=2 distinct outcome categories. (2) Define ABSTAIN-streak persistence explicitly (runs/senator_state.json) or remove demotion. (3) Specify tie-breaking rule for even voter_present counts.

### Senate Resolution — 2-senators-phase-a-reaudit · 18 May 2026 · MODIFY (GO 3 · MODIFY 4 · STOP 0)

> **Proposal:** Phase A re-audit (2026-05-18): Add 2 new senators to Senate mode — Deming (statistical-discipline: hit-rate, calibration, sample size, anti-anecdote) and Tacitus (retrospective-historian: compares pas…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Before merging: (1) deming.md must define 'calibration data' as reference to specific field in runs/senate/ JSON schema or explicitly state schema not yet extended (advisory-only); (2) tacitus.md must specify exact evidence source for 'what actually happened' (FEEDBACK.html structured entry, commit log, user annotation) and acknowledge limitation if source is unstructured; (3) both prompts must include one concrete example question. Test update 7-to-9 is necessary and correct — no objection there.
- [ ] **[CONFUCIUS]** Before merge: (1) confirm Tacitus prompt specifies which JSON fields it reads from runs/senate/ entries and has graceful degradation path if fields missing; (2) confirm Deming's calibration output fields are either already in aggregator schema or explicitly marked advisory-only so aggregator.py does not silently drop them.
- [ ] **[SOCRATE]** Before merging: deming.md and tacitus.md must each contain explicit 'degraded mode' section — what senator outputs when required corpus/data absent, and clear statement this degraded output should be weighted lower by synth.py. Additionally: verify via grep/test that no other assertion encodes literal integer 7 as senator count.
- [ ] **[MUSK]** Add Tacitus only (7-to-8, not 7-to-9). Merge Deming's calibration checklist into Musk prompt as structured sub-section ('statistical discipline questions') — zero sub-agent cost, same function. If user has concrete senate run where missing Deming verdict changed outcome, I retract and vote GO on both.
- [ ] **[DIMON]** Before GO: (1) Tacitus prompt must include explicit 'no-data' guard; (2) Deming prompt must specify minimum-evidence threshold behavior — what to output when n is structurally small; (3) confirm single-commit atomicity for all 4 changes; (4) verify validate_report.py and aggregator.py tolerate 9-senator output without dropping new senator fields.

### Senate Resolution — deliverable-enforcement-r3 · 18 May 2026 · MODIFY (GO 0 · MODIFY 4 · STOP 3)

> **Proposal:** Add Step 6.5 'Deliverable contract enforcement (auto)' to Consilium SKILL.md (+17 lines, between Step 6 and Step 7). Behavioral rule (text-only, no regex/parsing): if task prompt declares deliverable …

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Three mandatory operational precisions: (1) binary testable trigger, not open enumerative list; (2) testable definition for acceptable content (pytest 8/8, not just non-empty); (3) JSON schema Step 6 + validate_report.py extended with optional notes field.
- [ ] **[AURELIUS]** SKILL.md is not the right place for deterministic file enforcement. STOP on insertion into SKILL.md; immediate GO on implementation in run_task.py without additional audit.
- [ ] **[CONFUCIUS]** STOP on any variant that places the enforcement in SKILL.md. Empirical precedents (n=2 failures) and senate R2 verdict (7-0-0 MODIFY) are the institutional conclusion. The only validated path: harness-level implementation in run_task.py.
- [ ] **[SOCRATE]** Four undeclared load-bearing assumptions. At least (1) text-in-SKILL.md ≠ text-in-suffix and (2) SKILL.md reaches the executor agent's context must be declared and tested. STOP does not mean abandon — it means reformulation with cause investigation + verifiable preconditions + minimal falsification test.
- [ ] **[MUSK]** Two targeted cuts: (1) reduce trigger examples 5→2 (a header, an inline); (2) trim spec doc 230→60 lines. Core enforcement mechanism (gate + retry + soft-fail + exceptions) stays intact.
- [ ] **[DIMON]** Two preconditions remain unmet from R2: (1) Harness-level assertion in run_task.py — file exists + non-empty + distinct exit code on failure. Only structural guarantee against silent 0-scores. (2) Over-trigger disambiguation: distinguish 'filename declared as output' vs 'filename mentioned in context' — explicit negative example in rule text. Without these, proposal modifies cosmetic location, leaves counterparty risk unchanged.
- [ ] **[NAPOLEON]** MERGE SKILL.md change now — cost negligible, benefit real. Track run_task.py companion as separate issue. Close Senate thread after T1+T2 retest. No R4.

### Senate Resolution — deliverable-enforcement-r2 · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Proposal:** Step 6.5 in SKILL.md (deliverable contract enforcement, text-only behavioral rule with verify-then-emit gate) was implemented to force Sonnet 4.6 headless to call Write for declared deliverable files.…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Supply (1) deterministic extract_declared_files() function, (2) measurable pass rate across full benchmark suite, (3) explicit causal hypothesis for WHY model didn't call Write before choosing (a) vs (b).
- [ ] **[AURELIUS]** Drop senate-deliberation framing for this decision. Approve (b): define exact filename-declaration pattern, confirm claude_raw.json exposes fenced block content, add soft-fail log when extraction finds no match. Skip (a) entirely.
- [ ] **[CONFUCIUS]** Option (a) is STOP. Option (b) GO conditional: implement harness-level fenced-block extraction in run_task.py with non-empty file validation and explicit filename collision semantics. Option (c) two-pass is architecturally cleaner — if pursued, the pass-2 invocation should be unconditional. SKILL.md must NOT be the enforcement layer for file writes.
- [ ] **[SOCRATE]** Before implementation: (1) verify Write is available in headless mode; (2) determine exact failure cause for Attempt 2 (was Step 6.5 read?); (3) explicit silent-wrong-write criterion for (b).
- [ ] **[MUSK]** Delete Step 6.5 from SKILL.md entirely. Delete option (a) as candidate. Implement only (b): minimal stdlib Python post-processing in run_task.py. No new SKILL.md sections.
- [ ] **[DIMON]** Two preconditions: (1) harness-level assertion after claude -p before scoring: file exists + non-empty + no placeholder markers + distinct exit code on failure. (2) For (b): strict extraction contract — fence must contain exact declared filename as label; reject ambiguous blocks; hard error on no match (not silent skip).
- [ ] **[NAPOLEON]** GO on (b); STOP further investment in (a). Modify condition: (b) implementation plan must specify idempotency, error logging, filename matching logic before coding. Avoid third sunk-cost iteration.

### Senate Resolution — pend-triage-ok-outcome · 18 May 2026 · MODIFY (GO 1 · MODIFY 4 · STOP 2)

> **Proposal:** Mark the PEND from 2026-05-15 (run runs/2026-05-15_2236_todo-triage.json, chosen minimal_next_ship, conf=0.52) as OK — the triage was executed substantially: #2-#8 delivered, #16/#17/#20 dropped, #1…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Before marking PEND as OK, the proposal must operationally define three things: (1) the numeric threshold for 'substantially executed' (e.g. N/M items per chosen >= X%), (2) the criterion that separates acceptable from invalidating deviation — especially for #1 (DEFER→DROP), and (3) the explicit definition of OK outcome vs BAD/OVR in the PEND system, so two independent auditors reach the same verdict applying the same criteria.
- [ ] **[AURELIUS]** Not Senate for this. The proposal should be withdrawn from Senate and executed directly: mark_outcome with the justification that execution covered the chosen substantially (7/7 SHIP items delivered, minor deviations documented). Senate is reserved for changes to the skill itself or user code with real impact — not for bookkeeping on 3-day-old PENDs with confidence 0.52.
- [ ] **[CONFUCIUS]** Accepting OK is legitimate and the user has full authority to do so via mark_outcome.py. However, to respect the existing [confirmed] pattern in FEEDBACK.html (which requires outcome_reason with a verifiable artifact), marking as OK should include an explicit --reason that: (1) documents why #1 was DROPPED and not DEFERRED as in chosen, and (2) confirms the decision to deliver #2–#8 instead of just #2/3/8 was conscious and intentional, not accidental.
- [ ] **[SOCRATE]** Before marking OK, declare explicitly: (1) the operational definition of OK in priors.py — does it validate the chosen or problem resolution?; (2) an acceptable deviation threshold (e.g. at most N items deviate from chosen to consider the signal valid); (3) a minimal causal explanation for the deviations (#1 dropped, #4–#8 shipped) that confirms the deviations don't stem from an implicit alternative plan.
- [ ] **[MUSK]** Don't use Senate for trivial CLI operations. Run python scripts/mark_outcome.py --run-path runs/2026-05-15_2236_todo-triage.json --outcome OK directly. Senate is reserved for architectural decisions on the skill, not for confirming that an executed triage can be marked OK.
- [ ] **[DIMON]** Before marking OK: (1) add explicit deviation log to runs/2026-05-15_2236_todo-triage.json or an associated file that documents #1 DEFER→DROP and over-delivery on #4–#7; (2) clarify whether skeptic_on_chosen activated on this run (confidence 0.52) and if not, why; (3) define how priors.py will record this outcome — 'deliberation OK' vs. 'execution OK', a distinction that otherwise produces silently wrong calibration on parallel mode.

### Follow-up — feat/senate-senators-deming-tacitus (Phase A shipped 2026-05-18)

Bundle implemented after Senate R3 GO 7-0-0 (`runs/senate/2026-05-18_211621-2-senators-phase-a-r3-final.json`). Delivered scope: 2 new prompts (Deming + Tacitus), SENATORS tuple 7→9 in synth.py + test, minimal ABSTAIN handling (excluded from tally, reduces voters_present), 1 new test (`abstain_excluded`).

**To analyze (explicitly requested by user, 2026-05-18):**

- [ ] **Demotion — why was the language removed entirely in R3?** Reconstruct the reasoning: in R2 the proposal had "5 consecutive ABSTAIN OR correlation >0.9 → demoted". Wittgenstein/Dimon/Napoleon convergent in R2 demanded either a persistence layer (`runs/senate/senator_state.json` + evaluator), or deletion. R3 chose deletion. Question: if we bring back demotion as a separate feature (Phase B?), what is the correct architecture — stateful counter in synth.py, or external script that marks `registry.yaml`? Implicit: who makes the demotion decision — the automatic orchestrator or the user after review? Implicit: what's the reverse criterion — re-promote after the senator regains accuracy? Separate Senate audit before any implementation.

**Non-blocking nits R3 (TODO, not blocking):**

- [ ] **WITTGENSTEIN:** one-line comment in `senate_synth.py` — `voters_present := count of non-ABSTAIN votes` (clarifies dual-use quorum vs tie-breaking)
- [ ] **WITTGENSTEIN:** one-line comment in `tacitus.md` — pipeline `html.unescape() → str.casefold() → substring check` (instead of simple lowercase, to catch diacritics + HTML entities)
- [ ] **SOCRATE:** optional one-liner strip+casefold normalization note in label-match operational definition
- [ ] **CONFUCIUS:** explicit test case for tie-breaking rule (voter_present even → MODIFY default) — covers future regressions on synth.py
- [ ] **DIMON:** substring collision on label match (`STOP_LIGHT` matches `STOP`) — add word-boundary guard OR ABSTAIN-on-ambiguity in Tacitus implementation
- [ ] **CONFUCIUS:** tacitus.md note about cold-start period (~30 days post-deploy ABSTAIN expected) — verify if sufficiently documented in prompt
- [ ] **AURELIUS:** empirical monitoring — after 10+ runs with Deming/Tacitus, validate that ABSTAIN is not active on the majority of audits (drag proportionally bounded vs aspirational)

**Open architectural decisions (Phase B):**

- [ ] **QUORUM scaling with 9 senators** — currently `QUORUM=5` (5/9 = 56%). Confucius R1 flagged: "DEEPLY_SPLIT threshold defined for N=7 patterns but N=9 has different distributions (5-4, 4-3-2)". To analyze: does scaling to QUORUM=6 (6/9 = 67%, closer to 5/7 = 71%) put historical verdicts at the right threshold? Requires senate audit first.
- [ ] **Explicit timestamp field in JSON schema** — currently the timestamp is in the filename (`YYYY-MM-DD_HHMMSS`) + in the bundle. Tacitus reads from name + bundle field. Wittgenstein R3 requested an explicit top-level anchor. Verify whether synth emits it consistently in all code paths.
- [ ] **`vote_counts` field validation in `validate_report.py`** — verify whether it tolerates 9-senator output without dropping new fields (Deming/Tacitus). Dry-run on 9-senator bundle before first real run.
- [ ] **Falsification metrics infrastructure** — if demotion returns in Phase B, requires storage (`runs/senate/senator_state.json` or `priors.py --senator` extension) + evaluator script + reverse criterion (re-promote).

### Senate Resolution — mode-bugfix-performance · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Proposal:** Mode bugfix + performance v2: BUG-1 (Dialectic doesn't write artifact at root), BUG-2 (_safe_risk_score default 0.5 destroys separation on unanimous deliberations), BUG-3 (Trias dispatch crash on T01). Propose…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Mandatory operational definitions: artifact as a set of files specified in the task spec; strict Pass-1 JSON schema (chosen required, disagreements.severity enum) for P2; info_gain_pass2 on indexable JSON fields; B1 separation of primary fix vs safety net.
- [ ] **[AURELIUS]** Split into 2 tranches. Tranche 1 GO: B1 (complete×high, direct evidence), B2 (complete×moderate, 5 LOC), B3 (complete×moderate), P1 (partial×trivial, user agreed), E1+E2 (complete×trivial). Tranche 2 provisional STOP: P2 requires info_gain >= 0 on majority; P3 contradicts SKILL.md without empirical evidence; P4 requires prompt integrity test.
- [ ] **[CONFUCIUS]** Unconditional GO: B2, B3, E2. Conditional GO: B1 (specify the exact text in SKILL.md); P1 (explicit DEPRECATED marker + runs-citation, NOT silent deletion). MODIFY: P2 (operational definition of 'unanimous'). Provisional STOP: P3 (contradicts SKILL.md contract + personalities.py weights[conservator] becomes dead code). E1 GO as experiment but predefined decision table.
- [ ] **[SOCRATE]** Declare: (1) source of BUG-1 (benchmark prompt vs Dialectic orchestrator); (2) intended semantics for 'maintained' without risk_score; (3) >=1 empirical run that shows Pass-2 value on unanimous before P2; (4) P3 smoke test (Conservator with/without lens on the same input). B1+B3 forward; B2, P2, P3 require empirical proof.
- [ ] **[MUSK]** Minimum viable patch: B1+B2+P2 batch (fix correctness before optimization). Simplify B3 (loud-fail+timeout). Simplify P3 (1-sentence stripped lens). Simplify E2 (field in revision_log). Deletion of *_pass2.md + dialectic_merge.py gated on E1. P1+P4 forward (P4 as new projection).
- [ ] **[DIMON]** B1 content-validation (non-empty + exact path, NOT just exists). B2 ID-matching validation Pass-1/Pass-2 before taking risk_score. P2 'unanimous' formal includes all disagreement grades (NOT just substantial). P3 mandatory empirical experiment (Conservator with/without lens on the same input) before activation.
- [ ] **[NAPOLEON]** GO B1+B2+E2+P1 in 4h block (~3.25h total). P2 gated on E2 baseline data. STOP P3+P4+B3 this block. Optimal sequence: B2 (0.25h) → B1 (0.5h) → E2 (1.5h) → P1 (1h) → P2 (2h, if E2 with data). B3 defer until Trias volume >20/month.

**B. Actionable items (extracted from requests above):**

- [ ] **P1** (cross-ref: AURELIUS, CONFUCIUS, MUSK, NAPOLEON)
- [ ] **P2** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, SOCRATE, MUSK, DIMON, NAPOLEON)
- [ ] **P3** (cross-ref: AURELIUS, CONFUCIUS, SOCRATE, MUSK, DIMON, NAPOLEON)
- [ ] **P4** (cross-ref: AURELIUS, MUSK, NAPOLEON)

### Senate Resolution — benchmark-modes-efficiency-audit · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Proposal:** Benchmark-modes audit: verify benchmark result analysis and propose efficiency improvements (P1-P6) for consilium modes. P1: output-contract self-verify in final dispatch. P2: cost-aware…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** P1+P2 require mandatory operational clarifications: expected_files source, retry semantics, testable definition of easy_code, 25% recalculation excluding superpowers. P3/P5/P4/P6 can pass GO.
- [ ] **[AURELIUS]** P1 GO, P3+P5 immediate GO as preconditions. P2 provisional STOP. P4 MODIFY (already in SKILL.md). P6 MODIFY ($/verified as secondary metric not primary).
- [ ] **[CONFUCIUS]** P1 conditional GO (max 1 re-dispatch, fallback warning). P2 STOP/DEFER (classification without authority, contradicts P3 car-wash). P3+P5 one-liners without Senate. P4 GO. P6 MODIFY (retroactive recalculation).
- [ ] **[SOCRATE]** Before GO: (1) decide whether n=4 is sufficient; (2) empirical diagnosis T04; (3) recalculate $/verified excluding T00; (4) P1 declares expected_files protocol.
- [ ] **[MUSK]** Delete trias_split + avg proxy. Collapse P2 into P4. Merge P3+P5. Implement P1, P4, P6. Dialectic: fix path bug, keep.
- [ ] **[DIMON]** P3 prerequisite. P2 includes failure signal + override + fallback. P1 extended to non-empty + syntax check. P4 with documented decision tree.
- [ ] **[NAPOLEON]** GO {P3, P4, P5, P6} immediately. HOLD P1 until T04 re-run. STOP P2 (cost prohibitive for $17 savings).

**B. Actionable items (extracted from requests above):**

- [ ] **P1** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, SOCRATE, MUSK, DIMON, NAPOLEON)
- [ ] **P2** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, MUSK, DIMON, NAPOLEON)
- [ ] **P3** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, MUSK, DIMON, NAPOLEON)
- [ ] **P4** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, MUSK, DIMON, NAPOLEON)
- [ ] **P5** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, MUSK, NAPOLEON)
- [ ] **P6** (cross-ref: WITTGENSTEIN, AURELIUS, CONFUCIUS, MUSK, NAPOLEON)

### Senate Resolution — benchmark-report-audit · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Proposal:** Benchmark framework: verify results, analyze HTML display bugs, efficiency and cost per result, proposals.

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Operationally define: completed_run (num_turns>=2 + output_tokens>=500), real_mode (dynamic intersection of MODES and workspace/), correct_report (grep test), efficiency_metrics (4 columns), proxy_score (validation with ground-truth).
- [ ] **[AURELIUS]** Reduce scope: A+B fixes are trivial (one-liners), don't require Senate. Senate is useful only for proxy score redesign.
- [ ] **[CONFUCIUS]** Fix consilium_parallel->trias is unconditional GO. Mark superpowers as INVALID (visible). Add threshold N>=2 before aggregate score. Don't couple bug fixes with proxy formula change in same commit.
- [ ] **[SOCRATE]** Full audit of all references to consilium_parallel in repo. Clarify operational definition of BROKEN (testable threshold). Clarify whether trias 1-run is included or marked insufficient_data. Verify whether other hooks contaminate other modes.
- [ ] **[MUSK]** Delete proposals D and F. Fix root cause superpowers (disable hook), not the input_tokens<10 heuristic. Proxy = verify_score * completion_flag, not 40+30+30. Minimum viable: A + C + E.
- [ ] **[DIMON]** MODES derived dynamically from workspace/, not hardcoded. verify/report.json read with try/except + 3 states (OK/BROKEN/UNVERIFIED). Proxy score gate: verify=false -> score=0. Smoke test: completely empty mode column -> WARNING stdout.
- [ ] **[NAPOLEON]** GO on A+B+C (~2.6h). DEFER D. STOP on E (>1 day). Terrain: operator engaged, ROI A+B+C = 25-50x, go now.

**B. Actionable items (extracted from requests above):**

- [ ] **B** (cross-ref: AURELIUS, NAPOLEON)
- [ ] **C** (cross-ref: MUSK, NAPOLEON)

### Senate Resolution — blind-benchmark-wrapper · 18 May 2026 · MODIFY (GO 1 · MODIFY 6 · STOP 0)

> **Proposal:** Build an external wrapper (scripts/fix_benchmark_pendings.py) that post-hoc converts PEND entries to PEND_HEADLESS after claude -p finishes, allowing blind evaluation: Claude runs normally with…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Specifically: (1) operational definition of 'blind evaluation'; (2) exact algorithm for PEND identification from the session; (3) quantitative definition of success; (4) full contract of the mark_outcome.py extension.
- [ ] **[CONFUCIUS]** fix_benchmark_pendings.py must include: (1) idempotency guard; (2) inline documentation that it's a benchmark-exclusive wrapper. Extended mark_outcome.py must validate that PEND_HEADLESS is permitted only with explicit --benchmark flag.
- [ ] **[SOCRATE]** Add a firmer isolation mechanism than timestamp (e.g. env var or run-ID injected by wrapper). Clarify whether mark_outcome.py does in-place edit or appends correction entry — the append-only contract must be maintained.
- [ ] **[MUSK]** Eliminate claude -p wrapping from the script. Reduce fix_benchmark_pendings.py to ~15-20 lines: receives --since <timestamp>, iterates runs/, patching via extended mark_outcome.py. Verify whether runs/ iteration logic can be imported from priors.py.
- [ ] **[DIMON]** Replace timestamp-based matching with run-path fingerprint matching: fix_benchmark_pendings.py collects run-paths produced by claude -p, then calls mark_outcome.py with exact fingerprint. Completely eliminate temporal window dependency.
- [ ] **[NAPOLEON]** Merge current PR as-is, new session for fix_benchmark_pendings.py on separate branch, clean context.

### Senate Resolution — bug-audit-dashboard-sync · 17 May 2026 · GO (GO 5 · MODIFY 2 · STOP 0)

> **Proposal:** Audit of HIGH/CRITICAL bugs in the Dashboard_Sync codebase (Python trading dashboard). Identify, prioritize and concretely describe 5-10 bugs that can cause incorrect data, ImportError, or behavior…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Add to the proposal a severity table with numeric thresholds (P&L impact, frequency, detectability) before classifying bugs as HIGH/CRITICAL.
- [ ] **[AURELIUS]** Prioritize explicitly: (1) CRITICAL = blocks running or produces wrong financial data directly; (2) HIGH = produces wrong data indirectly or causes loss of portability; (3) MEDIUM = cosmetic/convenience.
- [ ] **[CONFUCIUS]** First verify which bugs are already fixed (there are Bug fix comments in the code). Exclude them from the active list. Clarify whether load_rules.py in Fx/ is a design choice or a deployment bug.
- [ ] **[SOCRATE]** Before the audit, verify the current state of each proposed bug (reading the actual code, not from a description). Eliminate from the final list any bugs already fixed. Add concrete verification criteria (input - expected - actual) for each remaining bug.
- [ ] **[MUSK]** Reduce the list to 5-6 active bugs (verified in current code, not already fixed). Eliminate theoretical bugs (stale cache, memory leak for batch scripts). Prioritize: (1) blocking ImportError; (2) incorrect P&L; (3) portability.
- [ ] **[DIMON]** Add for each bug fix a minimal test (input - expected output) to verify that the fix actually resolves the problem and doesn't introduce regressions.
- [ ] **[NAPOLEON]** Implement fixes in the order: (1) Quick wins under 30 min first; (2) Verify bugs already fixed and remove them from the list; (3) Leave cache/memory issues for last (minimal practical impact for batch scripts).

### Senate Resolution — refactoring-dedup-dashboard-sync · 17 May 2026 · MODIFY (GO 0 · MODIFY 6 · STOP 1)

> **Proposal:** Refactoring to eliminate duplicate code in the Dashboard_Sync Python codebase. We propose extracting common functions into a shared module (7.Analysis_Clasification/scripts/utils.py). The duplicates id…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** The proposal must include an explicit equivalence matrix: for each pair of implementations, demonstrate identical output for inputs in the overlap domain. Recommendation: unify ONLY normalize_symbol after proving equivalence, leave load_playbook variants separate with explanatory comments.
- [ ] **[AURELIUS]** The proposal must be staged in strictly increasing order of irreversibility: (1) normalize_symbol - fully reversible, do it first; (2) safe_str/safe_f - fully reversible, do it second; (3) path resolution - moderately reversible, do it third with migration script; (4) load_playbook - partially irreversible, NOT without automated tests. load_rules stays untouched until load_rules.py is found.
- [ ] **[CONFUCIUS]** Before utils.py: resolve the duplicate worktree and document load_rules.py's location. utils.py should be a proper Python package (with __init__.py in scripts/) not a script added in the same directory.
- [ ] **[SOCRATE]** Don't proceed to utils.py until you have: (1) empirically demonstrated equivalence matrix, (2) load_rules.py location documented, (3) duplicate worktree eliminated or synchronized.
- [ ] **[MUSK]** The proposal is over-scoped. Reduce to: (1) normalize_symbol -> symbol_utils.py (5 lines, 30 min); (2) safe_str/safe_f -> utils.py ONLY if proven identical. Remove from scope: load_playbook, path resolution, load_rules.
- [ ] **[DIMON]** The proposal MUST include: (1) before/after output equivalence test, (2) documented path resolution strategy, (3) plan for duplicate worktree, (4) normalize_symbol behavior defined for edge cases (None, symbol with dot, empty symbol).
- [ ] **[NAPOLEON]** Decompose into 3 PRs with different ROI: PR1 (normalize_symbol in symbol_utils.py, 0.5h, immediate GO), PR2 (safe_str/safe_f, 0.5h, GO after verification), PR3 (load_playbook, 4-6h, STOP until CI). Cost-efficiency order: PR1 > PR2 >>> PR3 (PR3 possibly never, negative ROI).

### Senate Resolution — top5-diagnostic-audit · 17 May 2026 · DIAGNOSTIC (no vote — 14 issues found, top-5 synthesized)

> **Scope:** Diagnostic audit on the existing Consilium skill (not a proposal vote). Each senator scanned through their lens; top 5 selected by severity + convergence + concreteness.
> **Bundle JSON:** `runs/senate/2026-05-17_161608-top5-diagnostic-audit.json`
> **Verification status:** Concrete code claims (#2/#3/#5) verified directly against current source on 2026-05-17.

**Top 5 — actionable, ranked:**

- [ ] **#1 [CRITICAL] voice_scores_uncalibrated_measurements** *(Socrate)*
  - Where: `scripts/aggregator.py` (all schemes) + `scripts/confidence.py:derive()` + SKILL.md Step 5
  - Issue: Aggregation veto (`risk > 0.8`) and confidence `pstdev(scores)` treat model self-assigned floats as calibrated [0,1] measurements. Same base model under different prompts produces three numbers; no inter-run stability test exists.
  - AC: declare in SKILL.md that voice scores are uncalibrated model estimates; add inter-run stability check (run identical input twice; flag if stdev > 0.15) before authoritative veto.
  - **R2 OUTCOME (Wittgenstein + Dimon, 2026-05-17):** VALIDATE-WITH-REFINEMENT. R2 sharpened the claim:
    - Calibration ASYMMETRY: Conservator IS anchored via `conservator.md:62-75` formula (categorical→numeric mapping: complete→0.1, irreversible→0.9, trivial→0.1, critical→0.9). Generator + Control emit UNANCHORED floats with no calibration protocol.
    - `confidence.py:194` "agreement" measures role-prompt divergence across 3 voices from the SAME base model — not measurement error, not inter-run stability.
    - `aggregator.py:46` DEFAULT_VETO=0.8 sits in the high-variance region of the score distribution — Dimon predicts inter-run pstdev 0.12-0.18 on `risk_score`, meaning the veto fires NON-DETERMINISTICALLY on boundary cases (the cases where it matters most).
    - Concrete experiment (1-day feasible per Dimon): 5 historical diffs × 2 runs each, mode=sequential, identical params. Measure pstdev per voice. If `mean(pstdev) > 0.10` on risk_score → Socrate's claim empirically confirmed.
  - **Refined AC:** (1) document calibration asymmetry in SKILL.md (Conservator anchored, Gen/Ctrl unanchored); (2) run the 1-day experiment; (3) IF pstdev > 0.10 → either add multi-sample averaging step or raise veto threshold above high-variance region. Fix priority per R2: `next_session`.
  - **EXPERIMENT RUN 2026-05-17:** `experiments/voice-score-stability-2026-05-17.md` — 10 paired Conservator dispatches across 5 risk-spectrum cases (LOW/MED/BOUNDARY_LO/BOUNDARY_HI/HIGH). Findings:
    - **F1** Mean pstdev on `net_concern` = **0.038**, max = 0.100. **Refutes** Dimon's 0.12-0.18 prediction.
    - **F2** Categorical flip rate on `magnitude`: **40%** (2/5 pairs). On `reversibility`: 20% (1/5). The real noise is *upstream of the formula*, in Q1-Q5 categorical assignment.
    - **F3** `do_nothing` baseline stable at pstdev 0.012 across 10 runs.
    - **F4** Veto threshold region (0.8) NOT probed — max observed `net_concern` was 0.42. Dimon's main claim (non-deterministic veto firing near 0.8) **remains unfalsifiable** until [0.7, 0.9] cases are sampled.
    - **F5** `meta_recommendation` disagrees in 2/5 pairs — same input could trigger different deliberation paths.
  - **Spawned follow-ups:**
    - [ ] **#1-A** Drop the `pstdev > 0.15` check from AC — never fires for typical cases (max observed 0.10).
    - [ ] **#1-B** Add a categorical-stability check instead: sample Conservator twice; surface `magnitude`/`reversibility` disagreement to orchestrator (don't auto-resolve). Catches the 40% flip rate at its source.
    - [ ] **#1-C** Re-run with 2-3 cases that produce `net_concern ∈ [0.7, 0.9]` to probe the veto-threshold variance region (F4 gap).
    - [ ] **#1-D** Probe Generator + Control stability (untested here — Wittgenstein's asymmetry claim is half-supported by this experiment).
    - [ ] **#1-E** SKILL.md edits per experiment's "Suggested SKILL.md edits" section (calibration-asymmetry note + 0.8 veto caveat) — separate PR.

- [ ] **#4-followup [MED] subagent-output-contracts-for-6-remaining-gates** *(Confucius R2 scope expansion)*
  - Spawned by #4 ship. The generic `blocking_gates` rule handles BLOCK-class catch-all, but the 6 non-BLOCK gates (REWORK / ADAPT / soft alerts) still have no explicit non-interactive substitute in consilium-subagent.md.
  - AC: enumerate each SKILL.md interactive checkpoint, map to a deterministic non-interactive output contract, document under `subagent_notes.*` field naming convention. Estimated +30 lines.
  - Where: SKILL.md Step 2 + `agents/consilium-subagent.md`
  - Issue: Conservator's `irreversibility_flag: true` is documented to BLOCK + require explicit user consent. The subagent wrapper forbids interactive prompts and is silent on this case — the safety gate is bypassed in the execution context where human oversight is lowest.
  - AC: add explicit subagent rule: when `irreversibility_flag=true`, surface `subagent_notes.irreversibility_blocked: true` and force `confidence: null` + `chosen_approach: null` so orchestrator cannot silently act.
  - **R2 OUTCOME (Confucius + Musk, 2026-05-17):** VALIDATE-AND-EXPAND. R2 sharpened the claim:
    - **Scope expanded** (Confucius): not just irreversibility. `consilium-subagent.md` rule 2 defines non-interactive substitutes for 3 SKILL.md interactive checkpoints (stale_pendings, clarity gate, confidence < 0.7) while leaving **7 OTHER gates undefined**: `irreversibility BLOCK hard`, `glossary_fail BLOCK soft`, `disagreements substantial REWORK`, `meta_recommendation: scale_up`, `challenge_upward triggered`, `retry_context single-pass`, `3+ simultaneous ESCALATE`.
    - **Mechanism refined** (Musk): aggregator.py already returns `result=BLOCK` on `irreversibility_flag=true`. The actual gap is a missing OUTPUT CONTRACT in subagent.md for what to emit when aggregator returns BLOCK — not a missing safety check upstream.
    - **Minimum viable fix** (Musk): 4-6 lines added to `consilium-subagent.md` only. Generic `blocking_gates` rule: pattern-match on aggregator `result=BLOCK` → set `subagent_notes.blocked_reason=<reason>` + force `confidence: null` + `chosen_approach: null`. One mechanism covers irreversibility + glossary_fail + future gates.
    - **Precedent** (Confucius): `runs/senate/2026-05-17_094306-voices-and-senators-to-subagents.json` (STOP UNANIMOUS) already flagged "subagent dispatch mechanism unspecified empirically" — Aurelius's R2 position. The current diagnostic confirms the prior STOP was load-bearing on this exact gap.
    - **Realness check** (Musk): subagent path is live but zero recorded runs have triggered irreversibility yet → risk is structural-imminence, not historical-occurrence.
  - **Refined AC:** (1) ship-now minimum fix per Musk (4-6 lines, generic `blocking_gates` rule in consilium-subagent.md); (2) follow-up audit pass over all 7 missing gates to write exhaustive output contracts (next-session); (3) re-validate by running a synthetic subagent dispatch with irreversibility_flag=true and asserting `subagent_notes.blocked_reason` populated.

**Honorable mentions (medium severity):**

- [ ] **HM1 [MED] meta_recommendation_per_candidate_vs_pipeline** *(Wittgenstein)* — Conservator emits per-candidate inside `scores[]`; aggregator reads top-level (`aggregator.py:372`-area). Top-level `meta_recommendation` is always missing → `scale_down`/`scale_up` triggers never fire in `aggregate_rund2`.
- [ ] **HM2 [MED] trias_cost_gate_soft_not_enforced** *(Aurelius)* — Trias `Skip if` rules are advisory prose; no mechanical check maps `magnitude × reversibility` to mode cost ceiling. AC: extend `scope_gate.py` with `mode_ceiling` derived from Conservator signals.
- [ ] **HM3 [MED] pilot_b_unenforced_activation_gate** *(Confucius)* — SKILL.md documents Pilot B with `N≥5 senate runs` gate; no script enforces or surfaces it. AC: either add `priors.py --senator-gate` check, or demote Pilot B to "design sketch / NOT YET ACTIVE" banner.
- [ ] **HM4 [HIGH] skeptic_catchrate_overgeneralized_from_P3** *(Socrate)* — SKILL.md claims `skeptic_on_chosen` catch-rate "100% simulation, 4/7 real" but all reruns on n=1 problem (P3). Cross-mode comparison claim built on n=1. AC: replace with explicit scope bound + falsification criterion on ≥3 distinct problems.
**Meta-pattern:** Three convergent root causes — (a) rhetorical deprecation without operational enforcement, (b) schema drift between prompts and scripts with no validation layer, (c) load-bearing quantitative claims built on n=1 problem.

---

### Senate Resolution — en-translation-senator-memory-fullnames · 17 May 2026 · MODIFY (GO 0 · MODIFY 5 · STOP 2)

> **Proposal:** Three bundled changes to the Consilium skill: (1) Full-repo English translation of all Romanian content (SKILL.md, CLAUDE.md, prompts/, scripts/ docstrings, memory/, FEEDBACK.html history). (2) Senato…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Make four definitions operational: (1) 'zero non-English content' scope+exemption list; (2) 'persistent memory' storage boundary + retrieval contract; (3) replace 'smoke test' with named script + assertion; (4) commit to exactly one memory mechanism or rank with selection rule.
- [ ] **[AURELIUS]** Split bundle into three independent PRs ordered: (1) renames, (2) translation, (3) memory. Each with own success criterion + smoke test. Memory PR must include at least one pilot run logged + validated.
- [ ] **[CONFUCIUS]** Split into three independent sequential proposals. Item 1 must exclude FEEDBACK.html history (irreversible audit trail destruction). Item 2 must commit to one mechanism + respect Pilot B activation gate before Pilot C. Item 3 must include atomic migration script for runs/senate/*.json senator name keys.
- [ ] **[SOCRATE]** Split bundle with independent validation gates. For Item 2: require explicit user confirmation 'debate to choose one' vs 'combine all three'. For Item 3: pre-merge grep audit confirming zero remaining short-name references. Memory translation needs per-instruction human review.
- [ ] **[MUSK]** Split into three sequential PRs: (1) Item 3 alone (renames, mechanical, ships now); (2) Item 2b alone (priors.py --senator, ~60 LOC); (3) Item 1 scoped (SKILL.md + CLAUDE.md + memory/*.md only, exclude FEEDBACK.html history, defer prompt translation pending voice regression). Drop Item 2a (no-op) and Item 2c (superseded by extended priors.py).
- [ ] **[DIMON]** Split with sequencing gates: (1) Item 3 needs key-alias migration layer for runs/senate/*.json + all 14 tests green before other items; (2) Item 1 explicitly exclude FEEDBACK.html append-only entries + define session-invalidation protocol; (3) Item 2 commit to exactly one mechanism before implementation.
- [ ] **[NAPOLEON]** Unbundle. Sequence: (1) Item 2 alone this session — focused, high-value, low-risk; (2) Item 3 separate mechanical PR; (3) Item 1 dedicated translation session when operator is fresh. Do NOT merge 1+2+3 — review noise from 2500-line translation will obscure Item 2 behavioral changes.

**B. Actionable items (extracted from requests above):**

- [ ] **B** (cross-ref: CONFUCIUS)
- [ ] **C** (cross-ref: CONFUCIUS)

### Senate Resolution — refactor-bundle-7items · 17 May 2026 · MODIFY (GO 1 · MODIFY 6 · STOP 0)

> **Proposal:** 7-item refactor bundle to reduce Consilium over-engineering (S1 dedup transcripts + S2 collapse skeptic modes + S3 veto cascade 4→2 + S4 delete Dialectic + S5 scripts cleanup + B cross-Qs to user + C R2 prompt on MODIFY). User narrowed scope post-R1 (S3+S4 deferred per Napoleon split); B refined (factual→user, opinion-senator→internal per user Q3).
>
> Bundle JSON: `runs/senate/2026-05-17_122622-refactor-bundle-7items.json`. Position changes R1→R2: aurelius MODIFY→GO (deferral resolves concerns), musk GO→MODIFY (wants pre-delete grep table).
>
> **Opt B format (item-grouped with cross-referenced acceptance criteria)** — supersedes auto-generated senator-grouped entry (see `feat/dedup-senate-transcript` branch for the original form).

**Items deferred to fresh session(s):**

- [ ] **S5 — scripts/ cleanup (~9 candidates: `migrate_feedback_md_to_html.py`, `senate_todo.py`, `precedent_search.py`, others TBD)**
  - AC: grep table `{script → referenced_in → verdict}` in PR description [MUSK]
  - AC: first move to `scripts/deprecated/`, final delete after one sprint [MUSK]
  - AC: verify zero orphan refs post-delete (priors.py, usage.py, audit_feedback.py) [DIMON]
- [ ] **B-refined — cross-questions UX (post-R1 factual→user, opinion-senator→internal)**
  - AC: classification rule documented per cross-Q type (factual vs opinion) [USER Q3]
  - AC: explicit timeout T default 30min with autoresolve fallback + audit trail for autoresolved Qs [DIMON]
  - AC: cross-Qs reformulated in user-friendly language (not verbatim from senator output) [SOCRATE]
**Deferred — needs empirical audit before execution:**

- [ ] **S3 — veto cascade 4→2** — Aurelius proposes a 4→3 compromise (keep REWORK+ESCALATE). Requires coverage audit on `aggregator.py`: which of the 7 routing outcomes actually appear in `runs/*.json`? [MUSK+AURELIUS]
- [ ] **S4 — delete Dialectic mode** — Requires empirical usage data from `runs/` (Dialectic frequency vs Sequential) + migration handler in `priors.py`/`usage.py` for orphan mode=dialectic runs [DIMON+SOCRATE]

**Cross-cutting concerns (all items):**

- [ ] Operational defs for "unused" / "non-blocking" / "composable" / R2 semantic disambiguation (B vs C) [WITTGENSTEIN]
- [ ] Falsification criteria for SUCCESS CRITERION — observable failure signals per item [SOCRATE+WITTGENSTEIN]
- [ ] Heterogeneous bundle pattern → MODIFY precedent confirmed; split done partially via Q5 [CONFUCIUS+NAPOLEON]

### Senate Resolution — senate-on-user-code-lens-r3 · 17 May 2026 · GO (GO 7 · MODIFY 0 · STOP 0)

> **Proposal:** R3: senate --on-code via code_domain in renamed domain_lens.md. EXPERIMENTAL_DRAFT until empirical gate (>=3 pilots, >=2/3 info-add, semantic_suspect <=20%). HARD orchestrator pre-compute (Patch 1: ex…

_The Senate approved the proposal. No modifications required._

> **Pilot 1 — 2026-05-17:** `runs/senate/2026-05-17_210550-bug-audit-dashboard-sync.json`. Verdict MODIFY (3GO-2MOD-0STOP). `semantic_suspect` rate = 2/7 = 28.6% (gate criterion ≤20% not met). Cause: senators were dispatched without injection of `code_domain` blocks from `domain_lens.md`. Pilot 2+ must include lens injection per senator via `dispatch_senate_on_code.py`.

### Senate Resolution — per-voice-dispatch-pinning · 17 May 2026 · MODIFY (GO 3 · MODIFY 3 · STOP 1)

> **Proposal:** Add canonical dispatch-defaults table to SKILL.md mapping each voice/senator prompt path to (default model, default tools). Zero new files, zero deletions. 1 file edit (~15-25 lines diff on SKILL.md o…

- [ ] **[WITTGENSTEIN]** Define operationally: (1) 'default model' — MUST-pass vs recommended; reconcile with existing 'Without override, voices inherit the orchestrator's model' text; (2) 'tool allowlist' in absence of technical enforcement — if advisory, say so and remove word 'allowlist'; (3) verification procedure that makes override 'auditable' beyond co-location; (4) correct '6 sections' claim to actual count (3 sections — Parallel/trias_split/Senate).
- [ ] **[CONFUCIUS]** Single advisory clarification: add table header/footnote marking columns as 'descriptive defaults, not enforced constraints' to prevent future readers from treating tools column as hard allowlist. Does not block GO.
- [ ] **[SOCRATE]** Specify explicitly: (1) tools per voice exists as operational distinction or conceptual only — if all voices receive same tools via Agent(), table invents structure that doesn't exist; (2) the 6 'model: sonnet' sections — edited to reference table or coexist with it (latter grows inconsistency); (3) what happens with agents/consilium-subagent.md if it contains its own model defaults.
- [ ] **[MUSK]** Real consolidation is SUBTRACTION, not ADDITION. If repetition is the bug, delete 5 of 6 inline mentions and point all modes to the one canonical paragraph in Parallel mode. Tool allowlist column is unenforceable documentation that rots the moment someone dispatches without consulting it. Resources pointer is category mismatch (Resources tracks scripts/CLIs, not doc anchors).
- [ ] **[DIMON]** Before GO: (1) Specify if lens files and skeptic.md are in or out of table; if in, add 'supplementary — not standalone' annotation per row; (2) Declare which is canonical when table and Parallel prose diverge (table wins / prose wins); (3) Provide runnable regex fixture for criterion 3 OR remove 'regex-verifiable' from success criteria — aspirational criteria are misleading.

### Senate Resolution — voices-and-senators-to-subagents · 17 May 2026 · MODIFY (GO 0 · MODIFY 3 · STOP 4)

> **Proposal:** Refactor consilium architecture: voices core (Generator/Control/Conservator/Skeptic) and 7 senators become subagents in agents/; frontend_domain_lens stays as voice. Pass-2 variants and attitudinal le…

- [ ] **[WITTGENSTEIN]** Operational definitions needed for: 'auto-discovered' (verify orchestrator no longer reads prompts/voices/ for promoted voices); 'promotion' (binary 3-condition definition applied consistently to explain why Skeptic is promoted but Pass-2 and frontend_domain_lens are not); verification method for SUCCESS CRITERION #3 that distinguishes subagent dispatch from inline-prompt dispatch.
- [ ] **[AURELIUS]** Scope to minimum reversible increment: (1) model pinning via dispatch parameters in SKILL.md only, no new agent files; (2) if agent files necessary, scope to voices only (Part A), defer senators (Part B); eliminate install script requirement (portability is core); revisit full promotion only after falsification gate of >=3 successful parallel runs with agent-file dispatch.
- [ ] **[CONFUCIUS]** Three precedent-based reasons for STOP: (1) per_voice_subagents_only was explicitly evaluated and rejected in runs/2026-05-12_1530 — current proposal resubmits without addressing rejection cause (Agent-inside-Agent uncertainty + Trias composition breakage); (2) senate_synth.py SENATORS hardcoded references prompts/senators/ — Part B deletes folder without atomic patch, repeats silent-dispatch-risk; (3) install step breaks self-contained-skill pattern without accepted precedent. If reformulated: separate Part A/B in distinct PRs; eliminate install step (symlink optional); include atomic patch of senate_synth.py + SKILL.md + Trias composition in same commit.
- [ ] **[SOCRATE]** Declare explicitly: (1) whether voice subagent dispatch uses Agent(subagent_type=...) auto-routing OR Read-then-inline — opposite implications for boilerplate; (2) add falsification criterion running test_senate_synth.py with prompts/senators/ deleted; (3) specify failure mode for users who pull commit without running install; (4) declare whether 'lens injected via prompt' in Trias is blocking or advisory — if blocking, N×M problem must be solved before Part A ships.
- [ ] **[MUSK]** Proposal adds 13 files + deletes 7 to solve 3 problems already solved by existing infrastructure: model pinning in SKILL.md Parallel dispatch; tool allowlist in consilium-subagent.md frontmatter; auto-discovery has no value for internal pipeline components. Verdict STOP: 0 of 3 stated benefits justify 13 new files + install dependency. If a real unmet need exists (voices running independent of orchestrator with own isolated context), formulate that use case concretely as new proposal with 1-2 files, not 13.
- [ ] **[DIMON]** Before proceeding: (1) Concrete Trias composition remediation plan — new lens-injection mechanism for agents/ YAML frontmatter OR documented Trias deprecation; (2) Fallback path for missing agent files (inline fallback + warning, not silent UNREACHABLE); (3) Resolve Pass-2 dialectic two-source problem with single canonical definition; (4) Verifiable install-check step (script validates all 11 symlinks exist non-stale before senate dispatch). Until these 4 addressed, silent failure modes outweigh benefits.
- [ ] **[NAPOLEON]** STOP on terrain, not merit. Real upside but implementation cost (6-10h, 1500-1800 lines diff, permanent install friction) not justified in stretched multi-change session with unresolved design tensions (Trias breakage, Pass-2 two-sources, consilium-subagent overlap). Defer to fresh session after: (1) quantifying invocation frequency to validate 30-line/call savings payback; (2) resolving 3 design tensions with explicit decisions; (3) confirming user's distribution model tolerates mandatory install step.

> Auto-append from `senate_synth.py` via `senate_todo.py`. Format: GO/MODIFY/STOP per senator.
>
> **Status (audit 2026-05-17):** Senator critiques marked `[DEFERRED]` per item — feedback on never-executed audit proposals ("flow-and-modes-audit"). Light touch: kept in TODO for reference, but they are not live action items. Re-evaluate when reopening the proposal or when `senate_todo.py` produces other blocks.

### Senate Resolution — phase1-deeply-split-plus-laws-mapping · 17 May 2026 · GO (GO 5 · MODIFY 2 · STOP 0)

> **Status (2026-05-17):** Shipped. One unaddressed item remains.

- [ ] **[SOCRATE — unaddressed]** Coverage table formally disjoint between DEEPLY_SPLIT and the other verdicts (GO/MODIFY/STOP/UNREACHABLE) across all tuples (GO, STOP, MODIFY, ABSENT) summing to 7 — the 5 existing unit tests do not constitute exhaustive boundary coverage.

### Senate Resolution — bundle-2-senators-plus-5-improvements · 17 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Proposal:** Bundle of 6 modifications to consilium Senate mode: A) add 2 new senators (Deming statistical-discipline, Tacitus retrospective-historian); B.1) codify Laws 1-4 in SKILL.md mapped to 4 Constitution Pr…

- [ ] **[WITTGENSTEIN]** Supply machine-executable definitions: (1) 'OK outcome' as ground truth for hit_rate (source + time window); (2) explicit boolean formula for DEEPLY_SPLIT trigger; (3) fixed JSON schema for cross_questions[] contract; (4) code-level definition of 'paragraph present'.
- [ ] **[AURELIUS]** Approve Phase A (2 new senators) + Phase B.1-2 (Laws + DEEPLY_SPLIT + tests). Defer B.3-5 (predispatch, calibration, round.py) until runs/senate/ has >=20 entries to justify automation cost and validate calibration data.
- [ ] **[CONFUCIUS]** Critical findings: (1) Laws are already 1-5 in docs/senate/architecture.md §8.1, NOT 1-4 — proposal conflicts with existing 5-Law structure (Mandatory Response / Cross-Q / Deadlock / Synthesis at end / Auditability); (2) runs/senate/ has only .gitkeep, zero real runs — calibration script orphaned; (3) SENATORS hardcoded 7-tuple in senate_synth.py + test asserts 'all 7 prompts' — silent non-dispatch risk if new senators not wired atomically; (4) DEEPLY_SPLIT threshold defined for N=7 patterns but N=9 has different distributions (5-4, 4-3-2); (5) cross-questions Law 2 was explicitly deferred 'after >=3 real invocations'.
- [ ] **[SOCRATE]** Three load-bearing assumptions must be declared: (1) minimum corpus size for senate_calibration.py validity — add guard + documentation; (2) decision rule for DEEPLY_SPLIT verdict (what user/orchestrator does on receipt) — must be explicit in SKILL.md, not implicit; (3) pre-dispatch Haiku gate semantics (hard block vs soft annotation) — implementation differs significantly between the two.
- [ ] **[MUSK]** Delete senate_predispatch.py (replace with one SKILL.md callsite note). Delete docs/senate/ subtree (move essential diagram to SKILL.md). Merge Deming's data-discipline into Musk's prompt (no new senator file, count stays at 8 not 9). Replace senate_calibration.py with --by-senator flag on existing priors.py. Keep: tacitus.md, Laws codification (reconcile with existing 5), DEEPLY_SPLIT, senate_round.py, test updates. Net: 2 new files instead of 7-8, ~150-200 lines instead of 400-600, 8 senators instead of 9.
- [ ] **[DIMON]** Before GO: (1) senate_round.py must validate cross_questions[] schema and log visible warning (not silent skip) when malformed; (2) DEEPLY_SPLIT threshold must cover 4-3-2 and 5-4 distributions minimum, with unit test per pattern; (3) senate_calibration.py must handle missing/empty runs/senate/ gracefully with explicit error+exit code, not crash or silent zero-output; (4) senate_predispatch.py must define fallback (proceed or abort) on unrecognized Haiku output. 5 silent failure modes identified and unaddressed.
- [ ] **[NAPOLEON]** Unbundle into 2 phases. Phase 1 ship now: Laws codification + DEEPLY_SPLIT + tests (~1-2 files, ~80-120 lines, ~1-2h, zero runtime cost increase). Phase 2 defer: Deming + Tacitus + senate_calibration.py + senate_round.py + senate_predispatch.py + docs — activate only after >=10 senate runs exist to justify 25-35% per-invocation cost increase and give calibration meaningful data.

### Senate Resolution — test-auto-todo · 16 May 2026 · UNREACHABLE (GO 2 · MODIFY 0 · STOP 0)

> **Proposal:** test proposal
> **Absent:** aurelius, confucius, dimon, napoleon, socrate

_No modification requests recorded._

### Senate Resolution — flow-and-modes-audit-r2 · 16 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)

> **Proposal:** Evaluate all workflow steps (0,1,1.5,2,3,4,5,5b,5c,5d,6) and all modes (Sequential, Dialectic, Trias, parallel_skeptic, dialectic_skeptic, trias_split, skeptic_on_chosen, senate) to determ…

- [ ] **[DEFERRED]** **[WITTGENSTEIN]** The proposal is not auditable in its current form: the key terms of questions (a), (b), (c) have no verifiable operational definitions. Before implementation: (1) metric for load-bearing; (2) metric for distinct use-case vs redundant; (3) elimination vs deprecation criterion for sections with documented problems.
- [ ] **[DEFERRED]** **[AURELIUS]** Reduce the scope of the proposal to a concrete operational question: which modes with 0 runs can be eliminated without contractual risk? This can be resolved with Sequential or a single focal agent (Musk/Napoleon), not with a full Senate. If the elimination decision has irreversible consequences, then Senate is justified — but only for the deletion decision, not for the preliminary audit.
- [ ] **[DEFERRED]** **[CONFUCIUS]** Non-blocking condition from round 1 partially satisfied. Additional requirements: (1) the demotion of Step 5c requires resolving the unimplemented precedent from runs/2026-05-16_0200_voice_audit_skeptic.json; (2) the collapse of Step 5d into skeptic_on_chosen must preserve the context-enrichment function or accept the loss with documented rationale.
- [ ] **[DEFERRED]** **[SOCRATE]** The proposal must declare: (1) the positive criterion for load-bearing — not just absence of negative effect; (2) whether usage count is the primary criterion or a proxy; (3) whether the RUND2 precedent is an authority argument or there is a transferable structural justification. Without these declarations, the audits operate on unspoken assumptions.
- [ ] **[DEFERRED]** **[MUSK]** DELETE: Step 5c, Step 5d, parallel_skeptic, dialectic_skeptic, trias_split, principle_extraction.py, RUND2 duplicate sections. SIMPLIFY: Dialectic (demote to experimental). KEEP: all the rest. Sequential implementation, not simultaneous — one mode per commit to test regressions.
- [ ] **[DEFERRED]** **[DIMON]** The proposal must explicitly address: (1) deprecation protocol for scripts that remain on disk after being removed from the contract (rename to *.deprecated.py or guard INACTIVE flag); (2) versioning of the runs/*.json schema to distinguish runs produced with the old workflow from those with the new one; (3) explicit specification of whether the automatic skeptic-on-chosen trigger (band [0.5, 0.7]) remains active after consolidation and where in the code this logic lives.
- [ ] **[DEFERRED]** **[NAPOLEON]** Mandatory narrowing: (1) exclude from the audit modes with <2 real runs; (2) separate workflow step analysis from mode analysis into two distinct deliberations; (3) defer the second senate run in the same session. If you continue now, limit to: Sequential vs Parallel (40 runs combined) + maximum 2 load-bearing steps out of 11.

### Senate Resolution — flow-and-modes-audit · 16 May 2026 · MODIFY (GO 1 · MODIFY 5 · STOP 0)

> **Proposal:** Evaluate all workflow steps (0,1,1.5,2,3,4,5,5b,5c,5d,6) and all modes (Sequential, Dialectic, Trias, parallel_skeptic, dialectic_skeptic, trias_split, skeptic_on_chosen, senate) to determ…
> **Absent:** napoleon

- [ ] **[DEFERRED]** **[WITTGENSTEIN]** Define operationally before implementation: (1) load-bearing with testable criterion; (2) empirical support with numeric threshold; (3) clearly marked for removal with exact physical form from SKILL.md.
- [ ] **[DEFERRED]** **[AURELIUS]** Reduce apparatus to /consilium parallel or sequential for the initial audit. Run Senate only after the audit produces concrete accepted changes for implementation.
- [ ] **[DEFERRED]** **[CONFUCIUS]** Non-blocking: the final output should explicitly cite relevant previous runs per elimination decision.
- [ ] **[DEFERRED]** **[SOCRATE]** Before continuing, declare: (1) operational definition of empirical support; (2) whether previous recommendations are treated as accepted priors; (3) whether skeptic_on_chosen is evaluated as a flag or peer mode; (4) the falsification criterion.
- [ ] **[DEFERRED]** **[MUSK]** 1. DELETE: dialectic_skeptic + trias_split from SKILL.md. 2. DELETE: scripts/principle_extraction.py. 3. REMOVE: parallel_skeptic as a named mode. 4. DEMOTE: Step 5c to Skill maintenance. 5. COLLAPSE: Step 5d into skeptic_on_chosen auto-trigger. 6. ADD: fabrication warning Dialectic Pass-2. 7. TIGHTEN: dialectic_merge.py dissent fallback to hard rejection.
- [ ] **[DEFERRED]** **[DIMON]** (1) Cross-reference verification mechanism after eliminations. (2) Treatment of historical runs/ with eliminated mode labels. (3) Exit condition for reflexive senate auto-modification.

---

## Benchmark — two-pass runner (to investigate)

**Context:** consilium_sequential benchmark runs produce 0/4 verify:OK with the current fix (CLAUDE_HEADLESS + CONSILIUM_SUFFIX). The suffix doesn't reach the internal sub-agents from trias/dialectic — post-deliberation implementation depends on each mode's orchestrator.

**Proposal:** redesign `run_task.py` for the `consilium_trias` and `consilium_dialectic` modes (and optionally sequential) with two separate steps:
- **Pass 1:** `claude -p "/consilium [--mode X] <task>"` → deliberation, report in `runs/<file>.json`
- **Pass 2:** `claude -p "chosen_approach: <extracted from runs/...json>. Task: <task>. Implement now: write output files."` → fresh context, 0 prior turns, direct implementation

**To investigate:**
- [ ] How to robustly extract `chosen_approach` from the Pass 1 response / `runs/<file>.json`
- [ ] What happens if `runs/<file>.json` is not written (consilium failure) — fallback to generic Pass 2?
- [ ] Cost impact: ~2× per consilium run ($3 vs $1.5); acceptable?
- [ ] Do Trias sub-agents write intermediate files to the workspace in Pass 1? If so, Pass 2 must see them
- [ ] Measurement: run consilium_trias + consilium_dialectic with two-pass and compare verify rate with current fix

**Priority:** after it's confirmed that the CONSILIUM_SUFFIX fix raises sequential to >2/4 verify. If sequential stays at 0/4, two-pass becomes priority.

---

## Rollback hooks

- **R.1** All new voices (philosophical variants) are **parallel**, not replacing — zero risk if not called.
- **R.2** If `aggregator.py` breaks old runs → revert that commit, keep prompts.
- **R.3** If Senate mode is too expensive → marked as premium, default remains standard modes.
- **R.4** If Napoleon over-fitted (post Phase 14A) → withdrawn from Senate, the Senate of 6 remains.

---

**End of consolidated TODO.**
---

## 🏛 Hotărâri Senate

### Hotărârea Senate — law9-senate-scope-definition · 19 Mai 2026 · MODIFY (GO 2 · MODIFY 7 · STOP 0)

> **Propunere:** Adăugăm Law 9 în Senate care definește când Senate e instrumentul corect — criterii clare de scope, routing, și calificare a propunerilor. Scopul: ca Senate să fie mai inteligent (evită mis-invocări),…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Law 9 are 9 termeni vagi neoperaționalizați. Propun reformulare ca funcție evaluabilă justifies_senate(proposal) → bool cu 3 criterii threshold-based (reversibility×magnitude, architectural tiers afectate, confidence floor). Această funcție e Law 9. O enumerare de tipuri de propuneri nu rezolvă problema — adaugă ambiguitate de tip 2 (edge cases între categorii). Adaugă: baseline empiric al mis-invocărilor actuale înainte de promulgare.
- [ ] **[AURELIUS]** Alternativa mai mică: patch de 3-5 linii la SKILL.md §'Routing boundary', fără numerotare de lege nouă. Legile Senate sunt pentru invarianți de comportament al senatorilor, nu pentru documentare de routing. Law 9 ca lege e o abstracție greșit adresată. MODIFY: reformulează ca addendum la §'Routing boundary' existent.
- [ ] **[SOCRATE]** 4 asumpții load-bearing nedeclarate. Înainte de Law 9: (1) adaugă baseline empiric — câte runs/senate/ ar fi fost filtrate de Law 9 dacă ar fi existat? (2) dacă baseline e zero, reformulează ca prevenție prospectivă cu clauză de auto-calibrare: 'Law 9 se reevaluează după 20 de runs Senate și se abrogă dacă rata de filtraj e sub 5%'; (3) testează partiția: ia ultimele 10 runs/senate/ și aplică manual criteriile propuse — câte ar fi OUT_OF_SCOPE? Dacă răspunsul e 0, criteriile sunt prea laxe.
- [ ] **[MUSK]** Nu crea Law 9 ca lege numerotată — adaugă 1 rând la tabelul de routing existent din SKILL.md: 'Not Senate if: reversibility=complete AND magnitude=trivial/moderate; sau confidence>0.7 pe modul standard; sau propunerea afectează ≤1 tier arhitectural.' Această linie face tot ce face Law 9 propusă, fără overhead de lege nouă și fără duplicat.
- [ ] **[DIMON]** 5 scenarii de eșec neadresate. Law 9 ca text manual e ornamentală. MODIFY: (1) implementează scripts/law9_scope_gate.py care evaluează automat justifies_senate(proposal) pe baza unor criterii obiective bazate pe fișiere (ex. input conține cuvintele 'scripts/', 'prompts/', 'SKILL.md', 'runs/senate/', 'architecture'); (2) criterii bazate pe pattern-matching fișiere din propunere, nu pe judecată subiectivă; (3) output al scriptului: GO/SCOPE_WARN/OUT_OF_SCOPE cu reasoning; (4) telemetry: fiecare invocare Law 9 se loghează în FEEDBACK.html cu outcome pentru calibrare; (5) clauză de auto-abrogare dacă rata de filtraj e sub 5% după 20 de runs.
- [ ] **[DEMING]** Baseline empiric: 54 senate runs, 0 scope_veto organice. Problema documentată nu există în corpus curent. MODIFY: (1) dacă Law 9 e prospectivă (prevenție), declară explicit că e prevenție, nu remediere; (2) adaugă clauză de auto-calibrare: 'Law 9 se reevaluează după fiecare 20 senate runs; dacă filtraj rate <5%, legea se abrogă automat'; (3) runs retrospective: aplică manual criteriile propuse pe ultimele 20 runs/senate/ și raportează câte ar fi filtrate — dacă 0, criteriile sunt fie prea laxe, fie problema nu există.
- [ ] **[TACITUS]** Nu adăuga criterii noi nedocumentate în runs/senate/. Promovează conținutul existent: (1) §'Routing boundary' din SKILL.md → Law 9, §1 (scope positiv); (2) §'Skip Senate dacă' din SKILL.md → Law 9, §2 (scope negativ); (3) Law 7 (scope_veto) → Law 9, §3 (corecție post-facto). Fiecare criteriu din §1 și §2 trebuie să citeze linia SKILL.md sau runs/senate/ precedent ca sursă. Nu adăuga criterii noi care nu au bază empirică în corpus.

### Hotărârea Senate — langgraph-sidecar-binary-r2 · 19 Mai 2026 · MODIFY (GO 1 · MODIFY 2 · STOP 6)

> **Propunere:** Decizie binară: Adoptăm optional_sidecar_visualizer (experiments/langgraph_replay/ izolat) cu 6 invariante verificabile: (1) grep -r 'langgraph|langchain' scripts/ prompts/ agents/ → 0 match-uri (CI g…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** 3 addenda rămân nerezolvate: (a) kill-criterion trebuie să măsoare valoarea, nu doar invocarea (.last_invoked insuficient — adaugă cerință de ≥1 insight documentat în FEEDBACK.html); (b) documentul de adopție trebuie marcat explicit ca elimination_certification (nu positive_certification); (c) CLAUDE.md sau sidecar README trebuie să citeze lanțul complet de deliberare ca proveniență. Cu aceste 3 addenda adăugate, devin GO.
- [ ] **[AURELIUS]** do_nothing rămâne proporțional pentru partial×high cu beneficiu slab articulat. Reexaminează dacă există use-case concret, frecvent, neacoperit de stdlib.
- [ ] **[CONFUCIUS]** Condiție prealabilă: formalizarea contractului de izolare în CLAUDE.md înainte de redeschidere.
- [ ] **[SOCRATE]** 2 asumpții rămân nedeclarate: (1) mecanismul kill-criterion trebuie să specifice ce contează drept invocație utilă vs. game-abil (adaugă în CLAUDE.md: kill-criterion se declanșează dacă .last_invoked > 90 zile SAU dacă nu există niciun rând în FEEDBACK.html referind un insight din sidecar în aceeași perioadă); (2) sidecar-ul trebuie să fie explicit EXPERIMENTAL_DRAFT în README până când prima utilizare reală e documentată în FEEDBACK.html. Cu aceste două declarate, devin GO.
- [ ] **[MUSK]** Nu există modificare viabilă. do_nothing e decizia corectă.
- [ ] **[DIMON]** Adresează toate scenariile critice înainte de GO.
- [ ] **[NAPOLEON]** STOP. Cost-benefit unfavorable; reluare doar cu evidență empirică din FEEDBACK.html.
- [ ] **[DEMING]** Re-run deliberarea sub RUND2 pentru n≥2 cu confidence>0.5 înainte de decizie.
