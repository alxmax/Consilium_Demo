# TODO — Consilium (cleaned 2026-05-26)

---

## HIGH PRIORITY

### Silent-audit-every-20-runs: implement or remove

> Discovered 2026-05-28 via Senate audit (`runs/senate/2026-05-28_094832-doc-drift-ssot-mode-docs.json`, Socrate's load-bearing premise). SKILL.md §"Parallel voices mode" and `modes/sequential.md` claim "every 20 runs parallel mode runs silently alongside sequential." Grep across `scripts/` for `silent.*audit|every.*20.*run|audit.*freq` returns **zero matches**. The mechanism does not exist.

- [ ] Decide between:
  - **Implement:** counter in `.consilium/`, increment per sequential run, every 20th triggers silent parallel cross-check stored alongside the normal run. Audit divergence; if N divergences in last M runs → frequency → 1/5.
  - **Remove:** delete the claim from SKILL.md (~L520) + `modes/sequential.md` (Auto-parallel section) + architecture diagram (modes.jsx parallel_auto step 6, currently marked "pending implementation check").
- [ ] **Acceptance:** either grep returns a real implementation OR no doc surface mentions the 20-run audit.
- [ ] **Constraint:** architecture explainer is CV-visible — solid > impressive-but-shaky. Don't leave the "pending check" note in place beyond one session.

---

### Track 2 — CI grep enforcement of mode invariants — DONE (2026-05-28)

> Senate audit `2026-05-28_094832-doc-drift-ssot-mode-docs.json` verdict MODIFY→GO after R2 (Tacitus position change MODIFY_R1_to_GO). Track 1 (commit `2114f21` on `fix/docs-arch-drift-sync`) shipped the 4 drift fixes; Track 2 implemented on `feat/doc-drift-ci-enforcement-v2`.

- [x] **b2 CI grep job**: `scripts/check_doc_drift.py` — 4 invariants (Trias parallel dispatch, Trias 2-1/2-0 confidence parity with `confidence.py`, sequential scale_down behavior, parallel-auto 2-turn structure) + legacy MODE alias removal-milestone enforcement. Negative-tested: induced drift → exit 1.
- [x] **Cite May-25 run id**: SKILL.md §"Parallel voices mode" now opens with a lineage blockquote citing `.consilium/runs/2026-05-25_160009-modes-dir-frontmatter-refactor.json` + the Senate audit bundle.
- [x] **Removal milestone**: `validate_report.py` `_LEGACY_MODE_ALIASES` annotated with `# remove after 2026-08-17` (parallel_skeptic, dialectic_skeptic) and `# remove after 2026-08-21` (trias_split). Script enforces presence of these dates.

---

### Efficiency / model-count audit

> Pre-registered spec (Consilium 2026-05-26 · `.consilium/runs/2026-05-26_1200_p1-efficiency-p2-explore-commit.json` · conf=0.74). Dimon constraint: no routing sentence in SKILL.md until n≥20.

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥5 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=5 (3 existing + architecture `03_cursor_pagination` + debugging `04_binary_search_bug`). Run all modes and oracle-validate.

---

## DEFERRED

- [ ] **§6 Showcase project — "AI Incident Investigation & Knowledge Copilot"** (separate repo) — RAG over PDFs + DLT/automotive logs, Jira/Confluence ingestion, hybrid search + reranking, FastAPI backend, eval dashboards. Highest-leverage CV move for Enterprise-GenAI/RAG roles (per Senate audit). Consilium stays the deep agentic/LLMOps artifact; §6 is the breadth artifact.

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
