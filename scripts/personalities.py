"""Sample personalities for ensemble deliberation.

Each personality is a weight vector (w_G, w_C, w_K) over three voices:
- G = Generator (creative)
- C = Control (analytic)
- K = Conservator (skeptic)

Constraints: each w in [0.2, 0.49], sum = 1.0. Rejection sampling ensures
no single voice dominates and none is silenced.

CLI:
    python personalities.py N    # emit N personalities as JSON array
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from typing import List, Tuple

WMIN = 0.2
WMAX = 0.49
TOL = 1e-6
MAX_TRIES = 10_000

Weights = Tuple[float, float, float]


def sample_personality(rng: random.Random | None = None) -> Weights:
    """Rejection-sample a weight triple (G, C, K) with each w in [0.2, 0.49],
    summing to 1.0.

    Strategy: sample two weights uniformly in [WMIN, WMAX], derive the third,
    accept iff the third also lies in [WMIN, WMAX].
    """
    r = rng or random
    for _ in range(MAX_TRIES):
        w_g = r.uniform(WMIN, WMAX)
        w_c = r.uniform(WMIN, WMAX)
        w_k = 1.0 - w_g - w_c
        if WMIN - TOL <= w_k <= WMAX + TOL:
            return (round(w_g, 4), round(w_c, 4), round(w_k, 4))
    raise RuntimeError("rejection sampling failed; check bounds")


def sample_ensemble(n: int, seed: int | None = None) -> List[Weights]:
    """Sample N independent personalities."""
    if n < 1:
        raise ValueError("n must be >= 1")
    rng = random.Random(seed)
    return [sample_personality(rng) for _ in range(n)]


def _to_dict(w: Weights) -> dict:
    return {"generator": w[0], "control": w[1], "conservator": w[2]}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("n", type=int, help="number of personalities to sample")
    ap.add_argument("--seed", type=int, default=None, help="rng seed")
    args = ap.parse_args(argv)

    ensemble = sample_ensemble(args.n, seed=args.seed)
    json.dump([_to_dict(w) for w in ensemble], sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
