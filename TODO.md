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

### Investigate: senate_transcript.py — RESOLVED (2026-05-25)

> **Status:** RESOLVED. Git pull 2026-05-25 added `scripts/senate_transcript.py` directly (option a). `senate_synth.py:758` loads from `scripts/senate_transcript.py` — no longer from `scripts/deprecated/`. The `deprecated/` copy is an archived duplicate.
>
> Option (c) — support for diagnostic schema (`top_5 + honorable_mentions`) remains a nice-to-have, tracked separately below.

- [x] Re-promoted from `scripts/deprecated/` to `scripts/` — done via git pull (2026-05-25).
- [ ] **(nice-to-have, separate)** Extend `senate_transcript.py` to support diagnostic schema (`top_5 + honorable_mentions`) as a first-class option.

### Usage & Efficiency reporting — IMPLEMENTED (2026-05-25)

> **Design:** `experiments/usage-efficiency-proposal-pending.md` (all 4 design questions resolved).
> **Consilium deliberation:** `runs/2026-05-25_1054_efficiency-design-q1q4.json` — Q1 user-confirmed: MODIFY → OK.

- [x] **`scripts/efficiency.py`:** `personalities` key support added (Q3 — flat trias schema: pioneer/architect/steward). `--self-test` passes.
- [x] **`scripts/usage.py`:** SENATORS tuple extended to include `deming` + `tacitus` (9 senators).
- [x] **`runs/README.md`:** telemetry schema documented for `senators`, `personalities`, `dispatch_count`, and totals.
- [x] **SKILL.md Step 6 telemetry:** mandatory emission discipline already present in SKILL.md (chars/4 per dispatch, voices/senators/personalities keys).
- [x] **UI tab:** "Usage & Efficiency" section (§12) added to `docs/architecture.html` — mode cost table, tokens_per_OK bar chart, CLI commands, caveats.

---

## 🤔 UNRESOLVED DECISIONS

- [x] **Re-test implementation pipeline — DONE (2026-05-25):** Added 3 refactor-regime tasks (T4/T5/T6). R2 result: 0 wins / 3 ties (all arms tied at full oracle score). Combined R1+R2: 1 win / 5 ties / 0 losses (n=6). Graduation criterion NOT met (need ≥2/3 wins). Pipeline stays EXPERIMENTAL_DRAFT, opt-in only. Key finding: pipeline value is specific to *semantically-isolated* secondary branches (T3 pattern) — algebraically-obvious paths (T4/T5) and trivial substitutions don't need it. T6 has valid T3-pattern structure but arm A prompt was compromised; marked invalid. See `experiments/pipeline-bench/RESULTS.md`.

- [ ] **Veto budget for `meta_recommendation`: is 5/month acceptable?** Aurelius+Napoleon proposed it, but the number is arbitrary. You might prefer 10 or 3.
- [ ] **Outcome tracking — manual or automatic?** For trading it can be automatic from MT4. For other domains it requires manual completion. If not, `principle_extraction` never activates.

---


## 🔧 Prompts & skill audit

> Source: `TO_DO_Consilium.md` (now consolidated). Ranked by impact/effort. Categories: **Prompt** (prompts/*.md), **Skill** (SKILL.md + scripts), **Arch**.

### Follow-up eval parity · Senate MODIFY 2026-05-25

> **Senate verdict:** MODIFY (GO 3 · MODIFY 5 · STOP 1) — `runs/senate/2026-05-25_081222-eval-parity-rest.json`
>
> **Key finding:** `audit_feedback.py` + `mark_outcome.py` already have `--feedback`/`--runs-dir` flags. Only `memory.py` + `priors.py` hardcode `ROOT` — immune to cwd-switch. Approach A (fixture_files + cwd) doesn't work for them.

**Status: flaguri implementate, 3 scenarii de bază trec — rămâne nota de documentare în scenarios.json.**

- [x] Add `--feedback-file` / `--runs-dir` to `memory.py` + `priors.py` only — implementat
- [x] No `fixture_files` extension to `run_evals.py` — constrângere respectată (stdin_json pattern intact)
- [x] Anchor `stale_pendings` dates — `evals/fixtures/priors_stale_pendings.html` folosește 2020-01-01 (nu driftează)
- [x] Clarify headless suppression — documentat în `priors.py` docstring + SKILL.md Step 0
- [x] Start with 1-2 scenarios on highest-risk script first — 2 scenarii priors + 1 memory PASS
- [x] Each scenario must assert a concrete output field — scenariile 56/57 verifică câmpuri specifice
- [x] Note in scenarios.json: synthetic fixtures validate code-path coverage only, not semantic correctness — added `note` field to scenarios 56/57 (`priors/weighted_bad_rate`, `priors/stale_pendings`); runner ignores the key, both still PASS

### Open items (Tier 2)

#### Substance-validation gap (accepted) · Arch · INVESTIGATE
`validate_report.py` checks report SHAPE only — no enforced gate that the voices did substantive (non-vacuous) work. `meta_critic.py` is advisory and now trimmed to a single `conservator_spread` heuristic. Accepted as a known gap (Senate 2026-05-24 MODIFY; Socrate). Revisit only if empty-but-schema-valid deliberations are observed in practice; minimal fix would be a ~20-line minimum-reasoning heuristic inside `validate_report.py` (Musk). Noted in `validate_report.py` docstring.

---

## 🏛 Senate Resolutions

### Senate Resolution — efficiency-explore-commit-audit · 25 May 2026 · MODIFY (GO 2 · MODIFY 6 · STOP 1)

> **Proposal:** Two architecture proposals for Consilium skill.

Proposal 1 — Efficiency/model-count audit: How many sub-agents does Consilium actually need? Should the count vary with task complexity? Define the tar…

**A. Per-senator decisions:**

- [ ] **[WITTGENSTEIN]** Both proposals lack rejection criteria. P1: replace 'actually need' with a floor-based test; bind 'task complexity' to the existing measured `magnitude` axis or name the new signal explicitly; express 'target end-state' as a diff-checkable artifact — the post-audit mode set plus a deterministic count→signal routing table. P2: declare whether 'formalize' means ENFORCED (numbered Steps with validate_report-checkable field) or DESCRIPTIVE (OTAL-style reading-aid with 'no new behavioral contracts' disclaimer); define EXPLORE's done-condition against Step 0/1 and COMMIT's relationship to CLAUDE.md git workflow.
- [ ] **[CONFUCIUS]** Proposal 1: MODIFY — the audit is institutionally sound, but must follow the precedent: (a) pre-register a kill-criterion and decision rule before any sub-agent count changes reach SKILL.md, (b) account for the Trias 9→3 budget-kill precedent by pairing any count reduction with a budget backstop. The audit question is GO; implementation without pre-registered criteria is MODIFY. Proposal 2: MODIFY — do not formalize EXPLORE or COMMIT into SKILL.md Steps 0–7. The OTAL framing already captures the descriptive shape and was explicitly blessed as docs-only. If formalization is desired, limit to updating the existing descriptive section with EXPLORE/COMMIT labels, not adding new behavioral steps. COMMIT belongs in CLAUDE.md, not SKILL.md.
- [ ] **[SOCRATE]** Both proposals carry undeclared load-bearing premises that must be declared before GO. P1: (a) declare whether the target is count-reduction or escalation-correctness; (b) declare a falsifiable kill-criterion per mode using an independent-oracle correctness measure. P2: (a) declare that COMMIT rules are already owned by CLAUDE.md and resolve the dual-source-of-truth risk; (b) declare the invariant 'formalization must be purely additive and touch no Step 0–7 numbering, or it is a breaking schema change.'
- [ ] **[MUSK]** Proposal 1: delete the audit work item; if warranted, add a single routing sentence to SKILL.md citing the existing benchmark cost/correctness finding. Proposal 2: delete entirely — EXPLORE duplicates Step 1, COMMIT duplicates CLAUDE.md, and the macro-framework adds no behavior, only renaming. Both proposals fail the deletion test.
- [ ] **[DIMON]** P1 must define the routing heuristic with an explicit fallback: when uncertain, MUST default to higher sub-agent count, not lower. n=6 is insufficient to support a mode-removal decision — minimum oracle-validated n≥20 with architectural ambiguity tasks required before removal. P2 must specify whether EXPLORE and COMMIT are mandatory or advisory for headless invocations, and must include a migration path for existing CI integrations.
- [ ] **[NAPOLEON]** Split the two proposals into separate verdicts: P2 (EXPLORE→PLAN→CODE→COMMIT) is GO — low cost, favorable terrain, actionable now. P1 (sub-agent efficiency audit) is STOP until benchmark n≥20 across diverse task types — current data is thin and terrain is stretched from the Senate split. Acting on P1 today risks compounding architectural churn without sufficient empirical grounding.
- [ ] **[DEMING]** For P1: (a) produce the Trias-vs-Sequential paired corpus (n≥5 tasks, same spec both arms, oracle-validated correctness, token+wall-clock variance per task) before invoking the cost-ratio in any architectural decision; (b) reconcile the n=6 pipeline benchmark figure — either surface the 6th result file or correct to n=5.

**B. Actionable items (extracted from requests above):**

- [ ] **P1** (cross-ref: WITTGENSTEIN, SOCRATE, DIMON, NAPOLEON, DEMING)
- [ ] **P2** (cross-ref: WITTGENSTEIN, SOCRATE, DIMON, NAPOLEON)

### Senate Resolution — pipeline-simplification-5phases · 25 May 2026 · MODIFY (GO 1 · MODIFY 8 · STOP 0) — **RESOLVED**

> Tabelul "Pipeline at a glance" (5 Stage-uri → 12 pași) + "Pipeline Invariants" adăugate în SKILL.md liniile 38-58. Variant A livrată, scripts/ neatinse, 58/58 evals PASS.

### Senate Resolution — eval-parity-script-flags · 25 May 2026 · MODIFY (GO 4 · MODIFY 5 · STOP 0) — **RESOLVED**

> Flaguri `--feedback-file` / `--runs-dir` implementate în `memory.py` + `priors.py`. Guard `_rel_or_str` prezent în `priors.py` (ValueError pentru căi în afara ROOT). Global reassignment în `main()`. Scenariile 56/57 din `evals/scenarios.json` validează flagurile cu fixture-uri reale.

### Senate Resolution — eval-parity-scenario-design · 25 May 2026 · MODIFY (GO 3 · MODIFY 6 · STOP 0) — **RESOLVED**

> Scenariile de design au fost implementate: fixture-uri statice în `evals/fixtures/`, pattern stdin_json+args, câmpuri concrete verificate. Scenariile 56 (weighted_bad_rate) și 57 (stale_pendings) PASS. Rămâne nota de documentare în `scenarios.json` (vezi "Follow-up eval parity" mai sus).

### Senate Resolution — eval-parity-rest · 25 May 2026 · MODIFY (GO 3 · MODIFY 5 · STOP 1) — **PARȚIAL RESOLVED**

> Blocajul principal (path-resolution) rezolvat via `--feedback-file`/`--runs-dir`. Scenariile de bază există și trec. Rămâne: nota de documentare în `scenarios.json` (Deming) + scenariile suplimentare pentru `memory.py` medium/long tiers dacă se dovedesc necesare empiric.

### Senate Resolution — kill-meta-critic-r2 · 24 May 2026 · MODIFY (GO 5 · MODIFY 3 · STOP 1) — **RESOLVED**

> `scripts/meta_critic.py` mutat în `scripts/deprecated/`. Step 5c marcat "retired 2026-05-25" în SKILL.md. `generator_divergence` + `control_concreteness` eliminate (0/163 fires); `conservator_spread` reținut. Substance-validation gap documentat în `validate_report.py` docstring + TODO.md Tier 2.

### Senate Resolution — kill-meta-critic · 24 May 2026 · MODIFY (GO 4 · MODIFY 4 · STOP 1) — **SUPERSEDED de kill-meta-critic-r2 (RESOLVED)**

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

### Follow-up — feat/senate-senators-deming-tacitus — **MOOT (Senate split 2026-05-25)**

> Senate a fost mutat în repo separat pe 2026-05-25. `senate_synth.py`, `tacitus.md`, SENATORS tuple, QUORUM, vote_counts, demotion Phase B — toate sunt acum în repo-ul `Senate`. Follow-up-urile de mai jos nu mai aparțin Consilium.

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
    - [x] **#1-A** Drop the `pstdev > 0.15` check din AC — retras (max observat 0.10, niciodată nu ar fi tras).
    - [ ] **#1-B** Add a categorical-stability check: sample Conservator twice; surface `magnitude`/`reversibility` disagreement to orchestrator (don't auto-resolve). Catches the 40% flip rate at its source.
    - [ ] **#1-C** Re-run with 2-3 cases that produce `net_concern ∈ [0.7, 0.9]` to probe the veto-threshold variance region (F4 gap).
    - [ ] **#1-D** Probe Generator + Control stability (untested here — Wittgenstein's asymmetry claim is half-supported by this experiment).
    - [x] **#1-E** SKILL.md edits — **RESOLVED** — veto caveat adăugat la Step 5 conservative_override + nota calibrare asimetrică la Step 5b (PR fix/skill-calibration-caveat, 2026-05-25).

- [x] **#4-followup [MED] subagent-output-contracts-for-6-remaining-gates** — **RESOLVED**
  - `agents/consilium-subagent.md` rule 2 conține regula generică `blocking_gates` (BLOCK → `blocked_reason` + `confidence: null` + `chosen_approach: null`) + contracte explicite pentru toate 6 gate-urile non-BLOCK: REWORK, ADAPT_SHORT, ADAPT_EXTENDED, challenge_upward, retry_context, scale_up.

**Honorable mentions (medium severity):**

- [x] **HM1 [MED] meta_recommendation_per_candidate_vs_pipeline** — **RESOLVED** — `aggregator.py:352-355` citește `meta_recommendation` din `conservator_out["scores"][i]`, nu top-level. `scale_up`/`scale_down` se activează corect.
- [x] **HM2 [MED] trias_cost_gate_soft_not_enforced** *(Aurelius)* — **RESOLVED (deviation noted)**
  - `mode_ceiling` field shipped in `64835c7`: `low→sequential`, `medium→dialectic`, `high→trias`; blocklist hits force `high→trias` (`scope_gate.py` `_MODE_CEILING`).
  - **Deviation from original AC:** ceiling derives from the LOC/files `magnitude` proxy, NOT from Conservator `irreversibility × magnitude`. By design — `scope_gate.py` runs *pre-deliberation*, so Conservator output does not exist at gate time; deriving from it would be circular. The proxy is the only signal available before voices run, and the gate fails OPEN.
- [x] **HM3 [MED] pilot_b_unenforced_activation_gate** — **MOOT** — Pilot B era despre Senate mode, acum split în repo separat.
- [x] **HM4 [HIGH] skeptic_catchrate_overgeneralized_from_P3** — **RESOLVED** — SKILL.md linia 719 adăugat scope caveat explicit: "(n=1 problem — P3 car wash only; generalizability unconfirmed until ≥3 distinct problems tested)".

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
- ~~**R.3** Senate cost~~ — moot (Senate split în repo separat 2026-05-25).
- ~~**R.4** Napoleon over-fitting~~ — moot (Senate split în repo separat 2026-05-25).

---

**End of consolidated TODO.**


## 🎯 User directions (open)

> Implemented items removed: code-writing subagents (coder/test/review, parallel) and "analyzed by Senate" — shipped, see the Post-deliberation pipeline item above.

- [x] **Enterprise GenAI Roadmap** — evaluated via Senate (`enterprise-genai-roadmap-cv-strategy`, MODIFY · GO 1 / MODIFY 7 / STOP 1, 2026-05-26). Outcome: README "Competencies demonstrated" matrix (Full/Partial/n.a) + honest "Why not LangGraph" note citing the recorded reject grounds; metric claims kept honest (telemetry instrumented; aggregate efficiency figures labelled illustrative until n grows — Deming). Breadth (RAG/backend/cloud) routed to the §6 showcase below, not bolted onto Consilium.
- [x] **Split Consilium / Senate** — Senate split into its own standalone skill repo (`Senate`, https://github.com/alxmax/Senate) on 2026-05-25; all senator prompts, `senate_*.py`, `docs/senate*`, and the `--strict-senate` validator removed from Consilium.
- [ ] **Public-release prep** — make the repo public; plan how to land it in a clean single commit.
- [ ] **Efficiency / model-count audit** — how many sub-agents are actually needed (1/2/3)? vary by complexity? define the target end-state.
- [ ] **EXPLORE → PLAN → CODE → COMMIT workflow** — formalize; relates to the post-deliberation implementation pipeline above.
- [ ] **§6 Showcase project — "AI Incident Investigation & Knowledge Copilot"** (separate repo) — carries the breadth Consilium deliberately excludes: RAG over PDFs + DLT/automotive logs, Jira/Confluence ingestion, hybrid search + reranking, a FastAPI backend, eval dashboards. Per the Senate audit above, this — not more Consilium polish — is the highest-leverage CV move for Enterprise-GenAI/RAG roles (Napoleon, Aurelius, Deming). Consilium stays the deep agentic/LLMOps artifact; §6 is the breadth artifact.
