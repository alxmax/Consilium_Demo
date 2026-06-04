---
id: CONSILIUM-STABILITY-CHECK-001
status: baseline
layer: feature
owner: auto
test_exempt: "reads runs/ directory at test time — integration-only analysis tool"
depends_on: [CONSILIUM-UTILS-001]
risk: 1
---

# stability_check

> Voice-score calibration analysis (retrospective / compare / pick) per the R2 audit Bug #1.

## Input
- `--runs-dir <path>`: directory of run JSON files (default: `.consilium/runs` from `CONSILIUM-UTILS-001 RUNS_DIR`, or `runs` as fallback)
- `--compare <RUN_A> <RUN_B>`: paths to two run JSON files for pairwise comparison
- `--pick <N>`: integer, number of candidate runs to select for the prospective experiment

## Description
Voice-score calibration analysis tool that implements the experiment protocol from the R2 audit (Bug #1: `voice_scores_uncalibrated_measurements`). In retrospective mode it scans an entire runs directory and prints per-voice statistics (mean, pstdev, quartiles) alongside a veto-boundary analysis highlighting runs whose conservator score falls in the uncertain band around the 0.8 veto threshold. In compare mode it takes two runs on the same input, computes pstdev per voice, flags high-variance voices, and checks categorical stability (magnitude and reversibility) to confirm or refute Bug #1 empirically. In pick mode it selects candidate runs closest to the veto boundary for use in a prospective re-run experiment.

## Output
- Retrospective: formatted calibration report and veto boundary analysis printed to stdout
- Compare: per-voice diff/pstdev table and Bug #1 verdict printed to stdout; exits 1 if `voice_scores` missing
- Pick: ranked list of N candidate runs with conservator scores and success criteria printed to stdout

## Acceptance (= tests)
- Running `--runs-dir` against a populated runs directory prints per-voice statistics for generator, control, and conservator without error.
- The `--compare` mode prints `Bug #1 CONFIRMED` when mean pstdev across voices exceeds 0.10 and `Bug #1 OK` when it does not.
- The `--compare` mode detects and flags a magnitude or reversibility mismatch between the two runs as `*** FLIP`.
- The `--pick` mode returns exactly N candidates sorted by proximity to the 0.8 veto boundary.
- A runs directory with no files containing `voice_scores` prints a `No runs with voice_scores found` message to stderr without crashing.
