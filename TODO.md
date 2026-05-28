# TODO — Consilium (cleaned 2026-05-26)

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

- [ ] Re-run consilium_dialectic on `reasoning/01_transport_choice` after merge. Expected: pipeline_executed still false (Gen+Ctrl skipped is correct cost-wise), but Skeptic now dispatches on the trivial-direct chosen. Outcome question: does Skeptic catch the "car must arrive" constraint and flip A→B? If yes, the fix delivers value; if no, Skeptic prompt may need strengthening (separate issue).
- [ ] Re-run consilium_dialectic on full n=10 reasoning corpus. Old score 9/10 (90%). Expected new score ≥9/10; if Skeptic ever flips a previously-correct answer to wrong, regression.
- [ ] Consider: should `--skeptic-can-override` become the default for Dialectic specifically? Currently advisory; for the cost-aware path (scale_down + Skeptic) it makes sense to honor Skeptic's challenge since otherwise scale_down's wrong answer ships unchallenged. Spec decision deferred to after benchmark data.

---

### Efficiency / model-count audit

> Pre-registered spec (Consilium 2026-05-26 · `.consilium/runs/2026-05-26_1200_p1-efficiency-p2-explore-commit.json` · conf=0.74). Dimon constraint: no routing sentence in SKILL.md until n≥20.

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥5 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=5 (3 existing + architecture `03_cursor_pagination` + debugging `04_binary_search_bug`). Run all modes and oracle-validate.

---

## DEFERRED

- [ ] **§6 Showcase project — "AI Incident Investigation & Knowledge Copilot"** (separate repo) — RAG over PDFs + DLT/automotive logs, Jira/Confluence ingestion, hybrid search + reranking, FastAPI backend, eval dashboards. Highest-leverage CV move for Enterprise-GenAI/RAG roles (per Senate audit). Consilium stays the deep agentic/LLMOps artifact; §6 is the breadth artifact.

- [ ] **pipeline_executed integration gaps** (left intentionally during 2026-05-28 sequential-observability work)
  - Two artifacts share the name `pipeline_executed` with ~80% overlapping semantics:
    - `.consilium/runs/<file>.json.pipeline_executed` — canonical Consilium field, "did the 3-voice deliberation actually run?" (added in `feat/sequential-observability-tightening`)
    - `benchmark/workspace/.../pipeline_audit.json.pipeline_executed` — benchmark-harness artifact, "did the model invoke `.consilium/runs/` path in its response?" (pre-existing, written by `benchmark/run_task.py`)
  - Decide: unify the two (single field with shared semantics, benchmark reads canonical) OR explicitly document the divergence (rename one to disambiguate).
  - Related: `scripts/audit_counter.py --increment` currently fires on every Sequential run including scale_down. Consider gating on canonical `pipeline_executed: true` so the silent-audit baseline measures only actual deliberations. Caveat: the original spec said "count scale_down too" because sequential-scale_down vs parallel-full IS divergence worth detecting; a change here is a spec change.
  - Effort: ~2-4h (decide direction + small refactor + update SKILL.md / TODO).

---

## 🎯 User directions (open)

- [ ] **Public-release prep** — make the repo public; plan how to land it in a clean single commit.

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
