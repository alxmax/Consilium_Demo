"""Aggregate telemetry across runs/*.json into usage statistics.

Walks runs/*.json, reads each report's optional `telemetry` block, and
emits totals + per-voice/per-mode breakdowns. Reports without telemetry
are counted but excluded from cost stats.

Useful for proving scope_gate ROI (skipped runs cost ~0 voice tokens) or
checking whether dialectic mode justifies its 2x cost on real changes.

Telemetry shape expected on each report (validated by validate_report.py):
    {
      "telemetry": {
        "mode": "sequential" | "parallel" | "dialectic" | "ensemble",
        "passes": 1,
        "voices": {
          "generator":   {"tokens_in": 1200, "tokens_out": 400, "latency_ms": 3500},
          "control":     {"tokens_in":  800, "tokens_out": 200, "latency_ms": 2100},
          "conservator": {"tokens_in":  900, "tokens_out": 180, "latency_ms": 1800}
        }
      }
    }

Any field inside `voices` may be omitted (e.g. sequential mode often
can't isolate per-voice tokens; just record latency_ms or skip).

CLI:
    python scripts/usage.py
    python scripts/usage.py --runs path/to/dir
    python scripts/usage.py --last 50            # most-recent N runs only
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path


VOICES = ("generator", "control", "conservator")
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


def collect(reports: list[dict]) -> dict:
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
        with_telemetry += 1

        mode = telemetry.get("mode") or "unspecified"
        mode_bucket = by_mode.setdefault(
            mode,
            {"count": 0, "tokens_in": 0, "tokens_out": 0, "latency_ms": 0},
        )
        mode_bucket["count"] += 1

        voices = telemetry.get("voices") or {}
        for vname, vdata in voices.items():
            if vname not in by_voice or not isinstance(vdata, dict):
                continue
            for f in COUNT_FIELDS:
                if f in vdata and isinstance(vdata[f], int) and not isinstance(vdata[f], bool):
                    by_voice[vname][f].append(vdata[f])
                    if f in mode_bucket:
                        mode_bucket[f] += vdata[f]

    return {
        "runs_total": total,
        "with_telemetry": with_telemetry,
        "skipped_runs": skipped,
        "voices": {v: {f: _percentiles(samples) for f, samples in fields.items()} for v, fields in by_voice.items()},
        "modes": by_mode,
    }


def load_reports(runs_dir: Path, last: int | None) -> list[dict]:
    files = sorted(runs_dir.glob("*.json"))
    if last is not None:
        files = files[-last:]
    reports: list[dict] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"skip {path.name}: {exc}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            reports.append(data)
    return reports


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default=None, help="path to runs/ dir (default: ./runs)")
    ap.add_argument("--last", type=int, default=None, help="restrict to most-recent N runs")
    args = ap.parse_args(argv)

    runs_dir = Path(args.runs) if args.runs else Path.cwd() / "runs"
    if not runs_dir.is_dir():
        json.dump(
            {"error": f"runs dir not found: {runs_dir}"},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1

    reports = load_reports(runs_dir, args.last)
    result = collect(reports)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
