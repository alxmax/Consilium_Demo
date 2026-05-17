"""Measure info-add of a senate code_audit bundle over a Trias bundle on the
same input. Implements the falsification criterion declared in the
EXPERIMENTAL_DRAFT phase of `senate --on-code` (SKILL.md Drafts footnote).

MAINTENANCE-DEFERRED: This script is frozen at current coverage until Senate
usage exceeds 5 runs/month. Do not add features or tests until gate criteria
are met (see SKILL.md Drafts footnote for gate definition).


Usage:
    python -X utf8 scripts/compare_senate_vs_trias.py <senate_bundle.json> <trias_bundle.json>

Exit codes:
    0 — Senate output ⊆ Trias output (no info-add; counts toward gate failure)
    1 — Senate output adds file/construct references absent from Trias (info-add)
    2 — Bundle parse error or missing required fields

Method: extract file paths and identifier tokens (function/class names matching
[A-Za-z_][A-Za-z0-9_]*\\(?) from each bundle's modify_requests + verdicts and
compute set difference. Both bundles must reference the same logical change
(same files_touched); caller is responsible for pairing.

Stdlib-only. No external dependencies. Path normalization is naive (strip
leading './' and absolute prefixes); supply normalized paths upstream for
strict matching.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
PATH_RE = re.compile(r"[A-Za-z0-9_./\\-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|md|json|yaml|yml|sh|sql|html|css)")


def normalize_path(p: str) -> str:
    p = p.strip().replace("\\", "/").lstrip("./")
    # Strip leading absolute prefix to first repo-rooted segment
    for marker in ("scripts/", "prompts/", "src/", "lib/", "tests/", "experiments/", "runs/"):
        i = p.find(marker)
        if i > 0:
            return p[i:]
    return p


def extract_refs(bundle: dict) -> tuple[set[str], set[str]]:
    """Return (file_refs, construct_names) from a senate or trias bundle."""
    blob = json.dumps(bundle, ensure_ascii=False)
    paths = {normalize_path(m) for m in PATH_RE.findall(blob)}
    constructs = set(IDENT_RE.findall(blob))
    # Strip common stop-words / framework tokens to reduce false positives
    stop = {
        "true", "false", "null", "and", "or", "not", "the", "for", "from",
        "with", "this", "that", "vote", "GO", "MODIFY", "STOP", "verdict",
        "Senate", "Trias", "Senator", "senator", "json", "JSON",
    }
    constructs = {c for c in constructs if c not in stop and not c.isdigit()}
    return paths, constructs


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    senate_path, trias_path = Path(sys.argv[1]), Path(sys.argv[2])
    try:
        senate = json.loads(senate_path.read_text(encoding="utf-8"))
        trias = json.loads(trias_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"compare_senate_vs_trias: parse error: {e}", file=sys.stderr)
        return 2

    s_paths, s_constructs = extract_refs(senate)
    t_paths, t_constructs = extract_refs(trias)
    paths_diff = s_paths - t_paths
    constructs_diff = s_constructs - t_constructs

    result = {
        "senate_bundle": str(senate_path),
        "trias_bundle": str(trias_path),
        "senate_unique_paths": sorted(paths_diff),
        "senate_unique_constructs": sorted(constructs_diff),
        "info_add": bool(paths_diff or constructs_diff),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["info_add"] else 0


if __name__ == "__main__":
    sys.exit(main())
