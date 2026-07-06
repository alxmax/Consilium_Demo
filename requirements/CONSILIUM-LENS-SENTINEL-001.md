---
milestone: v1.1
test_exempt: "prompt/mode document — acceptance validated by deliberation integration runs, not unit tests"
id: CONSILIUM-LENS-SENTINEL-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-PERSONALITIES-001]
---

# sentinel lens

> WHY: conservator-heavy member of the Trias personality team — biases all three voices toward stress-testing: sketch the plausible adverse scenario per candidate, weigh probability × downside magnitude, name the counterparty, and treat silent failure modes as the heaviest risk class.

## WHAT — Contract (normative)
- The lens shall cause the voice it overlays to weigh adverse scenarios (graceful / hard / silent failure) and counterparty exposure more heavily than it would by default, with silent failure modes weighted heaviest.
- The lens shall preserve each voice's standard structural role; it shifts perception and priority without suppressing the role's core output.
- When applied to Generator, stress framing shall be expressed in each candidate's risks/trade-off fields — the full 3-5 candidate spread is still produced, including higher-upside candidates; a candidate is never suppressed for having a stress scenario.
- When applied to Conservator, the lens shall affect only magnitude calibration and meta_recommendation; it shall not inflate the `net_concern` numerical formula through vivid scenario prose.
- The lens is the conservator-heavy Trias personality (weights generator 0.30 / control 0.30 / conservator 0.40) and is one of the three fixed personalities the Trias team dispatches.

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## HOW — Acceptance (= tests)
AC-1
  Given  two otherwise comparable candidates, one carrying a plausible silent-failure mode and one failing loudly
  When   the Sentinel lens is prepended to a core voice
  Then   the voice ranks the loud-failure candidate above the silent-failure one, and the silent-failure mode is surfaced explicitly

AC-2
  Given  the Sentinel lens applied to the Generator voice
  When   the Generator produces its candidate spread
  Then   the spread still contains 3-5 candidates including higher-upside options, each with its adverse scenario recorded in the risks/trade-off fields

## WHERE — Current implementation
- prompts/voices/sentinel_lens.md

## Why test_exempt

This file is a personality-lens overlay — plain text prepended to a core voice prompt at runtime by `personalities.py` for Trias mode. It contains no executable Python logic; conformance is validated through Trias deliberation integration runs. Deterministic guards (frontmatter + bias-keyword signature) live in scripts/test_lens_bias.py.
