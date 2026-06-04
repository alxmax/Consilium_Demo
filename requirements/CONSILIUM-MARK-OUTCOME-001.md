---
id: CONSILIUM-MARK-OUTCOME-001
status: confirmed
layer: feature
owner: auto
test_exempt: "importlib module loading and FEEDBACK.html mutation — integration-only"
depends_on: [CONSILIUM-FEEDBACK-001, CONSILIUM-RENDER-FEEDBACK-HTML-001, CONSILIUM-UTILS-001]
risk: 1
---

# mark_outcome

> Corrects a logged FEEDBACK.html outcome in place once production reality is known.

## Input
- CLI flag `--run-path`: relative or absolute path to a `runs/*.json` file used as a lookup key
- CLI flags `--date YYYY-MM-DD` and `--chosen <id>`: alternative direct-match strategy when `--run-path` is unavailable
- CLI flag `--outcome`: one of `OK | BAD | OVR | PEND | PEND_HEADLESS` (required)
- CLI flag `--reason`: optional short string appended to the note as `outcome_reason=...`
- CLI flag `--dry-run`: print matched rows without writing
- CLI flag `--benchmark`: required guard when `--outcome PEND_HEADLESS` is used
- CLI flag `--feedback`: optional override path to FEEDBACK.html
- `.consilium/FEEDBACK.html`: existing feedback journal read and rewritten in place
- `.consilium/runs/.run_path_map.json`: sidecar fingerprint map populated by `log_feedback.py`

## Description
Closes the feedback loop opened by `log_feedback.py` by allowing an outcome recorded at deliberation time to be corrected based on what happened in production. Because the initial outcome logged at Step 6 is a subjective gut-feel, production reality can contradict it days later (a chosen approach may break production, or a risky override may prove correct). The script rewrites the matched FEEDBACK.html row in place, updating the outcome cell and annotating the note with `[confirmed]` so `priors.py` can weight confirmed-outcome rows higher than purely subjective ones. Rows are located via a fingerprint sidecar map (`--run-path`) or by a direct date+chosen pair, with a fallback diagnostic listing the five most recent entries when no match is found. A `--dry-run` flag allows inspection of which rows would be updated without modifying any file.

## Output
- Overwrites `.consilium/FEEDBACK.html` atomically with updated outcome and annotated note for each matched row
- stdout: per-matched-row lines of the form `matched [i]: date | chosen | old_outcome -> new_outcome`
- stdout: `skip [i]: ...` lines when a row is already at the target outcome or when PEND_HEADLESS is applied to a non-PEND row
- stdout: `(dry-run; no write)` when `--dry-run` is active
- exit code 0 on success or when no rows needed updating; exit code 1 on missing feedback file, bad argument combinations, or no match found

## Acceptance (= tests)
- Given a valid `--run-path` pointing to a logged run, the corresponding FEEDBACK.html row's outcome field is updated to the specified value and the note gains `[confirmed]` (or `outcome_reason=...` if `--reason` is provided).
- Given `--dry-run`, no file is written and stdout reports the matched rows with their pending transition.
- Given `--outcome PEND_HEADLESS` without `--benchmark`, the script exits 1 with a descriptive error and does not modify FEEDBACK.html.
- Given neither `--run-path` nor both `--date` and `--chosen`, the script exits 1 with a usage error.
- Given a query that matches no rows, the script exits 1 and prints the last 5 rows to stderr as disambiguation candidates.
