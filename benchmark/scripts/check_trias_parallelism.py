"""Check whether a consilium_trias run dispatched the 3 personalities in parallel.

Reads Claude CLI's session JSONL transcript (~/.claude/projects/<encoded_cwd>/<session_id>.jsonl)
and counts how many Agent tool_use blocks each assistant message contained.

- modes/trias.md Step 3 mandates: "Dispatch all 3 personalities in parallel (3 consilium-subagent
  Agent calls in the same orchestrator message)". A parallel dispatch produces ONE assistant
  message with N>=2 Agent tool_use blocks. Serial dispatch produces N consecutive messages
  each with 1 Agent block.

Writes the verdict to pipeline_audit.json:
  trias_serial_dispatch: bool   — True if all dispatches were 1-per-message (or scale_down)
  trias_max_agents_in_message: int  — max parallel agents observed; 1 = serial, >=2 = some parallel
  trias_total_dispatches: int   — total Agent calls observed
  trias_dispatch_pattern: "serial" | "parallel" | "mixed" | "scale_down"

Sources of truth:
  - claude_raw.json (workspace) → session_id
  - cwd of the subprocess (= workspace path) → encoded_cwd for the projects/ dir
  - <encoded_cwd>/<session_id>.jsonl → per-message tool_use blocks with timestamps

CLI:
    python check_trias_parallelism.py <workspace_dir>

Exits 0 always (advisory). JSONL absence → no verdict written (graceful fallback).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

SCALE_DOWN_MAX_TURNS = 4


def _encode_cwd(cwd: Path) -> str:
    """Replicate Claude CLI's project-dir encoding.

    Observed: 'C:\\Users\\<user>\\…\\Consilium\\benchmark\\workspace\\consilium_trias\\code\\01_circuit_breaker'
       maps to: 'C--Users-<user>-…-Consilium-benchmark-workspace-consilium-trias-code-01-circuit-breaker'

    Rule (empirical): backslash, colon, and underscore all collapse to '-'.
    """
    s = str(cwd.resolve())
    s = s.replace(":", "-").replace("\\", "-").replace("/", "-").replace("_", "-")
    s = re.sub(r"-+", "-", s)
    return s


def _find_jsonl(workspace: Path, session_id: str) -> Path | None:
    """Locate the session JSONL in ~/.claude/projects/<encoded>/<session_id>.jsonl."""
    home = Path(os.path.expanduser("~"))
    proj_root = home / ".claude" / "projects"
    if not proj_root.exists():
        return None
    encoded = _encode_cwd(workspace)
    candidate = proj_root / encoded / f"{session_id}.jsonl"
    if candidate.exists():
        return candidate
    # Fallback: glob — encoding may differ on legacy runs.
    matches = list(proj_root.glob(f"*/{session_id}.jsonl"))
    return matches[0] if matches else None


def _count_agents_per_message(jsonl: Path) -> list[int]:
    """Return [N1, N2, ...] = Agent tool_use count for each assistant message that contained any."""
    counts: list[int] = []
    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "assistant":
                continue
            content = ev.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            n = sum(
                1
                for b in content
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Agent"
            )
            if n > 0:
                counts.append(n)
    return counts


def check(workspace: Path) -> dict | None:
    """Compute the parallelism verdict from JSONL transcript. Returns None if data unavailable."""
    raw = workspace / "claude_raw.json"
    if not raw.exists():
        # Try rep_*/
        rep_raws = sorted(
            (p / "claude_raw.json" for p in workspace.iterdir() if p.is_dir() and p.name.startswith("rep_")),
            key=lambda p: p.parent.name,
        )
        rep_raws = [r for r in rep_raws if r.exists()]
        if not rep_raws:
            return None
        raw = rep_raws[-1]

    try:
        data = json.loads(raw.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    turns = data.get("num_turns") or 0
    session_id = data.get("session_id")
    if not session_id:
        return None

    if turns <= SCALE_DOWN_MAX_TURNS:
        return {
            "trias_serial_dispatch": False,
            "trias_max_agents_in_message": 0,
            "trias_total_dispatches": 0,
            "trias_dispatch_pattern": "scale_down",
            "trias_num_turns": turns,
        }

    # Locate JSONL relative to the workspace cwd.
    jsonl = _find_jsonl(raw.parent, session_id)
    if jsonl is None:
        return None

    counts = _count_agents_per_message(jsonl)
    if not counts:
        return {
            "trias_serial_dispatch": False,
            "trias_max_agents_in_message": 0,
            "trias_total_dispatches": 0,
            "trias_dispatch_pattern": "no_dispatch_observed",
            "trias_num_turns": turns,
        }

    max_in_msg = max(counts)
    total = sum(counts)
    if max_in_msg >= 2 and min(counts) >= 2:
        pattern = "parallel"
        serial = False
    elif max_in_msg >= 2:
        pattern = "mixed"
        serial = False
    else:
        pattern = "serial"
        serial = True

    return {
        "trias_serial_dispatch": serial,
        "trias_max_agents_in_message": max_in_msg,
        "trias_total_dispatches": total,
        "trias_dispatch_pattern": pattern,
        "trias_num_turns": turns,
    }


def update_pipeline_audit(workspace: Path, verdict: dict) -> None:
    """Merge verdict into pipeline_audit.json (preserves other fields like report_detected)."""
    audit_path = workspace / "pipeline_audit.json"
    existing: dict = {}
    if audit_path.exists():
        try:
            existing = json.loads(audit_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            existing = {}
    # Remove old api/wall-ratio fields if present (superseded by JSONL-based audit).
    for old_field in ("trias_parallel_ratio",):
        existing.pop(old_field, None)
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
