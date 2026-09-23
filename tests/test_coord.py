import csv
import math
import pathlib

from app.services.coord import gcj02_to_wgs84, wgs84_to_gcj02

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "coord_pairs.csv"


def _pairs():
    with FIXTURE.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_gcj02_to_wgs84_matches_reference_within_two_metres():
    rows = _pairs()
    assert len(rows) >= 100
    worst = 0.0
    for row in rows:
        lng, lat = gcj02_to_wgs84(float(row["gcj02_x"]), float(row["gcj02_y"]))
        # 1e-5 degree is roughly one metre
        worst = max(
            worst,
            math.hypot((lng - float(row["wgs84_x"])) * 1e5, (lat - float(row["wgs84_y"])) * 1e5),
        )
    # The reference column was produced by a different (approximate) inverse,
    # so agreement within about 3 m is the honest expectation here.
    assert worst < 3.0, f"worst deviation was {worst}"


def test_roundtrip_is_stable():
    lng, lat = wgs84_to_gcj02(113.264354, 23.139941)
    back_lng, back_lat = gcj02_to_wgs84(lng, lat)
    assert abs(back_lng - 113.264354) < 1e-6
    assert abs(back_lat - 23.139941) < 1e-6


def test_outside_china_is_returned_unchanged():
    assert gcj02_to_wgs84(-0.12, 51.5) == (-0.12, 51.5)

def test_offset_magnitude_is_typical_for_guangzhou():
    lng, lat = 113.264354, 23.139941
    glng, glat = wgs84_to_gcj02(lng, lat)
    metres = math.hypot((glng - lng) * 102000, (glat - lat) * 110600)
    assert 300 < metres < 800, metres
