---
id: CONSILIUM-INFER-PIPELINE-001
status: baseline
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# infer_pipeline

> Infers the post-deliberation implementation steps from Conservator magnitude/reversibility.

## Input
- Deliberation report JSON - via `--input <path>` or stdin
- CLI flags: `--dry-run`, `--yes`, `--debug`

## Description
Infers and presents for confirmation the ordered post-deliberation implementation steps (implement, compile, review, test) based on the `magnitude` and `reversibility` fields from the Conservator voice in the deliberation log. A lookup table maps every `(magnitude, reversibility)` pair to a step list; when Conservator fields are absent or off-vocabulary the script falls back to deriving magnitude from `voice_scores.conservator` (a scalar net_concern) while carefully avoiding inferring `irreversible` from the scalar because a floored net_concern is ambiguous. The companion function `recommend_implement_mode` is also exported and used by the orchestrator to route Step 7 between `pipeline` and `single_shot` dispatch - the signal is the presence of a `review` step, which appears exactly in regression-prone quadrants. User rejections are persisted to `.consilium/runs/` as `pipeline_rejected.json` events.

## Output
- stdout: human-readable proposed pipeline and `{"steps": [...], "rationale": {...}}` JSON
- `.consilium/runs/<ts>_pipeline_rejected.json` written on user rejection (interactive mode only)
- exit code 0 on confirmation or dry-run, 1 on user decline or empty steps, 2 on malformed input

## Acceptance (= tests)
- For `chosen_approach` of `do_nothing` or `null`, `infer_steps` returns an empty list with a `reason` key in the rationale.
- A report with `magnitude=high` and `reversibility=irreversible` in the Conservator deliberation log yields steps `[implement, compile, review, test]`.
- When Conservator fields are missing, the script falls back to `voice_scores.conservator` scalar and never infers `irreversible` reversibility from it.
- `--dry-run` prints steps and rationale JSON and exits 0 without prompting the user.
- `--yes` skips the interactive confirmation prompt, enabling CI/headless use.
