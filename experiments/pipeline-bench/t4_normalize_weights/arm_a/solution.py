def normalize_weights(weights: list[float], scale: float = 1.0) -> list[float]:
    """Scale weights so they sum to `scale`.

    Guarantees (covered by the existing test suite):
    - empty input -> []
    - all-zero weights -> equal weights (scale/n each), no division by zero
    - basic: positive weights are scaled proportionally
    """
    if not weights:
        return []
    total = sum(weights)
    if total == 0.0:
        return [scale / len(weights)] * len(weights)
    return [w / total * scale for w in weights]
