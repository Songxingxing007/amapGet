"""CSV and GeoJSON writers for the fixed export schema."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable

from app.db.models import Record
from app.services import coord as coord_service
from app.services.geometry import parse_polyline

CSV_FIELDS = [
    "query_name",
    "match_level",
    "poi_name",
    "poi_id",
    "poi_type",
    "typecode",
    "address",
    "adname",
    "lng_gcj02",
    "lat_gcj02",
    "lng_wgs84",
    "lat_wgs84",
    "aoi_status",
    "aoi_area_ha",
]


def to_csv(records: Iterable[Record]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    for record in records:
        writer.writerow({field: getattr(record, field, "") for field in CSV_FIELDS})
    return buffer.getvalue()


def to_geojson(records: Iterable[Record], crs: str = "gcj02") -> dict:
    features = []
    for record in records:
        if record.aoi_status != "ok" or not record.polyline_gcj02:
            continue
        ring = parse_polyline(record.polyline_gcj02)
        if len(ring) < 3:
            continue
        if crs == "wgs84":
            ring = [coord_service.gcj02_to_wgs84(lng, lat) for lng, lat in ring]
        if ring[0] != ring[-1]:
            ring = ring + [ring[0]]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": [[[lng, lat] for lng, lat in ring]]},
                "properties": {field: getattr(record, field, None) for field in CSV_FIELDS},
            }
        )
    return {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": crs}}, "features": features}


def dumps(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)
