from app.services.geometry import parse_polyline, ring_area_ha


def test_parse_polyline_skips_malformed_tokens():
    ring = parse_polyline("113.1,23.1_113.2,23.1_bad_113.2,23.2_113.1,23.1")
    assert ring == [(113.1, 23.1), (113.2, 23.1), (113.2, 23.2), (113.1, 23.1)]
    assert parse_polyline("") == []


def test_area_of_ten_thousandth_degree_square():
    ring = [(113.0, 23.0), (113.01, 23.0), (113.01, 23.01), (113.0, 23.01)]
    area = ring_area_ha(ring)
    # 0.01 deg ~ 1.02 km east-west at this latitude and ~1.11 km north-south
    assert 108 < area < 118, area


def test_area_needs_three_points():
    assert ring_area_ha([(113.0, 23.0), (113.1, 23.1)]) == 0.0
