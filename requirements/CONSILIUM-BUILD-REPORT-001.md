---
milestone: v1.0
id: CONSILIUM-BUILD-REPORT-001
status: confirmed
layer: feature
owner: auto
depends_on: [CONSILIUM-UTILS-001]
risk: 2
---

# build_report

> Assembles the canonical deliberation report shape from intermediate voice/aggregation outputs.

## Input
- stdin or `--input` file: JSON bundle with keys `success_criterion`, `verification`, `generator`, `control`, `conservator`, `aggregate`, `confidence`, and optional `telemetry`, `reasoning`, `alternatives_limit`, `team`, `personalities`, `vote_pattern`, `personality_choices`, `deliberation_quality`, `vote_skipped`
- For skipped bundles: `skipped: true` plus `skip_reason` and `signals` instead of voice outputs
- CLI flag `--input`: path to JSON bundle file (default: stdin)

## Description
Assembles the canonical deliberation report shape from the intermediate voice and aggregation outputs, eliminating the error-prone manual JSON construction that previously occurred in the orchestrator between pipeline steps. It extracts the chosen candidate's voice scores from the control verdict and conservator score lists, derives `why_not` summaries for each non-chosen alternative from control issues and conservator risk, and stamps version provenance (`consilium_version` and `consilium_ref`) into the telemetry block of every report it emits. Skipped reports (trivial-direct, prior-deliberation passthrough) are handled via a separate code path that requires only `skip_reason` and `signals`; `pipeline_executed` is absent (not set) on skipped reports — `validate_report.py` skips the field check entirely when `skipped: true`. Full pipeline reports always set `pipeline_executed: true`. The output must pass `validate_report.py` to be written to `.consilium/runs/`.

`why_not` for non-chosen candidates combines both Control issues and Conservator risk: if the control verdict is invalid, it lists issue categories; if valid but issues exist, it uses the first issue's detail; if Conservator `net_concern >= 0.5`, it appends `risk=N.NN`. When neither source yields text, the fallback is `"ranked below chosen"` (or `"all candidates vetoed"` when `chosen` is null).

`--input` and stdin are mutually exclusive by argparse design (`FileType` default is stdin; providing `--input` opens the file instead). No conflict resolution is needed — only one source is ever active.

## Output
- stdout: canonical JSON report with fields: `success_criterion`, `verification`, `chosen_approach`, `reasoning`, `alternatives`, `voice_scores`, `confidence`, `pipeline_executed`, `deliberation_log`, `telemetry`, and optional Trias fields (`team`, `personalities`, `vote_pattern`, `dissent`, `abstained`, `personality_choices`)
- exit code 0 on success
- exit code 1 on missing required field
- exit code 2 on malformed JSON input

## WHAT — Verify intent (open questions for the human)
- None - all questions resolved.

## Acceptance (= tests)
- Given a well-formed full bundle, the output contains `pipeline_executed: true` and a `deliberation_log` array with entries for steps `generator`, `control`, `conservator`, and `aggregate`.
- Given a skipped bundle (`skipped: true`) with valid `skip_reason`, the output contains `chosen_approach: skipped`, `pipeline_executed` absent or false, and `deliberation_log: []`.
- Given a bundle where the chosen candidate has a control verdict with `valid=false` and issues, the output's `voice_scores.control` is less than 1.0 and alternatives list a `why_not` string derived from the issues.
- Given any valid bundle, the telemetry block in the output contains non-empty `consilium_version` and `consilium_ref` fields stamped by the version module.
- Given a bundle missing `success_criterion`, the script exits with code 1 and prints an error to stderr without writing any JSON to stdout.
