"""Trias mode — 3 fixed personalities with weights + lens paths.

Replaces the old random-sampling Ensemble personalities. Each personality is
a named character with:
- weights: how it ranks candidates after voice scores arrive
- lens: a prompt prepended to each voice prompt that biases voice perception

CLI:
    python personalities.py                  # emit all 3 as JSON array
    python personalities.py --name pioneer   # emit single personality
    python personalities.py <N>              # legacy form — rejected with exit 2
"""
# implements: CONSILIUM-PERSONALITIES-001

from __future__ import annotations

import argparse
import copy
import json
import sys

PERSONALITIES = [
    {
        "name": "pioneer",
        "weights": {"generator": 0.49, "control": 0.30, "conservator": 0.21},
        "lens": "prompts/voices/pioneer_lens.md",
    },
    {
        "name": "architect",
        "weights": {"generator": 0.30, "control": 0.40, "conservator": 0.30},
        "lens": "prompts/voices/architect_lens.md",
    },
    {
        "name": "steward",
        "weights": {"generator": 0.30, "control": 0.30, "conservator": 0.40},
        "lens": "prompts/voices/steward_lens.md",
    },
]

NAMES = tuple(p["name"] for p in PERSONALITIES)


def get_by_name(name: str) -> dict:
    """Return a deep copy of the named personality.

    Returns a copy (not a reference) so callers can augment the dict at
    runtime (e.g. adding `chose` during deliberation) without mutating the
    module-level PERSONALITIES list.
    """
    for p in PERSONALITIES:
        if p["name"] == name:
            return copy.deepcopy(p)
    raise KeyError(f"unknown personality: {name!r} (valid: {sorted(NAMES)})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--name",
        choices=sorted(NAMES),
        default=None,
        help="emit single personality by name (default: emit all 3)",
    )
    # Reject the old positional-N signature explicitly for clearer migration.
    ap.add_argument(
        "n_legacy",
        nargs="?",
        default=None,
        help=argparse.SUPPRESS,
    )
    args = ap.parse_args(argv)

    if args.n_legacy is not None:
        print(
            "error: personalities.py no longer samples random N personalities.\n"
            "       Trias mode uses 3 fixed personalities: pioneer, architect, steward.\n"
            "       Run without arguments to emit all 3, or use --name <pioneer|architect|steward>.",
            file=sys.stderr,
        )
        return 2

    if args.name is not None:
        json.dump(get_by_name(args.name), sys.stdout, indent=2)
    else:
        json.dump([copy.deepcopy(p) for p in PERSONALITIES], sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
