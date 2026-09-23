"""Configuration endpoints, including the third-party connectivity probe."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.settings import ConfigPayload, ConfigView, load_settings, mask_key, save_settings, to_view
from app.services import amap_errors

router = APIRouter(tags=["config"])

GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
AOI_URL = "https://restapi.amap.com/v5/aoi/polyline"
PROBE_ADDRESS = "\u8d8a\u79c0\u516c\u56ed"
PROBE_CITY = "\u5e7f\u5dde"
PROBE_POI_ID = "B00140BNNF"


class VerifyResult(BaseModel):
    key_masked: str
    key_status: str
    key_message: str
    geocode_status: str
    geocode_location: str = ""
    geocode_formatted_address: str = ""
    aoi_status: str
    aoi_message: str
    aoi_hint: str = ""


@router.get("/config", response_model=ConfigView)
def get_config() -> ConfigView:
    return to_view(load_settings())


@router.put("/config", response_model=ConfigView)
def put_config(payload: ConfigPayload) -> ConfigView:
    keys = [k.strip() for k in payload.keys if k.strip()]
    if not keys:
        raise HTTPException(status_code=422, detail="at least one API key is required")
    settings = load_settings()
    settings.keys = keys
    settings.qps = payload.qps
    settings.daily_limit_per_key = payload.daily_limit_per_key
    settings.default_region = payload.default_region
    settings.sleep_every = payload.sleep_every
    settings.sleep_min_seconds = payload.sleep_min_seconds
    settings.sleep_max_seconds = payload.sleep_max_seconds
    settings.poi_page_size = payload.poi_page_size
    settings.poi_max_pages = payload.poi_max_pages
    settings.typecode_prefix = payload.typecode_prefix.strip()
    save_settings(settings)
    return to_view(settings)


@router.post("/config/verify", response_model=VerifyResult)
async def verify_config() -> VerifyResult:
    """Probe the real Amap endpoints so the UI can tell the user what works."""
    settings = load_settings()
    if not settings.keys:
        raise HTTPException(status_code=422, detail="configure at least one API key first")
    key = settings.keys[0]

    async with httpx.AsyncClient(timeout=15.0) as client:
        geo_resp = await client.get(
            GEOCODE_URL, params={"key": key, "address": PROBE_ADDRESS, "city": PROBE_CITY}
        )
        geo = geo_resp.json()
        aoi_resp = await client.get(AOI_URL, params={"key": key, "id": PROBE_POI_ID})
        aoi = aoi_resp.json()

    key_bucket = amap_errors.classify(geo.get("infocode", ""))
    geocodes = geo.get("geocodes") or []
    location = geocodes[0].get("location", "") if geocodes else ""
    formatted = geocodes[0].get("formatted_address", "") if geocodes else ""

    aoi_bucket = amap_errors.classify(aoi.get("infocode", ""))
    hint = ""
    if aoi_bucket == "insufficient_privileges":
        hint = "AOI \u8fb9\u754c\u67e5\u8be2\u9700\u5728\u9ad8\u5fb7\u63a7\u5236\u53f0\u63d0\u5de5\u5355\u5f00\u901a\uff1ahttps://console.amap.com/dev/ticket/create/66"

    return VerifyResult(
        key_masked=mask_key(key),
        key_status=key_bucket,
        key_message=amap_errors.message(key_bucket),
        geocode_status=key_bucket,
        geocode_location=location,
        geocode_formatted_address=formatted,
        aoi_status=aoi_bucket,
        aoi_message=amap_errors.message(aoi_bucket),
        aoi_hint=hint,
    )
