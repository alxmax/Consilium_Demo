def normalize_scores(scores: list[float]) -> list[float]:
    """Min-max normalize scores into [0, 1].

    Guarantees (covered by the existing test suite):
    - empty input -> []
    - all-equal input -> all 0.0 (no division by zero)
    """
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    span = hi - lo
    if span == 0:
        return [0.0 for _ in scores]
    return [(s - lo) / span for s in scores]
