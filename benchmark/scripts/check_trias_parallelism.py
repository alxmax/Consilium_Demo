"""Check whether a consilium_trias run dispatched the 3 personalities in parallel.

Updates `pipeline_audit.json` in the workspace with `trias_serial_dispatch: bool`:
- True  = real deliberation (num_turns > 4) but api/wall ratio < 1.5 → sequential dispatch
- False = real deliberation with ratio >= 1.5 (parallel evidence) OR scale_down (num_turns <= 4, no dispatch to check)
- field absent = mode is not consilium_trias or claude_raw.json missing

Theoretical reference: 3 personalities dispatched in same orchestrator message → ratio ≈ 3.0.
Pure sequential dispatch → ratio ≈ 1.0. We flag below 1.5 as serial drift, calibrated from
the 2026-05-28 benchmark survey (n=8 real-deliberation Trias runs, range 0.99-1.19x).

CLI:
    python check_trias_parallelism.py <workspace_dir>

Exits 0 always (advisory, never blocks). Mirrors the pattern of
benchmark/run_task.py::detect_pipeline_execution.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SERIAL_RATIO_THRESHOLD = 1.5
SCALE_DOWN_MAX_TURNS = 4


def _find_raw(workspace: Path) -> Path | None:
    """Return claude_raw.json at workspace root or in the highest-numbered rep_*."""
    direct = workspace / "claude_raw.json"
    if direct.exists():
        return direct
    reps = sorted(
        (p for p in workspace.iterdir() if p.is_dir() and p.name.startswith("rep_")),
        key=lambda p: p.name,
    )
    for rep in reversed(reps):
        cand = rep / "claude_raw.json"
        if cand.exists():
            return cand
    return None


def check(workspace: Path) -> dict | None:
    """Compute the parallelism verdict for one workspace. Returns None if N/A."""
    raw = _find_raw(workspace)
    if raw is None:
        return None
    try:
        data = json.loads(raw.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    turns = data.get("num_turns") or 0
    wall_ms = data.get("duration_ms") or 0
    api_ms = data.get("duration_api_ms") or 0
    if wall_ms <= 0:
        return None

    ratio = api_ms / wall_ms
    if turns <= SCALE_DOWN_MAX_TURNS:
        return {
            "trias_serial_dispatch": False,
            "trias_parallel_ratio": round(ratio, 3),
            "trias_dispatch_pattern": "scale_down",
            "trias_num_turns": turns,
        }
    return {
        "trias_serial_dispatch": ratio < SERIAL_RATIO_THRESHOLD,
        "trias_parallel_ratio": round(ratio, 3),
        "trias_dispatch_pattern": "serial" if ratio < SERIAL_RATIO_THRESHOLD else "parallel",
        "trias_num_turns": turns,
    }


def update_pipeline_audit(workspace: Path, verdict: dict) -> None:
    """Merge the verdict into pipeline_audit.json (preserves report_detected etc.)."""
    audit_path = workspace / "pipeline_audit.json"
    existing: dict = {}
    if audit_path.exists():
        try:
            existing = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
    existing.update(verdict)
    audit_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_trias_parallelism.py <workspace_dir>", file=sys.stderr)
        return 2
    workspace = Path(sys.argv[1])
    if not workspace.exists():
        print(f"workspace not found: {workspace}", file=sys.stderr)
        return 0
    verdict = check(workspace)
    if verdict is None:
        return 0
    update_pipeline_audit(workspace, verdict)
    print(json.dumps(verdict, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
