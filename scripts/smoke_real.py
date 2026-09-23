"""End-to-end smoke test against the real Amap endpoints.

Spends real quota: round one issues one POI search per name, round two one AOI
request per selected record. Requires an explicit --yes.

    uv run python scripts/smoke_real.py --yes            (reads AMAP_KEY)
    uv run python scripts/smoke_real.py --yes --key KEY  (explicit key)
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
import tempfile

NL = chr(10)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default=os.environ.get("AMAP_KEY", ""))
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--data-dir", default="")
    args = parser.parse_args()
    if not args.yes:
        raise SystemExit("this script spends real Amap quota; re-run with --yes")
    if not args.key:
        raise SystemExit("no key: set AMAP_KEY or pass --key")

    data_dir = args.data_dir or tempfile.mkdtemp(prefix="amap-smoke-")
    os.environ["DATA_DIR"] = data_dir
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "backend"))

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    client.put("/api/config", json={"keys": [args.key], "qps": 2, "sleep_every": 0})
    payload = NL.join(
        [
            "名称,行政区",
            "越秀公园,越秀区",
            "天河公园,天河区",
            "广州从化云台山区级森林自然公园,从化区",
        ]
    ).encode("utf-8")
    created = client.post(
        "/api/tasks",
        files={"file": ("smoke.csv", payload, "text/csv")},
        data={"name_column": "名称", "adname_column": "行政区"},
    ).json()
    task_id = created["task_id"]
    print(f"task {task_id}: {created['total']} names")

    run = client.post(f"/api/tasks/{task_id}/run", params={"sync": "true"}).json()
    print("round1:", run)
    records = client.get("/api/records", params={"task_id": task_id, "page_size": 50}).json()
    for row in records["items"]:
        print(
            f"  {row['query_name']} -> {row['poi_name']!r} | {row['match_level']} | "
            f"{row['typecode']} | {row['adname']} | {row['aoi_status']}"
        )

    ids = [row["id"] for row in records["items"] if row["poi_id"]][:2]
    if ids:
        aoi = client.post(
            f"/api/tasks/{task_id}/aoi", params={"sync": "true"}, json={"record_ids": ids}
        ).json()
        print("round2:", aoi)
        after = client.get("/api/records", params={"task_id": task_id, "page_size": 50}).json()
        for row in after["items"]:
            if row["id"] in ids:
                print(f"  aoi {row['poi_id']}: status={row['aoi_status']} area={row['aoi_area_ha']}")
    print("data dir:", data_dir)


if __name__ == "__main__":
    main()
