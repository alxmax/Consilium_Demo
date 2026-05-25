def weighted_average(values: list[float], weights: list[float], default: float = 0.0) -> float:
    """Compute weighted average of values using weights.

    Weights need not sum to 1 — they are applied as relative importance.

    Guarantees (covered by the existing test suite):
    - empty inputs -> default  (no crash; treated as all-zero weights)
    - all-zero weights -> default  (no division by zero)
    - length mismatch -> raises ValueError
    - basic: correct weighted sum / total weight

    Args:
        values: list of values to average.
        weights: list of relative importance weights, same length as values.
        default: value to return when all weights are zero (or inputs are empty).
                 Defaults to 0.0, preserving existing behavior.
    """
    if len(values) != len(weights):
        raise ValueError(
            f"values and weights must have the same length, "
            f"got {len(values)} and {len(weights)}"
        )
    total_w = sum(weights)
    if total_w == 0.0:
        return default
    return sum(v * w for v, w in zip(values, weights)) / total_w
