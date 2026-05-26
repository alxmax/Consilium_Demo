"""Aggregate telemetry across runs/*.json into usage statistics.

Walks runs/*.json, reads each report's optional `telemetry` block, and emits
totals + per-voice/per-mode breakdowns. Reports without telemetry are counted
but excluded from cost stats.

Useful for proving scope_gate ROI (skipped runs cost ~0 voice tokens) or
checking whether dialectic mode justifies its 2x cost on real changes.

Telemetry shape expected on each report:
    {
      "telemetry": {
        "mode": "sequential" | "parallel" | "dialectic" | "trias",
        "passes": 1,
        "voices": {
          "generator":   {"tokens_in": 1200, "tokens_out": 400, "latency_ms": 3500},
          "wittgenstein": {"tokens_in": 6000, "tokens_out": 1200, "latency_ms": 8000,
                          "source": "api_usage_field"}
        }
      }
    }

Any field inside `voices` may be omitted. Source field is informational
("api_usage_field" | "estimate_chars_div_4") — defaults to estimate when absent.

CLI:
    python scripts/usage.py
    python scripts/usage.py --runs path/to/dir   # custom dir
    python scripts/usage.py --last 50            # most-recent N runs only
    python scripts/usage.py --mode trias         # filter by telemetry.mode
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from utils import RUNS_DIR


CORE_VOICES = ("generator", "control", "conservator")
VOICES = CORE_VOICES
COUNT_FIELDS = ("tokens_in", "tokens_out", "latency_ms")


def _percentiles(values: list[int]) -> dict:
    if not values:
        return {"count": 0}
    out: dict = {
        "count": len(values),
        "sum": sum(values),
        "mean": round(statistics.fmean(values), 1),
        "p50": round(statistics.median(values), 1),
    }
    if len(values) >= 2:
        # quantiles requires n >= 2; method='inclusive' is the default in 3.8+
        try:
            qs = statistics.quantiles(values, n=20, method="inclusive")
            out["p95"] = round(qs[18], 1)  # 95th percentile = 19th of 20 cutpoints
        except statistics.StatisticsError:
            pass
    return out


def _new_voice_bucket() -> dict:
    return {f: [] for f in COUNT_FIELDS}


def collect(reports: list[dict], mode_filter: str | None = None) -> dict:
    total = len(reports)
    with_telemetry = 0
    skipped = 0

    by_voice: dict = {v: _new_voice_bucket() for v in VOICES}
    by_mode: dict = {}

    for report in reports:
        if report.get("skipped") is True:
            skipped += 1
        telemetry = report.get("telemetry")
        if not isinstance(telemetry, dict):
            continue

        # Prefer telemetry.mode, fall back to a top-level mode field if absent.
        mode = telemetry.get("mode") or report.get("mode") or "unspecified"

        if mode_filter is not None and mode != mode_filter:
            continue
        with_telemetry += 1

        mode_bucket = by_mode.setdefault(
            mode,
            {"count": 0, "tokens_in": 0, "tokens_out": 0, "latency_ms": 0},
        )
        mode_bucket["count"] += 1

        voices = telemetry.get("voices") or {}
        # Collect per-voice latencies separately so parallel modes use max, not sum.
        run_latencies: list[float] = []
        for vname, vdata in voices.items():
            if vname not in by_voice or not isinstance(vdata, dict):
                continue
            for f in COUNT_FIELDS:
                if f in vdata and isinstance(vdata[f], (int, float)) and not isinstance(vdata[f], bool):
                    by_voice[vname][f].append(vdata[f])
                    if f == "latency_ms":
                        run_latencies.append(vdata[f])
                    elif f in mode_bucket:
                        mode_bucket[f] += vdata[f]
        # For parallel/trias modes voices run concurrently; wall-clock = max latency.
        if run_latencies:
            if mode in ("parallel", "trias", "trias_split"):
                mode_bucket["latency_ms"] += max(run_latencies)
            else:
                mode_bucket["latency_ms"] += sum(run_latencies)

    return {
        "runs_total": total,
        "with_telemetry": with_telemetry,
        "skipped_runs": skipped,
        "voices": {v: {f: _percentiles(samples) for f, samples in fields.items()} for v, fields in by_voice.items()},
        "modes": by_mode,
    }


def _latency_warnings(files: list[Path], reports: list[dict]) -> list[dict]:
    warnings: list[dict] = []
    for path, report in zip(files, reports):
        telemetry = report.get("telemetry")
        if not isinstance(telemetry, dict) or telemetry.get("mode") != "parallel":
            continue
        voices = telemetry.get("voices") or {}
        latencies = {
            v: d["latency_ms"]
            for v, d in voices.items()
            if isinstance(d, dict) and isinstance(d.get("latency_ms"), (int, float)) and not isinstance(d.get("latency_ms"), bool)
        }
        if len(latencies) < 2:
            continue
        vnames = list(latencies.keys())
        for i, vname in enumerate(vnames):
            peers = [latencies[n] for j, n in enumerate(vnames) if j != i]
            peer_median = statistics.median(peers)
            if peer_median > 0 and latencies[vname] > 2 * peer_median:
                warnings.append({
                    "type": "latency_spike",
                    "run": path.name,
                    "voice": vname,
                    "latency_ms": latencies[vname],
                    "peer_median_ms": int(peer_median),
                })
    return warnings


def load_reports(runs_dir: Path, last: int | None) -> tuple[list[Path], list[dict]]:
    files = sorted(runs_dir.glob("*.json"))
    if last is not None:
        files = files[-last:]
    paths: list[Path] = []
    reports: list[dict] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"skip {path.name}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            paths.append(path)
            reports.append(data)
    return paths, reports


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=None, help="path to runs/ dir (default: .consilium/runs)")
    ap.add_argument("--last", type=int, default=None, help="restrict to most-recent N runs")
    ap.add_argument("--mode", default=None, help="filter by telemetry.mode (e.g. trias, sequential)")
    args = ap.parse_args(argv)

    runs_dir = Path(args.runs) if args.runs else RUNS_DIR
    if not runs_dir.is_dir():
        json.dump(
            {"error": f"runs dir not found: {runs_dir}"},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1

    files, reports = load_reports(runs_dir, args.last)
    result = collect(reports, mode_filter=args.mode)
    result["warnings"] = _latency_warnings(files, reports)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
