"""Async client for the Amap Web service endpoints this project uses."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.services import amap_errors

POI_URL = "https://restapi.amap.com/v5/place/text"
AOI_URL = "https://restapi.amap.com/v5/aoi/polyline"
GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"


class AmapError(Exception):
    """Raised when Amap answers with status != 1."""

    def __init__(self, infocode: str, info: str) -> None:
        self.infocode = infocode
        self.info = info
        self.bucket = amap_errors.classify(infocode)
        super().__init__(f"{infocode} {info}")


@dataclass
class SearchHit:
    poi_id: str
    name: str
    poi_type: str
    typecode: str
    address: str
    adname: str
    lng: float | None
    lat: float | None


def parse_point(value: str) -> tuple[float | None, float | None]:
    parts = (value or "").split(",")
    if len(parts) != 2:
        return None, None
    try:
        return float(parts[0]), float(parts[1])
    except ValueError:
        return None, None


class AmapClient:
    """One key per client; rotation lives in the key pool."""

    def __init__(self, key: str, http: httpx.AsyncClient, region: str = "440100") -> None:
        self.key = key
        self.http = http
        self.region = region

    async def search_poi(
        self,
        keywords: str,
        page_size: int = 25,
        max_pages: int = 1,
        typecode_prefix: str = "",
    ) -> list[SearchHit]:
        """Search POIs. typecode_prefix filters on Amap's category code, e.g. "11" = parks."""
        hits: list[SearchHit] = []
        for page in range(1, max_pages + 1):
            payload = await self._get(
                POI_URL,
                {
                    "keywords": keywords,
                    "region": self.region,
                    "city_limit": "true",
                    "page_size": page_size,
                    "page_num": page,
                },
            )
            pois = payload.get("pois") or []
            if not pois:
                break
            for poi in pois:
                typecode = str(poi.get("typecode", ""))
                if typecode_prefix and not typecode.startswith(typecode_prefix):
                    continue
                lng, lat = parse_point(poi.get("location", ""))
                hits.append(
                    SearchHit(
                        poi_id=str(poi.get("id", "")),
                        name=str(poi.get("name", "")),
                        poi_type=str(poi.get("type", "")),
                        typecode=typecode,
                        address=str(poi.get("address", "")),
                        adname=str(poi.get("adname", "")),
                        lng=lng,
                        lat=lat,
                    )
                )
            if len(pois) < page_size:
                break
        return hits

    async def aoi_polyline(self, poi_id: str) -> str | None:
        payload = await self._get(AOI_URL, {"id": poi_id})
        aois = payload.get("aois") or []
        if not aois:
            return None
        return aois[0].get("polyline") or None

    async def geocode(self, address: str, city: str = "\u5e7f\u5dde") -> tuple[str, str]:
        payload = await self._get(GEOCODE_URL, {"address": address, "city": city})
        rows = payload.get("geocodes") or []
        if not rows:
            return "", ""
        return str(rows[0].get("location", "")), str(rows[0].get("formatted_address", ""))

    async def _get(self, url: str, params: dict[str, object]) -> dict:
        query = dict(params)
        query["key"] = self.key
        response = await self.http.get(url, params=query)
        response.raise_for_status()
        payload = response.json()
        if str(payload.get("status")) != "1":
            raise AmapError(str(payload.get("infocode", "")), str(payload.get("info", "")))
        return payload
