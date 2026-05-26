# TODO — Consilium (cleaned 2026-05-26)

---

## HIGH PRIORITY

### Voice score stability (open follow-ups · experiment 2026-05-17)

> Source: `runs/senate/2026-05-17_161608-top5-diagnostic-audit.json` — #1 CRITICAL: Conservator is anchored (categorical formula), Generator + Control emit unanchored floats. `confidence.py` agreement measures role-prompt divergence, not inter-run stability. Veto threshold (0.8) region not yet probed.

- [x] **#1-B** Add categorical-stability check: `stability_check.py --compare` now reports `magnitude`/`reversibility` disagreement from both flat and nested log schemas; emits explicit MISSING when fields absent.
- [ ] **#1-C** Re-run voice-score stability with 2-3 cases that produce `net_concern ∈ [0.7, 0.9]` to probe the veto-threshold variance region (F4 gap — max observed so far was 0.42). **Tooling ready, experiments pending.**
- [ ] **#1-D** Probe Generator + Control stability (untested in the 2026-05-17 experiment — Wittgenstein's asymmetry claim is half-supported but unconfirmed on the unanchored voices). **Tooling ready, experiments pending.**

### Efficiency / model-count audit

> Pre-registered spec (Consilium 2026-05-26 · `.consilium/runs/2026-05-26_1200_p1-efficiency-p2-explore-commit.json` · conf=0.74). Dimon constraint: no routing sentence in SKILL.md until n≥20.

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥20 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=6 (pipeline-bench R1+R2) is insufficient — algorithmic tasks only. Revisit when benchmark reaches n≥20 across diverse task types (architectural deliberations included).

---

## LOW PRIORITY

- [ ] **Veto budget for `meta_recommendation`** — is 5/month acceptable? The number is arbitrary (Aurelius+Napoleon proposed it). No urgency.
- [ ] **Outcome tracking — manual or automatic?** For trading, automatic from MT4 is feasible. For other domains it requires manual completion. If not addressed, `principle_extraction` never activates.
- [ ] **Substance-validation gap** (accepted known gap) — `validate_report.py` checks report shape only; no enforced gate that voices did substantive work. Minimal fix: ~20-line heuristic in `validate_report.py`. Revisit only if empty-but-schema-valid deliberations appear in practice.
- [ ] **scenarios.json note** — add documentation note that synthetic fixtures validate code-path coverage only, not semantic correctness (Deming's remaining request from eval-parity MODIFY 2026-05-25).

---

## Rollback hooks

- **R.1** All new voices (philosophical variants) are **parallel**, not replacing — zero risk if not called.
- **R.2** If `aggregator.py` breaks old runs → revert that commit, keep prompts.

---

## 🎯 User directions (open)

- [ ] **Public-release prep** — make the repo public; plan how to land it in a clean single commit.

---

## DEFERRED

- [ ] **§6 Showcase project — "AI Incident Investigation & Knowledge Copilot"** (separate repo) — RAG over PDFs + DLT/automotive logs, Jira/Confluence ingestion, hybrid search + reranking, FastAPI backend, eval dashboards. Highest-leverage CV move for Enterprise-GenAI/RAG roles (per Senate audit). Consilium stays the deep agentic/LLMOps artifact; §6 is the breadth artifact.
