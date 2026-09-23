import httpx
import pytest
import respx

from app.services.amap_client import AmapClient, AmapError

POI = "https://restapi.amap.com/v5/place/text"
AOI = "https://restapi.amap.com/v5/aoi/polyline"


@respx.mock
@pytest.mark.asyncio
async def test_search_poi_uses_v5_parameter_names():
    route = respx.get(POI).mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "1",
                "info": "OK",
                "infocode": "10000",
                "pois": [
                    {
                        "id": "B00140BNNF",
                        "name": "\u8d8a\u79c0\u516c\u56ed",
                        "type": "\u98ce\u666f\u540d\u80dc;\u516c\u56ed\u5e7f\u573a;\u516c\u56ed",
                        "typecode": "110101",
                        "address": "\u89e3\u653e\u5317\u8def988\u53f7",
                        "adname": "\u8d8a\u79c0\u533a",
                        "location": "113.265561,23.140096",
                    }
                ],
            },
        )
    )
    async with httpx.AsyncClient() as http:
        hits = await AmapClient("k", http, "440100").search_poi("\u8d8a\u79c0\u516c\u56ed")
    assert len(hits) == 1
    assert hits[0].poi_id == "B00140BNNF"
    assert hits[0].adname == "\u8d8a\u79c0\u533a"
    params = route.calls[0].request.url.params
    assert params["city_limit"] == "true"
    assert params["page_num"] == "1"
    assert "citylimit" not in params


@respx.mock
@pytest.mark.asyncio
async def test_search_poi_raises_bucketed_error():
    respx.get(POI).mock(
        return_value=httpx.Response(200, json={"status": "0", "info": "INVALID_USER_KEY", "infocode": "10001"})
    )
    async with httpx.AsyncClient() as http:
        with pytest.raises(AmapError) as excinfo:
            await AmapClient("k", http).search_poi("x")
    assert excinfo.value.bucket == "key_invalid"
    assert excinfo.value.infocode == "10001"


@respx.mock
@pytest.mark.asyncio
async def test_aoi_polyline_returns_text_or_none():
    respx.get(AOI).mock(
        return_value=httpx.Response(
            200,
            json={"status": "1", "info": "OK", "infocode": "10000", "aois": [{"polyline": "113.1,23.1_113.2,23.2"}]},
        )
    )
    async with httpx.AsyncClient() as http:
        text = await AmapClient("k", http).aoi_polyline("B1")
    assert text == "113.1,23.1_113.2,23.2"


@respx.mock
@pytest.mark.asyncio
async def test_aoi_polyline_returns_none_when_absent():
    respx.get(AOI).mock(
        return_value=httpx.Response(200, json={"status": "1", "info": "OK", "infocode": "10000", "aois": []})
    )
    async with httpx.AsyncClient() as http:
        assert await AmapClient("k", http).aoi_polyline("B1") is None
