"""Tests for USA IRC baseline MVP validator."""

from app.compliance.extraction_fallback import merge_heuristic_layout
from app.compliance.models import DoorExtract, LayoutExtract, RoomExtract, StairsExtract
from app.compliance.validator import parse_layout_from_llm_dict, validate_us_irc_baseline


def test_passing_bedroom_and_door():
    layout = LayoutExtract(
        rooms=[RoomExtract(name="Bedroom", area_sqft=120, ceiling_ft=8)],
        doors_inches=[DoorExtract(width_in=36)],
        stairs=None,
        egress_windows_sqft=[],
    )
    r = validate_us_irc_baseline(layout, raw_for_response=False)
    assert r.score_percent == 100.0
    assert r.status_label == "good"
    # Bedroom area + ceiling height + door width => 3 applicable checks.
    assert r.applicable_rules == 3
    assert len(r.violations) == 0


def test_small_bedroom_fails():
    layout = LayoutExtract(
        rooms=[RoomExtract(name="Primary bedroom", area_sqft=50, ceiling_ft=8)],
        doors_inches=[],
        stairs=None,
        egress_windows_sqft=[],
    )
    r = validate_us_irc_baseline(layout, raw_for_response=False)
    assert r.violations
    assert any(v.rule_id == "bedroom_min_area" for v in r.violations)
    assert r.score_percent is not None and r.score_percent < 100


def test_insufficient_data():
    layout = LayoutExtract(rooms=[], doors_inches=[], stairs=None, egress_windows_sqft=[])
    r = validate_us_irc_baseline(layout, raw_for_response=False)
    assert r.status_label == "insufficient_data"
    assert r.score_percent is None


def test_heuristic_merge_fills_sparse_llm():
    llm_empty = {}
    user = "Bedroom 14 ft by 12 ft, ceiling 8 ft, one door 36 inch, egress opening about 6 sq ft"
    cad = """BEDROOM 14'-0\" x 12'-0\" CEILING HEIGHT 8'-0\""""
    merged = merge_heuristic_layout(llm_empty, user, cad)
    layout = parse_layout_from_llm_dict(merged)
    r = validate_us_irc_baseline(layout, raw_for_response=False)
    assert r.status_label != "insufficient_data"
    assert r.applicable_rules >= 2


def test_heuristic_egress_inch_pair_scores_below_100():
    """18\" × 36\" ≈ 4.5 sq ft < 5.7 IRC screening minimum — must not report 100%."""
    llm_empty = {}
    user = (
        'Compact 2-bedroom: Bedroom A ~120 sq ft, Bedroom B ~100 sq ft, 9 ft ceilings, '
        'hallway 36 inch clear. Each bedroom: 18" W x 36" H NET CLEAR OPENING for egress screening.'
    )
    merged = merge_heuristic_layout(llm_empty, user, "")
    layout = parse_layout_from_llm_dict(merged)
    r = validate_us_irc_baseline(layout, raw_for_response=False)
    assert r.status_label != "insufficient_data"
    assert r.applicable_rules >= 4
    assert r.score_percent is not None and r.score_percent < 100
    assert any(v.rule_id == "egress_window_min_area" for v in r.violations)


def test_two_identical_undersized_egress_windows_counted():
    llm_empty = {}
    user = (
        'Bedroom A egress: 18" x 36" NET CLEAR.\n'
        'Bedroom B egress: 18" x 36" NET CLEAR.'
    )
    merged = merge_heuristic_layout(llm_empty, user, "")
    assert len(merged["egress_windows_sqft"]) == 2


def test_stairs_rise_fail():
    layout = LayoutExtract(
        rooms=[RoomExtract(name="Hall", area_sqft=None, ceiling_ft=None)],
        stairs=StairsExtract(rise_in=8.0, tread_in=11.0),
        doors_inches=[],
        egress_windows_sqft=[],
    )
    r = validate_us_irc_baseline(layout, raw_for_response=False)
    assert any(v.rule_id == "stair_max_rise" for v in r.violations)
