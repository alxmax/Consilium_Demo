def normalize_weights(weights: list[float]) -> list[float]:
    """Scale weights so they sum to 1.0.

    Guarantees (covered by the existing test suite):
    - empty input -> []
    - all-zero weights -> equal weights (1/n each), no division by zero
    - basic: positive weights are scaled proportionally
    """
    if not weights:
        return []
    total = sum(weights)
    if total == 0.0:
        return [1.0 / len(weights)] * len(weights)
    return [w / total for w in weights]
