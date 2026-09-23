# 外部接口台账

记录本项目用到的每个外部接口：文档地址、参数、返回字段、限制、实测结果、MCP 是否覆盖。
每次真实调用后都要更新「实测」一行。

## 1. 搜索 POI 2.0（第一轮主用）

- 文档：https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch
- URL：`GET https://restapi.amap.com/v5/place/text`
- 必填：`key`、`keywords`（单个关键字，长度不超过 80 字符；与 `types` 二选一）
- 常用可选：`types`（typecode，多个用 `|` 分隔）、`region`（citycode／adcode／cityname）、`city_limit`（true/false）、`page_size`（1—25）、`page_num`、`show_fields`
- 返回：`status`／`info`／`infocode` 加 `pois[]`，字段 `id、name、type、typecode、address、adname、pname、cityname、citycode、adcode、location`
- 限制：同一组参数翻页最多取 200 条；注意 V5 用 `city_limit`、`page_num`，V3 用 `citylimit`、`page`，写错会被静默忽略
- 实测（2026-09-23）：`keywords=越秀公园&region=440100&city_limit=true&page_size=3` → `status=1`、`infocode=10000`、命中 3 条，首条 越秀公园 `B00140BNNF`（110101，越秀区），耗时 0.15 秒
- 实测（2026-09-23）：`keywords=天河公园` → 首条 天河公园 `B00140H465`（110101，天河区），耗时 0.20 秒
- 实测（2026-09-23）：`keywords=广东流溪河国家森林自然公园` → 首条 流溪河国家森林公园 `B00140862A`（110202，从化区）
- 实测（2026-09-23）：`keywords=广州从化云台山区级森林自然公园` → 返回云台花园、广州文化公园、广州雕塑公园，均非目标，需人工处理
- MCP：覆盖（关键词搜索 `maps_text_search`）

## 2. AOI 边界查询（第二轮主用）

- 文档：https://lbs.amap.com/api/webservice/guide/api-advanced/search
- URL：`GET https://restapi.amap.com/v5/aoi/polyline`
- 必填：`key`、`id`（一次仅一个 poiid）；可选 `sig`、`callback`
- 返回：`aois[]`，字段 `name、id、location、polyline、type、typecode、pname、cityname、adname、address、pcode、citycode、adcode`
- `polyline` 是下划线分隔的 `lng,lat` 坐标串
- 限制：属高阶服务，须提工单开通：https://console.amap.com/dev/ticket/create/66
- 实测（2026-09-23）：`id=B00140BNNF` → `status=0`、`infocode=10012`、`INSUFFICIENT_PRIVILEGES`，耗时 0.13 秒；判定为无权限
- MCP：不覆盖

## 3. 地理编码（名称转坐标兜底）

- 文档：https://lbs.amap.com/api/webservice/guide/api/georegeo
- URL：`GET https://restapi.amap.com/v3/geocode/geo`
- 必填：`key`、`address`；可选 `city`
- 返回：`geocodes[]`，字段 `formatted_address、province、city、district、location、level`
- 实测（2026-09-23）：`address=越秀公园&city=广州` → `infocode=10000`、`level=兴趣点`、`location=113.264354,23.139941`，耗时 0.11 秒
- 注意：无 poi_id、无 AOI，只能做兜底
- MCP：覆盖（`maps_geo`）

## 4. 行政区域查询（确认不采用）

- 文档：https://lbs.amap.com/api/webservice/guide/api/district
- URL：`GET https://restapi.amap.com/v3/config/district`
- `keywords` 仅支持行政区名称、citycode、adcode；`extensions=all` 才返回行政区 `polyline`；不返回乡镇街道级边界
- 实测（2026-09-23）：`keywords=越秀公园&extensions=all` → `status=1` 但 `districts=[]`
- 结论：不能用于公园边界

## 5. 错误码处置

| infocode | 含义 | 处置 |
|---|---|---|
| 10000 | 正常 | 继续 |
| 10001 | Key 无效 | 禁用该 Key，换下一个 |
| 10012 | 权限不足 | 提示提工单，不重试 |
| 10003／10044 | 账号日配额耗尽 | 暂停任务，次日续跑 |
| 10014／10015 | QPS 超限 | 退避重试 |
| 10016—10021 | 其它临时错误 | 指数退避重试 3 次 |

## 6. MCP 交叉验证

- 服务：`@amap/amap-maps-mcp-server`（官方），env `AMAP_MAPS_API_KEY`
- 覆盖能力：关键词搜索、周边搜索、详情搜索、地理编码、逆地理编码等 16 项
- 不覆盖：AOI 边界查询
- 用法：对同一关键字比对自建客户端与 MCP 的命中数量、首条 `poi_id`、`adname`
- 用法：在本机配置官方 MCP Server 后生效

## 7. 真实调用记账

| 日期 | 场景 | 次数 | 备注 |
|---|---|---|---|
| 2026-09-23 | 规划阶段的接口探索 | 8 | 含一次 AOI 权限探测 |
| 2026-09-23 | Phase 1 联通性探针 | 4 | geocode 1、POI 2、AOI 1 |
| 2026-09-23 | Phase 2 前后端联调 | 0 | 只用后端接口与真实 xlsx，未调用高德接口 |
| 2026-09-24 | Phase 4 全链路联调 | 3 | 第一轮真实采集三个公园，全部命中 110101 |
| 2026-09-24 | Phase 3 真实冒烟与参数测量 | 7 | 3 次 POI + 2 次 AOI（10012）+ 2 次分类码效果测量 |
