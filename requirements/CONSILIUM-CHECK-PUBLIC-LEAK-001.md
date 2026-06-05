---
id: CONSILIUM-CHECK-PUBLIC-LEAK-001
status: confirmed
layer: feature
owner: auto
test_exempt: "subprocess git ls-files and filesystem scan — integration-only"
depends_on: []
risk: 1
---

# check_public_leak

> Fails CI if any git-tracked file references the private repo or a local developer path.

## Input
- All files tracked by `git ls-files` in the current working directory
- No CLI flags (runs unconditionally)

## Description
Guards the public release repository against accidentally referencing the private development repository or leaking local developer paths. It scans every git-tracked text file for two compiled regex patterns: a reference to the private dev repo (the owner/name slug, excluding the public `_Demo` mirror) and an absolute local path under the author's working tree. The exact patterns live in the source — this doc deliberately does not quote them, because doing so would itself trip the guard. Binary and image file extensions are skipped, and the guard file itself is excluded from its own scan. The check is wired into CI and fails with exit 1, printing the offending `file:line: description: match` tuples to stderr, making private-repo references un-shippable rather than a silent leak.

## Output
- stdout: `public-leak guard: clean` on success
- stderr: list of offending `file:line: description` strings on failure
- exit code 0 on clean, 1 on any pattern match

## WHAT — Contract (normative)
- The `PATTERNS` constant and its inline comments are the sole specification for the regex patterns; there is no secondary config or spec file.
- The skip list (`SKIP_SUFFIX`) is a heuristic hardcoded tuple of 11 extensions. A binary file committed with a `.txt` extension is **not** skipped — it is read with `errors="ignore"` and scanned like any text file.
- When run outside a git repository (`git ls-files` fails), the script raises an unhandled `subprocess.CalledProcessError` and exits 1 with a Python traceback to stderr — same exit code as a leak find, but distinguishable by the traceback.

## WHAT — Verify intent
- None - all questions resolved.

## Acceptance (= tests)
- Running against a repo with no private-repo (non-Demo) or local-path references exits 0 and prints `clean`.
- A tracked file containing a non-Demo private-repo ref causes exit 1 with the file and line number printed to stderr.
- A tracked file containing an absolute local developer path causes exit 1 with the offending location reported.
- Binary and image files (`.png`, `.woff`, etc.) are skipped even if they match the patterns byte-for-byte.
- The guard script itself (`check_public_leak.py`) is excluded from its own scan and never self-reports.

## Why test_exempt

`check_public_leak.py` shells out to `git ls-files` and scans all tracked file paths for local-path strings and private-repo references. Reproducing the scan in a unit test requires a real git repository with a known tracked file set. The CI run against the actual repo serves as the acceptance test — the script is meaningless outside a real git working tree.
