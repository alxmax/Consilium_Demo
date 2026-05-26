# TODO — Consilium (cleaned 2026-05-26)

---

## HIGH PRIORITY

### Voice score stability (open follow-ups · experiment 2026-05-17)

> Source: `runs/senate/2026-05-17_161608-top5-diagnostic-audit.json` — #1 CRITICAL: Conservator is anchored (categorical formula), Generator + Control emit unanchored floats. `confidence.py` agreement measures role-prompt divergence, not inter-run stability. Veto threshold (0.8) region not yet probed.

- [x] **#1-B** Add categorical-stability check: `stability_check.py --compare` now reports `magnitude`/`reversibility` disagreement from both flat and nested log schemas; emits explicit MISSING when fields absent.
- [x] **#1-C** Stability probed in 2026-05-26 experiment (Pair A + Pair B). Generator HIGH VARIANCE confirmed (pstdev=0.25 on ambiguous input). F4 gap (veto-boundary variance region) remains open — neither pair produced conservator in [0.7, 0.9]; see `experiments/voice-score-stability-2026-05-26.md`.
- [x] **#1-D** Wittgenstein's asymmetry confirmed: Control pstdev=0.000, Generator pstdev=0.250 on same ambiguous input. Two recommendations integrated: skeptic trigger band extended to [0.0, 0.7]; `low_separation` flag added to aggregator.py.

### Efficiency / model-count audit

> Pre-registered spec (Consilium 2026-05-26 · `.consilium/runs/2026-05-26_1200_p1-efficiency-p2-explore-commit.json` · conf=0.74). Dimon constraint: no routing sentence in SKILL.md until n≥20.

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥5 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=5 (3 existing + architecture `03_cursor_pagination` + debugging `04_binary_search_bug`). Run all modes and oracle-validate.

---

## MEDIUM PRIORITY

### Prior-deliberation passthrough — DONE (2026-05-26, branch `feat/prior-deliberation-passthrough`)

> Source: observed friction 2026-05-26 — stale-refs cleanup went through full Consilium pipeline
> even though the change directly implemented an already-finalized Senate MODIFY verdict.

- [x] `scripts/priors.py`: `--label TEXT` arg + `_find_prior_match()` (8-char min-length guard, 30-day window, outcomes OK/GO)
- [x] `scripts/validate_report.py`: bypass `_validate_deliberation_log` for `chosen_approach == "prior-deliberation"`
- [x] `SKILL.md` Step 0: passthrough gate documented with confirmation prompt + headless/FORCE_FULL semantics
- [x] `evals/scenarios.json`: 3 new scenarios (label match, min-length guard, validate_report acceptance) — 68 total

**Falsification criterion still active:** if passthrough fires on a case that later gets outcome=BAD, tighten the `--label` value or require more specific task descriptions.

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
