---
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-VOICE-CONTROL-001
status: baseline
layer: feature
owner: auto
depends_on: []
---

# control voice

> WHY: The Control voice analytically validates every Generator candidate for correctness, type safety, and goal-fit, and surfaces hidden assumptions and glossary gaps that could cause the deliberation to produce a wrong answer.

## WHAT — Contract (normative)

- The voice shall emit a `glossary` object with 2–5 operationally-defined terms specific to the current deliberation; if it cannot define a key term after 3 attempts it shall set `glossary_fail: true` and document all 3 attempts in `glossary_attempts`, which signals the aggregator to BLOCK and request reformulation.
- The voice shall emit a `verdicts` array containing one entry per candidate; each verdict must include `id`, `valid` (boolean), `confidence_in_verdict` (`high` | `medium` | `low`), `issues` (with `category`, `detail`, `severity` per entry), and `tests_to_write` (1–4 concrete test stubs for every `valid: true` candidate that is not `do_nothing`).
- The voice shall check goal-fit first and, if the candidate does not address `success_criterion`, mark `valid: false` with `category: "logic"` and skip all remaining checks for that candidate.
- The voice shall emit a `disagreements` array classifying any substantive conflict between voices as `substantial` (different answer → REWORK) or `terminological` (same answer, different words → note and continue).
- When the voice cannot verify a signature without reading a file and file access fails, the `unverifiable — file not accessible` marker in the verdict is the intended degradation signal. This is transparent and recorded in verdicts visible to the aggregator and report; no harder signal is required.
- The 3-entry cap on `hidden_assumptions` and the self-assessed selection criterion are by design. Control is a deliberative voice, not a formal verifier; the design intentionally trusts the voice to surface the most consequential assumptions.

## WHAT — Notes & known limitations (informative)

- `confidence_in_verdict: low` is advisory only — the aggregator does not automatically discount verdicts marked `low`, so a technically `valid: true` / `low` verdict can influence the final recommendation without the reader realizing the validation was speculative.

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
