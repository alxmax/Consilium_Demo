#!/usr/bin/env python3
"""Efficiency audit — accuracy + score comparison across benchmark modes.

Reads existing workspace/<mode>/<task>/rep_N/ data and oracle answers from
the sibling Benchmark-scoring/ repo. Reports per-mode accuracy (correct/n),
mean LLM-judge score, pipeline execution rate, and bootstrap 95% CI.

POWER NOTE: n_eff = number of distinct tasks with an oracle answer (currently
4 reasoning tasks). Bootstrap CIs are computed by resampling over tasks, so
the effective sample size is 4 — not total reps. With n=4 all pairwise
differences are statistically inconclusive (p >= 0.25 by construction for a
one-sided Fisher test). Results are DIRECTIONAL ONLY.

CLI:
    python benchmark/scripts/efficiency_audit.py
    python benchmark/scripts/efficiency_audit.py --json
    python benchmark/scripts/efficiency_audit.py --scoring-dir path/to/Benchmark-scoring
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path
from statistics import mean

BENCHMARK_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BENCHMARK_ROOT / "scripts"))
from _common import MODES, TASKS  # noqa: E402

DEFAULT_SCORING = Path(
    os.environ.get("BENCHMARK_SCORING_DIR")
    or BENCHMARK_ROOT.parent.parent / "Benchmark-scoring"
)
WORKSPACE = BENCHMARK_ROOT / "workspace"
BOOTSTRAP_N = 1000
BOOTSTRAP_SEED = 42


def _load_oracle(scoring_dir: Path) -> dict[str, str]:
    """Return {task_key: expected_letter} for tasks that have an oracle."""
    oracles: dict[str, str] = {}
    for task in TASKS:
        cat, name = task.split("/", 1)
        p = scoring_dir / cat / name / "expected_answer.txt"
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                oracles[task] = line.upper()
                break
    return oracles


def _load_rep(rep_dir: Path) -> dict:
    ans_file = rep_dir / "answer.md"
    vr_file = rep_dir / "verify" / "report.json"
    pa_file = rep_dir / "pipeline_audit.json"

    letter: str | None = None
    if ans_file.exists():
        for line in ans_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                letter = line.removeprefix("ANSWER:").strip().upper()[:1] or None
                break

    score: float | None = None
    max_score: float | None = None
    if vr_file.exists():
        try:
            vr = json.loads(vr_file.read_text(encoding="utf-8"))
            score = vr.get("score")
            max_score = vr.get("max_score")
        except (json.JSONDecodeError, OSError):
            pass

    pipeline: bool | None = None
    if pa_file.exists():
        try:
            pa = json.loads(pa_file.read_text(encoding="utf-8"))
            pipeline = pa.get("pipeline_executed")
        except (json.JSONDecodeError, OSError):
            pass

    return {"letter": letter, "score": score, "max_score": max_score, "pipeline": pipeline}


def _collect_reps(mode: str, task: str) -> list[dict]:
    base = WORKSPACE / mode / task
    reps = []
    if (base / "answer.md").exists():
        reps.append(_load_rep(base))
    if base.is_dir():
        for sub in sorted(base.iterdir()):
            if sub.is_dir() and sub.name.startswith("rep_") and any(sub.iterdir()):
                reps.append(_load_rep(sub))
    return reps


def _bootstrap_ci(values: list[float], n: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED) -> tuple[float, float]:
    """95% percentile bootstrap CI for mean, resampling over the values list."""
    if not values:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    means = [mean(rng.choices(values, k=len(values))) for _ in range(n)]
    means.sort()
    lo = means[int(0.025 * n)]
    hi = means[int(0.975 * n)]
    return (lo, hi)


def run_audit(scoring_dir: Path) -> dict:
    oracles = _load_oracle(scoring_dir)
    scored_tasks = sorted(oracles)
    n_tasks = len(scored_tasks)

    results: dict[str, dict] = {}
    for mode in MODES:
        acc_vec: list[float] = []   # 1=correct, 0=wrong, per task (oracle tasks only)
        score_vec: list[float] = []  # normalised 0-1, per task (all tasks with score)
        pipe_yes = pipe_no = pipe_unknown = 0

        for task in TASKS:
            reps = _collect_reps(mode, task)
            if not reps:
                continue
            rep = reps[0]  # use rep_1 / first available

            # accuracy
            if task in oracles and rep["letter"] is not None:
                acc_vec.append(1.0 if rep["letter"] == oracles[task] else 0.0)

            # score (normalised)
            if rep["score"] is not None and rep["max_score"]:
                score_vec.append(rep["score"] / rep["max_score"])

            # pipeline (oracle tasks only — keeps denominator consistent with accuracy)
            if task in oracles:
                if rep["pipeline"] is True:
                    pipe_yes += 1
                elif rep["pipeline"] is False:
                    pipe_no += 1
                else:
                    pipe_unknown += 1

        acc = mean(acc_vec) if acc_vec else None
        acc_ci = _bootstrap_ci(acc_vec) if acc_vec else None
        score_m = mean(score_vec) if score_vec else None
        score_ci = _bootstrap_ci(score_vec) if score_vec else None
        pipe_total = pipe_yes + pipe_no
        pipe_rate = pipe_yes / pipe_total if pipe_total else None

        results[mode] = {
            "accuracy": round(acc, 3) if acc is not None else None,
            "accuracy_ci_95": [round(acc_ci[0], 3), round(acc_ci[1], 3)] if acc_ci else None,
            "correct_k": sum(int(v) for v in acc_vec),
            "n_oracle_tasks": len(acc_vec),
            "mean_score": round(score_m, 3) if score_m is not None else None,
            "score_ci_95": [round(score_ci[0], 3), round(score_ci[1], 3)] if score_ci else None,
            "pipeline_rate": round(pipe_rate, 3) if pipe_rate is not None else None,
            "pipeline_yes": pipe_yes,
            "pipeline_no": pipe_no,
        }

    power_note = (
        f"n_eff={n_tasks} distinct tasks. Bootstrap CIs resample over tasks, not reps. "
        f"With n={n_tasks} all pairwise differences are inconclusive (p>=0.25). "
        "Results are DIRECTIONAL ONLY — do not infer significance."
    )
    warnings = [
        power_note,
        "pipeline_executed flag is post-hoc inferred from claude_raw.json, not live instrumentation — treat as indicative, not authoritative.",
        "pipeline denominator is now scoped to oracle-scored reasoning tasks only (same population as accuracy denominator); code tasks excluded from pipeline count.",
    ]
    return {
        "n_eff": n_tasks,
        "oracle_tasks": scored_tasks,
        "modes": results,
        "power_note": power_note,
        "warnings": warnings,
    }


def _print_table(audit: dict) -> None:
    modes = audit["modes"]
    print(f"\nEfficiency audit  (n_eff={audit['n_eff']} oracle tasks, bootstrap seed=42)")
    print(f"{'Mode':30s}  {'Acc':>5}  {'95% CI':>13}  {'Score':>6}  {'Score CI':>13}  {'Pipeline':>8}")
    print("-" * 90)
    for mode, m in modes.items():
        acc = f"{m['accuracy']:.0%}" if m["accuracy"] is not None else "—"
        ci = (f"[{m['accuracy_ci_95'][0]:.0%},{m['accuracy_ci_95'][1]:.0%}]"
              if m["accuracy_ci_95"] else "—")
        sc = f"{m['mean_score']:.2f}" if m["mean_score"] is not None else "—"
        sci = (f"[{m['score_ci_95'][0]:.2f},{m['score_ci_95'][1]:.2f}]"
               if m["score_ci_95"] else "—")
        pipe = (f"{m['pipeline_yes']}/{m['pipeline_yes']+m['pipeline_no']}"
                if m["pipeline_rate"] is not None else "n/a")
        print(f"{mode:30s}  {acc:>5}  {ci:>13}  {sc:>6}  {sci:>13}  {pipe:>8}")
    print()
    print(f"! {audit['power_note']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON only")
    ap.add_argument("--scoring-dir", default=None, help="path to Benchmark-scoring repo")
    args = ap.parse_args(argv)

    scoring_dir = Path(args.scoring_dir) if args.scoring_dir else DEFAULT_SCORING
    if not scoring_dir.is_dir():
        print(f"scoring dir not found: {scoring_dir}", file=sys.stderr)
        return 2

    audit = run_audit(scoring_dir)

    if args.json:
        json.dump(audit, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    _print_table(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
