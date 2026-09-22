---
milestone: v1.0
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-VOICE-CONTROL-001
status: confirmed
level: code
layer: feature
owner: alxmax
depends_on: []
satisfies: [ARCH-CONSILIUM-VOICES-001]
---

# control voice

> WHY: The Control voice analytically validates every Generator candidate for correctness, type safety, and goal-fit, and surfaces hidden assumptions and glossary gaps that could cause the deliberation to produce a wrong answer.

## WHAT — Contract (normative)

- The voice emits a `glossary` object with 2–5 operationally-defined terms specific to the current deliberation; if it cannot define a key term after 3 attempts, it sets `glossary_fail: true` and documents all 3 attempts in `glossary_attempts`, which signals the aggregator to BLOCK and request reformulation.
- The voice emits a `verdicts` array containing one entry per candidate; each verdict includes `id`, `valid` (boolean), `confidence_in_verdict` (`high` | `medium` | `low`), `issues` (with `category`, `detail`, `severity` per entry), and `tests_to_write` (1–4 concrete test stubs for every `valid: true` candidate that is not `do_nothing`).
- The voice checks goal-fit first and, if the candidate does not address `success_criterion`, marks `valid: false` with `category: "logic"` and skips all remaining checks for that candidate.
- The voice emits a `disagreements` array classifying any substantive conflict between voices as `substantial` (different answer → REWORK) or `terminological` (same answer, different words → note and continue).
- The voice cannot always verify a signature without reading a file; when file access fails in that situation, the `unverifiable — file not accessible` marker in the verdict is the intended degradation signal.
- This degradation is transparent: the marker is recorded in verdicts visible to the aggregator and the report, and no harder signal is required.
- The 3-entry cap on `hidden_assumptions` and the self-assessed selection criterion are by design. Control is a deliberative voice, not a formal verifier; the design intentionally trusts the voice to surface the most consequential assumptions.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## WHAT — Notes & known limitations (informative)

- `confidence_in_verdict: low` is advisory only — the aggregator does not automatically discount verdicts marked `low`, so a technically `valid: true` / `low` verdict can influence the final recommendation without the reader realizing the validation was speculative. This is intentional: `low` is a transparency signal prompting the reader to treat the verdict as speculative, not a veto mechanism. The design choice is to surface speculation honestly rather than suppress it.
- In Sequential mode all three voices (Generator → Conservator → Control) produce their outputs before the aggregator evaluates them. A `glossary_fail` is therefore detected post-hoc by the aggregator; Control always runs last (after Generator and Conservator) with access to Generator's candidates. (The irreversibility consent BLOCK, by contrast, fires pre-dispatch at Step 1.6, before Generator.) AC-2 reflects this correctly.
- No retrospective signal exists to detect cases where the 3-entry cap on `hidden_assumptions` caused a critical assumption to be dropped. This is a known, accepted gap.

## HOW — Acceptance (= tests)

AC-1
  Given a Generator candidate whose `sketch` does not address the stated `success_criterion`
  When  the Control voice runs
  Then  the verdict for that candidate has `valid: false`, `issues` contains exactly one entry with `category: "logic"`, and no `tests_to_write` entries are present for that candidate

AC-2
  Given a deliberation where a key term cannot be operationally defined within 3 attempts
  When  the Control voice runs
  Then  the output has `glossary_fail: true`, `glossary_attempts` is an array of exactly 3 entries, and no other mandatory processing is skipped (verdicts are still emitted)

AC-3
  Given a valid, non-`do_nothing` candidate that passes all checks
  When  the Control voice runs
  Then  the verdict has `valid: true`, `confidence_in_verdict` is one of `high|medium|low`, and `tests_to_write` contains at least 1 entry with both `name` and `assert` fields populated

## WHERE — Current implementation

- prompts/voices/control.md

## Why test_exempt

This file is a prompt document — plain text read by the deliberation orchestrator or a sub-agent at runtime. It contains no executable Python logic; its "behavior" is the model's response to the text, which is non-deterministic and cannot be asserted in a repeatable unit test. Correctness is validated through deliberation integration runs stored in `.consilium/runs/` and manual review of real outputs, not by a stable `expected == actual` assertion.
