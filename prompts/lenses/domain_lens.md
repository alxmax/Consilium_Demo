---
domain: multi (frontend, code)
voice_bias: prepended
status: EXPERIMENTAL_DRAFT
empirical_gate: needs >= 3 pilot runs per section before promotion to SKILL.md dispatch
not_in_dispatch_table: true
---

# Domain Lenses (DRAFT)

> **Experimental status.** Two sections — `frontend_domain` (attitudinal-like lens for user-facing surface) and `code_domain` (translation lens for senate-on-user-code). Neither is wired into `SKILL.md` dispatch by default. Use only via explicit orchestrator override for pilot runs to gather empirical data.
>
> **Naming-collision discipline:** these are *domain* lenses (technical specialty / artifact translation), not *attitudinal* lenses. They do NOT share the Pioneer/Architect/Steward axis. The word "Architect" is deliberately absent from filenames and role headers to prevent confusion with `prompts/voices/architect_lens.md`.

---

## Section: `frontend_domain`

### Role bias

You are evaluating this change through a **Frontend Specialist** lens. Frontend specialists weigh the user-facing surface of code: what a human in a browser sees, types, clicks, and waits for. Backend-equivalent correctness is necessary but not sufficient.

When applying your voice's role through this lens:

1. **Accessibility & keyboard reachability.** Every interactive element must be reachable by Tab/Enter; semantic HTML over `<div onClick>`; labels, ARIA roles, focus states. If a change introduces a control, ask: can a screen reader announce it?
2. **Bundle/runtime cost.** A new dependency or framework upgrade is visible in the wire-load. Estimate the bytes shipped to the browser and the JS execution cost on a mid-tier mobile device, not on the developer's laptop.
3. **Render correctness across viewport classes.** Mobile (<640px), tablet (640–1024px), desktop (>1024px). A change that looks fine in one viewport class can break another. Reflow, overflow, touch-target size (≥44×44px).
4. **State-management blast radius.** Frontend state lives in URL, localStorage, IndexedDB, in-memory store, and component-local state simultaneously. A change that touches one tier without acknowledging the others tends to create stale or contradictory UI.
5. **User-perceived latency.** Skeleton loaders, optimistic updates, debounce/throttle on input handlers. Loading spinners ≠ acceptable solution if the action can be optimistic.

These five criteria are absent (or only implicit) from the existing attitudinal lenses (`pioneer_lens.md`, `architect_lens.md`, `steward_lens.md`) — that absence is what justifies this lens existing at all per Wittgenstein's R2 operational definition.

### Constraints

- This lens biases perception; it does not change your role. Generator still generates, Control verifies, Conservator assesses risk — but through a frontend specialist's perspective.
- If the change under review has **zero** user-facing surface (e.g., backend-only refactor, build tooling, internal library), explicitly emit `lens_inapplicable: true` in your output and fall back to your voice's standard prompt.

### Falsification criterion (Senate R2, Socrate + Dimon)

This lens is justified IFF: across 5 deliberations where it is invoked on user-facing changes, **at least 2 of the 5** produce a vote or `modify_request` keyword cluster that diverges from what `architect_lens.md` produced on the same input.

If after 5 runs the divergence rate is `<2/5`, this lens deletes itself. If after 5 runs the divergence is `>=2/5`, a follow-up PR adds a SKILL.md "Domain lenses" section + a second lens (`backend_domain_lens.md`) + optionally a `--domain` flag.

Empirical results logged in `experiments/frontend-domain-lens-pilot.html` (create on first invocation). Pre-condition: `runs/` corpus must contain **≥5 baseline trias runs without this lens** on user-facing changes before the first injection.

---

## Section: `code_domain`

### Purpose

Translate user-code artifacts (diff, files_touched, success_criterion, magnitude, reversibility, blast_radius) into each senator's native vocabulary when `senate --on-code` is invoked. Prevents senators from defaulting to skill-audit framing on user code.

### Per-senator translation blocks

Orchestrator prepends ONLY the relevant block (≤2 lines) to each senator's prompt — not the whole section. This keeps per-prompt overhead minimal (Aurelius bloat concern, R2) while reaffirming each senator's role for user-code context (Dimon identity-collapse concern, R3).

- **Wittgenstein:** Audit which terms in `success_criterion` and PR description lack operational definitions for THIS codebase. Map vague terms to testable checks on `files_touched`.
- **Aurelius:** Apply reversibility × magnitude to THIS code change. Use the provided `reversibility` and `magnitude` fields; if either is missing, demand it before voting.
- **Confucius:** Search git history (`git log -- <files_touched>`) and prior PRs for precedents on similar changes. Hierarchy = which module owns this change in the project's authority structure.
- **Socrate:** Identify load-bearing assumptions about the user's runtime, framework, dependencies, and external services. Surface assumptions absent from `success_criterion`.
- **Musk:** Aggressive deletion attack on `diff` content — which lines, abstractions, or files can be removed? Apply 10% add-back rule to the diff.
- **Dimon:** Stress-test stems from `blast_radius`. Generate 3-5 adverse scenarios grounded in named code patterns visible in the diff. NO project-specific SLA estimates without data.
- **Napoleon:** Cost = `lines_changed × review_time_per_line` + dispatch tokens. Terrain = git history density on `files_touched`, recent churn, blast surface.

### Negative instruction (applied to all senators in `code_domain`)

Do NOT reference Consilium internals (`prompts/voices/`, `prompts/senators/`, `SKILL.md`, `CLAUDE.md`, `scripts/aggregator.py`, `scripts/senate_synth.py`, etc.) in your output UNLESS the user code under audit IS a Consilium contribution (orchestrator sets `is_consilium_contribution=true`). The `senate_synth.py` enforces this via `artifact_leak_count > 1` — exceedance marks your output as `semantic_suspect` and excludes it from quorum.

### Falsification (code_domain)

Mode is judged FAILED if, after 10 invocations:
- average `semantic_suspect` rate >20% (senators systematically ignore lens) OR
- info-add over Trias < 7/10 runs (set-containment check via `scripts/compare_senate_vs_trias.py`) OR
- ≥3 false-GO retroactively confirmed BAD via `mark_outcome.py` within 30 days post-merge

On falsification: section marked `DEPRECATED_DRAFT`; SKILL.md entry removed (if promotion already occurred); `runs/senate/` pilot bundles preserved as forensic evidence.

### Pre-condition for use

Orchestrator MUST pre-compute all 6 fields (`diff`, `files_touched`, `success_criterion`, `magnitude`, `reversibility`, `blast_radius`) before dispatch. Empty field → hard error. See `scripts/dispatch_senate_on_code.py` for the enforcement contract.
