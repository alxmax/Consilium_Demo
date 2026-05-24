def normalize_scores(scores: list[float], clip_floor: float = 0.0) -> list[float]:
    """Min-max normalize scores into [0, 1], then raise any value below clip_floor to clip_floor.
    Guarantees (covered by the existing test suite):
    - empty input -> []
    - all-equal input -> all 0.0 (no division by zero)
    - clip_floor=0.0 (default) leaves existing behavior unchanged
    """
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    span = hi - lo
    if span == 0:
        return [0.0 for _ in scores]
    return [max((s - lo) / span, clip_floor) for s in scores]
