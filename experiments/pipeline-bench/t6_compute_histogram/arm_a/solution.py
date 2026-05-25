def compute_histogram(data: list[float], bins: int, normalize: bool = False) -> list[int] | list[float]:
    """Count values falling in each of `bins` equal-width bins spanning [min, max].

    Bin i covers [min + i*width, min + (i+1)*width), except the last bin which is
    closed on the right: [min + (bins-1)*width, max].

    Guarantees (covered by the existing test suite):
    - empty data -> [0] * bins  (no crash)
    - all-equal data -> all counts in bin 0, rest zero (no division by zero)
    - basic: values distributed across bins correctly
    - bins=1 -> [len(data)] always

    When normalize=True, each count is divided by len(data) so the result sums to 1.0.
    Empty data with normalize=True returns [0.0] * bins.
    """
    if not data:
        return [0.0] * bins if normalize else [0] * bins
    lo, hi = min(data), max(data)
    span = hi - lo
    counts = [0] * bins
    if span == 0.0:
        counts[0] = len(data)
        if normalize:
            return [1.0] + [0.0] * (bins - 1)
        return counts
    for x in data:
        idx = int((x - lo) / span * bins)
        idx = min(idx, bins - 1)
        counts[idx] += 1
    if normalize:
        total = len(data)
        return [c / total for c in counts]
    return counts
