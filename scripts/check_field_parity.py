"""Compare the runtime response fields with what the frontend expects.

Run:
    uv run python scripts/check_field_parity.py --strict
Writes docs/field-parity.md and exits non-zero on any missing field.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

OUT = pathlib.Path(__file__).resolve().parents[1] / "docs" / "field-parity.md"
NL = chr(10)

RECORD_ROW_FIELDS = [
    "id",
    "task_id",
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
    "selected",
]

FRONTEND_REQUIRED: dict[str, list[str]] = {
    "GET /api/config": [
        "keys_masked",
        "key_count",
        "qps",
        "daily_limit_per_key",
        "default_region",
        "sleep_every",
        "sleep_min_seconds",
        "sleep_max_seconds",
        "poi_page_size",
        "poi_max_pages",
        "typecode_prefix",
    ],
    "POST /api/tasks/preview": [
        "columns",
        "rows",
        "suggested_name_column",
        "suggested_adname_column",
        "name_confidence",
        "row_count_preview",
    ],
    "POST /api/tasks": ["task_id", "total", "skipped"],
    "GET /api/tasks/{id}": [
        "id",
        "kind",
        "status",
        "source_filename",
        "total",
        "done",
        "failed",
        "paused_reason",
    ],
    "GET /api/records": ["total", "page", "page_size", "items", "ids"],
    "GET /api/records -> items[]": RECORD_ROW_FIELDS,
}

EXPORT_HEADER = [
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


def csv_bytes(rows: list[list[str]]) -> bytes:
    return NL.join(",".join(row) for row in rows).encode("utf-8")


def main() -> None:
    strict = "--strict" in sys.argv
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        os.environ["DATA_DIR"] = tmp
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        client.put(
            "/api/config",
            json={"keys": ["abcdefgh12345678"], "default_region": "440100"},
        )
        payload = csv_bytes(
            [["名称", "行政区"], ["越秀公园", "越秀区"]]
        )
        preview = client.post(
            "/api/tasks/preview", files={"file": ("c.csv", payload, "text/csv")}, params={"max_rows": 5}
        ).json()
        created = client.post(
            "/api/tasks",
            files={"file": ("c.csv", payload, "text/csv")},
            data={"name_column": "名称", "adname_column": "行政区"},
        ).json()
        task_id = created["task_id"]
        task = client.get(f"/api/tasks/{task_id}").json()
        records = client.get("/api/records", params={"task_id": task_id}).json()
        export_text = client.get(f"/api/tasks/{task_id}/export", params={"format": "csv"}).text

        runtime: dict[str, object] = {
            "GET /api/config": client.get("/api/config").json(),
            "POST /api/tasks/preview": preview,
            "POST /api/tasks": created,
            "GET /api/tasks/{id}": task,
            "GET /api/records": records,
            "GET /api/records -> items[]": (records.get("items") or [{}])[0],
        }

        rows_report = []
        missing_total = 0
        for endpoint, required in FRONTEND_REQUIRED.items():
            body = runtime.get(endpoint) or {}
            present = sorted(body.keys()) if isinstance(body, dict) else []
            missing = [field for field in required if field not in present]
            missing_total += len(missing)
            rows_report.append(
                {
                    "endpoint": endpoint,
                    "runtime": ", ".join(present) or "(empty)",
                    "missing": ", ".join(missing) or "-",
                }
            )
        export_header = export_text.strip().splitlines()[0].split(",") if export_text.strip() else []
        export_missing = [field for field in EXPORT_HEADER if field not in export_header]
        missing_total += len(export_missing)
        rows_report.append(
            {
                "endpoint": "GET /api/tasks/{id}/export (csv header)",
                "runtime": ", ".join(export_header) or "(empty)",
                "missing": ", ".join(export_missing) or "-",
            }
        )

        lines = [
            "# 字段对账报告",
            "",
            "由 `scripts/check_field_parity.py` 生成，规则是「后端运行时真实返回的字段为准」。",
            "前端如果引用了下表 `缺失` 列里的字段，必须先改后端或改前端。",
            "",
            "| 接口 | 运行时字段 | 缺失 |",
            "|---|---|---|",
        ]
        for row in rows_report:
            lines.append(f"| {row['endpoint']} | {row['runtime']} | {row['missing']} |")
        lines += [
            "",
            "## 结论",
            "",
            f"- 缺失字段总数：{missing_total}",
            "- `POST /api/config/verify` 与 `POST /api/tasks/{id}/run`、`/aoi`、`/pause`、`/resume` "
            "需要真实网络或后台任务，不在本报告里采集，字段以 openapi.json 为准。",
        ]
        OUT.write_text(NL.join(lines) + NL, encoding="utf-8", newline=NL)
        print(f"wrote {OUT} (missing fields: {missing_total})")
        if strict and missing_total:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
