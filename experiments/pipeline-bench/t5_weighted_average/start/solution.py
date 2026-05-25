def weighted_average(values: list[float], weights: list[float]) -> float:
    """Compute weighted average of values using weights.

    Weights need not sum to 1 — they are applied as relative importance.

    Guarantees (covered by the existing test suite):
    - empty inputs -> 0.0  (no crash; treated as all-zero weights)
    - all-zero weights -> 0.0  (no division by zero)
    - length mismatch -> raises ValueError
    - basic: correct weighted sum / total weight
    """
    if len(values) != len(weights):
        raise ValueError(
            f"values and weights must have the same length, "
            f"got {len(values)} and {len(weights)}"
        )
    total_w = sum(weights)
    if total_w == 0.0:
        return 0.0
    return sum(v * w for v, w in zip(values, weights)) / total_w
