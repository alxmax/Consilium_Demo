"""Compute per-mode efficiency score: total_tokens / OK_outcomes.

Reads runs/*.json (telemetry) and FEEDBACK.html (outcomes via
.run_path_map.json sidecar), joins by run-path, emits tokens_per_OK per
mode — lower = better.

Design decisions (Senate 2026-05-17, efficiency-py-design-decisions):
  Q1: Binary gate — FEEDBACK outcome=OK -> OK, anything else -> not counted.
  Q2: total_tokens = tokens_in + tokens_out (raw sum, actual cost).
      Output includes tokens_per_dispatch (normalized) alongside raw metric.
  Q3: Flat Trias schema: voices {pioneer_generator, architect_control, ...}
      Same flat dict shape as sequential/parallel.
  Q4: --self-test flag (inline fixture) + --feedback / --runs CLI overrides.

Caveat: cross-mode OK is not qualitatively comparable. A Trias OK represents
deeper deliberation than a Sequential OK. This metric measures cost-per-success
at equal quality label — not absolute decision quality.

CLI:
    python scripts/efficiency.py --by-mode
    python scripts/efficiency.py --by-mode --since 2026-05-01
    python scripts/efficiency.py --compare trias sequential parallel
    python scripts/efficiency.py --json
    python scripts/efficiency.py --self-test
    python scripts/efficiency.py --feedback path/to/FEEDBACK.html
    python scripts/efficiency.py --runs path/to/runs
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from utils import FEEDBACK_PATH, RUNS_DIR


MIN_RUNS = 3  # modes with fewer runs marked insufficient_data
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


# ---------------------------------------------------------------------------
# Feedback parsing (import from feedback.py to avoid duplication)
# ---------------------------------------------------------------------------

def _load_feedback_mod():
    spec = importlib.util.spec_from_file_location("consilium_feedback", HERE / "feedback.py")
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_log_feedback_mod():
    spec = importlib.util.spec_from_file_location("consilium_log_feedback", HERE / "log_feedback.py")
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_outcome_map(feedback_path: Path, runs_dir: Path) -> dict[str, str]:
    """Return {run_path_str: outcome} for all FEEDBACK entries with a sidecar mapping.

    Uses .run_path_map.json (written by log_feedback.py) to join fingerprints
    to run file paths, then reads outcomes from FEEDBACK.html rows.
    """
    # Sidecar: fingerprint -> run_path
    map_path = runs_dir / ".run_path_map.json"
    if not map_path.exists():
        return {}
    try:
        fp_to_run: dict[str, str] = json.loads(map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    fb_mod = _load_feedback_mod()
    if fb_mod is None or not feedback_path.exists():
        return {}

    log_mod = _load_log_feedback_mod()
    if log_mod is None:
        return {}

    rows: list[dict] = fb_mod.parse_feedback(feedback_path)
    # Join FEEDBACK rows to run paths via the CANONICAL fingerprint. The sidecar
    # key encodes run_id (= run-file basename), so derive it from each stored
    # run_path and recompute the row's fingerprint with it (mirrors
    # audit_feedback._row_run_path). The old context[:30]/no-run_id local copy
    # produced a disjoint hash space, so this map was always empty.
    result: dict[str, str] = {}
    for fp, run_path in fp_to_run.items():
        run_id = Path(run_path).name if run_path else None
        for row in rows:
            if log_mod._fingerprint(row["date"], row["chosen"], row["context"], run_id=run_id) == fp:
                result[run_path] = row["outcome"]
                break
    return result


# ---------------------------------------------------------------------------
# Run walking
# ---------------------------------------------------------------------------

def walk_runs(runs_dir: Path, since: str | None) -> list[tuple[Path, dict]]:
    """Yield (path, data) for all runs/*.json."""
    results: list[tuple[Path, dict]] = []
    patterns = ["*.json"]
    for pattern in patterns:
        for f in sorted(runs_dir.glob(pattern)):
            if f.name.startswith("_"):
                continue
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            if since:
                ts = str(data.get("timestamp", "")) or f.stem[:10]
                if ts < since:
                    continue
            results.append((f, data))
    return results


# ---------------------------------------------------------------------------
# Token computation
# ---------------------------------------------------------------------------

def extract_tokens(telemetry: dict) -> tuple[int, int, int]:
    """Return (total_tokens, dispatches, total_latency_ms) from a telemetry block.

    total_tokens = sum(tokens_in + tokens_out) across all voices.
    Flat schema: works for sequential (generator/control/conservator),
    parallel, and trias (pioneer_generator/pioneer_control/... — flat,
    Q3 decision).
    """
    # Merge voices and personalities keys.
    # - voices: sequential/dialectic (generator, control, conservator)
    # - personalities: trias mode (pioneer, architect, steward) — Q3 decision 2026-05-25
    # Guard: only merge dict-shaped blocks. Some legacy runs stored
    # `personalities` as a list (e.g. ["pioneer","architect","steward"]) which
    # would crash dict.update; skip those rather than fail the whole rollup.
    all_voices: dict = {}
    for key in ("voices", "personalities"):
        block = telemetry.get(key)
        if isinstance(block, dict):
            all_voices.update(block)

    total_tokens = 0
    dispatches = 0
    total_latency = 0
    for vdata in all_voices.values():
        if not isinstance(vdata, dict):
            continue
        ti = vdata.get("tokens_in") or 0
        to_ = vdata.get("tokens_out") or 0
        lat = vdata.get("latency_ms") or 0
        if ti or to_:
            total_tokens += ti + to_
            dispatches += 1
        if lat:
            total_latency += lat
    return total_tokens, dispatches, total_latency


# ---------------------------------------------------------------------------
# Efficiency aggregation
# ---------------------------------------------------------------------------

def collect_efficiency(
    runs: list[tuple[Path, dict]],
    outcome_map: dict[str, str],
    mode_filter: list[str] | None,
) -> dict:
    by_mode: dict[str, dict] = {}

    for path, data in runs:
        telemetry = data.get("telemetry")
        if not isinstance(telemetry, dict):
            continue

        mode = telemetry.get("mode") or data.get("mode") or "unspecified"
        if mode_filter and mode not in mode_filter:
            continue

        total_tokens, dispatches, latency_ms = extract_tokens(telemetry)

        # Q1: look up outcome via run-path join (try relative then absolute)
        outcome = None
        for candidate in (
            str(path.relative_to(ROOT)) if path.is_absolute() else str(path),
            str(path),
            "runs/" + path.name,
        ):
            outcome = outcome_map.get(candidate)
            if outcome is not None:
                break

        bucket = by_mode.setdefault(mode, {
            "runs_with_telemetry": 0,
            "ok_count": 0,
            "not_ok_count": 0,
            "unlogged_count": 0,
            "total_tokens": 0,
            "dispatches": 0,
            "total_latency_ms": 0,
        })
        bucket["runs_with_telemetry"] += 1
        bucket["total_tokens"] += total_tokens
        bucket["dispatches"] += dispatches
        bucket["total_latency_ms"] += latency_ms

        # Q1: binary gate — OK -> counts, everything else -> excluded from numerator
        if outcome == "OK":
            bucket["ok_count"] += 1
        elif outcome in ("BAD", "OVR", "PEND"):
            bucket["not_ok_count"] += 1
        else:
            bucket["unlogged_count"] += 1

    modes_out: dict[str, dict] = {}
    for mode, b in sorted(by_mode.items()):
        n = b["runs_with_telemetry"]
        ok = b["ok_count"]
        tok = b["total_tokens"]
        disp = b["dispatches"]

        if n < MIN_RUNS:
            tpok = None
            tpd = None
            note = f"insufficient_data (need >={MIN_RUNS} runs with telemetry, have {n})"
        elif ok == 0:
            tpok = None
            tpd = None
            note = "no_ok_outcomes_yet"
        else:
            tpok = round(tok / ok)
            # Q2 per Socrate: also show per_dispatch (normalized cost per agent call)
            tpd = round(tok / disp) if disp else None
            note = None

        entry: dict = {
            "runs": n,
            "ok_count": ok,
            "not_ok_count": b["not_ok_count"],
            "unlogged_count": b["unlogged_count"],
            "total_tokens": tok,
            "tokens_per_ok": tpok,
            "tokens_per_dispatch": tpd,
            "avg_latency_ms_per_run": round(b["total_latency_ms"] / n) if n else None,
        }
        if note:
            entry["note"] = note
        modes_out[mode] = entry

    ranked = sorted(
        [(m, d["tokens_per_ok"]) for m, d in modes_out.items()
         if d.get("tokens_per_ok") is not None],
        key=lambda x: x[1],
    )

    return {
        "modes": modes_out,
        "ranking": [
            {"mode": m, "tokens_per_ok": tok, "rank": i + 1}
            for i, (m, tok) in enumerate(ranked)
        ],
        "caveat": (
            "cross-mode OK is not qualitatively comparable; "
            "a Trias OK represents deeper deliberation than a Sequential OK"
        ),
    }


# ---------------------------------------------------------------------------
# Self-test fixture (Q4)
# ---------------------------------------------------------------------------

_SELF_TEST_RUNS: list[tuple[str, dict]] = [
    ("runs/2000-01-01_0000_seq-a.json", {
        "telemetry": {"mode": "sequential", "voices": {
            "generator":   {"tokens_in": 1000, "tokens_out": 300, "latency_ms": 4000},
            "control":     {"tokens_in":  800, "tokens_out": 200, "latency_ms": 3000},
            "conservator": {"tokens_in":  700, "tokens_out": 180, "latency_ms": 2500},
        }},
    }),
    ("runs/2000-01-02_0000_seq-b.json", {
        "telemetry": {"mode": "sequential", "voices": {
            "generator":   {"tokens_in": 1100, "tokens_out": 320},
            "control":     {"tokens_in":  850, "tokens_out": 210},
            "conservator": {"tokens_in":  750, "tokens_out": 190},
        }},
    }),
    ("runs/2000-01-03_0000_seq-c.json", {
        "telemetry": {"mode": "sequential", "voices": {
            "generator":   {"tokens_in": 1200, "tokens_out": 350},
            "control":     {"tokens_in":  900, "tokens_out": 230},
            "conservator": {"tokens_in":  800, "tokens_out": 200},
        }},
    }),
]

# Precomputed outcome map for fixture: all runs have outcome=OK
_SELF_TEST_OUTCOME_MAP: dict[str, str] = {rp: "OK" for rp, _ in _SELF_TEST_RUNS}


def run_self_test() -> int:
    runs: list[tuple[Path, dict]] = [
        (Path(rp), data) for rp, data in _SELF_TEST_RUNS
    ]

    result = collect_efficiency(runs, _SELF_TEST_OUTCOME_MAP, None)

    modes = result["modes"]
    errors: list[str] = []

    # Sequential: 3 runs, all OK, tokens_per_ok must be non-null
    seq = modes.get("sequential", {})
    if seq.get("tokens_per_ok") is None:
        errors.append("sequential tokens_per_ok is null")
    if seq.get("runs") != 3:
        errors.append(f"sequential runs={seq.get('runs')}, expected 3")
    if seq.get("ok_count") != 3:
        errors.append(f"sequential ok_count={seq.get('ok_count')}, expected 3")

    # Expected sequential total_tokens: sum over 3 runs
    # run-a: (1000+300)+(800+200)+(700+180) = 1300+1000+880 = 3180
    # run-b: (1100+320)+(850+210)+(750+190) = 1420+1060+940 = 3420
    # run-c: (1200+350)+(900+230)+(800+200) = 1550+1130+1000 = 3680
    # total = 3180+3420+3680 = 10280
    expected_seq_tokens = 10280
    if seq.get("total_tokens") != expected_seq_tokens:
        errors.append(
            f"sequential total_tokens={seq.get('total_tokens')}, expected {expected_seq_tokens}"
        )

    # Ranking: sequential should rank #1 (only mode in the fixture)
    ranking = result.get("ranking", [])
    if not ranking or ranking[0]["mode"] != "sequential":
        errors.append(f"expected sequential to rank #1, got {ranking}")

    # tokens_per_dispatch must be non-null
    if seq.get("tokens_per_dispatch") is None:
        errors.append("sequential tokens_per_dispatch is null")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        return 1

    print("self-test PASS")
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--by-mode", action="store_true", help="emit per-mode breakdown (default)")
    ap.add_argument("--compare", nargs="+", metavar="MODE",
                    help="filter to specific modes, e.g. --compare trias sequential")
    ap.add_argument("--since", default=None, metavar="YYYY-MM-DD",
                    help="restrict to runs with timestamp >= this date")
    ap.add_argument("--json", action="store_true", help="emit raw JSON (default when piped)")
    ap.add_argument("--self-test", action="store_true",
                    help="run against inline fixture and exit; no filesystem reads")
    ap.add_argument("--feedback", default=None,
                    help="path to FEEDBACK.html (default: .consilium/FEEDBACK.html)")
    ap.add_argument("--runs", default=None,
                    help="path to runs/ dir (default: .consilium/runs)")
    args = ap.parse_args(argv)

    if args.self_test:
        return run_self_test()

    runs_dir = Path(args.runs) if args.runs else RUNS_DIR
    feedback_path = Path(args.feedback) if args.feedback else FEEDBACK_PATH

    if not runs_dir.is_dir():
        json.dump({"error": f"runs dir not found: {runs_dir}"}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1

    outcome_map = load_outcome_map(feedback_path, runs_dir)
    if not outcome_map:
        print(
            "warning: no outcome map found — FEEDBACK.html outcomes will not be joined. "
            "Run log_feedback.py with --run-path to build the sidecar map.",
            file=sys.stderr,
        )

    runs = walk_runs(runs_dir, args.since)
    mode_filter = args.compare or None

    result = collect_efficiency(runs, outcome_map, mode_filter)

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
