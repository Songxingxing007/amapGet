"""Polyline parsing and area computation for AOI boundaries."""

from __future__ import annotations

import math

EARTH_RADIUS_M = 6378137.0


def parse_polyline(raw: str) -> list[tuple[float, float]]:
    """Parse Amap polyline text: pairs joined by commas, points joined by underscores."""
    ring: list[tuple[float, float]] = []
    for token in (raw or "").split("_"):
        parts = token.split(",")
        if len(parts) != 2:
            continue
        try:
            ring.append((float(parts[0]), float(parts[1])))
        except ValueError:
            continue
    return ring


def ring_area_ha(ring: list[tuple[float, float]]) -> float:
    """Spherical polygon area in hectares; adequate for park-sized AOIs."""
    if len(ring) < 3:
        return 0.0
    total = 0.0
    for index in range(len(ring)):
        lng1, lat1 = ring[index]
        lng2, lat2 = ring[(index + 1) % len(ring)]
        total += math.radians(lng2 - lng1) * (2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2)))
    square_metres = abs(total * EARTH_RADIUS_M * EARTH_RADIUS_M / 2.0)
    return square_metres / 10000.0
