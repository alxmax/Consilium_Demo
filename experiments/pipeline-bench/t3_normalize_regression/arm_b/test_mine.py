from solution import normalize_scores

# --- Existing guarantees (must not regress) ---

def test_empty():
    assert normalize_scores([]) == []

def test_all_equal_no_crash():
    assert normalize_scores([5, 5, 5]) == [0.0, 0.0, 0.0]

def test_basic_scaling():
    assert normalize_scores([0, 5, 10]) == [0.0, 0.5, 1.0]

# --- Existing guarantees still hold with explicit clip_floor=0.0 ---

def test_empty_with_default_clip():
    assert normalize_scores([], clip_floor=0.0) == []

def test_all_equal_no_crash_with_default_clip():
    assert normalize_scores([5, 5, 5], clip_floor=0.0) == [0.0, 0.0, 0.0]

def test_basic_scaling_with_default_clip():
    assert normalize_scores([0, 5, 10], clip_floor=0.0) == [0.0, 0.5, 1.0]

# --- New behavior: clip_floor raises values below the threshold ---

def test_clip_floor_raises_low_values():
    # [0, 5, 10] normalizes to [0.0, 0.5, 1.0]; with clip_floor=0.3, 0.0 -> 0.3
    result = normalize_scores([0, 5, 10], clip_floor=0.3)
    assert result == [0.3, 0.5, 1.0]

def test_clip_floor_does_not_lower_values_above_it():
    # 0.5 and 1.0 are already above 0.3, must remain unchanged
    result = normalize_scores([0, 5, 10], clip_floor=0.3)
    assert result[1] == 0.5
    assert result[2] == 1.0

def test_clip_floor_all_equal_still_no_crash():
    # all-equal -> all 0.0 before clip; with clip_floor=0.5, all become 0.5
    result = normalize_scores([7, 7, 7], clip_floor=0.5)
    assert result == [0.5, 0.5, 0.5]

def test_clip_floor_zero_is_identity():
    # clip_floor=0.0 must produce same result as no clip_floor
    scores = [1.0, 3.0, 2.0, 5.0]
    assert normalize_scores(scores, clip_floor=0.0) == normalize_scores(scores)

def test_clip_floor_one_clips_all_to_one():
    # clip_floor=1.0: every value raised to 1.0
    result = normalize_scores([0, 5, 10], clip_floor=1.0)
    assert result == [1.0, 1.0, 1.0]

def test_clip_floor_mid_range():
    # [0, 2, 4, 6, 8, 10] -> [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    # clip_floor=0.5: values 0.0, 0.2, 0.4 raised to 0.5
    result = normalize_scores([0, 2, 4, 6, 8, 10], clip_floor=0.5)
    assert result == [0.5, 0.5, 0.5, 0.6, 0.8, 1.0]

def test_clip_floor_negative_behaves_like_zero():
    # negative clip_floor: no value is below a negative threshold after [0,1] normalization
    result = normalize_scores([0, 5, 10], clip_floor=-0.5)
    assert result == [0.0, 0.5, 1.0]

def test_clip_floor_empty_still_empty():
    assert normalize_scores([], clip_floor=0.5) == []
