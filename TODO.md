# TODO — Consilium (cleaned 2026-05-26)

---

## HIGH PRIORITY

### Efficiency / model-count audit

> Pre-registered spec (Consilium 2026-05-26 · `.consilium/runs/2026-05-26_1200_p1-efficiency-p2-explore-commit.json` · conf=0.74). Dimon constraint: no routing sentence in SKILL.md until n≥20.

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥20 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=6 (pipeline-bench R1+R2) is insufficient — algorithmic tasks only. Revisit when benchmark reaches n≥20 across diverse task types (architectural deliberations included).

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
