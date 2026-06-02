"""Voice-score calibration analysis and stability experiment tool.

Implements the experiment protocol from R2 audit 2026-05-17 (Bug #1:
voice_scores_uncalibrated_measurements). Two modes:

RETROSPECTIVE — analyse existing runs for score distribution and boundary cases:
    python scripts/stability_check.py --runs-dir runs/

COMPARE — compare two runs on the same input to measure pstdev per voice:
    python scripts/stability_check.py --compare runs/run_a.json runs/run_b.json

PICK — print candidate runs for the prospective experiment:
    python scripts/stability_check.py --pick 5

EXPERIMENT PROTOCOL (prospective, ~1 day effort):
    1. Pick candidates:  python scripts/stability_check.py --pick 5
    2. For each printed run, re-invoke /consilium with the SAME input, mode=sequential.
       Save outputs to runs/<date>_stability_a.json and runs/<date>_stability_b.json.
    3. Compare each pair:
       python scripts/stability_check.py --compare stability_a.json stability_b.json
    4. Collect pstdev values across 5 pairs. If mean pstdev(risk_score) > 0.10,
       Bug #1 is empirically confirmed.
"""
# implements: CONSILIUM-STABILITY-CHECK-001
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

try:
    from utils import RUNS_DIR, force_utf8_streams
    force_utf8_streams()
    _DEFAULT_RUNS = str(RUNS_DIR)
except ImportError:
    _DEFAULT_RUNS = "runs"

DEFAULT_VETO = 0.8
UNCERTAINTY_BAND = 0.15
STABILITY_THRESHOLD = 0.10


def _load_run(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _voice_scores(run: dict) -> dict[str, float] | None:
    vs = run.get("voice_scores")
    if not isinstance(vs, dict):
        return None
    out = {}
    for voice in ("generator", "control", "conservator"):
        v = vs.get(voice)
        if isinstance(v, (int, float)):
            out[voice] = float(v)
    return out if out else None


def retrospective(runs_dir: str) -> None:
    files = sorted(Path(runs_dir).glob("*.json"))
    records: list[tuple[str, dict[str, float]]] = []
    for f in files:
        try:
            run = _load_run(f)
            vs = _voice_scores(run)
            if vs:
                records.append((f.name, vs))
        except Exception:
            pass

    if not records:
        print("No runs with voice_scores found.", file=sys.stderr)
        return

    voices = ("generator", "control", "conservator")
    print(f"=== Retrospective calibration report — {len(records)} runs ===\n")

    for voice in voices:
        vals = [vs[voice] for _, vs in records if voice in vs]
        if not vals:
            continue
        mean = statistics.mean(vals)
        pstdev = statistics.pstdev(vals)
        q = sorted(vals)
        p25 = q[len(q) // 4]
        p75 = q[3 * len(q) // 4]
        print(f"{voice:12s}: n={len(vals):3d}  mean={mean:.3f}  pstdev={pstdev:.3f}"
              f"  min={min(vals):.3f}  p25={p25:.3f}  p75={p75:.3f}  max={max(vals):.3f}")

    print()
    print(f"--- Veto boundary analysis (conservator, band=[{DEFAULT_VETO - UNCERTAINTY_BAND:.2f}, "
          f"{DEFAULT_VETO + UNCERTAINTY_BAND:.2f}]) ---")
    boundary = [(name, vs["conservator"]) for name, vs in records
                if "conservator" in vs
                and abs(vs["conservator"] - DEFAULT_VETO) <= UNCERTAINTY_BAND]
    above_veto = [(name, vs["conservator"]) for name, vs in records
                  if "conservator" in vs and vs["conservator"] > DEFAULT_VETO]
    print(f"Runs with conservator > {DEFAULT_VETO} (would veto): {len(above_veto)}")
    print(f"Runs in uncertain band ±{UNCERTAINTY_BAND}: {len(boundary)}")
    if boundary:
        for name, score in boundary:
            flag = "VETO" if score > DEFAULT_VETO else "near"
            print(f"  [{flag}] {name}: {score:.3f}")

    print()
    print("--- Calibration note ---")
    print("CROSS-INPUT pstdev (above) mixes true-risk variance with model variance.")
    print("To isolate model variance, run the prospective experiment:")
    print("  python scripts/stability_check.py --pick 5")
    print("  (re-run each selected input twice, then --compare each pair)")


def _categorical_fields(run: dict) -> dict | None:
    """Extract conservator magnitude/reversibility from either log schema.

    Handles flat schema {step:conservator, reversibility:..., magnitude:...} and
    nested schema {step:conservator, scores:[{id, regression_risk:{reversibility, magnitude}}]}.
    For nested, picks the chosen_approach candidate's score; falls back to first score.
    Returns None when conservator step or categorical fields are absent.
    """
    log = run.get("deliberation_log")
    if not isinstance(log, list):
        return None

    conservator_entry = None
    for entry in log:
        if isinstance(entry, dict) and entry.get("step") == "conservator":
            conservator_entry = entry
            break

    if conservator_entry is None:
        return None

    # Flat schema
    if "reversibility" in conservator_entry or "magnitude" in conservator_entry:
        rev = conservator_entry.get("reversibility")
        mag = conservator_entry.get("magnitude")
        if rev is not None or mag is not None:
            return {"reversibility": rev, "magnitude": mag}

    # Nested schema
    scores = conservator_entry.get("scores")
    if isinstance(scores, list) and scores:
        chosen = run.get("chosen_approach")
        score_entry = None
        if chosen:
            for s in scores:
                if isinstance(s, dict) and s.get("id") == chosen:
                    score_entry = s
                    break
        if score_entry is None:
            score_entry = scores[0]  # fallback to first candidate
        rr = score_entry.get("regression_risk", {}) if isinstance(score_entry, dict) else {}
        rev = rr.get("reversibility")
        mag = rr.get("magnitude")
        source_id = score_entry.get("id") if isinstance(score_entry, dict) else None
        if rev is not None or mag is not None:
            return {"reversibility": rev, "magnitude": mag, "source_id": source_id}

    return None


def compare(path_a: str, path_b: str) -> None:
    run_a = _load_run(path_a)
    run_b = _load_run(path_b)
    vs_a = _voice_scores(run_a)
    vs_b = _voice_scores(run_b)

    if not vs_a or not vs_b:
        print("ERROR: one or both runs lack voice_scores", file=sys.stderr)
        sys.exit(1)

    print(f"=== Stability comparison ===")
    print(f"  A: {path_a}")
    print(f"  B: {path_b}\n")

    voices = ("generator", "control", "conservator")
    pstdevs: list[float] = []
    for voice in voices:
        a = vs_a.get(voice)
        b = vs_b.get(voice)
        if a is None or b is None:
            print(f"  {voice:12s}: MISSING in one run")
            continue
        diff = abs(a - b)
        pstdev = statistics.pstdev([a, b])
        pstdevs.append(pstdev)
        flag = " *** HIGH VARIANCE" if pstdev > STABILITY_THRESHOLD else ""
        print(f"  {voice:12s}: A={a:.3f}  B={b:.3f}  diff={diff:.3f}  pstdev={pstdev:.3f}{flag}")

    if pstdevs:
        mean_pstdev = statistics.mean(pstdevs)
        verdict = "CONFIRMED (> 0.10)" if mean_pstdev > STABILITY_THRESHOLD else "OK (≤ 0.10)"
        print(f"\n  mean pstdev across voices: {mean_pstdev:.3f} → Bug #1 {verdict}")

    # Categorical stability
    cat_a = _categorical_fields(run_a)
    cat_b = _categorical_fields(run_b)
    print("\n--- Categorical stability ---")
    if cat_a is None and cat_b is None:
        print("  MISSING — categorical fields not found in either run")
    elif cat_a is None:
        print("  MISSING — categorical fields not found in run A")
    elif cat_b is None:
        print("  MISSING — categorical fields not found in run B")
    else:
        for field in ("magnitude", "reversibility"):
            a_val = cat_a.get(field)
            b_val = cat_b.get(field)
            if a_val is None and b_val is None:
                print(f"  {field:14s}: MISSING in both runs")
            elif a_val is None:
                print(f"  {field:14s}: MISSING in run A  B={b_val}")
            elif b_val is None:
                print(f"  {field:14s}: A={a_val}  MISSING in run B")
            else:
                match = "OK" if a_val == b_val else "*** FLIP"
                print(f"  {field:14s}: A={a_val}  B={b_val}  {match}")
        if cat_a.get("source_id"):
            print(f"  (A: scores from candidate '{cat_a['source_id']}')")
        if cat_b.get("source_id"):
            print(f"  (B: scores from candidate '{cat_b['source_id']}')")


def pick_candidates(runs_dir: str, n: int) -> None:
    files = sorted(Path(runs_dir).glob("*.json"))
    candidates = []
    for f in files:
        try:
            run = _load_run(f)
            vs = _voice_scores(run)
            sc = run.get("success_criterion", "")
            if vs and sc:
                candidates.append((f.name, vs.get("conservator", 0.0), sc[:80]))
        except Exception:
            pass

    candidates.sort(key=lambda t: abs(t[1] - DEFAULT_VETO))
    print(f"Top {n} candidates for stability experiment (sorted by proximity to veto boundary):\n")
    for name, cons_score, sc in candidates[:n]:
        print(f"  {name}  conservator={cons_score:.3f}")
        print(f"    criterion: {sc}")
        print()
    print("Instructions: re-run each with /consilium using the same input + mode=sequential.")
    print("Save outputs as runs/<date>_stability_a.json and runs/<date>_stability_b.json.")
    print("Then: python scripts/stability_check.py --compare a.json b.json")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runs-dir", default=_DEFAULT_RUNS, help="Directory with run JSON files")
    p.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
                   help="Compare two runs on the same input")
    p.add_argument("--pick", type=int, metavar="N",
                   help="Pick N candidate runs for the prospective experiment")
    args = p.parse_args()

    if args.compare:
        compare(args.compare[0], args.compare[1])
    elif args.pick:
        pick_candidates(args.runs_dir, args.pick)
    else:
        retrospective(args.runs_dir)


if __name__ == "__main__":
    main()
