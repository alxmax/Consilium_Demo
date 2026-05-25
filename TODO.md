# TODO — single source Consilium (consolidated 2026-05-17, cleaned 2026-05-25)

> All open TODOs + repo bugs in a single file.
> Consolidated from: `TODO.md` (old), `TO_DO_Consilium.md` (prompts/skill audit), `BUGS.md` (audit 2026-05-16, 107 findings, previously gitignored).
>
> The reference document `experiments/New phase senat/todos/SENAT-todo-rol-legi-functii.md` remains as conceptual specification (not an actionable TODO).

## Table of Contents

1. [❌ NOT IMPLEMENTED](#-not-implemented)
2. [🤔 UNRESOLVED DECISIONS](#-unresolved-decisions)
3. [🔧 Prompts & skill audit (items #9, #43, #45-#50)](#-prompts--skill-audit)
4. [🏛 Senate Resolutions](#-senate-resolutions)
5. [Rollback hooks](#rollback-hooks)
6. [🎯 User directions (open)](#-user-directions-open)

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

- [ ] **Re-test implementation pipeline before promoting:** add ≥3 more refactor-regime tasks; confirm the win rate holds (n=3 / 1 win is a pilot signal, not proof — Deming). Context: pipeline shipped as opt-in EXPERIMENTAL_DRAFT (`feat/implement-pipeline-scaffold`), kill-criterion not met (wins < 2/3), scoped to refactor/bugfix/regression-risk only.

- [ ] **Veto budget for `meta_recommendation`: is 5/month acceptable?** Aurelius+Napoleon proposed it, but the number is arbitrary. You might prefer 10 or 3.
- [ ] **Outcome tracking — manual or automatic?** For trading it can be automatic from MT4. For other domains it requires manual completion. If not, `principle_extraction` never activates.

---


## 🔧 Prompts & skill audit

> Source: `TO_DO_Consilium.md` (now consolidated). Ranked by impact/effort. Categories: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch**.

### Follow-up eval parity · Senate MODIFY 2026-05-25

> **Senate verdict:** MODIFY (GO 3 · MODIFY 5 · STOP 1) — `runs/senate/2026-05-25_081222-eval-parity-rest.json`
>
> **Key finding:** `audit_feedback.py` + `mark_outcome.py` already have `--feedback`/`--runs-dir` flags. Only `memory.py` + `priors.py` hardcode `ROOT` — immune to cwd-switch. Approach A (fixture_files + cwd) doesn't work for them.

**Mandatory before implementation:**
- [ ] Add `--feedback-file` / `--runs-dir` to `memory.py` + `priors.py` only (not all 4)
- [ ] No `fixture_files` extension to `run_evals.py` — preserve stdin_json pattern
- [ ] Anchor `stale_pendings` dates relative to `date.today()` in fixtures — prevents daily drift
- [ ] Clarify headless suppression (priors.py zeroes `stale_pendings`/`missing_feedback_runs` under non-TTY)
- [ ] Start with 1-2 scenarios on highest-risk script first, not all 9 at once
- [ ] Each scenario must assert a concrete output field that flips on regression (no exit==0-only)
- [ ] Note in scenarios.json: synthetic fixtures validate code-path coverage only, not semantic correctness

**Scope:** ~9 scenarios via stdin_json+args, implement in dedicated session.

### Open items (Tier 2)

#### Substance-validation gap (accepted) · Arch · INVESTIGATE
`validate_report.py` checks report SHAPE only — no enforced gate that the voices did substantive (non-vacuous) work. `meta_critic.py` is advisory and now trimmed to a single `conservator_spread` heuristic. Accepted as a known gap (Senate 2026-05-24 MODIFY; Socrate). Revisit only if empty-but-schema-valid deliberations are observed in practice; minimal fix would be a ~20-line minimum-reasoning heuristic inside `validate_report.py` (Musk). Noted in `validate_report.py` docstring.

---

## 🏛 Senate Resolutions

### Senate Resolution — eval-parity-script-flags · 25 May 2026 · MODIFY (GO 4 · MODIFY 5 · STOP 0)

> **Proposal:** Add --feedback-file and --runs-dir CLI flags to memory.py and priors.py. These are the only 2 of the 4 eval-relevant scripts that still hardcode ROOT-anchored paths (ROOT = Path(__file__).resolve().pa…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Pin the override mechanism to ONE approach and write it into the proposal. Recommended: explicit Path parameters threaded into build_priors() defaulting to current constants. Guard priors.py lines 231 and 244 (str(FEEDBACK.relative_to(ROOT)) raises ValueError for out-of-ROOT fixtures). Add a falsification check: scenario with fixture yields source.feedback_total == fixture row count AND default FEEDBACK.html content is absent. State explicitly what happens to existing flagless memory.py/priors.py scenarios.
- [ ] **[CONFUCIUS]** Resolve the flag-name inconsistency before merging: either rename '--feedback-file' to '--feedback' in memory.py and priors.py to match audit_feedback.py, or explicitly document why the names differ. Additionally, clarify whether mark_outcome.py intentionally omits '--runs-dir'.
- [ ] **[SOCRATE]** Two load-bearing gaps before GO: (1) Guard priors.py lines 231 and 244 — an override path outside the repo raises ValueError; fall back to str(path) when not relative to ROOT. (2) Add a falsification test with a sentinel-bearing fixture asserting BOTH that the sentinel appears AND default content is absent. Prefer global reassignment in main() over parameter-threading to avoid missing the 4 RUNS/FEEDBACK call sites in build_priors.
- [ ] **[MUSK]** Ship only the priors.py flags (--feedback-file + --runs-dir). Put memory.py flags on hold pending a code-level proof that memory.py performs independent I/O that priors.py flags cannot cover. Scope drops to ~15 lines across 1 file. Write 1 scenario per new flag before merging.
- [ ] **[DIMON]** (1) Audit parse_feedback() and parse_runs() to confirm they read reassigned module globals, not closures. If closures detected, refactor to pass FEEDBACK/RUNS as function arguments. (2) Convert --feedback-file and --runs-dir to absolute paths in main() before use. (3) Add validation in parse_runs(): log and skip malformed .json. (4) Add integration test: call priors.py with --feedback-file <fixture>, verify output differs from production.

### Senate Resolution — eval-parity-scenario-design · 25 May 2026 · MODIFY (GO 3 · MODIFY 6 · STOP 0)

> **Proposal:** Scenario design protocol for eval-parity-rest implementation. After adding --feedback-file/--runs-dir to memory.py + priors.py (separate proposal), write the first 2 scenarios for priors.py (highest-r…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** (1) Fix scenario (a) fixture: 1 confirmed BAD + 1 unconfirmed BAD yields weighted_bad_rate == bad_rate == 1.0 — inequality is FALSE. Change fixture to have mixed outcomes (e.g. 1 confirmed BAD + 1 unconfirmed OK) and pin both values. (2) Fix scenario (b): --headless zeroes stale_pendings unconditionally BEFORE date logic — run non-headless and assert 2020-01-01 entry IS present. (3) priors.py has no --feedback-file/--runs-dir flags — add them or define done-criterion of prerequisite. (4) Specify fixture mechanism (committed evals/fixtures/*.html or harness change). (5) Make doc_note a checkable property or downgrade to non-asserted comment.
- [ ] **[AURELIUS]** Prefer static fixture files in evals/fixtures/ over dynamic tempfile generation in run_evals.py. If run_evals.py needs fixture-injection support, scope that change minimally and keep it separate from the scenario JSON entries.
- [ ] **[CONFUCIUS]** (1) PREREQUISITE — add --feedback-file flag to priors.py in the same change as the scenarios; without it both scenarios fail with exit 2. (2) DETERMINISM — scenario (a) must also pass --no-runs to prevent priors.py from scanning production runs/ from ROOT. (3) DOC — add a fixture note to evals/README.md clarifying evals/fixtures/ contains synthetic HTML, coverage-only.
- [ ] **[SOCRATE]** (1) priors.py has no --feedback-file/--runs-dir — either add them or the scenarios exit 2. (2) Scenario (b) is a tautology: --headless blanks stale_pendings unconditionally — redesign as NON-headless asserting the 2020-01-01 row IS surfaced. (3) Scenario (a) fixture arithmetically yields bad_rate==weighted_bad_rate==1.0 — change to mixed outcomes. (4) Mutation-verification is a manual author-time check only — run_evals.py carries no expect-fail hook.
- [ ] **[MUSK]** Reduce to minimum viable: (1) one scenario only — scenario (a) for weighted_bad_rate; (2) no fixtures directory — inline the input or use a single flat file under evals/; (3) no doc_note field; (4) mutation check is a dev-time manual step, not a documented implementation artifact. If scenario (a) ships and catches a real regression within 2 weeks, scenario (b) and fixtures dir earn re-evaluation.
- [ ] **[DIMON]** (1) Add isolation verification: run scenario (a) with --runs-dir /tmp/empty and confirm priors.py does NOT read production ROOT/runs/. (2) Add fixture schema validation before subprocess. (3) Document fixture maintenance: when STALE_PEND_DAYS changes, which fixtures must be regenerated? (4) Automate mutation-verification rollback. (5) Verify --headless end-to-end in CI simulation.
- [ ] **[NAPOLEON]** Vote GO for the proposal content, but defer execution to next session. If the operator is willing to timebox to 20 minutes right now (fixtures only, JSON entries, no documentation), GO immediately — otherwise log as next-session opener and close this Senate thread cleanly.

### Senate Resolution — eval-parity-rest · 25 May 2026 · MODIFY (GO 3 · MODIFY 5 · STOP 1)

> **Proposal:** Follow-up eval parity — add ~9 new scenarios to evals/scenarios.json covering memory.py (medium/long tiers), audit_feedback.py (orphan detection + backfill idempotency), mark_outcome.py ([confirmed] m…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Before implementation, the proposal must make three things operational: (1) Per-scenario assertion spec — name the exact output field/exit-code asserted per scenario that would flip on regression. (2) Resolve the path-resolution split: memory.py and priors.py resolve FEEDBACK/RUNS from __file__-relative ROOT — cwd change does NOT redirect them; mark_outcome.py and audit_feedback.py already have --feedback/--runs-dir flags. (3) Pin determinism: anchor stale_pendings fixture dates relative to date.today() so assertions don't drift daily; clarify headless suppression of stale_pendings/missing_feedback_runs.
- [ ] **[AURELIUS]** One guard required before merge: run_evals.py fixture_files handling must raise an explicit error on temp-dir setup failure — must not silently skip the scenario and mark it PASS.
- [ ] **[CONFUCIUS]** Pursue the alternative: add --feedback-file and --runs-dir CLI flags to the 4 scripts instead of extending run_evals.py. This keeps all 9 new scenarios as pure stdin_json, preserves the established deterministic contract, and improves production script testability as a side effect. The fixture_files extension breaks the stdin_json pattern that has been stable for 50+ scenarios.
- [ ] **[SOCRATE]** Correct the factual premise first: audit_feedback.py and mark_outcome.py ALREADY expose --feedback/--runs-dir and resolve from cwd. Only memory.py and priors.py hardcode ROOT-anchored paths and are immune to Approach A. Minimal path: add flags to memory.py and priors.py only, write all 9 scenarios as stdin/args — no harness change. Also: make priors date-deterministic for eval and add mutation-verification step per scenario.
- [ ] **[MUSK]** Reject fixture_files harness extension and evals/fixtures/ directory entirely. Start minimal: add --feedback-file flag to the highest-risk script (audit_feedback.py or priors.py), write 1 scenario, verify it catches a real regression. Defer the other 3 scripts until a regression proves the need. The gravitational pull of fixture_files on future tests is the real cost — once the paradigm exists, every author reaches for it.
- [ ] **[DIMON]** The fixture approach is architecturally unsound. Scripts use Path(__file__).resolve().parent.parent — cwd changes are ignored. Fixtures written to temp dir are never read. This is a silent failure: tests pass while asserting nothing real. Must resolve the ROOT path problem before ANY fixture scenarios: add explicit --root-dir/--feedback-file flags to scripts OR pass ROOT as env var. Test ONE scenario end-to-end first to verify fixtures are actually read by the subprocess.
- [ ] **[NAPOLEON]** Scope down to 3-4 scenarios covering only critical-path scripts (priors.py stale detection, audit_feedback.py orphan detection). Implement in a dedicated future session, not appended to current cleanup context. Defer full 9-scenario parity until AUDIT_TODO.md harness fixes are addressed so both land in one coherent branch.
- [ ] **[DEMING]** Document in scenarios.json that priors.py tests use synthetic fixtures and validate code-path coverage only, not semantic correctness on real FEEDBACK.html/runs/*.json data.

### Senate Resolution — kill-meta-critic-r2 · 24 May 2026 · MODIFY (GO 5 · MODIFY 3 · STOP 1)

> **Proposal:** Remove scripts/meta_critic.py — the Step 5c deliberation-quality scorer (advisory, 345 lines, not enforced).

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Remove generator_divergence + control_concreteness (0/163 fires = dead weight); retain conservator_spread; confirm build_report degrades gracefully on absent key.
- [ ] **[CONFUCIUS]** Move to scripts/deprecated/; mark Step 5c retired noting the 2026-05-16 keep+fix verdict was never executed; passthrough no-op one cycle; log a closing record.
- [ ] **[SOCRATE]** Document the substance-vs-shape validation gap (in validate_report.py + a tracked TODO) so removal doesn't become invisible debt.
- [ ] **[DIMON]** Safe-removal checklist: patch build_report refs; update docs incl. 2 superpowers; note validate_report shape-only; log FEEDBACK entry.
- [ ] **[DEMING]** PATH A: accumulate n>=10 then recheck. PATH B (no n>=10 needed): remove generator_divergence + control_concreteness (0/163 = strong dead-code evidence), redesign/annotate conservator_spread rather than silent-delete. Either path accepted; wholesale delete as-is: STOP.
- [ ] **[TACITUS]** correct historical record; close #27/#28; drop passthrough + legacy readers

**B. Actionable items (extracted from requests above):**

- [ ] **B** (cross-ref: DEMING)

### Senate Resolution — kill-meta-critic · 24 May 2026 · MODIFY (GO 4 · MODIFY 4 · STOP 1)

> **Proposal:** Remove scripts/meta_critic.py — the Step 5c deliberation-quality scorer (advisory, 345 lines, not enforced). Delete the script, remove Step 5c from SKILL.md, drop the build_report.py passthrough, upda…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Before GO: (1) operationally define the numeric thresholds inside meta_critic that would be lost on deletion (document them or declare they have no empirical basis); (2) turn 'rarely non-empty' into a verifiable count with a false-negative estimate; (3) confirm build_report consumers handle a permanently absent deliberation_quality key with no silent behavior change.
- [ ] **[CONFUCIUS]** (1) Document why the prior decision stalled; (2) move to scripts/deprecated/ rather than hard-delete (project precedent: migrate_feedback_md_to_html.py); (3) mark SKILL.md Step 5c 'retired' with rationale, don't silently drop it; (4) keep build_report passthrough as a no-op stub with a deprecation comment for one cycle.
- [ ] **[SOCRATE]** Before deletion: (1) audit runs/ to quantify flag frequency and any correlation with human-identified low-quality runs; (2) resolve whether the prior non-execution was backlog or intentional hold; (3) specify what replaces the substantive-quality check before the passthrough is dropped.
- [ ] **[DIMON]** Before removal: (1) enumerate+patch all build_report.py reference sites (no KeyError path); (2) list+update every doc referencing Step 5c/meta_critic (incl. 2 superpowers docs); (3) add a note in validate_report.py that it is shape-only not substance, preserving the distinction in tooling; (4) define a post-removal observable signal substituting for the lost quality signal.
- [ ] **[DEMING]** Produce a count over runs/: (1) total runs with deliberation_quality, (2) subset where meta_critic was actually invoked, (3) subset with non-empty flags given invocation, (4) subset where flags appear downstream. If (3)/(2)<5% AND (4)=0 across n>=10 invoked runs, removal is supported; else instrument and collect first.
- [ ] **[TACITUS]** Not blocking: correct the historical record in the report (cite runs/2026-05-16_0148_voice_audit_meta.json accurately); close TODO #27/#28 as moot; drop the build_report.py passthrough AND any optional readers of deliberation_quality so the ~21 legacy runs with the field don't break validate_report.

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
