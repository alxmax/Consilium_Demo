# TODO — Consilium (cleaned 2026-05-26)

---

## 🚀 Release roadmap — v1.0 (public, source-available)

> Goal: make the repo public + presentable as the flagship agentic/LLMOps CV artifact, then cut a tagged v1.0. Grounded in a repo audit on 2026-05-29. License is already **BSL** (Licensor: Schipor Alexandru → Apache-2.0 on 2030-05-16) — source-available, *not* OSS; state this plainly in the README. All green gates pass locally today: `run_evals` 68/0, `check_doc_drift` OK, `driver.py smoke` green.

### Phase 0 — Pre-release hygiene (blockers)

- [ ] **Privacy sweep before going public.** `Enterprise_GenAI_Roadmap_Alex.pdf` is in the repo root, untracked AND not gitignored → committable by accident. Remove it or add to `.gitignore`. Re-confirm `.consilium/` (FEEDBACK.html real-usage data, runs/) stays gitignored and Benchmark answer keys remain an external sibling (CV-piece honesty: no leaked oracle values).
- [ ] **Clean the working tree.** Untracked scratch in root (`bundle_high_priority.json`, `bundle_min.json`, `bundle_smoke_tests.json`, `bundle_veto_op.json`, `test_bundle.json`) + `.consilium/*.py` / `tmp_*.json`. Per file: keep a canonical sample where it's referenced (the `run-consilium` driver + SKILL.md use `bundle_smoke_tests.json` — consider moving it to `evals/fixtures/`), gitignore the rest, delete pure scratch.
- [ ] **README for an outside reader** (currently 114 lines). Must answer: what Consilium is, install (drop into `.claude/skills/` → `/consilium`), a 30-second usage example, a link to the architecture explainer, and the BSL note. Clear/accurate/honest over impressive.
- [ ] **CI green-gate** — no `.github/workflows/` exists yet. Add a workflow running `run_evals.py`, `check_doc_drift.py`, `test_rund2.py`, `test_feedback_html.py`, and `docs/architecture/build.py --check` on every PR so the public repo can't drift red.

### Phase 1 — Cut the release

- [ ] **Distribution story** — decide how others consume it: (a) manual-install docs (copy to `~/.claude/skills/consilium/`), or (b) package as a Claude Code plugin (`.claude-plugin/plugin.json` + a marketplace entry). Pick one, document it in the README. The `run-consilium` skill is the "how to run/verify" companion.
- [ ] **CHANGELOG.md** — none exists. Seed it for v1.0 (modes, pipeline, silent audit, architecture explainer, run-consilium skill).
- [ ] **Tag v1.0.0** — no git tags exist. Optionally add a version marker the skill can surface.
- [ ] **Land public history clean** — ties into *User directions › Public-release prep* below; the repo has a large branch backlog, so plan the single-clean-commit / squash strategy for the public mirror.
- [ ] **Wire `trace_graph.py` into the README** (deferred — script already shipped on `feat/trace-graph-mermaid`). Add a short "Pipeline trace" section: one `python scripts/trace_graph.py --input .consilium/runs/<file>.json --fence` example + the rendered Mermaid block (GitHub renders it natively). Shows the per-run executed pipeline as a portfolio detail. Optional sibling follow-up: in-explainer rendering (own `/consilium`, touches `docs/architecture/`).

### Phase 2 — Post-v1 growth (already tracked below; not release-blockers)

- [ ] Efficiency / model-count audit kill-criterion (see HIGH PRIORITY) — gate any routing change on n≥5 oracle-validated wins.
- [ ] *User directions (open)*: multi-modal input, human-readable audit trail, versioning & config system, API backend, explainability UI.
- [ ] §6 Showcase project (see DEFERRED) — breadth CV artifact, separate repo.

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

- [x] Re-run consilium_dialectic on `reasoning/01_transport_choice` after merge. **Outcome 2026-05-28:** answer flipped A→B (correct), llm_judge 30/100→100/100. BUT `num_turns: 2` means Skeptic was NOT dispatched as a sub-agent. Most likely mechanism: **spec-priming contamination** — modes/dialectic.md and SKILL.md now contain the text *"correct is B (drive), motivating empirical case"* which leaked the answer into the orchestrator's reading context. The improvement may not generalize. Status: **applied-but-unvalidated**.
- [x] **Validation regression — spec-priming leak**: rewrite the empirical-motivation prose in modes/dialectic.md + SKILL.md so the validation task's correct letter is NOT embedded in spec text the orchestrator reads. Done 2026-05-28 (PR #261).
- [x] **Clean re-validation post-leak-removal** (2026-05-28): all 5 modes 100/100 on task 01, including `sonnet_bare`, with `pipeline_executed=False` and `num_turns=2` — **task 01 is not a discriminator**. Base model at `--effort high` answers B correctly on its own. The A→B flip was non-determinism, not spec-priming or Skeptic. Task 01 cannot validate the Skeptic mechanism.
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
- [ ] **Audit trail human-readable** — nu JSON pentru developeri, ci un raport citibil de un manager. Demonstrează gândire la utilizatorul final.
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
