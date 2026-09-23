"""One-off real probe against the Amap endpoints. The key is never written to disk."""

from __future__ import annotations

import argparse
import os
import time

import httpx

from app.services.amap_errors import classify, message

GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
POI_URL = "https://restapi.amap.com/v5/place/text"
AOI_URL = "https://restapi.amap.com/v5/aoi/polyline"
PROBE_POI_ID = "B00140BNNF"
SAMPLES = ["越秀公园", "天河公园"]


def call(client: httpx.Client, url: str, params: dict) -> tuple[dict, float]:
    started = time.perf_counter()
    resp = client.get(url, params=params)
    return resp.json(), time.perf_counter() - started


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", default=os.environ.get("AMAP_KEY", ""))
    parser.add_argument("--region", default="440100")
    args = parser.parse_args()
    if not args.key:
        raise SystemExit("no key: set AMAP_KEY or pass --key")

    with httpx.Client(timeout=20.0) as client:
        geo, dt = call(client, GEOCODE_URL, {"key": args.key, "address": SAMPLES[0], "city": "广州"})
        bucket = classify(geo.get("infocode", ""))
        print(f"[geocode] status={geo.get('status')} infocode={geo.get('infocode')} bucket={bucket} {message(bucket)} {dt:.2f}s")
        for g in (geo.get("geocodes") or [])[:1]:
            print(f"          location={g.get('location')} level={g.get('level')}")

        for name in SAMPLES:
            poi, dt = call(
                client,
                POI_URL,
                {"key": args.key, "keywords": name, "region": args.region, "city_limit": "true", "page_size": 3},
            )
            bucket = classify(poi.get("infocode", ""))
            pois = poi.get("pois") or []
            print(f"[poi] keywords={name} status={poi.get('status')} bucket={bucket} hits={len(pois)} {dt:.2f}s")
            for p in pois[:3]:
                print(f"      -> {p.get('name')} | {p.get('id')} | {p.get('typecode')} | {p.get('adname')}")

        aoi, dt = call(client, AOI_URL, {"key": args.key, "id": PROBE_POI_ID})
        bucket = classify(aoi.get("infocode", ""))
        print(f"[aoi] id={PROBE_POI_ID} status={aoi.get('status')} infocode={aoi.get('infocode')} bucket={bucket} {message(bucket)} {dt:.2f}s")


if __name__ == "__main__":
    main()
