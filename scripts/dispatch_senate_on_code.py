"""Pre-compute and validate the input fields required for `senate --on-code`.

This script does NOT dispatch sub-agents — that is the orchestrator's job
(Claude in `/consilium senate --on-code`). This script's contract is to
produce the JSON input for `senate_synth.py` (and the per-senator prompts)
in code_audit mode, OR to fail HARD if any required field is missing.

Hard-failure contract (R3, Dimon Patches 1+2):
  - Empty / missing field → ValueError, dispatch aborted before any senator call
  - Empty files_touched list specifically → ValueError (binary-only / pure-rename
    diffs are not auditable via code_domain lens)
  - Interactive prompts refuse to block in CI: stdin not a TTY OR env var
    CONSILIUM_NON_INTERACTIVE set → RuntimeError (fail fast, no deadlock)

is_consilium_contribution auto-detect (R3, Dimon Patch 3):
  - If any file in files_touched starts with a Consilium-managed path, the
    flag is automatically set True (caller can override with --consilium /
    --no-consilium). Prevents silent UNREACHABLE on self-improvement audits.

Usage:
    python -X utf8 scripts/dispatch_senate_on_code.py \
        --description "Refactor auth middleware to use JWT" \
        [--magnitude high] [--reversibility partial] \
        [--blast-radius "Affects all authenticated endpoints"] \
        [--success-criterion "Login flow returns same tokens for valid creds"] \
        [--base-ref main] [--consilium | --no-consilium]

    # Output: JSON ready to pipe into senate_synth.py after senators have run.

Stdlib-only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

CONSILIUM_NON_INTERACTIVE_ENV = "CONSILIUM_NON_INTERACTIVE"
CONSILIUM_PATHS = ("prompts/", "scripts/", "SKILL.md", "CLAUDE.md", "runs/senate/")
MAGNITUDE_CHOICES = ("trivial", "moderate", "high", "critical")
REVERSIBILITY_CHOICES = ("complete", "partial", "irreversible")


def git_diff(base_ref: str | None) -> str:
    cmd = ["git", "diff"]
    if base_ref:
        cmd.append(f"{base_ref}...HEAD")
    try:
        return subprocess.check_output(cmd, text=True, errors="replace")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise RuntimeError(f"git diff failed: {e}") from e


def parse_files_from_diff(diff_text: str) -> list[str]:
    """Extract paths from `diff --git a/<path> b/<path>` lines."""
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3][2:] if parts[3].startswith("b/") else parts[3]
                files.append(path)
    return files


def looks_like_consilium_contribution(files: list[str]) -> bool:
    return any(any(f.startswith(p) for p in CONSILIUM_PATHS) for f in files)


def prompt_if_missing(prompt: str, value: str | None) -> str:
    """Resolve a field by reading user input, OR raise in non-interactive context."""
    if value:
        return value
    if not sys.stdin.isatty():
        raise RuntimeError(
            f"senate --on-code requires field '{prompt}' but stdin is not a TTY "
            f"(CI/automated context). Pre-set this field. Refuse to deadlock."
        )
    if os.environ.get(CONSILIUM_NON_INTERACTIVE_ENV):
        raise RuntimeError(
            f"senate --on-code: {CONSILIUM_NON_INTERACTIVE_ENV} is set but field "
            f"'{prompt}' is missing. Caller declared non-interactive intent."
        )
    return input(f"{prompt}: ").strip()


def build_dispatch_input(args: argparse.Namespace) -> dict:
    diff_text = git_diff(args.base_ref)
    if not diff_text.strip():
        raise ValueError(
            "senate --on-code: empty diff (git diff returned no content). "
            "Either pass --base-ref or commit your changes first. Dispatch aborted."
        )
    files = parse_files_from_diff(diff_text)
    # Explicit non-empty list check (R3 Dimon Patch 1)
    if not isinstance(files, list) or len(files) == 0:
        raise ValueError(
            "senate --on-code requires files_touched to be a non-empty list. "
            "Binary-only diffs and pure-rename diffs are not auditable via "
            "code_domain lens. Either: (a) audit content separately, or (b) "
            "use trias for the architectural decision. Dispatch aborted."
        )

    fields = {
        "diff": diff_text,
        "files_touched": files,
        "description": args.description,
        "success_criterion": prompt_if_missing(
            "Write 1-sentence testable success criterion", args.success_criterion,
        ),
        "magnitude": args.magnitude or prompt_if_missing(
            f"magnitude {MAGNITUDE_CHOICES}", None,
        ),
        "reversibility": args.reversibility or prompt_if_missing(
            f"reversibility {REVERSIBILITY_CHOICES}", None,
        ),
        "blast_radius": prompt_if_missing(
            "What breaks if this change is wrong (1 sentence)", args.blast_radius,
        ),
    }
    for k, v in fields.items():
        if not v:
            raise ValueError(
                f"senate --on-code requires non-empty '{k}'. Dispatch aborted "
                f"before sub-agent calls."
            )
    if fields["magnitude"] not in MAGNITUDE_CHOICES:
        raise ValueError(f"magnitude must be one of {MAGNITUDE_CHOICES}; got {fields['magnitude']!r}")
    if fields["reversibility"] not in REVERSIBILITY_CHOICES:
        raise ValueError(f"reversibility must be one of {REVERSIBILITY_CHOICES}; got {fields['reversibility']!r}")

    # Consistency warning (R3 Dimon Patch 1 continuation)
    if fields["magnitude"] == "trivial" and len(fields["blast_radius"]) > 50:
        print(
            f"WARNING: magnitude='trivial' but blast_radius is substantive "
            f"({len(fields['blast_radius'])} chars). Re-check calibration.",
            file=sys.stderr,
        )

    # is_consilium_contribution auto-detect (R3 Patch 3)
    if args.consilium is True:
        is_contrib = True
    elif args.consilium is False:
        is_contrib = False
    else:
        is_contrib = looks_like_consilium_contribution(files)

    return {
        "proposal": args.description,
        "label": args.label or "senate-on-code",
        "mode": "code_audit",
        "files_touched": files,
        "is_consilium_contribution": is_contrib,
        "_dispatch_fields": fields,  # for orchestrator to compose senator prompts
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--description", required=True, help="Plain text describing the change")
    p.add_argument("--success-criterion", default=None)
    p.add_argument("--magnitude", choices=MAGNITUDE_CHOICES, default=None)
    p.add_argument("--reversibility", choices=REVERSIBILITY_CHOICES, default=None)
    p.add_argument("--blast-radius", default=None)
    p.add_argument("--base-ref", default=None, help="Git base ref to diff against (e.g. main)")
    p.add_argument("--label", default=None)
    consilium_group = p.add_mutually_exclusive_group()
    consilium_group.add_argument("--consilium", dest="consilium", action="store_true", default=None,
                                  help="Force is_consilium_contribution=True (disables off-target detection)")
    consilium_group.add_argument("--no-consilium", dest="consilium", action="store_false",
                                  help="Force is_consilium_contribution=False")
    return p.parse_args()


def main() -> int:
    try:
        result = build_dispatch_input(parse_args())
    except (ValueError, RuntimeError) as e:
        print(f"dispatch_senate_on_code: {e}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
