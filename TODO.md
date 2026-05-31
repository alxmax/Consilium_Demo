# TODO — Consilium (cleaned 2026-05-26)

---

## 🐞 Bug audit (2026-05-31) — multi-agent, **v1.0 BLOCKERS**

> **✅ Implementation status (2026-05-31) — branch `fix/bug-audit-implementation` (7 commits; pyright 0, run_evals 72/0, test_rund2 + test_feedback_html green throughout).** **25 / 37 fixed**, including **all 4 Criticals**. **10 deferred** to a `/consilium`-deliberated pass — these are NOT safe one-liners (semantics / coordinated fixture rewrite / calibration / cross-platform locking):
> - `aggregator.py:344` conservator nesting + `build_report.py:192` non-chosen result shapes — change BLOCK/aggregation semantics and need the masking `test_rund2` fixture rewritten in lockstep.
> - `log_feedback.py:215` PEND→OK in-place upgrade — close-the-loop workflow design (append vs update).
> - `modes/trias.md:5` Trias floor 0.80 — calibration decision (mirrored in `confidence.py` + `SKILL.md` + drift gate).
> - `audit_counter.py` cmd_increment lock (CONTESTED), cmd_check idempotency, HOT→DEFAULT window — concurrency/cadence semantics (save_state atomicity already fixed).
> - `infer_pipeline.py:58` reversibility-floor bucketing — heuristic; current behavior errs conservative/safe.
> - `verify.py:344` IndexError guard + `aggregator.py:318` ESCALATE docstring — small follow-ups.
>
> The 2 reclassified items remain non-bugs. Every other finding below is fixed on the branch.

> **✅ Deferred pass RESOLVED (2026-05-31) — `/consilium` Sequential, chosen `scoped_helpers_split_surface`, conf 0.575** (run `.consilium/runs/2026-05-31_1545_deferred-bugs-fix-plan.json`). **9 / 10 fixed, 1 deferred with rationale.** The deliberation rejected the "single shared schema accessor module" as over-engineering (only `aggregate_sequential` was an unfixed reader — 3 call sites; the rest were already fixed on main) and split Cluster A into the two real contract surfaces.
> - **PR #321** (`fix/deferred-cluster-c-mechanical`): `verify.py` group-less-regex IndexError guard; `aggregator.py:318` ESCALATE docstring reorder.
> - **PR #322** (`fix/deferred-cluster-a-aggregate-nesting`): `aggregate_sequential` reads `irreversibility_flag` + `net_concern` per-candidate from `scores[]` (2 local helpers); `test_rund2._base_conservator` rewritten to mirror real voice output, proven red→green in lockstep. `build_report.py:192` resolved by documenting the interception contract in SKILL.md Step 6 (the non-`AGGREGATE` shapes are intercepted before Step 6 — latent, not live).
> - **PR #323** (`fix/deferred-cluster-c-calibration`): Trias floor — decisive vote patterns (3-0/2-1/2-0) exempt from the WEAK flag (derived from `VOTE_PATTERN_CONFIDENCE`, no drift surface, so no new drift invariant needed); `log_feedback` PEND→OK in-place upgrade (+ regression test); `infer_pipeline` per-axis fallback (the "trivial+irreversible → spurious review" was fallback-only — the live path was already correct — and the fix never reduces safety).
> - **`fix/deferred-cluster-b-audit-counter`** (pending merge): `audit_counter` `cmd_check` idempotency (pending sentinel) + HOT→DEFAULT cadence anchored to `last_audit_run` (+ new `test_audit_counter.py`, wired into CI).
> - **DEFERRED for v1.0:** `audit_counter.py` `cmd_increment` file lock (CONTESTED 1/2). Single-user CLI; `save_state` is already atomic, so write contention is negligible. Revisit only if Consilium gains concurrent invocation.

> Source: exhaustive `consilium-bug-audit` Workflow (152 sub-agents, ~4.7M tokens, 22 min) over all 56 Python files. Each finding verified 2/2 (confirm-by-trace + adversarial refute); synthesis reclassified 3 raw findings as non-bugs. **51 raw → 37 distinct.** These passed the green gates (`run_evals` 72/0, `check_doc_drift`, `pyright`) — the suite did not catch them, and `test_rund2.py` fixtures **actively mask** several by injecting top-level fields the real voices never emit.
>
> **Systemic root cause:** producer↔consumer contract drift on `runs/<file>.json` — `build_report.py` writes one shape; `trace_graph`/`priors`/`retry_context`/`aggregator`/`efficiency`/`mark_outcome`/`usage` read a different key/level/type. Fix direction for the cluster: a single shared schema accessor that the writer and all readers go through. **Do `/consilium` before touching authoritative code (`validate_report`, `probe_change`, `aggregator`, `build_report`) + rewrite fixtures to mirror real voice output.**
>
> **Clean / reference modules (reuse these):** `utils.py` (`atomic_write_text`, `force_utf8_streams`), `audit_feedback.py` (imports `log_feedback._fingerprint` correctly), `analyze.py:proxy_score`, `confidence.py:VOTE_PATTERN_CONFIDENCE`.

### 🔴 Critical (4) — block v1.0
- [ ] **`scripts/probe_change.py:69-71` (parse_numstat)** — security-gate bypass: C-quoted git paths (non-ASCII filenames under `core.quotepath=true`) defeat 13/14 blocklist patterns → critical changes silently downgraded. → *decode C-quoted/octal paths to raw bytes before any consumer.* [CONFIRMED 2/2]
- [ ] **`scripts/validate_report.py:305-311` (`_vote_pattern_valid`)** — `sum(parts)==3` invariant rejects 4/7 legit vote patterns (`2-0`, `1-1-0`, `1-0-0`, `0-0-0`) → every Trias-with-abstention run fails the final gate; also wrongly accepts `3-0-0`. → *membership in the canonical 7-pattern set, single-sourced from `confidence.py:VOTE_PATTERN_CONFIDENCE`.* [CONFIRMED, 7 merged]
- [ ] **`scripts/validate_report.py:104` (`_validate_sequential_fields`)** — `--strict-rund2` crashes `AttributeError` on every real report (`float.get("scores")`). → *read conservator scores from `deliberation_log`, or guard the type.* [CONFIRMED, 2 merged]
- [ ] **`scripts/efficiency.py:59-61` + `scripts/mark_outcome.py:52-54` (`_fingerprint`)** — `context[:30]` + omits `run_id` → disjoint hash space vs `log_feedback.py` sidecar keys → `outcome_map` always empty, `mark_outcome --run-path` always fails. (Blocks the `calibrate.py`/outcome-join feature ideas.) → *delete both copies; import `log_feedback._fingerprint(... run_id=...)`.* [CONFIRMED, 5 merged]

### 🟠 High (19)
- [ ] **`scripts/aggregator.py:344-351, 418-421` (aggregate_sequential)** — reads `regression_risk`/`irreversibility_flag` at top level; real voice nests them in `scores[i]` → irreversibility BLOCK never fires, `net_concern` always 0.15. (`test_rund2` fixture masks it.) → *aggregate per-candidate; fix fixture.* [CONFIRMED 2/2]
- [ ] **`scripts/build_report.py:192-193`** — raises `ValueError` on 5/7 sequential result shapes (BLOCK/REWORK/ESCALATE/ADAPT_EXTENDED carry no `chosen`). → *handle non-chosen shapes, or document the interception contract in SKILL.md Step 6.* [CONFIRMED 2/2]
- [ ] **`scripts/trace_graph.py:90` + `scripts/priors.py:196`** — read a non-existent top-level `aggregate`/`aggregation` key (it lives in `deliberation_log[i]["result"]`) → "vetoed: N" never renders; `priors._run_had_veto` fast path dead. → *read from `deliberation_log`; centralize accessor.* [CONFIRMED 2/2 each]
- [ ] **`scripts/trace_graph.py:95-96`** — reads `confidence` as a dict; writer emits a scalar → confidence node never renders. → *treat as scalar.* [CONFIRMED 2/2]
- [ ] **`scripts/priors.py:207, 209` (`_run_had_veto`)** — `result` is a dict (string-guard early-returns), `chosen` checked at wrong level → `conservator_veto_rate` always 0. → *inspect `step["result"]` as dict; check `result["chosen"] is None`/`result["vetoed"]`.* [CONFIRMED 2/2]
- [ ] **`scripts/retry_context.py:82` (`_scores_for`)** — reads dead `risk_score` key → every candidate conservator=0.5, retry top-2 is risk-blind. → *read `regression_risk.net_concern` with legacy fallback (mirror `build_report._conservator_risk`).* [CONFIRMED 2/2]
- [ ] **`scripts/usage.py:44-45, 103-112`** — drops non-core voices (skeptic, Trias personalities) from per-voice + mode-bucket totals → Dialectic/Trias cost undercounted; disagrees with `efficiency.py`. → *accumulate mode-bucket over all voices.* [CONFIRMED, 2 merged]
- [ ] **`benchmark/scripts/efficiency_audit.py:92`** — reads stale `pipeline_executed` after rename to `report_detected` (no fallback, unlike `analyze.py`) → `pipeline_rate` always None. → *`pa.get("report_detected", pa.get("pipeline_executed"))`.* [CONFIRMED 2/2]
- [ ] **`benchmark/verify.py:364-382` + `benchmark/analyze.py:301-315`** — `ok=True, score=0` wrong-answer runs enter the efficiency table + inflate `verified_ok`. → *gate `efficiency_score`/`verified_ok` on `score>0`, not `ok`.* [CONFIRMED 2/2]
- [ ] **`scripts/scope_gate.py:39` (docstring) vs `:130` (`_MODE_CEILING`)** — docstring says `medium → dialectic`; code maps `medium → sequential` (drift from the lazy-routing change). → *correct the docstring.* [CONFIRMED, 2 merged]
- [ ] **`SKILL.md:615` vs `modes/trias.md` vs `scope_gate.py`** — summary says low/medium/high → Dialectic; real routing low/medium → Sequential, high → Dialectic → cost inflation (1.33× where 1× is correct). → *align the SKILL.md sentence.* [CONFIRMED 2/2]
- [ ] **`modes/trias.md:100`** — output example shows `vote_pattern: "3-0-0"` (unreachable; crashes `confidence.py`, validator wrongly accepts). → *change to `3-0`; extend drift check to `trias.md`.* [CONFIRMED, 2 merged]
- [ ] **`scripts/probe_change.py:46-51` (`_run_numstat`)** — `text=True` without `encoding="utf-8"` → cp1252 mangles UTF-8 filenames on Windows; `_commit_count` identical. → *pass `encoding="utf-8"` (use `utils.force_utf8_streams` pattern).* [CONTESTED 1/2 — Windows-specific, low FP risk]
- [ ] **`scripts/scope_gate.py:179-191` (`_gather_signals`)** — transitively inherits both `probe_change` path bugs; only `--signals-stdin` test hatch is clean. → *fix root + add a non-ASCII/C-quoted path eval scenario.* [CONFIRMED 2/2]
- [ ] **`scripts/audit_counter.py:99-101` (save_state)** — fixed `.json.tmp` + no fsync; concurrent writers corrupt it → `load_state` silently resets, wiping history. → *route through `utils.atomic_write_text`.* [CONFIRMED 2/2]
- [ ] **`scripts/audit_counter.py:116-122` (cmd_increment)** — unguarded read-modify-write loses increments under concurrency (TOCTOU). → *file lock (msvcrt/fcntl) or atomic CAS.* [CONTESTED 1/2 — shares root with save_state]
- [ ] **`scripts/log_feedback.py:215-216`** — `run_path` dedup swallows PEND→OK/BAD updates → Step-6 close-the-loop call exits 3, PEND never upgraded. → *only dedupe when stored outcome equals new; else upgrade in place.* [CONFIRMED 2/2]

### 🟡 Medium (9)
- [ ] **`SKILL.md:116` vs `scope_gate.py:81`** — docs `**/secrets*`, impl `**/*secrets*` → reader won't realize `prod-secrets.yaml` is blocked. → *correct SKILL.md.* [CONFIRMED 2/2]
- [ ] **`SKILL.md:237` vs `usage.py:14` vs `validate_report.py:167-169`** — `dispatch_count` (documented) vs `passes` (validated, never written) drift → validator check dead. → *pick one canonical name; update all three.* [CONFIRMED, 2 merged]
- [ ] **`scripts/infer_pipeline.py:95-106`** — off-prompt `'none'` token is truthy → bypasses falsy guard → full step set + `pipeline` routing instead of `single_shot`. → *treat `'none'`/off-vocab as missing.* [CONFIRMED 2/2]
- [ ] **`scripts/infer_pipeline.py:58-63, 78-82`** — reversibility floor pushes `trivial+irreversible` into the `critical/irreversible` bucket → spurious `review` step + `pipeline` misroute. → *separate magnitude axis from reversibility floor in bucketing.* [CONFIRMED 2/2]
- [ ] **`benchmark/verify.py:344-350, 284-285`** — uncaught `IndexError` (pattern matches but no capture group) crashes verification, writes no `report.json`. → *validate ≥1 group / catch `IndexError`.* [CONFIRMED 2/2]
- [ ] **`benchmark/analyze.py:332-341` (verify_html)** — green `verify-ok` badge for wrong-answer (`score=0, ok=True`) runs. → *color from `score>0`, not `state`.* [CONFIRMED 2/2 — same `ok`-vs-`correct` root as the High finding]
- [ ] **`scripts/render_feedback_html.py:52`** — `PEND_HEADLESS` outcome has no CSS rule → rows render unstyled. → *add `.PEND_HEADLESS` rule + update Entry-doc enum.* [CONFIRMED, 2 merged]
- [ ] **`scripts/log_feedback.py:338-342`** — exit-3 (duplicate skip) prints the same stdout summary as exit-0 → caller can't distinguish. → *suppress stdout on exit 3, or prefix `skipped:`.* [CONFIRMED, 2 merged]
- [ ] **`scripts/audit_counter.py:125-142` (cmd_check)** — non-idempotent: repeated `--check` before `--record-divergence` double-fires the audit trigger. → *pending sentinel, or make trigger idempotent on the same count.* [CONFIRMED 2/2]

### ⚪ Low (5)
- [ ] **`scripts/aggregator.py:156` (aggregate_conservative_override)** — tie-break uses insertion order; spec says "safer wins on tie". → *secondary sort key `(-score, conservator_risk, idx)` + a true-tie eval.* [CONFIRMED 2/2]
- [ ] **`scripts/aggregator.py:318-329` (docstring)** — ESCALATE documented at priority 6, fires at effective 3. → *reorder docstring to match code.* [CONFIRMED 2/2]
- [ ] **`modes/trias.md:5` (`confidence_floor: 0.80`)** — exceeds OK-auto confidences `2-1` (0.75) / `2-0` (0.70) → WEAK logged for valid Trias runs. → *lower Trias floor ≤0.70, or exempt valid non-null patterns from the WEAK check.* [CONFIRMED 2/2]
- [ ] **`scripts/validate_report.py:287-290` (`_MULTI_VOICE_MODES`)** — dead legacy alias entries (resolved to canonical before the check → unreachable). → *drop legacy names from the set.* [CONFIRMED 2/2]
- [ ] **`scripts/audit_counter.py:104-113, 125-142`** — HOT→DEFAULT transition can shorten the first DEFAULT window to 5 runs (no base reset). → *track an audit base offset, reset on frequency flip.* [CONFIRMED 2/2]

### Reclassified (verified NON-bugs — do not fix)
- `scripts/infer_pipeline.py:66-75` (`_extract_conservator_fields`) — correct: reads the properly-nested `scores[i]` from the stored report. NOT a bug.
- `benchmark/analyze.py:469` (`pipeline_executed` internal key) — internally consistent; naming-hygiene note only.
- `validate_report.py:302` regex permissiveness — subsumed by the Critical `_vote_pattern_valid` fix.

---

## 🚀 Release roadmap — v1.0 (public, source-available)

> Goal: make the repo public + presentable as the flagship agentic/LLMOps CV artifact, then cut a tagged v1.0. Grounded in a repo audit on 2026-05-29. License is already **BSL** (Licensor: Schipor Alexandru → Apache-2.0 on 2030-05-16) — source-available, *not* OSS; state this plainly in the README. All green gates pass locally today: `run_evals` 68/0, `check_doc_drift` OK, `driver.py smoke` green.

### Phase 0 — Pre-release hygiene (blockers)

- [x] **Privacy sweep before going public.** `Enterprise_GenAI_Roadmap_Alex.pdf` is in the repo root, untracked AND not gitignored → committable by accident. Remove it or add to `.gitignore`. Re-confirm `.consilium/` (FEEDBACK.html real-usage data, runs/) stays gitignored and Benchmark answer keys remain an external sibling (CV-piece honesty: no leaked oracle values).
- [x] **Clean the working tree.** Untracked scratch in root (`bundle_high_priority.json`, `bundle_min.json`, `bundle_smoke_tests.json`, `bundle_veto_op.json`, `test_bundle.json`) + `.consilium/*.py` / `tmp_*.json`. Per file: keep a canonical sample where it's referenced (the `run-consilium` driver + SKILL.md use `bundle_smoke_tests.json` — consider moving it to `evals/fixtures/`), gitignore the rest, delete pure scratch.
- [x] **README for an outside reader** (currently 114 lines). Must answer: what Consilium is, install (drop into `.claude/skills/` → `/consilium`), a 30-second usage example, a link to the architecture explainer, and the BSL note. Clear/accurate/honest over impressive.
- [x] **CI green-gate** — no `.github/workflows/` exists yet. Add a workflow running `run_evals.py`, `check_doc_drift.py`, `test_rund2.py`, `test_feedback_html.py`, and `docs/architecture/build.py --check` on every PR so the public repo can't drift red.

### Phase 1 — Cut the release

- [x] **Distribution story** — DONE: README §"Install" (Linux/macOS + Windows) + the `> **Distribution:** manual install is the supported path` note (README:60). Manual-install chosen over plugin/marketplace. Senate `2026-05-31_105804-consilium-v1-scope-decision` confirmed it is already shipped.
- [x] **README §"Why not RAG / LangGraph / LangChain" (architectural decisions).** Short, honest section documenting the *deliberate* rejection on scope/discipline grounds — stdlib-only, zero-dep reproducibility, no measured need at ~220 runs, native Agent-tool orchestration already covers the graph — framed as a strength, not an omission. Cite the Senate audit (Senate repo: `runs/senate/2026-05-29_120838-rag-langgraph-in-consilium-core.json` — verdict MODIFY; STOP 7 / MODIFY 2 / GO 0; both routed to §6) and its three precedents (2026-05-16, 2026-05-19 ×2). Recommended by the 2026-05-25 CV-strategy audit: "frame the LangGraph rejection as a scope/discipline decision, not 'LangGraph found inferior'." RAG/LangGraph/LangChain belong in §6.
- [x] **CHANGELOG.md** — none exists. Seed it for v1.0 (modes, pipeline, silent audit, architecture explainer, run-consilium skill).
- [ ] **Tag v1.0.0** — no git tags exist. Optionally add a version marker the skill can surface.
- [ ] **Land public history clean** — ties into *User directions › Public-release prep* below; the repo has a large branch backlog, so plan the single-clean-commit / squash strategy for the public mirror.
- [x] **Wire `trace_graph.py` into the README** — DONE: README §"Pipeline trace" (README:89) has the `trace_graph.py --fence` example + a static ```mermaid block (GitHub renders natively). The optional sibling follow-up (in-explainer **live** rendering via mermaid.js CDN) is **dropped** — Senate `2026-05-31_105804` Round 2, 6/6 senators against the runtime CDN: it duplicates the already-shipped static fence and adds a non-stdlib runtime surface (Tacitus: the 2026-05-19 sidecar precedent). The static fence IS the observability graph; if ever revived it must clear the sidecar bar (isolation contract + value kill-criterion + fully-offline build).

### Phase 2 — Post-v1 growth (already tracked below; not release-blockers)

- [ ] Efficiency / model-count audit kill-criterion (see HIGH PRIORITY) — gate any routing change on n≥5 oracle-validated wins.
- [ ] *User directions (open)*: multi-modal input, versioning & config system, API backend, explainability UI. (Human-readable audit trail RESOLVED — see User directions below.)
- [ ] §6 Showcase project (see DEFERRED) — breadth CV artifact, separate repo.
- [x] **Pipeline observability graph — WITHOUT LangGraph.** RESOLVED (Senate `2026-05-31_105804` Round 2). Part (a) — a stdlib script that reads `.consilium/runs/<file>.json` (`deliberation_log` + `telemetry`) and emits Mermaid flowchart text, zero deps — **shipped** as `scripts/trace_graph.py`, surfaced via README §"Pipeline trace" (static ```mermaid fence, GitHub renders natively). Part (b) — live in-explainer render via mermaid.js **CDN** — **dropped**: 6/6 senators against the runtime CDN (it duplicates the already-shipped static fence and adds a non-stdlib runtime surface). The static fence IS the canonical diagram; reviving a live render must clear the sidecar bar (isolation contract + value kill-criterion + fully-offline build — Tacitus, 2026-05-19 sidecar precedent).

---

## HIGH PRIORITY

### Silent-audit-every-20-runs — DONE (2026-05-28)

> Discovered 2026-05-28 via Senate audit (`runs/senate/2026-05-28_094832-doc-drift-ssot-mode-docs.json`, Socrate's load-bearing premise). Implemented on `feat/silent-parallel-audit`.

- [x] **Implementation:** `scripts/audit_counter.py` — counter + adaptive frequency (1/20 default, 1/5 HOT after ≥2 divergences in window of 5). State in `.consilium/audit_state.json` (gitignored). Lifecycle tested: 20-run trigger fires `should_audit: true`; headless contexts increment counter but skip dispatch; 3 divergences → frequency bumps to 1/5.
- [x] **Workflow wiring:** SKILL.md §"Silent parallel audit" describes the post-Step-6 orchestrator workflow (`--increment` → `--check` → optional 2-turn parallel dispatch → `--record-divergence`).
- [x] **Doc-drift guard:** new invariant `silent_audit_implemented` in `scripts/check_doc_drift.py` requires SKILL.md to reference `scripts/audit_counter.py` and forbids the old "no implementation in scripts/" / "pending implementation check" caveats.
- [x] **Calibration window:** Deming's 3-6 month longitudinal audit (TODO below) reads `audit_state.json.audits[]` for the before/after baseline.

---

### Track 2 — CI grep enforcement of mode invariants — DONE (2026-05-28)

> Senate audit `2026-05-28_094832-doc-drift-ssot-mode-docs.json` verdict MODIFY→GO after R2 (Tacitus position change MODIFY_R1_to_GO). Track 1 (commit `2114f21` on `fix/docs-arch-drift-sync`) shipped the 4 drift fixes; Track 2 implemented on `feat/doc-drift-ci-enforcement-v2`.

- [x] **b2 CI grep job**: `scripts/check_doc_drift.py` — 4 invariants (Trias parallel dispatch, Trias 2-1/2-0 confidence parity with `confidence.py`, sequential scale_down behavior, parallel-auto 2-turn structure) + legacy MODE alias removal-milestone enforcement. Negative-tested: induced drift → exit 1.
- [x] **Cite May-25 run id**: SKILL.md §"Parallel voices mode" now opens with a lineage blockquote citing `.consilium/runs/2026-05-25_160009-modes-dir-frontmatter-refactor.json` + the Senate audit bundle.
- [x] **Removal milestone**: `validate_report.py` `_LEGACY_MODE_ALIASES` annotated with `# remove after 2026-08-17` (parallel_skeptic, dialectic_skeptic) and `# remove after 2026-08-21` (trias_split). Script enforces presence of these dates.

---

### Dialectic Skeptic-on-scale_down — empirical validation

> Spec fix landed 2026-05-28 (`fix/dialectic-skeptic-on-scale-down`): SKILL.md Step 2 + modes/dialectic.md updated to require Skeptic stage even on Conservator scale_down short-circuits. Empirical validation deferred.

- [x] Re-run consilium_dialectic on `reasoning/01_transport_choice` after merge. **Outcome 2026-05-28:** answer flipped to the correct option, llm_judge 30/100→100/100. BUT `num_turns: 2` means Skeptic was NOT dispatched as a sub-agent. Most likely mechanism: **spec-priming contamination** — modes/dialectic.md and SKILL.md at the time contained the correct answer verbatim, which leaked it into the orchestrator's reading context (the leaking spec text was later removed in PR #261). The improvement may not generalize. Status: **applied-but-unvalidated**.
- [x] **Validation regression — spec-priming leak**: rewrite the empirical-motivation prose in modes/dialectic.md + SKILL.md so the validation task's correct letter is NOT embedded in spec text the orchestrator reads. Done 2026-05-28 (PR #261).
- [x] **Clean re-validation post-leak-removal** (2026-05-28): all 5 modes 100/100 on task 01, including `sonnet_bare`, with `pipeline_executed=False` and `num_turns=2` — **task 01 is not a discriminator**. Base model at `--effort high` answers it correctly on its own. The flip was non-determinism, not spec-priming or Skeptic. Task 01 cannot validate the Skeptic mechanism.
- [x] Construct a NEW eval task where the base model reliably fails without Skeptic guidance. **Outcome 2026-05-28:** Added `reasoning/11_marathon_prep` (arithmetic constraint over two events). All 5 modes 100/100 including sonnet_bare — **also not a discriminator**. Sonnet 4.6 at --effort high handles 2-step arithmetic correctly. The Skeptic-on-scale_down case remains mechanically validated but empirically unconfirmed.
- [x] Re-run consilium_dialectic on full n=10 reasoning corpus. **Outcome 2026-05-28:** 10/10 correct (up from 9/10). Skeptic dispatched on 5/10 tasks (04, 05, 08, 09, 10 — all full-pipeline, not scale_down). Net: fix works mechanically, empirical ROI unclear.
- [x] **`--skeptic-can-override` decision (2026-05-28): KEEP ADVISORY.** Zero oracle-validated cases where scale_down → wrong AND Skeptic → correct exist. Tasks 01 and 11 both confirm base model gets scale_down-class problems right. Skeptic IS dispatched on harder tasks (04, 05, 08) but those are full-pipeline, not scale_down — advisory vs default makes no difference there (no scale_down to override). Making it default would add Skeptic cost to every Dialectic run with no proven benefit on the scale_down path. **Reopen if**: ≥1 oracle-validated (scale_down wrong → Skeptic corrects) case found in future runs.

---

### Efficiency / model-count audit

> Pre-registered spec (Consilium 2026-05-26 · `.consilium/runs/2026-05-26_1200_p1-efficiency-p2-explore-commit.json` · conf=0.74). Dimon constraint: no routing sentence in SKILL.md until n≥20.

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥5 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=5 (3 existing + architecture `03_cursor_pagination` + debugging `04_binary_search_bug`). Run all modes and oracle-validate.

---

## DEFERRED

- [ ] **§6 Showcase project — "AI Incident Investigation & Knowledge Copilot"** (separate repo) — RAG over PDFs + DLT/automotive logs, Jira/Confluence ingestion, hybrid search + reranking, FastAPI backend, eval dashboards. Highest-leverage CV move for Enterprise-GenAI/RAG roles (per Senate audit). Consilium stays the deep agentic/LLMOps artifact; §6 is the breadth artifact.

- [x] **pipeline_executed integration gaps** — **Done 2026-05-28**: renamed benchmark field to `report_detected` in `pipeline_audit.json` (run_task.py + analyze.py with legacy fallback). Decision: document divergence by renaming, not unifying — the two fields measure genuinely different things (deliberation quality vs. subprocess observability). `audit_counter.py --increment` behavior unchanged (counts scale_down too, per original spec — a change here would require empirical justification).

---

## 🎯 User directions (open)

- [ ] **Public-release prep** — make the repo public; plan how to land it in a clean single commit.
- [ ] **Multi-modal input** — Consilium să accepte și documente/specificații, nu doar text liber. Relevant pentru enterprise workflows reale.
- [x] **Audit trail human-readable** — RESOLVED (Senate `2026-05-31_105804` Round 2, **unanimous 6/6: fold into existing `.consilium/FEEDBACK.html`**, do not build a separate renderer). FEEDBACK.html (append-only, `log_feedback.py`, atomic writes) already is the human-readable real-usage journal. Any future manager-facing view extends that single source of truth — no new audit-trail component.
- [ ] **Versioning & config system** — versiuni de prompts, versiuni de agents, config per workflow.
- [ ] **API real backend** — FastAPI / Node backend; endpoints: `/chat`, `/agents`, `/workflow`, `/memory`. (Verifică ce există deja înainte.)
- [ ] **Explainability UI** — "Why this answer?", "Which agents were used?", "What data was retrieved?".

---

## Rollback hooks

- **R.1** All new voices (philosophical variants) are **parallel**, not replacing — zero risk if not called.
- **R.2** If `aggregator.py` breaks old runs → revert that commit, keep prompts.

---

## Closed items (2026-05-26)

- ✅ Voice score stability (#1-B, #1-C, #1-D) — experiment done, recommendations integrated
- ✅ Prior-deliberation passthrough — implemented (`feat/prior-deliberation-passthrough`)
- ✅ Substance-validation gap — `_warn_substance()` added to `validate_report.py` (stderr, non-blocking)
- ✅ scenarios.json note — `_meta` sentinel added; `run_evals.py` skips non-tool entries
- ✅ Veto budget for `meta_recommendation` — 5/month accepted as documented in `SKILL.md:577`; no code enforcement needed
- ✅ Outcome tracking — domain-specific (MT4 for trading); `principle_extraction.py` not yet built; deferred until a concrete domain integration is requested
