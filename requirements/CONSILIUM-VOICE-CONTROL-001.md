---
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

## WHAT — Verify intent (open questions for the human)

- Observed: the prompt instructs Control to read files when it cannot verify a signature, but Control runs inside a single-context pipeline where it may not have tool access. The fallback (`mark category: "types", detail: "unverifiable — file not accessible"`) silently degrades confidence. Intended behavior, or should there be a harder signal when file access fails systematically?
- Observed: `hidden_assumptions` is capped at 3 entries, but the selection criterion ("only include assumptions where if false the answer changes") is self-assessed by the model. No external check exists on whether excluded assumptions actually were non-load-bearing. Is this intentional trust in the voice?

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
