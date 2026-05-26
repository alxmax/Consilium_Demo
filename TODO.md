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

- [ ] **Kill-criterion:** ≥2 wins (correctness gain over current mode) in n≥20 oracle-validated tasks for a reduced-agent mode before any SKILL.md routing change.
- [ ] **Target end-state:** diff-checkable change to the SKILL.md Routing Boundary table.
- [ ] **Precondition:** Trias-vs-Sequential paired corpus n≥5, same spec both arms, oracle-validated. Current n=6 (pipeline-bench R1+R2) is insufficient — algorithmic tasks only. Revisit when benchmark reaches n≥20 across diverse task types (architectural deliberations included).

---

## MEDIUM PRIORITY

### Prior-deliberation passthrough (skip re-deliberation when Senate/Consilium ran recently)

> Source: observed friction 2026-05-26 — stale-refs cleanup went through full Consilium pipeline
> even though the change directly implemented an already-finalized Senate MODIFY verdict.
> Scale-down short-circuit fired (trivial-direct), but the deliberation scaffolding still ran.

**Proposal:** At Step 0 Bootstrap, after `priors.py`, check for a recent authoritative run
(Senate bundle in `runs/senate/` OR `.consilium/runs/` entry) whose label matches the current task
within a configurable window (default 30 days). If found, skip to Step 7 directly — no Conservator,
no Generator, no Control — with `chosen_approach: "prior-deliberation"` and `confidence: 0.90`.

**Design constraints:**
- Match must be label-based (substring, normalized) — same as `senate_priors.py` logic.
- The authoritative run must have verdict `GO` or, for Senate, all senator-level MODIFY items resolved.
- Gate: user-facing confirmation prompt *"Prior deliberation found: `<label>` (`<date>`, verdict=`<v>`). Proceed directly to implementation?"* — bypass only with explicit YES or `CONSILIUM_FORCE_FULL=1`.
- `validate_report.py` must accept `chosen_approach: "prior-deliberation"` as a valid non-null value.
- Telemetry: `mode: "prior_deliberation_passthrough"`, `dispatch_count: 0`.

**Pre-registered falsification criterion:** if passthrough is used on a case that later gets
outcome=BAD, the match algorithm is too permissive — tighten label-match or add a required
`resolved_items` field on Senate bundles.

**Files to touch:** `scripts/priors.py` (return `prior_deliberation_match` field),
`SKILL.md` Step 0 (add check), `scripts/validate_report.py` (allow new mode value).

**Gate before merge:** Senate or Consilium deliberation on the design above (n=1 run minimum).

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
- [ ] **§6 Showcase project — "AI Incident Investigation & Knowledge Copilot"** (separate repo) — RAG over PDFs + DLT/automotive logs, Jira/Confluence ingestion, hybrid search + reranking, FastAPI backend, eval dashboards. Highest-leverage CV move for Enterprise-GenAI/RAG roles (per Senate audit). Consilium stays the deep agentic/LLMOps artifact; §6 is the breadth artifact.
