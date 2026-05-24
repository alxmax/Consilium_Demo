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
8. [🎯 User directions (open)](#-user-directions-open)

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

---

## 🤔 UNRESOLVED DECISIONS

From `TODO_RUND2.md` Appendix D — personal decisions that do not block current implementation:

- [ ] **[SENATE] Consilium as a deliberation + implementation tool** — In the benchmark context, Consilium deliberates but does not implement. Temporary fix: Step 7 `implement` extended (2026-05-18) to write files when the prompt declares `**Required output files**`. Unresolved architecture decision: do we want Consilium to be a *pure deliberation* tool (verdict + report → implementer decides) or a *deliberation + implementation* tool (verdict → Consilium writes the code)? Implications: (1) if implementation is in-scope, who decides where files get written in non-benchmark contexts? (2) the `implement` step becomes a blocking operation (Write tool), not an advisory reminder. To be discussed in Senate before extending scope beyond the current benchmark fix.

- [x] **[SHIPPED] Post-deliberation implementation pipeline** — supersedes parent item ↑. Senate verdict MODIFY (GO 0·MODIFY 2·STOP 7, `runs/senate/2026-05-24_200959-consilium-code-writer-vs-superpowers.json`); built per the sequential follow-up (`runs/2026-05-24_2030_implement-pipeline-scaffold.json`). Opt-in EXPERIMENTAL_DRAFT scaffold on branch `feat/implement-pipeline-scaffold`: `agents/consilium-implement-subagent.md` + `prompts/implement/{coder,test_writer}.md` + `scripts/implement_pipeline.py` (Coder → Test Writer ∥ Reviewer; reviewer reuses `control.md`; disjoint-path ownership, malformed-JSON hard-fail, red→green gate). Optional fan-out (task-split) documented on `feat/implement-pipeline-fanout`.
  - [x] **Kill-criterion gate — RUN 2026-05-24** (`experiments/pipeline-bench/RESULTS.md`): pipeline 1 win / 2 ties / 0 losses vs single-shot, ~1.1× tokens / 3–7× wall-clock. Win was the refactor/regression task (review caught a defect the single-shot shipped); greenfield was a wash. Pre-registered rule (wins < 2/3) → **not default**. **Decision: keep opt-in, scoped to refactor/bugfix/regression-risk changes only.**
  - [ ] **Re-test before promoting the narrow use:** add ≥3 more refactor-regime tasks; confirm the win rate holds (n=3 / 1 win is a pilot signal, not proof — Deming).

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

#### ~~18. Observe → Think → Act → Learn formal loop~~ — ✅ CLOSED (2026-05-19, Senate audit `runs/senate/2026-05-19_214850-todo-18-otal-formalization.json`, MODIFY 0-8-1)
Resolved at **Level 1 (docs-only)** per 8/9 senator convergence. Added descriptive OTAL framing + ASCII cycle diagram to `SKILL.md` § "Observe → Think → Act → Learn (descriptive framing)"; updated the Mermaid diagram in `docs/architecture.html` § "Observe → Think → Act → Learn" with correct RUND2 step order (Conservator first), `priors.py` in Observe, `retry_context.py` sub-iteration, and the partial-Learn caveat. Level 2 (`meta_critic.generator_divergence<0.4` iteration triggers) deferred until ≥3 PEND rows in `FEEDBACK.html` demonstrate the existing `confidence<0.7` retry underperforms; the metric currently has zero labeled triggering events. Level 3 (meta-controller) closed pending revival of dropped item #16 — contradicts Constitution Principle 2.

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
>
> **Status update 2026-05-19:** All 4 Critical and 12 High audit-flagged bugs are now closed.
> - 6 High fixed in `feat/fix-high-bugs` (commit 542c0d1): H2 priors.py backfill sidecar, H3 fuzzy-match zero-overlap guard, H5 SKILL.md unconventional documentation, H7 skeptic.md orchestrator-side validation, H9 pioneer_lens conservator carve-out, H12 clarity-gate 3-way reconciliation. H6 already-fixed.
> - C1+C2 atomic FEEDBACK.html writes: `utils.atomic_write_text` wired into `log_feedback.py:250` + `mark_outcome.py:197` + `log_feedback.py:_save_map` (sidecar map also atomic since this branch).
> - C3 VETO threshold drift: `render_feedback_html._cons_panel` now derives `vetoed_ids` from `agg_result.get("vetoed")` instead of hardcoded `>= 0.7` (lines 212-224).
> - C4 Pass-2 verdict schema: `dialectic_merge._merge_pass2_control_verdict` inherits `valid`/`issues`/`tests_to_write`/`notes` from Pass-1 (line 101-119) + `control_pass2.md` documents the override pattern for `valid: false → true` flips.
> - H1 dedup: fingerprint+sidecar-map keyed by `run_id` (`log_feedback.py:60-73`); cross-process lock skipped (single-user CLI).
> - H4 null risk_score: `_safe_risk_score` (line 122-129) treats explicit `null` as missing.
> - H8 Pass-2 `tests_to_write` slot: documented in `control_pass2.md` § "What carries over from Pass 1".
> - H10 Sequential mode wording: aligned with SKILL.md Sequential-first post-RUND2 (Parallel is no longer user-selectable).
> - H11 Tools list: `Write` is present in `agents/consilium-subagent.md` frontmatter `tools:` list.
>
> Remaining: 39 Medium + 52 Low (lower priority). Counts below reflect original audit and are kept as historical context.

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

### Critical (4) + High (12) — ✅ ALL CLOSED

Detail removed (fixed; see status block above + git history: `feat/fix-high-bugs` commit 542c0d1, atomic-write/VETO/Pass-2 fixes). Counts retained for context.


### Medium (39)
- **[scripts/aggregator.py:54-67] `aggregate_majority` sort crashes with TypeError on (mean, -stdev) tie** — Insert stable tiebreaker before `c` (enumerate index). Same exposure in `aggregate_weighted` (line 97).
- **[scripts/build_report.py:64-75] `_voice_scores_for` silently zeros control_score when chosen has no verdict** — Raise/warn when `verdict == {}` after lookup, or surface missing-verdict as a distinct null/sentinel.
- **[scripts/build_report.py:215-222] `_default_reasoning` mislabels Trias fragmentation as "all candidates vetoed"** — Branch on `scheme == "team_vote"` + `vote_pattern`. Fragmentation: "deliberation fragmented (vote_pattern=…); orchestrator must intervene".
- **[scripts/validate_report.py:170-174] `_validate_trias` iterates fields on personality entry without verifying dict** — `if not isinstance(p, dict): errors.append(...); continue`.
- **[scripts/validate_report.py:138-155] `_validate_telemetry_required` only enforces voices for "parallel" mode, not Trias** — `mode in ("parallel", "trias", "dialectic", "trias_split", "parallel_skeptic", "dialectic_skeptic")`.
- **[scripts/log_feedback.py:188,205-206] Fingerprint truncates context to 30 chars — distinct deliberations share drill-down run_path** — Include full context (or `run_path`) in fingerprint, or key sidecar map by `run_path` directly.
- **[scripts/log_feedback.py:146] OVR outcome with missing --override-target produces silent no-op** — Raise `ValueError("--outcome OVR requires --override-target <alt_id>")`.
- **[scripts/mark_outcome.py:83-91] `_annotate_note` not idempotent — duplicates `outcome_reason=` entries** — Filter existing `outcome_reason=` parts before appending.
- **[scripts/audit_feedback.py:116] Backfill performs N full read-render-write cycles — O(N²) work** — Batch backfill — accumulate Entry objects, render and write ONCE atomically.
- **[scripts/render_feedback_html.py:258-261] JSONDecodeError silently downgraded to "no detailed run data"** — Render dedicated `<div class="stub error">corrupted run JSON: <name></div>`.
- **[scripts/migrate_feedback_md_to_html.py:30] TOKEN_RE is ASCII-only — Romanian diacritics never tokenize** — `re.compile(r"[^\W\d_]{4,}", re.UNICODE)`.
- **[scripts/test_feedback_html.py:61-87] Test depends on tracked run file — couples tests to mutable session data** — Create temp directory with synthetic run JSON.
- **[scripts/test_feedback_html.py:1-225] Coverage gaps — no tests for log_feedback dedup, mark_outcome, audit_feedback, sidecar map** — Add dedup test, sidecar map round-trip, mark_outcome and audit_feedback happy-path.
- **[scripts/scope_gate.py:192-220] CONSILIUM_FORCE_FULL overridden by config load failure** — Move env override check to top of `main()`, before `load_config`.
- **[scripts/priors.py:197-203] `find_stale_pendings` surfaces entries with empty/missing dates** — Positive guard: `... and e.get("date", "") and e["date"] < cutoff`.
- **[scripts/dialectic_merge.py:124-126] `validate_input` strictly requires all 3 voices in pass1 (uses `sys.exit`)** — Tolerate missing voices as `{}` in `merge()`, or raise instead of `sys.exit`.
- **[scripts/run_evals.py:49-55] `subprocess.run(text=True)` uses platform encoding for stdin/stdout** — Pass `encoding="utf-8"` and `PYTHONIOENCODING=utf-8` in `env=`.
- **[scripts/utils.py:50-65] `validate_keys` calls `sys.exit(1)` — fatal for in-process callers** — Raise `ValidationError`; convert to exit code only in `main()` wrappers.
- **[scripts/probe_change.py:60-84] `parse_numstat` mis-handles rename syntax `{old => new}`** — Pass `--no-renames` to `git diff --numstat`, or parse and expand.
- **[scripts/dialectic_merge.py:122-126] `validate_input` accepts `pass2: [...]` (list) but `merge()` crashes** — `if "pass2" in payload and not isinstance(payload["pass2"], dict): exit/raise`.
- **[scripts/usage.py:96,120] Strict `isinstance(int)` silently drops `tokens_in: 5.0` (float JSON values)** — `isinstance(vdata[f], (int, float)) and not isinstance(vdata[f], bool)`.
- **[SKILL.md:108-110] Confidence input contract for null chosen says wrong thing** — Reword to "the `confidence` field in the response is `null`" + add "Step 5d is skipped in this case".
- **[SKILL.md:240 + Step 5 (parallel)] Parallel mode never mentions Step 5b/5c/5d before Step 6** — Add to Parallel section: "Continue with Step 5b → 6; capture tokens/latency per sub-agent dispatch".
- **[SKILL.md:286-294 (Trias workflow)] Workflow doesn't show JSON schema for Trias report** — Add an "Output JSON" mini-schema example in the Trias section.
- **[prompts/generator.md:47-74 Output format] Example JSON missing `adversarial_skipped` / `unconventional_skipped` siblings** — Add a second example: `{"candidates": [...], "adversarial_skipped": "goal unambiguous", "unconventional_skipped": "trivial doc fix"}`.
- **[prompts/conservator.md:39] Cumulative cap -0.20 vs quality-progress math doesn't add up** — "Apply up to two mitigations; cap total at -0.20. After mitigation 1 (-0.15), budget for mitigation 2 is -0.05 max." Mirror in pass2.
- **[prompts/generator_pass2.md] Pass-2 generator content shape ambiguous — missing summary/sketch/rationale** — Update generator_pass2.md to require full candidate fields (`summary`, `sketch`, `rationale`).
- **[prompts/control_pass2.md (entire)] Pass-2 schema has no escape hatch for `_no_viable_candidate` fallback** — Allow emission of new synthetic verdicts in Pass-2, OR drop the synthetic mechanism entirely.
- **[prompts/pioneer_lens.md/architect_lens.md/steward_lens.md vs SKILL.md] Lens prompts: no link from `voice_bias: prepended` to score-weighting** — Footer in each lens: "Your voice output will be re-weighted by the personality's aggregator weights — focus on perception-shift in your role."
- **[prompts/architect_lens.md:13 vs conservator.md L11] Architect lens "Weight test coverage heavily" overlaps with Control role** — Carve-out: "When applied to Conservator, 'test coverage' bias affects only the `regression_risk` quality-progress adjustment — do NOT inflate risk_score for absent tests."
- **[prompts/steward_lens.md:13 vs generator.md:9] Steward lens "Favor minimal-scope" suppresses Generator divergence** — Per-voice guidance: "When applied to Generator: still produce full 3-5 candidate spread, but order candidates with smaller-blast-radius first; do NOT suppress big-blast-radius candidates."
- **[agents/consilium-subagent.md:40 + 38] Final-message contract: "exactly that file's contents" but description adds extra top-level keys** — Define `subagent_notes` as an optional documented field in validate_report.py and SKILL.md.
- **[agents/consilium-subagent.md:38 vs SKILL.md:163-165] Step 6 confidence override delegated to "no --outcome flag" — different from SKILL.md null branch** — "Use `python -X utf8 scripts/log_feedback.py --run-path runs/<file>.json < runs/<file>.json` with no `--outcome` for both confidence < 0.7 and null cases."
- **[agents/consilium-subagent.md:14-23] Working directory setup uses bash export — Windows PowerShell can't execute verbatim** — Add PowerShell alternative, or wrap in launcher.
- **[prompts/conservator.md:49 vs scripts/aggregator.py] "Matches aggregator.py's expectation" claim is false** — Reword: "There is no automated check that this rule was applied — keep it disciplined manually."
- **[SKILL.md:39 Bootstrap step] "Read the contracts of the 3 voices" enumerates only 3 — skeptic.md and lens prompts not bootstrapped** — Update Step 0: "Read the contracts required by the mode: minimum 3 core; Dialectic adds `*_pass2.md`; Trias adds `<personality>_lens.md`; skeptic modes add `skeptic.md`."
- **[prompts/generator.md:31 + 40] adversarial/unconventional rationale overlap silently disables anti-stagnation** — Tighten (a): "Skip unconventional ONLY when adversarial ALSO varies on a non-scope axis."

### Low (52)
- **[scripts/aggregator.py:148-156] `auto_relax` retry_suggested emits non-actionable suggestion when lowest_risk exceeds RELAXED_VETO_CAP** — Omit `retry_suggested` or replace with `escalation_required` when `lowest_risk > RELAXED_VETO_CAP`.
- **[scripts/aggregator.py:239-309] `aggregate_team_vote` hardcodes abstain reason, losing per-personality context** — `abstained.append({"name": p["name"], "reason": p.get("abstain_reason") or "all candidates vetoed"})`.
- **[scripts/build_report.py:114-131] `_alternatives` emits misleading why_not when chosen=None** — When chosen=None, set why_not based on the candidate's actual veto/risk record.
- **[scripts/build_report.py:174] `int(bundle.get("alternatives_limit", 3))` raises on explicit None** — `alt_limit = int(bundle.get("alternatives_limit") or 3)`.
- **[scripts/build_report.py:78-91] `_why_not` slices `first.get("detail")` with `[:80]` without verifying string** — Add `isinstance(first.get("detail"), str)` guard.
- **[scripts/build_report.py:128-130] `_alternatives` off-by-one: `alternatives_limit=0` emits 1 alt** — Check `if len(out) >= limit: break` BEFORE append, or `if limit <= 0: return []`.
- **[scripts/build_report.py:206] aggregate variable reassigned with subtly different semantics** — Remove reassignment on line 206, reuse existing local.
- **[scripts/validate_report.py:158] VOTE_PATTERN_REGEX accepts impossible 3-voter patterns** — Tighten regex or add post-match sum check.
- **[scripts/validate_report.py:164-201] `_validate_trias` early-returns on personalities shape failure** — Replace `return` with flag; checks should run anyway.
- **[scripts/validate_report.py:164-201] `_validate_trias` doesn't verify weights sum to 1.0 or lens is a string** — Add weights-sum check + `isinstance(lens, str)` check.
- **[scripts/meta_critic.py:162-178] `conservator_spread` returns 0.0 for single candidate, falsely triggering "shrug" flag** — Return None for single-candidate; skip flag when spread is None.
- **[scripts/meta_critic.py:137-139] `_issue_is_concrete` raises TypeError on non-string detail** — `if not isinstance(detail, str): return False`.
- **[scripts/meta_critic.py:82] MAX_RISK_STDEV=0.5 under-normalizes for N≥3** — Compute as a function of N: `max_stdev = sqrt((n//2) * (n - n//2)) / n`.
- **[scripts/retry_context.py:103-119] `_grep_patterns` appends `\(` suffix to dotted symbols that aren't callable** — Only append `\(` for symbols matched by SYMBOL_CALL_RE.
- **[scripts/retry_context.py:65,99,103-110] `extract_targets` accepts multi-word backtick "symbols" yielding non-grep-able patterns** — Tighten `BACKTICK_RE` to `[\w.]{2,40}` or filter quoted entries with whitespace.
- **[scripts/log_feedback.py:108-109,116] `bool` slips past `isinstance(x, (int, float))` and prints as `1.00`/`0.00`** — Exclude bools: `isinstance(x, (int, float)) and not isinstance(x, bool)`.
- **[scripts/mark_outcome.py:144-147] Run-path match falls back to filename-only — can mis-match rows** — Match by `name` only when `wanted` is bare filename; otherwise require exact `as_posix()` equality.
- **[scripts/audit_feedback.py:111] Backfilled row inherits today's note tense** — Append `; backfilled` marker to note text.
- **[scripts/feedback.py:1-9,106] Docstring still describes FEEDBACK.md while code reads FEEDBACK.html** — s/FEEDBACK.md/FEEDBACK.html/.
- **[scripts/feedback.py:27] ROW_RE assumes `class="entry"` is first attribute of `<tr>` — implicit renderer coupling** — Order-agnostic regex `<tr[^>]*class="entry"[^>]*>`, or regression test.
- **[scripts/migrate_feedback_md_to_html.py:117-120] `md_path.rename(bak)` raises on Windows if .bak exists** — Use `os.replace(md_path, bak)`, or check `bak.exists()` before writing HTML.
- **[scripts/test_feedback_html.py:176] `import json` placed mid-file with `# noqa: E402` — fragile order** — Move import to top of file.
- **[scripts/scope_gate.py:213] CONSILIUM_FORCE_FULL emits sentinel `-1` signals not in documented schema** — Use `0` with `"reason": "...override..."`, or add documented `"forced": true` flag.
- **[scripts/priors.py:1] Docstring references `FEEDBACK.md` but code uses `FEEDBACK.html`** — s/FEEDBACK.md/FEEDBACK.html/.
- **[scripts/priors.py:117-149] `find_missing_feedback_runs` truncates `chosen` to 40 chars enabling collisions** — Use full chosen string, or document truncation with longer cap (≥80).
- **[scripts/feedback.py:90-99] `parse_runs` swallows JSON errors silently with no diagnostic** — Emit stderr warning for skipped files.
- **[scripts/dialectic_merge.py:142] Diff includes `revision`/`maintained` fields, producing noisy "modified" entries** — Filter `BOOKKEEPING = {"revision", "maintained"}` from diff keys.
- **[scripts/memory.py:125] Long tier `"total"` reports filtered count, not source total** — Compute `parse_feedback(FEEDBACK)` length, return as `"total"`.
- **[scripts/run_evals.py:97-103] No type-check on loaded scenarios; dict input crashes downstream** — `if not isinstance(scenarios, list): print(..., file=sys.stderr); return 2`.
- **[scripts/utils.py:50] `validate_keys` doesn't verify `data` is a dict** — `if not isinstance(data, dict): raise/exit with clear message`.
- **[scripts/probe_change.py:87-97] `_commit_count` silently returns 0 on git failure** — Distinguish via sentinel (`-1` or None) and log error to stderr.
- **[scripts/usage.py:91-99] Mode-level latency_ms summed across voices is misleading for parallel mode** — Track latency_ms as `max` for parallel mode, or document the field.
- **[scripts/strip_context.py:61,67] `c["id"]` / `v["id"]` raises KeyError on malformed inputs** — Use `c.get("id")` and skip entries with falsy id.
- **[scripts/probe_change.py:65-67] Tab-separated numstat parser silently drops paths containing tabs** — `parts = line.split("\t", 2)` or pass `-z` to git and split by null bytes.
- **[scripts/scope_gate.py:83-98] Case-sensitive `fnmatchcase` lets lowercase `dockerfile` bypass blocklist — "fails open"** — Case-insensitive variant for known-case-insensitive patterns.
- **[scripts/scope_gate.py:91-98] Blocklist patterns with backslashes never match anything** — `pattern = pattern.replace("\\", "/")` mirroring path normalization.
- **[scripts/personalities.py:21-37,84] PERSONALITIES is mutable module-level list; bulk-emit path doesn't deep-copy** — `MappingProxyType` for immutability, or `[copy.deepcopy(p) for p in PERSONALITIES]`.
- **[SKILL.md:144] voice_scores schema example shows 0.0 floats — Generator score never produced by Generator voice** — Add parenthetical: "voice_scores is derived by `build_report.py`, not emitted by voices directly."
- **[SKILL.md:206 + Resources table] dialectic_merge.py description omits silently_dropped recovery** — Skip (cosmetic), or augment Resources table description.
- **[SKILL.md:177-180] Eval harness skill_maintenance lists dialectic_merge.py but personalities.py omitted** — Add `personalities.py` to trigger list at SKILL.md L178.
- **[prompts/generator.md:45 vs dialectic_merge.py:101-112] adversarial_* gets generator_score=0.5; unconventional_* gets 1.0** — Add note in generator.md: "unconventional_* compete on equal footing in voice scoring; adversarial_* and do_nothing get 0.5 generator-score handicap."
- **[prompts/control.md:9] "category: 'types', detail: 'unverifiable — file not accessible'" — no way to emit unverifiable for valid:true candidate** — Add: "When emitting unverifiable issue, prefer `valid: true` and put note in `notes` rather than `issues`."
- **[prompts/conservator.md:51 + SKILL.md:87] rollback_recipe threshold 0.3 — Pass-2 conservator doesn't restate** — Add explicit instruction in conservator_pass2.md: if Pass-1 risk < 0.3 and Pass-2 ≥ 0.3, include new rollback_recipe in `what_changed` prose.
- **[prompts/skeptic.md:48 Output format] `failure_mode` required but no enumerated vocabulary beyond meta_scope_mismatch** — Document expected vocabulary: `regression_risk_uncovered | edge_case_drop | scope_creep | meta_scope_mismatch | ...`.
- **[prompts/generator_pass2.md vs SKILL.md:271] Pass-2 generator schema mismatch** — Reword SKILL.md L271 to clarify revision is a metadata wrapper, not new content.
- **[prompts/control_pass2.md:35] Rule misnamed — Conservator risk *can* surface a correctness concern** — Reword: "Don't revise valid:true because Conservator's aggregate score is high. DO revise if Conservator's factors.regression_risk notes name a concrete failure path."
- **[prompts/pioneer_lens.md/architect_lens.md/steward_lens.md] `voice_bias: prepended` front-matter declared but no code reads it** — Remove front-matter (no consumer), or wire it into the orchestrator template.
- **[agents/consilium-subagent.md:60] Subagent says "appends to runs/ and FEEDBACK.md" — project uses FEEDBACK.html** — s/FEEDBACK.md/FEEDBACK.html/.
- **[agents/consilium-subagent.md:5 model:sonnet vs SKILL.md:251 Sonnet 4.6 default] Model declared as "sonnet" — alias resolves to latest** — Either pin to `claude-sonnet-4-6-...` for reproducibility, or document that subagent tracks the alias.
- **[prompts/skeptic.md:46 + 67] `quoted_scenario` typed inconsistently** — Replace `"Optional: '...' OR null"` literal with comment-style marker.
- **[SKILL.md:69 "3-5 candidate"] Generator candidate budget tension with mandatory roles** — Bump upper bound to 6, or clarify mandatory roles count toward 3-5 budget.
- **[SKILL.md:104 vs SKILL.md:89] Aggregator description omits `risk_score > veto_threshold` veto semantics** — Reword: "veto at `risk_score > 0.8` (strict; 0.80 exact is NOT vetoed, 0.81+ IS)".

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

> Per-senator detail lives in `runs/senate/*.json` (source of truth). This is a de-duplicated index; blocks with live action items are kept in full.

### Senate Resolution — consilium-code-writer-vs-superpowers · 24 May 2026 · MODIFY (GO 0 · MODIFY 2 · STOP 7)
> **Proposal:** Keep Consilium's core identity (multi-agent deliberation where 3 independent voices evaluate every risky code change) but ALSO make it best-in-class at WRITING code (better/faster/smarter than Superpo…

### Senate Resolution — trias-additional-optimizations · 21 May 2026 · MODIFY (GO 3 · MODIFY 4 · STOP 2)
> **Proposal:** Additional optimizations for Trias cost reduction beyond Phase 1 (strip_for_trias) and Phase 2 (lazy routing). Empirical: Trias costs 3.03 USD total on code/01_circuit_breaker with Phase 1 applied (ca…

### Senate Resolution — consilium-modes-efficiency-audit-r2 · 21 May 2026 · MODIFY (GO 6 · MODIFY 3 · STOP 0)
> **Proposal:** Optimize the 3 Consilium modes (sequential, dialectic, trias) for efficiency on budget-constrained tasks. Round 2 focus: candidates A (strip_context per Trias sub-agent) and C (lazy Trias routing to D…

### Senate Resolution — consilium-modes-efficiency-audit · 21 May 2026 · MODIFY (GO 5 · MODIFY 3 · STOP 1)
> **Proposal:** Optimize the 3 Consilium modes (sequential, dialectic, trias) for efficiency on budget-constrained tasks. Trias exhausts the $3 budget cap (4.2M cache_read, $3.01, budget-killed). Proposed candidates:…

### Senate Resolution — law9-senate-scope-definition · 19 May 2026 · MODIFY (GO 2 · MODIFY 7 · STOP 0)
> **Proposal:** Adăugăm Law 9 în Senate care definește când Senate e instrumentul corect — criterii clare de scope, routing, și calificare a propunerilor. Scopul: ca Senate să fie mai inteligent (evită mis-invocări),…

### Senate Resolution — langgraph-sidecar-binary-r2 · 19 May 2026 · MODIFY (GO 1 · MODIFY 2 · STOP 6)
> **Proposal:** Decizie binară: Adoptăm optional_sidecar_visualizer (experiments/langgraph_replay/ izolat) cu 6 invariante verificabile: (1) grep -r 'langgraph|langchain' scripts/ prompts/ agents/ → 0 match-uri (CI g…

### Senate Resolution — langgraph-langchain-integration-audit · 19 May 2026 · MODIFY (GO 0 · MODIFY 3 · STOP 6)
> **Proposal:** Decizie arhitecturală: Ar trebui Consilium skill să integreze LangGraph/LangChain (oricare formă)? Deliberare anterioară (2026-05-16, confidence=0.36): do_nothing câștigat prin eliminare. Candidat via…

### Senate Resolution — consilium-refactor-cleanup-20pct · 19 May 2026 · MODIFY (GO 2 · MODIFY 6 · STOP 1)
> **Proposal:** Refactor Consilium with a 20-30% LOC/bytes reduction target via 5 pure-cleanup actions (zero semantics changed): (1) TODO consolidation 3 files → 1 reorganized by categories; (2) Junk cleanup root (…

### Senate Resolution — claude-md-refactor-r2-AplusC · 19 May 2026 · MODIFY (GO 6 · MODIFY 3 · STOP 0)
> **Proposal:** R2 (revised scope): apply only A (rm duplicate '# CLAUDE.md' H1 on L9) + C (replace 'workflow-ul în 6 pași' with 'workflow-ul în 8 pași', Steps 0..7 excl. sub-step 1.5). B/D/E deferred (B1 pending emp…

### Senate Resolution — claude-md-refactor-and-subdir-files · 19 May 2026 · MODIFY (GO 1 · MODIFY 7 · STOP 0)
> **Proposal:** Refactor Consilium/CLAUDE.md: (A) remove duplicate '# CLAUDE.md' H1 on L9; (B1) delete generic Sections 1-5 entirely OR (B2) keep at bottom + cross-reference; (C) fix 'în 6 pași' to actual SKILL.md st…

### Senate Resolution — deliverable-enforcement-step7-plus-deming-tacitus-integration · 18 May 2026 · MODIFY (GO 2 · MODIFY 7 · STOP 0)

> **Proposal:** feat/deliverable-enforcement: 3 clusters — (A) SKILL.md Step 7 implement expansion 1 line: implement becomes an active instruction with Write tool for files declared in prompt; (B) senate_synth.py: D…

### Senate Resolution — 2-senators-phase-a-r3-final · 18 May 2026 · GO (GO 7 · MODIFY 0 · STOP 0)
> **Proposal:** Phase A re-audit (2026-05-18): Add 2 new senators to Senate mode — Deming (statistical-discipline: hit-rate, calibration, sample size, anti-anecdote) and Tacitus (retrospective-historian: compares pas…

### Senate Resolution — 2-senators-phase-a-r2 · 18 May 2026 · MODIFY (GO 3 · MODIFY 4 · STOP 0)
> **Proposal:** Phase A re-audit (2026-05-18): Add 2 new senators to Senate mode — Deming (statistical-discipline: hit-rate, calibration, sample size, anti-anecdote) and Tacitus (retrospective-historian: compares pas…

### Senate Resolution — 2-senators-phase-a-reaudit · 18 May 2026 · MODIFY (GO 3 · MODIFY 4 · STOP 0)
> **Proposal:** Phase A re-audit (2026-05-18): Add 2 new senators to Senate mode — Deming (statistical-discipline: hit-rate, calibration, sample size, anti-anecdote) and Tacitus (retrospective-historian: compares pas…

### Senate Resolution — deliverable-enforcement-r3 · 18 May 2026 · MODIFY (GO 0 · MODIFY 4 · STOP 3)
> **Proposal:** Add Step 6.5 'Deliverable contract enforcement (auto)' to Consilium SKILL.md (+17 lines, between Step 6 and Step 7). Behavioral rule (text-only, no regex/parsing): if task prompt declares deliverable …

### Senate Resolution — deliverable-enforcement-r2 · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)
> **Proposal:** Step 6.5 in SKILL.md (deliverable contract enforcement, text-only behavioral rule with verify-then-emit gate) was implemented to force Sonnet 4.6 headless to call Write for declared deliverable files.…

### Senate Resolution — pend-triage-ok-outcome · 18 May 2026 · MODIFY (GO 1 · MODIFY 4 · STOP 2)
> **Proposal:** Mark the PEND from 2026-05-15 (run runs/2026-05-15_2236_todo-triage.json, chosen minimal_next_ship, conf=0.52) as OK — the triage was executed substantially: #2-#8 delivered, #16/#17/#20 dropped, #1…

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

### Senate Resolution — benchmark-modes-efficiency-audit · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)
> **Proposal:** Benchmark-modes audit: verify benchmark result analysis and propose efficiency improvements (P1-P6) for consilium modes. P1: output-contract self-verify in final dispatch. P2: cost-aware…

### Senate Resolution — benchmark-report-audit · 18 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)
> **Proposal:** Benchmark framework: verify results, analyze HTML display bugs, efficiency and cost per result, proposals.

### Senate Resolution — blind-benchmark-wrapper · 18 May 2026 · MODIFY (GO 1 · MODIFY 6 · STOP 0)
> **Proposal:** Build an external wrapper (scripts/fix_benchmark_pendings.py) that post-hoc converts PEND entries to PEND_HEADLESS after claude -p finishes, allowing blind evaluation: Claude runs normally with…

### Senate Resolution — bug-audit-dashboard-sync · 17 May 2026 · GO (GO 5 · MODIFY 2 · STOP 0)
> **Proposal:** Audit of HIGH/CRITICAL bugs in the Dashboard_Sync codebase (Python trading dashboard). Identify, prioritize and concretely describe 5-10 bugs that can cause incorrect data, ImportError, or behavior…

### Senate Resolution — refactoring-dedup-dashboard-sync · 17 May 2026 · MODIFY (GO 0 · MODIFY 6 · STOP 1)
> **Proposal:** Refactoring to eliminate duplicate code in the Dashboard_Sync Python codebase. We propose extracting common functions into a shared module (7.Analysis_Clasification/scripts/utils.py). The duplicates id…

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

### Senate Resolution — refactor-bundle-7items · 17 May 2026 · MODIFY (GO 1 · MODIFY 6 · STOP 0)
> **Proposal:** 7-item refactor bundle to reduce Consilium over-engineering (S1 dedup transcripts + S2 collapse skeptic modes + S3 veto cascade 4→2 + S4 delete Dialectic + S5 scripts cleanup + B cross-Qs to user + C R2 prompt on MODIFY). User narrowed scope post-R1 (S3+S4 deferred per Napoleon split); B refined (factual→user, opinion-senator→internal per user Q3).

### Senate Resolution — senate-on-user-code-lens-r3 · 17 May 2026 · GO (GO 7 · MODIFY 0 · STOP 0)

> **Proposal:** R3: senate --on-code via code_domain in renamed domain_lens.md. EXPERIMENTAL_DRAFT until empirical gate (>=3 pilots, >=2/3 info-add, semantic_suspect <=20%). HARD orchestrator pre-compute (Patch 1: ex…

_The Senate approved the proposal. No modifications required._

> **Pilot 1 — 2026-05-17:** `runs/senate/2026-05-17_210550-bug-audit-dashboard-sync.json`. Verdict MODIFY (3GO-2MOD-0STOP). `semantic_suspect` rate = 2/7 = 28.6% (gate criterion ≤20% not met). Cause: senators were dispatched without injection of `code_domain` blocks from `domain_lens.md`. Pilot 2+ must include lens injection per senator via `dispatch_senate_on_code.py`.

### Senate Resolution — per-voice-dispatch-pinning · 17 May 2026 · MODIFY (GO 3 · MODIFY 3 · STOP 1)
> **Proposal:** Add canonical dispatch-defaults table to SKILL.md mapping each voice/senator prompt path to (default model, default tools). Zero new files, zero deletions. 1 file edit (~15-25 lines diff on SKILL.md o…

### Senate Resolution — voices-and-senators-to-subagents · 17 May 2026 · MODIFY (GO 0 · MODIFY 3 · STOP 4)
> **Proposal:** Refactor consilium architecture: voices core (Generator/Control/Conservator/Skeptic) and 7 senators become subagents in agents/; frontend_domain_lens stays as voice. Pass-2 variants and attitudinal le…

### Senate Resolution — phase1-deeply-split-plus-laws-mapping · 17 May 2026 · GO (GO 5 · MODIFY 2 · STOP 0)

> **Status (2026-05-17):** Shipped. One unaddressed item remains.

- [ ] **[SOCRATE — unaddressed]** Coverage table formally disjoint between DEEPLY_SPLIT and the other verdicts (GO/MODIFY/STOP/UNREACHABLE) across all tuples (GO, STOP, MODIFY, ABSENT) summing to 7 — the 5 existing unit tests do not constitute exhaustive boundary coverage.

### Senate Resolution — bundle-2-senators-plus-5-improvements · 17 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)
> **Proposal:** Bundle of 6 modifications to consilium Senate mode: A) add 2 new senators (Deming statistical-discipline, Tacitus retrospective-historian); B.1) codify Laws 1-4 in SKILL.md mapped to 4 Constitution Pr…

### Senate Resolution — test-auto-todo · 16 May 2026 · UNREACHABLE (GO 2 · MODIFY 0 · STOP 0)
> **Proposal:** test proposal

### Senate Resolution — flow-and-modes-audit-r2 · 16 May 2026 · MODIFY (GO 0 · MODIFY 7 · STOP 0)
> **Proposal:** Evaluate all workflow steps (0,1,1.5,2,3,4,5,5b,5c,5d,6) and all modes (Sequential, Dialectic, Trias, parallel_skeptic, dialectic_skeptic, trias_split, skeptic_on_chosen, senate) to determ…

### Senate Resolution — flow-and-modes-audit · 16 May 2026 · MODIFY (GO 1 · MODIFY 5 · STOP 0)
> **Proposal:** Evaluate all workflow steps (0,1,1.5,2,3,4,5,5b,5c,5d,6) and all modes (Sequential, Dialectic, Trias, parallel_skeptic, dialectic_skeptic, trias_split, skeptic_on_chosen, senate) to determ…

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


## 🎯 User directions (open)

> Implemented items removed: code-writing subagents (coder/test/review, parallel) and "analyzed by Senate" — shipped, see the Post-deliberation pipeline item above.

- [ ] **Requirements in YAML** — single source of truth for the skill's requirements/contract.
- [ ] **Enterprise GenAI Roadmap** — evaluate techniques from `Enterprise_GenAI_Roadmap_Alex.pdf` for Consilium (CV/portfolio angle).
- [ ] **Split Consilium / Senate** — move Senate into its own repo, remove from Consilium.
- [ ] **Public-release prep** — make the repo public; plan how to land it in a clean single commit.
- [ ] **Efficiency / model-count audit** — how many sub-agents are actually needed (1/2/3)? vary by complexity? define the target end-state.
- [ ] **EXPLORE → PLAN → CODE → COMMIT workflow** — formalize; relates to the post-deliberation implementation pipeline above.
